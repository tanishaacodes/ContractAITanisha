"""
Clause Clustering Module
=========================
Groups similar clauses together using unsupervised machine learning.

This module uses K-Means clustering to automatically organize clauses into
semantic groups based on their embedding vectors.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import logging

logger = logging.getLogger(__name__)


class ClauseClusterer:
    """
    K-Means based clause clustering for organizing clauses into semantic groups.
    """

    def __init__(self, n_clusters: int = 8, random_state: int = 42):
        """
        Initialize the clause clusterer.

        Args:
            n_clusters (int): Number of clusters to create (default: 8)
                            Common clause types: Payment, Termination, Liability,
                            Confidentiality, IP, Warranty, Dispute, General
            random_state (int): Random seed for reproducibility (default: 42)
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model = None
        self.cluster_centers = None

    def fit(self, embeddings: List[List[float]]) -> 'ClauseClusterer':
        """
        Fit the clustering model on clause embeddings.

        Args:
            embeddings (List[List[float]]): List of clause embedding vectors

        Returns:
            ClauseClusterer: Self for method chaining
        """
        if not embeddings:
            logger.error("No embeddings provided for clustering")
            return self

        try:
            # Convert to numpy array
            X = np.array(embeddings)

            # Adjust n_clusters if we have fewer samples
            n_clusters = min(self.n_clusters, len(embeddings))

            if n_clusters < 2:
                logger.warning("Too few samples for clustering, need at least 2")
                return self

            # Fit K-Means
            logger.info(f"Fitting K-Means with {n_clusters} clusters on {len(embeddings)} samples")
            self.model = KMeans(
                n_clusters=n_clusters,
                random_state=self.random_state,
                n_init=10,
                max_iter=300
            )
            self.model.fit(X)
            self.cluster_centers = self.model.cluster_centers_

            logger.info(f"Clustering complete. Inertia: {self.model.inertia_:.2f}")

            return self

        except Exception as e:
            logger.error(f"Error during clustering: {e}")
            return self

    def predict(self, embeddings: List[List[float]]) -> List[int]:
        """
        Predict cluster labels for new embeddings.

        Args:
            embeddings (List[List[float]]): List of clause embedding vectors

        Returns:
            List[int]: Cluster labels for each embedding
        """
        if self.model is None:
            logger.error("Model not fitted. Call fit() first.")
            return [0] * len(embeddings)

        try:
            X = np.array(embeddings)
            labels = self.model.predict(X)
            return labels.tolist()

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return [0] * len(embeddings)

    def fit_predict(self, embeddings: List[List[float]]) -> List[int]:
        """
        Fit the model and return cluster labels in one step.

        Args:
            embeddings (List[List[float]]): List of clause embedding vectors

        Returns:
            List[int]: Cluster labels for each embedding

        Example:
            >>> clusterer = ClauseClusterer(n_clusters=5)
            >>> labels = clusterer.fit_predict(embeddings)
            >>> len(set(labels))  # Number of unique clusters
            5
        """
        if not embeddings:
            logger.error("No embeddings provided for clustering")
            return []

        try:
            X = np.array(embeddings)
            n_clusters = min(self.n_clusters, len(embeddings))

            if n_clusters < 2:
                logger.warning("Too few samples, assigning all to cluster 0")
                return [0] * len(embeddings)

            self.model = KMeans(
                n_clusters=n_clusters,
                random_state=self.random_state,
                n_init=10,
                max_iter=300
            )
            labels = self.model.fit_predict(X)
            self.cluster_centers = self.model.cluster_centers_

            return labels.tolist()

        except Exception as e:
            logger.error(f"Error during fit_predict: {e}")
            return [0] * len(embeddings)

    def get_cluster_quality(self, embeddings: List[List[float]], labels: List[int]) -> float:
        """
        Calculate silhouette score to measure clustering quality.

        Args:
            embeddings (List[List[float]]): Clause embeddings
            labels (List[int]): Cluster labels

        Returns:
            float: Silhouette score (-1 to 1, higher is better)
                  -1 = incorrect clustering
                   0 = overlapping clusters
                   1 = well-separated clusters
        """
        try:
            X = np.array(embeddings)
            n_unique = len(set(labels))

            if n_unique < 2 or len(embeddings) < 2:
                return 0.0

            score = silhouette_score(X, labels)
            logger.info(f"Silhouette score: {score:.3f}")
            return float(score)

        except Exception as e:
            logger.error(f"Error calculating silhouette score: {e}")
            return 0.0


