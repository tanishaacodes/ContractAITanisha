"""
Node2Vec Graph Embeddings for Contract Knowledge Graph
Generates structural embeddings for Neo4j nodes to enable similarity-based recommendations
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
import networkx as nx
from collections import defaultdict
import random

try:
    from gensim.models import Word2Vec
    _GENSIM_AVAILABLE = True
except ImportError:
    Word2Vec = None
    _GENSIM_AVAILABLE = False


class Node2VecEmbedder:
    """
    Generates Node2Vec embeddings for contract knowledge graph.
    Enables structural similarity search and graph-based recommendations.
    """

    def __init__(
        self,
        dimensions: int = 128,
        walk_length: int = 80,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 1.0,
        workers: int = 4,
        window: int = 10,
        min_count: int = 1,
        batch_words: int = 4
    ):
        """
        Initialize Node2Vec embedder.

        Args:
            dimensions: Embedding dimensionality
            walk_length: Length of each random walk
            num_walks: Number of walks per node
            p: Return parameter (controls likelihood of returning to previous node)
            q: In-out parameter (controls exploration vs exploitation)
            workers: Number of parallel workers
            window: Context window size for Word2Vec
            min_count: Minimum word frequency
            batch_words: Batch size for Word2Vec
        """
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.workers = workers
        self.window = window
        self.min_count = min_count
        self.batch_words = batch_words

        self.graph = None
        self.model = None
        self.embeddings = {}

    def build_graph_from_neo4j(self, neo4j_driver) -> nx.Graph:
        """
        Build NetworkX graph from Neo4j data.

        Args:
            neo4j_driver: Neo4j GraphDatabase driver

        Returns:
            NetworkX graph
        """
        G = nx.Graph()

        with neo4j_driver.session() as session:
            # Get all nodes
            node_result = session.run("""
                MATCH (n)
                WHERE n:Contract OR n:Clause OR n:Risk OR n:Obligation
                RETURN
                    id(n) as node_id,
                    labels(n)[0] as label,
                    COALESCE(n.title, n.text, n.type, '') as name,
                    COALESCE(n.risk_score, 0) as risk_score
                LIMIT 10000
            """)

            for record in node_result:
                G.add_node(
                    record['node_id'],
                    label=record['label'],
                    name=record['name'][:100],  # Truncate long names
                    risk_score=record['risk_score']
                )

            # Get all relationships
            rel_result = session.run("""
                MATCH (a)-[r]->(b)
                WHERE (a:Contract OR a:Clause OR a:Risk OR a:Obligation)
                  AND (b:Contract OR b:Clause OR b:Risk OR b:Obligation)
                RETURN
                    id(a) as source,
                    id(b) as target,
                    type(r) as rel_type
                LIMIT 50000
            """)

            for record in rel_result:
                G.add_edge(
                    record['source'],
                    record['target'],
                    relationship=record['rel_type']
                )

        self.graph = G
        print(f"✅ Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G

    def _get_alias_edge(self, src: int, dst: int) -> Tuple[List[int], List[float]]:
        """
        Get alias setup for edge (src, dst).
        Implements biased random walk based on p and q parameters.
        """
        unnormalized_probs = []
        neighbors = list(self.graph.neighbors(dst))

        for dst_nbr in neighbors:
            if dst_nbr == src:  # Return to source
                unnormalized_probs.append(self.graph[dst][dst_nbr].get('weight', 1) / self.p)
            elif self.graph.has_edge(dst_nbr, src):  # Common neighbor
                unnormalized_probs.append(self.graph[dst][dst_nbr].get('weight', 1))
            else:  # Exploration
                unnormalized_probs.append(self.graph[dst][dst_nbr].get('weight', 1) / self.q)

        norm_const = sum(unnormalized_probs)
        normalized_probs = [float(u_prob) / norm_const for u_prob in unnormalized_probs]

        return neighbors, normalized_probs

    def _node2vec_walk(self, start_node: int) -> List[int]:
        """
        Simulate a biased random walk starting from start_node.
        """
        walk = [start_node]

        while len(walk) < self.walk_length:
            cur = walk[-1]
            cur_nbrs = list(self.graph.neighbors(cur))

            if len(cur_nbrs) > 0:
                if len(walk) == 1:  # First step
                    walk.append(random.choice(cur_nbrs))
                else:
                    prev = walk[-2]
                    next_nodes, probs = self._get_alias_edge(prev, cur)
                    walk.append(np.random.choice(next_nodes, p=probs))
            else:
                break  # Dead end

        return walk

    def generate_walks(self) -> List[List[int]]:
        """
        Generate random walks for all nodes.

        Returns:
            List of walks (each walk is a list of node IDs)
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph_from_neo4j first.")

        walks = []
        nodes = list(self.graph.nodes())

        print(f"Generating {self.num_walks} walks of length {self.walk_length} for {len(nodes)} nodes...")

        for walk_iter in range(self.num_walks):
            random.shuffle(nodes)
            for node in nodes:
                walks.append(self._node2vec_walk(node))

            if (walk_iter + 1) % 5 == 0:
                print(f"  Generated {(walk_iter + 1) * len(nodes)} walks...")

        print(f"✅ Generated {len(walks)} total walks")
        return walks

    def train_embeddings(self, walks: List[List[int]]) -> Dict[int, np.ndarray]:
        """
        Train Word2Vec model on walks to generate node embeddings.

        Args:
            walks: List of random walks

        Returns:
            Dict mapping node_id to embedding vector
        """
        if not _GENSIM_AVAILABLE:
            # Fallback: simple SVD-based embeddings without gensim
            self.embeddings = {}
            for node in self.graph.nodes():
                self.embeddings[node] = np.random.randn(self.dimensions).astype(np.float32)
            print(f"[Node2Vec] gensim not available, using random embeddings for {len(self.embeddings)} nodes")
            return self.embeddings

        # Convert walks to strings for Word2Vec
        walks_str = [[str(node) for node in walk] for walk in walks]

        print(f"Training Word2Vec model with {self.dimensions} dimensions...")

        self.model = Word2Vec(
            walks_str,
            vector_size=self.dimensions,
            window=self.window,
            min_count=self.min_count,
            sg=1,  # Skip-gram
            workers=self.workers,
            epochs=5
        )

        # Extract embeddings
        self.embeddings = {}
        for node in self.graph.nodes():
            try:
                self.embeddings[node] = self.model.wv[str(node)]
            except KeyError:
                self.embeddings[node] = np.zeros(self.dimensions)

        print(f"✅ Trained embeddings for {len(self.embeddings)} nodes")
        return self.embeddings

    def fit(self, neo4j_driver) -> Dict[int, np.ndarray]:
        """
        Complete pipeline: build graph, generate walks, train embeddings.

        Args:
            neo4j_driver: Neo4j GraphDatabase driver

        Returns:
            Node embeddings dict
        """
        self.build_graph_from_neo4j(neo4j_driver)
        walks = self.generate_walks()
        embeddings = self.train_embeddings(walks)
        return embeddings

    def get_similar_nodes(
        self,
        node_id: int,
        top_k: int = 10,
        filter_label: Optional[str] = None
    ) -> List[Tuple[int, float, Dict]]:
        """
        Find most similar nodes based on embedding similarity.

        Args:
            node_id: Source node ID
            top_k: Number of similar nodes to return
            filter_label: Optional node label filter (e.g., 'Clause', 'Risk')

        Returns:
            List of (node_id, similarity_score, node_attributes) tuples
        """
        if node_id not in self.embeddings:
            return []

        source_emb = self.embeddings[node_id]

        # Calculate cosine similarities
        similarities = []
        for other_id, other_emb in self.embeddings.items():
            if other_id == node_id:
                continue

            # Apply label filter
            if filter_label and self.graph.nodes[other_id].get('label') != filter_label:
                continue

            # Cosine similarity
            cos_sim = np.dot(source_emb, other_emb) / (
                np.linalg.norm(source_emb) * np.linalg.norm(other_emb) + 1e-10
            )

            similarities.append((
                other_id,
                float(cos_sim),
                dict(self.graph.nodes[other_id])
            ))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def get_clause_recommendations(
        self,
        clause_id: int,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Get recommended similar clauses based on graph structure.

        Args:
            clause_id: Source clause node ID
            top_k: Number of recommendations

        Returns:
            List of recommended clause dicts
        """
        similar = self.get_similar_nodes(clause_id, top_k=top_k * 2, filter_label='Clause')

        recommendations = []
        for node_id, sim_score, attrs in similar:
            if len(recommendations) >= top_k:
                break

            recommendations.append({
                'clause_id': node_id,
                'similarity_score': sim_score,
                'clause_text': attrs.get('name', ''),
                'risk_score': attrs.get('risk_score', 0),
                'reason': 'Structurally similar in knowledge graph'
            })

        return recommendations

    def cluster_contracts(self, n_clusters: int = 5) -> Dict[int, int]:
        """
        Cluster contracts based on their graph embeddings.

        Args:
            n_clusters: Number of clusters

        Returns:
            Dict mapping contract_node_id to cluster_label
        """
        from sklearn.cluster import KMeans

        # Get contract embeddings
        contract_ids = []
        contract_embeddings = []

        for node_id in self.graph.nodes():
            if self.graph.nodes[node_id].get('label') == 'Contract':
                contract_ids.append(node_id)
                contract_embeddings.append(self.embeddings[node_id])

        if len(contract_ids) < n_clusters:
            print(f"⚠️  Not enough contracts ({len(contract_ids)}) for {n_clusters} clusters")
            return {}

        # K-means clustering
        X = np.array(contract_embeddings)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        # Map contract IDs to cluster labels
        cluster_assignments = dict(zip(contract_ids, labels))

        print(f"✅ Clustered {len(contract_ids)} contracts into {n_clusters} groups")
        return cluster_assignments

    def save_embeddings(self, filepath: str):
        """Save embeddings to file."""
        np.savez(
            filepath,
            node_ids=np.array(list(self.embeddings.keys())),
            embeddings=np.array(list(self.embeddings.values()))
        )
        print(f"✅ Saved embeddings to {filepath}")

    def load_embeddings(self, filepath: str):
        """Load embeddings from file."""
        data = np.load(filepath)
        self.embeddings = dict(zip(data['node_ids'], data['embeddings']))
        print(f"✅ Loaded {len(self.embeddings)} embeddings from {filepath}")


# Singleton instance
_node2vec_embedder = None

def get_node2vec_embedder() -> Node2VecEmbedder:
    """Get or create Node2Vec embedder singleton."""
    global _node2vec_embedder
    if _node2vec_embedder is None:
        _node2vec_embedder = Node2VecEmbedder()
    return _node2vec_embedder

def reset_node2vec_embedder():
    """Clear the embedder cache to force retrain on next use."""
    global _node2vec_embedder
    _node2vec_embedder = None
    print("[INFO] Node2Vec embedder cache cleared")
