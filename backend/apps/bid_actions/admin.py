"""
Django Admin Configuration for Bid Actions
"""
from django.contrib import admin
from .models import Department, ActionItem, RiskPropagation, DepartmentActionSummary


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'workload_weight', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'department', 'tender', 'priority',
        'status', 'risk_score', 'created_at'
    ]
    list_filter = ['department', 'priority', 'status', 'source_type', 'created_at']
    search_fields = ['title', 'description']
    autocomplete_fields = ['tender', 'department', 'assigned_to']
    filter_horizontal = ['depends_on']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('tender', 'department', 'title', 'description')
        }),
        ('Classification', {
            'fields': ('source_type', 'source_reference', 'priority', 'status')
        }),
        ('Risk & Complexity', {
            'fields': ('risk_score', 'complexity_score', 'financial_exposure')
        }),
        ('Dependencies & Assignment', {
            'fields': ('depends_on', 'assigned_to', 'due_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'completed_at']


@admin.register(RiskPropagation)
class RiskPropagationAdmin(admin.ModelAdmin):
    list_display = ['source_action', 'target_action', 'propagation_weight', 'created_at']
    list_filter = ['created_at']
    autocomplete_fields = ['source_action', 'target_action']


@admin.register(DepartmentActionSummary)
class DepartmentActionSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'tender', 'department', 'total_actions',
        'completed_actions', 'avg_risk_score', 'last_calculated'
    ]
    list_filter = ['department', 'last_calculated']
    autocomplete_fields = ['tender', 'department']
    readonly_fields = ['last_calculated']
