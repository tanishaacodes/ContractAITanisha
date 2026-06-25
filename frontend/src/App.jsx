import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import ProtectedRoute from './components/ProtectedRoute';
import { ToastProvider } from './components/ToastNotification';
import DashboardLayout from './components/DashboardLayout';
import useAuthStore from './store/authStore';
import useThemeStore from './store/themeStore';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Contracts from './pages/Contracts';
import AssignedContracts from './pages/AssignedContracts';
import UploadContract from './pages/UploadContract';
import ClauseExtraction from './pages/ClauseExtraction';
import RiskAnalysis from './pages/RiskAnalysis';
import RiskExplanation from './pages/RiskExplanation';
import ExecutiveSummary from './pages/ExecutiveSummary';
import ObligationTracker from './pages/ObligationTracker';
import FastProcessing from './pages/FastProcessing';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import UserProfile from './pages/UserProfile';
import Pricing from './pages/Pricing';
import MyPlan from './pages/MyPlan';
import AdminDashboard from './pages/AdminDashboard';
import GenerateContract from './GenerateContract';  // Keep old version for compatibility
import ContractGenerator from './pages/ContractGenerator';  // New RAG-based generator
import ContractDetails from './pages/ContractDetails';
import ContractCompare from './pages/ContractCompare';
import ContractSearch from './pages/ContractSearch';
import IntentAnalysis from './pages/IntentAnalysis';
import PortfolioAnalytics from './pages/PortfolioAnalytics';
import ComplianceDashboard from './pages/ComplianceDashboard';

// ✅ Contract Classification
import ContractClassify from './pages/ContractClassify';

// ✅ NEW: BERTopic Clustering Visualization
import ContractClusters from './pages/ContractClusters';

// ✅ NEW: Unified RAG Chat
import UnifiedChat from './pages/UnifiedChat';

// ✅ NEW: Chat Analytics
import ChatAnalytics from './pages/ChatAnalytics';

// ✅ NEW: Risky Clause Redlining
import ContractRedlining from './pages/ContractRedlining';

// ✅ NEW: Enhanced Contract Redline Editor
import ContractRedlineEditor from './pages/ContractRedlineEditor';

// ✅ NEW: Role-Based Approvals
import ApprovalInbox from './pages/ApprovalInbox';

// ✅ NEW: AI Clause Library
import ClauseLibrary from './pages/ClauseLibrary';
import ClauseLibrarySelector from './pages/ClauseLibrarySelector';
import AdvancedClauseLibrary from './pages/AdvancedClauseLibrary';
import ClauseHeatmap from './pages/ClauseHeatmap';
import ClauseEditPage from './pages/ClauseEditPage';
import ContractDocumentEditor from './pages/ContractDocumentEditor';

// ✅ NEW: RRIE (Risk & Responsibility Intelligence Engine)
import RRIE from './pages/RRIE';

// ✅ NEW: Alfresco RAG Integration
import AlfrescoSync from './pages/AlfrescoSync';
import RAGSearchPage from './pages/RAGSearchPage';

// ✅ NEW: Agentic AI (2026)
import AgenticAI from './pages/AgenticAI';
import AgenticAIDetails from './pages/AgenticAIDetails';

// ✅ NEW: Payment & Subscription
import SubscriptionPage from './pages/subscription/SubscriptionPage';
import PaymentHistory from './components/payments/PaymentHistory';

// ✅ NEW: Advanced AI Features (2026)
import CounterfactualEngine from './pages/CounterfactualEngine';
import DriftDetection from './pages/DriftDetection';
import RiskExposure from './pages/RiskExposure';

// ✅ NEW: Obligation & Clause AI Features (2026)
import ObligationsPage from './pages/ObligationsPage';
import AddClausePage from './pages/AddClausePage';
import AIRewritePage from './pages/AIRewritePage';
import CounterProposalPage from './pages/CounterProposalPage';
import RiskNetwork from './pages/RiskNetwork';
import RiskExplainability from './pages/RiskExplainability';
import ScenarioSimulation from './pages/ScenarioSimulation';

// ✅ NEW: Embedding-Based AI (Deterministic, Zero Hallucinations)
import EmbeddingRiskAnalysis from './pages/EmbeddingRiskAnalysis';
import EmbeddingRedline from './pages/EmbeddingRedline';
import EmbeddingChat from './pages/EmbeddingChat';

