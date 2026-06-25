"""
Clause Clustering Module
Implements BERT-based clause clustering using KMeans and LDA (topic modeling).
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None
import logging

logger = logging.getLogger(__name__)


class ClauseClusterer:
    """
    Handles clause clustering using BERT embeddings and KMeans
    """

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the clause clusterer

        Args:
            model_name: Name of the sentence transformer model to use
        """
        try:
            self.model = SentenceTransformer(model_name, device='cpu')
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def embed_clauses(self, clause_texts, batch_size=32, convert_to_numpy=True):
        """
        Generate BERT embeddings for clause texts with optimized batching

        Args:
            clause_texts: List of clause text strings
            batch_size: Batch size for encoding (default: 32)
            convert_to_numpy: Convert to numpy array (default: True)

        Returns:
            numpy array of embeddings
        """
        try:
            if not clause_texts:
                return np.array([])

            # Use batch processing and GPU if available
            embeddings = self.model.encode(
                clause_texts,
                show_progress_bar=False,
                batch_size=batch_size,
                convert_to_numpy=convert_to_numpy,
                normalize_embeddings=True  # Faster cosine similarity
            )
            logger.info(f"Generated embeddings for {len(clause_texts)} clauses")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to embed clauses: {e}")
            raise

    def determine_optimal_clusters(self, embeddings, min_k=3, max_k=12):
        """
        Determine optimal number of clusters using silhouette score

        Args:
            embeddings: Clause embeddings array
            min_k: Minimum number of clusters
            max_k: Maximum number of clusters

        Returns:
            Optimal number of clusters
        """
        if len(embeddings) < min_k:
            return min(len(embeddings), 2)

        best_k = min_k
        best_score = -1

        for k in range(min_k, min(max_k + 1, len(embeddings))):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)

            if score > best_score:
                best_score = score
                best_k = k

        logger.info(f"Optimal clusters: {best_k} (silhouette score: {best_score:.3f})")
        return best_k

    def cluster_clauses(self, clause_texts, n_clusters=None):
        """
        Cluster clauses using BERT embeddings and KMeans

        Args:
            clause_texts: List of clause text strings
            n_clusters: Number of clusters (if None, automatically determined)

        Returns:
            Dictionary with embeddings, labels, and cluster centers
        """
        try:
            if not clause_texts:
                return {
                    'embeddings': np.array([]),
                    'labels': np.array([]),
                    'n_clusters': 0,
                    'cluster_centers': np.array([])
                }

            # Generate embeddings
            embeddings = self.embed_clauses(clause_texts)

            # Determine optimal number of clusters if not provided
            if n_clusters is None:
                n_clusters = self.determine_optimal_clusters(embeddings)
            else:
                n_clusters = min(n_clusters, len(clause_texts))

            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)

            logger.info(f"Clustered {len(clause_texts)} clauses into {n_clusters} groups")

            return {
                'embeddings': embeddings,
                'labels': labels,
                'n_clusters': n_clusters,
                'cluster_centers': kmeans.cluster_centers_
            }
        except Exception as e:
            logger.error(f"Failed to cluster clauses: {e}")
            raise

    def cluster_clauses_lda(self, clause_texts, n_topics=None):
        """
        Cluster clauses using LDA topic modeling (alternative to KMeans).

        Args:
            clause_texts: List of clause text strings
            n_topics: Number of topics (if None, automatically determined via perplexity)

        Returns:
            Dict with labels, topic_words, n_clusters, topic_distributions
        """
        try:
            if not clause_texts or len(clause_texts) < 2:
                return {'labels': [], 'n_clusters': 0, 'topic_words': {}, 'topic_distributions': []}

            # TF-IDF vectorize
            vectorizer = CountVectorizer(
                max_features=500,
                stop_words='english',
                min_df=1,
                max_df=0.95,
            )
            dtm = vectorizer.fit_transform(clause_texts)

            # Determine n_topics
            if n_topics is None:
                n_topics = min(max(3, len(clause_texts) // 3), 10)
            n_topics = min(n_topics, len(clause_texts))

            # Fit LDA
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=20,
                learning_method='batch',
            )
            topic_dist = lda.fit_transform(dtm)  # shape: (n_docs, n_topics)

            # Assign each clause to its dominant topic
            labels = np.argmax(topic_dist, axis=1)

            # Get top words per topic
            feature_names = vectorizer.get_feature_names_out()
            topic_words = {}
            for topic_idx, topic in enumerate(lda.components_):
                top_indices = topic.argsort()[-10:][::-1]
                topic_words[topic_idx] = [feature_names[i] for i in top_indices]

            logger.info(f"LDA clustered {len(clause_texts)} clauses into {n_topics} topics")

            return {
                'labels': labels.tolist(),
                'n_clusters': n_topics,
                'topic_words': topic_words,
                'topic_distributions': topic_dist.tolist(),
                'method': 'lda',
            }
        except Exception as e:
            logger.error(f"LDA clustering failed: {e}", exc_info=True)
            raise

    def get_clause_groups(self, clause_texts, labels):
        """
        Group clauses by cluster labels

        Args:
            clause_texts: List of clause text strings
            labels: Cluster labels array

        Returns:
            Dictionary mapping cluster label to list of clause texts
        """
        clause_groups = {}

        for idx, label in enumerate(labels):
            label = int(label)
            if label not in clause_groups:
                clause_groups[label] = []
            clause_groups[label].append(clause_texts[idx])

        return clause_groups

    def find_representative_clause(self, cluster_clauses, cluster_center, embeddings):
        """
        Find the most representative clause for a cluster

        Args:
            cluster_clauses: List of clause texts in the cluster
            cluster_center: Centroid of the cluster
            embeddings: Embeddings of the clauses

        Returns:
            Most representative clause text
        """
        if not cluster_clauses:
            return ""

        # Calculate distances from center
        distances = np.linalg.norm(embeddings - cluster_center, axis=1)

        # Return clause closest to center
        closest_idx = np.argmin(distances)
        return cluster_clauses[closest_idx]


# Singleton instance
_clusterer = None


def get_clusterer():
    """Get or create singleton ClauseClusterer instance"""
    global _clusterer
    if _clusterer is None:
        _clusterer = ClauseClusterer()
    return _clusterer
