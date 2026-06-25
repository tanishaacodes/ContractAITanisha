"""
Financial Exposure Engine
===========================
Calculates monetary exposure from contract risk using graph-aware metrics.

Features:
1. Clause-level exposure calculation
2. Graph-aware interaction multipliers
3. Contract value parsing (Crores, Lakhs, USD, AED)
4. Before vs After exposure deltas
5. CFO-grade explainable metrics

Exposure Formula:
    Exposure = Base Amount x Risk Score x Obligation Multiplier x Interaction Multiplier

This converts risk scores into rupees/dollars for executive decision-making.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx

try:
    from .currency_converter import get_converter
    HAS_CURRENCY_CONVERTER = True
except ImportError:
    HAS_CURRENCY_CONVERTER = False

logger = logging.getLogger(__name__)


class ExposureEngine:
    """
    Converts graph-based risk into monetary exposure.

    Makes numbers explainable and auditable for CFO/CRO discussions.
    """

    # Default multipliers for obligation types
    OBLIGATION_MULTIPLIERS = {
        "indemnity": 1.0,
        "liability": 0.8,
        "limitation": 0.5,
        "termination": 0.3,
        "payment": 0.6,
        "sla": 0.4,
        "penalty": 0.5,
        "warranty": 0.4,
        "confidentiality": 0.2,
        "insurance": 0.3,
        "force_majeure": 0.2,
        "dispute": 0.2,
        "general": 0.25,
    }

    def __init__(self):
        pass

    def parse_contract_value(self, value_str: str) -> float:
        """
        Parse contract value string into a numeric amount in INR.

        Supports:
        - "10 Crore", "10Cr", "1000000000"
        - "50 Lakhs", "50L"
        - "1,000,000"
        - "$1M", "$1,000,000"
        - "AED 1,000,000"

        Returns:
            float: Value in INR (assumes 1 USD = 83 INR, 1 AED = 22.6 INR)
        """
        if not value_str:
            return 0.0

        value_str = str(value_str).strip().upper()

        # Remove currency symbols and commas
        clean_str = value_str.replace(',', '').replace(' ', '')

        # Handle Crore/Cr
        if 'CRORE' in clean_str or 'CR' in clean_str:
            num = re.findall(r'[\d.]+', clean_str)
            if num:
                return float(num[0]) * 10_000_000  # 1 Crore = 10 Million

        # Handle Lakh/L
        if 'LAKH' in clean_str or clean_str.endswith('L'):
            num = re.findall(r'[\d.]+', clean_str)
            if num:
                return float(num[0]) * 100_000  # 1 Lakh = 100,000

        # Handle Million/M
        if clean_str.endswith('M') or 'MILLION' in clean_str:
            num = re.findall(r'[\d.]+', clean_str)
            if num:
                return float(num[0]) * 1_000_000

        # Handle USD
        if '$' in value_str or 'USD' in clean_str:
            num = re.findall(r'[\d.]+', clean_str)
            if num:
                return float(num[0]) * 83  # USD to INR

        # Handle AED
        if 'AED' in clean_str:
            num = re.findall(r'[\d.]+', clean_str)
            if num:
                return float(num[0]) * 22.6  # AED to INR

        # Plain number
        num = re.findall(r'[\d.]+', clean_str)
        if num:
            return float(num[0])

        return 0.0

    def clause_base_amount(
        self,
        clause_text: str,
        clause_type: str,
        contract_value: float
    ) -> float:
        """
        Estimate base financial exposure of a clause.

        Args:
            clause_text: Full clause text
            clause_type: Clause type/category
            contract_value: Total contract value in INR

        Returns:
            Base exposure amount
        """
        text = clause_text.lower() if clause_text else ""
        clause_type = (clause_type or "general").lower()

        # Match based on clause content and type
        if "indemnity" in text or "indemnif" in clause_type:
            return contract_value * 1.0  # Full contract value at risk

        if "limitation of liability" in text or "limit" in clause_type:
            return contract_value * 0.5

        if "termination" in text or "terminat" in clause_type:
            return contract_value * 0.3

        if "sla" in text or "service level" in text or "penalty" in text:
            return contract_value * 0.2

        if "payment" in text or "payment" in clause_type:
            return contract_value * 0.4

        if "warranty" in text or "warrant" in clause_type:
            return contract_value * 0.25

        if "insurance" in text or "insurance" in clause_type:
            return contract_value * 0.15

        if "confidential" in text or "nda" in clause_type:
            return contract_value * 0.1

        # Default: 10% of contract value
        return contract_value * 0.1

    def interaction_multiplier(self, graph: nx.DiGraph, node_id: Any) -> float:
        """
        Calculate exposure multiplier based on graph connectivity.

        High-degree clauses have more potential cascading impact.

        Args:
            graph: NetworkX DiGraph
            node_id: Clause node ID

        Returns:
            Multiplier (1.0 to ~2.0)
        """
        if node_id not in graph:
            return 1.0

        in_degree = graph.in_degree(node_id)
        out_degree = graph.out_degree(node_id)
        total_degree = in_degree + out_degree

        # Scale: each connection adds 15% exposure amplification
        return 1 + (total_degree * 0.15)

    def calculate_clause_exposure(
        self,
        clause: Any,
        graph: nx.DiGraph,
        contract_value: float
    ) -> Dict[str, Any]:
        """
        Calculate exposure for a single clause.

        Args:
            clause: Clause model instance or dict
            graph: NetworkX graph
            contract_value: Total contract value

        Returns:
            Dict with exposure details
        """
        # Handle both model instances and dicts
        if hasattr(clause, 'id'):
            clause_id = clause.id
            # Try multiple text fields
            clause_text = (
                getattr(clause, 'extracted_text', '') or
                getattr(clause, 'context_sentences', '') or
                getattr(clause, 'text_spans', '') or
                ''
            )
            clause_type = getattr(clause, 'clause_type', None) or getattr(clause, 'clause_name', 'general') or 'general'
            risk_score = float(getattr(clause, 'risk_score', 0) or 0)
        else:
            clause_id = clause.get('id')
            clause_text = (
                clause.get('extracted_text', '') or
                clause.get('context_sentences', '') or
                clause.get('text_spans', '') or
                ''
            )
            clause_type = clause.get('clause_type') or clause.get('clause_name', 'general')
            risk_score = float(clause.get('risk_score', 0) or 0)

        # Prefer graph-node values: the graph builder already infers risk_score
        # and normalises clause_type for nodes where the DB fields are NULL.
        if graph is not None and clause_id in graph.nodes:
            node_data = graph.nodes[clause_id]
            risk_score = float(node_data.get('risk_score', risk_score) or risk_score)
            clause_type = node_data.get('clause_type', clause_type) or clause_type

        # Calculate components
        base = self.clause_base_amount(clause_text, clause_type, contract_value)
        interaction = self.interaction_multiplier(graph, clause_id)

        # Obligation multiplier based on clause type
        obligation_mult = self.OBLIGATION_MULTIPLIERS.get(
            clause_type.lower(), 0.25
        )

        # Final exposure
        exposure = base * risk_score * interaction * obligation_mult

        return {
            "clause_id": str(clause_id),
            "clause_type": clause_type,
            "risk_score": round(risk_score, 3),
            "exposure": round(exposure, 2),
            "components": {
                "base_amount": round(base, 2),
                "risk_score": round(risk_score, 3),
                "interaction_multiplier": round(interaction, 3),
                "obligation_multiplier": obligation_mult
            }
        }

    def calculate_total_exposure(
        self,
        clauses: List[Any],
        graph: nx.DiGraph,
        contract_value: float
    ) -> Tuple[float, List[Dict]]:
        """
        Calculate total contract exposure across all clauses.

        Args:
            clauses: List of Clause instances
            graph: NetworkX graph
            contract_value: Total contract value

        Returns:
            Tuple of (total_exposure, breakdown_list)
        """
        total = 0.0
        breakdown = []

        for clause in clauses:
            clause_exposure = self.calculate_clause_exposure(
                clause, graph, contract_value
            )
            total += clause_exposure['exposure']
            breakdown.append(clause_exposure)

        # Sort by exposure (highest first)
        breakdown.sort(key=lambda x: x['exposure'], reverse=True)

        return round(total, 2), breakdown

    def calculate_exposure_by_type(
        self,
        clauses: List[Any],
        graph: nx.DiGraph,
        contract_value: float
    ) -> Dict[str, float]:
        """
        Calculate exposure grouped by clause type.

        Returns:
            Dict mapping clause_type -> total_exposure
        """
        by_type = {}

        for clause in clauses:
            clause_exposure = self.calculate_clause_exposure(
                clause, graph, contract_value
            )
            clause_type = clause_exposure['clause_type']
            exposure = clause_exposure['exposure']

            by_type[clause_type] = by_type.get(clause_type, 0) + exposure

        # Sort by exposure
        sorted_types = dict(
            sorted(by_type.items(), key=lambda x: x[1], reverse=True)
        )

        return {k: round(v, 2) for k, v in sorted_types.items()}

    def get_exposure_hotspots(
        self,
        clauses: List[Any],
        graph: nx.DiGraph,
        contract_value: float,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Get top N clauses by exposure.

        Returns:
            List of top exposure clauses with details
        """
        _, breakdown = self.calculate_total_exposure(
            clauses, graph, contract_value
        )
        return breakdown[:top_n]

    def calculate_exposure_delta(
        self,
        original_clauses: List[Any],
        remaining_clauses: List[Any],
        original_graph: nx.DiGraph,
        simulated_graph: nx.DiGraph,
        contract_value: float
    ) -> Dict[str, Any]:
        """
        Calculate exposure change after clause modification.

        Args:
            original_clauses: All clauses before modification
            remaining_clauses: Clauses after modification
            original_graph: Graph before modification
            simulated_graph: Graph after modification
            contract_value: Total contract value

        Returns:
            Dict with before/after exposure comparison
        """
        exposure_before, breakdown_before = self.calculate_total_exposure(
            original_clauses, original_graph, contract_value
        )

        exposure_after, breakdown_after = self.calculate_total_exposure(
            remaining_clauses, simulated_graph, contract_value
        )

        delta = exposure_before - exposure_after
        reduction_pct = (delta / exposure_before * 100) if exposure_before > 0 else 0

        return {
            "currency": "INR",
            "exposure": {
                "before": exposure_before,
                "after": exposure_after,
                "delta": round(delta, 2),
                "reduction_pct": round(reduction_pct, 1)
            },
            "breakdown": {
                "before": breakdown_before[:10],  # Top 10
                "after": breakdown_after[:10]
            }
        }

    def format_currency(self, amount: float, currency: str = "INR") -> str:
        """
        Format amount as human-readable currency string.

        Args:
            amount: Amount in base currency
            currency: Currency code

        Returns:
            Formatted string (e.g., "₹10.5 Cr", "$1.2M")
        """
        if HAS_CURRENCY_CONVERTER:
            converter = get_converter()
            return converter.format_amount(amount, currency, include_symbol=True)

        # Fallback formatting
        if currency == "INR":
            if amount >= 10_000_000:
                return f"₹{amount / 10_000_000:.1f} Cr"
            elif amount >= 100_000:
                return f"₹{amount / 100_000:.1f} L"
            else:
                return f"₹{amount:,.0f}"
        else:
            if amount >= 1_000_000:
                return f"${amount / 1_000_000:.1f}M"
            else:
                return f"${amount:,.0f}"

    def convert_exposure(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Convert exposure amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Converted amount
        """
        if not HAS_CURRENCY_CONVERTER:
            logger.warning("Currency converter not available, returning original amount")
            return amount

        converter = get_converter()
        return converter.convert(amount, from_currency, to_currency)


# Convenience functions
def calculate_total_exposure(
    clauses: List[Any],
    graph: nx.DiGraph,
    contract_value: float
) -> Tuple[float, List[Dict]]:
    """Calculate total contract exposure"""
    engine = ExposureEngine()
    return engine.calculate_total_exposure(clauses, graph, contract_value)


def calculate_exposure_delta(
    original_clauses: List[Any],
    remaining_clauses: List[Any],
    original_graph: nx.DiGraph,
    simulated_graph: nx.DiGraph,
    contract_value: float
) -> Dict[str, Any]:
    """Calculate exposure change after modification"""
    engine = ExposureEngine()
    return engine.calculate_exposure_delta(
        original_clauses, remaining_clauses,
        original_graph, simulated_graph,
        contract_value
    )


def parse_contract_value(value_str: str) -> float:
    """Parse contract value string to numeric"""
    engine = ExposureEngine()
    return engine.parse_contract_value(value_str)