// ✅ NEW: MiniLM-Based Deviation & Safeguard Detection (2026)
import RiskHeatmapPage from './pages/RiskHeatmapPage';

// ✅ NEW: Playbook Automation
import PlaybookAutomation from './pages/PlaybookAutomation';

// ✅ NEW: UniContractAI Executive Dashboard (2026)
import ExecutiveDashboard from './prime/pages/ExecutiveDashboard';

// ✅ NEW: Contract Intelligence Maps (Gartner-style Analytics)
import ContractMapsAnalytics from './pages/ContractMapsAnalytics';

// ✅ NEW: Negotiation Intelligence (2026)
import NegotiationIntelligence from './pages/NegotiationIntelligence';

// ✅ NEW: Portfolio-Level Counterparty Risk Heatmap
import CounterpartyPortfolioHeatmap from './pages/CounterpartyPortfolioHeatmap';
import CounterpartyPortfolioTest from './pages/CounterpartyPortfolioTest';

// ✅ NEW: Graph Intelligence Dashboard (Phase 1)
import ContractGraphDashboard from './pages/ContractGraphDashboard';

// ✅ NEW: What-If Analysis (Graph-Based Simulation)
import WhatIfAnalysis from './pages/WhatIfAnalysis';

// ✅ NEW: Advanced Decision Intelligence (Rewrite + Counter-Proposal + Advanced What-If)
import AdvancedWhatIfDashboard from './pages/AdvancedWhatIfDashboard';

// ✅ NEW: Executive Snapshot (CXO / Board Mode)
import ExecutiveSnapshot from './pages/ExecutiveSnapshot';
import RiskValueMatrixPage from './pages/RiskValueMatrixPage';
import PortfolioIntelligence from './pages/PortfolioIntelligence';
import CounterfactualSimulation from './pages/CounterfactualSimulation';
import LossSentinel from './pages/LossSentinel';
import LegalPlaybook from './pages/LegalPlaybook';

// ✅ NEW: Clause Intelligence & Drift Radar
import ClauseIntelligence from './pages/ClauseIntelligence';

// ✅ NEW: Intent Mapping & Heatmap
import IntentHeatmap from './pages/IntentHeatmap';

// ✅ NEW: Low-Confidence Contracts
import LowConfidenceContracts from './pages/LowConfidenceContracts';

// ✅ NEW: Self-Healing Clause Library
import ClauseHealthDashboard from './pages/ClauseHealthDashboard';

// ✅ NEW: Neo4j Graph Status
import GraphStatus from './pages/GraphStatus';

// ✅ NEW: Live Clause Co-Pilot (Negotiation Mode)
import NegotiationMode from './pages/NegotiationMode';

// ✅ NEW: Clause Trust Score (CTS) - Feature #9
import ClauseTrustDashboard from './pages/ClauseTrustDashboard';
import ContractTrustDashboard from './pages/ContractTrustDashboard';

// ✅ NEW: Tender Intelligence Engine (2026)
import TenderUpload from './components/tender/TenderUpload';
import TenderDashboard from './components/tender/TenderDashboard';
import TenderList from './pages/TenderList';
import CompanyProfilePage from './pages/CompanyProfile';
import TrustStatistics from './pages/TrustStatistics';
import BidManagementDashboard from './pages/BidManagementDashboard';
import BuyerBidDashboard from './pages/BuyerBidDashboard';
import TenderPortfolio from './pages/TenderPortfolio';
import PortfolioDashboard from './pages/PortfolioDashboard';
import BidActionsDashboard from './pages/BidActionsDashboard';

// ✅ NEW: Neo4j Trust Propagation - Feature #10
import TrustPropagationGraph from './pages/TrustPropagationGraph';

// ✅ NEW: Negotiation Heat Engine - Feature #11
import NegotiationHeatMap from './pages/NegotiationHeatMap';
import ClauseHeatAnalysis from './pages/ClauseHeatAnalysis';

// ✅ NEW: Temporal Clause Evolution - Feature #12
import ClauseTemporalEvolution from './pages/ClauseTemporalEvolution';

// ✅ NEW: Review Time Analytics
import ReviewTimeAnalytics from './pages/ReviewTimeAnalytics';

