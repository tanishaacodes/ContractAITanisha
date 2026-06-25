from rest_framework import serializers
from .models import (
    User, Role, Contract, Clause, ContractRiskAnalysis, ClauseDeviation,
    ContractObligation, ContractVersion, Intent, ClauseIntent, IntentObligation, IntentRight,
    ComplianceFramework, ComplianceRequirement, IntentComplianceMapping, ContractComplianceAnalysis,
    ClauseRewriteSuggestion
)
import json


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions']


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    firstName = serializers.CharField(source='first_name', read_only=True)
    lastName = serializers.CharField(source='last_name', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    lastLogin = serializers.DateTimeField(source='last_login', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'role', 'isActive', 'lastLogin', 'createdAt',
                  'first_name', 'last_name', 'is_active', 'last_login', 'created_at']
        read_only_fields = ['id', 'createdAt', 'lastLogin', 'first_name', 'last_name',
                            'is_active', 'last_login', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# =========================
# UPDATED CONTRACT SERIALIZER
# =========================
class ContractSerializer(serializers.ModelSerializer):
    has_analysis = serializers.SerializerMethodField()
    hasClauses = serializers.SerializerMethodField()
    hasRiskAnalysis = serializers.SerializerMethodField()
    has_intelligence = serializers.SerializerMethodField()
    intelligence_extracted = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()

    uploadedAt = serializers.DateTimeField(source='uploaded_at', read_only=True)
    originalFilename = serializers.CharField(source='original_filename', read_only=True)

    contractType = serializers.CharField(source='contract_type', read_only=True)
    contractValue = serializers.CharField(source='contract_value', read_only=True, allow_null=True, required=False)

    # 🔥 FRONTEND LEGACY KEYS (REQUIRED)
    party_name = serializers.SerializerMethodField()
    contract_duration = serializers.SerializerMethodField()

    # 🔥 FRONTEND CAMELCASE KEYS
    partyName = serializers.SerializerMethodField()
    contractDuration = serializers.SerializerMethodField()

    # 🔥 INDIVIDUAL PARTY FIELDS
    partyA = serializers.CharField(source='party_a', read_only=True)
    partyB = serializers.CharField(source='party_b', read_only=True)

    # 🔥 DATE FIELDS
    startDate = serializers.DateField(source='start_date', read_only=True)
    endDate = serializers.DateField(source='end_date', read_only=True)

    # 🔥 NEW SEARCHABLE FIELDS (snake_case and camelCase)
    paymentTerms = serializers.CharField(source='payment_terms', read_only=True)
    liabilityLevel = serializers.CharField(source='liability_level', read_only=True)
    projectLocation = serializers.CharField(source='project_location', read_only=True, allow_null=True)
    supplierLocations = serializers.CharField(source='supplier_locations', read_only=True, allow_null=True)

    # 🔥 ASSIGNMENT TRACKING
    assignedBy = serializers.CharField(source='assigned_by', read_only=True, allow_null=True)

    class Meta:
        model = Contract
        fields = [
            'id',
            'filename',
            'original_filename',
            'originalFilename',
            'file_type',

            'contract_type',
            'contractType',

            'contract_value',
            'contractValue',

            # ✅ BOTH KEYS
            'party_name',
            'partyName',
            'contract_duration',
            'contractDuration',

            # ✅ INDIVIDUAL PARTY FIELDS (both formats)
            'party_a',
            'party_b',
            'partyA',
            'partyB',

            # ✅ DATE FIELDS (both formats)
            'start_date',
            'end_date',
            'startDate',
            'endDate',

            # ✅ NEW SEARCHABLE FIELDS
            'jurisdiction',
            'payment_terms',
            'paymentTerms',
            'liability_level',
            'liabilityLevel',
            'project_location',
            'projectLocation',
            'supplier_locations',
            'supplierLocations',

            'confidence_score',
            'ocr_performed',

            'uploaded_at',
            'uploadedAt',
            'created_at',

            'has_analysis',
            'hasClauses',
            'hasRiskAnalysis',
            'has_intelligence',
            'intelligence_extracted',
            'risk_level',
            'status',

            # ✅ ASSIGNMENT TRACKING
            'assigned_by',
            'assignedBy',
        ]

    # =====================
    # PARTY NAME (FIX)
    # =====================
    def get_party_name(self, obj):
        if obj.party_a and obj.party_b:
            return f"{obj.party_a} vs {obj.party_b}"
        return obj.party_a or obj.party_b

    def get_partyName(self, obj):
        return self.get_party_name(obj)

    # =====================
    # DURATION (FIX)
    # =====================
    def get_contract_duration(self, obj):
        if obj.start_date and obj.end_date:
            # Calculate years
            from datetime import date
            delta = obj.end_date - obj.start_date
            years = delta.days / 365.25

            # Format dates as DD-MM-YY
            start_formatted = obj.start_date.strftime('%d-%m-%y')
            end_formatted = obj.end_date.strftime('%d-%m-%y')

            # Determine year text (singular or plural)
            if years < 0.95:  # Less than ~11.5 months
                year_text = f"{delta.days} days"
            elif 0.95 <= years <= 1.05:  # Between 11.5 and 13 months = ~1 year
                year_text = "1 year"
            else:
                year_text = f"{int(round(years))} years"

            return f"{start_formatted} to {end_formatted} = {year_text}"
        return None

    def get_contractDuration(self, obj):
        return self.get_contract_duration(obj)

    def get_has_analysis(self, obj):
        return obj.clauses.exists()

    def get_hasClauses(self, obj):
        return obj.clauses.filter(found=True).exists()

    def get_hasRiskAnalysis(self, obj):
        return ContractRiskAnalysis.objects.filter(contract=obj).exists()

    def get_has_intelligence(self, obj):
        """Check if contract has extracted intelligence"""
        return hasattr(obj, 'intelligence') and obj.intelligence is not None

    def get_intelligence_extracted(self, obj):
        """Alias for has_intelligence for frontend compatibility"""
        return self.get_has_intelligence(obj)

    def get_risk_level(self, obj):
        """Get risk level from contract risk analysis"""
        try:
            risk_analysis = ContractRiskAnalysis.objects.filter(contract=obj).first()
            return risk_analysis.risk_level if risk_analysis else None
        except:
            return None



class ContractDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['id', 'filename', 'original_filename', 'file_type', 'full_text',
                  'contract_type', 'confidence_score', 'ocr_performed', 'uploaded_at',
                  'contract_value', 'party_name', 'contract_duration', 'status',
                  'party_a', 'party_b', 'start_date', 'end_date', 'jurisdiction',
                  'payment_terms', 'liability_level', 'has_arbitration',
                  'project_location', 'supplier_locations']
        read_only_fields = ['id', 'filename', 'uploaded_at']


class ClauseSerializer(serializers.ModelSerializer):
    text_spans = serializers.SerializerMethodField()
    context_sentences = serializers.SerializerMethodField()

    class Meta:
        model = Clause
        fields = ['id', 'clause_name', 'found', 'confidence', 'match_count',
                  'text_spans', 'context_sentences']
        read_only_fields = ['id']

    def get_text_spans(self, obj):
        try:
            return json.loads(obj.text_spans) if obj.text_spans else []
        except json.JSONDecodeError:
            return []

    def get_context_sentences(self, obj):
        try:
            return json.loads(obj.context_sentences) if obj.context_sentences else []
        except json.JSONDecodeError:
            return []


class ClauseDeviationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClauseDeviation
        fields = ['id', 'clause_name', 'deviation_type', 'severity', 'description',
                  'recommendation', 'created_at']
        read_only_fields = ['id', 'created_at']


class ContractRiskAnalysisSerializer(serializers.ModelSerializer):
    deviations = ClauseDeviationSerializer(many=True, read_only=True)

    class Meta:
        model = ContractRiskAnalysis
        fields = ['id', 'risk_level', 'risk_score', 'total_deviations', 'critical_issues',
                  'medium_issues', 'low_issues', 'analysis_summary', 'executive_summary',
                  'summary_generated_at', 'category_breakdown', 'detailed_breakdown',
                  'deviations', 'created_at']
        read_only_fields = ['id', 'created_at', 'executive_summary',
                            'summary_generated_at', 'category_breakdown', 'detailed_breakdown']


class ContractObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractObligation
        fields = ['id', 'title', 'description', 'full_text', 'category',
                  'responsible_party', 'priority', 'due_date_text',
                  'clause_reference', 'is_completed', 'completed_at',
                  'completion_notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContractVersionSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ContractVersion
        fields = ['id', 'version_number', 'created_by', 'created_by_email',
                  'created_by_name', 'change_description', 'filename',
                  'original_filename', 'file_type', 'file_path', 'full_text',
                  'contract_type', 'contract_value', 'party_name',
                  'contract_duration', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name or ''} {obj.created_by.last_name or ''}".strip() or obj.created_by.email
        return "System"

# =========================
# INTENT MINING SERIALIZERS
# =========================

class IntentSerializer(serializers.ModelSerializer):
    """Serializer for discovered legal intents"""
    occurrenceCount = serializers.IntegerField(source='occurrence_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Intent
        fields = ['id', 'name', 'description', 'confidence', 'occurrence_count',
                  'occurrenceCount', 'created_at', 'createdAt', 'updated_at', 'updatedAt']
        read_only_fields = ['id', 'created_at', 'updated_at', 'occurrence_count']


class IntentObligationSerializer(serializers.ModelSerializer):
    """Serializer for obligations extracted from clauses"""
    riskScore = serializers.FloatField(source='risk_score', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    intent_name = serializers.CharField(source='intent.name', read_only=True)
    clause_name = serializers.CharField(source='clause.clause_name', read_only=True)
    contractVersionId = serializers.CharField(source='contract_version.id', read_only=True, allow_null=True)
    versionNumber = serializers.IntegerField(source='contract_version.version_number', read_only=True, allow_null=True)

    class Meta:
        model = IntentObligation
        fields = ['id', 'clause', 'clause_name', 'intent', 'intent_name', 'party',
                  'action', 'condition', 'deadline', 'priority', 'risk_score',
                  'riskScore', 'created_at', 'createdAt', 'updated_at', 'updatedAt',
                  'contractVersionId', 'versionNumber']
        read_only_fields = ['id', 'created_at', 'updated_at']


class IntentRightSerializer(serializers.ModelSerializer):
    """Serializer for rights extracted from clauses"""
    riskScore = serializers.FloatField(source='risk_score', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    intent_name = serializers.CharField(source='intent.name', read_only=True)
    clause_name = serializers.CharField(source='clause.clause_name', read_only=True)
    contractVersionId = serializers.CharField(source='contract_version.id', read_only=True, allow_null=True)
    versionNumber = serializers.IntegerField(source='contract_version.version_number', read_only=True, allow_null=True)

    class Meta:
        model = IntentRight
        fields = ['id', 'clause', 'clause_name', 'intent', 'intent_name', 'party',
                  'entitlement', 'trigger', 'risk_score', 'riskScore',
                  'created_at', 'createdAt', 'updated_at', 'updatedAt',
                  'contractVersionId', 'versionNumber']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClauseIntentSerializer(serializers.ModelSerializer):
    """Serializer for clause-intent relationships"""
    isPrimary = serializers.BooleanField(source='is_primary', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    intent_details = IntentSerializer(source='intent', read_only=True)
    clause_name = serializers.CharField(source='clause.clause_name', read_only=True)
    contractVersionId = serializers.CharField(source='contract_version.id', read_only=True, allow_null=True)
    versionNumber = serializers.IntegerField(source='contract_version.version_number', read_only=True, allow_null=True)

    class Meta:
        model = ClauseIntent
        fields = ['id', 'clause', 'clause_name', 'intent', 'intent_details',
                  'confidence', 'is_primary', 'isPrimary', 'created_at', 'createdAt',
                  'contractVersionId', 'versionNumber']
        read_only_fields = ['id', 'created_at']


# =========================
# COMPLIANCE MAPPING SERIALIZERS
# =========================

class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    """Serializer for compliance frameworks (GDPR, SOX, HIPAA, GST)"""
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    effectiveDate = serializers.DateField(source='effective_date', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ComplianceFramework
        fields = ['id', 'code', 'name', 'description', 'jurisdiction', 'effective_date',
                  'effectiveDate', 'version', 'is_active', 'isActive', 'priority',
                  'created_at', 'createdAt', 'updated_at', 'updatedAt']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplianceRequirementSerializer(serializers.ModelSerializer):
    """Serializer for compliance requirements"""
    frameworkCode = serializers.CharField(source='framework.code', read_only=True)
    frameworkName = serializers.CharField(source='framework.name', read_only=True)
    requirementCode = serializers.CharField(source='requirement_code', read_only=True)
    requirementName = serializers.CharField(source='requirement_name', read_only=True)
    requirementType = serializers.CharField(source='requirement_type', read_only=True)
    detectionKeywords = serializers.JSONField(source='detection_keywords', read_only=True)
    riskWeight = serializers.FloatField(source='risk_weight', read_only=True)
    complianceScoreWeight = serializers.FloatField(source='compliance_score_weight', read_only=True)
    legalReference = serializers.CharField(source='legal_reference', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ComplianceRequirement
        fields = ['id', 'framework', 'frameworkCode', 'frameworkName', 'requirement_code',
                  'requirementCode', 'requirement_name', 'requirementName', 'description',
                  'requirement_type', 'requirementType', 'criticality', 'detection_keywords',
                  'detectionKeywords', 'risk_weight', 'riskWeight', 'compliance_score_weight',
                  'complianceScoreWeight', 'legal_reference', 'legalReference', 'is_active',
                  'isActive', 'created_at', 'createdAt', 'updated_at', 'updatedAt']
        read_only_fields = ['id', 'created_at', 'updated_at']


class IntentComplianceMappingSerializer(serializers.ModelSerializer):
    """Serializer for intent-to-requirement compliance mappings"""
    intentName = serializers.CharField(source='intent.name', read_only=True)
    intentDescription = serializers.CharField(source='intent.description', read_only=True)
    requirementCode = serializers.CharField(source='requirement.requirement_code', read_only=True)
    requirementName = serializers.CharField(source='requirement.requirement_name', read_only=True)
    frameworkCode = serializers.CharField(source='requirement.framework.code', read_only=True)
    frameworkName = serializers.CharField(source='requirement.framework.name', read_only=True)
    criticality = serializers.CharField(source='requirement.criticality', read_only=True)
    relevanceScore = serializers.FloatField(source='relevance_score', read_only=True)
    complianceStatus = serializers.CharField(source='compliance_status', read_only=True)
    analysisSummary = serializers.CharField(source='analysis_summary', read_only=True)
    gapDescription = serializers.CharField(source='gap_description', read_only=True)
    riskScore = serializers.FloatField(source='risk_score', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = IntentComplianceMapping
        fields = ['id', 'intent', 'intentName', 'intentDescription', 'requirement',
                  'requirementCode', 'requirementName', 'frameworkCode', 'frameworkName',
                  'criticality', 'contract', 'relevance_score', 'relevanceScore',
                  'compliance_status', 'complianceStatus', 'analysis_summary', 'analysisSummary',
                  'gap_description', 'gapDescription', 'recommendation', 'risk_score',
                  'riskScore', 'created_at', 'createdAt', 'updated_at', 'updatedAt']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContractComplianceAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for contract-level compliance analysis summary"""
    overallComplianceScore = serializers.FloatField(source='overall_compliance_score', read_only=True)
    totalRequirementsChecked = serializers.IntegerField(source='total_requirements_checked', read_only=True)
    compliantCount = serializers.IntegerField(source='compliant_count', read_only=True)
    partialCount = serializers.IntegerField(source='partial_count', read_only=True)
    nonCompliantCount = serializers.IntegerField(source='non_compliant_count', read_only=True)
    frameworkScores = serializers.JSONField(source='framework_scores', read_only=True)
    complianceRiskScore = serializers.FloatField(source='compliance_risk_score', read_only=True)
    criticalViolations = serializers.IntegerField(source='critical_violations', read_only=True)
    highViolations = serializers.IntegerField(source='high_violations', read_only=True)
    mediumViolations = serializers.IntegerField(source='medium_violations', read_only=True)
    lowViolations = serializers.IntegerField(source='low_violations', read_only=True)
    analysisCompletedAt = serializers.DateTimeField(source='analysis_completed_at', read_only=True)
    analysisDurationSeconds = serializers.FloatField(source='analysis_duration_seconds', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ContractComplianceAnalysis
        fields = ['id', 'contract', 'overall_compliance_score', 'overallComplianceScore',
                  'total_requirements_checked', 'totalRequirementsChecked', 'compliant_count',
                  'compliantCount', 'partial_count', 'partialCount', 'non_compliant_count',
                  'nonCompliantCount', 'framework_scores', 'frameworkScores',
                  'compliance_risk_score', 'complianceRiskScore', 'critical_violations',
                  'criticalViolations', 'high_violations', 'highViolations', 'medium_violations',
                  'mediumViolations', 'low_violations', 'lowViolations', 'analysis_completed_at',
                  'analysisCompletedAt', 'analysis_duration_seconds', 'analysisDurationSeconds',
                  'created_at', 'createdAt', 'updated_at', 'updatedAt']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClauseRewriteSuggestionSerializer(serializers.ModelSerializer):
    clauseId = serializers.CharField(source='clause.id', read_only=True)
    clauseName = serializers.CharField(source='clause.clause_name', read_only=True)
    contractId = serializers.CharField(source='contract.id', read_only=True)
    originalText = serializers.CharField(source='original_text')
    suggestedText = serializers.CharField(source='suggested_text')
    impactAnalysis = serializers.CharField(source='impact_analysis', required=False, allow_null=True, allow_blank=True)
    negotiationTips = serializers.CharField(source='negotiation_tips', required=False, allow_null=True, allow_blank=True)
    confidenceScore = serializers.FloatField(source='confidence_score')
    createdBy = serializers.SerializerMethodField()
    reviewedBy = serializers.SerializerMethodField()
    reviewedAt = serializers.DateTimeField(source='reviewed_at', read_only=True, allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    def get_createdBy(self, obj):
        return obj.created_by.email if obj.created_by else None

    def get_reviewedBy(self, obj):
        return obj.reviewed_by.email if obj.reviewed_by else None

    class Meta:
        model = ClauseRewriteSuggestion
        fields = ['id', 'clauseId', 'clauseName', 'contractId', 'original_text', 'originalText',
                  'suggested_text', 'suggestedText', 'rationale', 'category', 'priority', 'status',
                  'impact_analysis', 'impactAnalysis', 'negotiation_tips', 'negotiationTips',
                  'confidence_score', 'confidenceScore', 'createdBy', 'reviewedBy', 'reviewedAt',
                  'created_at', 'createdAt', 'updated_at', 'updatedAt']
        read_only_fields = ['id', 'clauseId', 'clauseName', 'contractId', 'createdBy',
                            'reviewedBy', 'reviewedAt', 'created_at', 'updated_at']


# =========================
# SUPERADMIN USER MANAGEMENT SERIALIZERS
# =========================

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users with connector permissions.
    Only SuperAdmin can use this serializer.
    """
    password = serializers.CharField(write_only=True, required=True)
    roleId = serializers.CharField(source='role_id', write_only=True, required=True)
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    fivetranAccess = serializers.BooleanField(source='fivetran_access', default=False)
    kafkaAccess = serializers.BooleanField(source='kafka_access', default=False)
    sapAccess = serializers.BooleanField(source='sap_access', default=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'firstName', 'lastName', 'roleId',
                  'fivetranAccess', 'kafkaAccess', 'sapAccess', 'first_name', 'last_name']

    def create(self, validated_data):
        # Extract role_id from validated data
        role_id = validated_data.pop('role_id', None)

        # Create user instance
        user = User(**validated_data)

        # Assign role
        if role_id:
            try:
                from .models import Role
                user.role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                raise serializers.ValidationError({'roleId': 'Invalid role ID'})

        # Password is automatically hashed in User.save()
        user.save()
        return user


class UserManagementSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and managing users (SuperAdmin only).
    Includes connector permission fields.
    """
    role = RoleSerializer(read_only=True)
    roleId = serializers.CharField(source='role.id', read_only=True)
    roleName = serializers.CharField(source='role.name', read_only=True)
    firstName = serializers.CharField(source='first_name', read_only=True)
    lastName = serializers.CharField(source='last_name', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    lastLogin = serializers.DateTimeField(source='last_login', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    # Connector permissions
    fivetranAccess = serializers.BooleanField(source='fivetran_access', read_only=True)
    kafkaAccess = serializers.BooleanField(source='kafka_access', read_only=True)
    sapAccess = serializers.BooleanField(source='sap_access', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'firstName', 'lastName', 'role', 'roleId', 'roleName',
                  'isActive', 'lastLogin', 'createdAt', 'updatedAt', 'fivetranAccess',
                  'kafkaAccess', 'sapAccess', 'first_name', 'last_name', 'is_active', 'last_login',
                  'created_at', 'updated_at', 'fivetran_access', 'kafka_access', 'sap_access']
        read_only_fields = ['id', 'email', 'createdAt', 'lastLogin']


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user connector permissions (SuperAdmin only).
    """
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    roleId = serializers.CharField(source='role_id', required=False, write_only=True)
    fivetranAccess = serializers.BooleanField(source='fivetran_access', required=False)
    kafkaAccess = serializers.BooleanField(source='kafka_access', required=False)
    sapAccess = serializers.BooleanField(source='sap_access', required=False)
    isActive = serializers.BooleanField(source='is_active', required=False)

    class Meta:
        model = User
        fields = ['firstName', 'lastName', 'roleId', 'fivetranAccess', 'kafkaAccess',
                  'sapAccess', 'isActive', 'first_name', 'last_name', 'is_active']

    def update(self, instance, validated_data):
        # Update role if provided
        role_id = validated_data.pop('role_id', None)
        if role_id:
            try:
                from .models import Role
                instance.role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                raise serializers.ValidationError({'roleId': 'Invalid role ID'})

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
