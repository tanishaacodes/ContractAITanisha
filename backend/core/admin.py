from django.contrib import admin
from .models import (
    Role, User, Contract, Clause, ComplianceFramework, ComplianceRequirement,
    IntentComplianceMapping, ContractComplianceAnalysis, ClauseRewriteSuggestion
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'created_at')
    list_filter = ('is_active', 'role', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'user', 'contract_type', 'confidence_score', 'uploaded_at')
    list_filter = ('contract_type', 'file_type', 'uploaded_at', 'ocr_performed')
    search_fields = ('original_filename', 'user__email')
    readonly_fields = ('id', 'filename', 'created_at', 'updated_at', 'uploaded_at')


@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('clause_name', 'contract', 'found', 'confidence', 'match_count')
    list_filter = ('found', 'confidence')
    search_fields = ('clause_name', 'contract__original_filename')
    readonly_fields = ('id', 'created_at', 'updated_at')


# =========================
# COMPLIANCE MAPPING ADMIN
# =========================

@admin.register(ComplianceFramework)
class ComplianceFrameworkAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'priority', 'created_at')
    list_filter = ('is_active', 'code', 'priority')
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Framework Info', {
            'fields': ('code', 'name', 'description', 'jurisdiction', 'version', 'priority')
        }),
        ('Settings', {
            'fields': ('is_active', 'effective_date')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ComplianceRequirement)
class ComplianceRequirementAdmin(admin.ModelAdmin):
    list_display = ('requirement_code', 'framework', 'requirement_type', 'criticality', 'is_active')
    list_filter = ('framework', 'criticality', 'requirement_type', 'is_active')
    search_fields = ('requirement_code', 'requirement_name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Requirement Info', {
            'fields': ('framework', 'requirement_code', 'requirement_name', 'description')
        }),
        ('Classification', {
            'fields': ('requirement_type', 'criticality', 'legal_reference')
        }),
        ('Scoring', {
            'fields': ('risk_weight', 'compliance_score_weight')
        }),
        ('Detection', {
            'fields': ('detection_keywords', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(IntentComplianceMapping)
class IntentComplianceMappingAdmin(admin.ModelAdmin):
    list_display = ('intent', 'requirement', 'compliance_status', 'risk_score', 'relevance_score')
    list_filter = ('compliance_status', 'requirement__criticality', 'requirement__framework', 'created_at')
    search_fields = ('intent__name', 'requirement__requirement_code', 'contract__original_filename')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Mapping', {
            'fields': ('intent', 'requirement', 'contract')
        }),
        ('Analysis Results', {
            'fields': ('relevance_score', 'compliance_status', 'analysis_summary')
        }),
        ('Gaps & Recommendations', {
            'fields': ('gap_description', 'recommendation')
        }),
        ('Scoring', {
            'fields': ('risk_score',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContractComplianceAnalysis)
class ContractComplianceAnalysisAdmin(admin.ModelAdmin):
    list_display = ('contract', 'overall_compliance_score', 'critical_violations', 'compliance_risk_score', 'analysis_completed_at')
    list_filter = ('analysis_completed_at', 'created_at')
    search_fields = ('contract__original_filename',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'framework_scores')
    fieldsets = (
        ('Contract', {
            'fields': ('contract',)
        }),
        ('Overall Scores', {
            'fields': ('overall_compliance_score', 'compliance_risk_score')
        }),
        ('Requirements Status', {
            'fields': ('total_requirements_checked', 'compliant_count', 'partial_count', 'non_compliant_count')
        }),
        ('Violations by Criticality', {
            'fields': ('critical_violations', 'high_violations', 'medium_violations', 'low_violations')
        }),
        ('Framework Breakdown', {
            'fields': ('framework_scores',),
            'classes': ('collapse',)
        }),
        ('Analysis Details', {
            'fields': ('analysis_completed_at', 'analysis_duration_seconds'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# =========================
# NEGOTIATION AGENT ADMIN
# =========================

@admin.register(ClauseRewriteSuggestion)
class ClauseRewriteSuggestionAdmin(admin.ModelAdmin):
    list_display = ('clause', 'category', 'priority', 'status', 'confidence_score', 'created_at')
    list_filter = ('category', 'priority', 'status', 'created_at')
    search_fields = ('clause__clause_name', 'contract__original_filename', 'rationale')
    readonly_fields = ('id', 'created_by', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at')
    fieldsets = (
        ('Clause Info', {
            'fields': ('clause', 'contract')
        }),
        ('Original & Suggested', {
            'fields': ('original_text', 'suggested_text', 'rationale')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'status', 'confidence_score')
        }),
        ('Analysis', {
            'fields': ('impact_analysis', 'negotiation_tips')
        }),
        ('Review', {
            'fields': ('created_by', 'reviewed_by', 'reviewed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
