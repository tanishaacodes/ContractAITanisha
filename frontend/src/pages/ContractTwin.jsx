/**
 * Contract Twin Engine
 * ====================
 * Digital twin simulation — models financial chain reactions from
 * supplier failure, force majeure, and payment default scenarios.
 */

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import {
  AlertTriangle, TrendingDown, Zap, DollarSign,
  Shield, RefreshCw, ChevronRight, ArrowLeft,
  CheckCircle, XCircle, Activity
} from 'lucide-react';
import useThemeStore from '../store/themeStore';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const SCENARIO_META = {
  supplier_failure: {
    label: 'Supplier Failure',
    icon: AlertTriangle,
    color: 'text-orange-400',
    bg: 'bg-orange-500/10 border-orange-500/30',
    description: 'Primary supplier disruption — supply chain breakdown',
  },
  force_majeure: {
    label: 'Force Majeure',
    icon: Zap,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10 border-purple-500/30',
    description: 'Act of God / pandemic / war — full operational disruption',
  },
  payment_default: {
    label: 'Payment Default',
    icon: DollarSign,
    color: 'text-red-400',
    bg: 'bg-red-500/10 border-red-500/30',
    description: 'Counterparty payment default — financial recovery simulation',
  },
};

const RiskBadge = ({ level }) => {
  const colors = {
    CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/30',
    HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    MEDIUM: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    LOW: 'bg-green-500/20 text-green-400 border-green-500/30',
    UNKNOWN: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  };
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${colors[level] || colors.UNKNOWN}`}>
      {level}
    </span>
  );
};

const MetricCard = ({ label, value }) => (
  <div className="bg-white/5 border border-white/10 rounded-xl p-4">
    <p className="text-slate-400 text-xs mb-1">{label}</p>
    <p className="text-white font-bold text-base">{value}</p>
  </div>
);

const fmt = (v) =>
  v != null ? `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—';

const SimCard = ({ simKey, sim }) => {
  const meta = SCENARIO_META[simKey] || {};
  const Icon = meta.icon || Activity;
  if (!sim || sim.error) return null;

  return (
    <div className={`rounded-2xl border p-5 ${meta.bg || 'bg-white/5 border-white/10'}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-white/5">
          <Icon className={`w-5 h-5 ${meta.color || 'text-white'}`} />
        </div>
        <div>
          <h3 className="text-white font-semibold text-sm">{meta.label || simKey}</h3>
          <p className="text-slate-400 text-xs">{meta.description || ''}</p>
        </div>
        <div className="ml-auto">
          <RiskBadge level={sim.risk_level || 'UNKNOWN'} />
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <MetricCard label="Revenue Impact" value={fmt(sim.revenue_impact ?? sim.default_amount)} />
        <MetricCard
          label={sim.sla_penalty != null ? 'SLA Penalty' : 'Penalty Interest'}
          value={
            sim.sla_waiver_applicable
              ? 'WAIVED'
              : fmt(sim.sla_penalty ?? sim.penalty_interest)
          }
        />
        <MetricCard label="Total Exposure" value={fmt(sim.total_exposure)} />
        <MetricCard
          label={sim.insurance_claim != null ? 'Insurance' : 'Recovery Probability'}
          value={
            sim.insurance_claim != null
              ? sim.insurance_claim ? '✓ Triggered' : '✗ Below threshold'
              : sim.recovery_probability != null
              ? `${(sim.recovery_probability * 100).toFixed(0)}%`
              : '—'
          }
        />
      </div>

      {sim.recovery_timeline_days != null && (
        <p className="text-slate-400 text-xs mb-3">
          Recovery timeline:{' '}
          <span className="text-white font-medium">{sim.recovery_timeline_days} days</span>
        </p>
      )}

      {sim.has_force_majeure_clause != null && (
        <div className="flex items-center gap-2 text-xs mb-3">
          {sim.has_force_majeure_clause ? (
            <CheckCircle className="w-4 h-4 text-green-400" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
          <span className={sim.has_force_majeure_clause ? 'text-green-400' : 'text-red-400'}>
            Force Majeure clause{' '}
            {sim.has_force_majeure_clause ? 'detected' : 'NOT found in contract'}
          </span>
        </div>
      )}

      {sim.recommendations?.length > 0 && (
        <div className="mt-3">
          <p className="text-slate-400 text-xs mb-2 font-semibold uppercase tracking-wider">
            Recommendations
          </p>
          <ul className="space-y-1.5">
            {sim.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                <ChevronRight className="w-3 h-3 mt-0.5 text-blue-400 flex-shrink-0" />
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default function ContractTwin() {
  const { id: paramId } = useParams();
  const navigate = useNavigate();
  const { theme } = useThemeStore();

  const [contracts, setContracts] = useState([]);
  const [contractId, setContractId] = useState(paramId || '');
  const [scenario, setScenario] = useState('all');
  const [manualValue, setManualValue] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  const runSimulation = async () => {
    if (!contractId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const params = new URLSearchParams();
      if (scenario !== 'all') params.set('scenario', scenario);
      if (manualValue) params.set('override_value', manualValue.replace(/[,₹$€\s]/g, ''));
      const qs = params.toString() ? `?${params.toString()}` : '';
      const res = await axios.get(`${API_BASE}/api/contract-twin/${contractId}/${qs}`);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.error || e.message || 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

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
            <TrendingDown className="w-6 h-6 text-blue-400" />
            Contract Digital Twin
          </h1>
          <p className="text-slate-400 text-sm">
            Simulate financial chain reactions from real-world disruption scenarios
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-5 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-slate-400 text-xs mb-1 block">Contract</label>
            <select
              value={contractId}
              onChange={(e) => setContractId(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 placeholder:text-slate-600"
            />
          </div>

          <div>
            <label className="text-slate-400 text-xs mb-1 block">
              Contract Value Override{' '}
              <span className="text-slate-600">(if showing ₹0)</span>
            </label>
            <input
              value={manualValue}
              onChange={(e) => setManualValue(e.target.value)}
              placeholder="e.g. 85000000"
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 placeholder:text-slate-600"
            />
          </div>

          <div>
            <label className="text-slate-400 text-xs mb-1 block">Scenario</label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Scenarios</option>
              <option value="supplier_failure">Supplier Failure</option>
              <option value="force_majeure">Force Majeure</option>
              <option value="payment_default">Payment Default</option>
            </select>
          </div>
        </div>

        <button
          onClick={runSimulation}
          disabled={loading || !contractId}
          className="mt-4 flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white font-semibold text-sm transition-colors"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Running Simulation...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              Run Twin Simulation
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
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-white font-semibold">
                {result.contract_title || 'Simulation Results'}
              </h2>
              <p className="text-slate-400 text-xs">
                Contract Value:{' '}
                {fmt(
                  result.contract_value ??
                    result.simulations?.supplier_failure?.contract_value
                )}
              </p>
            </div>
            <Shield className="w-5 h-5 text-blue-400" />
          </div>

          {/* All-scenarios mode */}
          {result.simulations &&
            Object.entries(result.simulations).map(([key, sim]) => (
              <SimCard key={key} simKey={key} sim={sim} />
            ))}

          {/* Single scenario mode */}
          {result.scenario && <SimCard simKey={result.scenario} sim={result} />}
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="text-center py-20">
          <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">
            Select a contract and run a simulation to see the digital twin analysis
          </p>
        </div>
      )}
    </div>
  );
}
