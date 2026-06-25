"""
Portfolio Clustering Engine
Uses sentence-transformers + sklearn for semantic contract clustering
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

# Initialize embedder (cached globally for performance)
embedder = None

def get_embedder():
    """Lazy load embedder to avoid startup overhead"""
    global embedder
    if embedder is None:
        logger.info("Loading MiniLM embedder...")
        embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
    return embedder


def cluster_contracts(contracts, n_clusters=6):
    """
    Cluster contracts using semantic embeddings + KMeans

    Args:
        contracts: List of dicts with keys: id, name, text, industry, jurisdiction, vendor, risk_score
        n_clusters: Number of clusters (default: 6)

    Returns:
        List of dicts with x, y, z coordinates, cluster labels, and outlier flags
    """
    if not contracts:
        return []

    logger.info(f"Clustering {len(contracts)} contracts...")

    # Extract texts for embedding
    texts = []
    for c in contracts:
        # Combine multiple fields for richer semantic representation
        text_parts = []
        if c.get("text"):
            text_parts.append(c["text"][:5000])  # Limit to 5000 chars for performance
        if c.get("industry"):
            text_parts.append(f"Industry: {c['industry']}")
        if c.get("jurisdiction"):
            text_parts.append(f"Jurisdiction: {c['jurisdiction']}")

        combined_text = " ".join(text_parts) if text_parts else "Unknown contract"
        texts.append(combined_text)

    # Generate embeddings
    embedder_model = get_embedder()
    logger.info("Generating embeddings...")
    embeddings = embedder_model.encode(texts, show_progress_bar=False)

    # Standardize embeddings
    scaler = StandardScaler()
    embeddings_scaled = scaler.fit_transform(embeddings)

    # Reduce dimensions using PCA (384 -> 3)
    logger.info("Reducing dimensions with PCA...")
    pca = PCA(n_components=3, random_state=42)
    reduced = pca.fit_transform(embeddings_scaled)

    # Cluster using KMeans
    logger.info(f"Clustering with KMeans (k={n_clusters})...")
    # Adjust n_clusters if we have fewer contracts
    actual_clusters = min(n_clusters, len(contracts))
    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(reduced)
    centroids = kmeans.cluster_centers_

    # Detect outliers (95th percentile distance from centroid)
    logger.info("Detecting outliers...")
    distances = []
    for i in range(len(labels)):
        dist = np.linalg.norm(reduced[i] - centroids[labels[i]])
        distances.append(dist)

    outlier_threshold = np.percentile(distances, 95)

    # Map cluster numbers to meaningful archetypes
    cluster_archetypes = {
        0: "Standard Commercial",
        1: "High Risk Construction",
        2: "Service Agreements",
        3: "Procurement & Supply",
        4: "Legal & Compliance",
        5: "Infrastructure Projects"
    }

    # Build results
    results = []
    for i, contract in enumerate(contracts):
        cluster_id = int(labels[i])
        dist = distances[i]
        is_outlier = dist > outlier_threshold

        results.append({
            "id": contract["id"],
            "contract_name": contract["name"],
            "x": float(reduced[i][0]),
            "y": float(reduced[i][1]),
            "z": float(reduced[i][2]),
            "cluster": cluster_archetypes.get(cluster_id, f"Cluster {cluster_id}"),
            "cluster_id": cluster_id,
            "risk_archetype": "Unlimited Liability Heavy" if contract.get("risk_score", 0) > 70 else "Standard Risk",
            "industry": contract.get("industry", "Unknown"),
            "jurisdiction": contract.get("jurisdiction", "Unknown"),
            "vendor": contract.get("vendor", "Unknown"),
            "risk_score": contract.get("risk_score", 0),
            "outlier": is_outlier,
            "distance_from_center": float(dist)
        })

    logger.info(f"Clustering complete: {len(results)} contracts, {actual_clusters} clusters, {sum(1 for r in results if r['outlier'])} outliers")

    return results


def get_cluster_statistics(clustered_contracts):
    """
    Calculate cluster statistics for dashboard metrics

    Returns:
        Dict with cluster stats: sizes, avg risk scores, top industries per cluster
    """
    if not clustered_contracts:
        return {}

    # Group by cluster
    clusters = {}
    for c in clustered_contracts:
        cluster_id = c["cluster_id"]
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(c)

    # Calculate stats per cluster
    cluster_stats = []
    for cluster_id, contracts in clusters.items():
        cluster_name = contracts[0]["cluster"]
        avg_risk = np.mean([c["risk_score"] for c in contracts])
        outlier_count = sum(1 for c in contracts if c["outlier"])

        cluster_stats.append({
            "cluster_id": cluster_id,
            "cluster_name": cluster_name,
            "contract_count": len(contracts),
            "avg_risk_score": round(avg_risk, 1),
            "outlier_count": outlier_count,
            "outlier_percentage": round((outlier_count / len(contracts)) * 100, 1)
        })

    return {
        "total_contracts": len(clustered_contracts),
        "total_clusters": len(clusters),
        "total_outliers": sum(1 for c in clustered_contracts if c["outlier"]),
        "clusters": cluster_stats
    }
