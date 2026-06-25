"""
Force Majeure Intelligence Engine — URL Configuration
"""
from django.urls import path
from .radar_views import (
    FMRadarLiveEventsView,
    FMRiskMapView,
    FMContractExposureView,
    FMEventStreamView,
    FMWarIntelligenceView,
    FMPortfolioAlertsView,
    FMBalticDryView,
    FMAlertEngineView,
)
from .advanced_views import (
    FMCounterfactualView,
    FMPortfolioSimulateView,
    FMKnowledgeGraphView,
    FMDigitalTwinView,
    FMMultiAgentNegotiateView,
    FMSupplyChainMapView,
    FMDynamicPriorsView,
    FMRiskCascadeView,
    FMClauseOptimizerView,
    FMTemporalForecastView,
    FMRiskFormulaView,
    FMBulkAutoCorrectView,
    # New advanced features
    FMLLMClauseRewriteView,
    FMLLMGenerateClauseView,
    FMWarSupplyChainView,
    FMRouteClosureSimView,
    FMWarLossPredictionView,
    FMWarInsurancePremiumView,
    FMShippingDisruptionsView,
    FMCommodityPricesView,
    FMSanctionsCheckView,
    FMPoliticalRiskView,
    FMLaborStrikeRiskView,
    # Geopolitical & Portfolio
    FMGeopoliticalRiskView,
    FMConflictEscalationView,
    FMDiplomaticStabilityView,
    FMPortfolioSimulatorView,
    # Phase 4: Advanced Engines
    FMTemporalForecastAdvancedView,
    FMScenarioComparisonView,
    FMDigitalTwinCreateView,
    FMDigitalTwinSimulateView,
    FMDigitalTwinStatusView,
    FMDigitalTwinCompareView,
    FMDoInterventionView,
    FMCounterfactualQueryView,
    FMCausalEffectView,
    FMSensitivityAnalysisView,
    FMClauseOptimizeView,
    FMMultiPartyOptimizeView,
    # Approval Workflows
    FMApprovalRequestCreateView,
    FMApprovalApproveView,
    FMApprovalRejectView,
    FMApprovalStatusView,
    FMApprovalPendingView,
)
from .views import (
    FMPredictView,
    FMAuditClauseView,
    FMAutoCorrectView,
    FMWarRiskView,
    FMSimulateScenarioView,
    FMBulkAuditView,
    FMPredictionListView,
    FMPredictionDetailView,
    FMClauseAuditListView,
    FMAlertListView,
    FMAlertCreateView,
    FMBayesianGraphView,
    FMPortfolioSummaryView,
)