// ✅ NEW: Risk Intelligence (Graph + Monte Carlo + RAG) - Feature #13
import RiskIntelligenceDashboard from './pages/RiskIntelligenceDashboard';

// ✅ NEW: Contract Graph Explorer (Neo4j-style visualization)
import ContractGraphExplorer from './pages/ContractGraphExplorer';

// ✅ NEW: CUAD Contract Differential Intelligence Engine
import ContractDifferentialEngine from './pages/ContractDifferentialEngine';
import ConceptCorrelationGraph from './pages/ConceptCorrelationGraph';

// ✅ NEW: Contract Digital Twin + Strategic Intelligence Radar
import ContractTwin from './pages/ContractTwin';
import StrategicRadar from './pages/StrategicRadar';

// ✅ NEW: Contract Intelligence (AutoRAG + Neo4j Graph Q&A)
import ContractIntelligence from './pages/ContractIntelligence';

// ✅ NEW: SuperAdmin & Integrations
import UserManagement from './pages/SuperAdmin/UserManagement';
import SystemStats from './pages/SuperAdmin/SystemStats';
import FivetranDashboard from './pages/Integrations/FivetranDashboard';
import KafkaDashboard from './pages/Integrations/KafkaDashboard';
import SAPDashboard from './pages/Integrations/SAPDashboard';
import InforDashboard from './pages/Integrations/InforDashboard';
import IntegrationHub from './pages/Integrations/IntegrationHub';

// ✅ NEW: Enterprise Risk & Profitability Intelligence Platform
import GlobalRiskDashboard from './pages/enterprise/GlobalRiskDashboard';
import ContractKnowledgeGraph from './pages/enterprise/ContractKnowledgeGraph';
import GeoPoliticalRiskMap from './pages/enterprise/GeoPoliticalRiskMap';
import MonteCarloSimulation from './pages/enterprise/MonteCarloSimulation';
import SupplyChainRiskDashboard from './pages/enterprise/SupplyChainRiskDashboard';
import CommodityForecastDashboard from './pages/enterprise/CommodityForecastDashboard';
import MarginSensitivityAnalysis from './pages/enterprise/MarginSensitivityAnalysis';
import PortfolioVaRDashboard from './pages/enterprise/PortfolioVaRDashboard';
import InsurancePolicyDashboard from './pages/enterprise/InsurancePolicyDashboard';

// ✅ NEW: Arbitration Risk Intelligence Engine
import ArbitrationDashboard from './pages/ArbitrationDashboard';

// ✅ NEW: Dispute Predictor & Simulator
import DisputePredictor from './pages/DisputePredictor';

// ✅ NEW: Force Majeure Intelligence Engine
import ForceMajeureDashboard from './pages/ForceMajeureDashboard';

// ✅ NEW: Legal Reviewer – AI case law + Bayesian risk review
import LegalReview from './pages/LegalReview';
import LegalReviewSelector from './pages/LegalReviewSelector';

// ✅ NEW: Clause Library Advanced Features
import ClauseDriftDashboard from './pages/ClauseDriftDashboard';
import CFODashboard from './pages/CFODashboard';
import PredictiveRiskEngine from './pages/PredictiveRiskEngine';
import AutoRedlining from './pages/AutoRedlining';

// ✅ NEW: Smart Contract Search Intelligence
import SmartContractSearch from './pages/SmartContractSearch';

// ✅ NEW: AI Studio & Contract AI Suite
import AIStudio from './pages/AIStudio';
import ContractAISuite from './pages/ContractAISuite';


// ✅ NEW: Contract Intelligence Orchestrator
import OrchestratorDashboard from './pages/OrchestratorDashboard';


// ✅ NEW: Multi-Modal AI (Feature 8)
import MultiModalAI from './pages/MultiModalAI';

