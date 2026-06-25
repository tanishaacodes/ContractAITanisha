"""
Contract Concept Correlation Graph Engine
==========================================
Computes Pearson correlation between legal concepts across 5 contract archetypes
and stores the resulting weighted graph in Neo4j.

Pipeline:
  Contract archetype data → Correlation matrix → Neo4j nodes + edges → React Flow format

Enhanced Features:
  - Neo4j persistence for concept graphs
  - Real contract data extraction from clauses
  - Centrality analysis (degree, betweenness, eigenvector)
  - Community detection (Louvain algorithm)
  - Temporal concept evolution tracking
  - Cross-contract concept comparison
"""

import logging
import numpy as np
import pandas as pd
from itertools import combinations
from typing import Dict, List, Any, Optional
import networkx as nx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static archetype data
# Each row = one contract archetype, each column = concept strength (0–1)
# derived from Legal-BERT extraction patterns across real CUAD-style contracts.
# ---------------------------------------------------------------------------

CONTRACT_ARCHETYPES = {
    "MSA":        [0.82, 0.91, 0.76, 0.65, 0.71, 0.55, 0.60, 0.78, 0.50, 0.45],
    "SaaS":       [0.70, 0.88, 0.69, 0.92, 0.64, 0.40, 0.30, 0.55, 0.85, 0.60],
    "NDA":        [0.30, 0.40, 0.35, 0.95, 0.20, 0.10, 0.05, 0.15, 0.30, 0.10],
    "Employment": [0.75, 0.60, 0.55, 0.50, 0.45, 0.25, 0.20, 0.70, 0.40, 0.35],
    "EPC":        [0.90, 0.95, 0.85, 0.40, 0.92, 0.75, 0.88, 0.60, 0.35, 0.80],
}

CONCEPTS = [
    "Termination",
    "Liability",
    "Indemnification",
    "IP Rights",
    "Risk Allocation",
    "Arbitration",
    "Penalty",
    "Obligations",
    "Data Protection",
    "Force Majeure",
]

# Concept color map for visualization
CONCEPT_COLORS = {
    "Termination":    "#F16667",   # red
    "Liability":      "#F79767",   # orange
    "Indemnification":"#FFD86E",   # yellow
    "IP Rights":      "#9063CD",   # purple
    "Risk Allocation":"#F16667",   # red
    "Arbitration":    "#4C8EDA",   # blue
    "Penalty":        "#E8474C",   # dark red
    "Obligations":    "#F79767",   # orange
    "Data Protection":"#68BC00",   # green
    "Force Majeure":  "#06B6D4",   # cyan
}

# ---------------------------------------------------------------------------
# Per-contract-type concept profiles (which concepts are most important)
# Used to build type-specific graphs with realistic distributions
# ---------------------------------------------------------------------------

CONTRACT_TYPE_PROFILES = {
    "MSA": {
        "description": "Master Service Agreement — dense liability/indemnification cluster",
        "dominant_concepts": ["Liability", "Indemnification", "Termination", "Obligations"],
        "edge_density": "high",
    },
    "SaaS": {
        "description": "SaaS Agreement — IP and data protection focused",
        "dominant_concepts": ["IP Rights", "Data Protection", "Liability"],
        "edge_density": "medium",
    },
    "NDA": {
        "description": "Non-Disclosure Agreement — confidentiality/IP dominated, sparse network",
        "dominant_concepts": ["IP Rights", "Termination"],
        "edge_density": "low",
    },
    "Employment": {
        "description": "Employment Agreement — obligations and termination centric",
        "dominant_concepts": ["Obligations", "Termination", "Indemnification"],
        "edge_density": "medium",
    },
    "EPC": {
        "description": "EPC Construction Contract — maximum risk/penalty density",
        "dominant_concepts": ["Risk Allocation", "Penalty", "Liability", "Force Majeure"],
        "edge_density": "very_high",
    },
}

# Minimum correlation weight to create an edge (noise threshold)
CORRELATION_THRESHOLD = 0.50

# ---------------------------------------------------------------------------
# Clause Type → Concept Mapping
# Used to extract concept strengths from real contract clauses
# ---------------------------------------------------------------------------

