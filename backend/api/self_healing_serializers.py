"""
Serializers for Self-Healing Clause Library models
"""

from rest_framework import serializers
from core.models import ClauseEvent, ClauseHealthMetrics, Clause, ClauseVersion


class ClauseEventSerializer(serializers.ModelSerializer):
    """Serializer for ClauseEvent model"""

    class Meta:
        model = ClauseEvent
        fields = [
            'id',
            'clause_version',
            'contract',
            'event_type',
            'outcome_score',
            'description',
            'jurisdiction',
            'counterparty_type',
            'settlement_amount',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ClauseHealthMetricsSerializer(serializers.ModelSerializer):
    """Serializer for ClauseHealthMetrics model"""

    clause_name = serializers.CharField(source='clause.clause_name', read_only=True)

    class Meta:
        model = ClauseHealthMetrics
        fields = [
            'id',
            'clause',
            'clause_name',
            'usage_count',
            'success_rate',
            'enforceability_score',
            'negotiation_score',
            'health_score',
            'status',
            'is_promoted',
            'promoted_at',
            'promotion_reason',
            'last_calculated',
            'created_at'
        ]
        read_only_fields = ['id', 'last_calculated', 'created_at']


class ClauseHealthSummarySerializer(serializers.Serializer):
    """Lightweight serializer for clause health dashboard"""

    clause_id = serializers.CharField()
    clause_code = serializers.CharField()
    status = serializers.CharField()
    health_score = serializers.FloatField()
    success_rate = serializers.FloatField()
    current_version = serializers.CharField(required=False)


class ClausePromotionRequestSerializer(serializers.Serializer):
    """Serializer for promotion requests"""

    dry_run = serializers.BooleanField(default=False)


class ClauseRetirementRequestSerializer(serializers.Serializer):
    """Serializer for retirement requests"""

    dry_run = serializers.BooleanField(default=False)
    min_health_score = serializers.FloatField(default=0.45, min_value=0.0, max_value=1.0)


class ClauseSimilarityRequestSerializer(serializers.Serializer):
    """Serializer for similarity search requests"""

    text = serializers.CharField()
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)
