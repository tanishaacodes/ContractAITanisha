"""
Keyword-Based Risk Scoring Engine for Clause Library
=====================================================
Computes numerical risk scores based on keyword weights as specified in PDF requirements.

Keyword Weights (from PDF):
- liability: 5
- penalty: 4
- delay: 3
- termination: 5
- indemnity: 5

Additional high-risk keywords:
- breach, default, forfeiture, liquidated damages, etc.

Usage:
    scorer = get_risk_scorer()
    result = scorer.score("The Contractor shall be liable for any delay and may face penalties.")
    # Returns: {'score': 12, 'keywords': {'liability': 5, 'delay': 3, 'penalty': 4}, 'normalized_score': 0.8}
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class RiskKeywordScorer:
    """
    Scores contract clauses based on risk keyword detection with configurable weights.
    """

    # Risk keyword weights (from PDF specification)
    KEYWORD_WEIGHTS = {
        # Primary keywords from PDF
        'liability': 5,
        'liable': 5,
        'penalty': 4,
        'penalties': 4,
        'delay': 3,
        'delayed': 3,
        'delays': 3,
        'termination': 5,
        'terminate': 5,
        'indemnity': 5,
        'indemnification': 5,
        'indemnify': 5,

        # Additional high-risk keywords (weight 5)
        'breach': 5,
        'default': 5,
        'forfeiture': 5,
        'liquidated damages': 5,
        'damages': 4,
        'force majeure': 4,

        # Medium-risk keywords (weight 3-4)
        'failure': 3,
        'non-compliance': 3,
        'violation': 3,
        'risk': 3,
        'loss': 3,
        'damage': 3,
        'injury': 4,
        'harm': 3,
        'dispute': 3,
        'arbitration': 3,
        'litigation': 4,
        'claim': 3,

        # Financial risk keywords
        'fine': 4,
        'fee': 2,
        'deduction': 3,
        'withhold': 3,
        'suspension': 4,
        'cancellation': 4,

        # Time-based risk keywords
        'overrun': 3,
        'extension': 2,
        'acceleration': 2,

        # Performance risk keywords
        'defect': 3,
        'defective': 3,
        'rejection': 3,
        'non-performance': 4,
        'underperformance': 3,
    }

    # Maximum possible score for normalization
    MAX_NORMALIZED_SCORE = 1.0

    # Clause type risk modifiers (applied to final score)
    CLAUSE_TYPE_MODIFIERS = {
        'FORCE MAJEURE': 0.3,  # Protective - reduces risk by 70%
        'LIMITATION OF LIABILITY': 0.4,  # Caps liability - reduces risk
        'TERMINATION': 0.7,  # Can be risky but also protective
        'CONFIDENTIALITY': 0.6,  # Mutual obligation
        'INDEMNIFICATION': 1.3,  # High risk - increases by 30%
        'PAYMENT TERMS': 0.8,  # Moderate risk
        'LIQUIDATED DAMAGES': 1.2,  # High risk
        'NON-COMPETE': 1.1,  # Restrictive
        'INTELLECTUAL PROPERTY': 0.9,  # Depends on direction
        'GOVERNING LAW': 0.5,  # Procedural, not risky
        'DISPUTE RESOLUTION': 0.6,  # Procedural
        'ARBITRATION': 0.6,  # Procedural
    }

    def __init__(self, custom_weights: Dict[str, int] = None):
        """
        Initialize the risk keyword scorer.

        Args:
            custom_weights (Dict[str, int], optional): Custom keyword weights to override defaults
        """
        self.keyword_weights = self.KEYWORD_WEIGHTS.copy()
        if custom_weights:
            self.keyword_weights.update(custom_weights)

        logger.info(f"RiskKeywordScorer initialized with {len(self.keyword_weights)} keywords")

    def _detect_negations(self, text: str) -> float:
        """
        Detect negation patterns that REDUCE risk.
        Returns a multiplier (0.3 to 1.0) based on protective language.
        """
        text_lower = text.lower()

        # Strong negation patterns - reduce risk by 70%
        strong_negations = [
            r'shall not be liable',
            r'not liable for',
            r'shall not apply',
            r'does not apply',
            r'not responsible for',
            r'no liability',
            r'neither party shall be liable',
            r'excluded from liability',
            r'limitation of liability',
            r'limited to',
            r'capped at',
            r'maximum.*(?:of|not to exceed)',
        ]

        # Medium negation patterns - reduce risk by 40%
        medium_negations = [
            r'except',
            r'excluding',
            r'save for',
            r'other than',
            r'provided that',
            r'subject to',
            r'notwithstanding',
        ]

        # Protective patterns - reduce risk by 50%
        protective_patterns = [
            r'force majeure',
            r'acts? of god',
            r'beyond.*control',
            r'reasonable efforts',
            r'best efforts',
            r'commercially reasonable',
        ]

        multiplier = 1.0

        # Check for strong negations
        for pattern in strong_negations:
            if re.search(pattern, text_lower):
                multiplier = min(multiplier, 0.3)  # Reduce to 30%
                logger.debug(f"Strong negation found: {pattern}")
                break

        # Check for medium negations
        if multiplier > 0.5:
            for pattern in medium_negations:
                if re.search(pattern, text_lower):
                    multiplier = min(multiplier, 0.6)  # Reduce to 60%
                    break

        # Check for protective patterns
        if multiplier > 0.5:
            for pattern in protective_patterns:
                if re.search(pattern, text_lower):
                    multiplier = min(multiplier, 0.5)  # Reduce to 50%
                    break

        return multiplier

    def _get_clause_type_modifier(self, clause_name: str) -> float:
        """
        Get risk modifier based on clause type/name.
        """
        if not clause_name:
            return 1.0

        clause_upper = clause_name.upper()

        # Check for exact matches
        for clause_type, modifier in self.CLAUSE_TYPE_MODIFIERS.items():
            if clause_type in clause_upper:
                return modifier

        return 1.0

    def score(self, text: str, clause_name: str = None, sentence_type: str = None, party: str = None) -> Dict:
        """
        Context-aware risk scoring with negation detection and clause type modifiers.

        Args:
            text (str): The clause text to analyze
            clause_name (str): Name of the clause (e.g., "Force Majeure", "Indemnification")
            sentence_type (str): Type classification (RISK, OBLIGATION, RIGHT, etc.)
            party (str): Party attribution (CONTRACTOR, EMPLOYER, SHARED)

        Returns:
            Dict: {
                'score': int,  # Raw score (sum of keyword weights)
                'keywords': Dict[str, int],  # Detected keywords and their weights
                'normalized_score': float,  # Context-adjusted score (0-1)
                'risk_level': str,  # LOW, MEDIUM, or HIGH
                'adjustments': Dict  # Applied modifiers for transparency
            }
        """
        if not text or not text.strip():
            return {
                'score': 0,
                'keywords': {},
                'normalized_score': 0.0,
                'risk_level': 'LOW',
                'adjustments': {}
            }

        text_lower = text.lower().strip()
        detected_keywords = {}
        total_score = 0

        # Step 1: Detect keywords (unchanged)
        for keyword, weight in self.keyword_weights.items():
            pattern = r'\b' + re.escape(keyword) + r'(?:s|es|ed|ing)?\b'
            if re.search(pattern, text_lower):
                detected_keywords[keyword] = weight
                total_score += weight

        # Step 2: Calculate base normalized score
        base_normalized = min(total_score / 50.0, 1.0)

        # Step 3: Apply context-aware adjustments
        adjustments = {}

        # 3a. Detect negations and protective language
        negation_multiplier = self._detect_negations(text)
        if negation_multiplier < 1.0:
            adjustments['negation'] = negation_multiplier

        # 3b. Apply clause type modifier
        clause_modifier = self._get_clause_type_modifier(clause_name)
        if clause_modifier != 1.0:
            adjustments['clause_type'] = clause_modifier

        # 3c. Apply sentence type modifier
        sentence_modifier = 1.0
        if sentence_type == 'RIGHT':
            sentence_modifier = 0.5  # Rights are protective
            adjustments['sentence_type'] = sentence_modifier
        elif sentence_type == 'RISK':
            sentence_modifier = 1.2  # Risk clauses are riskier
            adjustments['sentence_type'] = sentence_modifier
        elif sentence_type == 'DEFINITION':
            sentence_modifier = 0.4  # Definitions rarely risky
            adjustments['sentence_type'] = sentence_modifier

        # 3d. Apply party attribution modifier
        party_modifier = 1.0
        if party == 'CONTRACTOR':
            party_modifier = 1.1  # Contractor obligations are riskier
            adjustments['party'] = party_modifier
        elif party == 'EMPLOYER':
            party_modifier = 0.7  # Employer obligations favor us
            adjustments['party'] = party_modifier

        # Step 4: Calculate final adjusted score
        adjusted_score = base_normalized * negation_multiplier * clause_modifier * sentence_modifier * party_modifier
        normalized_score = min(adjusted_score, 1.0)

        # Step 5: Determine risk level
        if normalized_score >= 0.6:
            risk_level = 'HIGH'
        elif normalized_score >= 0.3:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        result = {
            'score': total_score,
            'keywords': detected_keywords,
            'normalized_score': round(normalized_score, 3),
            'risk_level': risk_level,
            'adjustments': adjustments
        }

        if adjustments:
            logger.debug(f"Scored '{clause_name or text[:30]}' - Base: {round(base_normalized, 2)} → Adjusted: {round(normalized_score, 2)} (Risk: {risk_level}) - Adjustments: {adjustments}")
        else:
            logger.debug(f"Scored '{clause_name or text[:30]}' - Score: {total_score}, Risk: {risk_level}")

        return result

    def score_batch(self, texts: List[str]) -> List[Dict]:
        """
        Score multiple clauses in batch.

        Args:
            texts (List[str]): List of clause texts

        Returns:
            List[Dict]: List of scoring results
        """
        return [self.score(text) for text in texts]

    def get_top_risk_keywords(self, text: str, top_n: int = 5) -> List[Tuple[str, int]]:
        """
        Get top N risk keywords found in the text.

        Args:
            text (str): The clause text
            top_n (int): Number of top keywords to return

        Returns:
            List[Tuple[str, int]]: List of (keyword, weight) tuples, sorted by weight
        """
        result = self.score(text)
        keywords = result['keywords']

        # Sort by weight (descending)
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        return sorted_keywords[:top_n]

    def calculate_financial_impact(
        self,
        risk_score: float,
        multiplier: float = 100000.0,
        currency: str = '₹'
    ) -> Dict:
        """
        Calculate financial impact based on risk score.

        From PDF: financial_impact = risk_score × ₹100,000

        Args:
            risk_score (float): Normalized risk score (0-1)
            multiplier (float): Multiplier value (default: 100,000)
            currency (str): Currency symbol (default: ₹)

        Returns:
            Dict: {
                'amount': float,
                'formatted': str,
                'currency': str
            }
        """
        amount = risk_score * multiplier

        return {
            'amount': round(amount, 2),
            'formatted': f'{currency}{amount:,.2f}',
            'currency': currency
        }

    def get_risk_breakdown(self, text: str) -> Dict:
        """
        Get detailed risk breakdown with keyword contributions (RRIE Explainability Feature).

        This method provides transparency into why a clause is risky by showing:
        - Which keywords were detected
        - How much each keyword contributes to the total risk score
        - Overall risk assessment

        Args:
            text (str): The clause text to analyze

        Returns:
            Dict: {
                'success': bool,
                'total_score': int,
                'normalized_score': float,
                'risk_level': str,  # LOW/MEDIUM/HIGH
                'keyword_contributions': List[Dict],  # [{keyword, weight}]
                'financial_impact': Dict,  # {amount, formatted}
                'explanation': str
            }

        Example:
            >>> scorer = get_risk_scorer()
            >>> breakdown = scorer.get_risk_breakdown("Contractor is liable for penalties and delays")
            >>> print(breakdown)
            {
                'success': True,
                'total_score': 12,
                'normalized_score': 0.4,
                'risk_level': 'MEDIUM',
                'keyword_contributions': [
                    {'keyword': 'liable', 'weight': 5, 'contribution_pct': 41.7},
                    {'keyword': 'penalty', 'weight': 4, 'contribution_pct': 33.3},
                    {'keyword': 'delay', 'weight': 3, 'contribution_pct': 25.0}
                ],
                'financial_impact': {...},
                'explanation': 'Risk driven by liability (41.7%), penalties (33.3%), and delays (25.0%)'
            }
        """
        if not text or not text.strip():
            return {
                'success': True,
                'total_score': 0,
                'normalized_score': 0.0,
                'risk_level': 'LOW',
                'keyword_contributions': [],
                'financial_impact': {'amount': 0.0, 'formatted': '₹0.00'},
                'explanation': 'No risk keywords detected'
            }

        # Get scoring result
        score_result = self.score(text)

        # Build keyword contributions list with percentage contribution
        keyword_contributions = []
        total_score = score_result['score']

        for keyword, weight in sorted(score_result['keywords'].items(), key=lambda x: x[1], reverse=True):
            contribution_pct = (weight / total_score * 100) if total_score > 0 else 0

            keyword_contributions.append({
                'keyword': keyword,
                'weight': weight,
                'contribution_pct': round(contribution_pct, 1)
            })

        # Calculate financial impact
        financial_impact = self.calculate_financial_impact(score_result['normalized_score'])

        # Generate human-readable explanation
        if keyword_contributions:
            top_contributors = keyword_contributions[:3]  # Top 3 keywords
            explanation_parts = [
                f"{kw['keyword']} ({kw['contribution_pct']}%)"
                for kw in top_contributors
            ]
            explanation = f"Risk driven by {', '.join(explanation_parts)}"
        else:
            explanation = "No significant risk keywords detected"

        return {
            'success': True,
            'total_score': total_score,
            'normalized_score': score_result['normalized_score'],
            'risk_level': score_result['risk_level'],
            'keyword_contributions': keyword_contributions,
            'financial_impact': financial_impact,
            'explanation': explanation
        }


# Singleton instance
_scorer_instance: Optional[RiskKeywordScorer] = None


@lru_cache(maxsize=1)
def get_risk_scorer() -> RiskKeywordScorer:
    """
    Get singleton instance of risk keyword scorer.

    Returns:
        RiskKeywordScorer: The scorer instance
    """
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = RiskKeywordScorer()
    return _scorer_instance


# Convenience functions
def score_risk(text: str) -> Dict:
    """
    Quick risk scoring for a single clause.

    Args:
        text (str): Clause text

    Returns:
        Dict: Scoring result
    """
    scorer = get_risk_scorer()
    return scorer.score(text)


def calculate_financial_impact(risk_score: float) -> float:
    """
    Calculate financial impact from risk score.

    Args:
        risk_score (float): Normalized risk score (0-1)

    Returns:
        float: Financial impact in currency units
    """
    scorer = get_risk_scorer()
    result = scorer.calculate_financial_impact(risk_score)
    return result['amount']
