"""
PrimeContractAI - Contract Graph Model
Core graph-based intelligence layer for contract analysis
"""

import networkx as nx
import uuid
from typing import Dict, List, Optional
from datetime import datetime


class ContractNode:
    """Represents a node in the contract graph"""

    def __init__(self, name: str, node_type: str, attributes: Dict):
        self.id = str(uuid.uuid4())
        self.name = name
        self.node_type = node_type
        self.attributes = attributes
        self.created_at = datetime.now()


class PrimeContractGraph:
    """
    Main graph model for contract intelligence
    Supports: Risk analysis, Drift detection, Counterfactual simulation
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.metadata = {
            "created_at": datetime.now(),
            "total_contracts": 0,
            "total_clauses": 0,
            "total_risks": 0
        }

    def add_contract(self, contract_data: Dict) -> str:
        """Add a contract node to the graph"""
        contract_id = contract_data.get("contract_id", str(uuid.uuid4()))

        # Exclude keys we're explicitly setting to avoid duplicate argument errors
        excluded_keys = {"contract_id", "name", "value", "risk_score", "status", "counterparty", "start_date", "end_date", "type"}
        extra_data = {k: v for k, v in contract_data.items() if k not in excluded_keys}

        self.graph.add_node(
            contract_id,
            type="CONTRACT",
            name=contract_data.get("name", f"Contract-{contract_id[:8]}"),
            value=contract_data.get("value", 0),
            risk_score=contract_data.get("risk_score", 0),
            status=contract_data.get("status", "active"),
            counterparty=contract_data.get("counterparty", "Unknown"),
            start_date=contract_data.get("start_date"),
            end_date=contract_data.get("end_date"),
            **extra_data
        )

        self.metadata["total_contracts"] += 1
        return contract_id

    def add_clause(self, contract_id: str, clause_data: Dict) -> str:
        """Add a clause node and link it to a contract"""
        clause_id = str(uuid.uuid4())

        # Exclude keys we're explicitly setting to avoid duplicate argument errors
        excluded_keys = {"text", "category", "risk_score", "confidence", "type"}
        extra_data = {k: v for k, v in clause_data.items() if k not in excluded_keys}

        self.graph.add_node(
            clause_id,
            type="CLAUSE",
            text=clause_data.get("text", ""),
            category=clause_data.get("category", "general"),
            risk_score=clause_data.get("risk_score", 0),
            confidence=clause_data.get("confidence", 0),
            **extra_data
        )

        # Link clause to contract
        self.graph.add_edge(
            contract_id,
            clause_id,
            relation="HAS_CLAUSE",
            weight=1.0
        )

        self.metadata["total_clauses"] += 1
        return clause_id

    def add_risk(self, clause_id: str, risk_data: Dict) -> str:
        """Add a risk node and link it to a clause"""
        risk_id = str(uuid.uuid4())

        # Exclude keys we're explicitly setting to avoid duplicate argument errors
        excluded_keys = {"category", "severity", "score", "description", "mitigation", "type"}
        extra_data = {k: v for k, v in risk_data.items() if k not in excluded_keys}

        self.graph.add_node(
            risk_id,
            type="RISK",
            category=risk_data.get("category", "general"),
            severity=risk_data.get("severity", "medium"),
            score=risk_data.get("score", 0),
            description=risk_data.get("description", ""),
            mitigation=risk_data.get("mitigation", ""),
            **extra_data
        )

        # Link risk to clause
        self.graph.add_edge(
            clause_id,
            risk_id,
            relation="HAS_RISK",
            weight=risk_data.get("score", 0) / 100
        )

        self.metadata["total_risks"] += 1
        return risk_id

    def calculate_total_contract_risk(self, contract_id: str) -> float:
        """Calculate aggregate risk score for a contract"""
        if contract_id not in self.graph:
            return 0.0

        total_risk = 0.0
        clause_count = 0

        # Traverse contract -> clauses -> risks
        for _, clause_id in self.graph.out_edges(contract_id):
            if self.graph.nodes[clause_id].get("type") == "CLAUSE":
                clause_count += 1
                clause_risk = self.graph.nodes[clause_id].get("risk_score", 0)
                total_risk += clause_risk

                # Add risks linked to this clause
                for _, risk_id in self.graph.out_edges(clause_id):
                    if self.graph.nodes[risk_id].get("type") == "RISK":
                        risk_score = self.graph.nodes[risk_id].get("score", 0)
                        total_risk += risk_score * 0.5  # Weight risk nodes at 50%

        return total_risk / max(clause_count, 1)

    def detect_unlimited_liability(self, contract_id: str) -> bool:
        """Detect if contract has unlimited liability clauses"""
        if contract_id not in self.graph:
            return False

        for _, clause_id in self.graph.out_edges(contract_id):
            if self.graph.nodes[clause_id].get("type") == "CLAUSE":
                category = self.graph.nodes[clause_id].get("category", "").lower()
                if "liability" in category:
                    cap = self.graph.nodes[clause_id].get("liability_cap")
                    if cap and str(cap).lower() in ["unlimited", "none", "infinite"]:
                        return True

        return False

    def detect_auto_renewal(self, contract_id: str) -> bool:
        """Detect if contract has auto-renewal clauses"""
        if contract_id not in self.graph:
            return False

        for _, clause_id in self.graph.out_edges(contract_id):
            if self.graph.nodes[clause_id].get("type") == "CLAUSE":
                category = self.graph.nodes[clause_id].get("category", "").lower()
                if "renewal" in category or "termination" in category:
                    auto_renew = self.graph.nodes[clause_id].get("auto_renewal", False)
                    if auto_renew:
                        return True

        return False

    def get_high_risk_contracts(self, threshold: float = 70.0) -> List[Dict]:
        """Get all contracts with risk score above threshold"""
        high_risk = []

        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "CONTRACT":
                risk_score = self.calculate_total_contract_risk(node_id)
                if risk_score >= threshold:
                    high_risk.append({
                        "id": node_id,
                        "name": data.get("name", "Unknown"),
                        "risk_score": risk_score,
                        "value": data.get("value", 0),
                        "counterparty": data.get("counterparty", "Unknown")
                    })

        return sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)

    def export_for_visualization(self) -> Dict:
        """Export graph data for frontend visualization"""
        nodes = []
        links = []

        def serialize_value(value):
            """Convert datetime and other non-serializable objects to strings"""
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, (list, tuple)):
                return [serialize_value(v) for v in value]
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            return value

        for node_id, data in self.graph.nodes(data=True):
            node_data = {
                "id": str(node_id),
                "name": data.get("name", str(node_id)[:8]),
                "type": data.get("type", "UNKNOWN"),
                "risk": data.get("risk_score", 0)
            }
            # Add other attributes, serializing datetime objects
            for k, v in data.items():
                if k not in ["name", "type", "risk_score"]:
                    node_data[k] = serialize_value(v)

            nodes.append(node_data)

        for source, target, data in self.graph.edges(data=True):
            links.append({
                "source": str(source),
                "target": str(target),
                "relation": data.get("relation", "RELATED"),
                "weight": data.get("weight", 1.0)
            })

        # Serialize metadata datetime
        metadata = {
            "total_contracts": self.metadata["total_contracts"],
            "total_clauses": self.metadata["total_clauses"],
            "total_risks": self.metadata["total_risks"],
            "created_at": self.metadata["created_at"].isoformat()
        }

        return {
            "nodes": nodes,
            "links": links,
            "metadata": metadata
        }

    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        # Calculate density safely (returns 0 for graphs with < 2 nodes)
        try:
            density = float(nx.density(self.graph)) if self.graph.number_of_nodes() > 1 else 0.0
        except:
            density = 0.0

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "contracts": self.metadata["total_contracts"],
            "clauses": self.metadata["total_clauses"],
            "risks": self.metadata["total_risks"],
            "density": density,
            "created_at": self.metadata["created_at"].isoformat()
        }