urlpatterns = [
    # Core prediction & analysis
    path('predict/', FMPredictView.as_view(), name='fm-predict'),
    path('audit-clause/', FMAuditClauseView.as_view(), name='fm-audit-clause'),
    path('auto-correct/', FMAutoCorrectView.as_view(), name='fm-auto-correct'),
    path('war-risk/', FMWarRiskView.as_view(), name='fm-war-risk'),
    path('simulate-scenario/', FMSimulateScenarioView.as_view(), name='fm-simulate-scenario'),
    path('bulk-audit/', FMBulkAuditView.as_view(), name='fm-bulk-audit'),

    # Data retrieval
    path('predictions/', FMPredictionListView.as_view(), name='fm-predictions'),
    path('predictions/<str:prediction_id>/', FMPredictionDetailView.as_view(), name='fm-prediction-detail'),
    path('clause-audits/', FMClauseAuditListView.as_view(), name='fm-clause-audits'),

    # Alerts
    path('alerts/', FMAlertListView.as_view(), name='fm-alerts'),
    path('alerts/create/', FMAlertCreateView.as_view(), name='fm-alert-create'),

    # Visualization data
    path('bayesian-graph/', FMBayesianGraphView.as_view(), name='fm-bayesian-graph'),

    # Portfolio
    path('portfolio-summary/', FMPortfolioSummaryView.as_view(), name='fm-portfolio-summary'),

    # ── Live Radar & Real-Time Data ──────────────────────────────────────────
    path('radar/live-events/', FMRadarLiveEventsView.as_view(), name='fm-radar-live-events'),
    path('radar/risk-map/', FMRiskMapView.as_view(), name='fm-radar-risk-map'),
    path('radar/contract-exposure/', FMContractExposureView.as_view(), name='fm-radar-contract-exposure'),
    path('radar/event-stream/', FMEventStreamView.as_view(), name='fm-radar-event-stream'),
    path('radar/war-intelligence/', FMWarIntelligenceView.as_view(), name='fm-radar-war-intelligence'),
    path('radar/portfolio-alerts/', FMPortfolioAlertsView.as_view(), name='fm-radar-portfolio-alerts'),

    # ── Advanced Features ─────────────────────────────────────────────────────
    path('counterfactual/', FMCounterfactualView.as_view(), name='fm-counterfactual'),
    path('portfolio-simulate/', FMPortfolioSimulateView.as_view(), name='fm-portfolio-simulate'),
    path('knowledge-graph/', FMKnowledgeGraphView.as_view(), name='fm-knowledge-graph'),
    path('digital-twin/', FMDigitalTwinView.as_view(), name='fm-digital-twin'),
    path('multi-agent-negotiate/', FMMultiAgentNegotiateView.as_view(), name='fm-multi-agent-negotiate'),
    path('supply-chain-map/', FMSupplyChainMapView.as_view(), name='fm-supply-chain-map'),

    # ── New Phase-2 Features ──────────────────────────────────────────────────
    path('dynamic-priors/', FMDynamicPriorsView.as_view(), name='fm-dynamic-priors'),
    path('risk-cascade/', FMRiskCascadeView.as_view(), name='fm-risk-cascade'),
    path('clause-optimizer/', FMClauseOptimizerView.as_view(), name='fm-clause-optimizer'),
    path('temporal-forecast/', FMTemporalForecastView.as_view(), name='fm-temporal-forecast'),
    path('risk-formula/', FMRiskFormulaView.as_view(), name='fm-risk-formula'),
    path('bulk-auto-correct/', FMBulkAutoCorrectView.as_view(), name='fm-bulk-auto-correct'),
    path('radar/baltic-dry/', FMBalticDryView.as_view(), name='fm-baltic-dry'),
    path('alert-engine/', FMAlertEngineView.as_view(), name='fm-alert-engine'),

    # ── NEW Advanced Features (LLM, War Loss, Data Sources) ───────────────────
    path('llm-clause-rewrite/', FMLLMClauseRewriteView.as_view(), name='fm-llm-clause-rewrite'),
    path('llm-generate-clause/', FMLLMGenerateClauseView.as_view(), name='fm-llm-generate-clause'),
    path('war-supply-chain/', FMWarSupplyChainView.as_view(), name='fm-war-supply-chain'),
    path('route-closure/', FMRouteClosureSimView.as_view(), name='fm-route-closure'),
    path('war-loss-prediction/', FMWarLossPredictionView.as_view(), name='fm-war-loss-prediction'),
    path('war-insurance-premium/', FMWarInsurancePremiumView.as_view(), name='fm-war-insurance-premium'),
    path('shipping-disruptions/', FMShippingDisruptionsView.as_view(), name='fm-shipping-disruptions'),
    path('commodity-prices/', FMCommodityPricesView.as_view(), name='fm-commodity-prices'),
    path('sanctions-check/', FMSanctionsCheckView.as_view(), name='fm-sanctions-check'),
    path('political-risk/', FMPoliticalRiskView.as_view(), name='fm-political-risk'),
    path('labor-strike-risk/', FMLaborStrikeRiskView.as_view(), name='fm-labor-strike-risk'),

    # ── Geopolitical & Portfolio (Latest) ─────────────────────────────────────
    path('geopolitical-risk/', FMGeopoliticalRiskView.as_view(), name='fm-geopolitical-risk'),
    path('conflict-escalation/', FMConflictEscalationView.as_view(), name='fm-conflict-escalation'),
    path('diplomatic-stability/', FMDiplomaticStabilityView.as_view(), name='fm-diplomatic-stability'),
    path('portfolio-simulator/', FMPortfolioSimulatorView.as_view(), name='fm-portfolio-simulator'),

    # ── Phase 4: Advanced Engines (Dynamic Bayesian, Digital Twin, Causal, Optimization) ──
    # Dynamic Bayesian Network (Temporal)
    path('temporal-forecast-advanced/', FMTemporalForecastAdvancedView.as_view(), name='fm-temporal-forecast-advanced'),
    path('scenario-comparison/', FMScenarioComparisonView.as_view(), name='fm-scenario-comparison'),

    # Contract Digital Twin
    path('digital-twin/create/', FMDigitalTwinCreateView.as_view(), name='fm-digital-twin-create'),
    path('digital-twin/simulate/', FMDigitalTwinSimulateView.as_view(), name='fm-digital-twin-simulate'),
    path('digital-twin/status/<str:twin_id>/', FMDigitalTwinStatusView.as_view(), name='fm-digital-twin-status'),
    path('digital-twin/compare-scenarios/', FMDigitalTwinCompareView.as_view(), name='fm-digital-twin-compare'),

    # Enhanced Counterfactual (Do-Calculus)
    path('do-intervention/', FMDoInterventionView.as_view(), name='fm-do-intervention'),
    path('counterfactual-query/', FMCounterfactualQueryView.as_view(), name='fm-counterfactual-query'),
    path('causal-effect/', FMCausalEffectView.as_view(), name='fm-causal-effect'),
    path('sensitivity-analysis/', FMSensitivityAnalysisView.as_view(), name='fm-sensitivity-analysis'),

    # Clause Optimization
    path('clause-optimize/', FMClauseOptimizeView.as_view(), name='fm-clause-optimize'),
    path('multi-party-optimize/', FMMultiPartyOptimizeView.as_view(), name='fm-multi-party-optimize'),

    # Approval Workflows
    path('approval/create/', FMApprovalRequestCreateView.as_view(), name='fm-approval-create'),
    path('approval/approve/', FMApprovalApproveView.as_view(), name='fm-approval-approve'),
    path('approval/reject/', FMApprovalRejectView.as_view(), name='fm-approval-reject'),
    path('approval/status/<str:request_id>/', FMApprovalStatusView.as_view(), name='fm-approval-status'),
    path('approval/pending/', FMApprovalPendingView.as_view(), name='fm-approval-pending'),
]
