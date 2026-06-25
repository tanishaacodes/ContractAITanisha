from django.contrib import admin
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
    CompanyProfile
)


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'title', 'estimated_value', 'submission_deadline', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'reference_number', 'organization']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TenderSection)
class TenderSectionAdmin(admin.ModelAdmin):
    list_display = ['tender', 'section_number', 'title', 'level']
    list_filter = ['level']
    search_fields = ['section_number', 'title']


@admin.register(TenderWorkItem)
class TenderWorkItemAdmin(admin.ModelAdmin):
    list_display = ['tender', 'item_code', 'description', 'category', 'quantity', 'unit', 'estimated_cost']
    list_filter = ['category']
    search_fields = ['item_code', 'description']


@admin.register(TenderEligibility)
class TenderEligibilityAdmin(admin.ModelAdmin):
    list_display = ['tender', 'min_turnover', 'min_projects', 'min_project_value']
    search_fields = ['tender__reference_number']


@admin.register(TenderRisk)
class TenderRiskAdmin(admin.ModelAdmin):
    list_display = ['tender', 'category', 'severity', 'severity_score', 'financial_exposure']
    list_filter = ['category', 'severity']
    search_fields = ['description']


@admin.register(TenderConflict)
class TenderConflictAdmin(admin.ModelAdmin):
    list_display = ['tender', 'clause_a_reference', 'clause_b_reference', 'contradiction_score']
    search_fields = ['clause_a', 'clause_b']


@admin.register(BidScenario)
class BidScenarioAdmin(admin.ModelAdmin):
    list_display = ['tender', 'margin_percentage', 'bid_price', 'win_probability', 'is_recommended']
    list_filter = ['is_recommended']


@admin.register(TenderProposal)
class TenderProposalAdmin(admin.ModelAdmin):
    list_display = ['tender', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TenderNegotiation)
class TenderNegotiationAdmin(admin.ModelAdmin):
    list_display = ['tender', 'issue_type', 'negotiation_status', 'acceptance_probability']
    list_filter = ['negotiation_status', 'issue_type']


@admin.register(PreBidQuestion)
class PreBidQuestionAdmin(admin.ModelAdmin):
    list_display = ['tender', 'category', 'question', 'is_submitted']
    list_filter = ['category', 'is_submitted']


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'annual_turnover', 'net_worth', 'total_projects_completed', 'past_win_rate']
    search_fields = ['company_name', 'registration_number']
