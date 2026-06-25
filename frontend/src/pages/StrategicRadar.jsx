/**
 * Strategic Contract Intelligence Radar
 * =======================================
 * Market-aware contracting engine — maps real-time macro signals
 * (steel, interest rates, FX) to contract-level financial exposure.
 * Generates LLM-powered executive recommendations via Qwen2.5.
 */

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Radio, TrendingUp, TrendingDown, DollarSign,
  AlertTriangle, CheckCircle, RefreshCw, ArrowLeft,
  Activity, Zap, Globe, BarChart3
} from 'lucide-react';
import useThemeStore from '../store/themeStore';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const fmt = (v) =>
  v != null ? `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—';

const pctColor = (v) => {
  if (v == null) return 'text-slate-400';
  return v < 0 ? 'text-green-400' : v > 0 ? 'text-red-400' : 'text-slate-400';
};

const pctArrow = (v) => {
  if (v == null) return null;
  return v < 0
    ? <TrendingDown className="w-4 h-4 text-green-400 inline" />
    : <TrendingUp className="w-4 h-4 text-red-400 inline" />;
};

const SignalCard = ({ label, signal }) => {
  const pct = signal?.percent_change;
  const isLive = signal?.status === 'live';
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">{label}</p>
        <span
          className={`text-xs px-1.5 py-0.5 rounded-full border ${
            isLive
              ? 'bg-green-500/10 text-green-400 border-green-500/20'
              : 'bg-slate-500/10 text-slate-500 border-slate-500/20'
          }`}
        >
          {signal?.status || 'N/A'}
        </span>
      </div>
      <p className="text-white font-bold text-lg">
        {signal?.current_value != null
          ? Number(signal.current_value).toFixed(2)
          : '—'}
      </p>
      <p className={`text-sm font-medium mt-1 ${pctColor(pct)}`}>
        {pct != null ? (
          <>
            {pctArrow(pct)} {pct > 0 ? '+' : ''}{pct.toFixed(2)}%
          </>
        ) : '—'}
      </p>
      <p className="text-slate-500 text-xs mt-1">{signal?.signal_name || ''}</p>
    </div>
  );
};

const ExposureRow = ({ exp }) => {
  const impact = exp.estimated_impact ?? exp.annual_financing_impact ?? 0;
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
      <div>
        <p className="text-white text-sm font-medium capitalize">{exp.exposure_type}</p>
        <p className="text-slate-500 text-xs mt-0.5">{exp.message}</p>
      </div>
      <div className="text-right ml-4 flex-shrink-0">
        <p className={`font-bold text-sm ${exp.protected ? 'text-green-400' : 'text-orange-400'}`}>
          {exp.protected ? 'HEDGED' : fmt(impact)}
        </p>
        {!exp.protected && exp.percent_change != null && (
          <p className={`text-xs ${pctColor(exp.percent_change)}`}>
            {exp.percent_change > 0 ? '+' : ''}{Number(exp.percent_change).toFixed(2)}%
          </p>
        )}
      </div>
    </div>
  );
};

const AlertPanel = ({ alert }) => {
  const isOpportunity = alert.alert_type === 'strategic_opportunity';
  return (
    <div
      className={`rounded-2xl border p-5 ${
        isOpportunity
          ? 'bg-green-500/10 border-green-500/30'
          : 'bg-orange-500/10 border-orange-500/30'
      }`}
    >
      <div className="flex items-center gap-3 mb-3">
        {isOpportunity ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-orange-400" />
        )}
        <div>
          <p className={`font-semibold text-sm ${isOpportunity ? 'text-green-300' : 'text-orange-300'}`}>
            {isOpportunity ? 'Strategic Opportunity Detected' : 'Cost Risk Alert'}
          </p>
          <p className="text-slate-400 text-xs capitalize">{alert.exposure_type} exposure</p>
        </div>
        <div className="ml-auto">
          <p className={`font-bold text-lg ${isOpportunity ? 'text-green-400' : 'text-red-400'}`}>
            {fmt(alert.estimated_value)}
          </p>
          <p className="text-slate-400 text-xs text-right">estimated impact</p>
        </div>
      </div>
      <p className="text-slate-300 text-sm leading-relaxed bg-black/20 rounded-xl p-3">
        {alert.message}
      </p>
    </div>
  );
};

export default function StrategicRadar() {
  const { id: paramId } = useParams();
  const navigate = useNavigate();
  const { theme } = useThemeStore();

  const [contracts, setContracts] = useState([]);
  const [contractId, setContractId] = useState(paramId || '');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [marketSignals, setMarketSignals] = useState(null);
  const [loadingSignals, setLoadingSignals] = useState(false);

  // Load contracts
  useEffect(() => {
    const token = localStorage.getItem('token');
    axios
      .get(`${API_BASE}/api/contracts/list`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      .then((res) => {
        const list = res.data?.contracts || res.data || [];
        setContracts(list);
        if (!contractId && list.length > 0) setContractId(list[0].id);
      })
      .catch(() => {});
  }, []);

  const fetchMarketSignals = async () => {
    setLoadingSignals(true);
    try {
      const res = await axios.get(`${API_BASE}/api/market/signals/`);
      setMarketSignals(res.data.signals);
    } catch (e) {
      // silent fail — signals shown via radar result
    } finally {
      setLoadingSignals(false);
    }
  };

  const runRadar = async () => {
    if (!contractId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await axios.get(`${API_BASE}/api/strategic-radar/${contractId}/`);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.error || e.message || 'Radar scan failed');
    } finally {
      setLoading(false);
    }
  };

  const signals = result?.market_signals || {};

  return (
    <div
      className={`min-h-screen bg-gradient-to-br ${
        theme?.colors?.bgPrimary || 'from-slate-950 via-slate-900 to-slate-950'
      } p-6`}
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Radio className="w-6 h-6 text-cyan-400" />
            Strategic Intelligence Radar
          </h1>
          <p className="text-slate-400 text-sm">
            Real-time macro signal → contract exposure mapping with AI recommendations
          </p>
        </div>
        <button
          onClick={fetchMarketSignals}
          disabled={loadingSignals}
          className="ml-auto flex items-center gap-2 px-4 py-2 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/30 rounded-xl text-cyan-400 text-sm transition-colors disabled:opacity-50"
        >
          {loadingSignals
            ? <RefreshCw className="w-4 h-4 animate-spin" />
            : <Globe className="w-4 h-4" />}
          Live Signals
        </button>
      </div>

      {/* Live market signals — contract-type specific */}
      {marketSignals && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <p className="text-slate-500 text-xs uppercase tracking-wider">
              Live Market Signals — relevant to this contract
            </p>
            <span className="text-slate-600 text-xs">
              (fetched: {new Date().toLocaleTimeString()})
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {marketSignals.map((sig, i) => (
              <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-3">
                <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">{sig.signal_name}</p>
                <p className="text-white font-bold">
                  {sig.current_value != null ? Number(sig.current_value).toFixed(2) : '—'}
                </p>
                <p className={`text-xs mt-1 font-medium ${pctColor(sig.percent_change)}`}>
                  {sig.percent_change != null
                    ? `${sig.percent_change > 0 ? '+' : ''}${Number(sig.percent_change).toFixed(2)}% (1d)`
                    : '—'}
                </p>
                <p className="text-slate-600 text-xs mt-0.5">{sig.ticker || ''}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Radar Controls */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-slate-400 text-xs mb-1 block">Contract</label>
            <select
              value={contractId}
              onChange={(e) => setContractId(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500"
            >
              {contracts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.filename || c.original_filename || c.id}
                </option>
              ))}
              {contracts.length === 0 && <option value="">Enter ID below</option>}
            </select>
          </div>
          <div>
            <label className="text-slate-400 text-xs mb-1 block">Or paste Contract ID</label>
            <input
              value={contractId}
              onChange={(e) => setContractId(e.target.value)}
              placeholder="UUID..."
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500 placeholder:text-slate-600"
            />
          </div>
        </div>

        <button
          onClick={runRadar}
          disabled={loading || !contractId}
          className="mt-4 flex items-center gap-2 px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white font-semibold text-sm transition-colors"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Scanning Markets...
            </>
          ) : (
            <>
              <Radio className="w-4 h-4" />
              Run Strategic Radar
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Contract summary */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-white font-semibold text-lg">{result.contract_title}</h2>
                <div className="flex items-center gap-3 mt-1">
                  <p className="text-slate-400 text-sm">
                    Contract Value: <span className="text-white">{fmt(result.contract_value)}</span>
                  </p>
                  {result.contract_type && (() => {
                    const typeColors = {
                      'Software/IT/Service':  'bg-blue-500/20 text-blue-400 border-blue-500/30',
                      'Real Estate/Lease':    'bg-purple-500/20 text-purple-400 border-purple-500/30',
                      'Financial/Loan':       'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
                      'Logistics/Transport':  'bg-green-500/20 text-green-400 border-green-500/30',
                      'Physical/Procurement': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
                    };
                    const cls = typeColors[result.contract_type] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
                    return (
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${cls}`}>
                        {result.contract_type}
                      </span>
                    );
                  })()}
                </div>
              </div>
              <div className="text-right">
                <p className="text-slate-400 text-xs">Total Exposure</p>
                <p className="text-2xl font-bold text-orange-400">{fmt(result.total_exposure)}</p>
              </div>
            </div>

            {/* Clause profile */}
            {result.clause_exposure_profile && (
              <div className="mt-3">
                <p className="text-slate-400 text-xs mb-2 font-semibold uppercase tracking-wider">
                  Clause Profile
                </p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(result.clause_exposure_profile).map(([type, count]) =>
                    count > 0 ? (
                      <span
                        key={type}
                        className="text-xs px-2 py-0.5 rounded-full bg-white/10 border border-white/10 text-slate-300"
                      >
                        {type.replace(/_/g, ' ')}: {count}
                      </span>
                    ) : null
                  )}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  {result.has_price_adjustment_clause ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                  )}
                  <span
                    className={`text-xs ${
                      result.has_price_adjustment_clause ? 'text-green-400' : 'text-yellow-400'
                    }`}
                  >
                    {result.has_price_adjustment_clause
                      ? 'Price adjustment clause present — commodity exposure hedged'
                      : 'No price adjustment clause — full commodity exposure'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Market Signals Grid — contract-specific relevance */}
          <div>
            <p className="text-slate-400 text-xs mb-3 font-semibold uppercase tracking-wider">
              Market Signal Impact — This Contract
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(signals).map(([key, sig]) => {
                const isRelevant = sig.relevant !== false;
                return (
                  <div
                    key={key}
                    className={`rounded-xl border p-3 relative ${
                      isRelevant
                        ? 'bg-cyan-500/10 border-cyan-500/30'
                        : 'bg-white/3 border-white/5 opacity-50'
                    }`}
                  >
                    {isRelevant && (
                      <span className="absolute top-2 right-2 text-xs bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 px-1.5 py-0.5 rounded-full">
                        Active
                      </span>
                    )}
                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">
                      {sig.signal_name || key.replace(/_/g, ' ')}
                    </p>
                    <p className={`font-bold ${isRelevant ? 'text-white' : 'text-slate-600'}`}>
                      {sig.current_value != null ? Number(sig.current_value).toFixed(2) : '—'}
                    </p>
                    <p className={`text-xs mt-1 font-medium ${isRelevant ? pctColor(sig.percent_change) : 'text-slate-600'}`}>
                      {sig.percent_change != null
                        ? `${sig.percent_change > 0 ? '+' : ''}${Number(sig.percent_change).toFixed(2)}%`
                        : '—'}
                    </p>
                    <p className={`text-xs mt-1.5 ${isRelevant ? 'text-slate-400' : 'text-slate-700'}`}>
                      {sig.relevance_reason || ''}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Exposure Breakdown */}
          {result.exposures?.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-4 h-4 text-slate-400" />
                <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  Exposure Breakdown
                </p>
              </div>
              {result.exposures.map((exp, i) => (
                <ExposureRow key={i} exp={exp} />
              ))}
            </div>
          )}

          {/* Strategic Alerts / LLM Recommendations */}
          {result.alerts?.length > 0 ? (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Zap className="w-4 h-4 text-cyan-400" />
                <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  AI Executive Recommendations
                </p>
              </div>
              {result.alerts.map((alert, i) => (
                <AlertPanel key={i} alert={alert} />
              ))}
            </div>
          ) : (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-5 text-center">
              <CheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <p className="text-green-400 font-medium">No strategic alerts</p>
              <p className="text-slate-400 text-sm">
                No significant market-driven exposure detected for this contract
              </p>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="text-center py-20">
          <Radio className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">
            Select a contract and run the radar to map macro signals to contract exposure
          </p>
        </div>
      )}
    </div>
  );
}
