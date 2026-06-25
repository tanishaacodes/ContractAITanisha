/**
 * Risk Intelligence Dashboard
 * ============================
 * Unified dashboard for graph-based risk analysis, Monte Carlo simulation,
 * and RAG-powered clause search.
 *
 * Features:
 * - Risk graph visualization (React Flow)
 * - Monte Carlo exposure distribution
 * - Value at Risk (VaR) metrics
 * - Stress test scenarios
 * - Similar clause search (BM25 + BERT)
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  BarChart3,
  Network,
  Search,
  Zap,
  ArrowLeft
} from 'lucide-react';
import {
  runMonteCarloSimulation,
  calculateVaR,
  runStressTest,
  getRiskSubgraph,
  searchSimilarClauses,
  getCascadingRisks,
  getBlastRadius,
  getRiskSubgraphMultihop
} from '../services/riskIntelligence';
import api from '../utils/api';
import ContractNetworkGraph from '../components/graph/ContractNetworkGraph';
import MonteCarloChart from '../components/risk/MonteCarloChart';
import VaRMetrics from '../components/risk/VaRMetrics';
import StressTestTable from '../components/risk/StressTestTable';
import ClauseSearchPanel from '../components/risk/ClauseSearchPanel';
import CascadingRisksView from '../components/risk/CascadingRisksView';
import BlastRadiusView from '../components/risk/BlastRadiusView';

export default function RiskIntelligenceDashboard() {
  const { contractId } = useParams();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('monte-carlo');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [selectedContractId, setSelectedContractId] = useState(contractId || '');

  // Data states
  const [monteCarloData, setMonteCarloData] = useState(null);
  const [varData, setVarData] = useState(null);
  const [stressTestData, setStressTestData] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [cascadingData, setCascadingData] = useState(null);
  const [blastRadiusData, setBlastRadiusData] = useState(null);

  // Load contracts list if no contractId in URL
  useEffect(() => {
    if (!contractId) {
      loadContracts();
    }
  }, []);

  // Load initial data when contract or tab changes
  useEffect(() => {
    const activeContractId = contractId || selectedContractId;
    if (!activeContractId) return;

    if (activeTab === 'monte-carlo' && !monteCarloData) {
      loadMonteCarloData(activeContractId);
    } else if (activeTab === 'var' && !varData) {
      loadVaRData(activeContractId);
    } else if (activeTab === 'stress-test' && !stressTestData) {
      loadStressTestData(activeContractId);
    } else if (activeTab === 'graph' && !graphData) {
      loadGraphData(activeContractId);
    } else if (activeTab === 'cascading' && !cascadingData) {
      loadCascadingData(activeContractId);
    } else if (activeTab === 'blast-radius' && !blastRadiusData) {
      loadBlastRadiusData(activeContractId);
    }
  }, [contractId, selectedContractId, activeTab]);

  const loadContracts = async () => {
    try {
      console.log('Loading contracts...');
      const response = await api.get('/contracts/list');
      const data = response.data?.contracts || [];
      console.log('Loaded contracts:', data.length, data);
      setContracts(data);
      if (data.length > 0) {
        setSelectedContractId(data[0].id);
        console.log('Selected first contract:', data[0].id);
      } else {
        setError('No contracts found. Please upload a contract first.');
      }
    } catch (err) {
      console.error('Failed to load contracts:', err);
      setError('Failed to load contracts: ' + (err.response?.data?.error || err.message));
    }
  };

  const loadMonteCarloData = async (cId) => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading Monte Carlo for contract:', cId);
      const result = await runMonteCarloSimulation(cId, 5000);
      console.log('Monte Carlo result:', result);
      setMonteCarloData(result);
    } catch (err) {
      console.error('Monte Carlo failed:', err);
      console.error('Error response:', err.response?.data);
      const errorMsg = err.response?.data?.error || err.response?.data?.detail || err.message || 'Failed to load Monte Carlo simulation';
      setError(`Monte Carlo Error: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const loadVaRData = async (cId) => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading VaR for contract:', cId);
      const result = await calculateVaR(cId, 0.95);
      console.log('VaR result:', result);
      setVarData(result);
    } catch (err) {
      console.error('VaR calculation failed:', err);
      setError(err.response?.data?.error || err.message || 'Failed to calculate VaR');
    } finally {
      setLoading(false);
    }
  };

  const loadStressTestData = async (cId) => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading stress test for contract:', cId);
      const result = await runStressTest(cId);
      console.log('Stress test result:', result);
      setStressTestData(result);
    } catch (err) {
      console.error('Stress test failed:', err);
      setError(err.response?.data?.error || err.message || 'Failed to run stress test');
    } finally {
      setLoading(false);
    }
  };

  const loadGraphData = async (cId) => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading multi-hop risk graph for contract:', cId);
      const result = await getRiskSubgraphMultihop(cId, 2);
      console.log('Risk graph result:', result);
      setGraphData(result);
    } catch (err) {
      console.error('Graph load failed:', err);
      setError(err.response?.data?.error || err.message || 'Failed to load risk graph');
    } finally {
      setLoading(false);
    }
  };

  const loadCascadingData = async (cId) => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading cascading risks for contract:', cId);
      // Use RISK_INDEMNITY as default source risk - you can make this configurable
      const result = await getCascadingRisks('RISK_INDEMNITY', 3);
      console.log('Cascading risks result:', result);
      setCascadingData(result);
    } catch (err) {
      console.error('Cascading risks failed:', err);
      setError(err.response?.data?.error || err.message || 'Failed to load cascading risks');
    } finally {
      setLoading(false);
    }
  };

  const loadBlastRadiusData = async (cId) => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading blast radius for contract:', cId);
      const result = await getBlastRadius(cId, 3);
      console.log('Blast radius result:', result);
      setBlastRadiusData(result);
    } catch (err) {
      console.error('Blast radius failed:', err);
      setError(err.response?.data?.error || err.message || 'Failed to load blast radius');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'monte-carlo', label: 'Monte Carlo', icon: Activity },
    { id: 'var', label: 'Value at Risk', icon: Target },
    { id: 'stress-test', label: 'Stress Test', icon: AlertTriangle },
    { id: 'graph', label: 'Risk Graph', icon: Network },
    { id: 'cascading', label: 'Cascading Risks', icon: TrendingDown },
    { id: 'blast-radius', label: 'Blast Radius', icon: Zap },
    { id: 'search', label: 'Clause Search', icon: Search }
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-gray-400 hover:text-white mb-4 transition"
        >
          <ArrowLeft size={18} className="mr-2" />
          Back
        </button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center">
              <Zap className="mr-3 text-purple-500" size={32} />
              Risk Intelligence
            </h1>
            <p className="text-gray-400 mt-1">
              Graph-based risk modeling & Monte Carlo simulation
            </p>
          </div>

          {!contractId && contracts.length > 0 && (
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-400">Select Contract:</label>
              <select
                value={selectedContractId}
                onChange={(e) => {
                  console.log('Contract changed to:', e.target.value);
                  setSelectedContractId(e.target.value);
                  // Reset data when contract changes
                  setMonteCarloData(null);
                  setVarData(null);
                  setStressTestData(null);
                  setGraphData(null);
                  setCascadingData(null);
                  setBlastRadiusData(null);
                }}
                className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
              >
                {contracts.map((contract) => (
                  <option key={contract.id} value={contract.id}>
                    {contract.original_filename || contract.file_name || contract.contract_name || `Contract ${contract.id.substring(0, 8)}`}
                  </option>
                ))}
              </select>
            </div>
          )}

          {contractId && (
            <div className="text-sm text-gray-400">
              Contract ID: <span className="font-mono text-purple-400">{contractId}</span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700 mb-6">
        <div className="flex space-x-6">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-4 py-3 border-b-2 transition ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-white'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <Icon size={18} className="mr-2" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <AlertTriangle className="text-red-400 mr-3 mt-0.5" size={20} />
            <div>
              <p className="font-medium text-red-300">Error</p>
              <p className="text-red-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
          <span className="ml-4 text-gray-400">Loading...</span>
        </div>
      )}

      {/* Tab Content */}
      {!loading && (
        <>
          {activeTab === 'monte-carlo' && monteCarloData && (
            <MonteCarloChart data={monteCarloData} />
          )}

          {activeTab === 'var' && varData && (
            <VaRMetrics data={varData} />
          )}

          {activeTab === 'stress-test' && stressTestData && (
            <StressTestTable data={stressTestData} />
          )}

          {activeTab === 'graph' && (
            <ContractNetworkGraph
              contractId={contractId || selectedContractId}
              initialData={graphData}
            />
          )}

          {activeTab === 'cascading' && cascadingData && (
            <CascadingRisksView data={cascadingData} />
          )}

          {activeTab === 'blast-radius' && blastRadiusData && (
            <BlastRadiusView data={blastRadiusData} />
          )}

          {activeTab === 'search' && (
            <ClauseSearchPanel contractId={contractId} />
          )}
        </>
      )}

      {/* Empty States */}
      {!loading && !error && (
        <>
          {activeTab === 'monte-carlo' && !monteCarloData && (
            <div className="text-center py-12">
              <BarChart3 className="mx-auto text-gray-600 mb-4" size={48} />
              <p className="text-gray-400">No Monte Carlo data available</p>
              {(contractId || selectedContractId) && (
                <button
                  onClick={() => loadMonteCarloData(contractId || selectedContractId)}
                  className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition"
                >
                  Run Simulation
                </button>
              )}
            </div>
          )}

          {activeTab === 'var' && !varData && (
            <div className="text-center py-12">
              <Target className="mx-auto text-gray-600 mb-4" size={48} />
              <p className="text-gray-400">No VaR data available</p>
              {(contractId || selectedContractId) && (
                <button
                  onClick={() => loadVaRData(contractId || selectedContractId)}
                  className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition"
                >
                  Calculate VaR
                </button>
              )}
            </div>
          )}

          {activeTab === 'stress-test' && !stressTestData && (
            <div className="text-center py-12">
              <AlertTriangle className="mx-auto text-gray-600 mb-4" size={48} />
              <p className="text-gray-400">No stress test data available</p>
              {(contractId || selectedContractId) && (
                <button
                  onClick={() => loadStressTestData(contractId || selectedContractId)}
                  className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition"
                >
                  Run Stress Test
                </button>
              )}
            </div>
          )}

          {activeTab === 'graph' && !graphData && (
            <div className="text-center py-12">
              <Network className="mx-auto text-gray-600 mb-4" size={48} />
              <p className="text-gray-400">No graph data available</p>
              {(contractId || selectedContractId) && (
                <button
                  onClick={() => loadGraphData(contractId || selectedContractId)}
                  className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition"
                >
                  Load Risk Graph
                </button>
              )}
            </div>
          )}

          {activeTab === 'cascading' && !cascadingData && (
            <div className="text-center py-12">
              <TrendingDown className="mx-auto text-gray-600 mb-4" size={48} />
              <p className="text-gray-400">No cascading risk data available</p>
              {(contractId || selectedContractId) && (
                <button
                  onClick={() => loadCascadingData(contractId || selectedContractId)}
                  className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition"
                >
                  Analyze Cascading Risks
                </button>
              )}
            </div>
          )}

          {activeTab === 'blast-radius' && !blastRadiusData && (
            <div className="text-center py-12">
              <Zap className="mx-auto text-gray-600 mb-4" size={48} />
              <p className="text-gray-400">No blast radius data available</p>
              {(contractId || selectedContractId) && (
                <button
                  onClick={() => loadBlastRadiusData(contractId || selectedContractId)}
                  className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition"
                >
                  Calculate Blast Radius
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
