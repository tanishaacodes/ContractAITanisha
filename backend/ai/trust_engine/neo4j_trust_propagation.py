"""
Neo4j Trust Propagation Service

Extends Neo4j graph with trust propagation capabilities.
Enables causal trust analysis across clause relationships.
"""
import logging
from typing import Dict, Any, List, Optional
from contractai.neo4j_config import get_neo4j_driver, check_neo4j_available

logger = logging.getLogger(__name__)


class TrustPropagationService:
    """
    Trust propagation and decay analysis using Neo4j.
    """

    # Trust decay weights for different relationships
    RELATIONSHIP_WEIGHTS = {
        'EVOLVED_FROM': 0.8,      # 80% trust transfer to child
        'SIMILAR_TO': 0.6,        # 60% trust transfer to similar
        'SAME_COUNTERPARTY': 0.7, # 70% trust transfer same counterparty
        'SAME_JURISDICTION': 0.75 # 75% trust transfer same jurisdiction
    }

    def __init__(self):
        self.driver = None
        self.neo4j_available = False
        self._initialize()

    def _initialize(self):
        """Initialize Neo4j connection"""
        try:
            if check_neo4j_available():
                self.driver = get_neo4j_driver()
                self.neo4j_available = True
                logger.info("[TRUST-PROPAGATION] Neo4j available")
            else:
                logger.warning("[TRUST-PROPAGATION] Neo4j not available")
        except Exception as e:
            logger.error(f"[TRUST-PROPAGATION] Initialization failed: {e}")
            self.neo4j_available = False

    def _run_query(self, query: str, params: Dict = None):
        """Execute Cypher query"""
        if not self.neo4j_available or not self.driver:
            logger.warning("[TRUST-PROPAGATION] Neo4j not available")
            return []

        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"[TRUST-PROPAGATION] Query failed: {e}")
            return []

    def sync_clause_trust(self, clause_id: str, trust_score: float,
                          enforceability: float, negotiability: float,
                          ambiguity: float, litigation_survival: float,
                          badge: str):
        """
        Sync trust scores to Neo4j clause node.

        Args:
            clause_id: Clause ID
            trust_score: Overall trust score
            enforceability: Enforceability score
            negotiability: Negotiability score
            ambiguity: Ambiguity score
            litigation_survival: Litigation survival score
            badge: Trust badge
        """
        query = """
        MERGE (c:Clause {id: $clause_id})
        SET c.trust_score = $trust_score,
            c.enforceability = $enforceability,
            c.negotiability = $negotiability,
            c.ambiguity = $ambiguity,
            c.litigation_survival = $litigation_survival,
            c.trust_badge = $badge,
            c.trust_updated_at = datetime()
        RETURN c
        """

        return self._run_query(query, {
            "clause_id": clause_id,
            "trust_score": trust_score,
            "enforceability": enforceability,
            "negotiability": negotiability,
            "ambiguity": ambiguity,
            "litigation_survival": litigation_survival,
            "badge": badge
        })

    def add_trust_relationship(self, source_clause_id: str, target_clause_id: str,
                               relationship_type: str, weight: float = None):
        """
        Add trust-carrying relationship between clauses.

        Args:
            source_clause_id: Source clause
            target_clause_id: Target clause
            relationship_type: Type (EVOLVED_FROM, SIMILAR_TO, etc.)
            weight: Optional custom weight (defaults from RELATIONSHIP_WEIGHTS)
        """
        if weight is None:
            weight = self.RELATIONSHIP_WEIGHTS.get(relationship_type, 0.5)

        query = f"""
        MATCH (source:Clause {{id: $source_id}})
        MATCH (target:Clause {{id: $target_id}})
        MERGE (source)-[r:{relationship_type}]->(target)
        SET r.trust_weight = $weight,
            r.created_at = datetime()
        RETURN source, r, target
        """

        return self._run_query(query, {
            "source_id": source_clause_id,
            "target_id": target_clause_id,
            "weight": weight
        })

    def propagate_trust_impact(self, clause_id: str, max_depth: int = 3):
        """
        Calculate trust impact radius from a clause.

        If this clause fails, which clauses are affected?

        Args:
            clause_id: Starting clause
            max_depth: Maximum propagation depth

        Returns:
            List of affected clauses with propagated trust scores
        """
        query = """
        MATCH (source:Clause {id: $clause_id})
        MATCH path = (source)-[r:EVOLVED_FROM|SIMILAR_TO|SAME_COUNTERPARTY|SAME_JURISDICTION*1..$max_depth]->(affected)
        WITH affected,
             source.trust_score AS source_trust,
             reduce(
                 score = source.trust_score,
                 rel IN relationships(path) |
                 score * coalesce(rel.trust_weight, 0.7)
             ) AS propagated_trust
        RETURN
            affected.id AS clause_id,
            affected.trust_score AS current_trust,
            propagated_trust,
            (affected.trust_score - propagated_trust) AS trust_delta,
            length(path) AS distance
        ORDER BY propagated_trust ASC
        """

        results = self._run_query(query, {
            "clause_id": clause_id,
            "max_depth": max_depth
        })

        return results

    def find_silent_killers(self, min_local_trust: float = 0.7, max_neighbor_trust: float = 0.4):
        """
        Find Silent Killer clauses:
        - High local trust score
        - But connected to many low-trust neighbors

        Args:
            min_local_trust: Minimum trust for the clause itself
            max_neighbor_trust: Maximum average neighbor trust

        Returns:
            List of silent killer clauses
        """
        query = """
        MATCH (c:Clause)
        WHERE c.trust_score > $min_local_trust
        MATCH (c)-[:SIMILAR_TO|EVOLVED_FROM]->(neighbor:Clause)
        WITH c, avg(neighbor.trust_score) AS neighbor_trust
        WHERE neighbor_trust < $max_neighbor_trust
        RETURN
            c.id AS clause_id,
            c.trust_score AS local_trust,
            neighbor_trust,
            c.trust_badge AS badge
        ORDER BY (c.trust_score - neighbor_trust) DESC
        """

        results = self._run_query(query, {
            "min_local_trust": min_local_trust,
            "max_neighbor_trust": max_neighbor_trust
        })

        return results

    def jurisdictional_trust_drift(self):
        """
        Analyze trust by jurisdiction.

        Returns clauses that are court-proven in some jurisdictions
        but fail in others.

        Returns:
            Trust scores grouped by jurisdiction
        """
        query = """
        MATCH (c:Clause)-[:USED_IN]->(j:Jurisdiction)
        RETURN
            j.name AS jurisdiction,
            avg(c.trust_score) AS avg_trust,
            count(c) AS clause_count,
            collect(c.id) AS clauses
        ORDER BY avg_trust ASC
        """

        return self._run_query(query)

    def counterparty_trust_collapse(self):
        """
        Find clauses that fail with specific counterparty types.

        Returns:
            Counterparty types with lowest trust clauses
        """
        query = """
        MATCH (c:Clause)-[:USED_WITH]->(cp:CounterpartyType)
        WHERE c.trust_score < 0.5
        RETURN
            cp.name AS counterparty_type,
            count(c) AS risky_clause_count,
            avg(c.trust_score) AS avg_trust,
            collect({id: c.id, trust: c.trust_score}) AS clauses
        ORDER BY risky_clause_count DESC
        """

        return self._run_query(query)

    def trust_contagion_simulation(self, failed_clause_id: str):
        """
        Simulate what happens if a clause fails.

        Calculates cascading trust impact across the graph.

        Args:
            failed_clause_id: Clause that failed

        Returns:
            Simulation results with affected clauses
        """
        # Step 1: Get affected clauses
        affected = self.propagate_trust_impact(failed_clause_id, max_depth=3)

        # Step 2: Classify impact severity
        results = []
        for clause in affected:
            trust_delta = clause.get('trust_delta', 0)

            if trust_delta > 0.2:
                severity = "CRITICAL"
            elif trust_delta > 0.1:
                severity = "HIGH"
            elif trust_delta > 0.05:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            results.append({
                **clause,
                "impact_severity": severity
            })

        return {
            "failed_clause": failed_clause_id,
            "affected_count": len(results),
            "affected_clauses": results,
            "critical_count": sum(1 for r in results if r["impact_severity"] == "CRITICAL"),
            "high_count": sum(1 for r in results if r["impact_severity"] == "HIGH")
        }

    def recommend_trust_repair(self, clause_id: str):
        """
        Recommend actions to repair trust for a clause.

        Args:
            clause_id: Clause to repair

        Returns:
            Recommendations based on graph analysis
        """
        # Get clause trust and its neighbors
        query = """
        MATCH (c:Clause {id: $clause_id})
        OPTIONAL MATCH (c)-[:SIMILAR_TO]->(similar:Clause)
        WHERE similar.trust_score > 0.8
        RETURN
            c.trust_score AS current_trust,
            c.trust_badge AS badge,
            collect({
                id: similar.id,
                trust: similar.trust_score,
                badge: similar.trust_badge
            }) AS high_trust_alternatives
        """

        results = self._run_query(query, {"clause_id": clause_id})

        if not results:
            return {
                "clause_id": clause_id,
                "recommendations": ["No data available"]
            }

        data = results[0]
        current_trust = data.get("current_trust", 0)
        badge = data.get("badge", "UNKNOWN")
        alternatives = data.get("high_trust_alternatives", [])

        recommendations = []

        # Badge-specific recommendations
        if badge == "SILENT_KILLER":
            recommendations.append("URGENT: Replace with court-proven alternative")
            recommendations.append("Consult legal counsel before using")
        elif badge == "LITIGATION_RISK":
            recommendations.append("CRITICAL: Remove from all contracts")
            recommendations.append("Search for proven alternative in library")
        elif badge == "NEGOTIATION_FRAGILE":
            recommendations.append("Review and simplify language")
            recommendations.append("Add negotiation fallback options")

        # Alternative suggestions
        if alternatives:
            recommendations.append(f"Found {len(alternatives)} high-trust alternatives:")
            for alt in alternatives[:3]:
                recommendations.append(f"  → Clause {alt['id']} (Trust: {alt['trust']:.0%}, Badge: {alt['badge']})")

        return {
            "clause_id": clause_id,
            "current_trust": current_trust,
            "badge": badge,
            "recommendations": recommendations,
            "alternatives": alternatives
        }


# Singleton instance
_trust_propagation_service = None


def get_trust_propagation_service():
    """Get singleton trust propagation service instance"""
    global _trust_propagation_service
    if _trust_propagation_service is None:
        _trust_propagation_service = TrustPropagationService()
    return _trust_propagation_service
