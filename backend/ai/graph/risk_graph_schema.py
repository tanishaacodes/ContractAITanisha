"""
Enhanced Neo4j Risk Graph Schema
==================================
Production-grade graph schema for legal risk modeling.

Node Types:
- Contract: Top-level contract node
- Clause: Individual contract clauses
- Risk: Risk factors (indemnity, liability, termination, etc.)
- Jurisdiction: Legal jurisdictions with risk multipliers
- Obligation: Extracted obligations from clauses

Relationship Types:
- HAS_CLAUSE: Contract -> Clause
- INTRODUCES: Clause -> Risk
- IMPACTS: Risk -> Risk (risk propagation)
- AMPLIFIES: Risk -> Risk (risk amplification)
- GOVERNED_BY: Contract -> Jurisdiction
- CONTAINS_OBLIGATION: Clause -> Obligation
- RELATES_TO: Clause -> Clause (semantic relationship)

Properties:
- Clauses: breach_probability, loss_mean, loss_std, severity_dist
- Risks: base_multiplier, category, severity
- Jurisdictions: risk_multiplier, legal_system
- Obligations: type, deadline, penalty

Author: PrimeContractAI System
"""

import logging
from typing import Dict, List, Any, Optional
from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available

logger = logging.getLogger(__name__)


# Graph schema constraints and indices
GRAPH_SCHEMA_CYPHER = """
-- Create uniqueness constraints
CREATE CONSTRAINT contract_id_unique IF NOT EXISTS
FOR (c:Contract) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT clause_id_unique IF NOT EXISTS
FOR (cl:Clause) REQUIRE cl.id IS UNIQUE;

CREATE CONSTRAINT risk_id_unique IF NOT EXISTS
FOR (r:Risk) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT jurisdiction_code_unique IF NOT EXISTS
FOR (j:Jurisdiction) REQUIRE j.code IS UNIQUE;

CREATE CONSTRAINT obligation_id_unique IF NOT EXISTS
FOR (o:Obligation) REQUIRE o.id IS UNIQUE;

-- Create indices for performance
CREATE INDEX clause_contract_idx IF NOT EXISTS
FOR (cl:Clause) ON (cl.contract_id);

CREATE INDEX clause_risk_score_idx IF NOT EXISTS
FOR (cl:Clause) ON (cl.risk_score);

CREATE INDEX risk_category_idx IF NOT EXISTS
FOR (r:Risk) ON (r.category);

CREATE INDEX risk_severity_idx IF NOT EXISTS
FOR (r:Risk) ON (r.severity);
"""


# Risk categories with base multipliers
RISK_CATEGORIES = {
    "INDEMNITY": {
        "base_multiplier": 1.0,
        "severity": "CRITICAL",
        "description": "Unlimited or broad indemnification obligations"
    },
    "LIABILITY": {
        "base_multiplier": 0.8,
        "severity": "HIGH",
        "description": "Liability caps, limitations, and exclusions"
    },
    "TERMINATION": {
        "base_multiplier": 0.6,
        "severity": "MEDIUM",
        "description": "Termination rights and consequences"
    },
    "PAYMENT": {
        "base_multiplier": 0.7,
        "severity": "HIGH",
        "description": "Payment terms, delays, and penalties"
    },
    "CONFIDENTIALITY": {
        "base_multiplier": 0.5,
        "severity": "MEDIUM",
        "description": "NDA and confidentiality obligations"
    },
    "INTELLECTUAL_PROPERTY": {
        "base_multiplier": 0.9,
        "severity": "CRITICAL",
        "description": "IP ownership, licensing, and infringement"
    },
    "WARRANTY": {
        "base_multiplier": 0.4,
        "severity": "MEDIUM",
        "description": "Warranties and representations"
    },
    "COMPLIANCE": {
        "base_multiplier": 0.7,
        "severity": "HIGH",
        "description": "Regulatory and legal compliance"
    },
    "DISPUTE_RESOLUTION": {
        "base_multiplier": 0.5,
        "severity": "MEDIUM",
        "description": "Arbitration, jurisdiction, governing law"
    },
    "FORCE_MAJEURE": {
        "base_multiplier": 0.3,
        "severity": "LOW",
        "description": "Force majeure and unforeseeable events"
    }
}


