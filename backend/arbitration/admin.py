"""
Django Admin Interface for Arbitration Risk Intelligence
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ArbitrationAnalysis,
    ArbitrationClause,
    TribunalSimulation,
    ArbitrationScenario,
    HistoricalArbitrationCase,
    ClauseRewrite,
    GNNPrediction,
)


@admin.register(ArbitrationAnalysis)
class ArbitrationAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'contract_name', 'risk_level_badge', 'dispute_probability',
        'total_clauses', 'high_risk_clauses', 'expected_loss_display',
        'settlement_decision', 'created_at'
    ]
    list_filter = ['overall_risk_level', 'settlement_decision', 'created_at']
    search_fields = ['contract__original_filename', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Contract', {
            'fields': ('contract', 'analysis_version')
        }),
        ('Risk Summary', {
            'fields': (
                'total_clauses', 'high_risk_clauses', 'medium_risk_clauses', 'low_risk_clauses',
                'avg_composite_risk', 'dispute_probability', 'overall_risk_level'
            )
        }),
        ('Monte Carlo Results', {
            'fields': (
                'monte_carlo_runs', 'expected_loss', 'median_loss', 'p75_loss',
                'p90_loss', 'worst_case_p95', 'var_99', 'std_deviation'
            )
        }),
        ('Tribunal Simulation', {
            'fields': (
                'tribunal_runs', 'buyer_win_probability', 'supplier_win_probability',
                'partial_award_probability', 'settlement_probability', 'expected_award'
            )
        }),
        ('Exposure & Settlement', {
            'fields': (
                'arbitration_exposure', 'legal_cost_estimate', 'total_exposure',
                'settlement_offer', 'settlement_decision', 'potential_saving'
            )
        }),
        ('Optimal Configuration', {
            'fields': (
                'optimal_seat', 'optimal_tribunal', 'optimal_cost_rule',
                'optimal_institution', 'optimal_expected_cost'
            )
        }),
        ('GNN Predictions', {
            'fields': ('gnn_dispute_probability', 'gnn_confidence')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )

    def contract_name(self, obj):
        return obj.contract.original_filename
    contract_name.short_description = 'Contract'

    def risk_level_badge(self, obj):
        colors = {
            'LOW': '#10b981',
            'MEDIUM': '#f59e0b',
            'HIGH': '#f97316',
            'CRITICAL': '#ef4444',
        }
        color = colors.get(obj.overall_risk_level, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 500;">{}</span>',
            color, obj.overall_risk_level
        )
    risk_level_badge.short_description = 'Risk Level'

    def expected_loss_display(self, obj):
        return f"${obj.expected_loss:,.0f}"
    expected_loss_display.short_description = 'Expected Loss'


@admin.register(ArbitrationClause)
class ArbitrationClauseAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'analysis_link', 'clause_index', 'risk_level_badge',
        'composite_risk', 'pattern_hits', 'created_at'
    ]
    list_filter = ['risk_level', 'created_at']
    search_fields = ['clause_text', 'analysis__contract__original_filename']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Clause Info', {
            'fields': ('analysis', 'clause_index', 'clause_text', 'confidence', 'pattern_hits')
        }),
        ('Risk Vector', {
            'fields': (
                'jurisdiction_risk', 'cost_exposure', 'institutional_risk',
                'tribunal_structure', 'procedural_risk', 'enforcement_risk',
                'delay_dispute_risk', 'subcontractor_pass_through', 'composite_risk'
            )
        }),
        ('Classification', {
            'fields': ('risk_level',)
        }),
        ('Embeddings & Graph', {
            'fields': ('embedding', 'graph_node_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at')
        }),
    )

    def analysis_link(self, obj):
        return f"{obj.analysis.contract.original_filename[:30]}..."
    analysis_link.short_description = 'Analysis'

    def risk_level_badge(self, obj):
        colors = {'LOW': '#10b981', 'MEDIUM': '#f59e0b', 'HIGH': '#ef4444'}
        color = colors.get(obj.risk_level, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 500;">{}</span>',
            color, obj.risk_level
        )
    risk_level_badge.short_description = 'Risk'


@admin.register(TribunalSimulation)
class TribunalSimulationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'analysis_link', 'runs', 'buyer_win_prob', 'supplier_win_prob',
        'settlement_prob', 'expected_award_display', 'created_at'
    ]
    list_filter = ['created_at']
    readonly_fields = ['id', 'created_at']

    def analysis_link(self, obj):
        return str(obj.analysis)
    analysis_link.short_description = 'Analysis'

    def expected_award_display(self, obj):
        return f"${obj.expected_award:,.0f}"
    expected_award_display.short_description = 'Expected Award'


@admin.register(ArbitrationScenario)
class ArbitrationScenarioAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'seat', 'tribunal_size', 'cost_rule', 'institution',
        'expected_cost_display', 'is_optimal', 'is_worst', 'created_at'
    ]
    list_filter = ['is_optimal', 'is_worst', 'seat', 'institution']
    search_fields = ['analysis__contract__original_filename']
    readonly_fields = ['id', 'created_at']

    def expected_cost_display(self, obj):
        return f"${obj.expected_cost:,.0f}"
    expected_cost_display.short_description = 'Cost'


@admin.register(HistoricalArbitrationCase)
class HistoricalArbitrationCaseAdmin(admin.ModelAdmin):
    list_display = [
        'case_number', 'case_year', 'institution', 'seat', 'outcome_badge',
        'contract_value_display', 'award_percentage', 'duration_months',
        'used_for_training'
    ]
    list_filter = [
        'outcome', 'institution', 'case_year', 'contract_type',
        'used_for_training', 'has_delay_claims', 'has_liquidated_damages'
    ]
    search_fields = ['case_number', 'case_summary']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Case Metadata', {
            'fields': (
                'case_number', 'case_year', 'institution', 'seat',
                'governing_law', 'data_source'
            )
        }),
        ('Contract Details', {
            'fields': (
                'contract_type', 'contract_value', 'industry_sector'
            )
        }),
        ('Tribunal', {
            'fields': ('number_of_arbitrators', 'tribunal_composition')
        }),
        ('Dispute Characteristics', {
            'fields': (
                'has_delay_claims', 'has_liquidated_damages', 'has_cost_shifting',
                'has_subcontractor_dispute', 'has_multi_party'
            )
        }),
        ('Risk Scores', {
            'fields': (
                'jurisdiction_risk_score', 'enforcement_risk_score', 'procedural_complexity'
            )
        }),
        ('Outcome', {
            'fields': (
                'outcome', 'award_amount', 'award_percentage',
                'arbitration_cost', 'duration_months'
            )
        }),
        ('Text Data', {
            'fields': ('case_summary', 'key_issues')
        }),
        ('ML Features', {
            'fields': ('graph_features', 'clause_embedding', 'used_for_training'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )

    def outcome_badge(self, obj):
        colors = {
            'BUYER_WIN': '#10b981',
            'SUPPLIER_WIN': '#ef4444',
            'PARTIAL_AWARD': '#f59e0b',
            'SETTLEMENT': '#06b6d4',
            'DISMISSED': '#6b7280',
        }
        color = colors.get(obj.outcome, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 500;">{}</span>',
            color, obj.get_outcome_display()
        )
    outcome_badge.short_description = 'Outcome'

    def contract_value_display(self, obj):
        return f"${obj.contract_value:,.0f}"
    contract_value_display.short_description = 'Contract Value'


@admin.register(ClauseRewrite)
class ClauseRewriteAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'clause_link', 'risk_reduction_pct', 'status_badge',
        'llm_model', 'reviewed_by', 'created_at'
    ]
    list_filter = ['status', 'rewrite_strategy', 'llm_model', 'created_at']
    search_fields = ['original_text', 'rewritten_text', 'review_notes']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Clause', {
            'fields': ('clause',)
        }),
        ('Original', {
            'fields': ('original_text', 'original_risk_score')
        }),
        ('Rewritten', {
            'fields': ('rewritten_text', 'predicted_risk_score', 'risk_reduction', 'improvements')
        }),
        ('Rewrite Parameters', {
            'fields': ('rewrite_strategy', 'llm_model', 'temperature')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'review_notes')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )

    def clause_link(self, obj):
        return f"Clause {obj.clause.clause_index}"
    clause_link.short_description = 'Clause'

    def risk_reduction_pct(self, obj):
        return f"{obj.risk_reduction:.1%}"
    risk_reduction_pct.short_description = 'Risk Reduction'

    def status_badge(self, obj):
        colors = {
            'DRAFT': '#6b7280',
            'APPROVED': '#10b981',
            'REJECTED': '#ef4444',
            'IMPLEMENTED': '#06b6d4',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 500;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(GNNPrediction)
class GNNPredictionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'analysis_link', 'model_version', 'dispute_probability',
        'buyer_win_probability', 'prediction_confidence', 'inference_time_ms', 'created_at'
    ]
    list_filter = ['model_version', 'created_at']
    readonly_fields = ['id', 'created_at']

    fieldsets = (
        ('Analysis', {
            'fields': ('analysis',)
        }),
        ('Model', {
            'fields': ('model_version', 'model_checkpoint')
        }),
        ('Predictions', {
            'fields': (
                'dispute_probability', 'buyer_win_probability', 'supplier_win_probability',
                'partial_award_probability', 'settlement_probability'
            )
        }),
        ('Confidence', {
            'fields': ('prediction_confidence', 'model_certainty')
        }),
        ('Graph Features', {
            'fields': ('node_count', 'edge_count', 'avg_node_degree', 'graph_density')
        }),
        ('Explainability', {
            'fields': ('top_influential_clauses', 'attention_weights'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('inference_time_ms',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at')
        }),
    )

    def analysis_link(self, obj):
        return str(obj.analysis)
    analysis_link.short_description = 'Analysis'