function App() {
  const { isAuthenticated, isInitialized, initializeAuth } = useAuthStore();
  const { initializeTheme } = useThemeStore();

  useEffect(() => {
    initializeAuth();
    initializeTheme();
  }, [initializeAuth, initializeTheme]);

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-white via-slate-50 to-slate-100">
        <div className="text-center">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-lg mx-auto mb-4 animate-pulse">
            <span className="text-white font-bold text-xl">CA</span>
          </div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <ToastProvider>
      <Routes>

        {/* ================= PUBLIC ROUTES ================= */}
        <Route path="/" element={<Home />} />
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
        />
        <Route
          path="/register"
          element={<Register />}
        />

        {/* ================= DASHBOARD ================= */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Dashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= PRIME CONTRACT AI EXECUTIVE DASHBOARD ================= */}
        <Route
          path="/prime-dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ExecutiveDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= CONTRACTS ================= */}
        {/* ⚠️ IMPORTANT: Specific routes must come BEFORE parameterized routes! */}

        {/* Contracts List - MUST be before /contracts/:contractId */}
        <Route
          path="/contracts"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Contracts />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contracts/list"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Contracts />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/assigned-contracts"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AssignedContracts />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Single Contract Details - MUST come AFTER specific routes like /list */}
        <Route
          path="/contracts/:contractId"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractDetails />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ Graph Intelligence Dashboard */}
        <Route
          path="/contracts/:contractId/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractDetails />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ Graph Intelligence Dashboard - Alternate route */}
        <Route
          path="/contracts/:contractId/graph-dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractGraphDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ What-If Analysis */}
        <Route
          path="/contracts/:contractId/what-if"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <WhatIfAnalysis />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ Advanced Decision Intelligence – contract-scoped */}
        <Route
          path="/contracts/:contractId/advanced-what-if"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AdvancedWhatIfDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ Advanced Decision Intelligence – standalone (rewrite / counter-proposal) */}
        <Route
          path="/advanced-what-if"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AdvancedWhatIfDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Risk Intelligence Dashboard - contract-scoped */}
        <Route
          path="/contracts/:contractId/risk-intelligence"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskIntelligenceDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Risk Intelligence Dashboard - standalone */}
        <Route
          path="/risk-intelligence"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskIntelligenceDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Contract Graph Explorer - Neo4j visualization */}
        <Route
          path="/contract-graph"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractGraphExplorer />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: CUAD Contract Differential Intelligence Engine */}
        <Route
          path="/contract-differential"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractDifferentialEngine />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Concept Correlation Graph Engine */}
        <Route
          path="/concept-correlation"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ConceptCorrelationGraph />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Arbitration Risk Intelligence Engine (EPC / $100M+) */}
        <Route
          path="/arbitration-intelligence"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ArbitrationDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Dispute Predictor & Simulator */}
        <Route
          path="/dispute-predictor"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <DisputePredictor />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: AI Studio */}
        <Route
          path="/ai-studio"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AIStudio />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Contract AI Suite */}
        <Route
          path="/contract-ai-suite"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractAISuite />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />


        {/* ✅ NEW: Contract Intelligence Orchestrator */}
        <Route
          path="/orchestrator"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <OrchestratorDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />


        {/* ✅ NEW: Legal Review – contract selector (sidebar entry) */}
        <Route
          path="/legal-review"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <LegalReviewSelector />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Legal Reviewer – AI case law + Bayesian risk */}
        <Route
          path="/contracts/:contractId/legal-review"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <LegalReview />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Clause Drift Detection Dashboard */}
        <Route
          path="/clause-drift"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseDriftDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: CFO Financial Analytics Dashboard */}
        <Route
          path="/cfo-dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CFODashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Predictive Risk Engine */}
        <Route
          path="/predictive-risk"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PredictiveRiskEngine />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Auto Contract Redlining */}
        <Route
          path="/contracts/:contractId/auto-redline"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AutoRedlining />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Force Majeure Intelligence Engine */}
        <Route
          path="/force-majeure"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ForceMajeureDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />


        {/* ✅ NEW: Obligation Extraction */}
        <Route
          path="/contracts/:contractId/obligations"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ObligationsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Add Clause with Risk Assessment */}
        <Route
          path="/contracts/:contractId/add-clause"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AddClausePage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: AI Clause Rewriter */}
        <Route
          path="/contracts/:contractId/ai-rewrite"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AIRewritePage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Counter-Proposal Generator */}
        <Route
          path="/contracts/:contractId/counter-proposal"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CounterProposalPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contracts/:contractId/redlining"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractRedlining />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ Enhanced Redline Editor with track changes */}
        <Route
          path="/contracts/:contractId/redline-editor"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractRedlineEditor />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= EMBEDDING-BASED AI (DETERMINISTIC) ================= */}
        <Route
          path="/contracts/:contractId/embedding-risk"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <EmbeddingRiskAnalysis />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contracts/:contractId/embedding-redline"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <EmbeddingRedline />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contracts/:contractId/embedding-chat"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <EmbeddingChat />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Risk Heatmap & Deviation Analysis (MiniLM) */}
        <Route
          path="/contracts/:contractId/risk-heatmap"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskHeatmapPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Playbook Automation – per-contract */}
        <Route
          path="/contracts/:contractId/playbook"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PlaybookAutomation />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Playbook Automation – portfolio / admin view */}
        <Route
          path="/playbook"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PlaybookAutomation />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= AGENTIC AI (2026) ================= */}
        <Route
          path="/agentic-ai"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AgenticAI />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/agentic-ai/:contractId"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AgenticAIDetails />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= ADVANCED AI FEATURES (2026) ================= */}
        <Route
          path="/counterfactual-engine"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CounterfactualEngine />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/drift-detection"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <DriftDetection />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/risk-exposure"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskExposure />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/risk-network"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskNetwork />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/risk-explain/:contractId"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskExplainability />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/scenario-simulation"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ScenarioSimulation />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Negotiation Intelligence */}
        <Route
          path="/negotiation-intelligence"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <NegotiationIntelligence />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/negotiation-intelligence/:contractId"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <NegotiationIntelligence />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Portfolio-Level Counterparty Risk Heatmap */}
        <Route
          path="/counterparty-portfolio-test"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CounterpartyPortfolioTest />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/counterparty-portfolio"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CounterpartyPortfolioHeatmap />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <UploadContract />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractSearch />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/smart-search"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <SmartContractSearch />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/compare"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractCompare />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= CLASSIFICATION ================= */}
        <Route
          path="/contract-classify"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractClassify />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ BERTopic Cluster Visualization */}
        <Route
          path="/contract-classify/clusters"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractClusters />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= NLP / ANALYSIS ================= */}
        <Route
          path="/contract/:contractId/clauses"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseExtraction />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/clause-library"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseLibrarySelector />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contract/:contractId/clause-library"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseLibrary />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/advanced-clause-library"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AdvancedClauseLibrary />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/rrie"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RRIE />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/clause-heatmap"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseHeatmap />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Self-Healing Clause Library */}
        <Route
          path="/clause-health"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseHealthDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Neo4j Graph Status */}
        <Route
          path="/graph-status"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <GraphStatus />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Live Clause Co-Pilot (Negotiation Mode) */}
        <Route
          path="/negotiation-mode"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <NegotiationMode />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Clause Trust Score (CTS) - Feature #9 */}
        <Route
          path="/clauses/:clauseId/trust"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseTrustDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contracts/:contractId/trust"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractTrustDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/trust/statistics"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TrustStatistics />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Neo4j Trust Propagation - Feature #10 */}
        <Route
          path="/clauses/:clauseId/trust/propagation"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TrustPropagationGraph />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Negotiation Heat Engine - Feature #11 */}
        <Route
          path="/clauses/:clauseId/heat"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseHeatAnalysis />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contracts/:contractId/heat"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <NegotiationHeatMap />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/heat/portfolio"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <NegotiationHeatMap />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Temporal Clause Evolution - Feature #12 */}
        <Route
          path="/clauses/:clauseId/temporal"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseTemporalEvolution />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contracts/:contractId/edit"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ClauseEditPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contract/:contractId/intents"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <IntentAnalysis />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/risk-analysis"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskAnalysis />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/risk-analysis/:contractId"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskAnalysis />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/risk-explanation"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskExplanation />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/executive-summary"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ExecutiveSummary />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/obligation-tracker"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ObligationTracker />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= ANALYTICS ================= */}
        <Route
          path="/portfolio-analytics"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PortfolioAnalytics />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Analytics />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Executive Snapshot (CXO / Board Mode) */}
        <Route
          path="/executive-snapshot"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ExecutiveSnapshot />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Risk vs Value Matrix (Bubble Chart) */}
        <Route
          path="/risk-value-matrix"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RiskValueMatrixPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Portfolio Intelligence - Contract Clustering Galaxy */}
        <Route
          path="/portfolio-intelligence"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PortfolioIntelligence />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/counterfactual-simulation"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CounterfactualSimulation />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/loss-sentinel"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <LossSentinel />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/legal-playbook"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <LegalPlaybook />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Clause Intelligence & Drift Radar */}
        <Route
          path="/clauses/:clauseId/intelligence"
          element={
            <ProtectedRoute>
              <ClauseIntelligence />
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Intent Mapping & Heatmap */}
        <Route
          path="/contracts/:contractId/intent-heatmap"
          element={
            <ProtectedRoute>
              <IntentHeatmap />
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Low-Confidence Contracts */}
        <Route
          path="/low-confidence-contracts"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <LowConfidenceContracts />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Review Time Analytics */}
        <Route
          path="/review-time-analytics"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ReviewTimeAnalytics />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ✅ NEW: Contract Intelligence Maps (Gartner-style) */}
        <Route
          path="/contract-maps"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractMapsAnalytics />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/fast-processing"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <FastProcessing />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= RAG CHAT ================= */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <UnifiedChat />
            </ProtectedRoute>
          }
        />

        {/* ================= CHAT ANALYTICS ================= */}
        <Route
          path="/chat/analytics"
          element={
            <ProtectedRoute>
              <ChatAnalytics />
            </ProtectedRoute>
          }
        />

        {/* ================= COMPLIANCE ================= */}
        <Route
          path="/compliance/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ComplianceDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= APPROVALS ================= */}
        <Route
          path="/approvals/inbox"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ApprovalInbox />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= USER ================= */}
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <UserProfile />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Settings />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/my-plan"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MyPlan />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/pricing"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Pricing />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= PAYMENT & SUBSCRIPTION ================= */}
        <Route
          path="/subscription"
          element={
            <ProtectedRoute>
              <SubscriptionPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/payments/history"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PaymentHistory />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/generate"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractGenerator />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Keep old generator for reference/compatibility */}
        <Route
          path="/generate-simple"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <GenerateContract />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= ADMIN ================= */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="Admin">
              <DashboardLayout>
                <AdminDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= SUPERADMIN ================= */}
        <Route
          path="/superadmin/users"
          element={
            <ProtectedRoute requiredRole="SuperAdmin">
              <DashboardLayout>
                <UserManagement />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/superadmin/stats"
          element={
            <ProtectedRoute requiredRole="SuperAdmin">
              <DashboardLayout>
                <SystemStats />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= INTEGRATIONS ================= */}
        <Route
          path="/integrations/fivetran"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <FivetranDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/integrations/kafka"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <KafkaDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/integrations/sap"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <SAPDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/integrations/infor"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <InforDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/integrations/hub"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <IntegrationHub />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= ENTERPRISE RISK INTELLIGENCE ================= */}
        <Route
          path="/enterprise/risk-dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <GlobalRiskDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/contract-graph"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractKnowledgeGraph />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/geo-risk"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <GeoPoliticalRiskMap />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/monte-carlo"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MonteCarloSimulation />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/supply-chain"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <SupplyChainRiskDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/commodity"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CommodityForecastDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/margin-sensitivity"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MarginSensitivityAnalysis />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/portfolio-var"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PortfolioVaRDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enterprise/insurance"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <InsurancePolicyDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= CONTRACT DIGITAL TWIN ================= */}
        <Route
          path="/contract-twin"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractTwin />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/contract-twin/:id"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractTwin />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= CONTRACT INTELLIGENCE ================= */}
        <Route
          path="/contract-intelligence"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ContractIntelligence />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= STRATEGIC RADAR ================= */}
        <Route
          path="/strategic-radar"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <StrategicRadar />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/strategic-radar/:id"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <StrategicRadar />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= ALFRESCO RAG ================= */}
        <Route
          path="/alfresco-sync"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AlfrescoSync />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/rag-search"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <RAGSearchPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= TENDER INTELLIGENCE ================= */}
        <Route
          path="/tenders"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TenderList />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/upload"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TenderUpload />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/company-profile"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CompanyProfilePage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/:id"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TenderDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/:id/bid-management"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <BidManagementDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/:tenderId/buyer"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <BuyerBidDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/portfolio"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TenderPortfolio />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/portfolio"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PortfolioDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/:tenderId/actions"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <BidActionsDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tenders/:id/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <TenderDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= MULTI-MODAL AI ================= */}
        <Route
          path="/multimodal-ai"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MultiModalAI />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* ================= FALLBACK ================= */}
        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />}
        />

      </Routes>
      </ToastProvider>
    </Router>
  );
}

export default App;