def cluster_clauses(embeddings: List[List[float]], k: int = 8) -> List[int]:
    """
    Convenience function to cluster clauses using K-Means.

    Args:
        embeddings (List[List[float]]): List of clause embedding vectors
        k (int): Number of clusters (default: 8)

    Returns:
        List[int]: Cluster label for each clause

    Example:
        >>> from nlp.clustering import cluster_clauses
        >>> labels = cluster_clauses(embeddings, k=5)
        >>> labels
        [0, 1, 0, 2, 1, 3, ...]
    """
    clusterer = ClauseClusterer(n_clusters=k)
    return clusterer.fit_predict(embeddings)


def group_clauses_by_cluster(clauses: List[str], labels: List[int]) -> Dict[int, List[str]]:
    """
    Group clauses by their cluster labels.

    Args:
        clauses (List[str]): List of clause texts
        labels (List[int]): Cluster labels for each clause

    Returns:
        Dict[int, List[str]]: Dictionary mapping cluster_id -> list of clauses

    Example:
        >>> clauses = ["Payment clause", "Termination clause", "Invoice clause"]
        >>> labels = [0, 1, 0]
        >>> groups = group_clauses_by_cluster(clauses, labels)
        >>> groups[0]
        ['Payment clause', 'Invoice clause']
    """
    groups = {}
    for clause, label in zip(clauses, labels):
        if label not in groups:
            groups[label] = []
        groups[label].append(clause)
    return groups


def find_optimal_k(embeddings: List[List[float]], min_k: int = 2, max_k: int = 15) -> Tuple[int, List[float]]:
    """
    Find optimal number of clusters using the elbow method.

    Args:
        embeddings (List[List[float]]): Clause embeddings
        min_k (int): Minimum number of clusters to try (default: 2)
        max_k (int): Maximum number of clusters to try (default: 15)

    Returns:
        Tuple[int, List[float]]: (optimal_k, list of inertia scores)

    Example:
        >>> optimal_k, scores = find_optimal_k(embeddings)
        >>> print(f"Optimal number of clusters: {optimal_k}")
    """
    if not embeddings:
        logger.error("No embeddings provided")
        return 2, []

    try:
        X = np.array(embeddings)
        max_possible_k = min(max_k, len(embeddings) - 1)

        if max_possible_k < min_k:
            logger.warning(f"Not enough samples. Using k={min_k}")
            return min_k, []

        inertias = []
        k_range = range(min_k, max_possible_k + 1)

        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)

        # Find elbow using rate of change
        if len(inertias) < 2:
            return min_k, inertias

        # Calculate second derivative (rate of change of rate of change)
        deltas = np.diff(inertias)
        second_deltas = np.diff(deltas)

        # Find elbow (point of maximum curvature)
        if len(second_deltas) > 0:
            elbow_idx = np.argmax(np.abs(second_deltas)) + 1
            optimal_k = min_k + elbow_idx
        else:
            optimal_k = min_k

        logger.info(f"Optimal k found: {optimal_k}")
        return optimal_k, inertias

    except Exception as e:
        logger.error(f"Error finding optimal k: {e}")
        return min_k, []


def get_cluster_statistics(embeddings: List[List[float]], labels: List[int]) -> Dict[int, Dict]:
    """
    Get statistics for each cluster.

    Args:
        embeddings (List[List[float]]): Clause embeddings
        labels (List[int]): Cluster labels

    Returns:
        Dict[int, Dict]: Statistics for each cluster including size and cohesion

    Example:
        >>> stats = get_cluster_statistics(embeddings, labels)
        >>> stats[0]
        {'size': 15, 'avg_distance_to_center': 0.23, 'density': 0.85}
    """
    try:
        X = np.array(embeddings)
        stats = {}

        for cluster_id in set(labels):
            # Get all points in this cluster
            cluster_mask = np.array(labels) == cluster_id
            cluster_points = X[cluster_mask]

            # Calculate statistics
            size = len(cluster_points)
            if size > 0:
                center = cluster_points.mean(axis=0)
                distances = np.linalg.norm(cluster_points - center, axis=1)
                avg_distance = distances.mean()
                max_distance = distances.max() if size > 0 else 0

                stats[cluster_id] = {
                    'size': size,
                    'avg_distance_to_center': float(avg_distance),
                    'max_distance_to_center': float(max_distance),
                    'density': float(1.0 / (1.0 + avg_distance)) if avg_distance > 0 else 1.0
                }
            else:
                stats[cluster_id] = {
                    'size': 0,
                    'avg_distance_to_center': 0.0,
                    'max_distance_to_center': 0.0,
                    'density': 0.0
                }

        return stats

    except Exception as e:
        logger.error(f"Error calculating cluster statistics: {e}")
        return {}
