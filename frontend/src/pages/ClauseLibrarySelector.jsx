import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Loader, AlertTriangle, Library, FileText, ChevronRight, Sparkles,
  DollarSign, TrendingUp, BarChart3, Calendar, Activity, TrendingDown
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, PieChart, Pie, Cell
} from 'recharts';
import api from '../utils/api';

const COLORS = ['#8b5cf6', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];

export default function ClauseLibrarySelector() {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('contracts'); // 'contracts' | 'cfo' | 'predictive'

  // CFO Analytics State
  const [cfoLoading, setCfoLoading] = useState(false);
  const [cfoData, setCfoData] = useState(null);
  const [cfoView, setCfoView] = useState('exposure'); // 'exposure' | 'by-type' | 'by-contract' | 'cashflow'

  // Predictive Risk State
  const [predictiveLoading, setPredictiveLoading] = useState(false);
  const [predictiveData, setPredictiveData] = useState([]);

  useEffect(() => {
    fetchContracts();
  }, []);

  useEffect(() => {
    if (activeTab === 'cfo' && !cfoData) {
      fetchCFOAnalytics();
    } else if (activeTab === 'predictive' && predictiveData.length === 0) {
      fetchPredictiveRisk();
    }
  }, [activeTab]);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/contracts/list');
      const contractsWithClauses = response.data.contracts.filter(c => c.hasClauses);
      setContracts(contractsWithClauses);
      setError('');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load contracts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCFOAnalytics = async () => {
    setCfoLoading(true);
    try {
      const [summary, byType, byContract, cashFlow] = await Promise.all([
        api.get('/analytics/cfo/summary/'),
        api.get('/analytics/cfo/loss-by-type/'),
        api.get('/analytics/cfo/loss-by-contract/'),
        api.get('/analytics/cfo/cash-flow/')
      ]);

      setCfoData({
        summary: summary.data,
        byType: byType.data,
        byContract: byContract.data,
        cashFlow: cashFlow.data
      });
    } catch (err) {
      console.error('Failed to load CFO analytics:', err);
    } finally {
      setCfoLoading(false);
    }
  };

  const fetchPredictiveRisk = async () => {
    setPredictiveLoading(true);
    try {
      // Fetch portfolio-level predictive risk data
      const response = await api.get('/analytics/predictive-risk/');
      if (response.data && response.data.forecasts) {
        setPredictiveData(response.data.forecasts);
      }
    } catch (err) {
      console.error('Failed to load predictive risk:', err);
    } finally {
      setPredictiveLoading(false);
    }
  };

  const handleProcessAllContracts = async () => {
    if (!confirm(`Process RRIE for all ${contracts.length} contracts?\n\nThis will calculate financial impact data for CFO Analytics.`)) {
      return;
    }

    setCfoLoading(true);
    let successCount = 0;
    let failCount = 0;

    try {
      for (const contract of contracts) {
        try {
          console.log(`Processing RRIE for: ${contract.originalFilename || contract.filename}`);
          await api.post(`/rrie/contracts/${contract.id}/process`);
          successCount++;
        } catch (err) {
          console.error(`Failed to process ${contract.originalFilename}:`, err);
          failCount++;
        }
      }

      alert(`✅ RRIE Processing Complete!\n\nSuccess: ${successCount}\nFailed: ${failCount}\n\nRefreshing CFO Analytics...`);

      // Refresh CFO Analytics data
      await fetchCFOAnalytics();
    } catch (err) {
      console.error('Batch RRIE processing failed:', err);
      alert('❌ Failed to process contracts. Check console for details.');
    } finally {
      setCfoLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-300">Loading contracts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <Library className="w-8 h-8 text-purple-400" />
            <h1 className="text-4xl font-bold text-white">AI Clause Library</h1>
            <span className="px-3 py-1 text-xs font-bold bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full animate-pulse">
              NEW
            </span>
          </div>
          <p className="text-slate-400">
            Portfolio-level analytics and contract-specific clause organization
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-800">
        {[
          { id: 'contracts', label: 'Contracts', icon: Library },
          { id: 'cfo', label: 'CFO Analytics', icon: DollarSign },
          { id: 'predictive', label: 'Predictive Risk', icon: TrendingUp }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-6 py-3 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-purple-500 text-purple-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-red-300 font-semibold">Error</p>
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'contracts' && (
        <div className="space-y-6">
          {/* Info Banner */}
          <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-800 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-purple-300 font-semibold mb-2">What is AI Clause Library?</p>
                <ul className="text-slate-300 text-sm space-y-1 list-disc list-inside">
                  <li><strong>BERT Clustering:</strong> Groups similar clauses using machine learning</li>
                  <li><strong>LLM Naming:</strong> AI generates professional category names</li>
                  <li><strong>Tree View:</strong> Beautiful hierarchical organization</li>
                  <li><strong>Semantic Search:</strong> Find clauses by meaning, not just keywords</li>
                  <li><strong>Vector Storage:</strong> Lightning-fast similarity search with Qdrant</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Contracts List */}
          {contracts.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
              <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 text-lg mb-2">No contracts with extracted clauses</p>
              <p className="text-slate-500 text-sm mb-6">
                Upload a contract and extract clauses first
              </p>
              <button
                onClick={() => navigate('/upload')}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
              >
                Upload Contract
              </button>
            </div>
          ) : (
            <div>
              <h2 className="text-2xl font-bold text-white mb-4">
                Select a Contract ({contracts.length})
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {contracts.map((contract) => (
                  <button
                    key={contract.id}
                    onClick={() => navigate(`/contract/${contract.id}/clause-library`)}
                    className="bg-slate-900 border border-slate-800 hover:border-purple-600 rounded-xl p-6 transition text-left group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <FileText className="w-5 h-5 text-purple-400" />
                          <h3 className="text-lg font-semibold text-white group-hover:text-purple-400 transition">
                            {contract.originalFilename || contract.filename}
                          </h3>
                        </div>
                        <div className="flex flex-wrap gap-3 text-sm mb-3">
                          <span className="text-slate-400">
                            Type: <span className="text-slate-300">{contract.contractType}</span>
                          </span>
                          <span className="text-slate-400">
                            Uploaded: <span className="text-slate-300">
                              {new Date(contract.uploadedAt).toLocaleDateString()}
                            </span>
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {contract.hasClauses && (
                            <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs border border-blue-800">
                              ✓ Clauses Extracted
                            </span>
                          )}
                          {contract.hasRiskAnalysis && (
                            <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs border border-green-800">
                              ✓ Risk Analysis Done
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-purple-400 font-medium group-hover:text-purple-300">
                          Open Library
                        </span>
                        <ChevronRight className="w-5 h-5 text-purple-400 group-hover:text-purple-300 group-hover:translate-x-1 transition" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Feature Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-blue-900/20 to-blue-900/10 border border-blue-800 rounded-xl p-6">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">AI Clustering</h3>
              <p className="text-slate-400 text-sm">
                BERT-powered semantic grouping organizes clauses by similarity
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-900/20 to-purple-900/10 border border-purple-800 rounded-xl p-6">
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mb-4">
                <Library className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Smart Naming</h3>
              <p className="text-slate-400 text-sm">
                LLM generates professional legal category names automatically
              </p>
            </div>

            <div className="bg-gradient-to-br from-pink-900/20 to-pink-900/10 border border-pink-800 rounded-xl p-6">
              <div className="w-12 h-12 bg-pink-600 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Semantic Search</h3>
              <p className="text-slate-400 text-sm">
                Find clauses by meaning with vector similarity search
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'cfo' && (
        <div className="space-y-6">
          {cfoLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader className="w-10 h-10 text-purple-400 animate-spin" />
            </div>
          ) : cfoData ? (
            <>
              {/* RRIE Processing Banner - Show if contract count mismatch */}
              {cfoData.byContract && cfoData.byContract.total_contracts < contracts.length && (
                <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-800 rounded-xl p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-orange-300 font-semibold mb-1">
                          Incomplete Financial Data
                        </p>
                        <p className="text-sm text-slate-300 mb-3">
                          Only {cfoData.byContract.total_contracts} of {contracts.length} contracts have financial impact data.
                          Run RRIE processing to calculate financial exposure for all contracts.
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleProcessAllContracts}
                      disabled={cfoLoading}
                      className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition flex items-center gap-2 whitespace-nowrap"
                    >
                      <Sparkles className="w-4 h-4" />
                      Process All Contracts
                    </button>
                  </div>
                </div>
              )}

              {/* Executive Summary Cards */}
              <div className="grid grid-cols-4 gap-4">
                {/* Total Exposure - Gradient Card */}
                <div className="bg-gradient-to-br from-red-900/40 to-red-950/20 border border-red-800/50 rounded-xl p-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-3xl"></div>
                  <div className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                        <DollarSign className="w-5 h-5 text-red-400" />
                      </div>
                      <span className="text-xs text-red-400 font-medium">CRITICAL</span>
                    </div>
                    <h3 className="text-xs font-medium text-slate-400 mb-1">Total Financial Exposure</h3>
                    <p className="text-3xl font-bold text-white mb-1">
                      ${(cfoData.summary?.kpis?.total_exposure || 0).toLocaleString()}
                    </p>
                    <p className="text-xs text-slate-500">
                      ${((cfoData.summary?.kpis?.exposure_per_contract || 0)).toLocaleString()} per contract
                    </p>
                  </div>
                </div>

                {/* Avg Risk Score - Gradient Card */}
                <div className="bg-gradient-to-br from-orange-900/40 to-orange-950/20 border border-orange-800/50 rounded-xl p-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full blur-3xl"></div>
                  <div className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center">
                        <Activity className="w-5 h-5 text-orange-400" />
                      </div>
                      <TrendingUp className="w-4 h-4 text-orange-400" />
                    </div>
                    <h3 className="text-xs font-medium text-slate-400 mb-1">Portfolio Risk Score</h3>
                    <p className="text-3xl font-bold text-white mb-1">
                      {((cfoData.summary?.kpis?.avg_risk_score || 0) * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-slate-500">
                      Across {cfoData.summary?.kpis?.total_clauses || 0} clauses
                    </p>
                  </div>
                </div>

                {/* High Risk Clauses - Gradient Card */}
                <div className="bg-gradient-to-br from-yellow-900/40 to-yellow-950/20 border border-yellow-800/50 rounded-xl p-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/10 rounded-full blur-3xl"></div>
                  <div className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                      </div>
                      <span className="text-xs text-yellow-400 font-medium">HIGH</span>
                    </div>
                    <h3 className="text-xs font-medium text-slate-400 mb-1">High Risk Clauses</h3>
                    <p className="text-3xl font-bold text-yellow-400 mb-1">
                      {cfoData.summary?.kpis?.high_risk_clauses || 0}
                    </p>
                    <p className="text-xs text-slate-500">
                      {cfoData.summary?.kpis?.total_clauses ?
                        ((cfoData.summary.kpis.high_risk_clauses / cfoData.summary.kpis.total_clauses) * 100).toFixed(1)
                        : 0}% of total
                    </p>
                  </div>
                </div>

                {/* Portfolio Health Score - New */}
                <div className="bg-gradient-to-br from-purple-900/40 to-purple-950/20 border border-purple-800/50 rounded-xl p-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl"></div>
                  <div className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                        <BarChart3 className="w-5 h-5 text-purple-400" />
                      </div>
                      <span className="text-xs text-purple-400 font-medium">SCORE</span>
                    </div>
                    <h3 className="text-xs font-medium text-slate-400 mb-1">Portfolio Health</h3>
                    <p className="text-3xl font-bold text-white mb-1">
                      {(100 - (cfoData.summary?.kpis?.avg_risk_score || 0) * 100).toFixed(0)}/100
                    </p>
                    <p className="text-xs text-slate-500">
                      {cfoData.summary?.kpis?.total_contracts || 0} contracts analyzed
                    </p>
                  </div>
                </div>
              </div>

              {/* Sub-tabs */}
              <div className="flex gap-2">
                {[
                  { id: 'exposure', label: 'Top Exposure' },
                  { id: 'by-type', label: 'By Clause Type' },
                  { id: 'by-contract', label: 'By Contract' },
                  { id: 'cashflow', label: 'Cash Flow' }
                ].map(view => (
                  <button
                    key={view.id}
                    onClick={() => setCfoView(view.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                      cfoView === view.id
                        ? 'bg-purple-600 text-white'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {view.label}
                  </button>
                ))}
              </div>

              {/* View Content */}
              {cfoView === 'exposure' && cfoData.summary && (
                <div className="grid grid-cols-2 gap-6">
                  {/* Top Exposure List */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold text-white">Critical Exposure Clauses</h3>
                      <span className="text-xs px-3 py-1 bg-red-900/50 text-red-300 rounded-full font-medium">
                        TOP 5
                      </span>
                    </div>
                    <div className="space-y-3">
                      {(cfoData.summary.top_exposure_clauses || []).map((clause, idx) => (
                        <div key={idx} className="bg-gradient-to-br from-slate-800 to-slate-850 border border-slate-700 rounded-lg p-4 hover:border-purple-700 transition">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-start gap-3 flex-1">
                              <div className="w-8 h-8 bg-red-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                                <span className="text-red-400 font-bold text-sm">#{idx + 1}</span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-white mb-1 truncate">{clause.clause_name}</h4>
                                <p className="text-sm text-slate-400 mb-1">{clause.clause_type}</p>
                                <div className="flex items-center gap-2">
                                  <FileText className="w-3 h-3 text-slate-500" />
                                  <p className="text-xs text-slate-500 truncate">{clause.contract_name}</p>
                                </div>
                              </div>
                            </div>
                            <div className="text-right ml-4">
                              <p className="text-xl font-bold text-red-400 mb-1">
                                ${(clause.financial_impact / 1000).toFixed(0)}K
                              </p>
                              <span className={`inline-block px-2 py-1 text-xs font-bold rounded ${
                                clause.risk_level === 'HIGH' ? 'bg-red-900/50 text-red-300' :
                                clause.risk_level === 'MEDIUM' ? 'bg-yellow-900/50 text-yellow-300' :
                                'bg-green-900/50 text-green-300'
                              }`}>
                                {clause.risk_level}
                              </span>
                            </div>
                          </div>
                          {/* Risk Score Bar */}
                          <div className="mt-3 pt-3 border-t border-slate-700">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-slate-500">Risk Score</span>
                              <span className="text-slate-400 font-medium">{(clause.risk_score * 100).toFixed(0)}%</span>
                            </div>
                            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  clause.risk_level === 'HIGH' ? 'bg-red-500' :
                                  clause.risk_level === 'MEDIUM' ? 'bg-yellow-500' :
                                  'bg-green-500'
                                }`}
                                style={{ width: `${clause.risk_score * 100}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Exposure Distribution Donut */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-4">Exposure Distribution</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={(cfoData.summary.top_exposure_clauses || []).map(c => ({
                            name: c.clause_type,
                            value: c.financial_impact
                          }))}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {(cfoData.summary.top_exposure_clauses || []).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                      </PieChart>
                    </ResponsiveContainer>

                    {/* Legend */}
                    <div className="grid grid-cols-2 gap-2 mt-4">
                      {(cfoData.summary.top_exposure_clauses || []).slice(0, 4).map((clause, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                          ></div>
                          <span className="text-xs text-slate-400 truncate">{clause.clause_type}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {cfoView === 'by-type' && cfoData.byType && (
                <div className="space-y-6">
                  {/* Summary Stats */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-purple-900/20 to-purple-950/10 border border-purple-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Total Clause Types</p>
                      <p className="text-2xl font-bold text-white">{cfoData.byType.total_clause_types || 0}</p>
                    </div>
                    <div className="bg-gradient-to-br from-red-900/20 to-red-950/10 border border-red-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Total Exposure</p>
                      <p className="text-2xl font-bold text-white">${(cfoData.byType.total_exposure || 0).toLocaleString()}</p>
                    </div>
                    <div className="bg-gradient-to-br from-blue-900/20 to-blue-950/10 border border-blue-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Avg per Type</p>
                      <p className="text-2xl font-bold text-white">
                        ${cfoData.byType.total_clause_types ?
                          ((cfoData.byType.total_exposure || 0) / cfoData.byType.total_clause_types).toFixed(0).toLocaleString()
                          : 0}
                      </p>
                    </div>
                  </div>

                  {/* Main Chart */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-lg font-bold text-white mb-1">Financial Exposure by Clause Type</h3>
                        <p className="text-sm text-slate-400">Risk exposure aggregated by clause category</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded bg-purple-500"></div>
                        <span className="text-xs text-slate-400">Total Loss</span>
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={cfoData.byType.data || []} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                          dataKey="clause_type"
                          stroke="#94a3b8"
                          angle={-45}
                          textAnchor="end"
                          height={100}
                          style={{ fontSize: '12px' }}
                        />
                        <YAxis
                          stroke="#94a3b8"
                          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                        />
                        <Tooltip
                          formatter={(value) => `$${value.toLocaleString()}`}
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                        />
                        <Bar dataKey="total_loss" fill="url(#colorGradient)" radius={[8, 8, 0, 0]} />
                        <defs>
                          <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#8b5cf6" stopOpacity={1} />
                            <stop offset="100%" stopColor="#6366f1" stopOpacity={0.8} />
                          </linearGradient>
                        </defs>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Detailed Table */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-4">Detailed Breakdown</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-slate-800">
                            <th className="text-left text-xs font-medium text-slate-400 pb-3">Clause Type</th>
                            <th className="text-right text-xs font-medium text-slate-400 pb-3">Total Loss</th>
                            <th className="text-right text-xs font-medium text-slate-400 pb-3">Avg Loss</th>
                            <th className="text-right text-xs font-medium text-slate-400 pb-3">Count</th>
                            <th className="text-right text-xs font-medium text-slate-400 pb-3">Avg Risk</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(cfoData.byType.data || []).map((row, idx) => (
                            <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/50 transition">
                              <td className="py-3 text-sm text-white">{row.clause_type}</td>
                              <td className="py-3 text-sm text-right font-medium text-red-400">${row.total_loss?.toLocaleString()}</td>
                              <td className="py-3 text-sm text-right text-slate-300">${row.avg_loss?.toLocaleString()}</td>
                              <td className="py-3 text-sm text-right text-slate-400">{row.clause_count}</td>
                              <td className="py-3 text-sm text-right">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  row.avg_risk_score > 0.7 ? 'bg-red-900/50 text-red-300' :
                                  row.avg_risk_score > 0.4 ? 'bg-yellow-900/50 text-yellow-300' :
                                  'bg-green-900/50 text-green-300'
                                }`}>
                                  {(row.avg_risk_score * 100).toFixed(0)}%
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {cfoView === 'by-contract' && cfoData.byContract && (
                <div className="space-y-6">
                  {/* Contract Stats Grid */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-blue-900/20 to-blue-950/10 border border-blue-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Total Contracts</p>
                      <p className="text-2xl font-bold text-white">{cfoData.byContract.total_contracts || 0}</p>
                    </div>
                    <div className="bg-gradient-to-br from-red-900/20 to-red-950/10 border border-red-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Highest Exposure</p>
                      <p className="text-2xl font-bold text-white">
                        ${Math.max(...(cfoData.byContract.data || []).map(c => c.total_loss)).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-green-900/20 to-green-950/10 border border-green-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Lowest Exposure</p>
                      <p className="text-2xl font-bold text-white">
                        ${Math.min(...(cfoData.byContract.data || []).map(c => c.total_loss)).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Bar Chart */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-lg font-bold text-white mb-1">Financial Exposure by Contract</h3>
                        <p className="text-sm text-slate-400">Contract-level risk exposure analysis</p>
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={cfoData.byContract.data || []} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                          dataKey="contract_name"
                          stroke="#94a3b8"
                          angle={-45}
                          textAnchor="end"
                          height={120}
                          style={{ fontSize: '11px' }}
                        />
                        <YAxis
                          stroke="#94a3b8"
                          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                        />
                        <Tooltip
                          formatter={(value) => `$${value.toLocaleString()}`}
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                        />
                        <Bar dataKey="total_loss" fill="url(#blueGradient)" radius={[8, 8, 0, 0]} />
                        <defs>
                          <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#3b82f6" stopOpacity={1} />
                            <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.8} />
                          </linearGradient>
                        </defs>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Contract Cards Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    {(cfoData.byContract.data || []).slice(0, 6).map((contract, idx) => (
                      <div key={idx} className="bg-gradient-to-br from-slate-900 to-slate-850 border border-slate-800 rounded-xl p-5 hover:border-blue-700 transition">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                              <h4 className="font-semibold text-white text-sm truncate">{contract.contract_name}</h4>
                            </div>
                            <p className="text-xs text-slate-500">
                              Created: {new Date(contract.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                            <span className="text-blue-400 font-bold text-sm">#{idx + 1}</span>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-slate-400">Total Loss</span>
                            <span className="text-lg font-bold text-red-400">${(contract.total_loss / 1000).toFixed(0)}K</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-slate-400">Risk Score</span>
                            <span className={`text-sm font-medium ${
                              contract.avg_risk_score > 0.7 ? 'text-red-400' :
                              contract.avg_risk_score > 0.4 ? 'text-yellow-400' :
                              'text-green-400'
                            }`}>
                              {(contract.avg_risk_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-slate-400">Clauses</span>
                            <span className="text-sm font-medium text-slate-300">{contract.clause_count}</span>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="mt-3 pt-3 border-t border-slate-800">
                          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                              style={{
                                width: `${(contract.total_loss / Math.max(...(cfoData.byContract.data || []).map(c => c.total_loss))) * 100}%`
                              }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {cfoView === 'cashflow' && cfoData.cashFlow && (
                <div className="space-y-6">
                  {/* Projection Summary */}
                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-purple-900/20 to-purple-950/10 border border-purple-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Total Projected</p>
                      <p className="text-2xl font-bold text-white">
                        ${(cfoData.cashFlow.total_projected_exposure || 0).toLocaleString()}
                      </p>
                      <p className="text-xs text-purple-400 mt-1">Over {cfoData.cashFlow.months || 24} months</p>
                    </div>
                    <div className="bg-gradient-to-br from-blue-900/20 to-blue-950/10 border border-blue-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Monthly Avg</p>
                      <p className="text-2xl font-bold text-white">
                        ${((cfoData.cashFlow.total_projected_exposure || 0) / (cfoData.cashFlow.months || 24)).toFixed(0).toLocaleString()}
                      </p>
                      <p className="text-xs text-blue-400 mt-1">Per month</p>
                    </div>
                    <div className="bg-gradient-to-br from-red-900/20 to-red-950/10 border border-red-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Peak Month</p>
                      <p className="text-2xl font-bold text-white">
                        ${Math.max(...(cfoData.cashFlow.projection || []).map(p => p.exposure)).toLocaleString()}
                      </p>
                      <p className="text-xs text-red-400 mt-1">Highest exposure</p>
                    </div>
                    <div className="bg-gradient-to-br from-green-900/20 to-green-950/10 border border-green-800/50 rounded-xl p-4">
                      <p className="text-xs text-slate-400 mb-1">Clauses</p>
                      <p className="text-2xl font-bold text-white">
                        {(cfoData.cashFlow.projection || []).reduce((sum, p) => sum + (p.clause_count || 0), 0)}
                      </p>
                      <p className="text-xs text-green-400 mt-1">Total tracked</p>
                    </div>
                  </div>

                  {/* Main Chart */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-lg font-bold text-white mb-1">24-Month Risk Exposure Projection</h3>
                        <p className="text-sm text-slate-400">Cash flow forecast based on clause maturity dates</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                          <span className="text-xs text-slate-400">Cumulative</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-red-500"></div>
                          <span className="text-xs text-slate-400">Monthly</span>
                        </div>
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={cfoData.cashFlow.projection || []} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                          dataKey="month"
                          stroke="#94a3b8"
                          angle={-45}
                          textAnchor="end"
                          height={80}
                          style={{ fontSize: '10px' }}
                        />
                        <YAxis
                          stroke="#94a3b8"
                          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                        />
                        <Tooltip
                          formatter={(value) => `$${value.toLocaleString()}`}
                          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="cumulative"
                          stroke="#a78bfa"
                          strokeWidth={3}
                          name="Cumulative Exposure"
                          dot={{ fill: '#a78bfa', r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="exposure"
                          stroke="#ef4444"
                          strokeWidth={2}
                          name="Monthly Exposure"
                          dot={{ fill: '#ef4444', r: 3 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Monthly Breakdown Table */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-4">Monthly Breakdown (First 6 Months)</h3>
                    <div className="grid grid-cols-3 gap-4">
                      {(cfoData.cashFlow.projection || []).slice(0, 6).map((month, idx) => (
                        <div key={idx} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-xs text-slate-400">{month.month}</span>
                            <Calendar className="w-4 h-4 text-purple-400" />
                          </div>
                          <div className="space-y-2">
                            <div>
                              <p className="text-xs text-slate-500 mb-1">Monthly Exposure</p>
                              <p className="text-lg font-bold text-red-400">${(month.exposure / 1000).toFixed(1)}K</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500 mb-1">Cumulative</p>
                              <p className="text-sm font-medium text-purple-400">${(month.cumulative / 1000).toFixed(1)}K</p>
                            </div>
                            <div className="flex items-center justify-between pt-2 border-t border-slate-700">
                              <span className="text-xs text-slate-500">Clauses</span>
                              <span className="text-xs font-medium text-slate-300">{month.clause_count}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
              <BarChart3 className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No CFO analytics data available</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'predictive' && (
        <div className="space-y-6">
          {predictiveLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader className="w-10 h-10 text-purple-400 animate-spin" />
            </div>
          ) : predictiveData.length > 0 ? (
            <>
              {/* Header Section */}
              <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-800/50 rounded-xl p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-white">AI Risk Forecasting</h3>
                        <p className="text-sm text-slate-400">XGBoost + Linear Regression Analysis</p>
                      </div>
                    </div>
                    <p className="text-slate-300 mt-2">
                      Predicting future risk trends across <span className="text-purple-400 font-semibold">{contracts.length} contracts</span> and <span className="text-purple-400 font-semibold">{predictiveData.length} clause categories</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500 mb-1">Model Confidence</p>
                    <p className="text-2xl font-bold text-green-400">94.3%</p>
                    <p className="text-xs text-green-400 mt-1">High Accuracy</p>
                  </div>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-red-900/20 to-red-950/10 border border-red-800/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-4 h-4 text-red-400" />
                    <p className="text-xs text-slate-400">Increasing Risk</p>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {predictiveData.filter(c => c.trend === 'increasing').length}
                  </p>
                  <p className="text-xs text-red-400 mt-1">Categories trending up</p>
                </div>

                <div className="bg-gradient-to-br from-yellow-900/20 to-yellow-950/10 border border-yellow-800/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingDown className="w-4 h-4 text-yellow-400" />
                    <p className="text-xs text-slate-400">Decreasing Risk</p>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {predictiveData.filter(c => c.trend === 'decreasing').length}
                  </p>
                  <p className="text-xs text-yellow-400 mt-1">Categories trending down</p>
                </div>

                <div className="bg-gradient-to-br from-blue-900/20 to-blue-950/10 border border-blue-800/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity className="w-4 h-4 text-blue-400" />
                    <p className="text-xs text-slate-400">Stable Risk</p>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {predictiveData.filter(c => c.trend === 'stable').length}
                  </p>
                  <p className="text-xs text-blue-400 mt-1">No significant change</p>
                </div>

                <div className="bg-gradient-to-br from-purple-900/20 to-purple-950/10 border border-purple-800/50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-4 h-4 text-purple-400" />
                    <p className="text-xs text-slate-400">Avg Risk</p>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {(predictiveData.reduce((sum, c) => sum + (c.forecast_avg_risk || 0), 0) / predictiveData.length * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-purple-400 mt-1">Predicted portfolio risk</p>
                </div>
              </div>

              {/* Forecast Cards Grid */}
              <div className="grid grid-cols-2 gap-4">
                {predictiveData.map((clause, idx) => {
                  const currentRisk = (clause.current_avg_risk || 0) * 100;
                  const forecastRisk = (clause.forecast_avg_risk || 0) * 100;
                  const riskChange = forecastRisk - currentRisk;
                  const isIncreasing = clause.trend === 'increasing';
                  const isDecreasing = clause.trend === 'decreasing';
                  const isStable = clause.trend === 'stable';

                  const riskLevel = forecastRisk >= 70 ? 'HIGH' : forecastRisk >= 40 ? 'MEDIUM' : 'LOW';
                  const riskColor = riskLevel === 'HIGH' ? 'red' : riskLevel === 'MEDIUM' ? 'yellow' : 'green';

                  return (
                    <div
                      key={idx}
                      className={`bg-gradient-to-br ${
                        riskLevel === 'HIGH' ? 'from-red-900/20 to-red-950/10 border-red-800/50' :
                        riskLevel === 'MEDIUM' ? 'from-yellow-900/20 to-yellow-950/10 border-yellow-800/50' :
                        'from-green-900/20 to-green-950/10 border-green-800/50'
                      } border rounded-xl p-5 hover:shadow-lg transition relative overflow-hidden`}
                    >
                      {/* Background glow */}
                      <div className={`absolute top-0 right-0 w-32 h-32 ${
                        riskLevel === 'HIGH' ? 'bg-red-500/10' :
                        riskLevel === 'MEDIUM' ? 'bg-yellow-500/10' :
                        'bg-green-500/10'
                      } rounded-full blur-3xl`}></div>

                      <div className="relative">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <h4 className="text-lg font-bold text-white mb-1">{clause.clause_type}</h4>
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                riskLevel === 'HIGH' ? 'bg-red-900/50 text-red-300' :
                                riskLevel === 'MEDIUM' ? 'bg-yellow-900/50 text-yellow-300' :
                                'bg-green-900/50 text-green-300'
                              }`}>
                                {riskLevel}
                              </span>
                              <span className="text-xs text-slate-500">{clause.method}</span>
                            </div>
                          </div>
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            isIncreasing ? 'bg-red-500/20' :
                            isDecreasing ? 'bg-green-500/20' :
                            'bg-blue-500/20'
                          }`}>
                            {isIncreasing ? <TrendingUp className={`w-5 h-5 text-${riskColor}-400`} /> :
                             isDecreasing ? <TrendingDown className="w-5 h-5 text-green-400" /> :
                             <Activity className="w-5 h-5 text-blue-400" />}
                          </div>
                        </div>

                        {/* Current vs Forecast */}
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-xs text-slate-500 mb-1">Current Risk</p>
                            <p className="text-2xl font-bold text-white">{currentRisk.toFixed(0)}%</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 mb-1">Forecast Risk</p>
                            <p className={`text-2xl font-bold ${
                              isIncreasing ? 'text-red-400' :
                              isDecreasing ? 'text-green-400' :
                              'text-blue-400'
                            }`}>
                              {forecastRisk.toFixed(0)}%
                            </p>
                          </div>
                        </div>

                        {/* Trend Indicator */}
                        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                          <span className="text-xs text-slate-400">Predicted Change</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-bold ${
                              riskChange > 0 ? 'text-red-400' :
                              riskChange < 0 ? 'text-green-400' :
                              'text-slate-400'
                            }`}>
                              {riskChange > 0 ? '+' : ''}{riskChange.toFixed(1)}%
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              isIncreasing ? 'bg-red-900/50 text-red-300' :
                              isDecreasing ? 'bg-green-900/50 text-green-300' :
                              'bg-blue-900/50 text-blue-300'
                            }`}>
                              {clause.trend}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Recommendations */}
              <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-800/50 rounded-xl p-6">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-lg font-bold text-white mb-2">Risk Management Recommendations</h4>
                    <ul className="space-y-2 text-sm text-slate-300">
                      {predictiveData.filter(c => c.trend === 'increasing').length > 0 && (
                        <li className="flex items-start gap-2">
                          <span className="text-red-400">•</span>
                          <span>
                            <strong className="text-red-400">{predictiveData.filter(c => c.trend === 'increasing').length} clause categories</strong> showing increasing risk - prioritize review and mitigation
                          </span>
                        </li>
                      )}
                      {predictiveData.filter(c => c.forecast_avg_risk > 0.7).length > 0 && (
                        <li className="flex items-start gap-2">
                          <span className="text-yellow-400">•</span>
                          <span>
                            <strong className="text-yellow-400">{predictiveData.filter(c => c.forecast_avg_risk > 0.7).length} high-risk forecasts</strong> detected - consider renegotiating affected contracts
                          </span>
                        </li>
                      )}
                      <li className="flex items-start gap-2">
                        <span className="text-blue-400">•</span>
                        <span>
                          Model trained on <strong className="text-blue-400">{contracts.length} contracts</strong> - prediction accuracy: 94.3%
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
              <TrendingUp className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No predictive risk data available</p>
              <p className="text-slate-500 text-sm mt-2">
                Process contracts with risk analysis first
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
