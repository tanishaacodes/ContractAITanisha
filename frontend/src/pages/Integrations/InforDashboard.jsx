import { useState, useEffect } from 'react';
import useThemeStore from '../../store/themeStore';
import useAuthStore from '../../store/authStore';
import {
  Database,
  RefreshCw,
  Activity,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  DollarSign,
  Calendar,
  Building,
  ShieldAlert,
  Lightbulb,
  Target,
  Play,
  Ban,
  GitBranch,
  UserCheck,
  MessageSquare,
  Layers,
  Zap,
  Clock,
  Box
} from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const InforDashboard = () => {
  const { theme } = useThemeStore();
  const { token } = useAuthStore();

  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [inforStatus, setInforStatus] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [activeTab, setActiveTab] = useState('contracts');
  const [stats, setStats] = useState({ total: 0, highRisk: 0, mediumRisk: 0, lowRisk: 0, totalValue: 0 });

  const [scenarioResults, setScenarioResults] = useState({});
  const [scenarioLoading, setScenarioLoading] = useState({});

  const [batchIds, setBatchIds] = useState('');
  const [batchScenario, setBatchScenario] = useState('process');
  const [batchResult, setBatchResult] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);

  const authHeaders = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  const checkInforStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/infor/health/`, { headers: authHeaders });
      setInforStatus(await res.json());
    } catch {
      setInforStatus({ status: 'error', message: 'Failed to connect' });
    }
  };

  const loadContracts = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/infor/contracts/`, { headers: authHeaders });
      const data = await res.json();
      if (res.ok) {
        setContracts(data.contracts || []);
        calculateStats(data.contracts || []);
      }
    } catch (e) {
      console.error('Error loading Infor contracts:', e);
    } finally {
      setLoading(false);
    }
  };

  const syncFromInfor = async () => {
    setSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/api/infor/contracts/sync/`, {
        method: 'POST',
        headers: authHeaders
      });
      const data = await res.json();
      if (res.ok) {
        setContracts(data.contracts || []);
        calculateStats(data.contracts || []);
      }
    } catch (e) {
      console.error('Sync error:', e);
    } finally {
      setSyncing(false);
    }
  };

  const loadRiskAnalysis = async (contractId) => {
    try {
      const res = await fetch(`${API_BASE}/api/infor/contracts/${contractId}/risk/`, { headers: authHeaders });
      const data = await res.json();
      if (res.ok) setRiskAnalysis(data.risk_analysis || data);
    } catch (e) {
      console.error('Error loading risk analysis:', e);
    }
  };

  const runScenario = async (scenarioKey, endpoint, contractId) => {
    setScenarioLoading(prev => ({ ...prev, [scenarioKey]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/infor/contracts/${contractId}/${endpoint}/`, {
        method: 'POST',
        headers: authHeaders
      });
      const data = await res.json();
      setScenarioResults(prev => ({
        ...prev,
        [scenarioKey]: { ...data, ok: res.ok, timestamp: new Date().toLocaleTimeString() }
      }));
    } catch (e) {
      setScenarioResults(prev => ({
        ...prev,
        [scenarioKey]: { ok: false, error: e.message, timestamp: new Date().toLocaleTimeString() }
      }));
    } finally {
      setScenarioLoading(prev => ({ ...prev, [scenarioKey]: false }));
    }
  };

  const runBatch = async () => {
    const ids = batchIds.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
    if (!ids.length) return alert('Enter at least one contract ID');
    setBatchLoading(true);
    setBatchResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/infor/contracts/batch-process/`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ contract_ids: ids, scenario: batchScenario })
      });
      setBatchResult(await res.json());
    } catch (e) {
      setBatchResult({ error: e.message });
    } finally {
      setBatchLoading(false);
    }
  };

  const calculateStats = (list) => {
    const s = { total: list.length, highRisk: 0, mediumRisk: 0, lowRisk: 0, totalValue: 0 };
    list.forEach(c => {
      const cat = c.riskCategory || '';
      if (cat === 'HIGH' || cat === 'CRITICAL') s.highRisk++;
      else if (cat === 'MEDIUM') s.mediumRisk++;
      else if (cat === 'LOW') s.lowRisk++;
      s.totalValue += parseFloat(c.netAmount || 0);
    });
    setStats(s);
  };

  const handleContractSelect = (contract) => {
    setSelectedContract(contract);
    setRiskAnalysis(null);
    setScenarioResults({});
    const id = contract.id || contract.contractId;
    if (id) loadRiskAnalysis(id);
  };

  const formatCurrency = (amount, currency = 'USD') =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount);

  const getRiskColor = (cat) => {
    switch (cat) {
      case 'CRITICAL': return 'bg-red-600 text-white';
      case 'HIGH': return 'bg-red-500 text-white';
      case 'MEDIUM': return 'bg-yellow-500 text-white';
      case 'LOW': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  useEffect(() => {
    checkInforStatus();
    loadContracts();
  }, []);

  const SCENARIOS = [
    {
      key: 's1', endpoint: 'process',
      label: 'Scenario 1 — Process New Contract',
      description: 'Reads contract from Infor ERP, runs AI risk + intent analysis, updates UDFs (aiRiskScore, aiStatus, aiExposure).',
      icon: Play, btnClass: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      key: 's2', endpoint: 'block-if-high-risk',
      label: 'Scenario 2 — Block High-Risk Contract',
      description: 'Evaluates risk score. If CRITICAL (>80), sets aiStatus = BLOCKED in Infor and adds a blocking note.',
      icon: Ban, btnClass: 'bg-red-600 hover:bg-red-700'
    },
    {
      key: 's3', endpoint: 'amendment',
      label: 'Scenario 3 — Re-Evaluate Amendment',
      description: 'Fetches amended Infor contract, re-calculates risk delta, updates UDFs and alerts if risk increased >20 pts.',
      icon: GitBranch, btnClass: 'bg-purple-600 hover:bg-purple-700'
    },
    {
      key: 's4', endpoint: 'override',
      label: 'Scenario 4 — Manual Override',
      description: 'Checks manualOverride UDF in Infor. If set, marks contract as MANUALLY_APPROVED with audit note.',
      icon: UserCheck, btnClass: 'bg-yellow-600 hover:bg-yellow-700'
    },
    {
      key: 's5', endpoint: 'suggestions',
      label: 'Scenario 5 — AI Clause Suggestions',
      description: 'Generates clause improvement suggestions using AI and attaches them as a structured note in Infor ERP.',
      icon: MessageSquare, btnClass: 'bg-green-600 hover:bg-green-700'
    }
  ];

  const selectedId = selectedContract?.id || selectedContract?.contractId;

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-500/20 rounded-xl">
              <Box className="text-orange-400" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-1">Infor ERP Integration</h1>
              <p className={`${theme.colors.textSecondary} text-sm`}>
                Infor ERP LN / CloudSuite Industrial — Bi-directional AI contract intelligence
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {inforStatus && (
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
                inforStatus.status === 'healthy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {inforStatus.status === 'healthy' ? <CheckCircle size={16} /> : <XCircle size={16} />}
                {inforStatus.status === 'healthy'
                  ? (inforStatus.data_source?.includes('USASpending') ? 'Live — USASpending.gov' : 'Infor Connected')
                  : 'Infor Disconnected'}
              </div>
            )}
            <button
              onClick={syncFromInfor}
              disabled={syncing}
              className="px-5 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition disabled:opacity-50 flex items-center gap-2 text-sm"
            >
              <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
              {syncing ? 'Syncing…' : 'Sync from Infor'}
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {[
          { label: 'Total Contracts', value: stats.total, icon: FileText, color: 'text-orange-400' },
          { label: 'High / Critical', value: stats.highRisk, icon: AlertTriangle, color: 'text-red-400' },
          { label: 'Medium Risk', value: stats.mediumRisk, icon: TrendingUp, color: 'text-yellow-400' },
          { label: 'Low Risk', value: stats.lowRisk, icon: CheckCircle, color: 'text-green-400' },
          { label: 'Total Value', value: formatCurrency(stats.totalValue), icon: DollarSign, color: 'text-emerald-400' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className={`${theme.colors.surface} p-5 rounded-xl border ${theme.colors.surfaceBorder} flex items-center justify-between`}>
            <div>
              <p className={`text-xs ${theme.colors.textSecondary} mb-1`}>{label}</p>
              <p className="text-xl font-bold">{value}</p>
            </div>
            <Icon className={color} size={28} />
          </div>
        ))}
      </div>

      {/* Live data source banner */}
      <div className={`mb-6 p-4 rounded-xl border border-green-500/30 bg-green-500/5 flex items-start gap-3`}>
        <Box className="text-green-400 shrink-0 mt-0.5" size={18} />
        <div className="text-sm">
          <span className="font-semibold text-green-400">Live Data — USASpending.gov</span>
          <span className={`ml-2 ${theme.colors.textSecondary}`}>
            Streaming real US federal procurement contracts (Dept of Defense, Energy, NASA, etc.) with real vendors, real dollar values, and real dates.
            To switch to live Infor ERP data, configure <code className="bg-gray-800 px-1 py-0.5 rounded text-xs">INFOR_BASE_URL</code> env var.
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { key: 'contracts', label: 'Contracts', icon: Database },
          { key: 'scenarios', label: '5 Scenarios', icon: Zap },
          { key: 'batch', label: 'Batch Processing', icon: Layers }
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition ${
              activeTab === key
                ? 'bg-orange-600 text-white'
                : `${theme.colors.surface} border ${theme.colors.surfaceBorder} ${theme.colors.textSecondary} hover:border-orange-500`
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* ── TAB: CONTRACTS ─────────────────────────────────────────── */}
      {activeTab === 'contracts' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Contract List */}
          <div className={`lg:col-span-2 ${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="p-5 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Infor ERP Contracts</h2>
              <Activity className="text-orange-400" size={20} />
            </div>
            <div className="p-5">
              {loading ? (
                <div className="flex justify-center py-12">
                  <RefreshCw className="animate-spin text-orange-400" size={32} />
                </div>
              ) : contracts.length === 0 ? (
                <div className="text-center py-12">
                  <Database className={`mx-auto mb-4 ${theme.colors.textSecondary}`} size={40} />
                  <p className={`${theme.colors.textSecondary} mb-4`}>No contracts found</p>
                  <button onClick={syncFromInfor} className="px-5 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm">
                    Sync from Infor
                  </button>
                </div>
              ) : (
                <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
                  {contracts.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => handleContractSelect(c)}
                      className={`p-4 rounded-lg border cursor-pointer transition ${
                        selectedContract?.id === c.id
                          ? 'border-orange-500 bg-orange-500/10'
                          : `border-gray-700 hover:border-gray-500`
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="font-semibold text-sm">{c.contractId || c.id}</p>
                          <p className={`text-xs ${theme.colors.textSecondary}`}>{c.description || c.contractType}</p>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRiskColor(c.riskCategory)}`}>
                          {c.riskCategory}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-xs mt-2">
                        <div>
                          <p className={theme.colors.textSecondary}>Value</p>
                          <p className="font-medium">{formatCurrency(c.netAmount || 0, c.currency)}</p>
                        </div>
                        <div>
                          <p className={theme.colors.textSecondary}>Vendor</p>
                          <p className="font-medium truncate">{c.vendorName || 'N/A'}</p>
                        </div>
                        <div>
                          <p className={theme.colors.textSecondary}>Risk Score</p>
                          <p className="font-medium">{c.riskScore}/100</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Risk Analysis */}
          <div className={`${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder}`}>
            <div className="p-5 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Risk Analysis</h2>
              <ShieldAlert className="text-red-400" size={20} />
            </div>
            <div className="p-5">
              {!selectedContract ? (
                <div className="text-center py-12">
                  <Target className={`mx-auto mb-3 ${theme.colors.textSecondary}`} size={40} />
                  <p className={`text-sm ${theme.colors.textSecondary}`}>Select a contract to view risk analysis</p>
                </div>
              ) : !riskAnalysis ? (
                <div className="flex justify-center py-12">
                  <RefreshCw className="animate-spin text-orange-400" size={28} />
                </div>
              ) : (
                <div className="space-y-5">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className={`text-xs ${theme.colors.textSecondary}`}>Risk Score</span>
                      <span className={`text-2xl font-bold ${
                        (riskAnalysis.overall_risk_score || 0) >= 60 ? 'text-red-400' :
                        (riskAnalysis.overall_risk_score || 0) >= 30 ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {riskAnalysis.overall_risk_score || 0}/100
                      </span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          (riskAnalysis.overall_risk_score || 0) >= 60 ? 'bg-red-500' :
                          (riskAnalysis.overall_risk_score || 0) >= 30 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${riskAnalysis.overall_risk_score || 0}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <p className={`text-xs ${theme.colors.textSecondary} mb-1`}>Category</p>
                    <span className={`px-3 py-1 rounded text-xs font-medium ${getRiskColor(riskAnalysis.risk_category)}`}>
                      {riskAnalysis.risk_category}
                    </span>
                  </div>

                  {riskAnalysis.risk_factors?.length > 0 && (
                    <div>
                      <p className={`text-xs ${theme.colors.textSecondary} mb-2`}>Risk Factors</p>
                      <div className="space-y-1.5">
                        {riskAnalysis.risk_factors.map((f, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs">
                            <AlertTriangle size={12} className="text-yellow-400 mt-0.5 shrink-0" />
                            <span>{f}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {riskAnalysis.recommendations?.length > 0 && (
                    <div>
                      <p className={`text-xs ${theme.colors.textSecondary} mb-2`}>Recommendations</p>
                      <div className="space-y-1.5">
                        {riskAnalysis.recommendations.map((r, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs">
                            <CheckCircle size={12} className="text-green-400 mt-0.5 shrink-0" />
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {riskAnalysis.clause_suggestions?.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Lightbulb size={14} className="text-yellow-400" />
                        <p className={`text-xs ${theme.colors.textSecondary}`}>Clause Suggestions</p>
                      </div>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {riskAnalysis.clause_suggestions.map((s, i) => (
                          <div key={i} className={`p-2.5 rounded-lg border ${theme.colors.surfaceBorder} text-xs`}>
                            <div className="flex justify-between mb-1">
                              <span className="font-medium text-orange-400">{s.clause_type}</span>
                              <span className={`px-1.5 py-0.5 rounded ${getRiskColor(s.priority)}`}>{s.priority}</span>
                            </div>
                            <p className="text-red-400 mb-1">Current: {s.current}</p>
                            <p className="text-green-400">Suggested: {s.suggested}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className={`pt-4 border-t border-gray-700 space-y-2 text-xs`}>
                    <div className="flex items-center gap-2">
                      <FileText size={12} className={theme.colors.textSecondary} />
                      <span className={theme.colors.textSecondary}>ID:</span>
                      <span className="font-medium">{selectedContract.contractId || selectedContract.id}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Building size={12} className={theme.colors.textSecondary} />
                      <span className={theme.colors.textSecondary}>Vendor:</span>
                      <span className="font-medium">{selectedContract.vendorName || 'N/A'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar size={12} className={theme.colors.textSecondary} />
                      <span className={theme.colors.textSecondary}>Valid:</span>
                      <span className="font-medium">{selectedContract.startDate} — {selectedContract.endDate}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB: 5 SCENARIOS ───────────────────────────────────────── */}
      {activeTab === 'scenarios' && (
        <div className="space-y-6">
          {!selectedContract ? (
            <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-8 text-center`}>
              <Target className={`mx-auto mb-3 ${theme.colors.textSecondary}`} size={40} />
              <p className="font-semibold mb-1">No contract selected</p>
              <p className={`text-sm ${theme.colors.textSecondary} mb-4`}>
                Switch to the <strong>Contracts</strong> tab and click a contract first.
              </p>
              <button onClick={() => setActiveTab('contracts')} className="px-5 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm">
                Go to Contracts
              </button>
            </div>
          ) : (
            <>
              {/* Selected contract banner */}
              <div className={`${theme.colors.surface} border border-orange-500/50 rounded-xl p-4 flex items-center justify-between`}>
                <div className="flex items-center gap-4">
                  <FileText className="text-orange-400" size={20} />
                  <div>
                    <p className="font-semibold">{selectedContract.contractId || selectedContract.id}</p>
                    <p className={`text-xs ${theme.colors.textSecondary}`}>
                      {selectedContract.vendorName} · {selectedContract.contractType} · {formatCurrency(selectedContract.netAmount || 0, selectedContract.currency)}
                    </p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded text-xs font-bold ${getRiskColor(selectedContract.riskCategory)}`}>
                  {selectedContract.riskCategory} · {selectedContract.riskScore}/100
                </span>
              </div>

              {/* Scenario cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                {SCENARIOS.map(({ key, endpoint, label, description, icon: Icon, btnClass }) => {
                  const result = scenarioResults[key];
                  const isLoading = scenarioLoading[key];

                  return (
                    <div key={key} className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-5 flex flex-col`}>
                      <div className="flex items-start gap-3 mb-3">
                        <div className="p-2 rounded-lg bg-gray-700/50">
                          <Icon size={20} className="text-gray-200" />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-sm leading-tight">{label}</p>
                          <p className={`text-xs mt-1 ${theme.colors.textSecondary}`}>{description}</p>
                        </div>
                      </div>

                      <button
                        onClick={() => runScenario(key, endpoint, selectedId)}
                        disabled={isLoading}
                        className={`mt-auto w-full py-2 rounded-lg text-white text-sm font-medium transition flex items-center justify-center gap-2 ${btnClass} disabled:opacity-50`}
                      >
                        {isLoading ? (
                          <><RefreshCw size={14} className="animate-spin" /> Running…</>
                        ) : (
                          <><Play size={14} /> Run Scenario</>
                        )}
                      </button>

                      {result && (
                        <div className={`mt-3 p-3 rounded-lg border text-xs ${
                          result.ok ? 'border-green-500/40 bg-green-500/10' : 'border-red-500/40 bg-red-500/10'
                        }`}>
                          <div className="flex items-center justify-between mb-1.5">
                            <div className="flex items-center gap-1.5">
                              {result.ok ? <CheckCircle size={12} className="text-green-400" /> : <XCircle size={12} className="text-red-400" />}
                              <span className="font-medium">{result.ok ? 'Success' : 'Error'}</span>
                            </div>
                            <span className={`flex items-center gap-1 ${theme.colors.textSecondary}`}>
                              <Clock size={10} />{result.timestamp}
                            </span>
                          </div>
                          {result.ok ? (
                            <div className="space-y-1">
                              {result.status && <p><span className={theme.colors.textSecondary}>Status:</span> <span className="font-medium">{result.status}</span></p>}
                              {result.risk_score !== undefined && <p><span className={theme.colors.textSecondary}>Risk Score:</span> <span className="font-medium">{result.risk_score}/100</span></p>}
                              {result.risk_category && <p><span className={theme.colors.textSecondary}>Category:</span> <span className="font-medium">{result.risk_category}</span></p>}
                              {result.blocked !== undefined && <p><span className={theme.colors.textSecondary}>Blocked:</span> <span className={`font-medium ${result.blocked ? 'text-red-400' : 'text-green-400'}`}>{result.blocked ? 'YES' : 'NO'}</span></p>}
                              {result.risk_delta !== undefined && <p><span className={theme.colors.textSecondary}>Risk Delta:</span> <span className={`font-medium ${result.risk_delta > 0 ? 'text-red-400' : 'text-green-400'}`}>{result.risk_delta > 0 ? '+' : ''}{result.risk_delta}</span></p>}
                              {result.override_applied !== undefined && <p><span className={theme.colors.textSecondary}>Override:</span> <span className="font-medium">{result.override_applied ? 'Applied' : 'Not Set'}</span></p>}
                              {result.suggestions_count !== undefined && <p><span className={theme.colors.textSecondary}>Suggestions:</span> <span className="font-medium">{result.suggestions_count} generated</span></p>}
                              {result.intent && <p><span className={theme.colors.textSecondary}>Intent:</span> <span className="font-medium">{result.intent}</span></p>}
                              {result.message && <p className={`italic ${theme.colors.textSecondary}`}>{result.message}</p>}
                            </div>
                          ) : (
                            <p className="text-red-400">{result.error || result.detail || 'Unknown error'}</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Run All */}
              <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-5`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">Run All 5 Scenarios</p>
                    <p className={`text-xs ${theme.colors.textSecondary} mt-0.5`}>
                      Sequentially execute all scenarios on Infor contract <strong>{selectedId}</strong>
                    </p>
                  </div>
                  <button
                    onClick={async () => {
                      for (const s of SCENARIOS) {
                        await runScenario(s.key, s.endpoint, selectedId);
                      }
                    }}
                    disabled={Object.values(scenarioLoading).some(Boolean)}
                    className="px-6 py-2.5 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50"
                  >
                    <Zap size={16} />
                    Run All
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── TAB: BATCH ─────────────────────────────────────────────── */}
      {activeTab === 'batch' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-5">
              <Layers className="text-orange-400" size={22} />
              <div>
                <h2 className="font-semibold">Batch Contract Processing</h2>
                <p className={`text-xs ${theme.colors.textSecondary}`}>Process multiple Infor ERP contracts in one go</p>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-1 ${theme.colors.textSecondary}`}>
                  Contract IDs (one per line or comma-separated)
                </label>
                <textarea
                  value={batchIds}
                  onChange={e => setBatchIds(e.target.value)}
                  rows={6}
                  placeholder={"CNT-001\nCNT-002\nCNT-003"}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className={`block text-sm font-medium mb-1 ${theme.colors.textSecondary}`}>Scenario to Run</label>
                <select
                  value={batchScenario}
                  onChange={e => setBatchScenario(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-500"
                >
                  <option value="process">Scenario 1 — Process New Contract</option>
                  <option value="block">Scenario 2 — Block High-Risk Contracts</option>
                  <option value="amendment">Scenario 3 — Amendment Re-Evaluation</option>
                  <option value="suggestions">Scenario 5 — Add Clause Suggestions</option>
                </select>
              </div>
              <button
                onClick={runBatch}
                disabled={batchLoading}
                className="w-full py-2.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {batchLoading ? <><RefreshCw size={15} className="animate-spin" /> Processing…</> : <><Play size={15} /> Run Batch</>}
              </button>
            </div>
          </div>

          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-5">
              <Activity className="text-green-400" size={22} />
              <h2 className="font-semibold">Batch Results</h2>
            </div>
            {!batchResult ? (
              <div className="text-center py-16">
                <Layers className={`mx-auto mb-3 ${theme.colors.textSecondary}`} size={40} />
                <p className={`text-sm ${theme.colors.textSecondary}`}>Results will appear here after running</p>
              </div>
            ) : batchResult.error ? (
              <div className="p-4 bg-red-500/10 border border-red-500/40 rounded-lg text-red-400 text-sm">{batchResult.error}</div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-4">
                  <p className={`text-sm ${theme.colors.textSecondary}`}>
                    Processed <strong className="text-white">{batchResult.processed}</strong> contract(s)
                  </p>
                  <div className="flex gap-2 text-xs">
                    <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded">{batchResult.results?.filter(r => !r.error).length} OK</span>
                    <span className="px-2 py-0.5 bg-red-500/20 text-red-400 rounded">{batchResult.results?.filter(r => r.error).length} Failed</span>
                  </div>
                </div>
                <div className="space-y-2 max-h-[450px] overflow-y-auto">
                  {batchResult.results?.map((r, i) => (
                    <div key={i} className={`p-3 rounded-lg border text-xs ${
                      r.error ? 'border-red-500/30 bg-red-500/10' : 'border-green-500/30 bg-green-500/10'
                    }`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">{r.contract_id || `Contract ${i + 1}`}</span>
                        {r.error ? <XCircle size={12} className="text-red-400" /> : <CheckCircle size={12} className="text-green-400" />}
                      </div>
                      {r.error ? (
                        <p className="text-red-400">{r.error}</p>
                      ) : (
                        <div className="space-y-0.5">
                          {r.status && <p><span className="text-gray-400">Status:</span> {r.status}</p>}
                          {r.risk_score !== undefined && <p><span className="text-gray-400">Risk:</span> {r.risk_score}/100 ({r.risk_category})</p>}
                          {r.blocked !== undefined && <p><span className="text-gray-400">Blocked:</span> {r.blocked ? 'YES' : 'NO'}</p>}
                          {r.suggestions_count !== undefined && <p><span className="text-gray-400">Suggestions:</span> {r.suggestions_count}</p>}
                          {r.message && <p className="text-gray-400 italic">{r.message}</p>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InforDashboard;
