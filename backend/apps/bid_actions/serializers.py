"""
Serializers for Bid Actions API
"""
from rest_framework import serializers
from .models import Department, ActionItem, RiskPropagation, DepartmentActionSummary


class DepartmentSerializer(serializers.ModelSerializer):
    """Department serializer"""

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description',
            'color_hex', 'workload_weight', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ActionItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta:
        model = ActionItem
        fields = [
            'id', 'title', 'department', 'department_name', 'department_code',
            'priority', 'status', 'risk_score', 'complexity_score',
            'financial_exposure', 'source_type', 'created_at'
        ]


class ActionItemDetailSerializer(serializers.ModelSerializer):
    """Full serializer with all relationships"""
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.UUIDField(write_only=True)
    depends_on_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    dependencies = ActionItemListSerializer(source='depends_on', many=True, read_only=True)

    class Meta:
        model = ActionItem
        fields = [
            'id', 'tender', 'department', 'department_id',
            'title', 'description', 'source_type', 'source_reference',
            'priority', 'status', 'risk_score', 'complexity_score',
            'financial_exposure', 'depends_on_ids', 'dependencies',
            'assigned_to', 'due_date', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']

    def create(self, validated_data):
        depends_on_ids = validated_data.pop('depends_on_ids', [])
        action = ActionItem.objects.create(**validated_data)
        if depends_on_ids:
            action.depends_on.set(depends_on_ids)
        return action

    def update(self, instance, validated_data):
        depends_on_ids = validated_data.pop('depends_on_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if depends_on_ids is not None:
            instance.depends_on.set(depends_on_ids)
        return instance


class RiskPropagationSerializer(serializers.ModelSerializer):
    """Risk propagation edge serializer"""

    class Meta:
        model = RiskPropagation
        fields = [
            'id', 'source_action', 'target_action',
            'propagation_weight', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DepartmentSummarySerializer(serializers.ModelSerializer):
    """Department statistics serializer"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = DepartmentActionSummary
        fields = [
            'id', 'tender', 'department', 'department_name', 'department_code',
            'total_actions', 'completed_actions', 'completion_percentage',
            'avg_risk_score', 'total_financial_exposure', 'last_calculated'
        ]

    def get_completion_percentage(self, obj):
        if obj.total_actions == 0:
            return 0
        return round((obj.completed_actions / obj.total_actions) * 100, 2)


class ActionItemStatusUpdateSerializer(serializers.Serializer):
    """Serializer for bulk status updates"""
    action_ids = serializers.ListField(child=serializers.UUIDField())
    status = serializers.ChoiceField(choices=ActionItem.STATUS_CHOICES)
