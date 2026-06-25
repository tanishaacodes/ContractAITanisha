from django.urls import path
from api import views
from api import classification_views
from api import approval_views
from api import clause_library_views
from api import alfresco_rag_views
from api import contract_operations
from api import agent_views
from api import payment_views
from api import redline_views
from api import embedding_views
from api import map_views
from api import drilldown_views
from api import embedding_model_views
from api import playbook_views
from api import obligation_views
from api import clause_views
from api import negotiation_views
from api import dashboard_views
from api import bulk_operations
from api import executive_views
from api import clause_drift_views
from api import intent_heatmap_views
from api import counterfactual_views
from api import loss_views
from api import self_healing_views
from api import graph_views
from api import live_copilot_views
from api import trust_views
from api import trust_propagation_views
from api import heat_views
from api import temporal_views
from api import risk_intelligence_views
from api import cuad_graph_views
from api import concept_graph_views
from api import arbitration_views
from api import legal_review_views
from api import cfo_analytics_views
from api import predictive_risk_views
from api import auto_redlining_views
from api import rrie_views
from api import search_intelligence_views
from api import search_intelligence_new_views
from api import ai_studio_views
from api import orchestrator_views
from api import contract_suite_views
from api import multimodal_views
from api import erp_execution_views
from api import advanced_clause_library_views