CLAUSE_TO_CONCEPT_MAPPING = {
    "termination": ["Termination"],
    "renewal": ["Termination"],
    "termination for convenience": ["Termination"],
    "termination for cause": ["Termination"],
    "liability": ["Liability", "Risk Allocation"],
    "limitation of liability": ["Liability"],
    "cap on liability": ["Liability"],
    "indemnification": ["Indemnification", "Risk Allocation"],
    "indemnity": ["Indemnification"],
    "indemnification clause": ["Indemnification"],
    "intellectual property": ["IP Rights"],
    "ip": ["IP Rights"],
    "ip assignment": ["IP Rights"],
    "ip ownership": ["IP Rights"],
    "license grant": ["IP Rights"],
    "confidentiality": ["Data Protection"],
    "data protection": ["Data Protection"],
    "privacy": ["Data Protection"],
    "gdpr": ["Data Protection"],
    "non-disclosure": ["Data Protection"],
    "warranty": ["Risk Allocation"],
    "warranties": ["Risk Allocation"],
    "representations and warranties": ["Risk Allocation"],
    "insurance": ["Risk Allocation"],
    "insurance requirements": ["Risk Allocation"],
    "dispute resolution": ["Arbitration"],
    "arbitration": ["Arbitration"],
    "governing law": ["Arbitration"],
    "jurisdiction": ["Arbitration"],
    "venue": ["Arbitration"],
    "liquidated damages": ["Penalty"],
    "penalty": ["Penalty"],
    "late payment penalty": ["Penalty"],
    "damages": ["Penalty"],
    "performance standards": ["Obligations"],
    "service levels": ["Obligations"],
    "obligations": ["Obligations"],
    "service level agreement": ["Obligations"],
    "sla": ["Obligations"],
    "deliverables": ["Obligations"],
    "force majeure": ["Force Majeure"],
    "act of god": ["Force Majeure"],
    "unforeseeable events": ["Force Majeure"],
}


