"""
Geopolitical Inference Engine
Analyzes geopolitical tensions, conflict escalation, and diplomatic stability
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class GeopoliticalEvent:
    """Geopolitical event data"""
    event_id: str
    event_type: str  # diplomatic_tension, military_buildup, sanctions, treaty, alliance
    countries_involved: List[str]
    severity: float  # 0-1
    date: datetime
    escalation_potential: float  # 0-1
    regional_impact: List[str]


@dataclass
class ConflictRisk:
    """Conflict risk assessment"""
    region: str
    conflict_probability: float
    escalation_trajectory: str  # escalating, stable, de-escalating
    key_actors: List[str]
    flashpoints: List[str]
    time_horizon_days: int


class GeopoliticalInferenceEngine:
    """Engine for analyzing geopolitical risks and conflict escalation"""

    def __init__(self):
        self.conflict_indicators = {}
        self.regional_tensions = {}
        self._initialize_indicators()

    def _initialize_indicators(self):
        """Initialize geopolitical conflict indicators"""

        # Define key conflict indicators and their weights
        self.conflict_indicators = {
            'military_buildup': {
                'weight': 0.25,
                'description': 'Troop movements, military exercises, deployments'
            },
            'diplomatic_breakdown': {
                'weight': 0.20,
                'description': 'Embassy closures, ambassador recalls, dialogue cessation'
            },
            'economic_sanctions': {
                'weight': 0.15,
                'description': 'Trade restrictions, financial sanctions, embargoes'
            },
            'territorial_disputes': {
                'weight': 0.15,
                'description': 'Border conflicts, territorial claims, maritime disputes'
            },
            'proxy_conflicts': {
                'weight': 0.10,
                'description': 'Support for opposing factions, indirect military engagement'
            },
            'cyber_warfare': {
                'weight': 0.08,
                'description': 'State-sponsored cyber attacks, infrastructure hacking'
            },
            'information_warfare': {
                'weight': 0.07,
                'description': 'Propaganda campaigns, disinformation, media warfare'
            }
        }

        # Current regional tensions (simplified model)
        self.regional_tensions = {
            'Eastern Europe': {
                'base_risk': 0.75,
                'primary_actors': ['Russia', 'Ukraine', 'NATO'],
                'key_issues': ['territorial integrity', 'NATO expansion', 'energy security'],
                'escalation_triggers': ['NATO troop movements', 'energy cutoffs', 'territorial changes']
            },
            'Middle East': {
                'base_risk': 0.70,
                'primary_actors': ['Iran', 'Israel', 'Saudi Arabia', 'USA'],
                'key_issues': ['nuclear program', 'regional hegemony', 'proxy conflicts'],
                'escalation_triggers': ['nuclear developments', 'direct military engagement', 'oil disruption']
            },
            'East Asia': {
                'base_risk': 0.60,
                'primary_actors': ['China', 'Taiwan', 'USA', 'Japan'],
                'key_issues': ['Taiwan sovereignty', 'South China Sea', 'trade competition'],
                'escalation_triggers': ['Taiwan independence moves', 'military incidents', 'economic decoupling']
            },
            'South Asia': {
                'base_risk': 0.55,
                'primary_actors': ['India', 'Pakistan', 'China'],
                'key_issues': ['Kashmir', 'border disputes', 'water resources'],
                'escalation_triggers': ['terrorist attacks', 'border skirmishes', 'nuclear posturing']
            },
            'Korean Peninsula': {
                'base_risk': 0.65,
                'primary_actors': ['North Korea', 'South Korea', 'USA', 'China'],
                'key_issues': ['nuclear weapons', 'regime stability', 'reunification'],
                'escalation_triggers': ['nuclear tests', 'missile launches', 'regime collapse']
            },
            'Africa': {
                'base_risk': 0.50,
                'primary_actors': ['Various states', 'Regional powers'],
                'key_issues': ['resource conflicts', 'ethnic tensions', 'state fragility'],
                'escalation_triggers': ['coups', 'ethnic violence', 'resource competition']
            }
        }

    def analyze_geopolitical_risk(
        self,
        region: str,
        project_location: Dict,
        supply_chain_locations: List[Dict],
        time_horizon_days: int = 365
    ) -> Dict:
        """
        Comprehensive geopolitical risk analysis for a project

        Args:
            region: Primary region of interest
            project_location: Project location dict with country, coordinates
            supply_chain_locations: List of supplier/dependency locations
            time_horizon_days: Analysis time horizon

        Returns:
            Comprehensive geopolitical risk assessment
        """

        # Get base regional risk
        regional_data = self.regional_tensions.get(region, {
            'base_risk': 0.40,
            'primary_actors': ['Unknown'],
            'key_issues': ['General instability'],
            'escalation_triggers': ['Various factors']
        })

        base_risk = regional_data['base_risk']

        # Analyze conflict indicators
        indicator_scores = self._assess_conflict_indicators(region)

        # Calculate escalation probability
        escalation_prob = self._calculate_escalation_probability(
            base_risk,
            indicator_scores,
            time_horizon_days
        )

        # Identify specific flashpoints
        flashpoints = self._identify_flashpoints(region, project_location)

        # Assess supply chain exposure
        supply_chain_risk = self._assess_supply_chain_exposure(
            supply_chain_locations,
            regional_data
        )

        # Generate risk trajectory
        trajectory = self._determine_trajectory(indicator_scores)

        # Calculate timeline milestones
        timeline = self._generate_risk_timeline(base_risk, escalation_prob, time_horizon_days)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            base_risk,
            escalation_prob,
            flashpoints,
            supply_chain_risk
        )

        return {
            'region': region,
            'base_risk_score': round(base_risk, 3),
            'current_conflict_probability': round(escalation_prob, 3),
            'escalation_trajectory': trajectory,
            'time_horizon_days': time_horizon_days,
            'primary_actors': regional_data['primary_actors'],
            'key_issues': regional_data['key_issues'],
            'escalation_triggers': regional_data['escalation_triggers'],
            'conflict_indicators': indicator_scores,
            'flashpoints': flashpoints,
            'supply_chain_exposure': supply_chain_risk,
            'risk_timeline': timeline,
            'recommendations': recommendations,
            'risk_level': self._categorize_risk(escalation_prob)
        }

    def predict_conflict_escalation(
        self,
        current_events: List[Dict],
        region: str,
        days_ahead: int = 90
    ) -> Dict:
        """
        Predict probability of conflict escalation

        Args:
            current_events: Recent geopolitical events
            region: Region of analysis
            days_ahead: Prediction horizon

        Returns:
            Escalation prediction with probabilities
        """

        # Parse events and extract signals
        signals = self._extract_escalation_signals(current_events)

        # Calculate escalation momentum
        momentum = self._calculate_momentum(signals)

        # Predict probability by timeframe
        escalation_curve = []
        base_prob = self.regional_tensions.get(region, {}).get('base_risk', 0.40)

        for day in [7, 14, 30, 60, 90]:
            if day <= days_ahead:
                # Escalation probability grows with time and momentum
                prob = min(0.95, base_prob + (momentum * (day / 90)))
                escalation_curve.append({
                    'day': day,
                    'probability': round(prob, 3),
                    'confidence': 'high' if day <= 30 else 'medium' if day <= 60 else 'low'
                })

        # Identify critical events that could trigger escalation
        trigger_events = self._identify_trigger_events(region, signals)

        return {
            'region': region,
            'prediction_horizon_days': days_ahead,
            'current_escalation_probability': round(base_prob + momentum, 3),
            'escalation_momentum': round(momentum, 3),
            'escalation_curve': escalation_curve,
            'trigger_events': trigger_events,
            'early_warning_indicators': self._get_early_warning_indicators(signals),
            'confidence_level': self._assess_prediction_confidence(signals)
        }

    def assess_diplomatic_stability(
        self,
        countries: List[str],
        include_alliances: bool = True
    ) -> Dict:
        """
        Assess diplomatic stability between countries

        Args:
            countries: List of countries to analyze
            include_alliances: Include alliance/treaty analysis

        Returns:
            Diplomatic stability assessment
        """

        # Calculate bilateral relationships
        relationships = {}
        for i, country_a in enumerate(countries):
            for country_b in countries[i+1:]:
                rel_score = self._calculate_bilateral_relationship(country_a, country_b)
                relationships[f"{country_a}-{country_b}"] = rel_score

        # Overall stability score
        avg_stability = np.mean(list(relationships.values())) if relationships else 0.5

        # Identify unstable pairs
        unstable_pairs = [
            pair for pair, score in relationships.items()
            if score < 0.40
        ]

        # Alliance analysis
        alliances = self._analyze_alliances(countries) if include_alliances else []

        return {
            'countries_analyzed': countries,
            'overall_stability_score': round(avg_stability, 3),
            'bilateral_relationships': {k: round(v, 3) for k, v in relationships.items()},
            'unstable_pairs': unstable_pairs,
            'alliances': alliances,
            'diplomatic_risk_level': self._categorize_risk(1 - avg_stability)
        }

    # ============================================
    # HELPER METHODS
    # ============================================

    def _assess_conflict_indicators(self, region: str) -> Dict:
        """Assess current state of conflict indicators"""
        scores = {}

        # Simplified scoring based on known situations
        if region == 'Eastern Europe':
            scores = {
                'military_buildup': 0.85,
                'diplomatic_breakdown': 0.70,
                'economic_sanctions': 0.90,
                'territorial_disputes': 0.80,
                'proxy_conflicts': 0.60,
                'cyber_warfare': 0.75,
                'information_warfare': 0.80
            }
        elif region == 'Middle East':
            scores = {
                'military_buildup': 0.70,
                'diplomatic_breakdown': 0.65,
                'economic_sanctions': 0.75,
                'territorial_disputes': 0.60,
                'proxy_conflicts': 0.85,
                'cyber_warfare': 0.60,
                'information_warfare': 0.70
            }
        elif region == 'East Asia':
            scores = {
                'military_buildup': 0.75,
                'diplomatic_breakdown': 0.55,
                'economic_sanctions': 0.60,
                'territorial_disputes': 0.70,
                'proxy_conflicts': 0.40,
                'cyber_warfare': 0.65,
                'information_warfare': 0.60
            }
        else:
            # Default moderate scores
            scores = {indicator: 0.50 for indicator in self.conflict_indicators.keys()}

        # Add weighted scores
        weighted_scores = {}
        for indicator, score in scores.items():
            weight = self.conflict_indicators[indicator]['weight']
            weighted_scores[indicator] = {
                'score': round(score, 3),
                'weight': weight,
                'weighted_score': round(score * weight, 3)
            }

        return weighted_scores

    def _calculate_escalation_probability(
        self,
        base_risk: float,
        indicator_scores: Dict,
        days: int
    ) -> float:
        """Calculate probability of escalation"""

        # Sum weighted indicator scores
        total_weighted = sum(
            ind['weighted_score']
            for ind in indicator_scores.values()
        )

        # Time factor (risk increases with longer horizons)
        time_factor = min(1.0, days / 365) * 0.15

        # Combined probability
        escalation_prob = min(0.95, base_risk + total_weighted + time_factor)

        return escalation_prob

    def _determine_trajectory(self, indicator_scores: Dict) -> str:
        """Determine if situation is escalating, stable, or de-escalating"""

        # Calculate trend (simplified)
        avg_score = np.mean([ind['score'] for ind in indicator_scores.values()])

        if avg_score > 0.70:
            return 'escalating'
        elif avg_score > 0.45:
            return 'stable'
        else:
            return 'de-escalating'

    def _identify_flashpoints(self, region: str, location: Dict) -> List[Dict]:
        """Identify specific conflict flashpoints"""

        flashpoint_map = {
            'Eastern Europe': [
                {'name': 'Donbas Region', 'risk': 0.85, 'type': 'territorial'},
                {'name': 'Crimea', 'risk': 0.80, 'type': 'territorial'},
                {'name': 'Black Sea', 'risk': 0.70, 'type': 'maritime'},
                {'name': 'Belarus Border', 'risk': 0.60, 'type': 'border'}
            ],
            'Middle East': [
                {'name': 'Strait of Hormuz', 'risk': 0.75, 'type': 'maritime'},
                {'name': 'Golan Heights', 'risk': 0.70, 'type': 'territorial'},
                {'name': 'Yemen', 'risk': 0.80, 'type': 'proxy_war'},
                {'name': 'Nuclear Sites', 'risk': 0.85, 'type': 'strategic'}
            ],
            'East Asia': [
                {'name': 'Taiwan Strait', 'risk': 0.75, 'type': 'territorial'},
                {'name': 'South China Sea', 'risk': 0.70, 'type': 'maritime'},
                {'name': 'Senkaku Islands', 'risk': 0.55, 'type': 'territorial'}
            ],
            'Korean Peninsula': [
                {'name': 'DMZ', 'risk': 0.65, 'type': 'border'},
                {'name': 'Nuclear Sites', 'risk': 0.80, 'type': 'strategic'},
                {'name': 'Maritime Border', 'risk': 0.55, 'type': 'maritime'}
            ]
        }

        return flashpoint_map.get(region, [])

    def _assess_supply_chain_exposure(
        self,
        locations: List[Dict],
        regional_data: Dict
    ) -> Dict:
        """Assess supply chain exposure to geopolitical risk"""

        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0

        for loc in locations:
            country = loc.get('country', '')
            # Simple classification
            if country in regional_data.get('primary_actors', []):
                high_risk_count += 1
            elif self._is_adjacent_to_conflict(country, regional_data):
                medium_risk_count += 1
            else:
                low_risk_count += 1

        total = len(locations) if locations else 1

        return {
            'total_dependencies': total,
            'high_risk_dependencies': high_risk_count,
            'medium_risk_dependencies': medium_risk_count,
            'low_risk_dependencies': low_risk_count,
            'exposure_percentage': round((high_risk_count / total) * 100, 1) if total > 0 else 0
        }

    def _is_adjacent_to_conflict(self, country: str, regional_data: Dict) -> bool:
        """Check if country is adjacent to conflict zone"""
        # Simplified logic
        adjacent_countries = {
            'Poland': True,  # Adjacent to Ukraine
            'Romania': True,
            'Turkey': True,  # Adjacent to Middle East
            'Jordan': True,
            'Philippines': True,  # South China Sea
            'Vietnam': True
        }
        return adjacent_countries.get(country, False)

    def _generate_risk_timeline(
        self,
        base_risk: float,
        escalation_prob: float,
        days: int
    ) -> List[Dict]:
        """Generate risk probability over time"""

        timeline = []
        for milestone in [30, 90, 180, 365]:
            if milestone <= days:
                # Risk increases gradually over time
                prob = min(0.95, base_risk + (escalation_prob - base_risk) * (milestone / days))
                timeline.append({
                    'day': milestone,
                    'probability': round(prob, 3),
                    'description': f"{milestone}-day outlook"
                })

        return timeline

    def _generate_recommendations(
        self,
        base_risk: float,
        escalation_prob: float,
        flashpoints: List[Dict],
        supply_chain_risk: Dict
    ) -> List[str]:
        """Generate risk mitigation recommendations"""

        recommendations = []

        if escalation_prob > 0.70:
            recommendations.append("CRITICAL: Activate emergency response plan immediately")
            recommendations.append("Consider project suspension or relocation")
            recommendations.append("Secure war risk insurance with maximum coverage")

        if escalation_prob > 0.50:
            recommendations.append("HIGH PRIORITY: Diversify supply chain away from conflict zones")
            recommendations.append("Establish alternative logistics routes")
            recommendations.append("Increase inventory buffers by 90 days")

        if supply_chain_risk.get('high_risk_dependencies', 0) > 0:
            recommendations.append(f"Replace {supply_chain_risk['high_risk_dependencies']} high-risk suppliers")
            recommendations.append("Conduct supplier risk audit for all dependencies")

        if len(flashpoints) > 2:
            recommendations.append(f"Monitor {len(flashpoints)} identified flashpoints daily")
            recommendations.append("Establish early warning monitoring system")

        recommendations.append("Include comprehensive FM clause covering geopolitical events")
        recommendations.append("Maintain regular communication with local authorities")

        return recommendations

    def _categorize_risk(self, probability: float) -> str:
        """Categorize risk level"""
        if probability > 0.75:
            return 'CRITICAL'
        elif probability > 0.60:
            return 'HIGH'
        elif probability > 0.40:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _extract_escalation_signals(self, events: List[Dict]) -> Dict:
        """Extract escalation signals from events"""
        signals = {
            'military_activity': 0,
            'diplomatic_incidents': 0,
            'economic_measures': 0,
            'cyber_incidents': 0
        }

        for event in events:
            event_type = event.get('type', '').lower()
            if 'military' in event_type:
                signals['military_activity'] += 1
            elif 'diplomatic' in event_type:
                signals['diplomatic_incidents'] += 1
            elif 'sanction' in event_type or 'economic' in event_type:
                signals['economic_measures'] += 1
            elif 'cyber' in event_type:
                signals['cyber_incidents'] += 1

        return signals

    def _calculate_momentum(self, signals: Dict) -> float:
        """Calculate escalation momentum from signals"""
        total_signals = sum(signals.values())
        if total_signals == 0:
            return 0.0

        # More signals = higher momentum
        momentum = min(0.30, total_signals * 0.05)
        return momentum

    def _identify_trigger_events(self, region: str, signals: Dict) -> List[str]:
        """Identify potential trigger events"""
        triggers = []

        if signals.get('military_activity', 0) > 3:
            triggers.append("Significant military buildup detected")

        if signals.get('diplomatic_incidents', 0) > 2:
            triggers.append("Diplomatic relations deteriorating")

        if signals.get('cyber_incidents', 0) > 0:
            triggers.append("Cyber warfare activity detected")

        regional_triggers = self.regional_tensions.get(region, {}).get('escalation_triggers', [])
        triggers.extend(regional_triggers[:2])

        return triggers

    def _get_early_warning_indicators(self, signals: Dict) -> List[str]:
        """Get early warning indicators"""
        indicators = []

        if signals.get('military_activity', 0) > 0:
            indicators.append("Monitor troop movements and military exercises")

        if signals.get('diplomatic_incidents', 0) > 0:
            indicators.append("Track diplomatic communications and negotiations")

        indicators.append("Monitor international news and intelligence reports")
        indicators.append("Track commodity prices (oil, gas) for disruption signals")

        return indicators

    def _assess_prediction_confidence(self, signals: Dict) -> str:
        """Assess confidence level of predictions"""
        total_signals = sum(signals.values())

        if total_signals >= 5:
            return 'high'
        elif total_signals >= 2:
            return 'medium'
        else:
            return 'low'

    def _calculate_bilateral_relationship(self, country_a: str, country_b: str) -> float:
        """Calculate relationship score between two countries"""

        # Simplified relationship scoring
        hostile_pairs = {
            ('Russia', 'Ukraine'): 0.10,
            ('Iran', 'Israel'): 0.15,
            ('China', 'Taiwan'): 0.30,
            ('India', 'Pakistan'): 0.25,
            ('North Korea', 'South Korea'): 0.20
        }

        # Check both orderings
        pair1 = (country_a, country_b)
        pair2 = (country_b, country_a)

        if pair1 in hostile_pairs:
            return hostile_pairs[pair1]
        elif pair2 in hostile_pairs:
            return hostile_pairs[pair2]
        else:
            return 0.70  # Default neutral relationship

    def _analyze_alliances(self, countries: List[str]) -> List[Dict]:
        """Analyze alliance structures"""

        known_alliances = {
            'NATO': ['USA', 'UK', 'France', 'Germany', 'Poland', 'Turkey'],
            'CSTO': ['Russia', 'Belarus', 'Kazakhstan'],
            'Quad': ['USA', 'India', 'Japan', 'Australia'],
            'SCO': ['China', 'Russia', 'India', 'Pakistan']
        }

        alliances = []
        for alliance_name, members in known_alliances.items():
            countries_in_alliance = [c for c in countries if c in members]
            if countries_in_alliance:
                alliances.append({
                    'name': alliance_name,
                    'members_in_analysis': countries_in_alliance,
                    'cohesion': 'strong' if len(countries_in_alliance) >= 2 else 'moderate'
                })

        return alliances


# Global instance
geopolitical_engine = GeopoliticalInferenceEngine()


# Convenience function
def analyze_geopolitical_risk(contract_data: Dict) -> Dict:
    """Convenience function for geopolitical risk analysis"""
    region = contract_data.get('region', 'Global')
    project_location = contract_data.get('project_location', {})
    supply_chain = contract_data.get('supply_chain_locations', [])

    return geopolitical_engine.analyze_geopolitical_risk(
        region,
        project_location,
        supply_chain,
        time_horizon_days=365
    )
