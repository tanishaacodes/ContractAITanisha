"""
Clause Health Scoring Engine
Computes health metrics based on real-world outcomes
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q


class ClauseHealthScorer:
    """
    Calculate health scores for clauses based on:
    - Success rate (positive outcomes vs negative)
    - Usage frequency
    - Enforceability (litigation outcomes)
    - Negotiation difficulty
    """

    # Scoring weights (customizable)
    WEIGHTS = {
        'success_rate': 0.40,
        'enforceability': 0.30,
        'negotiation': 0.20,
        'usage': 0.10
    }

    # Status thresholds
    THRESHOLDS = {
        'ALIVE': 0.75,  # Health score > 0.75
        'WEAK': 0.45,   # Health score 0.45-0.75
        'RETIRED': 0.45 # Health score < 0.45
    }

    def __init__(self):
        pass

    def calculate_success_rate(self, events: List) -> float:
        """
        Calculate success rate from clause events
        EXECUTED/RENEWED = positive (outcome_score = 1.0)
        DISPUTED/LITIGATED = negative (outcome_score = 0.0-0.5)

        Args:
            events: List of ClauseEvent objects

        Returns:
            Success rate (0-1)
        """
        if not events:
            return 0.5  # Neutral for new clauses

        # Calculate average outcome score
        total_score = sum(e.outcome_score for e in events)
        avg_score = total_score / len(events)

        return max(0.0, min(1.0, avg_score))

    def calculate_enforceability(self, events: List) -> float:
        """
        Calculate enforceability score from litigation outcomes
        Based on LITIGATED events and their outcomes

        Args:
            events: List of ClauseEvent objects

        Returns:
            Enforceability score (0-1)
        """
        litigated = [e for e in events if e.event_type == 'LITIGATED']

        if not litigated:
            return 0.8  # Assume good until tested

        # Count wins vs losses
        wins = sum(1 for e in litigated if e.outcome_score >= 0.7)
        total = len(litigated)

        return wins / total if total > 0 else 0.5

    def calculate_negotiation_score(self, events: List) -> float:
        """
        Calculate negotiation difficulty score
        Lower disputes = easier negotiations

        Args:
            events: List of ClauseEvent objects

        Returns:
            Negotiation score (0-1), higher = easier
        """
        if not events:
            return 0.5  # Neutral

        disputes = [e for e in events if e.event_type == 'DISPUTED']
        total = len(events)

        # Calculate dispute rate
        dispute_rate = len(disputes) / total if total > 0 else 0

        # Invert: fewer disputes = higher score
        return 1.0 - min(dispute_rate * 2, 1.0)

    def calculate_usage_score(self, usage_count: int, max_usage: int = 100) -> float:
        """
        Calculate usage score
        More usage = more confidence in the clause

        Args:
            usage_count: Number of times clause was used
            max_usage: Maximum expected usage for normalization

        Returns:
            Usage score (0-1)
        """
        return min(usage_count / max_usage, 1.0)

    def compute_health(self, events: List, usage_count: int = 0) -> Dict[str, float]:
        """
        Compute comprehensive health metrics

        Args:
            events: List of ClauseEvent objects
            usage_count: Total usage count

        Returns:
            Dict with all health metrics and composite score
        """
        # Calculate component scores
        success_rate = self.calculate_success_rate(events)
        enforceability = self.calculate_enforceability(events)
        negotiation = self.calculate_negotiation_score(events)
        usage_score = self.calculate_usage_score(usage_count)

        # Calculate composite health score
        health_score = (
            self.WEIGHTS['success_rate'] * success_rate +
            self.WEIGHTS['enforceability'] * enforceability +
            self.WEIGHTS['negotiation'] * negotiation +
            self.WEIGHTS['usage'] * usage_score
        )

        return {
            'success_rate': round(success_rate, 3),
            'enforceability_score': round(enforceability, 3),
            'negotiation_score': round(negotiation, 3),
            'usage_score': round(usage_score, 3),
            'health_score': round(health_score, 3)
        }

    def determine_status(self, health_score: float) -> str:
        """
        Determine clause status based on health score

        Args:
            health_score: Composite health score (0-1)

        Returns:
            Status string: 'ALIVE', 'WEAK', or 'RETIRED'
        """
        if health_score >= self.THRESHOLDS['ALIVE']:
            return 'ALIVE'
        elif health_score >= self.THRESHOLDS['WEAK']:
            return 'WEAK'
        else:
            return 'RETIRED'

    def should_promote(self, clause_metrics: Dict, sibling_metrics: List[Dict]) -> Tuple[bool, str]:
        """
        Determine if a clause version should be auto-promoted

        Args:
            clause_metrics: Health metrics of candidate clause
            sibling_metrics: Health metrics of sibling versions

        Returns:
            Tuple of (should_promote: bool, reason: str)
        """
        candidate_score = clause_metrics.get('health_score', 0)
        candidate_success = clause_metrics.get('success_rate', 0)

        # Must be ALIVE status
        if candidate_score < self.THRESHOLDS['ALIVE']:
            return False, "Health score below promotion threshold"

        # Must have sufficient usage (at least 3 events = 0.03 score)
        if clause_metrics.get('usage_score', 0) < 0.03:
            return False, "Insufficient usage data"

        # Must outperform siblings
        if sibling_metrics:
            max_sibling_score = max(m.get('health_score', 0) for m in sibling_metrics)
            if candidate_score <= max_sibling_score:
                return False, "Not best performing version"

        # Success rate must be high
        if candidate_success < 0.8:
            return False, f"Success rate too low: {candidate_success:.1%}"

        # All checks passed
        reason = (
            f"Auto-promoted: Health {candidate_score:.2f}, "
            f"Success {candidate_success:.1%}, "
            f"Outperforms {len(sibling_metrics)} sibling versions"
        )

        return True, reason

    def should_retire(self, clause_metrics: Dict, age_days: int = None) -> Tuple[bool, str]:
        """
        Determine if a clause should be auto-retired

        Args:
            clause_metrics: Health metrics of the clause
            age_days: Age of the clause in days

        Returns:
            Tuple of (should_retire: bool, reason: str)
        """
        health_score = clause_metrics.get('health_score', 0.5)
        success_rate = clause_metrics.get('success_rate', 0.5)

        # Low health score
        if health_score < self.THRESHOLDS['RETIRED']:
            return True, f"Health score critical: {health_score:.2f}"

        # Very low success rate
        if success_rate < 0.3:
            return True, f"Success rate critical: {success_rate:.1%}"

        # Old and unused
        if age_days and age_days > 365 and clause_metrics.get('usage_score', 0) < 0.05:
            return True, f"Obsolete: {age_days} days old with minimal usage"

        return False, "Clause is active"

    def analyze_degradation(self, historical_metrics: List[Dict]) -> Dict:
        """
        Analyze clause degradation over time

        Args:
            historical_metrics: List of metrics over time (ordered by date)

        Returns:
            Analysis dict with trend and warnings
        """
        if len(historical_metrics) < 2:
            return {'trend': 'stable', 'warning': None}

        # Calculate trend
        scores = [m['health_score'] for m in historical_metrics]
        recent_avg = sum(scores[-3:]) / min(len(scores[-3:]), 3)
        older_avg = sum(scores[:3]) / min(len(scores[:3]), 3)

        change = recent_avg - older_avg

        if change < -0.15:
            trend = 'declining'
            warning = f"Clause health declining: {change:.1%} drop"
        elif change > 0.15:
            trend = 'improving'
            warning = None
        else:
            trend = 'stable'
            warning = None

        return {
            'trend': trend,
            'change': round(change, 3),
            'warning': warning
        }


# Singleton instance
_health_scorer = None


def get_health_scorer() -> ClauseHealthScorer:
    """Get or create singleton health scorer"""
    global _health_scorer
    if _health_scorer is None:
        _health_scorer = ClauseHealthScorer()
    return _health_scorer
