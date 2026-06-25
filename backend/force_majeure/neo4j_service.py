"""
Neo4j Knowledge Graph Service
Provides in-memory graph capabilities with NetworkX for FM knowledge representation
(Can be upgraded to real Neo4j when database is available)
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class Neo4jKnowledgeGraph:
    """In-memory knowledge graph for Force Majeure relationships"""

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._initialize_schema()

    def _initialize_schema(self):
        """Initialize FM knowledge graph schema"""

        # Node types
        self.node_types = [
            'Contract', 'Clause', 'Event', 'Risk', 'Mitigation',
            'LegalCase', 'IndustryTemplate', 'Disruption',
            'InfrastructureImpact', 'SupplyChainImpact', 'ContractOutcome',
            'Supplier', 'Port', 'Country', 'RiskEvent', 'Outcome'
        ]

        # Relationship types
        self.relationship_types = [
            'CONTAINS', 'COVERS', 'CAUSES', 'MITIGATED_BY', 'SUPPORTED_BY',
            'DEPENDS_ON', 'LOCATED_IN', 'HAS_EVENT', 'HAS_CLAUSE',
            'IMPACTS', 'AFFECTS', 'RELATED_TO', 'PART_OF'
        ]

        # Add sample nodes and relationships
        self._add_sample_data()

    def _add_sample_data(self):
        """Add sample FM knowledge graph data"""

        # Add FM event nodes
        fm_events = [
            'war', 'terrorism', 'cyber_warfare', 'pandemic', 'earthquake',
            'flood', 'sanctions', 'supply_chain_disruption', 'port_closure'
        ]

        for event in fm_events:
            self.add_node(
                node_id=f"event_{event}",
                node_type='Event',
                properties={'name': event, 'category': 'fm_event'}
            )

        # Add disruption nodes
        disruptions = [
            'factory_shutdown', 'transport_shutdown', 'labor_shortage',
            'power_grid_failure', 'port_closure'
        ]

        for disruption in disruptions:
            self.add_node(
                node_id=f"disruption_{disruption}",
                node_type='Disruption',
                properties={'name': disruption}
            )

        # Add outcome nodes
        outcomes = [
            'project_delay', 'cost_overrun', 'contract_suspension',
            'fm_invocation', 'contract_termination'
        ]

        for outcome in outcomes:
            self.add_node(
                node_id=f"outcome_{outcome}",
                node_type='ContractOutcome',
                properties={'name': outcome}
            )

        # Add causal relationships
        # War -> disruptions
        self.add_relationship('event_war', 'disruption_factory_shutdown', 'CAUSES', {'probability': 0.65})
        self.add_relationship('event_war', 'disruption_transport_shutdown', 'CAUSES', {'probability': 0.70})
        self.add_relationship('event_war', 'disruption_port_closure', 'CAUSES', {'probability': 0.60})

        # Pandemic -> disruptions
        self.add_relationship('event_pandemic', 'disruption_labor_shortage', 'CAUSES', {'probability': 0.75})
        self.add_relationship('event_pandemic', 'disruption_factory_shutdown', 'CAUSES', {'probability': 0.60})

        # Disruptions -> outcomes
        self.add_relationship('disruption_factory_shutdown', 'outcome_project_delay', 'CAUSES', {'probability': 0.80})
        self.add_relationship('disruption_transport_shutdown', 'outcome_project_delay', 'CAUSES', {'probability': 0.75})
        self.add_relationship('disruption_labor_shortage', 'outcome_cost_overrun', 'CAUSES', {'probability': 0.60})

        # Outcomes -> FM invocation
        self.add_relationship('outcome_project_delay', 'outcome_fm_invocation', 'CAUSES', {'probability': 0.50})
        self.add_relationship('outcome_cost_overrun', 'outcome_fm_invocation', 'CAUSES', {'probability': 0.45})

    def add_node(
        self,
        node_id: str,
        node_type: str,
        properties: Optional[Dict] = None
    ) -> str:
        """Add a node to the graph"""
        if properties is None:
            properties = {}

        self.graph.add_node(
            node_id,
            node_type=node_type,
            **properties
        )

        return node_id

    def add_relationship(
        self,
        from_node: str,
        to_node: str,
        relationship_type: str,
        properties: Optional[Dict] = None
    ) -> None:
        """Add a relationship between nodes"""
        if properties is None:
            properties = {}

        self.graph.add_edge(
            from_node,
            to_node,
            relationship_type=relationship_type,
            **properties
        )

    def query_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 5
    ) -> List[List[str]]:
        """Find all paths between source and target"""
        try:
            paths = list(nx.all_simple_paths(
                self.graph,
                source,
                target,
                cutoff=max_depth
            ))
            return paths
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return []

    def get_neighbors(
        self,
        node_id: str,
        relationship_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all neighbors of a node"""
        if node_id not in self.graph:
            return []

        neighbors = []
        for successor in self.graph.successors(node_id):
            edge_data = self.graph.get_edge_data(node_id, successor)

            # Get first edge if multiple edges exist
            if edge_data:
                first_edge = next(iter(edge_data.values()))

                if relationship_type is None or first_edge.get('relationship_type') == relationship_type:
                    neighbors.append({
                        'node_id': successor,
                        'node_type': self.graph.nodes[successor].get('node_type'),
                        'relationship': first_edge.get('relationship_type'),
                        'properties': {k: v for k, v in self.graph.nodes[successor].items() if k != 'node_type'}
                    })

        return neighbors

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node details"""
        if node_id not in self.graph:
            return None

        node_data = self.graph.nodes[node_id]
        return {
            'node_id': node_id,
            'node_type': node_data.get('node_type'),
            'properties': {k: v for k, v in node_data.items() if k != 'node_type'}
        }

    def query_by_type(self, node_type: str, limit: int = 100) -> List[Dict]:
        """Get all nodes of a specific type"""
        nodes = []
        count = 0

        for node_id, data in self.graph.nodes(data=True):
            if data.get('node_type') == node_type:
                nodes.append({
                    'node_id': node_id,
                    'node_type': node_type,
                    'properties': {k: v for k, v in data.items() if k != 'node_type'}
                })
                count += 1
                if count >= limit:
                    break

        return nodes

    def get_subgraph(
        self,
        node_id: str,
        depth: int = 2
    ) -> Dict:
        """Get subgraph around a node"""
        if node_id not in self.graph:
            return {'nodes': [], 'edges': []}

        # BFS to get nodes within depth
        visited = set()
        queue = [(node_id, 0)]
        subgraph_nodes = []

        while queue:
            current, current_depth = queue.pop(0)

            if current in visited or current_depth > depth:
                continue

            visited.add(current)
            subgraph_nodes.append(current)

            if current_depth < depth:
                for neighbor in self.graph.neighbors(current):
                    if neighbor not in visited:
                        queue.append((neighbor, current_depth + 1))

        # Get subgraph
        subgraph = self.graph.subgraph(subgraph_nodes)

        # Format for output
        nodes = []
        for node in subgraph.nodes():
            node_data = self.graph.nodes[node]
            nodes.append({
                'id': node,
                'type': node_data.get('node_type'),
                'label': node_data.get('name', node),
                'properties': {k: v for k, v in node_data.items() if k not in ['node_type', 'name']}
            })

        edges = []
        for source, target, data in subgraph.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'type': data.get('relationship_type', 'RELATED_TO'),
                'properties': {k: v for k, v in data.items() if k != 'relationship_type'}
            })

        return {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges)
        }

    def find_causal_chain(
        self,
        event: str,
        outcome: str
    ) -> List[Dict]:
        """Find causal chains from event to outcome"""
        event_node = f"event_{event}"
        outcome_node = f"outcome_{outcome}"

        paths = self.query_paths(event_node, outcome_node, max_depth=10)

        chains = []
        for path in paths:
            chain_details = []
            for i in range(len(path) - 1):
                edge_data = self.graph.get_edge_data(path[i], path[i+1])
                first_edge = next(iter(edge_data.values()))

                chain_details.append({
                    'from': path[i],
                    'to': path[i+1],
                    'relationship': first_edge.get('relationship_type'),
                    'probability': first_edge.get('probability', 0.5)
                })

            # Calculate chain probability
            chain_prob = 1.0
            for link in chain_details:
                chain_prob *= link.get('probability', 0.5)

            chains.append({
                'path': path,
                'chain': chain_details,
                'probability': round(chain_prob, 4),
                'length': len(path)
            })

        # Sort by probability
        chains.sort(key=lambda x: x['probability'], reverse=True)

        return chains

    def get_graph_stats(self) -> Dict:
        """Get graph statistics"""
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': {
                node_type: sum(1 for _, data in self.graph.nodes(data=True) if data.get('node_type') == node_type)
                for node_type in self.node_types
            },
            'relationship_types': self.relationship_types,
            'is_directed': self.graph.is_directed(),
            'density': nx.density(self.graph)
        }

    def export_graph(self, format: str = 'cytoscape') -> Dict:
        """Export graph in visualization format"""
        if format == 'cytoscape':
            return self._export_cytoscape()
        elif format == 'networkx':
            return nx.node_link_data(self.graph)
        else:
            return {'error': f'Unsupported format: {format}'}

    def _export_cytoscape(self) -> Dict:
        """Export in Cytoscape.js format"""
        elements = []

        # Add nodes
        for node_id, data in self.graph.nodes(data=True):
            elements.append({
                'data': {
                    'id': node_id,
                    'label': data.get('name', node_id),
                    'type': data.get('node_type', 'Unknown'),
                    **{k: v for k, v in data.items() if k not in ['node_type', 'name']}
                }
            })

        # Add edges
        for source, target, data in self.graph.edges(data=True):
            elements.append({
                'data': {
                    'source': source,
                    'target': target,
                    'label': data.get('relationship_type', ''),
                    **{k: v for k, v in data.items() if k != 'relationship_type'}
                }
            })

        return {
            'elements': elements,
            'format': 'cytoscape'
        }


# Global instance
neo4j_graph = Neo4jKnowledgeGraph()


# Convenience functions
def get_fm_knowledge_graph():
    """Get the FM knowledge graph instance"""
    return neo4j_graph


def query_event_outcome_chain(event: str, outcome: str) -> List[Dict]:
    """Query causal chain from event to outcome"""
    return neo4j_graph.find_causal_chain(event, outcome)


def get_event_impacts(event: str) -> List[Dict]:
    """Get all impacts of an FM event"""
    event_node = f"event_{event}"
    return neo4j_graph.get_neighbors(event_node, 'CAUSES')
