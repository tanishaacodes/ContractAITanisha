"""
Negotiation API Serializers
"""

from rest_framework import serializers
from .models import (
    Counterparty,
    NegotiationHistory,
    ExculpatoryAnalysis,
    ExculpatoryClause,
    ExculpatoryPattern
)


class CounterpartySerializer(serializers.ModelSerializer):
    """Serializer for Counterparty model"""

    class Meta:
        model = Counterparty
        fields = [
            'id', 'name', 'industry', 'risk_profile',
            'aggressiveness_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NegotiationHistorySerializer(serializers.ModelSerializer):
    """Serializer for NegotiationHistory model"""

    class Meta:
        model = NegotiationHistory
        fields = [
            'id', 'counterparty', 'clause_type', 'clause_text',
            'deviation_score', 'accepted', 'redline_rounds',
            'stalled', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ExculpatoryPatternSerializer(serializers.ModelSerializer):
    """Serializer for ExculpatoryPattern model"""

    class Meta:
        model = ExculpatoryPattern
        fields = [
            'id', 'pattern_id', 'label', 'text', 'risk_category',
            'controlled_by', 'explanation', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ExculpatoryClauseSerializer(serializers.ModelSerializer):
    """Serializer for individual exculpatory clause analysis"""

    imbalance = serializers.SerializerMethodField()

    class Meta:
        model = ExculpatoryClause
        fields = [
            'id', 'clause_name', 'text', 'risk_score', 'is_exculpatory',
            'risk_category', 'imbalance', 'pattern_matches', 'suggestions',
            # Enhanced fields from Prof. Murali's research
            'imbalance_severity', 'imbalance_score', 'financial_exposure',
            'proper_allocation_advice', 'impact_chain_data', 'deal_breaker',
            'probability', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_imbalance(self, obj):
        """Return imbalance information"""
        return {
            "controlled_by": obj.controlled_by,
            "bearer": obj.bearer,
            "is_imbalanced": obj.is_imbalanced,
            "explanation": obj.imbalance_explanation
        }


class ExculpatoryAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for complete exculpatory analysis with clauses"""

    clauses = ExculpatoryClauseSerializer(many=True, read_only=True)
    summary = serializers.SerializerMethodField()

    class Meta:
        model = ExculpatoryAnalysis
        fields = [
            'id', 'contract', 'total_clauses', 'analyzed_clauses',
            'clauses', 'summary', 'analyzed_at', 'updated_at'
        ]
        read_only_fields = ['id', 'analyzed_at', 'updated_at']

    def get_summary(self, obj):
        """Return summary statistics with enhanced metrics"""
        from ai.clause_interaction_detector import detect_clause_interactions, calculate_compound_risk_score, prioritize_negotiation_points, ClauseData

        # Get all clauses for this analysis
        clauses = obj.clauses.all()

        # Calculate deal breakers
        deal_breakers = sum(1 for c in clauses if c.deal_breaker)

        # Calculate base risk score
        base_risk_score = sum(c.risk_score for c in clauses) / len(clauses) if len(clauses) > 0 else 0

        # Detect clause interactions
        clause_data_list = [
            ClauseData(
                clause_id=c.clause_name,
                text=c.text,
                category=c.risk_category,
                risk_score=c.risk_score,
                is_exculpatory=c.is_exculpatory
            )
            for c in clauses
        ]

        interaction_risks = detect_clause_interactions(clause_data_list)
        compound_risk_score = calculate_compound_risk_score(base_risk_score, interaction_risks)
        negotiation_priorities = prioritize_negotiation_points(interaction_risks)

        # Calculate total financial exposure
        total_financial_exposure = {
            "maximum_exposure": 0,
            "likely_exposure": 0,
            "minimum_exposure": 0
        }

        for clause in clauses:
            if clause.financial_exposure:
                total_financial_exposure["maximum_exposure"] += clause.financial_exposure.get("maximum_exposure", 0)
                total_financial_exposure["likely_exposure"] += clause.financial_exposure.get("likely_exposure", 0)
                total_financial_exposure["minimum_exposure"] += clause.financial_exposure.get("minimum_exposure", 0)

        return {
            "total_clauses": obj.total_clauses,
            "analyzed_clauses": obj.analyzed_clauses,
            "risk_distribution": {
                "high": obj.high_risk_count,
                "medium": obj.medium_risk_count,
                "low": obj.low_risk_count
            },
            "risk_percentages": {
                "high": round((obj.high_risk_count / obj.analyzed_clauses * 100), 1) if obj.analyzed_clauses > 0 else 0,
                "medium": round((obj.medium_risk_count / obj.analyzed_clauses * 100), 1) if obj.analyzed_clauses > 0 else 0,
                "low": round((obj.low_risk_count / obj.analyzed_clauses * 100), 1) if obj.analyzed_clauses > 0 else 0
            },
            "imbalanced_clauses": obj.imbalanced_count,
            "category_breakdown": obj.category_breakdown,
            "recommendation": obj.recommendation,
            # Enhanced fields from Prof. Murali's research
            "deal_breakers": deal_breakers,
            "base_risk_score": round(base_risk_score, 2),
            "compound_risk_score": round(compound_risk_score, 2),
            "interaction_risks": [
                {
                    "risk_type": i.risk_type,
                    "severity": i.severity,
                    "description": i.description,
                    "financial_multiplier": i.financial_multiplier,
                    "involved_clauses": i.involved_clauses
                }
                for i in interaction_risks
            ],
            "negotiation_priorities": negotiation_priorities,
            "total_financial_exposure": total_financial_exposure
        }


class ExculpatoryAnalysisSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for summary view only"""

    summary = serializers.SerializerMethodField()

    class Meta:
        model = ExculpatoryAnalysis
        fields = ['id', 'contract', 'summary', 'analyzed_at', 'updated_at']
        read_only_fields = ['id', 'analyzed_at', 'updated_at']

    def get_summary(self, obj):
        """Return summary statistics with enhanced metrics"""
        from ai.clause_interaction_detector import detect_clause_interactions, calculate_compound_risk_score, prioritize_negotiation_points, ClauseData

        # Get all clauses for this analysis
        clauses = obj.clauses.all()

        # Calculate deal breakers
        deal_breakers = sum(1 for c in clauses if c.deal_breaker)

        # Calculate base risk score
        base_risk_score = sum(c.risk_score for c in clauses) / len(clauses) if len(clauses) > 0 else 0

        # Detect clause interactions
        clause_data_list = [
            ClauseData(
                clause_id=c.clause_name,
                text=c.text,
                category=c.risk_category,
                risk_score=c.risk_score,
                is_exculpatory=c.is_exculpatory
            )
            for c in clauses
        ]

        interaction_risks = detect_clause_interactions(clause_data_list)
        compound_risk_score = calculate_compound_risk_score(base_risk_score, interaction_risks)
        negotiation_priorities = prioritize_negotiation_points(interaction_risks)

        # Calculate total financial exposure
        total_financial_exposure = {
            "maximum_exposure": 0,
            "likely_exposure": 0,
            "minimum_exposure": 0
        }

        for clause in clauses:
            if clause.financial_exposure:
                total_financial_exposure["maximum_exposure"] += clause.financial_exposure.get("maximum_exposure", 0)
                total_financial_exposure["likely_exposure"] += clause.financial_exposure.get("likely_exposure", 0)
                total_financial_exposure["minimum_exposure"] += clause.financial_exposure.get("minimum_exposure", 0)

        return {
            "total_clauses": obj.total_clauses,
            "analyzed_clauses": obj.analyzed_clauses,
            "risk_distribution": {
                "high": obj.high_risk_count,
                "medium": obj.medium_risk_count,
                "low": obj.low_risk_count
            },
            "risk_percentages": {
                "high": round((obj.high_risk_count / obj.analyzed_clauses * 100), 1) if obj.analyzed_clauses > 0 else 0,
                "medium": round((obj.medium_risk_count / obj.analyzed_clauses * 100), 1) if obj.analyzed_clauses > 0 else 0,
                "low": round((obj.low_risk_count / obj.analyzed_clauses * 100), 1) if obj.analyzed_clauses > 0 else 0
            },
            "imbalanced_clauses": obj.imbalanced_count,
            "category_breakdown": obj.category_breakdown,
            "recommendation": obj.recommendation,
            # Enhanced fields from Prof. Murali's research
            "deal_breakers": deal_breakers,
            "base_risk_score": round(base_risk_score, 2),
            "compound_risk_score": round(compound_risk_score, 2),
            "interaction_risks": [
                {
                    "risk_type": i.risk_type,
                    "severity": i.severity,
                    "description": i.description,
                    "financial_multiplier": i.financial_multiplier,
                    "involved_clauses": i.involved_clauses
                }
                for i in interaction_risks
            ],
            "negotiation_priorities": negotiation_priorities,
            "total_financial_exposure": total_financial_exposure
        }