urlpatterns = [

    # =======================
    # Smart Contract Search & Intelligence
    # =======================
    path('search-intelligence/prebuilt/', search_intelligence_views.PrebuiltSearchView.as_view(), name='search_prebuilt_list'),
    path('search-intelligence/prebuilt/run/', search_intelligence_views.PrebuiltSearchView.as_view(), name='search_prebuilt_run'),
    path('search-intelligence/semantic/', search_intelligence_views.SemanticSearchView.as_view(), name='search_semantic'),
    path('search-intelligence/agent/', search_intelligence_views.AIAgentSearchView.as_view(), name='search_agent'),
    path('search-intelligence/analytics/', search_intelligence_views.SearchAnalyticsView.as_view(), name='search_analytics'),
    path('search-intelligence/negotiate/', search_intelligence_views.NegotiationAgentView.as_view(), name='search_negotiate'),
    path('search-intelligence/stats/', search_intelligence_views.ContractStatsView.as_view(), name='search_stats'),
    path('search-intelligence/graph-build/', search_intelligence_views.AutoGraphBuilderView.as_view(), name='search_graph_build'),
    path('search-intelligence/fm-score/', search_intelligence_views.ForceMajeureRiskScorerView.as_view(), name='search_fm_score'),
    path('search-intelligence/memory/', search_intelligence_views.NegotiationMemoryView.as_view(), name='search_memory'),
    path('search-intelligence/graph-multihop/', search_intelligence_views.GraphMultiHopView.as_view(), name='search_graph_multihop'),
    path('search-intelligence/graph-expand/<str:node_id>/', search_intelligence_views.GraphNodeExpandView.as_view(), name='search_graph_expand'),
    path('search-intelligence/benchmark/', search_intelligence_views.ClauseBenchmarkView.as_view(), name='search_benchmark'),
    path('search-intelligence/reclassify/', search_intelligence_views.BulkReclassifyView.as_view(), name='search_reclassify'),

    # New Advanced Features
    path('search-intelligence/legal-bert/', search_intelligence_new_views.LegalBERTClassificationView.as_view(), name='search_legal_bert'),
    path('search-intelligence/node2vec/', search_intelligence_new_views.Node2VecRecommendationsView.as_view(), name='search_node2vec'),
    path('search-intelligence/langchain-agent/', search_intelligence_new_views.LangChainAgentSearchView.as_view(), name='search_langchain_agent'),
    path('search-intelligence/temporal/', search_intelligence_new_views.TemporalAnalysisView.as_view(), name='search_temporal'),
    path('search-intelligence/anomaly/', search_intelligence_new_views.AnomalyDetectionView.as_view(), name='search_anomaly'),
    path('search-intelligence/realtime-sync/', search_intelligence_new_views.RealTimeGraphSyncView.as_view(), name='search_realtime_sync'),
    path('search-intelligence/cfo-metrics/', search_intelligence_new_views.CFOFinancialMetricsView.as_view(), name='search_cfo_metrics'),
    path('search-intelligence/party-attribution/', search_intelligence_new_views.PartyAttributionView.as_view(), name='search_party_attribution'),


    # =======================
    # Live Clause Co-Pilot (Negotiation Mode) - Feature 3
    # =======================
    path('copilot/sessions/', live_copilot_views.NegotiationSessionListView.as_view(), name='copilot_session_list'),
    path('copilot/sessions/<str:session_id>/', live_copilot_views.NegotiationSessionDetailView.as_view(), name='copilot_session_detail'),
    path('copilot/sessions/<str:session_id>/messages/', live_copilot_views.NegotiationMessageView.as_view(), name='copilot_send_message'),
    path('copilot/sessions/<str:session_id>/clauses/', live_copilot_views.NegotiationClauseListView.as_view(), name='copilot_clause_list'),

    # =======================
    # Neo4j Clause Evolution Graph Endpoints
    # =======================
    path('graph/status/', graph_views.GraphStatusView.as_view(), name='graph_status'),
    path('graph/initialize/', graph_views.GraphInitializeView.as_view(), name='graph_initialize'),
    path('graph/sync/', graph_views.GraphSyncView.as_view(), name='graph_sync_all'),
    path('graph/sync/<str:clause_id>/', graph_views.GraphSyncView.as_view(), name='graph_sync_clause'),
    path('graph/evolution/<str:clause_id>/', graph_views.ClauseEvolutionView.as_view(), name='clause_evolution'),
    path('graph/best-version/<str:clause_id>/', graph_views.ClauseBestVersionView.as_view(), name='clause_best_version'),

    # =======================
    # Self-Healing Clause Library Endpoints
    # =======================
    # Clause Health (specific routes BEFORE parameterized routes)
    path('clauses/health/report/', self_healing_views.ClauseHealthReportView.as_view(), name='clause_health_report'),
    path('clauses/health/', self_healing_views.ClauseHealthView.as_view(), name='clause_health_all'),
    path('clauses/health/<str:clause_id>/', self_healing_views.ClauseHealthView.as_view(), name='clause_health_detail'),

    # Auto-Promotion & Retirement
    path('clauses/promote/<str:clause_id>/', self_healing_views.ClausePromotionView.as_view(), name='clause_promote'),
    path('clauses/promote/batch/', self_healing_views.ClausePromotionView.as_view(), name='clause_promote_batch'),
    path('clauses/retire/', self_healing_views.ClauseRetirementView.as_view(), name='clause_retire'),

    # Analysis
    path('clauses/analyze/<str:clause_id>/', self_healing_views.ClauseAnalysisView.as_view(), name='clause_analyze'),

    # Events
    path('clauses/events/', self_healing_views.ClauseEventView.as_view(), name='clause_event_create'),
    path('clauses/events/<str:clause_version_id>/', self_healing_views.ClauseEventView.as_view(), name='clause_event_list'),

    # Similarity Search (RAG)
    path('clauses/similar/', self_healing_views.ClauseSimilarityView.as_view(), name='clause_similar'),


    # =======================
    # Payment & Subscription Endpoints
    # =======================
    # PayPal
    path('payments/paypal/create-order', payment_views.create_paypal_order, name='paypal_create_order'),
    path('payments/paypal/capture-order', payment_views.capture_paypal_order, name='paypal_capture_order'),

    # Stripe
    path('payments/stripe/create-intent', payment_views.create_stripe_payment_intent, name='stripe_create_intent'),
    path('payments/stripe/confirm', payment_views.confirm_stripe_payment, name='stripe_confirm_payment'),

    # Webhooks
    path('payments/stripe/webhook', payment_views.stripe_webhook, name='stripe_webhook'),
    path('payments/paypal/webhook', payment_views.paypal_webhook, name='paypal_webhook'),

    # Payment Info
    path('payments/history', payment_views.get_payment_history, name='payment_history'),
    path('subscription/current', payment_views.get_current_subscription, name='current_subscription'),

    # =======================
    # Auth endpoints
    # =======================
    path('auth/register', views.register),
    path('auth/login', views.login),
    path('auth/me', views.get_current_user),
    path('auth/update-profile', views.update_profile),

    # =======================
    # Dashboard Metrics
    # =======================
    path('dashboard/header', dashboard_views.DashboardHeaderView.as_view(), name='dashboard_header'),
    path('dashboard/debug', dashboard_views.DashboardDebugView.as_view(), name='dashboard_debug'),
    path('dashboard/contracts', dashboard_views.DashboardContractsListView.as_view(), name='dashboard_contracts_list'),
    path('dashboard/low-confidence-contracts', dashboard_views.LowConfidenceContractsView.as_view(), name='low_confidence_contracts'),
    path('dashboard/longest-review-contracts', dashboard_views.LongestReviewContractsView.as_view(), name='longest_review_contracts'),

    # =======================
    # Executive Snapshot (CXO / Board Mode)
    # =======================
    path('executive/exposure', executive_views.ExecutiveExposureView.as_view(), name='executive_exposure'),
    path('executive/risk-trend', executive_views.ExecutiveRiskTrendView.as_view(), name='executive_risk_trend'),
    path('executive/risk-drivers', executive_views.ExecutiveRiskDriversView.as_view(), name='executive_risk_drivers'),
    path('executive/loss-risk', executive_views.ExecutiveLossRiskView.as_view(), name='executive_loss_risk'),
    path('executive/interventions', executive_views.ExecutiveInterventionsView.as_view(), name='executive_interventions'),
    path('executive/risk-value-matrix', executive_views.RiskValueMatrixView.as_view(), name='risk_value_matrix'),
    path('executive/risk-value-matrix-filters', executive_views.RiskValueMatrixFiltersView.as_view(), name='risk_value_matrix_filters'),
    path('executive/clustering-galaxy', executive_views.ContractClusteringGalaxyView.as_view(), name='clustering_galaxy'),

    # =======================
    # Counterfactual & What-If Simulation
    # =======================
    path('counterfactual/simulate', counterfactual_views.CounterfactualSimulationView.as_view(), name='counterfactual_simulate'),
    path('counterfactual/contracts', counterfactual_views.ContractListForSimulationView.as_view(), name='counterfactual_contracts'),

    # =======================
    # Loss Prediction & Liability Sentinel
    # =======================
    path('loss-sentinel/dashboard', loss_views.LossSentinelDashboardView.as_view(), name='loss_sentinel_dashboard'),
    path('loss-sentinel/unlimited-watchlist', loss_views.UnlimitedLiabilityWatchlistView.as_view(), name='unlimited_watchlist'),

    # =======================
    # Pricing Plans & Subscription
    # =======================
    path('pricing/plans', views.get_pricing_plans),
    path('user/subscription', views.get_user_subscription),
    path('user/select-plan', views.select_plan),
    path('user/upgrade-plan', views.upgrade_plan),

    # =======================
    # Contract endpoints
    # =======================
    path('contracts/upload', views.upload_contract),
    path('contracts/upload-folder', views.upload_folder_view),
    path('contracts/list', views.list_contracts),
    path('contracts/list/', views.list_contracts),

    # Bulk Operations
    path('contracts/bulk-delete', bulk_operations.BulkDeleteContractsView.as_view(), name='bulk_delete_contracts'),
    path('contracts/delete-all', bulk_operations.BulkDeleteAllContractsView.as_view(), name='delete_all_contracts'),
    path('contracts/search', views.search_contracts),
    path('contracts/compare', views.compare_contracts_view),
    path('contracts/compare-upload', views.compare_contracts_upload),
    path('contracts/refresh-all-metadata', views.refresh_all_metadata),
    path('contracts/<uuid:contract_id>', views.get_contract),
    path('contracts/<uuid:contract_id>/status', views.update_contract_status),
    path('contracts/<uuid:contract_id>/delete', views.delete_contract_by_id),
    path('contracts/<uuid:contract_id>/versions', views.get_contract_versions),
    path('contracts/<uuid:contract_id>/versions/upload', views.upload_contract_version),
    path('contracts/<uuid:contract_id>/assign', views.assign_contract),
    path('contracts/<str:filename>', views.delete_contract),

    # =======================
    # Clause endpoints
    # =======================
    path('contracts/<uuid:contract_id>/extract-clauses', views.extract_clauses_view),
    path('contracts/<uuid:contract_id>/clauses', views.get_clauses),
    path('contracts/<uuid:contract_id>/refresh-metadata', views.refresh_contract_metadata),

    # Clause Addition (AI-Powered)
    path('contracts/<uuid:contract_id>/clauses/add', clause_views.add_clause_to_contract, name='add_clause_to_contract'),
    path('contracts/<uuid:contract_id>/clauses/simulate-addition', clause_views.simulate_clause_addition, name='simulate_clause_addition'),
    path('clauses/<uuid:clause_id>/delete', clause_views.delete_clause, name='delete_clause'),

    # Clause Rewriting (AI-Powered)
    path('clauses/<uuid:clause_id>/rewrite', clause_views.rewrite_clause_with_ai, name='rewrite_clause_ai'),
    path('clauses/<uuid:clause_id>/apply-rewrite', clause_views.apply_clause_rewrite, name='apply_clause_rewrite'),

    # =======================
    # Clause Library (AI-Powered)
    # =======================
    path('contracts/<uuid:contract_id>/clause-library/process', clause_library_views.process_contract_clause_library),
    path('contracts/<uuid:contract_id>/clause-library', clause_library_views.get_clause_library),
    path('clause-library/search', clause_library_views.search_similar_clauses),
    path('clause-library/hybrid-search', clause_library_views.hybrid_search_clauses),
    path('clause-library/qdrant-stats', clause_library_views.get_qdrant_stats),
    path('clauses/<str:clause_id>/full-text/', clause_library_views.get_full_clause_text),

    # =======================
    # Advanced Clause Library (Taxonomy Engine)
    # =======================
    path('acl/seed/', advanced_clause_library_views.seed_taxonomy),
    path('acl/tree/', advanced_clause_library_views.get_taxonomy_tree),
    path('acl/analytics/', advanced_clause_library_views.get_analytics),
    path('acl/process/<str:contract_id>/', advanced_clause_library_views.process_contract),
    path('acl/search/', advanced_clause_library_views.search_clauses),
    path('acl/clean/', advanced_clause_library_views.clean_taxonomy),
    path('acl/categories/', advanced_clause_library_views.list_categories),
    path('acl/clauses/<str:category_name>/', advanced_clause_library_views.clauses_in_category),
    path('acl/graph/', advanced_clause_library_views.get_neo4j_graph),
    path('acl/insights/<str:category_name>/', advanced_clause_library_views.clause_insights),
    path('acl/score-risk/', advanced_clause_library_views.score_clause_risk),
    path('acl/negotiate/', advanced_clause_library_views.negotiate_clause),
    path('acl/contract-risk/', advanced_clause_library_views.contract_risk_view),
    path('acl/process-all/', advanced_clause_library_views.process_all_contracts),

    # =======================
    # RRIE (Risk & Responsibility Intelligence Engine)
    # =======================
    path('rrie/contracts/<str:contract_id>/process', rrie_views.process_contract_rrie, name='rrie_process'),
    path('rrie/contracts/<str:contract_id>/analysis', rrie_views.get_rrie_analysis, name='rrie_analysis'),
    path('rrie/explain', rrie_views.explain_clause, name='rrie_explain'),
    path('rrie/clauses/<str:clause_id>/risk-breakdown', rrie_views.get_risk_breakdown, name='rrie_risk_breakdown'),
    path('rrie/contracts/<str:contract_id>/clauses', rrie_views.get_clause_table, name='rrie_clause_table'),
    path('rrie/contracts/<str:contract_id>/clauses/', rrie_views.get_clause_table),
    path('rrie/contracts/<str:contract_id>/heatmap', rrie_views.get_risk_heatmap, name='rrie_heatmap'),
    path('rrie/contracts/<str:contract_id>/heatmap/', rrie_views.get_risk_heatmap),
    path('rrie/contracts/<str:contract_id>/insights', rrie_views.get_ai_insights, name='rrie_insights'),
    path('rrie/contracts/<str:contract_id>/insights/', rrie_views.get_ai_insights),
    path('rrie/contracts/<str:contract_id>/deal-score', rrie_views.get_deal_score, name='rrie_deal_score'),
    path('rrie/contracts/<str:contract_id>/deal-score/', rrie_views.get_deal_score),
    path('rrie/contracts/<str:contract_id>/graph', rrie_views.get_contract_graph, name='rrie_graph'),
    path('rrie/contracts/<str:contract_id>/graph/', rrie_views.get_contract_graph),
    path('rrie/contracts/<str:contract_id>/rl-negotiation', rrie_views.get_rl_negotiation, name='rrie_rl_negotiation'),
    path('rrie/contracts/<str:contract_id>/rl-negotiation/', rrie_views.get_rl_negotiation),

    # =======================
    # Clause Drift Detection (Cross-Contract BERT similarity)
    # =======================
    path('clause-library/drift/summary/', clause_drift_views.CrossContractDriftView.as_view(), name='drift_summary'),
    path('clause-library/drift/type/', clause_drift_views.DriftByTypeView.as_view(), name='drift_by_type'),
    path('clause-library/drift/timeline/', clause_drift_views.DriftTimelineView.as_view(), name='drift_timeline'),
    path('clause-library/drift/matrix/', clause_drift_views.DriftMatrixView.as_view(), name='drift_matrix'),

    # =======================
    # CFO Financial Analytics Dashboard
    # =======================
    path('analytics/cfo/summary/', cfo_analytics_views.CFOSummaryView.as_view(), name='cfo_summary'),
    path('analytics/cfo/loss-by-type/', cfo_analytics_views.LossByClauseTypeView.as_view(), name='cfo_loss_by_type'),
    path('analytics/cfo/loss-by-contract/', cfo_analytics_views.LossByContractView.as_view(), name='cfo_loss_by_contract'),
    path('analytics/cfo/cash-flow/', cfo_analytics_views.CashFlowProjectionView.as_view(), name='cfo_cash_flow'),
    path('analytics/cfo/risk-heatmap/', cfo_analytics_views.RiskHeatmapView.as_view(), name='cfo_risk_heatmap'),

    # =======================
    # Predictive Risk Engine
    # =======================
    path('analytics/predictive-risk/', predictive_risk_views.PredictiveRiskAllView.as_view(), name='predictive_risk_all'),
    path('analytics/predictive-risk/<str:clause_type>/', predictive_risk_views.PredictiveRiskByTypeView.as_view(), name='predictive_risk_by_type'),

    # =======================
    # Auto Contract Redlining
    # =======================
    path('contracts/<uuid:contract_id>/redline/', auto_redlining_views.ContractRedlineView.as_view(), name='contract_redline'),
    path('contracts/<uuid:contract_id>/redline/export/', auto_redlining_views.RedlineExportView.as_view(), name='contract_redline_export'),
    path('clauses/<str:clause_id>/redline/', auto_redlining_views.ClauseRedlineView.as_view(), name='clause_redline'),

    # =======================
    # Risk Analysis
    # =======================
    path('contracts/<uuid:contract_id>/analyze-risk', views.analyze_contract_risk_view),
    path('contracts/<uuid:contract_id>/risk-analysis', views.get_contract_risk_analysis),
    path('contracts/<uuid:contract_id>/explain-risks', views.explain_contract_risks),
    path('contracts/<uuid:contract_id>/keyword-sentences', views.get_keyword_sentences),
    path('contracts/<uuid:contract_id>/generate-summary', views.generate_executive_summary_view),

    # =======================
    # Risky Clause Redlining
    # =======================
    path('contracts/<uuid:contract_id>/risky-clauses', views.get_risky_clauses_view),
    path('contracts/clauses/<str:clause_id>/auto-correct', views.auto_correct_clause_view),
    path('contracts/clauses/<str:clause_id>/accept-suggestion', views.accept_clause_suggestion_view),
    path('contracts/<uuid:contract_id>/download-modified', views.download_modified_contract_view),

    # =======================
    # Obligations
    # =======================
    path('contracts/<uuid:contract_id>/obligations', views.get_contract_obligations),
    path('contracts/<uuid:contract_id>/generate-obligations', views.generate_obligations_view),
    path('obligations/<uuid:obligation_id>/update', views.update_obligation_status),

    # New Obligation Extraction (AI-Powered)
    path('contracts/<uuid:contract_id>/obligations/extract', obligation_views.extract_obligations_from_contract, name='extract_contract_obligations'),
    path('clauses/<uuid:clause_id>/obligations/extract', obligation_views.extract_obligations_from_clause, name='extract_clause_obligations'),
    path('contracts/<uuid:contract_id>/obligations/list', obligation_views.list_contract_obligations, name='list_contract_obligations'),
    path('obligations/<uuid:obligation_id>/complete', obligation_views.mark_obligation_complete, name='mark_obligation_complete'),

    # =======================
    # Dashboard
    # =======================
    path('dashboard/stats', views.get_dashboard_stats),

    # =======================
    # RAG
    # =======================
    path('rag/upload', views.rag_upload_files),
    path('rag/upload-extract', views.rag_upload_extract),  # Upload and extract text from reference contract
    path('rag/ingest', views.rag_ingest),
    path('rag/qa', views.rag_qa),
    path('rag/generate', views.rag_generate),  # Modify contract text based on instructions
    path('rag/generate-from-samples', views.rag_generate_from_samples),  # Generate new contract from indexed samples
    path('rag/generate-pdf', views.generate_contract_pdf),  # Generate PDF from modified contract text
    path('rag/chat', views.unified_rag_chat),  # Unified chat across all user contracts
    path('rag/stats', views.rag_collection_stats),  # Get vector database statistics

    # =======================
    # AI Chat Improvements
    # =======================
    path('chat/conversations', views.get_conversations),  # Get all conversations
    path('chat/conversations/<str:conversation_id>/messages', views.get_conversation_messages),  # Get conversation messages
    path('chat/suggested-questions', views.get_suggested_questions),  # Get suggested questions
    path('chat/analytics', views.get_chat_analytics),  # Get chat analytics

    # =======================
    # Intent Mining
    # =======================
    path('contracts/<uuid:contract_id>/intents/analyze', views.analyze_contract_intents),
    path('contracts/<uuid:contract_id>/intents', views.get_contract_intents),
    path('intents', views.get_all_intents),
    path('intents/analytics', views.get_intent_analytics),
    path('portfolio/risk', views.get_portfolio_risk_score),  # NEW: Portfolio risk aggregation

    # =======================
    # Compliance
    # =======================
    path('contracts/<uuid:contract_id>/compliance/analyze', views.analyze_contract_compliance),
    path('contracts/<uuid:contract_id>/compliance', views.get_contract_compliance),
    path('compliance/dashboard', views.get_compliance_dashboard),
    path('compliance/frameworks', views.get_compliance_frameworks),

    # =======================
    # Knowledge Graph
    # =======================
    path('contracts/<uuid:contract_id>/sync-to-graph', views.sync_contract_to_graph),
    path('contracts/<uuid:contract_id>/graph', views.get_contract_graph),
    path('contracts/<uuid:contract_id>/similar', views.find_similar_contracts_graph),
    path('knowledge-graph/query', views.query_knowledge_graph),

    # Graph Intelligence Dashboard (Phase 1)
    path('contracts/<uuid:contract_id>/graph-dashboard', views.contract_graph_dashboard, name='contract_graph_dashboard'),

    # =======================
    # Negotiation & Intent Drift
    # =======================
    path('contracts/<uuid:contract_id>/drift-timeline', views.get_drift_timeline),
    path('contracts/<uuid:contract_id>/versions/<uuid:version1_id>/compare/<uuid:version2_id>', views.compare_contract_versions),
    path('contracts/<uuid:contract_id>/negotiation-suggestions', views.get_negotiation_suggestions),
    path('contracts/<uuid:contract_id>/clauses/<uuid:clause_id>/analyze-negotiation', views.analyze_clause_for_negotiation),
    path('negotiation-suggestions/<uuid:suggestion_id>/update-status', views.update_negotiation_suggestion_status),

    # AI-Powered Negotiation & Counter-Proposals
    path('clauses/<uuid:clause_id>/counter-proposal', negotiation_views.generate_counter_proposal, name='generate_counter_proposal'),
    path('clauses/<uuid:clause_id>/analyze-negotiation', negotiation_views.analyze_clause_for_negotiation, name='analyze_clause_negotiation'),
    path('contracts/<uuid:contract_id>/analyze-for-negotiation', negotiation_views.batch_analyze_contract_for_negotiation, name='batch_analyze_negotiation'),
    path('counterparties/<uuid:counterparty_id>/profile', negotiation_views.get_counterparty_profile, name='counterparty_profile'),

    # =======================
    # ✅ CONTRACT CLASSIFICATION (FINAL & STABLE)
    # =======================
    path(
        'contracts/classify/',
        classification_views.contract_classify_list,
        name='contract_classify_list'
    ),
    path(
        'contracts/classify/<uuid:contract_id>/',
        classification_views.classify_contract_view,
        name='classify_contract'
    ),
    path(
        'contracts/classify/portfolio-risk/',
        classification_views.portfolio_risk_map,
        name='portfolio_risk_map'
    ),

    path(
        "contracts/classify/clusters/",
        classification_views.contract_clusters_view,
        name="contract_clusters"
    ),

    # =======================
    # ✅ ROLE-BASED APPROVALS
    # =======================
    path('approvals/inbox', approval_views.get_approval_inbox, name='approval_inbox'),
    path('approvals/stats', approval_views.get_approval_stats, name='approval_stats'),
    path('approvals/contracts/<uuid:contract_id>/initiate', approval_views.initiate_workflow, name='initiate_workflow'),
    path('approvals/contracts/<uuid:contract_id>', approval_views.get_contract_approvals, name='get_contract_approvals'),
    path('approvals/contracts/<uuid:contract_id>/timeline', approval_views.get_approval_timeline, name='approval_timeline'),
    path('approvals/tasks/<uuid:task_id>/approve', approval_views.approve_approval_task, name='approve_task'),
    path('approvals/tasks/<uuid:task_id>/reject', approval_views.reject_approval_task, name='reject_task'),

    # =======================
    # Clause Heatmap
    # =======================
    path('clause-heatmap/portfolio', views.get_clause_heatmap, name='clause_heatmap_portfolio'),
    path('contracts/<uuid:contract_id>/clauses/enrich', views.enrich_contract_clauses, name='enrich_contract_clauses'),

    # =======================
    # Alfresco Integration & RAG
    # =======================
    path('alfresco/health', alfresco_rag_views.alfresco_health, name='alfresco_health'),
    path('alfresco/sync', alfresco_rag_views.sync_contracts_from_alfresco, name='alfresco_sync'),
    path('alfresco/sync/status/<str:task_id>', alfresco_rag_views.sync_status, name='alfresco_sync_status'),
    path('alfresco/query', alfresco_rag_views.query_contracts, name='alfresco_query'),
    path('alfresco/contracts/<uuid:contract_id>/intelligence', alfresco_rag_views.contract_intelligence, name='contract_intelligence'),
    path('alfresco/contracts/<uuid:contract_id>/extract', alfresco_rag_views.extract_contract_intelligence, name='extract_intelligence'),

    # =======================
    # Contract Operations - Download & Bulk Actions
    # =======================
    path('contracts/<uuid:contract_id>/download', contract_operations.download_contract, name='download_contract'),
    path('contracts/bulk/extract-intelligence', contract_operations.bulk_extract_intelligence, name='bulk_extract_intelligence'),
    path('contracts/bulk/risk-analysis', contract_operations.bulk_risk_analysis, name='bulk_risk_analysis'),

    # =======================
    # Clause Editing
    # =======================
    path('contracts/<uuid:contract_id>/clauses/edit', views.get_contract_clauses_for_editing, name='get_clauses_for_editing'),
    path('clauses/<uuid:clause_id>/edit', views.update_clause_text, name='update_clause'),
    path('clauses/<uuid:clause_id>/versions', views.get_clause_version_history, name='clause_version_history'),
    path('contracts/<uuid:contract_id>/regenerate', views.regenerate_modified_contract, name='regenerate_contract'),
    path('contract-versions/<uuid:version_id>/download', views.download_modified_contract, name='download_contract_version'),

    # =======================
    # AI Suggestions
    # =======================
    path('ai/suggest-improvement', views.get_ai_suggestion, name='ai_suggest_improvement'),
    path('ai/suggest-alternatives', views.get_ai_alternatives, name='ai_suggest_alternatives'),

    # =======================
    # Agentic AI System (2026)
    # =======================
    path('agent/health', agent_views.agent_health, name='agent_health'),
    path('agent/contracts/<uuid:contract_id>/analyze', agent_views.analyze_with_agent, name='agent_analyze'),
    path('agent/contracts/<uuid:contract_id>/results', agent_views.get_agent_analysis, name='agent_results'),

    # Quick agent actions (optimized endpoints)
    path('agent/contracts/<uuid:contract_id>/quick-risk', agent_views.quick_risk_score, name='agent_quick_risk'),
    path('agent/contracts/<uuid:contract_id>/quick-intent', agent_views.quick_intent_mine, name='agent_quick_intent'),
    path('agent/contracts/<uuid:contract_id>/quick-summary', agent_views.quick_summary, name='agent_quick_summary'),
    path('agent/contracts/<uuid:contract_id>/quick-classify', agent_views.quick_classify, name='agent_quick_classify'),
    path('agent/contracts/<uuid:contract_id>/quick-extract', agent_views.quick_extract_clauses, name='agent_quick_extract'),

    # =======================
    # Contract Redlining (Enhanced)
    # =======================
    # Session management
    path('redline/sessions', redline_views.list_redline_sessions, name='list_redline_sessions'),
    path('redline/contracts/<uuid:contract_id>/start', redline_views.start_redline_session, name='start_redline_session'),
    path('redline/contracts/<uuid:contract_id>/sessions', redline_views.get_contract_redline_sessions, name='get_contract_redline_sessions'),
    path('redline/sessions/<str:session_id>', redline_views.get_redline_session, name='get_redline_session'),
    path('redline/sessions/<str:session_id>/complete', redline_views.complete_redline_session, name='complete_redline_session'),

    # Change management
    path('redline/changes/<str:change_id>/update', redline_views.update_redline_change, name='update_redline_change'),
    path('redline/changes/<str:change_id>/regenerate', redline_views.regenerate_suggestion, name='regenerate_suggestion'),
    path('redline/changes/<str:change_id>/legal-analysis', redline_views.get_legal_analysis, name='get_legal_analysis'),

    # Export
    path('redline/sessions/<str:session_id>/export/docx', redline_views.export_redline_docx, name='export_redline_docx'),
    path('redline/sessions/<str:session_id>/export/pdf', redline_views.export_redline_pdf, name='export_redline_pdf'),

    # =======================
    # EMBEDDING-BASED AI (No LLM, Deterministic)
    # =======================
    # Risk Scoring
    path('embedding/contracts/<uuid:contract_id>/analyze-risk', embedding_views.analyze_risk_embedding, name='embedding_analyze_risk'),
    path('embedding/clauses/<uuid:clause_id>/score-risk', embedding_views.score_clause_risk, name='embedding_score_clause_risk'),

    # Intent Detection
    path('embedding/contracts/<uuid:contract_id>/detect-intents', embedding_views.detect_contract_intents, name='embedding_detect_intents'),
    path('embedding/clauses/<uuid:clause_id>/detect-intent', embedding_views.detect_clause_intent, name='embedding_detect_clause_intent'),
    path('embedding/contracts/<uuid:contract_id>/find-by-intent', embedding_views.find_clauses_by_intent, name='embedding_find_by_intent'),

    # Redlining (Approved Clause Library)
    path('embedding/contracts/<uuid:contract_id>/suggest-redlines', embedding_views.suggest_contract_redlines, name='embedding_suggest_redlines'),
    path('embedding/clauses/<uuid:clause_id>/suggest-redline', embedding_views.suggest_clause_redline, name='embedding_suggest_clause_redline'),

    # Chat (Pure Semantic Retrieval)
    path('embedding/contracts/<uuid:contract_id>/query', embedding_views.query_contract_embedding, name='embedding_query_contract'),
    path('embedding/contracts/query-multiple', embedding_views.query_multiple_contracts, name='embedding_query_multiple'),
    path('embedding/contracts/<uuid:contract_id>/suggest-questions', embedding_views.suggest_questions, name='embedding_suggest_questions'),

    # Admin - Manage Libraries
    path('embedding/admin/risk-playbooks', embedding_views.manage_risk_playbooks, name='manage_risk_playbooks'),
    path('embedding/admin/intent-templates', embedding_views.manage_intent_templates, name='manage_intent_templates'),
    path('embedding/admin/approved-clauses', embedding_views.manage_approved_clauses, name='manage_approved_clauses'),
    path('embedding/admin/gold-standards', embedding_views.create_gold_standard_template, name='create_gold_standard'),
    path('embedding/admin/expected-obligations', embedding_views.create_expected_obligation, name='create_expected_obligation'),

    # Feature 1: Deviation Detection
    path('embedding/clauses/<uuid:clause_id>/analyze-deviation', embedding_views.analyze_clause_deviation, name='embedding_analyze_clause_deviation'),
    path('embedding/contracts/<uuid:contract_id>/analyze-deviations', embedding_views.analyze_contract_deviations, name='embedding_analyze_contract_deviations'),
    path('embedding/clauses/<uuid:clause_id>/deviation-score', embedding_views.get_clause_deviation_score, name='embedding_get_deviation_score'),

    # Feature 2: Missing Safeguard Detection
    path('embedding/contracts/<uuid:contract_id>/detect-safeguards', embedding_views.detect_missing_safeguards, name='embedding_detect_safeguards'),
    path('embedding/contracts/<uuid:contract_id>/safeguard-table', embedding_views.get_safeguard_summary_table, name='embedding_safeguard_table'),

    # Feature 3: Risk Heatmap
    path('embedding/contracts/<uuid:contract_id>/risk-heatmap', embedding_views.get_contract_risk_heatmap, name='embedding_risk_heatmap'),

    # =======================
    # Intelligent Clustering Maps (Gartner-style Quadrants)
    # =======================
    path('maps/risk-value/', map_views.risk_value_map, name='risk_value_map'),
    path('maps/risk-liability/', map_views.risk_liability_map, name='risk_liability_map'),
    path('maps/geo-value/', map_views.geo_value_map, name='geo_value_map'),
    path('maps/ip-liability/', map_views.ip_liability_map, name='ip_liability_map'),
    path('maps/strategic/', map_views.strategic_quadrant_map, name='strategic_quadrant_map'),

    # Version & Time Slider
    path('maps/versions/', map_views.get_available_versions, name='get_available_versions'),
    path('maps/timeline/<uuid:contract_id>/', map_views.contract_risk_timeline, name='contract_risk_timeline'),

    # =======================
    # Clause Drill-Down (Click dot → See risky clauses)
    # =======================
    path('contracts/<uuid:contract_id>/clauses/drilldown/', drilldown_views.contract_clause_drilldown, name='contract_clause_drilldown'),
    path('contracts/<uuid:contract_id>/clauses/high-risk/', drilldown_views.high_risk_clauses_only, name='high_risk_clauses_only'),
    path('contracts/<uuid:contract_id>/clauses/auto-redline/', drilldown_views.auto_redline_high_risk, name='auto_redline_high_risk'),
    path('clauses/search/', drilldown_views.clause_search, name='clause_search'),

    # =======================
    # Portfolio-Level Counterparty Risk Heatmap
    # =======================
    path('counterparty/portfolio-heatmap', views.get_counterparty_portfolio_heatmap, name='counterparty_portfolio_heatmap'),
    path('contracts/<uuid:contract_id>/portfolio-risk-detail', views.get_contract_portfolio_risk_detail, name='contract_portfolio_risk_detail'),

    # =======================
    # What-If Simulation & Exposure Analysis
    # =======================
    path('contracts/<uuid:contract_id>/what-if/remove-clause', views.what_if_remove_clause, name='what_if_remove_clause'),
    path('contracts/<uuid:contract_id>/what-if/batch-removal', views.what_if_batch_removal, name='what_if_batch_removal'),
    path('contracts/<uuid:contract_id>/exposure-analysis', views.get_exposure_analysis, name='exposure_analysis'),
    path('contracts/<uuid:contract_id>/monte-carlo-simulation', views.monte_carlo_simulation, name='monte_carlo_simulation'),

    # Currency Conversion APIs
    path('currency/convert', views.convert_currency, name='convert_currency'),
    path('currency/supported', views.get_supported_currencies, name='supported_currencies'),
    path('currency/rate/<str:from_currency>/<str:to_currency>', views.get_exchange_rate, name='exchange_rate'),

    # Portfolio Exposure APIs
    path('portfolio/exposure', views.get_portfolio_exposure, name='portfolio_exposure'),
    path('portfolio/trends', views.get_portfolio_trends, name='portfolio_trends'),
    path('portfolio/export-pdf', views.export_portfolio_pdf, name='export_portfolio_pdf'),

    # PDF Export APIs
    path('contracts/<uuid:contract_id>/what-if/export-pdf', views.export_what_if_pdf, name='export_what_if_pdf'),

    # =======================
    # Embedding Model Selector (any authenticated user)
    # =======================
    path('embedding-model/', embedding_model_views.embedding_model_view, name='embedding_model'),

    # =======================
    # Playbook Automation
    # =======================
    # Per-contract: run & retrieve results
    path('playbook/contracts/<uuid:contract_id>/run', playbook_views.run_playbook_check, name='playbook_run'),
    path('playbook/contracts/<uuid:contract_id>/results', playbook_views.get_playbook_results, name='playbook_results'),

    # Accept a single fallback suggestion
    path('playbook/results/<str:result_id>/accept', playbook_views.accept_playbook_fallback, name='playbook_accept'),

    # Drift analytics
    path('playbook/drift', playbook_views.get_playbook_drift, name='playbook_drift'),
    path('playbook/drift/capture', playbook_views.capture_drift, name='playbook_drift_capture'),

    # Coverage dashboard
    path('playbook/coverage', playbook_views.get_playbook_coverage, name='playbook_coverage'),

    # Update suggestions (data-driven playbook evolution)
    path('playbook/update-suggestions', playbook_views.get_update_suggestions, name='playbook_update_suggestions'),
    path('playbook/update-suggestions/<str:suggestion_id>/approve', playbook_views.approve_update_suggestion, name='playbook_approve_suggestion'),
    path('playbook/update-suggestions/<str:suggestion_id>/reject', playbook_views.reject_update_suggestion, name='playbook_reject_suggestion'),

    # Heatmap overlay (clause-type × drift)
    path('playbook/heatmap', playbook_views.get_playbook_heatmap, name='playbook_heatmap'),

    # Admin – manage LegalPlaybook library
    path('playbook/admin/playbooks', playbook_views.manage_playbooks, name='playbook_admin'),

    # =======================
    # Legal Playbook & Action Engine
    # =======================
    path('legal-playbook/clauses', playbook_views.get_clauses_for_action, name='legal_playbook_clauses'),
    path('legal-playbook/clause/<str:clause_id>', playbook_views.get_legal_playbook_analysis, name='legal_playbook_analysis'),
    path('legal-playbook/clause/<str:clause_id>/counter-proposal', playbook_views.generate_counter_proposal_action, name='legal_playbook_counter_proposal'),
    path('legal-playbook/clause/<str:clause_id>/export-redlines', playbook_views.export_redlines_action, name='legal_playbook_export_redlines'),
    path('legal-playbook/clause/<str:clause_id>/approve', playbook_views.trigger_approval_workflow, name='legal_playbook_approve'),

    # =======================
    # Clause Rewrite & Counter-Proposal (Decision Intelligence)
    # =======================
    path('clause-rewrite/', views.clause_rewrite, name='clause_rewrite'),
    path('counter-proposal/', views.counter_proposal, name='counter_proposal'),
    path('contracts/<uuid:contract_id>/advanced-what-if/', views.advanced_what_if, name='advanced_what_if'),

    # =======================
    # Risk Intelligence (Graph-Based Monte Carlo & RAG)
    # =======================
    path('risk-intelligence/monte-carlo', risk_intelligence_views.MonteCarloExposureView.as_view(), name='risk_intelligence_monte_carlo'),
    path('risk-intelligence/var', risk_intelligence_views.ValueAtRiskView.as_view(), name='risk_intelligence_var'),
    path('risk-intelligence/stress-test', risk_intelligence_views.StressTestView.as_view(), name='risk_intelligence_stress_test'),
    path('risk-intelligence/risk-subgraph/<uuid:contract_id>/', risk_intelligence_views.RiskSubgraphView.as_view(), name='risk_intelligence_subgraph'),
    path('risk-intelligence/similar-clauses', risk_intelligence_views.SimilarClausesView.as_view(), name='risk_intelligence_similar_clauses'),
    path('risk-intelligence/propagate', risk_intelligence_views.RiskPropagationView.as_view(), name='risk_intelligence_propagate'),
    path('risk-intelligence/setup-graph', risk_intelligence_views.SetupGraphSchemaView.as_view(), name='risk_intelligence_setup'),

    # Multi-hop Graph Traversal Endpoints (NEW)
    path('risk-intelligence/cascading-risks/<str:risk_id>/', risk_intelligence_views.CascadingRisksView.as_view(), name='risk_intelligence_cascading_risks'),
    path('risk-intelligence/blast-radius/<uuid:contract_id>/', risk_intelligence_views.RiskBlastRadiusView.as_view(), name='risk_intelligence_blast_radius'),
    path('risk-intelligence/risk-subgraph-multihop/<uuid:contract_id>/', risk_intelligence_views.MultiHopRiskGraphView.as_view(), name='risk_intelligence_multihop'),

    # =======================
    # Clause Drift Intelligence
    # =======================
    path('clauses/<str:clause_id>/drift', clause_drift_views.ClauseDriftView.as_view(), name='clause_drift'),
    path('contracts/<uuid:contract_id>/clause-drift-summary', clause_drift_views.ContractClauseDriftSummaryView.as_view(), name='contract_drift_summary'),
    path('clauses/<str:clause_id>/drift-history', clause_drift_views.ClauseDriftHistoryView.as_view(), name='clause_drift_history'),

    # =======================
    # Intent Mapping & Heatmap
    # =======================
    path('contracts/<uuid:contract_id>/intent-heatmap', intent_heatmap_views.ContractIntentHeatmapView.as_view(), name='contract_intent_heatmap'),
    path('clauses/<str:clause_id>/intent-analysis', intent_heatmap_views.ClauseIntentAnalysisView.as_view(), name='clause_intent_analysis'),
    path('contracts/<uuid:contract_id>/intent-drift', intent_heatmap_views.IntentDriftComparisonView.as_view(), name='intent_drift_comparison'),

    # =======================
    # Clause Trust Score (CTS) - Feature #9
    # =======================
    path('clauses/<str:clause_id>/trust/', trust_views.ClauseTrustScoreView.as_view(), name='clause_trust_score'),
    path('clauses/<str:clause_id>/trust/update/', trust_views.ClauseTrustUpdateView.as_view(), name='clause_trust_update'),
    path('clauses/trust/bulk/', trust_views.BulkTrustScoreView.as_view(), name='bulk_trust_score'),
    path('trust/statistics/', trust_views.TrustStatisticsView.as_view(), name='trust_statistics'),
    path('trust/badges/', trust_views.TrustBadgesView.as_view(), name='trust_badges'),
    path('trust/compare/', trust_views.ClauseTrustCompareView.as_view(), name='trust_compare'),
    path('contracts/<uuid:contract_id>/trust/dashboard/', trust_views.ContractTrustDashboardView.as_view(), name='contract_trust_dashboard'),

    # =======================
    # Neo4j Trust Propagation - Feature #10
    # =======================
    path('clauses/<str:clause_id>/trust/impact/', trust_propagation_views.TrustImpactRadiusView.as_view(), name='trust_impact_radius'),
    path('trust/silent-killers/', trust_propagation_views.SilentKillerDetectionView.as_view(), name='silent_killers'),
    path('trust/jurisdictional-drift/', trust_propagation_views.JurisdictionalTrustDriftView.as_view(), name='jurisdictional_trust_drift'),
    path('trust/counterparty-collapse/', trust_propagation_views.CounterpartyTrustCollapseView.as_view(), name='counterparty_trust_collapse'),
    path('clauses/<str:clause_id>/trust/simulate-failure/', trust_propagation_views.TrustContagionSimulationView.as_view(), name='trust_contagion'),
    path('clauses/<str:clause_id>/trust/repair-recommendations/', trust_propagation_views.TrustRepairRecommendationView.as_view(), name='trust_repair'),
    path('clauses/<str:clause_id>/trust/sync-to-graph/', trust_propagation_views.SyncClauseTrustToGraphView.as_view(), name='sync_trust_to_graph'),

    # =======================
    # Negotiation Heat Engine - Feature #11
    # =======================
    path('clauses/<str:clause_id>/heat/', heat_views.ClauseHeatAnalysisView.as_view(), name='clause_heat'),
    path('contracts/<uuid:contract_id>/heat-map/', heat_views.ContractHeatMapView.as_view(), name='contract_heat_map'),
    path('heat/compare/', heat_views.HeatComparisonView.as_view(), name='heat_compare'),
    path('clauses/<str:clause_id>/heat/cooling-strategies/', heat_views.CoolingStrategyView.as_view(), name='cooling_strategies'),
    path('heat/portfolio-stats/', heat_views.PortfolioHeatStatsView.as_view(), name='portfolio_heat_stats'),

    # =======================
    # Temporal Clause Evolution - Feature #12
    # =======================
    path('clauses/<str:clause_id>/temporal/', temporal_views.ClauseTemporalAnalysisView.as_view(), name='clause_temporal'),
    path('clauses/<str:clause_id>/temporal/trend/', temporal_views.TemporalTrendView.as_view(), name='temporal_trend'),
    path('temporal/aging-clauses/', temporal_views.AgingClausesView.as_view(), name='aging_clauses'),
    path('temporal/regulatory-drift/', temporal_views.RegulatoryDriftView.as_view(), name='regulatory_drift'),

    # =======================
    # CUAD Graph Intelligence (Contract Differential Engine)
    # =======================
    # Original 5 endpoints
    path('cuad-graph/ingest/<uuid:contract_id>/', cuad_graph_views.IngestContractGraphView.as_view(), name='cuad_graph_ingest'),
    path('cuad-graph/compare/', cuad_graph_views.CompareContractGraphView.as_view(), name='cuad_graph_compare'),
    path('cuad-graph/compare-multi/', cuad_graph_views.MultiContractCompareView.as_view(), name='cuad_graph_compare_multi'),
    path('cuad-graph/pagerank/<str:contract_id>/', cuad_graph_views.GDSPageRankView.as_view(), name='cuad_graph_pagerank'),
    path('cuad-graph/similarity/', cuad_graph_views.GDSSimilarityView.as_view(), name='cuad_graph_similarity'),
    path('cuad-graph/gnn-score/', cuad_graph_views.GNNScoringView.as_view(), name='cuad_graph_gnn_score'),
    # GraphRAG + Qwen 2.5
    path('cuad-graph/rag-analyze/', cuad_graph_views.RAGAnalyzeView.as_view(), name='cuad_rag_analyze'),
    path('cuad-graph/rag-compare/', cuad_graph_views.RAGCompareView.as_view(), name='cuad_rag_compare'),
    path('cuad-graph/rag-negotiate/', cuad_graph_views.RAGNegotiateView.as_view(), name='cuad_rag_negotiate'),
    # GNN Training
    path('cuad-graph/gnn-train/', cuad_graph_views.GNNTrainView.as_view(), name='cuad_gnn_train'),
    # SIMILAR edge persistence
    path('cuad-graph/build-similar/', cuad_graph_views.BuildSimilarEdgesView.as_view(), name='cuad_build_similar'),
    # Bulk CUAD JSON ingestion
    path('cuad-graph/ingest-cuad-json/', cuad_graph_views.IngestCUADJsonView.as_view(), name='cuad_ingest_json'),
    # Native GDS algorithms
    path('cuad-graph/gds-pagerank/<str:contract_id>/', cuad_graph_views.GDSNativePageRankView.as_view(), name='cuad_gds_pagerank'),
    path('cuad-graph/gds-similarity/', cuad_graph_views.GDSNativeSimilarityView.as_view(), name='cuad_gds_similarity'),
    # Temporal amendment tracking
    path('cuad-graph/amendment/', cuad_graph_views.TrackAmendmentView.as_view(), name='cuad_track_amendment'),
    path('cuad-graph/amendments/<str:contract_id>/', cuad_graph_views.AmendmentHistoryView.as_view(), name='cuad_amendment_history'),

    # ==============================
    # Concept Correlation Graph Engine
    # ==============================
    path('concept-graph/all/', concept_graph_views.ConceptGraphAllView.as_view(), name='concept_graph_all'),
    path('concept-graph/matrix/', concept_graph_views.ConceptCorrelationMatrixView.as_view(), name='concept_graph_matrix'),
    path('concept-graph/summary/', concept_graph_views.ConceptSummaryView.as_view(), name='concept_graph_summary'),

    # NEW: Real Contract Data Extraction
    path('concept-graph/contract/<str:contract_id>/', concept_graph_views.ContractConceptGraphView.as_view(), name='concept_graph_contract'),
    path('concept-graph/compare/', concept_graph_views.ContractConceptComparisonView.as_view(), name='concept_graph_compare'),

    # NEW: Advanced Analytics
    path('concept-graph/analytics/centrality/', concept_graph_views.ConceptCentralityView.as_view(), name='concept_graph_centrality'),
    path('concept-graph/analytics/communities/', concept_graph_views.ConceptCommunitiesView.as_view(), name='concept_graph_communities'),
    path('concept-graph/analytics/evolution/<str:contract_id>/', concept_graph_views.ConceptEvolutionView.as_view(), name='concept_graph_evolution'),

    # This must be LAST (catch-all for archetype names)
    path('concept-graph/<str:contract_type>/', concept_graph_views.ConceptGraphByTypeView.as_view(), name='concept_graph_by_type'),

    # =======================
    # Arbitration Risk Intelligence Engine (EPC / $100M+)
    # =======================
    path('arbitration/analyze', arbitration_views.ArbitrationFullAnalysisView.as_view(), name='arbitration_full_analysis'),
    path('arbitration/monte-carlo', arbitration_views.ArbitrationMonteCarloView.as_view(), name='arbitration_monte_carlo'),
    path('arbitration/scenarios', arbitration_views.ArbitrationScenariosView.as_view(), name='arbitration_scenarios'),
    path('arbitration/tribunal', arbitration_views.ArbitrationTribunalView.as_view(), name='arbitration_tribunal'),
    path('arbitration/exposure', arbitration_views.ArbitrationExposureView.as_view(), name='arbitration_exposure'),
    path('arbitration/optimize', arbitration_views.ArbitrationOptimizerView.as_view(), name='arbitration_optimize'),
    path('arbitration/strategies', arbitration_views.ArbitrationStrategiesView.as_view(), name='arbitration_strategies'),
    path('arbitration/knowledge-graph/<uuid:contract_id>/', arbitration_views.ArbitrationKnowledgeGraphView.as_view(), name='arbitration_knowledge_graph'),
    path('arbitration/canonical-graph/', arbitration_views.ArbitrationCanonicalGraphView.as_view(), name='arbitration_canonical_graph'),
    path('arbitration/extract-clauses', arbitration_views.ArbitrationClauseExtractView.as_view(), name='arbitration_extract_clauses'),
    path('arbitration/extract-text', arbitration_views.ArbitrationExtractTextView.as_view(), name='arbitration_extract_text'),

    # Enhanced arbitration features (Neo4j, LegalBERT, GNN, AI Rewrites)
    path('arbitration/analysis/<uuid:analysis_id>/', arbitration_views.GetArbitrationAnalysisView.as_view(), name='get_arbitration_analysis'),
    path('arbitration/rewrites/<uuid:analysis_id>/', arbitration_views.GetClauseRewritesView.as_view(), name='get_clause_rewrites'),
    path('arbitration/gnn-prediction/<uuid:analysis_id>/', arbitration_views.GetGNNPredictionView.as_view(), name='get_gnn_prediction'),
    path('arbitration/similar-clauses/', arbitration_views.FindSimilarClausesView.as_view(), name='find_similar_clauses'),
    path('arbitration/neo4j-graph/<uuid:contract_id>/', arbitration_views.GetNeo4jGraphView.as_view(), name='get_neo4j_graph'),
    path('arbitration/rewrite-clause/', arbitration_views.RewriteClauseView.as_view(), name='rewrite_clause'),

    # =======================
    # Legal Reviewer - AI-powered legal review with case law + Bayesian risk
    # =======================
    path('legal-review/contracts/<str:contract_id>/analyze', legal_review_views.LegalReviewAnalyzeView.as_view(), name='legal_review_analyze'),
    path('legal-review/explain', legal_review_views.LegalReviewExplainView.as_view(), name='legal_review_explain'),
    path('legal-review/stats', legal_review_views.LegalReviewStatsView.as_view(), name='legal_review_stats'),
    path('legal-review/case-law', legal_review_views.LegalReviewCaseLawView.as_view(), name='legal_review_case_law'),
    path('legal-review/rag', legal_review_views.LegalReviewRAGView.as_view(), name='legal_review_rag'),
    path('legal-review/graphrag', legal_review_views.LegalReviewGraphRAGView.as_view(), name='legal_review_graphrag'),
    path('legal-review/copilot', legal_review_views.LegalCopilotView.as_view(), name='legal_review_copilot'),
    path('legal-review/live-events', legal_review_views.LegalLiveEventsView.as_view(), name='legal_review_live_events'),
    path('legal-review/events/process', legal_review_views.LegalEventProcessView.as_view(), name='legal_review_event_process'),
    path('legal-review/precedents/similar', legal_review_views.LegalPrecedentSimilarityView.as_view(), name='legal_review_precedents'),
    path('legal-review/cpt/update', legal_review_views.LegalCPTUpdateView.as_view(), name='legal_review_cpt_update'),
    path('legal-review/neo4j/graph/<str:contract_id>', legal_review_views.LegalReviewNeo4jGraphView.as_view(), name='legal_review_neo4j_graph'),
    path('legal-review/crawler/trigger', legal_review_views.LegalCrawlerTriggerView.as_view(), name='legal_review_crawler_trigger'),
    path('legal-review/sse-events', legal_review_views.LegalReviewSSEView.as_view(), name='legal_review_sse'),
    path('legal-review/simulate-event', legal_review_views.LegalReviewAutoSimulateView.as_view(), name='legal_review_simulate_event'),
    path('legal-review/portfolio-heatmap', legal_review_views.LegalPortfolioHeatmapView.as_view(), name='legal_review_portfolio_heatmap'),
    path('legal-review/auto-redline', legal_review_views.LegalAutoRedlineView.as_view(), name='legal_review_auto_redline'),

    # =======================
    # AI Studio – Contract-specific AI features (Features 1, 2, 4, 5)
    # =======================
    path('ai-studio/redline/', ai_studio_views.RedlineGenerateView.as_view(), name='ai_studio_redline_generate'),
    path('ai-studio/redline/accept/', ai_studio_views.RedlineAcceptView.as_view(), name='ai_studio_redline_accept'),
    path('ai-studio/negotiate/', ai_studio_views.NegotiationAgentsView.as_view(), name='ai_studio_negotiate'),
    path('ai-studio/cfo-simulate/', ai_studio_views.CFOSimulateView.as_view(), name='ai_studio_cfo_simulate'),
    path('ai-studio/simulate-contract/', ai_studio_views.CFOSimulateContractView.as_view(), name='ai_studio_simulate_contract'),
    path('ai-studio/risk-insights/', ai_studio_views.CFORiskInsightsView.as_view(), name='ai_studio_risk_insights'),
    path('ai-studio/scenario-analysis/', ai_studio_views.CFOScenarioAnalysisView.as_view(), name='ai_studio_scenario_analysis'),
    path('ai-studio/legal-analyze/', ai_studio_views.LegalAnalyzeView.as_view(), name='ai_studio_legal_analyze'),
    # ── Contract Intelligence Orchestrator ──────────────────────────────────
    # Primary contract-first endpoint (supports file upload + DB persistence)
    path('analyze-contract/', orchestrator_views.AnalyzeContractView.as_view(), name='analyze_contract'),
    path('analyze-contract/<str:analysis_id>/', orchestrator_views.AnalysisStoredResultView.as_view(), name='analyze_contract_result'),
    path('analyze-contract/contract/<str:contract_id>/latest/', orchestrator_views.ContractLatestAnalysisView.as_view(), name='analyze_contract_latest'),
    path('analyze-contract/contract/<str:contract_id>/all/', orchestrator_views.ContractAllAnalysesView.as_view(), name='analyze_contract_all'),
    # Legacy (kept for backwards compatibility)
    path('ai-studio/full-analysis/', orchestrator_views.FullAnalysisView.as_view(), name='ai_studio_full_analysis'),
    path('ai-studio/analysis-result/<str:analysis_id>/', orchestrator_views.AnalysisResultView.as_view(), name='ai_studio_analysis_result'),
    # Advanced negotiation engine (Feature 2b)
    path('ai-studio/negotiate-advanced/', ai_studio_views.AdvancedNegotiationView.as_view(), name='ai_studio_negotiate_advanced'),
    path('ai-studio/negotiation-history/', ai_studio_views.NegotiationHistoryView.as_view(), name='ai_studio_negotiation_history'),
    path('ai-studio/evaluate-outcome/', ai_studio_views.EvaluateOutcomeView.as_view(), name='ai_studio_evaluate_outcome'),

    # =======================
    # Contract AI Suite – Platform-wide AI features (Features 3, 6, 7)
    # =======================
    path('contract-suite/memory/build/', contract_suite_views.StrategyMemoryBuildView.as_view(), name='contract_suite_memory_build'),
    path('contract-suite/memory/insights/', contract_suite_views.StrategyMemoryInsightsView.as_view(), name='contract_suite_memory_insights'),
    path('contract-suite/memory/search/', contract_suite_views.StrategyMemorySearchView.as_view(), name='contract_suite_memory_search'),
    path('contract-suite/memory/temporal/', contract_suite_views.TemporalEvolutionView.as_view(), name='contract_suite_temporal'),
    path('contract-suite/monitor/events/', contract_suite_views.MonitorEventsView.as_view(), name='contract_suite_monitor_events'),
    path('contract-suite/monitor/alerts/', contract_suite_views.MonitorAlertsView.as_view(), name='contract_suite_monitor_alerts'),
    path('contract-suite/monitor/scan/', contract_suite_views.MonitorScanView.as_view(), name='contract_suite_monitor_scan'),
    path('contract-suite/rl/record/', contract_suite_views.RLRecordView.as_view(), name='contract_suite_rl_record'),
    path('contract-suite/rl/experiences/', contract_suite_views.RLExperiencesView.as_view(), name='contract_suite_rl_experiences'),
    path('contract-suite/rl/insights/', contract_suite_views.RLInsightsView.as_view(), name='contract_suite_rl_insights'),
    path('contract-suite/rl/feedback/', contract_suite_views.RLHFFeedbackView.as_view(), name='contract_suite_rl_feedback'),
    path('contract-suite/rl/train/', contract_suite_views.RLTrainView.as_view(), name='contract_suite_rl_train'),
    path('contract-suite/rl/recommend/', contract_suite_views.RLRecommendView.as_view(), name='contract_suite_rl_recommend'),
    path('contract-suite/benchmarking/', contract_suite_views.BenchmarkingView.as_view(), name='contract_suite_benchmarking'),
    path('contract-suite/benchmarking/contracts/', contract_suite_views.BenchmarkingContractListView.as_view(), name='contract_suite_benchmarking_contracts'),
    path('contract-suite/benchmarking/insights/', contract_suite_views.BenchmarkingInsightsView.as_view(), name='contract_suite_benchmarking_insights'),
    path('contract-suite/benchmarking/clauses/', contract_suite_views.BenchmarkingClausesView.as_view(), name='contract_suite_benchmarking_clauses'),
    path('contract-suite/benchmarking/recommendations/', contract_suite_views.BenchmarkingRecommendationsView.as_view(), name='contract_suite_benchmarking_recommendations'),
    path('contract-suite/dashboards/risk-margin/', contract_suite_views.RiskMarginFrontierView.as_view(), name='contract_suite_risk_margin'),
    path('contract-suite/dashboards/supplier-heatmap/', contract_suite_views.SupplierHeatmapView.as_view(), name='contract_suite_supplier_heatmap'),
    path('contract-suite/dashboards/dispute-timeline/', contract_suite_views.DisputeTimelineView.as_view(), name='contract_suite_dispute_timeline'),
    path('contract-suite/monitor/auto-action/', contract_suite_views.AutoActionView.as_view(), name='contract_suite_auto_action'),
    path('contract-suite/monitor/auto-actions/', contract_suite_views.AutoActionLogView.as_view(), name='contract_suite_auto_action_log'),
    path('contract-suite/monitor/auto-action/bulk/', contract_suite_views.BulkAutoActionView.as_view(), name='contract_suite_auto_action_bulk'),

    # =======================
    # Multi-Modal AI (Feature 8)
    # =======================
    path('multimodal/voice/', multimodal_views.VoiceContractView.as_view(), name='multimodal_voice'),
    path('multimodal/document/', multimodal_views.DocumentScanView.as_view(), name='multimodal_document'),
    path('multimodal/email/', multimodal_views.EmailParserView.as_view(), name='multimodal_email'),

    # =======================
    # ERP Auto-Execution (Feature 9)
    # =======================
    path('erp/auto-trigger/', erp_execution_views.ERPAutoTriggerView.as_view(), name='erp_auto_trigger'),
    path('erp/execution-log/', erp_execution_views.ERPExecutionLogView.as_view(), name='erp_execution_log'),
    path('erp/bulk-execute/', erp_execution_views.ERPBulkExecuteView.as_view(), name='erp_bulk_execute'),
    path('erp/contracts/', erp_execution_views.ERPContractsListView.as_view(), name='erp_contracts_list'),

]