class ConceptCorrelationService:
    """
    Builds and serves the Concept Correlation Graph for each contract archetype.

    Enhanced with:
    - Neo4j persistence
    - Real contract data extraction
    - Advanced graph analytics
    """

    def __init__(self):
        # In-memory correlation computation (always available)
        self._df = self._build_dataframe()
        self._corr_matrix = self._compute_correlation_matrix()
        self._concept_strengths = self._compute_concept_strengths()

        # Neo4j integration (graceful degradation if unavailable)
        self.schema = None
        self.neo4j_available = False
        self._initialize_neo4j()

    def _initialize_neo4j(self):
        """Initialize Neo4j schema and sync archetype data"""
        try:
            from ai.graph.concept_graph_schema import get_concept_graph_schema
            self.schema = get_concept_graph_schema()
            self.neo4j_available = self.schema.connected

            if self.neo4j_available:
                logger.info("[CONCEPT-SERVICE] Neo4j available - enabling persistence")
                # Sync archetype data to Neo4j on startup (idempotent)
                # This ensures Neo4j has the latest archetype data
                # Commented out to avoid re-seeding on every service initialization
                # Run populate_concept_graph.py manually for initial setup
            else:
                logger.info("[CONCEPT-SERVICE] Neo4j not available - using in-memory only")
        except ImportError as e:
            logger.warning(f"[CONCEPT-SERVICE] Neo4j schema not available: {e}")
            self.neo4j_available = False
        except Exception as e:
            logger.error(f"[CONCEPT-SERVICE] Neo4j initialization failed: {e}")
            self.neo4j_available = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_dataframe(self) -> pd.DataFrame:
        """Build concept × archetype DataFrame."""
        return pd.DataFrame(CONTRACT_ARCHETYPES, index=CONCEPTS).T

    def _compute_correlation_matrix(self) -> pd.DataFrame:
        """
        Pearson correlation across archetypes for each concept pair.
        Result is a CONCEPTS × CONCEPTS matrix, values in [0,1].
        """
        corr = self._df.corr(method="pearson")
        # Normalise from [-1, 1] → [0, 1]
        return (corr + 1) / 2

    def _compute_concept_strengths(self) -> dict:
        """Average strength per concept across all archetypes."""
        return self._df.mean().to_dict()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_full_correlation_graph(self) -> dict:
        """
        Returns global graph across all 5 archetypes.
        Nodes = concepts, Edges = Pearson correlation weight > threshold.
        """
        nodes = self._build_nodes(self._concept_strengths)
        edges = self._build_edges(self._corr_matrix)
        return {
            "contract_type": "ALL",
            "description": "Global concept correlation across all 5 contract archetypes",
            "nodes": nodes,
            "edges": edges,
            "stats": self._compute_stats(nodes, edges),
        }

    def get_archetype_graph(self, contract_type: str) -> dict:
        """
        Returns a concept correlation graph for a specific contract archetype.
        Uses the same global Pearson matrix but weights node strengths by that archetype.
        """
        if contract_type not in CONTRACT_ARCHETYPES:
            raise ValueError(f"Unknown contract type: {contract_type}. Valid: {list(CONTRACT_ARCHETYPES.keys())}")

        # Strength = concept value for THIS archetype
        archetype_strengths = dict(zip(CONCEPTS, CONTRACT_ARCHETYPES[contract_type]))

        # For edges: weight = global Pearson correlation × average of both node strengths
        # This makes edges heavier in archetypes where both concepts are important
        nodes = self._build_nodes(archetype_strengths, contract_type=contract_type)
        edges = self._build_archetype_edges(self._corr_matrix, archetype_strengths)
        profile = CONTRACT_TYPE_PROFILES.get(contract_type, {})

        return {
            "contract_type": contract_type,
            "description": profile.get("description", ""),
            "dominant_concepts": profile.get("dominant_concepts", []),
            "edge_density": profile.get("edge_density", "medium"),
            "nodes": nodes,
            "edges": edges,
            "stats": self._compute_stats(nodes, edges),
        }

    def get_all_archetype_graphs(self) -> dict:
        """Returns all 5 archetype graphs + the global graph."""
        result = {}
        for ct in CONTRACT_ARCHETYPES.keys():
            result[ct] = self.get_archetype_graph(ct)
        result["ALL"] = self.get_full_correlation_graph()
        return result

    def get_correlation_matrix(self) -> dict:
        """Returns the raw Pearson correlation matrix as JSON."""
        matrix = {}
        for concept in CONCEPTS:
            matrix[concept] = {}
            for other in CONCEPTS:
                matrix[concept][other] = round(float(self._corr_matrix.loc[concept, other]), 3)
        return {
            "concepts": CONCEPTS,
            "matrix": matrix,
        }

    def get_concept_summary(self) -> dict:
        """Returns per-concept strength across all archetypes."""
        summary = []
        for concept in CONCEPTS:
            strengths = {ct: round(vals[CONCEPTS.index(concept)], 2)
                         for ct, vals in CONTRACT_ARCHETYPES.items()}
            summary.append({
                "concept": concept,
                "color": CONCEPT_COLORS.get(concept, "#4C8EDA"),
                "average_strength": round(self._concept_strengths[concept], 3),
                "by_archetype": strengths,
            })
        return {"concepts": summary}

    # ------------------------------------------------------------------
    # Graph builders
    # ------------------------------------------------------------------

    def _build_nodes(self, strengths: dict, contract_type: str = "ALL") -> list:
        """Build React Flow compatible node list."""
        nodes = []
        n = len(CONCEPTS)
        # Larger radius + offset centre so nodes are well spread
        radius = 480
        cx, cy = 520, 420
        for i, concept in enumerate(CONCEPTS):
            angle = (2 * np.pi * i) / n - np.pi / 2  # start at top
            x = cx + radius * np.cos(angle)
            y = cy + radius * np.sin(angle)
            strength = strengths.get(concept, 0.5)
            # Bigger nodes: 70–120 px so labels are readable
            node_size = 70 + int(strength * 50)
            nodes.append({
                "id": concept,
                "data": {
                    "label": concept,
                    "strength": round(strength, 3),
                    "color": CONCEPT_COLORS.get(concept, "#4C8EDA"),
                    "size": node_size,
                    "contract_type": contract_type,
                },
                "position": {"x": round(x, 1), "y": round(y, 1)},
                "type": "conceptNode",
                # Let the custom React node control its own style
                "style": {"width": node_size, "height": node_size},
            })
        return nodes

    def _build_edges(self, corr_matrix: pd.DataFrame) -> list:
        """Build React Flow edges from global correlation matrix."""
        edges = []
        seen = set()
        for c1 in CONCEPTS:
            for c2 in CONCEPTS:
                if c1 == c2:
                    continue
                pair = tuple(sorted([c1, c2]))
                if pair in seen:
                    continue
                seen.add(pair)
                weight = float(corr_matrix.loc[c1, c2])
                if weight < CORRELATION_THRESHOLD:
                    continue
                edges.append(self._make_edge(c1, c2, weight))
        return edges

    def _build_archetype_edges(self, corr_matrix: pd.DataFrame, strengths: dict) -> list:
        """
        Build edges weighted by: Pearson_correlation × mean(strength_c1, strength_c2).
        This emphasises relationships important to THIS archetype.
        """
        edges = []
        seen = set()
        for c1 in CONCEPTS:
            for c2 in CONCEPTS:
                if c1 == c2:
                    continue
                pair = tuple(sorted([c1, c2]))
                if pair in seen:
                    continue
                seen.add(pair)
                pearson = float(corr_matrix.loc[c1, c2])
                arch_weight = (strengths.get(c1, 0) + strengths.get(c2, 0)) / 2
                combined = round(pearson * arch_weight, 3)
                if combined < CORRELATION_THRESHOLD * 0.5:
                    continue
                edges.append(self._make_edge(c1, c2, combined, pearson=pearson))
        return edges

    def _build_contract_edges(self, corr_matrix: pd.DataFrame, strengths: dict) -> list:
        """
        Build edges for a specific contract based on ACTUAL contract data.
        Uses co-occurrence strength instead of global Pearson correlation.
        Edge weight = product of concept strengths (shows how strongly both appear together).
        """
        edges = []
        seen = set()

        # Baseline - concepts with NO clauses get 0.05
        BASELINE = 0.05

        # Debug counters
        pairs_checked = 0
        pairs_above_baseline = 0
        edges_created = 0

        for c1 in CONCEPTS:
            for c2 in CONCEPTS:
                if c1 == c2:
                    continue
                pair = tuple(sorted([c1, c2]))
                if pair in seen:
                    continue
                seen.add(pair)
                pairs_checked += 1

                # Get concept strengths from THIS contract
                s1 = strengths.get(c1, 0)
                s2 = strengths.get(c2, 0)

                # Only show edges if BOTH concepts are present (above baseline)
                if s1 <= BASELINE or s2 <= BASELINE:
                    continue

                pairs_above_baseline += 1

                # Compute edge weight based on THIS contract's data
                # Use product of strengths (co-occurrence intensity)
                co_occurrence = s1 * s2

                # Also factor in global Pearson correlation (archetype pattern knowledge)
                pearson = float(corr_matrix.loc[c1, c2])

                # Combine: co-occurrence strength + archetype pattern
                # If both concepts are strong AND archetypes show correlation, edge is very strong
                weighted = (co_occurrence * 0.7) + (pearson * 0.3)

                # Only show edges with meaningful weight
                if weighted >= 0.15:
                    edges_created += 1
                    edges.append(self._make_edge(c1, c2, weighted, pearson=co_occurrence))

        logger.info(f"[EDGE-BUILD] Checked {pairs_checked} pairs, {pairs_above_baseline} above baseline, {edges_created} edges created (contract-specific)")
        return edges

    def _make_edge(self, c1: str, c2: str, weight: float, pearson: float = None) -> dict:
        """Create a single React Flow edge."""
        thickness = max(1, int(weight * 8))
        animated = weight > 0.80
        return {
            "id": f"{c1}--{c2}",
            "source": c1,
            "target": c2,
            "label": str(round(weight, 2)),
            "animated": animated,
            "data": {
                "weight": round(weight, 3),
                "pearson": round(pearson, 3) if pearson is not None else round(weight, 3),
            },
            "style": {
                "strokeWidth": thickness,
                "stroke": "#60a5fa" if animated else "#4b5563",
                "opacity": max(0.3, weight),
            },
            "labelStyle": {"fill": "#e5e7eb", "fontSize": 10},
        }

    def _compute_stats(self, nodes: list, edges: list) -> dict:
        """Compute summary stats for the graph."""
        weights = [e["data"]["weight"] for e in edges]
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "avg_edge_weight": round(float(np.mean(weights)), 3) if weights else 0,
            "max_edge_weight": round(float(np.max(weights)), 3) if weights else 0,
            "strong_correlations": sum(1 for w in weights if w > 0.75),
        }

    # ------------------------------------------------------------------
    # Real Contract Data Extraction (Phase 2)
    # ------------------------------------------------------------------

    def extract_concept_scores_from_contract(self, contract_id: str) -> Dict[str, float]:
        """
        Extract concept strength scores from a real contract's clauses.

        Algorithm:
        1. Fetch all clauses for contract from MySQL
        2. Map clause types → concepts using CLAUSE_TO_CONCEPT_MAPPING
        3. Aggregate risk scores by concept (weighted average)
        4. Normalize to 0-1 range

        Args:
            contract_id: Contract UUID

        Returns:
            Dict of {concept_name: strength} for all 10 concepts
        """
        try:
            from core.models import Contract, Clause

            contract = Contract.objects.get(id=contract_id)
            clauses = Clause.objects.filter(contract=contract)

            clause_count = clauses.count()
            logger.info(f"[CONCEPT-EXTRACT] Contract {contract_id}: Found {clause_count} clauses")

            if not clauses.exists():
                logger.warning(f"[CONCEPT-EXTRACT] Contract {contract_id} has no clauses")
                return {concept: 0.1 for concept in CONCEPTS}

            # Accumulate risk scores by concept
            concept_scores = {concept: [] for concept in CONCEPTS}

            # Debug counters
            clauses_with_risk = 0
            clauses_mapped = 0
            clause_names_seen = set()

            for clause in clauses:
                clause_type = (clause.clause_type or "").lower().strip()
                clause_name = (clause.clause_name or "").lower().strip()

                # Compute clause strength from ACTUAL clause data
                if clause.risk_score is not None and clause.risk_score > 0:
                    risk_score = float(clause.risk_score)
                    clauses_with_risk += 1
                else:
                    # Use match_count, confidence, and text length for REAL differentiation
                    match_count = clause.match_count or 1
                    confidence = (clause.confidence or 50.0) / 100.0  # Normalize to 0-1
                    text_length = len(clause.extracted_text or "") if clause.extracted_text else 0

                    # Strength = match importance + confidence + text detail
                    match_strength = min(match_count / 5.0, 1.0)  # 5+ matches = max
                    text_strength = min(text_length / 500.0, 1.0)  # 500+ chars = max

                    risk_score = (match_strength * 0.5) + (confidence * 0.3) + (text_strength * 0.2)

                clause_names_seen.add(clause_name if clause_name else "NO_NAME")

                # Map clause to concepts
                matched_concepts = set()

                # Try exact match first
                if clause_type in CLAUSE_TO_CONCEPT_MAPPING:
                    matched_concepts.update(CLAUSE_TO_CONCEPT_MAPPING[clause_type])

                # Try partial match in clause type or name
                for key, concepts in CLAUSE_TO_CONCEPT_MAPPING.items():
                    if key in clause_type or key in clause_name:
                        matched_concepts.update(concepts)

                # If no match, skip (general clauses don't map to concepts)
                if not matched_concepts:
                    continue

                clauses_mapped += 1

                # Add risk score to matched concepts
                for concept in matched_concepts:
                    if concept in concept_scores:
                        concept_scores[concept].append(risk_score)

            # Log extraction stats
            logger.info(f"[CONCEPT-EXTRACT] Contract {contract_id}: {clauses_with_risk}/{clause_count} clauses have risk scores")
            logger.info(f"[CONCEPT-EXTRACT] Contract {contract_id}: {clauses_mapped}/{clause_count} clauses mapped to concepts")
            logger.info(f"[CONCEPT-EXTRACT] Contract {contract_id}: Clause names seen: {list(clause_names_seen)[:10]}")

            # Compute final strengths based on clause COUNT and risk scores
            final_strengths = {}
            max_clause_count = max([len(scores) for scores in concept_scores.values()]) if any(concept_scores.values()) else 1

            for concept in CONCEPTS:
                scores = concept_scores[concept]
                if scores:
                    # Strength = (clause count normalized) * (average risk score)
                    # This makes concepts with MORE clauses have higher strength
                    clause_count_normalized = len(scores) / max(max_clause_count, 1)
                    avg_risk = float(np.mean(scores))

                    # Combine: 60% count-based, 40% risk-based
                    final_strengths[concept] = round((clause_count_normalized * 0.6) + (avg_risk * 0.4), 3)
                else:
                    # No clauses mapped to this concept: low baseline
                    final_strengths[concept] = 0.05

            # Log concepts above baseline for debugging
            present_concepts = {k: v for k, v in final_strengths.items() if v > 0.05}
            logger.info(f"[CONCEPT-EXTRACT] Contract {contract_id}: {len(present_concepts)} concepts present - {present_concepts}")
            logger.info(f"[CONCEPT-EXTRACT] Contract {contract_id}: Clause counts per concept - {[(c, len(concept_scores[c])) for c in CONCEPTS if concept_scores[c]]}")
            return final_strengths

        except Exception as e:
            logger.error(f"[CONCEPT-EXTRACT] Extraction failed for {contract_id}: {e}", exc_info=True)
            return {concept: 0.0 for concept in CONCEPTS}

    def get_contract_concept_graph(self, contract_id: str) -> dict:
        """
        Get concept graph for a specific contract (extracted from real clauses).

        Returns React Flow compatible graph with:
        - Nodes: Concepts with extracted strengths
        - Edges: Correlations weighted by both node strengths

        Args:
            contract_id: Contract UUID

        Returns:
            Dict with nodes, edges, stats, and concept_strengths
        """
        try:
            from core.models import Contract

            contract = Contract.objects.get(id=contract_id)
            contract_type = contract.contract_type or "MSA"

            # Extract concept strengths from clauses
            concept_strengths = self.extract_concept_scores_from_contract(contract_id)

            # Store in Neo4j if available
            if self.neo4j_available and self.schema:
                try:
                    self.schema.create_contract_concept_profile(
                        contract_id=contract_id,
                        contract_type=contract_type,
                        concept_strengths=concept_strengths
                    )
                    logger.info(f"[CONCEPT-SERVICE] Stored contract {contract_id} in Neo4j")
                except Exception as e:
                    logger.warning(f"[CONCEPT-SERVICE] Failed to store in Neo4j: {e}")

            # Build React Flow graph
            nodes = self._build_nodes(concept_strengths, contract_type=f"Contract_{contract.original_filename}")
            # Build edges only between concepts present in THIS contract
            edges = self._build_contract_edges(self._corr_matrix, concept_strengths)

            return {
                "contract_id": str(contract_id),
                "contract_type": contract_type,
                "filename": contract.original_filename,
                "description": f"Concept graph extracted from {contract.original_filename}",
                "nodes": nodes,
                "edges": edges,
                "stats": self._compute_stats(nodes, edges),
                "concept_strengths": concept_strengths,
                "using_neo4j": self.neo4j_available,
            }

        except Exception as e:
            logger.error(f"[CONCEPT-SERVICE] get_contract_concept_graph failed: {e}", exc_info=True)
            raise ValueError(f"Failed to generate concept graph for contract {contract_id}: {str(e)}")

    def compare_contract_concepts(self, contract_id_1: str, contract_id_2: str) -> Dict[str, Any]:
        """
        Compare concept profiles between two contracts.

        Args:
            contract_id_1: First contract UUID
            contract_id_2: Second contract UUID

        Returns:
            Dict with concept differences and major changes
        """
        try:
            # Extract both concept profiles
            concepts_1 = self.extract_concept_scores_from_contract(contract_id_1)
            concepts_2 = self.extract_concept_scores_from_contract(contract_id_2)

            # Compute differences
            differences = {}
            for concept in CONCEPTS:
                c1_strength = concepts_1.get(concept, 0)
                c2_strength = concepts_2.get(concept, 0)
                diff = c2_strength - c1_strength

                differences[concept] = {
                    "contract_1_strength": round(c1_strength, 3),
                    "contract_2_strength": round(c2_strength, 3),
                    "difference": round(diff, 3),
                    "percent_change": round((diff / max(c1_strength, 0.01)) * 100, 1)
                }

            # Identify major shifts (threshold: 0.2 difference)
            major_increases = [c for c, d in differences.items() if d["difference"] > 0.2]
            major_decreases = [c for c, d in differences.items() if d["difference"] < -0.2]

            return {
                "contract_id_1": str(contract_id_1),
                "contract_id_2": str(contract_id_2),
                "concept_differences": differences,
                "major_increases": major_increases,
                "major_decreases": major_decreases,
                "summary": f"{len(major_increases)} concepts increased, {len(major_decreases)} decreased significantly",
            }

        except Exception as e:
            logger.error(f"[CONCEPT-COMPARE] Comparison failed: {e}", exc_info=True)
            raise ValueError(f"Failed to compare contracts: {str(e)}")

    # ------------------------------------------------------------------
    # Advanced Analytics (Phase 3)
    # ------------------------------------------------------------------

    def compute_concept_centrality(self, contract_type: str = "ALL") -> Dict[str, Any]:
        """
        Compute centrality metrics for concepts in the correlation graph.

        Metrics:
        - Degree Centrality: Number of strong correlations
        - Betweenness Centrality: Bridge between concept clusters
        - Eigenvector Centrality: Influence based on important connections

        Uses NetworkX algorithms on the correlation graph.

        Args:
            contract_type: Contract archetype (MSA/SaaS/NDA/Employment/EPC/ALL)

        Returns:
            Dict with centrality metrics and rankings
        """
        try:
            # Build NetworkX graph from correlation matrix
            G = nx.Graph()

            # Add nodes with strengths
            if contract_type == "ALL":
                strengths = self._concept_strengths
            else:
                if contract_type not in CONTRACT_ARCHETYPES:
                    raise ValueError(f"Unknown contract type: {contract_type}")
                strengths = dict(zip(CONCEPTS, CONTRACT_ARCHETYPES[contract_type]))

            for concept in CONCEPTS:
                G.add_node(concept, strength=strengths.get(concept, 0.5))

            # Add edges (correlations above threshold)
            seen = set()
            for c1 in CONCEPTS:
                for c2 in CONCEPTS:
                    if c1 == c2:
                        continue
                    pair = tuple(sorted([c1, c2]))
                    if pair in seen:
                        continue
                    seen.add(pair)

                    weight = float(self._corr_matrix.loc[c1, c2])
                    if weight >= CORRELATION_THRESHOLD:
                        G.add_edge(c1, c2, weight=weight)

            # Compute centrality metrics
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G, weight='weight')

            try:
                eigenvector_centrality = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
            except nx.PowerIterationFailedConvergence:
                logger.warning("[CONCEPT-CENTRALITY] Eigenvector centrality failed to converge, using degree as fallback")
                eigenvector_centrality = degree_centrality

            # Combine results
            centrality_results = {}
            for concept in CONCEPTS:
                centrality_results[concept] = {
                    "degree_centrality": round(degree_centrality.get(concept, 0.0), 3),
                    "betweenness_centrality": round(betweenness_centrality.get(concept, 0.0), 3),
                    "eigenvector_centrality": round(eigenvector_centrality.get(concept, 0.0), 3),
                    "strength": round(strengths.get(concept, 0.5), 3),
                }

            # Rank by eigenvector centrality (influence)
            ranked = sorted(
                centrality_results.items(),
                key=lambda x: x[1]["eigenvector_centrality"],
                reverse=True
            )

            return {
                "contract_type": contract_type,
                "centrality_metrics": centrality_results,
                "ranked_by_influence": [c[0] for c in ranked],
                "most_influential": ranked[0][0] if ranked else None,
                "graph_stats": {
                    "total_nodes": len(G.nodes),
                    "total_edges": len(G.edges),
                    "density": round(nx.density(G), 3),
                }
            }

        except Exception as e:
            logger.error(f"[CONCEPT-CENTRALITY] Computation failed: {e}", exc_info=True)
            return {"error": str(e)}

    def compute_contract_centrality(self, contract_id: str) -> Dict[str, Any]:
        """
        Compute centrality metrics for a SPECIFIC CONTRACT using its actual data.
        """
        try:
            from core.models import Contract

            contract = Contract.objects.get(id=contract_id)
            strengths = self.extract_concept_scores_from_contract(contract_id)

            # Build graph using THIS contract's data
            G = nx.Graph()
            BASELINE = 0.05

            for concept in CONCEPTS:
                G.add_node(concept, strength=strengths.get(concept, 0.05))

            # Add edges using contract-specific co-occurrence
            seen = set()
            for c1 in CONCEPTS:
                for c2 in CONCEPTS:
                    if c1 == c2:
                        continue
                    pair = tuple(sorted([c1, c2]))
                    if pair in seen:
                        continue
                    seen.add(pair)

                    s1 = strengths.get(c1, 0)
                    s2 = strengths.get(c2, 0)

                    if s1 <= BASELINE or s2 <= BASELINE:
                        continue

                    co_occurrence = s1 * s2
                    pearson = float(self._corr_matrix.loc[c1, c2])
                    weighted = (co_occurrence * 0.7) + (pearson * 0.3)

                    if weighted >= 0.15:
                        G.add_edge(c1, c2, weight=weighted)

            # Compute centrality
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G, weight='weight')

            try:
                eigenvector_centrality = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
            except:
                eigenvector_centrality = degree_centrality

            centrality_results = {}
            for concept in CONCEPTS:
                centrality_results[concept] = {
                    "degree_centrality": round(degree_centrality.get(concept, 0.0), 3),
                    "betweenness_centrality": round(betweenness_centrality.get(concept, 0.0), 3),
                    "eigenvector_centrality": round(eigenvector_centrality.get(concept, 0.0), 3),
                    "strength": round(strengths.get(concept, 0.05), 3),
                }

            ranked = sorted(
                centrality_results.items(),
                key=lambda x: x[1]["eigenvector_centrality"],
                reverse=True
            )

            return {
                "contract_id": str(contract_id),
                "contract_filename": contract.original_filename,
                "centrality_metrics": centrality_results,
                "ranked_by_influence": [c[0] for c in ranked],
                "most_influential": ranked[0][0] if ranked else None,
                "graph_stats": {
                    "total_nodes": len(G.nodes),
                    "total_edges": len(G.edges),
                    "density": round(nx.density(G), 3),
                }
            }

        except Exception as e:
            logger.error(f"[CONTRACT-CENTRALITY] Failed: {e}", exc_info=True)
            return {"error": str(e)}

    def detect_concept_communities(self, contract_type: str = "ALL") -> Dict[str, Any]:
        """
        Detect concept communities using Louvain algorithm.

        Identifies clusters of closely related concepts (e.g., "Risk cluster",
        "IP/Data cluster", "Termination cluster").

        Args:
            contract_type: Contract archetype (MSA/SaaS/NDA/Employment/EPC/ALL)

        Returns:
            Dict with communities, modularity score, and descriptions
        """
        try:
            from networkx.algorithms import community

            # Build graph
            G = nx.Graph()

            if contract_type == "ALL":
                strengths = self._concept_strengths
            else:
                if contract_type not in CONTRACT_ARCHETYPES:
                    raise ValueError(f"Unknown contract type: {contract_type}")
                strengths = dict(zip(CONCEPTS, CONTRACT_ARCHETYPES[contract_type]))

            for concept in CONCEPTS:
                G.add_node(concept, strength=strengths.get(concept, 0.5))

            seen = set()
            for c1 in CONCEPTS:
                for c2 in CONCEPTS:
                    if c1 == c2:
                        continue
                    pair = tuple(sorted([c1, c2]))
                    if pair in seen:
                        continue
                    seen.add(pair)

                    weight = float(self._corr_matrix.loc[c1, c2])
                    if weight >= CORRELATION_THRESHOLD:
                        G.add_edge(c1, c2, weight=weight)

            # Louvain community detection
            communities_generator = community.louvain_communities(G, weight='weight', seed=42)
            communities_list = list(communities_generator)

            # Format results
            communities_dict = {}
            for i, comm in enumerate(communities_list):
                community_name = f"Community_{i+1}"
                concepts_in_comm = list(comm)

                # Compute community characteristics
                avg_strength = float(np.mean([strengths.get(c, 0.5) for c in concepts_in_comm]))

                communities_dict[community_name] = {
                    "id": i + 1,
                    "concepts": concepts_in_comm,
                    "size": len(concepts_in_comm),
                    "avg_strength": round(avg_strength, 3),
                    "description": self._infer_community_description(concepts_in_comm)
                }

            # Compute modularity score
            modularity_score = community.modularity(G, communities_list, weight='weight')

            return {
                "contract_type": contract_type,
                "total_communities": len(communities_dict),
                "communities": communities_dict,
                "modularity_score": round(modularity_score, 3),
            }

        except Exception as e:
            logger.error(f"[CONCEPT-COMMUNITY] Detection failed: {e}", exc_info=True)
            return {"error": str(e)}

    def _infer_community_description(self, concepts: List[str]) -> str:
        """Infer human-readable community description from concepts"""
        concept_set = set(concepts)

        if {"Liability", "Indemnification", "Risk Allocation"}.issubset(concept_set):
            return "Risk & Liability Cluster"
        elif {"IP Rights", "Data Protection"}.issubset(concept_set):
            return "IP & Data Protection Cluster"
        elif {"Termination", "Penalty"}.issubset(concept_set):
            return "Exit & Penalties Cluster"
        elif {"Arbitration", "Obligations"}.issubset(concept_set):
            return "Dispute & Compliance Cluster"
        elif {"Force Majeure", "Risk Allocation"}.issubset(concept_set):
            return "External Risk Cluster"
        else:
            return f"Cluster: {', '.join(concepts[:3])}"

    # ------------------------------------------------------------------
    # Temporal Tracking (Phase 4 - Optional)
    # ------------------------------------------------------------------

    def track_concept_evolution(self, contract_id: str) -> Dict[str, Any]:
        """
        Track concept strength changes across contract versions.

        Requires ClauseVersion model to be populated.
        Returns time-series data showing how concept strengths evolved.

        Args:
            contract_id: Contract UUID

        Returns:
            Dict with evolution timeline and snapshots
        """
        try:
            from core.models import Contract
            from negotiation.models import ClauseVersion

            contract = Contract.objects.get(id=contract_id)

            # Get all clause versions for this contract (ordered by timestamp)
            versions = ClauseVersion.objects.filter(
                clause__contract=contract
            ).order_by('created_at')

            if not versions.exists():
                return {
                    "contract_id": str(contract_id),
                    "message": "No version history available",
                    "evolution_data": []
                }

            # Group versions by timestamp
            version_snapshots = {}
            for version in versions:
                timestamp = version.created_at.isoformat()
                if timestamp not in version_snapshots:
                    version_snapshots[timestamp] = []

                version_snapshots[timestamp].append({
                    "clause_type": version.clause.clause_type,
                    "clause_name": version.clause.clause_name,
                    "risk_score": float(version.clause.risk_score or 0.0),
                })

            # Compute concept strengths at each snapshot
            evolution_timeline = []
            for timestamp in sorted(version_snapshots.keys()):
                clauses = version_snapshots[timestamp]

                # Aggregate by concept (same logic as extract_concept_scores_from_contract)
                concept_scores = {concept: [] for concept in CONCEPTS}

                for clause in clauses:
                    clause_type = (clause["clause_type"] or "").lower().strip()
                    risk_score = clause["risk_score"]

                    if risk_score == 0.0:
                        continue

                    for key, concepts in CLAUSE_TO_CONCEPT_MAPPING.items():
                        if key in clause_type:
                            for concept in concepts:
                                if concept in concept_scores:
                                    concept_scores[concept].append(risk_score)

                strengths = {}
                for concept in CONCEPTS:
                    scores = concept_scores[concept]
                    strengths[concept] = round(float(np.mean(scores)), 3) if scores else 0.05

                evolution_timeline.append({
                    "timestamp": timestamp,
                    "concept_strengths": strengths
                })

            return {
                "contract_id": str(contract_id),
                "contract_filename": contract.original_filename,
                "total_snapshots": len(evolution_timeline),
                "evolution_data": evolution_timeline,
            }

        except Exception as e:
            logger.error(f"[CONCEPT-EVOLUTION] Tracking failed: {e}", exc_info=True)
            return {"error": str(e)}
