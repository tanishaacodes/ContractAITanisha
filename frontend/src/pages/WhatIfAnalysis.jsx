import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FlaskConical,
  Loader,
  AlertTriangle,
  RefreshCw,
  Network,
  TrendingDown
} from 'lucide-react';
import api from '../utils/api';
import useThemeStore from '../store/themeStore';

// What-If Components
import {
  WhatIfPanel,
  WhatIfKPIs,
  WhatIfGraphComparison,
  ExposureKPIs,
  NegotiationImpactSummary,
  MonteCarloVisualization,
  CurrencySelector,
  RiskPropagationChart
} from '../components/what-if';

/**
 * What-If Analysis Dashboard
 *
 * Executive-grade simulation interface for:
 * - Clause removal simulation
 * - Risk impact analysis
 * - Financial exposure calculation
 * - Monte Carlo confidence ranges
 */
export default function WhatIfAnalysis() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const { currentTheme } = useThemeStore();
  const theme = currentTheme; // For backwards compatibility

  // State
  const [contract, setContract] = useState(null);
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [error, setError] = useState(null);

  // Simulation state
  const [selectedClauseId, setSelectedClauseId] = useState('');
  const [includeExposure, setIncludeExposure] = useState(true);
  const [includeMonteCarlo, setIncludeMonteCarlo] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);
  const [targetCurrency, setTargetCurrency] = useState('INR');

  // Load contract and clauses
  useEffect(() => {
    // Redirect to contracts list if no contract ID
    if (!contractId) {
      navigate('/contracts/list');
      return;
    }
    loadContractData();
  }, [contractId, navigate]);

  const loadContractData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load contract details
      const contractRes = await api.get(`/contracts/${contractId}`);
      if (contractRes.data.success) {
        setContract(contractRes.data.contract);
      }

      // Load clauses
      const clausesRes = await api.get(`/contracts/${contractId}/clauses`);
      if (clausesRes.data.success) {
        setClauses(clausesRes.data.clauses || []);
      }
    } catch (err) {
      console.error('Load error:', err);

      // If contract not found (404), redirect to contracts list
      if (err.response?.status === 404) {
        setTimeout(() => {
          navigate('/contracts/list');
        }, 2000); // Give user time to see the error
      }

      setError(err.response?.data?.error || 'Failed to load contract data');
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async (clauseId) => {
    if (!clauseId) return;

    setSimulationLoading(true);
    setSimulationResult(null);

    try {
      const response = await api.post(`/contracts/${contractId}/what-if/remove-clause`, {
        clause_id: clauseId,
        include_exposure: includeExposure,
        include_monte_carlo: includeMonteCarlo
      });

      if (response.data.success) {
        setSimulationResult(response.data);
      } else {
        setError(response.data.error || 'Simulation failed');
      }
    } catch (err) {
      console.error('Simulation error:', err);
      setError(err.response?.data?.error || 'Failed to run simulation');
    } finally {
      setSimulationLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${
        theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
      }`}>
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
            Loading contract data...
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !simulationResult) {
    return (
      <div className={`min-h-screen p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="max-w-2xl mx-auto">
          <div className={`rounded-lg shadow-lg p-8 text-center ${
            theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
          }`}>
            <AlertTriangle className="w-16 h-16 text-red-600 mx-auto mb-4" />
            <h2 className={`text-2xl font-bold mb-2 ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Error Loading Data
            </h2>
            <p className={`mb-6 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              {error}
            </p>
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => navigate('/contracts/list')}
                className={`px-6 py-2 rounded-lg ${
                  theme === 'dark'
                    ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Back to Contracts
              </button>
              <button
                onClick={loadContractData}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const selectedClause = clauses.find(c => c.id === selectedClauseId);

  return (
    <div className={`min-h-screen p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <button
          onClick={() => navigate(`/contracts/${contractId}/graph-dashboard`)}
          className={`flex items-center mb-4 transition-colors ${
            theme === 'dark'
              ? 'text-gray-400 hover:text-white'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Graph Dashboard
        </button>

        <div className={`rounded-lg shadow-lg p-6 ${
          theme === 'dark'
            ? 'bg-gradient-to-r from-purple-900 to-blue-900 border border-purple-800'
            : 'bg-gradient-to-r from-purple-600 to-blue-600'
        } text-white`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-white bg-opacity-20 p-3 rounded-lg">
                <FlaskConical className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-bold">What-If Analysis</h1>
                <p className={`mt-1 ${theme === 'dark' ? 'text-purple-200' : 'text-purple-100'}`}>
                  {contract?.filename || 'Contract'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate(`/contracts/${contractId}/graph-dashboard`)}
                className="flex items-center space-x-2 bg-white bg-opacity-20 px-4 py-2 rounded-lg hover:bg-opacity-30 transition-colors"
              >
                <Network className="w-5 h-5" />
                <span>Graph Dashboard</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Simulation Controls */}
          <div className="lg:col-span-1">
            <WhatIfPanel
              clauses={clauses}
              selectedClauseId={selectedClauseId}
              onSelectClause={setSelectedClauseId}
              onRunSimulation={runSimulation}
              loading={simulationLoading}
              includeExposure={includeExposure}
              onToggleExposure={setIncludeExposure}
              includeMonteCarlo={includeMonteCarlo}
              onToggleMonteCarlo={setIncludeMonteCarlo}
            />

            {/* Currency Selector */}
            <CurrencySelector
              defaultCurrency={targetCurrency}
              onCurrencyChange={setTargetCurrency}
            />

            {/* Contract Info Card */}
            <div className={`rounded-lg shadow p-4 ${
              theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
            }`}>
              <h4 className={`text-sm font-semibold mb-3 ${
                theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Contract Information
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                    Total Clauses:
                  </span>
                  <span className={theme === 'dark' ? 'text-white' : 'text-gray-900'}>
                    {clauses.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                    High Risk:
                  </span>
                  <span className="text-red-600 font-medium">
                    {clauses.filter(c => (c.risk_score || 0) >= 0.7).length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                    Contract Value:
                  </span>
                  <span className={theme === 'dark' ? 'text-white' : 'text-gray-900'}>
                    {contract?.contract_value || 'Not set'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                    Display Currency:
                  </span>
                  <span className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'} font-medium`}>
                    {targetCurrency}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel - Results */}
          <div className="lg:col-span-2">
            {!simulationResult && !simulationLoading && (
              <div className={`rounded-lg shadow-lg p-12 text-center ${
                theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
              }`}>
                <FlaskConical className={`w-16 h-16 mx-auto mb-4 ${
                  theme === 'dark' ? 'text-gray-600' : 'text-gray-300'
                }`} />
                <h3 className={`text-xl font-semibold mb-2 ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Select a Clause to Simulate
                </h3>
                <p className={`max-w-md mx-auto ${
                  theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                }`}>
                  Choose a clause from the left panel and click "Simulate Removal" to see
                  how removing it would impact contract risk, financial exposure, and
                  negotiation priorities.
                </p>
              </div>
            )}

            {simulationLoading && (
              <div className={`rounded-lg shadow-lg p-12 text-center ${
                theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
              }`}>
                <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
                <h3 className={`text-xl font-semibold mb-2 ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Running Simulation...
                </h3>
                <p className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}>
                  {includeMonteCarlo
                    ? 'Running Monte Carlo analysis (3000 iterations)...'
                    : 'Calculating risk propagation impact...'}
                </p>
              </div>
            )}

            {simulationResult && (
              <div className="space-y-6">
                {/* Removed Clause Info */}
                {simulationResult.removed_clause && (
                  <div className={`rounded-lg p-4 ${
                    theme === 'dark'
                      ? 'bg-red-900 bg-opacity-30 border border-red-800'
                      : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex items-center space-x-3">
                      <TrendingDown className="w-5 h-5 text-red-600" />
                      <div>
                        <p className={`font-medium ${
                          theme === 'dark' ? 'text-red-300' : 'text-red-800'
                        }`}>
                          Simulating removal of: {simulationResult.removed_clause.type || 'Unknown'} clause
                        </p>
                        <p className={`text-sm ${
                          theme === 'dark' ? 'text-red-400' : 'text-red-600'
                        }`}>
                          Risk Score: {simulationResult.removed_clause.risk_score?.toFixed(3)} |
                          Connections: {simulationResult.removed_clause.connections_removed}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* KPIs */}
                <WhatIfKPIs
                  delta={simulationResult.delta}
                  exposure={simulationResult.exposure}
                />

                {/* Graph Comparison */}
                <WhatIfGraphComparison timeline={simulationResult.timeline} />

                {/* Risk Propagation with Confidence Bands */}
                {simulationResult.timeline?.before && (
                  <>
                    <RiskPropagationChart
                      timeline={simulationResult.timeline.before}
                      monteCarlo={simulationResult.monte_carlo?.before}
                      title="Risk Propagation - Before (Current Contract)"
                    />
                    <RiskPropagationChart
                      timeline={simulationResult.timeline.after}
                      monteCarlo={simulationResult.monte_carlo?.after}
                      title="Risk Propagation - After (Clause Removed)"
                    />
                  </>
                )}

                {/* Exposure Analysis */}
                {simulationResult.exposure && (
                  <ExposureKPIs exposure={simulationResult.exposure} />
                )}

                {/* Negotiation Impact */}
                <NegotiationImpactSummary
                  negotiation={simulationResult.negotiation}
                  delta={simulationResult.delta}
                />

                {/* Monte Carlo Results */}
                {simulationResult.monte_carlo && (
                  <MonteCarloVisualization monteCarlo={simulationResult.monte_carlo} />
                )}

                {/* Graph Metrics */}
                {simulationResult.graph_metrics && (
                  <div className={`rounded-lg shadow p-4 ${
                    theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
                  }`}>
                    <h4 className={`text-sm font-semibold mb-3 ${
                      theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                    }`}>
                      Graph Structure Impact
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                          Nodes Before
                        </p>
                        <p className={`font-medium ${
                          theme === 'dark' ? 'text-white' : 'text-gray-900'
                        }`}>
                          {simulationResult.graph_metrics.nodes_before}
                        </p>
                      </div>
                      <div>
                        <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                          Nodes After
                        </p>
                        <p className="font-medium text-green-600">
                          {simulationResult.graph_metrics.nodes_after}
                        </p>
                      </div>
                      <div>
                        <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                          Edges Before
                        </p>
                        <p className={`font-medium ${
                          theme === 'dark' ? 'text-white' : 'text-gray-900'
                        }`}>
                          {simulationResult.graph_metrics.edges_before}
                        </p>
                      </div>
                      <div>
                        <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                          Edges After
                        </p>
                        <p className="font-medium text-green-600">
                          {simulationResult.graph_metrics.edges_after}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
