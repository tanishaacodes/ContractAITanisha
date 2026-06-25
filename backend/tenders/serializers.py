"""
Django REST Framework Serializers for Tender Intelligence
"""
from rest_framework import serializers
from .models import (
    Tender,
    TenderSection,
    TenderWorkItem,
    TenderEligibility,
    TenderRisk,
    TenderConflict,
    BidScenario,
    TenderProposal,
    TenderNegotiation,
    PreBidQuestion,
    CompanyProfile,
    TenderAmendment,
    BidDepartment,
    BidActionItem,
    BidDepartmentRiskPropagation,
    BidReadinessSnapshot,
)


class TenderSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderSection
        fields = '__all__'


class TenderWorkItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderWorkItem
        fields = '__all__'


class TenderEligibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderEligibility
        fields = '__all__'


class TenderRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderRisk
        fields = '__all__'


class TenderConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderConflict
        fields = '__all__'


class BidScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidScenario
        fields = '__all__'


class TenderProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderProposal
        fields = '__all__'


class TenderNegotiationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderNegotiation
        fields = '__all__'


class PreBidQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreBidQuestion
        fields = '__all__'


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class TenderAmendmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TenderAmendment
        fields = '__all__'

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            # Construct full name from first_name and last_name
            if hasattr(obj.uploaded_by, 'first_name') and hasattr(obj.uploaded_by, 'last_name'):
                first_name = obj.uploaded_by.first_name or ''
                last_name = obj.uploaded_by.last_name or ''
                full_name = f"{first_name} {last_name}".strip()
                return full_name if full_name else obj.uploaded_by.email
            # Fallback to email or username
            return getattr(obj.uploaded_by, 'email', None) or getattr(obj.uploaded_by, 'username', 'Unknown')
        return None


class TenderListSerializer(serializers.ModelSerializer):
    """Serializer for tender list view"""

    class Meta:
        model = Tender
        fields = [
            'id', 'reference_number', 'title', 'estimated_value',
            'submission_deadline', 'status', 'created_at'
        ]


class TenderDetailSerializer(serializers.ModelSerializer):
    """Serializer for tender detail view with related data"""

    sections = TenderSectionSerializer(many=True, read_only=True)
    work_items = TenderWorkItemSerializer(many=True, read_only=True)
    eligibility = TenderEligibilitySerializer(read_only=True)
    risks = TenderRiskSerializer(many=True, read_only=True)
    conflicts = TenderConflictSerializer(many=True, read_only=True)
    bid_scenarios = BidScenarioSerializer(many=True, read_only=True)
    proposal = TenderProposalSerializer(read_only=True)
    negotiations = TenderNegotiationSerializer(many=True, read_only=True)
    prebid_questions = PreBidQuestionSerializer(many=True, read_only=True)
    amendments = TenderAmendmentSerializer(many=True, read_only=True)

    class Meta:
        model = Tender
        fields = '__all__'


class TenderUploadSerializer(serializers.ModelSerializer):
    """Serializer for tender upload"""

    class Meta:
        model = Tender
        fields = ['title', 'pdf_file', 'pdf_url']


# ─── Bid Management Serializers ───────────────────────────────────────────────

class BidDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidDepartment
        fields = ['id', 'name', 'workload_weight', 'description']


class BidActionItemSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source='department.name', read_only=True
    )
    financial_exposure = serializers.FloatField()

    class Meta:
        model = BidActionItem
        fields = [
            'id', 'department', 'department_name',
            'source_type', 'source_ref',
            'title', 'description',
            'priority', 'status',
            'risk_score', 'complexity_score', 'financial_exposure',
            'ai_generated', 'due_date',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BidActionItemUpdateSerializer(serializers.ModelSerializer):
    """Lightweight serializer for status/priority updates."""
    class Meta:
        model = BidActionItem
        fields = ['status', 'priority', 'due_date', 'description']


class BidDepartmentRiskPropagationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidDepartmentRiskPropagation
        fields = [
            'id', 'department_name',
            'base_risk', 'propagated_risk', 'amplification',
            'predicted_delay_days', 'task_count', 'computed_at',
        ]


class BidReadinessSnapshotSerializer(serializers.ModelSerializer):
    total_exposure = serializers.FloatField()

    class Meta:
        model = BidReadinessSnapshot
        fields = [
            'id',
            'readiness_index', 'data_readiness', 'task_completion',
            'total_actions', 'completed_actions', 'critical_pending',
            'total_exposure', 'created_at',
        ]