# Jurisdiction risk multipliers
JURISDICTION_MULTIPLIERS = {
    "US-NY": {"multiplier": 1.2, "legal_system": "Common Law", "litigation_friendly": True},
    "US-CA": {"multiplier": 1.3, "legal_system": "Common Law", "litigation_friendly": True},
    "US-DE": {"multiplier": 1.1, "legal_system": "Common Law", "litigation_friendly": True},
    "IN": {"multiplier": 0.9, "legal_system": "Common Law", "litigation_friendly": False},
    "UK": {"multiplier": 1.1, "legal_system": "Common Law", "litigation_friendly": True},
    "SG": {"multiplier": 1.0, "legal_system": "Common Law", "litigation_friendly": False},
    "HK": {"multiplier": 1.05, "legal_system": "Common Law", "litigation_friendly": True},
    "UAE": {"multiplier": 0.85, "legal_system": "Civil Law", "litigation_friendly": False},
    "EU": {"multiplier": 1.15, "legal_system": "Civil Law", "litigation_friendly": True}
}


class RiskGraphSchema:
    """
    Enhanced Neo4j graph schema manager for risk modeling.
    """

    def __init__(self):
        self.driver = None
        self.connected = False
        self._initialize()

    def _initialize(self):
        """Initialize Neo4j connection and schema"""
        try:
            self.driver = get_neo4j_driver()
            if self.driver:
                # Test connection
                try:
                    self.driver.verify_connectivity()
                    self.connected = True
                    logger.info("[RISK-GRAPH] Connected to Neo4j")
                except Exception as conn_err:
                    logger.warning(f"[RISK-GRAPH] Neo4j not reachable: {conn_err}")
                    self.connected = False
            else:
                logger.warning("[RISK-GRAPH] Neo4j driver not available")
                self.connected = False
        except Exception as e:
            logger.error(f"[RISK-GRAPH] Initialization failed: {e}")
            self.connected = False

    def apply_schema(self) -> bool:
        """
        Apply graph schema (constraints and indices).

        Returns:
            Success boolean
        """
        if not self.connected:
            logger.warning("[RISK-GRAPH] Cannot apply schema - not connected")
            return False

        try:
            with self.driver.session() as session:
                # Execute schema statements
                for statement in GRAPH_SCHEMA_CYPHER.strip().split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            session.run(statement)
                        except Exception as e:
                            # Constraint might already exist
                            logger.debug(f"[RISK-GRAPH] Schema statement skipped: {e}")

            logger.info("[RISK-GRAPH] Schema applied successfully")
            return True

        except Exception as e:
            logger.error(f"[RISK-GRAPH] Schema application failed: {e}")
            return False

    def seed_risk_categories(self) -> bool:
        """
        Seed Risk nodes for all risk categories.

        Returns:
            Success boolean
        """
        if not self.connected:
            return False

        try:
            with self.driver.session() as session:
                for category, props in RISK_CATEGORIES.items():
                    session.run("""
                        MERGE (r:Risk {id: $risk_id})
                        SET r.category = $category,
                            r.base_multiplier = $base_multiplier,
                            r.severity = $severity,
                            r.description = $description
                    """, risk_id=f"RISK_{category}",
                        category=category,
                        base_multiplier=props["base_multiplier"],
                        severity=props["severity"],
                        description=props["description"])

            logger.info(f"[RISK-GRAPH] Seeded {len(RISK_CATEGORIES)} risk categories")
            return True

        except Exception as e:
            logger.error(f"[RISK-GRAPH] Risk seeding failed: {e}")
            return False

    def seed_jurisdictions(self) -> bool:
        """
        Seed Jurisdiction nodes.

        Returns:
            Success boolean
        """
        if not self.connected:
            return False

        try:
            with self.driver.session() as session:
                for code, props in JURISDICTION_MULTIPLIERS.items():
                    session.run("""
                        MERGE (j:Jurisdiction {code: $code})
                        SET j.risk_multiplier = $multiplier,
                            j.legal_system = $legal_system,
                            j.litigation_friendly = $litigation_friendly
                    """, code=code,
                        multiplier=props["multiplier"],
                        legal_system=props["legal_system"],
                        litigation_friendly=props["litigation_friendly"])

            logger.info(f"[RISK-GRAPH] Seeded {len(JURISDICTION_MULTIPLIERS)} jurisdictions")
            return True

        except Exception as e:
            logger.error(f"[RISK-GRAPH] Jurisdiction seeding failed: {e}")
            return False

    def create_contract_with_risks(
        self,
        contract_id: str,
        clauses: List[Dict[str, Any]],
        jurisdiction: Optional[str] = None
    ) -> bool:
        """
        Create contract graph with risk modeling.

        Args:
            contract_id: Contract UUID
            clauses: List of clause dicts with risk attributes
            jurisdiction: Jurisdiction code (e.g., "US-NY", "IN")

        Returns:
            Success boolean
        """
        if not self.connected:
            return False

        try:
            # Ensure contract_id is a string (convert UUID if needed)
            contract_id_str = str(contract_id)

            with self.driver.session() as session:
                # Create Contract node
                session.run("""
                    MERGE (c:Contract {id: $contract_id})
                    SET c.created_at = datetime()
                """, contract_id=contract_id_str)

                # Link to Jurisdiction if provided
                if jurisdiction and jurisdiction in JURISDICTION_MULTIPLIERS:
                    session.run("""
                        MATCH (c:Contract {id: $contract_id})
                        MERGE (j:Jurisdiction {code: $jurisdiction})
                        MERGE (c)-[:GOVERNED_BY]->(j)
                    """, contract_id=contract_id_str, jurisdiction=jurisdiction)

                # Create Clause nodes with risk attributes
                for clause in clauses:
                    clause_id = str(clause['id'])  # Convert UUID to string
                    clause_name = clause.get('clause_name', '')
                    clause_type = clause.get('clause_type', 'general')
                    risk_score = clause.get('risk_score', 0.5)

                    # Monte Carlo attributes
                    breach_probability = clause.get('breach_probability', risk_score * 0.1)
                    loss_mean = clause.get('loss_mean', 0.0)
                    loss_std = clause.get('loss_std', 0.0)

                    session.run("""
                        MATCH (c:Contract {id: $contract_id})
                        MERGE (cl:Clause {id: $clause_id})
                        SET cl.contract_id = $contract_id,
                            cl.clause_name = $clause_name,
                            cl.clause_type = $clause_type,
                            cl.risk_score = $risk_score,
                            cl.breach_probability = $breach_probability,
                            cl.loss_mean = $loss_mean,
                            cl.loss_std = $loss_std
                        MERGE (c)-[:HAS_CLAUSE]->(cl)
                    """, contract_id=contract_id_str, clause_id=clause_id,
                        clause_name=clause_name, clause_type=clause_type,
                        risk_score=risk_score, breach_probability=breach_probability,
                        loss_mean=loss_mean, loss_std=loss_std)

                    # Link clause to risk category
                    risk_category = self._map_clause_to_risk_category(clause_type)
                    if risk_category:
                        weight = risk_score  # Higher risk = stronger relationship
                        session.run("""
                            MATCH (cl:Clause {id: $clause_id})
                            MATCH (r:Risk {id: $risk_id})
                            MERGE (cl)-[rel:INTRODUCES {weight: $weight}]->(r)
                        """, clause_id=clause_id,
                            risk_id=f"RISK_{risk_category}",
                            weight=weight)

                # Create risk propagation relationships
                self._create_risk_propagation(session, contract_id_str, clauses)

            logger.info(f"[RISK-GRAPH] Created contract graph for {contract_id_str}")
            return True

        except Exception as e:
            logger.error(f"[RISK-GRAPH] Contract creation failed: {e}", exc_info=True)
            return False

    def _create_risk_propagation(
        self,
        session: Any,
        contract_id: str,
        clauses: List[Dict[str, Any]]
    ):
        """Create IMPACTS relationships between risks"""
        # Define risk propagation rules
        propagation_rules = {
            "INDEMNITY": ["LIABILITY", "PAYMENT", "COMPLIANCE"],
            "LIABILITY": ["PAYMENT", "TERMINATION"],
            "PAYMENT": ["TERMINATION", "DISPUTE_RESOLUTION"],
            "INTELLECTUAL_PROPERTY": ["LIABILITY", "INDEMNITY"],
            "COMPLIANCE": ["LIABILITY", "TERMINATION"]
        }

        for source_risk, target_risks in propagation_rules.items():
            for target_risk in target_risks:
                # Create IMPACTS relationship
                session.run("""
                    MATCH (source:Risk {id: $source_id})
                    MATCH (target:Risk {id: $target_id})
                    MERGE (source)-[rel:IMPACTS {
                        weight: 0.7,
                        description: 'Risk propagation from ' + $source_category + ' to ' + $target_category
                    }]->(target)
                """, source_id=f"RISK_{source_risk}",
                    target_id=f"RISK_{target_risk}",
                    source_category=source_risk,
                    target_category=target_risk)

    def _map_clause_to_risk_category(self, clause_type: str) -> Optional[str]:
        """Map clause type to risk category"""
        clause_type_lower = clause_type.lower()

        mapping = {
            "indemnity": "INDEMNITY",
            "liability": "LIABILITY",
            "termination": "TERMINATION",
            "payment": "PAYMENT",
            "confidentiality": "CONFIDENTIALITY",
            "intellectual property": "INTELLECTUAL_PROPERTY",
            "ip": "INTELLECTUAL_PROPERTY",
            "warranty": "WARRANTY",
            "compliance": "COMPLIANCE",
            "dispute": "DISPUTE_RESOLUTION",
            "arbitration": "DISPUTE_RESOLUTION",
            "force majeure": "FORCE_MAJEURE"
        }

        for key, category in mapping.items():
            if key in clause_type_lower:
                return category

        return None  # General clause

    def get_cascading_risks(
        self,
        risk_id: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get cascading risk impacts using multi-hop traversal.

        Args:
            risk_id: Source risk ID
            max_depth: Maximum traversal depth (1-5)

        Returns:
            Dict with cascading risks and paths
        """
        if not self.connected:
            return {"cascading_risks": [], "paths": [], "total_impact": 0}

        try:
            max_depth = min(max(1, max_depth), 5)  # Clamp between 1-5

            with self.driver.session() as session:
                # Multi-hop IMPACTS traversal
                result = session.run(f"""
                    MATCH path = (source:Risk {{id: $risk_id}})-[impacts:IMPACTS*1..{max_depth}]->(target:Risk)
                    WITH path, target,
                         length(path) as depth,
                         reduce(weight = 1.0, r in relationships(path) | weight * r.weight) as cumulative_weight
                    RETURN target.id as risk_id,
                           target.category as category,
                           target.severity as severity,
                           target.base_multiplier as base_multiplier,
                           depth,
                           cumulative_weight,
                           [node in nodes(path) | node.category] as risk_path
                    ORDER BY depth ASC, cumulative_weight DESC
                """, risk_id=risk_id)

                cascading_risks = []
                paths = []
                seen_risks = set()

                for record in result:
                    risk_id_val = str(record['risk_id'])

                    if risk_id_val not in seen_risks:
                        cascading_risks.append({
                            "risk_id": risk_id_val,
                            "category": str(record['category']),
                            "severity": str(record['severity']),
                            "base_multiplier": float(record['base_multiplier']),
                            "depth": int(record['depth']),
                            "cumulative_impact": float(record['cumulative_weight'])
                        })
                        seen_risks.add(risk_id_val)

                    paths.append({
                        "target": risk_id_val,
                        "depth": int(record['depth']),
                        "path": record['risk_path'],
                        "impact_weight": float(record['cumulative_weight'])
                    })

                # Calculate total cascading impact
                total_impact = sum(r['cumulative_impact'] for r in cascading_risks)

                return {
                    "source_risk": risk_id,
                    "cascading_risks": cascading_risks,
                    "paths": paths,
                    "total_cascading_risks": len(cascading_risks),
                    "max_depth_reached": max(p['depth'] for p in paths) if paths else 0,
                    "total_impact": round(total_impact, 3)
                }

        except Exception as e:
            logger.error(f"[RISK-GRAPH] Cascading risk analysis failed: {e}")
            return {"cascading_risks": [], "paths": [], "total_impact": 0}

    def get_risk_blast_radius(
        self,
        contract_id: str,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Calculate blast radius for all risks in a contract using multi-hop analysis.

        Args:
            contract_id: Contract UUID
            max_hops: Maximum hops for impact analysis (1-5)

        Returns:
            Dict with risk blast radius analysis
        """
        if not self.connected:
            return {"risks": [], "total_blast_radius": 0}

        try:
            contract_id_str = str(contract_id)
            max_hops = min(max(1, max_hops), 5)

            with self.driver.session() as session:
                # For each risk introduced by contract clauses, find cascading impacts
                result = session.run(f"""
                    MATCH (c:Contract {{id: $contract_id}})-[:HAS_CLAUSE]->(cl:Clause)-[:INTRODUCES]->(r:Risk)
                    OPTIONAL MATCH path = (r)-[impacts:IMPACTS*1..{max_hops}]->(downstream:Risk)
                    WITH r,
                         collect(DISTINCT downstream) as affected_risks,
                         count(DISTINCT downstream) as blast_radius,
                         max(length(path)) as max_depth
                    RETURN r.id as risk_id,
                           r.category as category,
                           r.severity as severity,
                           blast_radius,
                           max_depth,
                           [risk in affected_risks | {{id: risk.id, category: risk.category, severity: risk.severity}}] as affected
                    ORDER BY blast_radius DESC
                """, contract_id=contract_id_str)

                risks = []
                total_blast_radius = 0

                for record in result:
                    blast_radius = int(record['blast_radius'] or 0)
                    total_blast_radius += blast_radius

                    risks.append({
                        "risk_id": str(record['risk_id']),
                        "category": str(record['category']),
                        "severity": str(record['severity']),
                        "blast_radius": blast_radius,
                        "max_depth": int(record['max_depth'] or 0),
                        "affected_risks": record['affected'] or []
                    })

                return {
                    "contract_id": contract_id,
                    "risks": risks,
                    "total_blast_radius": total_blast_radius,
                    "high_impact_risks": [r for r in risks if r['blast_radius'] >= 3],
                    "analysis_depth": max_hops
                }

        except Exception as e:
            logger.error(f"[RISK-GRAPH] Blast radius calculation failed: {e}")
            return {"risks": [], "total_blast_radius": 0}

    def get_risk_subgraph(
        self,
        contract_id: str,
        include_multihop: bool = False,
        max_hops: int = 2
    ) -> Dict[str, Any]:
        """
        Fetch risk subgraph for contract with optional multi-hop traversal.

        Args:
            contract_id: Contract UUID
            include_multihop: Include multi-hop IMPACTS paths
            max_hops: Maximum hops for multi-hop analysis (1-3)

        Returns:
            Dict with nodes and edges
        """
        if not self.connected:
            return {"nodes": [], "edges": []}

        try:
            # Ensure contract_id is a string (convert UUID if needed)
            contract_id_str = str(contract_id)

            with self.driver.session() as session:
                if include_multihop:
                    max_hops = min(max(1, max_hops), 3)  # Clamp 1-3
                    # Multi-hop query
                    result = session.run(f"""
                        MATCH (c:Contract {{id: $contract_id}})-[:HAS_CLAUSE]->(cl:Clause)
                        OPTIONAL MATCH (cl)-[intro:INTRODUCES]->(r:Risk)
                        OPTIONAL MATCH path = (r)-[impacts:IMPACTS*1..{max_hops}]->(r2:Risk)
                        OPTIONAL MATCH (c)-[:GOVERNED_BY]->(j:Jurisdiction)
                        WITH c, cl, r, r2, j, intro, impacts, path,
                             CASE WHEN path IS NOT NULL THEN length(path) ELSE null END as hop_count,
                             CASE WHEN path IS NOT NULL
                                  THEN reduce(w = 1.0, rel in relationships(path) | w * rel.weight)
                                  ELSE null END as cumulative_weight
                        RETURN c, cl, r, r2, j, intro, impacts, hop_count, cumulative_weight
                    """, contract_id=contract_id_str)
                else:
                    # Single-hop query (original)
                    result = session.run("""
                        MATCH (c:Contract {id: $contract_id})-[:HAS_CLAUSE]->(cl:Clause)
                        OPTIONAL MATCH (cl)-[intro:INTRODUCES]->(r:Risk)
                        OPTIONAL MATCH (r)-[imp:IMPACTS]->(r2:Risk)
                        OPTIONAL MATCH (c)-[:GOVERNED_BY]->(j:Jurisdiction)
                        RETURN c, cl, r, r2, j, intro, imp
                    """, contract_id=contract_id_str)

                nodes = []
                edges = []
                seen_nodes = set()
                seen_edges = set()

                for record in result:
                    # Add clause node
                    if record['cl'] and record['cl'].get('id') not in seen_nodes:
                        nodes.append({
                            "id": str(record['cl']['id']),  # Convert UUID to string
                            "type": "Clause",
                            "label": str(record['cl'].get('clause_name', 'Unnamed')),
                            "risk_score": float(record['cl'].get('risk_score', 0.5)),
                            "breach_probability": float(record['cl'].get('breach_probability', 0.05))
                        })
                        seen_nodes.add(record['cl']['id'])

                    # Add risk nodes (source and target)
                    if record['r'] and record['r'].get('id') not in seen_nodes:
                        nodes.append({
                            "id": str(record['r']['id']),  # Convert to string
                            "type": "Risk",
                            "label": str(record['r'].get('category', 'Unknown')),
                            "severity": str(record['r'].get('severity', 'MEDIUM')),
                            "base_multiplier": float(record['r'].get('base_multiplier', 0.5))
                        })
                        seen_nodes.add(record['r']['id'])

                    if record['r2'] and record['r2'].get('id') not in seen_nodes:
                        nodes.append({
                            "id": str(record['r2']['id']),
                            "type": "Risk",
                            "label": str(record['r2'].get('category', 'Unknown')),
                            "severity": str(record['r2'].get('severity', 'MEDIUM')),
                            "base_multiplier": float(record['r2'].get('base_multiplier', 0.5))
                        })
                        seen_nodes.add(record['r2']['id'])

                    # Add INTRODUCES edges
                    if record['intro'] and record['cl'] and record['r']:
                        edge_key = f"{record['cl']['id']}-INTRODUCES->{record['r']['id']}"
                        if edge_key not in seen_edges:
                            edges.append({
                                "source": str(record['cl']['id']),
                                "target": str(record['r']['id']),
                                "type": "INTRODUCES",
                                "weight": float(record['intro'].get('weight', 0.5))
                            })
                            seen_edges.add(edge_key)

                    # Add IMPACTS edges (single-hop or multi-hop)
                    if include_multihop:
                        # Multi-hop edges
                        if record.get('impacts') and record['r'] and record['r2']:
                            edge_key = f"{record['r']['id']}-IMPACTS->{record['r2']['id']}"
                            if edge_key not in seen_edges:
                                edges.append({
                                    "source": str(record['r']['id']),
                                    "target": str(record['r2']['id']),
                                    "type": "IMPACTS",
                                    "weight": float(record.get('cumulative_weight', 0.7)),
                                    "hops": int(record.get('hop_count', 1)),
                                    "multi_hop": int(record.get('hop_count', 1)) > 1
                                })
                                seen_edges.add(edge_key)
                    else:
                        # Single-hop edges
                        if record.get('imp') and record['r'] and record['r2']:
                            edge_key = f"{record['r']['id']}-IMPACTS->{record['r2']['id']}"
                            if edge_key not in seen_edges:
                                edges.append({
                                    "source": str(record['r']['id']),
                                    "target": str(record['r2']['id']),
                                    "type": "IMPACTS",
                                    "weight": float(record['imp'].get('weight', 0.7))
                                })
                                seen_edges.add(edge_key)

                return {
                    "nodes": nodes,
                    "edges": edges,
                    "contract_id": contract_id,
                    "multi_hop_enabled": include_multihop,
                    "max_hops": max_hops if include_multihop else 1
                }

        except Exception as e:
            logger.error(f"[RISK-GRAPH] Subgraph fetch failed: {e}")
            return {"nodes": [], "edges": []}


# Singleton instance
_risk_graph_schema = None


def get_risk_graph_schema() -> RiskGraphSchema:
    """Get singleton risk graph schema instance"""
    global _risk_graph_schema
    if _risk_graph_schema is None:
        _risk_graph_schema = RiskGraphSchema()
    return _risk_graph_schema
