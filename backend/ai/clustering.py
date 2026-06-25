"""
Clustering Engine for Contracts and Clauses
Uses KMeans for intelligent clustering visualizations
"""
from sklearn.cluster import KMeans
import numpy as np

def cluster_clauses(clauses: list, n_clusters: int = 4):
    """
    Cluster clauses by risk score and contract value

    Args:
        clauses: List of clause dictionaries with risk_score and contract_value
        n_clusters: Number of clusters to create

    Returns:
        List of clauses with cluster assignments
    """
    if not clauses or len(clauses) < n_clusters:
        # Not enough data for clustering
        for i, c in enumerate(clauses):
            c['cluster'] = 0
        return clauses

    data = np.array([
        [c.get('risk_score', 0), c.get('contract_value', 0)]
        for c in clauses
    ])

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(data)

    for i, c in enumerate(clauses):
        c['cluster'] = int(labels[i])

    return clauses

def cluster_contracts(contracts: list, n_clusters: int = 3):
    """
    Cluster contracts by value and liability

    Args:
        contracts: List of contract dictionaries with contract_value and total_liability
        n_clusters: Number of clusters to create

    Returns:
        List of dictionaries with cluster assignments
    """
    if not contracts or len(contracts) < n_clusters:
        result = []
        for i, c in enumerate(contracts):
            result.append({
                'contract': c.get('contract_name', 'Unknown'),
                'x': c.get('contract_value', 0),
                'y': c.get('total_liability', 0),
                'cluster': 0,
                'contract_id': c.get('id')
            })
        return result

    data = np.array([
        [c.get('contract_value', 0), c.get('total_liability', 0)]
        for c in contracts
    ])

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(data)

    result = []
    for i, c in enumerate(contracts):
        result.append({
            'contract': c.get('contract_name', 'Unknown'),
            'x': c.get('contract_value', 0),
            'y': c.get('total_liability', 0),
            'cluster': int(labels[i]),
            'contract_id': c.get('id')
        })

    return result
