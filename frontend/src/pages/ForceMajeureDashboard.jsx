/**
 * Force Majeure Intelligence Engine — Dashboard
 * All-in-one: Risk Predictor, Clause Auditor, War Risk, Scenario Sim,
 * Risk Graph, Live Terminal, Counterfactual, Portfolio Sim,
 * Knowledge Graph, Digital Twin, Multi-Agent Negotiation, Supply Chain
 */
import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import {
  Shield, AlertTriangle, Zap, Activity, BarChart2, Info,
  CheckCircle, XCircle, RefreshCw, Download, Globe, Sword,
  TrendingUp, FileText, Eye, Target, Radio, GitBranch, Cpu,
  Users, Truck, Play, Clock, Bell, Layers, Filter, ChevronRight,
  Sliders, Lock, Maximize2, Minimize2, Edit3,
} from 'lucide-react';
import ReactFlow, { Background, Controls, MiniMap, Handle, Position, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, AreaChart, Area,
  ReferenceLine, ReferenceArea, ComposedChart,
} from 'recharts';
import {
  predictFMRisk,
  auditFMClause,
  autoCorrectFMClause,
  analyzeWarRisk,
  simulateFMScenario,
  getFMBayesianGraph,
  getFMPortfolioSummary,
  getLiveEvents,
  getWarIntelligence,
  getEventStream,
  getRiskMapData,
  getPortfolioAlerts,
  FM_SCENARIO_TEMPLATES,
  FM_EVENT_CATEGORIES,
  runCounterfactual,
  simulatePortfolio,
  getFMKnowledgeGraph,
  runDigitalTwin,
  runMultiAgentNegotiate,
  getSupplyChainMap,
  getDynamicPriors,
  getRiskCascade,
  runClauseOptimizer,
  getTemporalForecast,
  getRiskFormula,
  getAlertEngine,
  getBalticDry,
  bulkAutoCorrect,
} from '../services/forceMajeureService';
import { useNavigate, useLocation } from 'react-router-dom';

// ─── Colour helpers ───────────────────────────────────────────────────────────
const riskColor = (score) =>
  score > 0.6 ? '#F16667' : score > 0.35 ? '#F79767' : '#68BC00';
const riskLabel = (score) =>
  score > 0.6 ? 'HIGH' : score > 0.35 ? 'MEDIUM' : 'LOW';

const SEVERITY_COLORS = { low: '#68BC00', medium: '#F79767', high: '#F16667', critical: '#9d1b1b' };
const PIE_COLORS = ['#4C8EDA', '#F16667', '#F79767', '#9063CD', '#68BC00', '#06B6D4'];

// ─── Tab config ───────────────────────────────────────────────────────────────
const TABS = [
  { id: 'predict',        label: 'Risk Predictor',    icon: Shield },
  { id: 'audit',          label: 'Clause Auditor',    icon: FileText },
  { id: 'war',            label: 'War Risk',          icon: Sword },
  { id: 'scenario',       label: 'Scenario Sim',      icon: Activity },
  { id: 'graph',          label: 'Risk Graph',        icon: Eye },
  { id: 'terminal',       label: 'Live Terminal',     icon: Radio },
  { id: 'counterfactual', label: 'Counterfactual',    icon: GitBranch },
  { id: 'portfolio_sim',  label: 'Portfolio Sim',     icon: BarChart2 },
  { id: 'kg',             label: 'Knowledge Graph',   icon: Globe },
  { id: 'twin',           label: 'Digital Twin',      icon: Cpu },
  { id: 'negotiation',    label: 'Multi-Agent Nego',  icon: Users },
  { id: 'supply',         label: 'Supply Chain',      icon: Truck },
  // ── Phase-2 New Tabs ──────────────────────────────────────────────
  { id: 'dynamic_priors', label: 'Dynamic Priors',    icon: Sliders },
  { id: 'risk_cascade',   label: 'Risk Cascade',      icon: Layers },
  { id: 'clause_opt',     label: 'Clause Optimizer',  icon: CheckCircle },
  { id: 'temporal',       label: '12M Forecast',      icon: TrendingUp },
  { id: 'formula',        label: 'Risk Formula',      icon: Target },
  { id: 'howit',          label: 'How It Works',      icon: Info },
];

// ─── Reusable metric card ─────────────────────────────────────────────────────
const MetricCard = ({ label, value, sub, color = '#4C8EDA', icon: Icon }) => (
  <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex flex-col gap-1">
    <div className="flex items-center gap-2 text-gray-400 text-xs">
      {Icon && <Icon size={13} />}
      {label}
    </div>
    <div className="text-2xl font-bold" style={{ color }}>{value}</div>
    {sub && <div className="text-gray-500 text-xs">{sub}</div>}
  </div>
);

// ─── Score gauge ─────────────────────────────────────────────────────────────
const ScoreGauge = ({ score, label }) => {
  const color = riskColor(score);
  const pct = Math.round(score * 100);
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="w-28 h-28 rounded-full flex items-center justify-center border-4"
        style={{ borderColor: color, boxShadow: `0 0 20px ${color}55` }}
      >
        <div className="text-center">
          <div className="text-3xl font-bold" style={{ color }}>{pct}%</div>
          <div className="text-xs text-gray-400">{riskLabel(score)}</div>
        </div>
      </div>
      <div className="text-gray-400 text-xs">{label}</div>
    </div>
  );
};

// ─── Event coverage badge ─────────────────────────────────────────────────────
const EventBadge = ({ event, covered }) => (
  <span
    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
      covered ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
    }`}
  >
    {covered ? <CheckCircle size={10} /> : <XCircle size={10} />}
    {event.replace(/_/g, ' ')}
  </span>
);

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 1 — RISK PREDICTOR  (inputs live here; result flows to all other tabs)
// ═══════════════════════════════════════════════════════════════════════════════
// NOTE: ContractPanel removed — inputs are now only on the Predict tab (Dispute Predictor pattern)
const _UNUSED_ContractPanel = ({ ctx, setCtx, onAnalyze, analyzed }) => {
  const [open, setOpen] = useState(true);

  return (
    <div className="bg-gray-850 border-b border-gray-700" style={{ background: '#141820' }}>
      {/* Bar — always visible */}
      <div
        className="flex items-center gap-3 px-6 py-2.5 cursor-pointer select-none"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-center gap-2 flex-1">
          <FileText size={14} className="text-blue-400" />
          <span className="text-sm font-semibold text-white">Contract Context</span>
          {analyzed && (
            <span className="flex items-center gap-1 px-2 py-0.5 bg-green-900 text-green-300 text-xs rounded-full font-medium">
              <CheckCircle size={10} /> Loaded — all tabs use this contract
            </span>
          )}
          {ctx.contract_title && (
            <span className="text-gray-400 text-xs truncate max-w-xs">· {ctx.contract_title}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {analyzed && !open && (
            <span className="text-xs text-gray-500">
              {ctx.contract_value ? `$${Number(ctx.contract_value).toLocaleString()}` : ''}{ctx.jurisdiction ? ` · ${ctx.jurisdiction}` : ''}
            </span>
          )}
          <ChevronRight size={14} className={`text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`} />
        </div>
      </div>

      {/* Expanded form */}
      {open && (
        <div className="px-6 pb-4 space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <input
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 col-span-1"
              placeholder="Contract Title"
              value={ctx.contract_title}
              onChange={e => setCtx(c => ({ ...c, contract_title: e.target.value }))}
            />
            <input
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
              placeholder="Contract Value (USD)"
              value={ctx.contract_value}
              onChange={e => setCtx(c => ({ ...c, contract_value: e.target.value }))}
            />
            <input
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
              placeholder="Jurisdiction (e.g., India, UAE)"
              value={ctx.jurisdiction}
              onChange={e => setCtx(c => ({ ...c, jurisdiction: e.target.value }))}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
              placeholder="Project Location (e.g., Middle East, Ukraine)"
              value={ctx.project_location}
              onChange={e => setCtx(c => ({ ...c, project_location: e.target.value }))}
            />
            <input
              className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
              placeholder="Supplier Locations (comma-separated)"
              value={ctx.supplier_locations}
              onChange={e => setCtx(c => ({ ...c, supplier_locations: e.target.value }))}
            />
          </div>
          <textarea
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 font-mono resize-none"
            rows={5}
            placeholder="Paste full contract text here — all tabs will use this automatically…"
            value={ctx.contract_text}
            onChange={e => setCtx(c => ({ ...c, contract_text: e.target.value }))}
          />
          <div className="flex items-center gap-3">
            <button
              onClick={onAnalyze}
              disabled={!ctx.contract_text.trim()}
              className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-semibold rounded-lg transition"
            >
              <Zap size={14} /> Load Contract into All Tabs
            </button>
            {analyzed && (
              <span className="text-green-400 text-xs flex items-center gap-1">
                <CheckCircle size={12} /> Contract loaded — switch to any tab to run analysis
              </span>
            )}
            {ctx.contract_text.trim() && (
              <span className="text-gray-500 text-xs ml-auto">
                {ctx.contract_text.trim().split(/\s+/).length} words
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 1 — RISK PREDICTOR  (all inputs live here)
// ═══════════════════════════════════════════════════════════════════════════════
const RiskPredictorTab = ({ contract, setContract, onPredict, loading, result, error }) => {
  const outcomeData = result ? [
    { name: 'Force Majeure Invocation', value: Math.round((result.fm_invocation_probability || 0) * 100) },
    { name: 'Project Delay', value: Math.round((result.project_delay_probability || 0) * 100) },
    { name: 'Cost Overrun', value: Math.round((result.cost_overrun_probability || 0) * 100) },
    { name: 'Suspension', value: Math.round((result.contract_suspension_probability || 0) * 100) },
    { name: 'Termination', value: Math.round((result.contract_termination_probability || 0) * 100) },
  ] : [];

  const set = (k) => (e) => setContract(c => ({ ...c, [k]: e.target.value }));

  return (
    <div className="space-y-6">
      {/* Input form */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 space-y-4">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <Shield size={16} className="text-blue-400" /> Contract Analysis
        </h3>
        <div className="grid grid-cols-3 gap-3">
          <input className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 col-span-2"
            placeholder="Contract Title (optional)" value={contract.contract_title} onChange={set('contract_title')} />
          <input className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
            placeholder="Contract Value (USD)" value={contract.contract_value} onChange={set('contract_value')} />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <input className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
            placeholder="Jurisdiction (e.g., India, UAE)" value={contract.jurisdiction} onChange={set('jurisdiction')} />
          <input className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
            placeholder="Project Location" value={contract.project_location} onChange={set('project_location')} />
          <input className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
            placeholder="Supplier Locations (comma-separated)" value={contract.supplier_locations} onChange={set('supplier_locations')} />
        </div>
        <textarea className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500 font-mono resize-none"
          rows={7} placeholder="Paste contract text here — all tabs will auto-populate after analysis…"
          value={contract.contract_text} onChange={set('contract_text')} />
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <button onClick={onPredict} disabled={loading || !contract.contract_text.trim()}
          className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-bold rounded-lg transition">
          {loading ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
          {loading ? 'Analyzing…' : 'RUN FORCE MAJEURE RISK ANALYSIS'}
        </button>
        {!result && !loading && <p className="text-center text-gray-500 text-xs">All tabs unlock after analysis</p>}
      </div>

      {result && (() => {
        const fmScore = result.fm_risk_score || 0;
        const fmInvoc = result.fm_invocation_probability || 0;
        const projDelay = result.project_delay_probability || 0;
        const clauseStr = result.clause_strength_score || 0;
        const expLoss = result.expected_loss_usd || 0;
        const p95 = result.p95_loss_usd || 0;
        const p99 = result.p99_loss_usd || 0;
        const covered = (result.covered_events || []).length;
        const contractVal = parseFloat(contract.contract_value) || 1;
        const lossRatio = expLoss / contractVal;
        const drivers = result.top_risk_drivers || [];
        const overallRisk = fmScore > 0.8 ? 'CRITICAL' : fmScore > 0.6 ? 'HIGH' : fmScore > 0.4 ? 'MEDIUM' : 'LOW';
        const riskTxt = { CRITICAL: 'text-red-400', HIGH: 'text-orange-400', MEDIUM: 'text-yellow-400', LOW: 'text-green-400' };
        const riskBorder = { CRITICAL: 'border-red-600', HIGH: 'border-orange-600', MEDIUM: 'border-yellow-600', LOW: 'border-green-600' };
        const fmt = v => v >= 1e9 ? `$${(v/1e9).toFixed(2)}B` : v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : `$${(v/1000).toFixed(0)}K`;

        const outcomeData = [
          { name: 'Force Majeure Invocation', value: Math.round(fmInvoc * 100), desc: 'Probability Force Majeure clause gets triggered' },
          { name: 'Project Delay', value: Math.round(projDelay * 100), desc: 'Probability of schedule slippage' },
          { name: 'Cost Overrun', value: Math.round((result.cost_overrun_probability || 0) * 100), desc: 'Probability of budget exceedance' },
          { name: 'Suspension', value: Math.round((result.contract_suspension_probability || 0) * 100), desc: 'Work stoppage probability' },
          { name: 'Termination', value: Math.round((result.contract_termination_probability || 0) * 100), desc: 'Contract cancellation risk' },
          { name: 'Insurance Claim', value: Math.round((result.insurance_claim_probability || fmInvoc * 0.88) * 100), desc: 'Probability of insurance payout' },
        ];

        const radarData = outcomeData.map(d => ({ subject: d.name, value: d.value, fullMark: 100 }));

        const driverData = drivers.slice(0, 8).map(d => ({
          name: d.node?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          prob: Math.round(d.probability * 100),
          fill: riskColor(d.probability),
        }));

        const lossCurveData = [
          { pct: '50th', loss: Math.round(expLoss * 0.7 / 1e6) },
          { pct: '75th', loss: Math.round(expLoss * 0.9 / 1e6) },
          { pct: 'Mean', loss: Math.round(expLoss / 1e6) },
          { pct: '90th', loss: Math.round(p95 * 0.88 / 1e6) },
          { pct: 'Stress Test', loss: Math.round(p95 / 1e6) },
          { pct: 'Catastrophic', loss: Math.round(p99 / 1e6) },
        ];

        const coverageData = [
          { name: 'Covered', value: covered, fill: '#68BC00' },
          { name: 'Missing', value: 14 - covered, fill: '#374151' },
        ];

        return (
          <>
            {/* ── HERO BANNER ── */}
            <div className={`relative overflow-hidden bg-gray-900 border-2 ${riskBorder[overallRisk]} rounded-2xl p-5`}
              style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
              <div className="absolute inset-0 opacity-5" style={{ backgroundImage: 'radial-gradient(circle at 80% 50%, #F16667 0%, transparent 60%)' }} />
              <div className="relative flex items-start justify-between flex-wrap gap-4">
                <div>
                  <div className="text-gray-500 text-xs uppercase tracking-widest mb-1">Force Majeure Intelligence Engine</div>
                  <div className={`text-5xl font-black tracking-tight ${riskTxt[overallRisk]}`}>{overallRisk} RISK</div>
                  <div className="text-gray-300 font-semibold mt-1">{contract.contract_title || 'Contract Analysis'}</div>
                  <div className="text-gray-500 text-xs mt-1">Jurisdiction: {contract.jurisdiction || '—'} · Value: {fmt(contractVal)} · 35-Node Bayesian Network</div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Force Majeure Invocation Probability', val: `${Math.round(fmInvoc*100)}%`, sub: 'Chance Force Majeure clause gets triggered', color: riskTxt[overallRisk] },
                    { label: 'Clause Protection Score', val: `${Math.round(clauseStr*100)}%`, sub: clauseStr > 0.6 ? 'Strong Force Majeure clause' : clauseStr > 0.3 ? 'Weak Force Majeure clause' : 'Missing/inadequate clause', color: clauseStr > 0.6 ? 'text-green-400' : clauseStr > 0.3 ? 'text-yellow-400' : 'text-red-400' },
                    { label: 'Expected Financial Loss', val: fmt(expLoss), sub: `${lossRatio.toFixed(1)}× contract value`, color: 'text-orange-400' },
                    { label: 'Force Majeure Event Coverage', val: `${covered}/14`, sub: `${14-covered} categories unprotected`, color: covered >= 12 ? 'text-green-400' : covered >= 8 ? 'text-yellow-400' : 'text-red-400' },
                  ].map((k, i) => (
                    <div key={i} className="bg-gray-800/60 border border-gray-700 rounded-xl p-3 min-w-[180px]">
                      <div className="text-gray-500 text-xs mb-1">{k.label}</div>
                      <div className={`text-xl font-bold ${k.color}`}>{k.val}</div>
                      <div className="text-gray-600 text-xs mt-0.5">{k.sub}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* ── ROW 1: Loss Curve + Radar ── */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="text-white text-sm font-semibold">Monte Carlo Loss Distribution</h4>
                  <span className="text-gray-500 text-xs">5,000 iterations</span>
                </div>
                <p className="text-gray-500 text-xs mb-3">Financial exposure at each risk level — worst-case scenario planning</p>
                <ResponsiveContainer width="100%" height={190}>
                  <AreaChart data={lossCurveData}>
                    <defs>
                      <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F16667" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#F16667" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="pct" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#9CA3AF', fontSize: 10 }} tickFormatter={v => `$${v}M`} />
                    <Tooltip formatter={v => [`$${v}M`, 'Loss']} contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                    <Area type="monotone" dataKey="loss" stroke="#F16667" strokeWidth={2} fill="url(#lossGrad)" dot={{ fill: '#F16667', r: 4 }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="text-white text-sm font-semibold">Contract Risk Radar</h4>
                  <span className="text-gray-500 text-xs">6 outcome dimensions</span>
                </div>
                <p className="text-gray-500 text-xs mb-3">Spider chart showing probability of each adverse contract outcome — larger area = higher risk</p>
                <ResponsiveContainer width="100%" height={190}>
                  <RadarChart data={radarData} cx="50%" cy="50%" outerRadius={75}>
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9CA3AF', fontSize: 9 }} />
                    <Radar name="Probability" dataKey="value" stroke="#F16667" fill="#F16667" fillOpacity={0.25} strokeWidth={2} />
                    <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* ── ROW 2: Outcome Probabilities detailed ── */}
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
              <div className="flex items-start justify-between mb-1">
                <h4 className="text-white text-sm font-semibold">Contract Outcome Probabilities — What Could Go Wrong?</h4>
                <span className="text-gray-500 text-xs">Bayesian forward propagation</span>
              </div>
              <p className="text-gray-500 text-xs mb-4">Each bar shows how likely that outcome is for THIS contract given its clauses, jurisdiction, and supply chain</p>
              <div className="grid grid-cols-6 gap-3">
                {outcomeData.map((d, i) => (
                  <div key={i} className="flex flex-col items-center">
                    <div className="w-full bg-gray-700 rounded-lg overflow-hidden h-32 flex items-end relative">
                      <div className="w-full rounded-t-lg transition-all"
                        style={{ height: `${d.value}%`, background: d.value > 75 ? 'linear-gradient(to top, #991b1b, #F16667)' : d.value > 50 ? 'linear-gradient(to top, #92400e, #F79767)' : 'linear-gradient(to top, #1e3a5f, #4C8EDA)' }} />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-white font-black text-lg">{d.value}%</span>
                      </div>
                    </div>
                    <div className="text-center mt-2">
                      <div className="text-gray-300 text-xs font-medium">{d.name}</div>
                      <div className="text-gray-600 text-xs mt-0.5 leading-tight">{d.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── ROW 3: Top Risk Drivers + Coverage ── */}
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="text-white text-sm font-semibold">Top Risk Drivers — Bayesian Probability</h4>
                  <span className="text-gray-500 text-xs">From 35-node causal network</span>
                </div>
                <p className="text-gray-500 text-xs mb-3">Which specific events are most likely to trigger Force Majeure for this contract, based on clause text + jurisdiction + supply chain analysis</p>
                <div className="space-y-2.5">
                  {driverData.map((d, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-gray-600 text-xs w-5 shrink-0 text-right">{i+1}</span>
                      <span className="text-gray-300 text-xs w-36 shrink-0">{d.name}</span>
                      <div className="flex-1 bg-gray-900 rounded-full h-4 overflow-hidden">
                        <div className="h-4 rounded-full flex items-center justify-end pr-2 transition-all"
                          style={{ width: `${d.prob}%`, background: `linear-gradient(90deg, ${d.fill}88, ${d.fill})` }}>
                          <span className="text-white text-xs font-bold">{d.prob}%</span>
                        </div>
                      </div>
                      <span className="text-xs w-10 text-right font-bold shrink-0" style={{ color: d.fill }}>
                        {d.prob > 75 ? '🔴' : d.prob > 50 ? '🟠' : '🟡'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="mb-1">
                  <h4 className="text-white text-sm font-semibold">Force Majeure Clause Coverage</h4>
                  <p className="text-gray-500 text-xs mt-0.5">How many of 14 standard Force Majeure event categories your clause covers</p>
                </div>
                <div className="flex flex-col items-center mt-3">
                  <ResponsiveContainer width="100%" height={130}>
                    <PieChart>
                      <Pie data={coverageData} cx="50%" cy="50%" innerRadius={38} outerRadius={58} dataKey="value" paddingAngle={2} startAngle={90} endAngle={-270}>
                        {coverageData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className={`text-3xl font-black mt-1 ${covered >= 12 ? 'text-green-400' : covered >= 8 ? 'text-yellow-400' : 'text-red-400'}`}>{covered}/14</div>
                  <div className="text-gray-500 text-xs">categories covered</div>
                  <div className="w-full mt-3 space-y-1">
                    <div className="flex justify-between text-xs"><span className="text-green-400">✓ Protected</span><span className="text-green-400 font-bold">{covered}</span></div>
                    <div className="flex justify-between text-xs"><span className="text-red-400">✗ Unprotected</span><span className="text-red-400 font-bold">{14-covered}</span></div>
                    <div className="flex justify-between text-xs"><span className="text-gray-500">Coverage %</span><span className="text-white font-bold">{Math.round(covered/14*100)}%</span></div>
                  </div>
                </div>
              </div>
            </div>

            {/* ── ROW 4: Event badges ── */}
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
              <h4 className="text-white text-sm font-semibold mb-1">Force Majeure Event Coverage — 14 Standard Categories</h4>
              <p className="text-gray-500 text-xs mb-3">Green = your contract's Force Majeure clause explicitly covers this. Red = NOT covered — you bear full risk for these events.</p>
              <div className="flex flex-wrap gap-2">
                {FM_EVENT_CATEGORIES.map(ev => (
                  <EventBadge key={ev} event={ev} covered={(result.covered_events || []).includes(ev)} />
                ))}
              </div>
            </div>

            {/* ── ROW 5: AI + Mitigation ── */}
            <div className="grid grid-cols-2 gap-4">
              {result.explanation && (
                <div className="bg-gray-900 border border-blue-800 rounded-xl p-4" style={{ background: 'linear-gradient(135deg, #0f172a, #1e3a5f22)' }}>
                  <h4 className="text-blue-400 text-sm font-semibold mb-2 flex items-center gap-2">
                    <Zap size={13} /> AI Risk Assessment
                  </h4>
                  <p className="text-gray-500 text-xs mb-2">Generated by AI analysis of your specific contract text, jurisdiction, and supply chain</p>
                  <p className="text-gray-200 text-sm leading-relaxed">{result.explanation}</p>
                </div>
              )}
              {(result.mitigation_suggestions || []).length > 0 && (
                <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                  <h4 className="text-white text-sm font-semibold mb-1">Mitigation Recommendations</h4>
                  <p className="text-gray-500 text-xs mb-3">Priority actions to reduce Force Majeure risk exposure for this contract</p>
                  <div className="space-y-2.5">
                    {result.mitigation_suggestions.slice(0, 6).map((m, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className={`shrink-0 mt-0.5 px-2 py-0.5 rounded-full text-xs font-bold ${m.priority === 'high' ? 'bg-red-900/60 text-red-300 border border-red-700' : 'bg-yellow-900/60 text-yellow-300 border border-yellow-700'}`}>
                          {m.priority?.toUpperCase()}
                        </span>
                        <span className="text-gray-300 text-xs leading-relaxed">{m.suggestion}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        );
      })()}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 2 — CLAUSE AUDITOR
// ═══════════════════════════════════════════════════════════════════════════════
const ClauseAuditorTab = ({ contract }) => {
  const ctx = contract;
  const [loading, setLoading] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [correctionResult, setCorrectionResult] = useState(null);
  const [correctLoading, setCorrectLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [activeView, setActiveView] = useState('overview'); // overview | coverage | benchmark | rewrite

  const handleAudit = async () => {
    if (!ctx.contract_text.trim()) { setError('Paste contract text in the Contract Context panel above first'); return; }
    setLoading(true); setError(''); setAuditResult(null); setCorrectionResult(null); setActiveView('overview');
    try {
      const data = await auditFMClause({ contract_text: ctx.contract_text, contract_id: ctx.contract_title });
      setAuditResult(data);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally { setLoading(false); }
  };

  const handleAutoCorrect = async () => {
    if (!ctx.contract_text.trim()) return;
    setCorrectLoading(true);
    try {
      const data = await autoCorrectFMClause({ contract_text: ctx.contract_text, contract_id: ctx.contract_title });
      setCorrectionResult(data);
      setActiveView('rewrite');
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally { setCorrectLoading(false); }
  };

  const handleCopy = () => {
    if (correctionResult?.corrected_clause) {
      navigator.clipboard.writeText(correctionResult.corrected_clause);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const STATUS_META = {
    strong:  { color: '#68BC00', bg: 'rgba(104,188,0,0.1)',   border: '#68BC00', icon: '✅', label: 'STRONG CLAUSE' },
    weak:    { color: '#F79767', bg: 'rgba(247,151,103,0.1)', border: '#F79767', icon: '⚠️', label: 'WEAK CLAUSE' },
    missing: { color: '#F16667', bg: 'rgba(241,102,103,0.1)', border: '#F16667', icon: '❌', label: 'MISSING CLAUSE' },
  };

  const BENCHMARKS = auditResult ? [
    { label: 'This Contract', score: auditResult.strength_score,       color: STATUS_META[auditResult.status]?.color || '#aaa', isThis: true },
    { label: 'FIDIC Standard', score: auditResult.benchmark_fidic_score, color: '#4C8EDA' },
    { label: 'NEC Standard',   score: auditResult.benchmark_nec_score,   color: '#9063CD' },
    { label: 'ICC Standard',   score: auditResult.benchmark_icc_score,   color: '#F79767' },
  ] : [];

  const covered   = auditResult?.covered_events || [];
  const uncovered = FM_EVENT_CATEGORIES.filter(e => !covered.includes(e));
  const score     = Math.round((auditResult?.strength_score || 0) * 100);
  const meta      = STATUS_META[auditResult?.status] || STATUS_META.missing;

  // Radar chart data: map FM_EVENT_CATEGORIES to 6 groups for visual
  const RADAR_GROUPS = [
    { subject: 'War/Conflict',    events: ['war','terrorism','cyber warfare','government lockdown'] },
    { subject: 'Natural Disaster',events: ['earthquake','flood','hurricane','wildfire','volcanic eruption'] },
    { subject: 'Trade/Sanctions', events: ['trade sanctions','embargo','satellite disruption'] },
    { subject: 'Supply Chain',    events: ['supply chain disruption','port closure','airspace closure'] },
    { subject: 'Health',          events: ['pandemic','epidemic'] },
    { subject: 'Energy',          events: ['energy shortages','commodity shock'] },
  ];
  const radarData = RADAR_GROUPS.map(g => ({
    subject: g.subject,
    covered: g.events.filter(e => covered.map(c=>c.toLowerCase()).includes(e.toLowerCase())).length,
    total: g.events.length,
    pct: Math.round(g.events.filter(e => covered.map(c=>c.toLowerCase()).includes(e.toLowerCase())).length / g.events.length * 100),
  }));

  const VIEWS = [
    { id: 'overview',  label: 'Overview',  icon: Eye },
    { id: 'coverage',  label: 'Coverage',  icon: Shield },
    { id: 'benchmark', label: 'Benchmark', icon: BarChart2 },
    ...(correctionResult ? [{ id: 'rewrite', label: 'AI Rewrite', icon: Zap }] : []),
  ];

  return (
    <div className="space-y-4">
      {/* ── Header bar ── */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center gap-4">
        <div className="flex-1">
          <h3 className="text-white font-bold text-base flex items-center gap-2">
            <FileText size={16} className="text-green-400" /> Force Majeure Clause Auditor
          </h3>
          <p className="text-gray-400 text-xs mt-0.5">
            {ctx.contract_title || 'No contract loaded'} — scans for 14 Force Majeure event categories, benchmarks vs FIDIC/NEC/ICC
          </p>
          {!ctx.contract_text.trim() && (
            <p className="text-yellow-500 text-xs mt-1">⚠ Paste contract text in the Contract Context panel above first</p>
          )}
        </div>
        {error && <div className="text-red-400 text-xs max-w-xs">{error}</div>}
        <div className="flex gap-2 shrink-0">
          <button onClick={handleAudit} disabled={loading || !ctx.contract_text.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition">
            {loading ? <RefreshCw size={13} className="animate-spin" /> : <FileText size={13} />}
            {loading ? 'Auditing…' : 'Audit Force Majeure Clause'}
          </button>
          {auditResult && (
            <button onClick={handleAutoCorrect} disabled={correctLoading}
              className="flex items-center gap-2 px-4 py-2 bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition">
              {correctLoading ? <RefreshCw size={13} className="animate-spin" /> : <Zap size={13} />}
              {correctLoading ? 'Rewriting…' : 'AI Auto-Correct'}
            </button>
          )}
        </div>
      </div>

      {auditResult && (
        <>
          {/* ── KPI row ── */}
          <div className="grid grid-cols-5 gap-3">
            {/* Big status card */}
            <div className="col-span-2 rounded-xl p-5 flex flex-col justify-between"
              style={{ background: meta.bg, border: `2px solid ${meta.border}66` }}>
              <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">Clause Status</div>
              <div className="text-3xl font-black" style={{ color: meta.color }}>{meta.icon} {meta.label}</div>
              <div className="mt-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Strength Score</span>
                  <span className="font-bold" style={{ color: meta.color }}>{score}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2.5">
                  <div className="h-2.5 rounded-full transition-all" style={{ width: `${score}%`, background: `linear-gradient(90deg, ${meta.color}99, ${meta.color})` }} />
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div className="bg-black/20 rounded-lg p-2 text-center">
                  <div className="text-2xl font-black text-green-400">{covered.length}</div>
                  <div className="text-gray-400">Covered</div>
                </div>
                <div className="bg-black/20 rounded-lg p-2 text-center">
                  <div className="text-2xl font-black text-red-400">{uncovered.length}</div>
                  <div className="text-gray-400">Missing</div>
                </div>
              </div>
            </div>

            {/* Benchmark mini cards */}
            <div className="col-span-3 grid grid-cols-3 gap-3">
              {BENCHMARKS.slice(1).map((b) => {
                const gap = score - Math.round((b.score || 0) * 100);
                return (
                  <div key={b.label} className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-2">
                    <div className="text-gray-400 text-xs font-semibold">{b.label}</div>
                    <div className="text-2xl font-black" style={{ color: b.color }}>
                      {Math.round((b.score || 0) * 100)}%
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full" style={{ width: `${Math.round((b.score||0)*100)}%`, background: b.color }} />
                    </div>
                    <div className={`text-xs font-bold ${gap >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {gap >= 0 ? `▼ ${gap}pp below` : `▲ ${Math.abs(gap)}pp above`}
                    </div>
                  </div>
                );
              })}
              {/* Score gauge donut-style */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col items-center justify-center">
                <div className="relative" style={{ width: 80, height: 80 }}>
                  <svg viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="#374151" strokeWidth="3" />
                    <circle cx="18" cy="18" r="15.9" fill="none" stroke={meta.color} strokeWidth="3"
                      strokeDasharray={`${score} ${100 - score}`} strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-lg font-black" style={{ color: meta.color }}>{score}%</span>
                  </div>
                </div>
                <div className="text-gray-400 text-xs mt-1 text-center">Force Majeure Score</div>
              </div>
            </div>
          </div>

          {/* ── Sub-nav tabs ── */}
          <div className="flex gap-1 bg-gray-800/60 rounded-lg p-1 border border-gray-700 w-fit">
            {VIEWS.map(v => (
              <button key={v.id} onClick={() => setActiveView(v.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold transition ${activeView === v.id ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}>
                <v.icon size={11} /> {v.label}
                {v.id === 'rewrite' && <span className="bg-purple-600 text-white text-xs px-1 rounded">NEW</span>}
              </button>
            ))}
          </div>

          {/* ── Overview panel ── */}
          {activeView === 'overview' && (
            <div className="grid grid-cols-2 gap-4">
              {/* Missing events alert */}
              {uncovered.length > 0 && (
                <div className="bg-red-900/20 border border-red-700/50 rounded-xl p-4">
                  <div className="text-red-400 text-sm font-bold mb-3 flex items-center gap-2">
                    <AlertTriangle size={13} /> {uncovered.length} Uncovered Force Majeure Events — Gaps in Protection
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {uncovered.map(ev => (
                      <span key={ev} className="px-2 py-0.5 rounded text-xs font-medium bg-red-900/40 border border-red-700/60 text-red-300">
                        ✕ {ev}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {/* Covered events */}
              <div className="bg-green-900/10 border border-green-700/30 rounded-xl p-4">
                <div className="text-green-400 text-sm font-bold mb-3 flex items-center gap-2">
                  <CheckCircle size={13} /> {covered.length} Events Covered
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {covered.map(ev => (
                    <span key={ev} className="px-2 py-0.5 rounded text-xs font-medium bg-green-900/40 border border-green-700/60 text-green-300">
                      ✓ {ev}
                    </span>
                  ))}
                </div>
              </div>
              {/* Radar chart */}
              <div className="col-span-2 bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="text-gray-300 text-sm font-semibold mb-3">Force Majeure Coverage by Risk Category</div>
                <ResponsiveContainer width="100%" height={220}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                    <Radar name="Coverage %" dataKey="pct" stroke={meta.color} fill={meta.color} fillOpacity={0.25} strokeWidth={2} />
                    <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#fff', fontSize: 11 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* ── Coverage detail panel ── */}
          {activeView === 'coverage' && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
              <div className="text-gray-300 text-sm font-semibold mb-4">All 14 Force Majeure Event Categories — Coverage Status</div>
              <div className="grid grid-cols-2 gap-3">
                {FM_EVENT_CATEGORIES.map((ev) => {
                  const isCovered = covered.map(c => c.toLowerCase()).includes(ev.toLowerCase());
                  return (
                    <div key={ev} className="flex items-center gap-3 p-3 rounded-lg"
                      style={{ background: isCovered ? 'rgba(104,188,0,0.08)' : 'rgba(241,102,103,0.08)', border: `1px solid ${isCovered ? '#68BC0040' : '#F1666740'}` }}>
                      <div className="text-lg">{isCovered ? '✅' : '❌'}</div>
                      <div className="flex-1">
                        <div className="text-sm font-semibold" style={{ color: isCovered ? '#68BC00' : '#F16667' }}>{ev}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{isCovered ? 'Explicitly covered' : 'Not found in clause'}</div>
                      </div>
                      <div className={`text-xs font-bold px-2 py-0.5 rounded ${isCovered ? 'bg-green-900/40 text-green-400' : 'bg-red-900/40 text-red-400'}`}>
                        {isCovered ? 'COVERED' : 'MISSING'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Benchmark panel ── */}
          {activeView === 'benchmark' && (
            <div className="space-y-4">
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="text-gray-300 text-sm font-semibold mb-4">Benchmark Comparison — Industry Standards</div>
                <div className="space-y-4">
                  {BENCHMARKS.map((b) => {
                    const pct = Math.round((b.score || 0) * 100);
                    return (
                      <div key={b.label}>
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            {b.isThis && <span className="bg-gray-700 text-gray-300 text-xs px-1.5 py-0.5 rounded font-bold">YOUR CONTRACT</span>}
                            <span className="text-gray-300 text-sm font-semibold">{b.label}</span>
                          </div>
                          <span className="text-lg font-black" style={{ color: b.color }}>{pct}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-4 relative overflow-hidden">
                          <div className="h-4 rounded-full transition-all"
                            style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${b.color}88, ${b.color})` }} />
                          {b.isThis && (
                            <div className="absolute inset-0 flex items-center px-2">
                              <span className="text-white text-xs font-bold">{pct}% Force Majeure Coverage</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              {/* Gap analysis */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="text-gray-300 text-sm font-semibold mb-3">Gap Analysis vs Industry Leaders</div>
                <div className="grid grid-cols-3 gap-3">
                  {BENCHMARKS.slice(1).map(b => {
                    const gap = score - Math.round((b.score || 0) * 100);
                    return (
                      <div key={b.label} className="bg-gray-900 rounded-xl p-4 text-center">
                        <div className="text-gray-400 text-xs mb-2">{b.label}</div>
                        <div className={`text-2xl font-black ${gap >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                          {gap >= 0 ? '-' : '+'}{Math.abs(gap)}pp
                        </div>
                        <div className="text-gray-500 text-xs mt-1">{gap >= 0 ? 'below standard' : 'above standard'}</div>
                        <div className="mt-2 text-xs font-medium" style={{ color: b.color }}>Target: {Math.round((b.score||0)*100)}%</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ── AI Rewrite panel ── */}
          {activeView === 'rewrite' && correctionResult && (
            <div className="space-y-4">
              {/* Before/After KPIs */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4 text-center">
                  <div className="text-gray-400 text-xs mb-1">Before (Original)</div>
                  <div className="text-3xl font-black text-red-400">
                    {Math.round((correctionResult.original_strength_score || 0) * 100)}%
                  </div>
                  <div className="text-gray-500 text-xs mt-1">Force Majeure Coverage</div>
                </div>
                <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col items-center justify-center gap-1">
                  <Zap size={24} className="text-purple-400" />
                  <div className="text-2xl font-black text-purple-400">
                    +{Math.round((correctionResult.improvement || 0) * 100)}%
                  </div>
                  <div className="text-gray-400 text-xs">Improvement</div>
                </div>
                <div className="bg-green-900/20 border border-green-700/40 rounded-xl p-4 text-center">
                  <div className="text-gray-400 text-xs mb-1">After (AI Rewrite)</div>
                  <div className="text-3xl font-black text-green-400">
                    {Math.round((correctionResult.new_strength_score || 0) * 100)}%
                  </div>
                  <div className="text-gray-500 text-xs mt-1">Force Majeure Coverage</div>
                </div>
              </div>

              {/* Side-by-Side Redlining */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
                <div className="grid grid-cols-2 gap-0">
                  {/* LEFT: Original Clause */}
                  <div className="bg-red-900/10 border-r border-gray-700">
                    <div className="flex items-center gap-2 px-4 py-3 bg-gray-900 border-b border-red-700/40">
                      <XCircle size={13} className="text-red-400" />
                      <span className="text-red-300 text-sm font-bold">Original Clause</span>
                    </div>
                    <div className="p-4 max-h-96 overflow-y-auto">
                      <p className="text-sm text-red-300 leading-relaxed whitespace-pre-wrap line-through">
                        {ctx.contract_text}
                      </p>
                    </div>
                  </div>

                  {/* RIGHT: Suggested Revision */}
                  <div className="bg-green-900/10">
                    <div className="flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-green-700/40">
                      <div className="flex items-center gap-2">
                        <CheckCircle size={13} className="text-green-400" />
                        <span className="text-green-300 text-sm font-bold">Suggested Revision</span>
                      </div>
                      <button onClick={handleCopy}
                        className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded font-semibold transition ${copied ? 'bg-green-700 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'}`}>
                        <Download size={10} /> {copied ? '✓' : 'Copy'}
                      </button>
                    </div>
                    <div className="p-4 max-h-96 overflow-y-auto">
                      <p className="text-sm text-green-300 leading-relaxed whitespace-pre-wrap">
                        {correctionResult.corrected_clause}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 3 — WAR RISK
// ═══════════════════════════════════════════════════════════════════════════════
const WarRiskTab = ({ contract }) => {
  const ctx = contract;
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!ctx.contract_text.trim()) { setError('Paste contract text in the Contract Context panel above first'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const data = await analyzeWarRisk({
        contract_text: ctx.contract_text,
        contract_title: ctx.contract_title,
        contract_value: parseFloat(ctx.contract_value) || 0,
        project_location: ctx.project_location,
        supplier_locations: ctx.supplier_locations.split(',').map(s => s.trim()).filter(Boolean),
      });
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center gap-4">
        <div className="flex-1">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Sword size={16} className="text-red-400" /> War & Geopolitical Risk Analysis
          </h3>
          {ctx.project_location && <p className="text-gray-400 text-xs mt-1">Location: {ctx.project_location}{ctx.supplier_locations ? ` · Suppliers: ${ctx.supplier_locations}` : ''}</p>}
          {!ctx.contract_text.trim() && <p className="text-yellow-500 text-xs mt-1">⚠ Paste contract text in the Contract Context panel above first</p>}
        </div>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <button onClick={handleAnalyze} disabled={loading || !ctx.contract_text.trim()}
          className="flex items-center gap-2 px-5 py-2.5 bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition shrink-0">
          {loading ? <RefreshCw size={14} className="animate-spin" /> : <Globe size={14} />}
          {loading ? 'Analyzing…' : 'Run War Risk Analysis'}
        </button>
      </div>

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="War Risk Score" value={`${Math.round((result.war_risk_score || 0) * 100)}%`}
              color={riskColor(result.war_risk_score)} icon={Sword} sub={riskLabel(result.war_risk_score)} />
            <MetricCard label="Expected Loss" value={`$${((result.war_loss_expected_usd || 0) / 1000).toFixed(0)}K`} color="#F16667" icon={TrendingUp} />
            <MetricCard label="Worst Case" value={`$${((result.war_loss_worst_usd || 0) / 1000).toFixed(0)}K`} color="#9063CD" icon={AlertTriangle} />
            <MetricCard label="Top Threats" value={(result.top_threats || []).length} color="#F79767" icon={Target} />
          </div>

          {(result.top_threats || []).length > 0 && (
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
              <h4 className="text-white text-sm font-semibold mb-3">Top Geopolitical Threats</h4>
              <div className="space-y-2">
                {result.top_threats.map((t, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-red-400 text-xs w-5">{i+1}.</span>
                    <span className="text-gray-300 text-sm capitalize flex-1">{t.event?.replace(/_/g, ' ')}</span>
                    <div className="flex-1 bg-gray-700 rounded-full h-2 max-w-40">
                      <div className="h-2 rounded-full bg-red-500" style={{ width: `${Math.round((t.probability || 0) * 100)}%` }} />
                    </div>
                    <span className="text-red-400 text-xs w-10 text-right">{Math.round((t.probability || 0) * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
            <h4 className="text-white text-sm font-semibold mb-3">War Risk Mitigation Clauses</h4>
            <div className="space-y-2">
              {(result.war_mitigation_clauses || []).map((clause, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <CheckCircle size={13} className="text-green-400 mt-0.5 shrink-0" />
                  <span className="text-gray-300">{clause}</span>
                </div>
              ))}
            </div>
          </div>

          {result.explanation && (
            <div className="bg-gray-800 border border-red-800 rounded-xl p-4">
              <h4 className="text-red-400 text-sm font-semibold mb-2">AI War Risk Assessment</h4>
              <p className="text-gray-300 text-sm leading-relaxed">{result.explanation}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 4 — SCENARIO SIMULATION
// ═══════════════════════════════════════════════════════════════════════════════
const ScenarioSimTab = ({ contract }) => {
  const ctx = contract;
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [activeResultTab, setActiveResultTab] = useState('overview');

  const handleSimulate = async () => {
    if (!selectedTemplate) { setError('Select a scenario template'); return; }
    setLoading(true); setError(''); setResult(null); setActiveResultTab('overview');
    try {
      const tpl = FM_SCENARIO_TEMPLATES.find(t => t.id === selectedTemplate);
      const data = await simulateFMScenario({
        contract_value: parseFloat(ctx.contract_value) || 5000000,
        scenario_type: tpl.id.includes('war') ? 'war' : tpl.id,
        scenario_name: tpl.name,
        description: tpl.description,
        input_params: tpl.params,
        scenario_template: tpl.id,
        iterations: 5000,
      });
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally { setLoading(false); }
  };

  const tpl = FM_SCENARIO_TEMPLATES.find(t => t.id === selectedTemplate);
  const cv = parseFloat(ctx.contract_value) || 5000000;

  const lossData = result?.loss_breakdown
    ? Object.entries(result.loss_breakdown).map(([k, v]) => ({
        name: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        value: Math.round(v),
        pct: Math.round((v / (result.expected_loss_usd || 1)) * 100),
      }))
    : [];

  const fmtMoney = (v) => {
    if (v >= 1e9) return `$${(v/1e9).toFixed(2)}B`;
    if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
    return `$${(v/1000).toFixed(0)}K`;
  };

  const RESULT_TABS = [
    { id: 'overview',  label: 'Overview',     icon: Activity },
    { id: 'montecarlo',label: 'Monte Carlo',   icon: TrendingUp },
    { id: 'breakdown', label: 'Loss Breakdown',icon: BarChart2 },
  ];

  // Percentile table data
  const distData = (result?.loss_distribution || []).map((v, i) => ({
    percentile: `${i * 5}%`,
    loss: Math.round(v / 1000),
    lossM: v / 1e6,
  }));

  // Key probability metrics from result
  const probMetrics = result ? [
    { label: 'Force Majeure Invocation',     value: result.fm_invocation_prob || 0,    color: '#9063CD', icon: Shield },
    { label: 'Project Delay',     value: result.project_delay_prob || 0,     color: '#4C8EDA', icon: Clock },
    { label: 'Cost Overrun',      value: result.cost_overrun_prob || 0,      color: '#F79767', icon: TrendingUp },
    { label: 'Contract Suspend',  value: result.contract_suspension_prob || 0,color: '#F16667', icon: AlertTriangle },
  ] : [];

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Activity size={18} className="text-purple-400" /> Monte Carlo Scenario Simulation
          </h2>
          <p className="text-gray-400 text-sm mt-0.5">5,000-iteration stochastic simulation across 8 Force Majeure scenario templates</p>
        </div>
        {ctx.contract_value && (
          <div className="text-right">
            <div className="text-gray-500 text-xs">Contract Value</div>
            <div className="text-white font-bold text-sm">{fmtMoney(cv)}</div>
          </div>
        )}
      </div>

      {/* ── Scenario selector grid ── */}
      <div className="grid grid-cols-4 gap-3">
        {FM_SCENARIO_TEMPLATES.map((t) => {
          const isSel = selectedTemplate === t.id;
          return (
            <button key={t.id} onClick={() => setSelectedTemplate(t.id)}
              className="text-left rounded-xl p-4 border-2 transition-all group"
              style={{
                background: isSel ? `${t.color}18` : 'rgba(31,41,55,0.8)',
                borderColor: isSel ? t.color : '#374151',
                boxShadow: isSel ? `0 0 16px ${t.color}44, inset 0 0 20px ${t.color}08` : 'none',
              }}>
              <div className="flex items-start justify-between mb-2">
                <span className="text-2xl">{t.icon}</span>
                {isSel && <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ background: `${t.color}33`, color: t.color }}>SELECTED</span>}
              </div>
              <div className="text-white text-sm font-bold mb-1">{t.name}</div>
              <div className="text-gray-500 text-xs leading-relaxed">{t.description}</div>
              {t.params && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {Object.entries(t.params).slice(0,2).map(([k,v]) => (
                    <span key={k} className="text-xs px-1.5 py-0.5 rounded font-mono"
                      style={{ background: `${t.color}22`, color: t.color }}>
                      {k}: {typeof v === 'number' ? v.toFixed(1) : v}
                    </span>
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Run bar ── */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {tpl ? (
            <div className="flex items-center gap-3">
              <span className="text-2xl">{tpl.icon}</span>
              <div>
                <div className="text-white text-sm font-bold">{tpl.name}</div>
                <div className="text-gray-400 text-xs">{tpl.description}</div>
              </div>
            </div>
          ) : (
            <span className="text-gray-500 text-sm">← Select a scenario above</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {error && <span className="text-red-400 text-sm">{error}</span>}
          <div className="text-gray-500 text-xs text-right">
            <div>5,000 iterations</div>
            <div>Monte Carlo</div>
          </div>
          <button onClick={handleSimulate} disabled={loading || !selectedTemplate}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold transition disabled:opacity-50"
            style={{ background: tpl ? `linear-gradient(135deg, ${tpl.color}cc, ${tpl.color}88)` : '#6d28d9' }}>
            {loading ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            {loading ? 'Simulating…' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {result && (
        <>
          {/* ── Result tabs ── */}
          <div className="flex gap-1 bg-gray-800/60 rounded-lg p-1 border border-gray-700 w-fit">
            {RESULT_TABS.map(v => (
              <button key={v.id} onClick={() => setActiveResultTab(v.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold transition ${activeResultTab === v.id ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}>
                <v.icon size={11} /> {v.label}
              </button>
            ))}
          </div>

          {/* ── Overview ── */}
          {activeResultTab === 'overview' && (
            <div className="space-y-4">
              {/* Scenario banner */}
              <div className="rounded-xl p-4 flex items-center gap-4"
                style={{ background: tpl ? `${tpl.color}18` : '#1f2937', border: `1px solid ${tpl?.color || '#374151'}44` }}>
                <span className="text-4xl">{tpl?.icon}</span>
                <div className="flex-1">
                  <div className="text-white font-bold text-base">{result.scenario_name || tpl?.name}</div>
                  <div className="text-gray-400 text-xs mt-0.5">{tpl?.description}</div>
                </div>
                <div className="text-right">
                  <div className="text-gray-400 text-xs">Force Majeure Risk Score</div>
                  <div className="text-2xl font-black" style={{ color: riskColor(result.fm_risk_score || 0) }}>
                    {Math.round((result.fm_risk_score || 0) * 100)}%
                  </div>
                  <div className="text-xs font-bold" style={{ color: riskColor(result.fm_risk_score || 0) }}>
                    {riskLabel(result.fm_risk_score || 0)} RISK
                  </div>
                </div>
              </div>

              {/* KPI cards */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Expected Loss',  value: fmtMoney(result.expected_loss_usd || 0), color: '#F16667', icon: TrendingUp, sub: 'mean of 5,000 runs' },
                  { label: 'Stress Test Loss',       value: fmtMoney(result.p95_loss_usd || 0),      color: '#F79767', icon: BarChart2,  sub: '1-in-20 stress scenario' },
                  { label: 'Worst Case',     value: fmtMoney(result.worst_case_loss_usd || result.p95_loss_usd || 0), color: '#9063CD', icon: AlertTriangle, sub: '1-in-100 worst case' },
                  { label: '% of Contract',  value: `${Math.min(100, Math.round(((result.expected_loss_usd||0)/cv)*100))}%`, color: '#4C8EDA', icon: Shield, sub: 'expected exposure' },
                ].map((m, i) => (
                  <div key={i} className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                    <div className="flex items-center gap-1 text-gray-400 text-xs mb-2">
                      <m.icon size={11} /> {m.label}
                    </div>
                    <div className="text-2xl font-black" style={{ color: m.color }}>{m.value}</div>
                    <div className="text-gray-600 text-xs mt-1">{m.sub}</div>
                  </div>
                ))}
              </div>

              {/* Probability meters */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="text-gray-300 text-sm font-semibold mb-4">Contract Outcome Probabilities</div>
                <div className="grid grid-cols-2 gap-4">
                  {probMetrics.map((m, i) => (
                    <div key={i}>
                      <div className="flex justify-between items-center mb-1.5">
                        <div className="flex items-center gap-1.5 text-gray-300 text-xs"><m.icon size={11}/> {m.label}</div>
                        <span className="font-black text-sm" style={{ color: m.color }}>{Math.round(m.value * 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                        <div className="h-3 rounded-full transition-all" style={{
                          width: `${Math.round(m.value * 100)}%`,
                          background: `linear-gradient(90deg, ${m.color}88, ${m.color})`,
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── Monte Carlo distribution ── */}
          {activeResultTab === 'montecarlo' && distData.length > 0 && (() => {
            const p50val  = distData[10]?.loss || 0;  // Index 10 = P50 (10/20 = 50%)
            const p75val  = distData[15]?.loss || 0;  // Index 15 = P75 (15/20 = 75%)
            const p90val  = distData[18]?.loss || 0;  // Index 18 = P90 (18/20 = 90%)
            const p95val  = distData[19]?.loss || 0;  // Index 19 = P95 (19/20 = 95%)
            const p99val  = Math.round((result.p99_loss_usd || 0) / 1000);  // Use direct P99 from backend (not from distData)
            const maxLoss = Math.max(...distData.map(d => d.loss));
            const expectedK = Math.round((result.expected_loss_usd || 0) / 1000);

            // Enrich distData with EXCEEDANCE probability (inverted from CDF)
            const enriched = distData.map((d, i) => {
              const percentile = i * 5; // 0%, 5%, 10%... 100%
              const exceedance = 100 - percentile; // 100%, 95%, 90%... 0%
              return {
                ...d,
                percentile: `${exceedance}%`, // Show exceedance instead of percentile
                originalPercentile: percentile,
                zone: i < 10 ? 'safe' : i < 16 ? 'moderate' : i < 19 ? 'high' : 'critical',
                barColor: i < 10 ? '#68BC00' : i < 16 ? '#F1C40F' : i < 19 ? '#F79767' : '#F16667',
              };
            });

            const PCTILES = [
              { label: 'Typical Case (P50)', val: p50val,  color: '#68BC00', desc: '50/50 chance — half of scenarios are worse' },
              { label: 'Elevated Risk (P75)', val: p75val,  color: '#F1C40F', desc: '1-in-4 chance — 25% of scenarios are worse' },
              { label: 'Bad Case (P90)',      val: p90val,  color: '#F79767', desc: '1-in-10 chance — 10% of scenarios are worse' },
              { label: 'Stress Test (P95)',   val: p95val,  color: '#F16667', desc: '1-in-20 chance — reserve buffer for planning' },
              { label: 'Catastrophic (P99)',  val: p99val,  color: '#9063CD', desc: '1-in-100 chance — black swan event' },
            ];

            const CustomTooltip = ({ active, payload, label }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0]?.payload;
              return (
                <div style={{ background: '#111827', border: '1px solid #374151', borderRadius: 10, padding: '10px 14px', fontSize: 11 }}>
                  <div style={{ color: '#9ca3af', marginBottom: 4 }}>Exceedance Probability: <b style={{ color: '#fff' }}>{label}</b></div>
                  <div style={{ color: '#9ca3af' }}>Loss at P{d?.originalPercentile}: <b style={{ color: d?.barColor || '#4C8EDA' }}>${(d?.loss || 0).toLocaleString()}K</b></div>
                  <div style={{ color: '#9ca3af' }}>= <b style={{ color: '#e5e7eb' }}>{fmtMoney((d?.loss || 0) * 1000)}</b></div>
                  <div style={{ marginTop: 4, color: '#6b7280', fontSize: 10 }}>
                    <b style={{ color: '#fff' }}>{label}</b> of scenarios will EXCEED this loss
                  </div>
                </div>
              );
            };

            return (
              <div className="space-y-4">
                {/* ── Main chart ── */}
                <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                  <div className="flex items-start justify-between mb-1">
                    <div>
                      <div className="text-white text-sm font-bold">Monte Carlo Loss Exceedance Curve</div>
                      <div className="text-gray-500 text-xs mt-0.5">{result.iterations?.toLocaleString() || '5,000'} iterations · probability of EXCEEDING each loss level</div>
                    </div>
                    <div className="flex gap-3 text-xs">
                      {[['#F16667','Catastrophic (1-in-20 or worse)'],['#F79767','Bad Case (1-in-4 to 1-in-20)'],['#F1C40F','Elevated Risk (1-in-2 to 1-in-4)'],['#68BC00','Typical (better than 50/50)']].map(([c,l]) => (
                        <div key={l} className="flex items-center gap-1">
                          <div className="w-2.5 h-2.5 rounded-sm" style={{ background: c }} />
                          <span className="text-gray-400">{l}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <ResponsiveContainer width="100%" height={300}>
                    <ComposedChart data={enriched} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="mcSafeGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#68BC00" stopOpacity={0.25} />
                          <stop offset="100%" stopColor="#68BC00" stopOpacity={0.02} />
                        </linearGradient>
                        <linearGradient id="mcCritGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#F16667" stopOpacity={0.35} />
                          <stop offset="100%" stopColor="#F16667" stopOpacity={0.03} />
                        </linearGradient>
                      </defs>

                      {/* Risk zone shading (inverted for exceedance) */}
                      <ReferenceArea x1="100%" x2="50%" fill="#68BC00" fillOpacity={0.04} />
                      <ReferenceArea x1="50%" x2="25%" fill="#F1C40F" fillOpacity={0.04} />
                      <ReferenceArea x1="25%" x2="5%" fill="#F79767" fillOpacity={0.05} />
                      <ReferenceArea x1="5%" x2="0%" fill="#F16667" fillOpacity={0.07} />

                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                      <XAxis dataKey="percentile" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={{ stroke: '#374151' }} tickLine={false}
                        label={{ value: 'Exceedance Probability', position: 'insideBottom', offset: -5, fill: '#9ca3af', fontSize: 10 }} reversed />
                      <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false}
                        tickFormatter={v => v >= 1000 ? `$${(v/1000).toFixed(0)}M` : `$${v}K`}
                        label={{ value: 'Loss Amount', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 10 }} />
                      <Tooltip content={<CustomTooltip />} />

                      {/* Reference lines for key percentiles (now showing exceedance) */}
                      <ReferenceLine x="50%" stroke="#68BC00" strokeDasharray="4 3" strokeWidth={1.5}
                        label={{ value: 'Typical (50/50)', position: 'top', fill: '#68BC00', fontSize: 9 }} />
                      <ReferenceLine x="25%" stroke="#F1C40F" strokeDasharray="4 3" strokeWidth={1.5}
                        label={{ value: 'Elevated (1-in-4)', position: 'top', fill: '#F1C40F', fontSize: 9 }} />
                      <ReferenceLine x="5%" stroke="#F16667" strokeDasharray="4 3" strokeWidth={1.5}
                        label={{ value: 'Stress Test (1-in-20)', position: 'top', fill: '#F16667', fontSize: 9 }} />

                      {/* Expected loss reference line */}
                      <ReferenceLine y={expectedK} stroke="#fff" strokeDasharray="6 3" strokeWidth={1.5} strokeOpacity={0.5}
                        label={{ value: `Expected $${fmtMoney(result.expected_loss_usd||0)}`, position: 'insideTopRight', fill: '#e5e7eb', fontSize: 9 }} />

                      {/* Area fill */}
                      <Area type="monotone" dataKey="loss" stroke="none" fill="url(#mcSafeGrad)" dot={false} legendType="none" />

                      {/* Main line */}
                      <Line type="monotone" dataKey="loss" stroke="#4C8EDA" strokeWidth={3} dot={false} />

                      {/* Dots at key percentiles */}
                      <Line type="monotone" dataKey="loss" strokeWidth={0} dot={(props) => {
                        const keyIdx = [10, 15, 18, 19];
                        const colors = ['#68BC00','#F1C40F','#F79767','#F16667'];
                        const pos = keyIdx.indexOf(props.index);
                        if (pos === -1) return null;
                        return <circle key={props.index} cx={props.cx} cy={props.cy} r={5} fill={colors[pos]} stroke="#111827" strokeWidth={2} />;
                      }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>

                {/* ── Percentile cards row ── */}
                <div className="grid grid-cols-5 gap-2">
                  {PCTILES.map(p => (
                    <div key={p.label} className="bg-gray-800 border border-gray-700 rounded-xl p-3 text-center hover:border-gray-500 transition">
                      <div className="text-xs font-bold mb-1" style={{ color: p.color }}>{p.label}</div>
                      <div className="text-lg font-black text-white">{fmtMoney(p.val * 1000)}</div>
                      <div className="text-gray-600 text-xs mt-1 leading-relaxed">{p.desc}</div>
                      {/* Mini bar showing proportion of max */}
                      <div className="mt-2 bg-gray-700 rounded-full h-1">
                        <div className="h-1 rounded-full" style={{ width: `${Math.round((p.val / (maxLoss||1))*100)}%`, background: p.color }} />
                      </div>
                    </div>
                  ))}
                </div>

                {/* ── Stats row ── */}
                <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 grid grid-cols-4 gap-4">
                  {[
                    { label: 'Expected Loss',   val: fmtMoney(result.expected_loss_usd||0), color: '#4C8EDA',  sub: 'mean of all iterations' },
                    { label: 'Risk Spread (Catastrophic to Typical)', val: fmtMoney((p99val - p50val)*1000), color: '#F16667', sub: 'spread of uncertainty' },
                    { label: 'Prob > Expected', val: `~50%`, color: '#F79767', sub: 'by definition of mean' },
                    { label: '% of Contract',   val: `${Math.min(100,Math.round(((result.expected_loss_usd||0)/cv)*100))}%`, color: '#68BC00', sub: `of ${fmtMoney(cv)} contract value` },
                  ].map((s,i) => (
                    <div key={i}>
                      <div className="text-gray-500 text-xs mb-1">{s.label}</div>
                      <div className="text-xl font-black" style={{ color: s.color }}>{s.val}</div>
                      <div className="text-gray-600 text-xs mt-0.5">{s.sub}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* ── Loss breakdown ── */}
          {activeResultTab === 'breakdown' && lossData.length > 0 && (
            <div className="grid grid-cols-2 gap-4">
              {/* Donut chart */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="text-gray-300 text-sm font-semibold mb-3">Loss Breakdown by Category</div>
                <div className="flex items-center justify-center">
                  <PieChart width={200} height={200}>
                    <Pie data={lossData} cx={95} cy={95} innerRadius={55} outerRadius={88} dataKey="value" paddingAngle={3}>
                      {lossData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', color: '#fff', borderRadius: 8 }}
                      formatter={v => [`$${(v/1000).toFixed(0)}K`, 'Loss']} />
                  </PieChart>
                </div>
                <div className="space-y-1.5 mt-2">
                  {lossData.map((d, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                      <span className="text-gray-400 flex-1 capitalize">{d.name}</span>
                      <span className="text-white font-bold">${(d.value/1000).toFixed(0)}K</span>
                      <span className="text-gray-600">{d.pct}%</span>
                    </div>
                  ))}
                </div>
              </div>
              {/* Horizontal bar breakdown */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="text-gray-300 text-sm font-semibold mb-4">Category Contribution</div>
                <div className="space-y-3">
                  {lossData.map((d, i) => {
                    const pct = Math.round((d.value / lossData.reduce((a,b) => a+b.value, 0)) * 100);
                    return (
                      <div key={i}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-300 capitalize">{d.name}</span>
                          <span className="font-bold" style={{ color: PIE_COLORS[i % PIE_COLORS.length] }}>{pct}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2.5">
                          <div className="h-2.5 rounded-full" style={{ width: `${pct}%`, background: PIE_COLORS[i % PIE_COLORS.length] }} />
                        </div>
                        <div className="text-gray-600 text-xs mt-0.5">${(d.value/1000).toFixed(0)}K</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 5 — RISK GRAPH (Bayesian Causal Network)
// ═══════════════════════════════════════════════════════════════════════════════
const RiskGraphTab = ({ prediction }) => {
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [evidence, setEvidence] = useState('');
  const [error, setError] = useState('');
  const [fullscreen, setFullscreen] = useState(false);

  const loadGraph = async () => {
    setLoading(true); setError('');
    try {
      const data = await getFMBayesianGraph(evidence);
      setGraphData(data);
    } catch (e) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  // Active nodes from prediction
  const activeNodes = React.useMemo(() => {
    const active = new Set();
    (prediction?.top_risk_drivers || []).forEach(d => { if (d.node) active.add(d.node.toLowerCase()); });
    Object.entries(prediction?.bayesian_nodes || {}).forEach(([k, v]) => { if (v > 0.5) active.add(k.toLowerCase()); });
    return active;
  }, [prediction]);

  const highlightedNodes = React.useMemo(() => {
    if (!graphData?.nodes) return [];
    return graphData.nodes.map(n => {
      const key = (n.data?.label || n.id || '').toLowerCase().replace(/\s+/g, '_');
      const isActive = activeNodes.has(key) || activeNodes.has((n.data?.label || '').toLowerCase());
      if (!isActive) return n;
      return {
        ...n,
        style: {
          ...n.style,
          boxShadow: '0 0 16px 4px #facc15, 0 0 4px 1px #facc15',
          border: '2px solid #facc15',
          zIndex: 10,
        },
      };
    });
  }, [graphData, activeNodes]);

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center gap-4">
        <div className="flex-1">
          <div className="text-gray-400 text-xs mb-1">Evidence Override (optional)</div>
          <input
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-500"
            placeholder="e.g., war:0.8,trade_sanctions:0.7,pandemic:0.3"
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
          />
        </div>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <button
          onClick={loadGraph}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition whitespace-nowrap"
        >
          {loading ? <RefreshCw size={14} className="animate-spin" /> : <Eye size={14} />}
          {loading ? 'Loading…' : 'Load Graph'}
        </button>
      </div>

      {!graphData && !loading && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-8 text-center">
          <Eye size={40} className="text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400">Click "Load Graph" to visualize the 35-node Bayesian causal network</p>
          <p className="text-gray-600 text-sm mt-1">Optionally set evidence values to see how risk propagates</p>
        </div>
      )}

      {graphData && (
        <>
          <div className="flex gap-4 text-xs text-gray-400 flex-wrap items-center">
            {[
              { color: '#F16667', label: 'High Risk (>60%)' },
              { color: '#F79767', label: 'Medium Risk (35–60%)' },
              { color: '#68BC00', label: 'Low Risk (<35%)' },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-1">
                <div className="w-3 h-3 rounded" style={{ background: item.color }} />
                {item.label}
              </div>
            ))}
            {activeNodes.size > 0 && (
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs"
                style={{background:'#facc1522', color:'#facc15', border:'1px solid #facc1544'}}>
                <span className="w-2 h-2 rounded-full inline-block" style={{background:'#facc15'}}/>
                ⚡ Active in YOUR contract ({activeNodes.size} nodes)
              </span>
            )}
            <span className="ml-auto mr-2">{graphData.nodes?.length} nodes · {graphData.edges?.length} edges</span>
            <button
              onClick={() => setFullscreen(f => !f)}
              className="flex items-center gap-1 px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-xs transition"
            >
              {fullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
              {fullscreen ? 'Exit' : 'Fullscreen'}
            </button>
          </div>

          {fullscreen && (
            <div className="fixed inset-0 z-50 bg-gray-950 flex flex-col">
              <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700">
                <span className="text-white text-sm font-semibold">Bayesian Risk Graph — {graphData.nodes?.length} nodes · {graphData.edges?.length} edges</span>
                <button onClick={() => setFullscreen(false)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-xs transition">
                  <Minimize2 size={13} /> Exit Fullscreen
                </button>
              </div>
              <div className="flex-1">
                <ReactFlow nodes={highlightedNodes} edges={graphData.edges || []} fitView proOptions={{ hideAttribution: true }}>
                  <Background color="#374151" gap={20} />
                  <Controls />
                  <MiniMap nodeColor={(n) => n.style?.background || '#4C8EDA'} style={{ background: '#111827' }} />
                </ReactFlow>
              </div>
            </div>
          )}

          <div className="h-[520px] bg-gray-900 rounded-xl border border-gray-700">
            <ReactFlow
              nodes={highlightedNodes}
              edges={graphData.edges || []}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#374151" gap={20} />
              <Controls />
              <MiniMap
                nodeColor={(n) => n.style?.background || '#4C8EDA'}
                style={{ background: '#111827' }}
              />
            </ReactFlow>
          </div>
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 6 — HOW IT WORKS
// ═══════════════════════════════════════════════════════════════════════════════
const HowItWorksTab = () => (
  <div className="space-y-4 text-sm text-gray-300">
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
      <h3 className="text-white font-bold text-base mb-3">Force Majeure Intelligence Engine — Architecture</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { title: '1. Force Majeure Risk Predictor', color: '#4C8EDA', desc: '35-node Bayesian causal network with 4 layers: Root Events → Intermediate Disruptions → Supply Chain Impacts → Contract Outcomes. Noisy-OR forward propagation gives posterior probabilities.' },
          { title: '2. Force Majeure Loss Predictor', color: '#F79767', desc: '5,000-iteration Monte Carlo simulation. Samples delay cost, cost overrun, suspension, and termination losses using Bayesian outcome probabilities as sampling weights.' },
          { title: '3. Force Majeure Clause Auditor', color: '#68BC00', desc: 'Scans contracts for 14 modern Force Majeure event categories using keyword/regex matching. Computes strength score (0–1) vs. FIDIC, NEC, ICC benchmarks.' },
          { title: '4. Auto-Correct Engine', color: '#9063CD', desc: 'LLM (Qwen 2.5 via Ollama) rewrites weak Force Majeure clauses to cover all 14 event categories with notice period, cost escalation, insurance trigger, and termination clauses.' },
          { title: '5. War Risk Engine', color: '#F16667', desc: '17-node war event ontology (invasion, cyber, blockade, sanctions…) with Noisy-OR causal weights mapping to supply chain disruptions. Returns war risk score and top threats.' },
          { title: '6. Scenario Simulation', color: '#06B6D4', desc: '6 pre-built scenario templates (war escalation, pandemic, supply chain collapse, commodity shock, financial crisis, base case) + custom. Monte Carlo per scenario with loss breakdown.' },
        ].map(card => (
          <div key={card.title} className="bg-gray-900 rounded-lg p-4 border-l-4" style={{ borderLeftColor: card.color }}>
            <div className="font-semibold mb-1" style={{ color: card.color }}>{card.title}</div>
            <p className="text-gray-400 text-xs leading-relaxed">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>

    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
      <h3 className="text-white font-bold mb-3">Bayesian Network — 35 Nodes, 4 Layers</h3>
      <div className="space-y-3">
        {[
          { layer: 'Layer 1 — Root Events (15)', color: '#4C8EDA', nodes: 'War, Regional Conflict, Cyber Warfare, Terrorism, Pandemic, Epidemic, Earthquake, Flood, Hurricane, Wildfire, Volcanic Eruption, Political Coup, Trade Sanctions, Economic Collapse, Energy Crisis' },
          { layer: 'Layer 2 — Intermediate Disruptions (12)', color: '#F79767', nodes: 'Sanctions Expansion, Currency Volatility, Commodity Price Shock, Energy Price Spike, Labor Shortage, Factory Shutdown, Transport Shutdown, Port Closure, Airspace Closure, Telecom Disruption, Power Grid Failure, Financial Market Crash' },
          { layer: 'Layer 3 — Supply Chain Impacts (8)', color: '#9063CD', nodes: 'Supplier Failure, Inventory Shortage, Logistics Delay, Shipping Route Disruption, Manufacturing Delay, Equipment Delivery Delay, Commodity Cost Escalation, Insurance Premium Spike' },
          { layer: 'Layer 4 — Contract Outcomes (6)', color: '#F16667', nodes: 'Project Delay, Cost Overrun, Contract Suspension, Insurance Claim, Force Majeure Invocation, Contract Termination' },
        ].map(l => (
          <div key={l.layer}>
            <div className="font-semibold text-xs mb-1" style={{ color: l.color }}>{l.layer}</div>
            <div className="text-gray-500 text-xs">{l.nodes}</div>
          </div>
        ))}
      </div>
    </div>

    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
      <h3 className="text-white font-bold mb-2">API Endpoints</h3>
      <div className="space-y-1 font-mono text-xs text-gray-400">
        {[
          ['POST', '/api/force-majeure/predict/', 'Force Majeure risk prediction'],
          ['POST', '/api/force-majeure/audit-clause/', 'Force Majeure clause audit'],
          ['POST', '/api/force-majeure/auto-correct/', 'LLM clause rewrite'],
          ['POST', '/api/force-majeure/war-risk/', 'War risk analysis'],
          ['POST', '/api/force-majeure/simulate-scenario/', 'Monte Carlo scenario'],
          ['POST', '/api/force-majeure/bulk-audit/', 'Portfolio bulk audit'],
          ['GET', '/api/force-majeure/bayesian-graph/', 'Bayesian network graph data'],
          ['GET', '/api/force-majeure/portfolio-summary/', 'Portfolio Force Majeure summary'],
          ['GET', '/api/force-majeure/alerts/', 'Global Force Majeure alerts'],
        ].map(([method, path, desc]) => (
          <div key={path} className="flex gap-3">
            <span className={`w-10 ${method === 'POST' ? 'text-yellow-400' : 'text-green-400'}`}>{method}</span>
            <span className="text-blue-400 w-72">{path}</span>
            <span className="text-gray-500">{desc}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: LIVE TERMINAL (Bloomberg-style inline panel)
// ═══════════════════════════════════════════════════════════════════════════════
const severityColor = { CRITICAL: '#9d1b1b', HIGH: '#F16667', MEDIUM: '#F79767', LOW: '#68BC00' };
const evIcon = { war:'⚔️', sanctions:'🚫', pandemic:'🦠', port_closure:'⚓', natural_disaster:'🌊', energy_shortage:'⚡', supply_chain_disruption:'🔗', cyber_attack:'💻', terrorism:'💣', earthquake:'🌋', unknown:'❓' };

const RiskBadge = ({ score }) => {
  const c = score > 0.7 ? '#F16667' : score > 0.4 ? '#F79767' : '#68BC00';
  const l = score > 0.7 ? 'HIGH' : score > 0.4 ? 'MED' : 'LOW';
  return <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ background: c+'33', color: c }}>{l}</span>;
};
const LiveDot = () => (
  <span className="relative flex h-2 w-2">
    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
    <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
  </span>
);

const LiveTerminalTab = () => {
  const [eventStream, setEventStream] = useState(null);
  const [warIntel, setWarIntel]       = useState(null);
  const [riskMap, setRiskMap]         = useState(null);
  const [alerts, setAlerts]           = useState(null);
  const [radar, setRadar]             = useState(null);
  const [loading, setLoading]         = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [auto, setAuto]               = useState(true);
  const intervalRef = useRef(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const [s,w,m,a,r] = await Promise.allSettled([
      getEventStream(), getWarIntelligence(), getRiskMapData(), getPortfolioAlerts(), getLiveEvents(),
    ]);
    if (s.status==='fulfilled') setEventStream(s.value);
    if (w.status==='fulfilled') setWarIntel(w.value);
    if (m.status==='fulfilled') setRiskMap(m.value);
    if (a.status==='fulfilled') setAlerts(a.value);
    if (r.status==='fulfilled') setRadar(r.value);
    setLoading(false);
    setLastRefresh(new Date());
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);
  useEffect(() => {
    if (auto) intervalRef.current = setInterval(fetchAll, 60000);
    return () => clearInterval(intervalRef.current);
  }, [auto, fetchAll]);

  // Enhanced barData with color coding and risk severity
  const barData = Object.entries(radar?.by_event_type || {}).map(([k,v]) => {
    const name = k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
    // Determine color based on event type risk level
    let color = '#9063CD'; // default purple
    let riskLevel = 'Medium';
    const highRiskEvents = ['war', 'military_invasion', 'naval_blockade', 'sanctions', 'cyber_warfare', 'terrorism'];
    const mediumRiskEvents = ['political_coup', 'earthquake', 'pandemic', 'port_shutdown'];

    if (highRiskEvents.includes(k)) {
      color = '#F16667'; // red
      riskLevel = 'High';
    } else if (mediumRiskEvents.includes(k)) {
      color = '#F79767'; // orange
      riskLevel = 'Medium';
    } else {
      color = '#68BC00'; // green
      riskLevel = 'Low';
    }

    return {
      name,
      count: v,
      color,
      riskLevel,
      percentage: radar?.total ? Math.round((v / radar.total) * 100) : 0
    };
  }).sort((a,b)=>b.count-a.count);

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex items-center justify-between bg-gray-800 rounded-xl px-4 py-2 border border-gray-700">
        <div className="flex items-center gap-3 text-xs">
          <LiveDot />
          <span className="text-white font-bold">FORCE MAJEURE LIVE TERMINAL</span>
          <span className="text-gray-500">GDELT · USGS · ReliefWeb · NewsAPI</span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-purple-400 font-bold">{radar?.total || 0} events</span>
          <span className="text-red-400 font-bold">{radar?.high_risk_count || 0} high-risk</span>
          <span className="text-yellow-400 font-bold">{alerts?.critical_alerts || 0} critical alerts</span>
          <button onClick={fetchAll} className="flex items-center gap-1 px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded transition">
            <RefreshCw size={10} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button onClick={()=>setAuto(a=>!a)} className={`flex items-center gap-1 px-2 py-1 rounded transition ${auto?'bg-green-900 text-green-400':'bg-gray-700 text-gray-400'}`}>
            <Radio size={10} /> {auto?'AUTO ON':'AUTO OFF'}
          </button>
          <span className="text-gray-600 flex items-center gap-1"><Clock size={10}/> {lastRefresh.toLocaleTimeString()}</span>
        </div>
      </div>

      {/* 3-col top row */}
      <div className="grid grid-cols-3 gap-3">
        {/* Event Stream */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl flex flex-col" style={{maxHeight:320}}>
          <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700 text-xs font-bold text-yellow-400"><Radio size={11}/>LIVE EVENTS</div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {loading ? <div className="text-gray-500 text-xs text-center py-4">Loading…</div> :
              (eventStream?.ticker||[]).length===0 ? <div className="text-gray-500 text-xs text-center py-4">No events</div> :
              (eventStream?.ticker||[]).map((ev,i)=>(
                <div key={i} className="flex items-start gap-2 p-1.5 rounded hover:bg-gray-700 transition">
                  <span className="text-gray-500 text-xs w-10 shrink-0 font-mono">{ev.time?.slice(11,16)||'--:--'}</span>
                  <span className="text-xs">{evIcon[ev.event_type]||'📌'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-gray-200 text-xs leading-tight truncate">{ev.title}</div>
                    <div className="text-gray-500 text-xs">{ev.location} · {ev.source}</div>
                  </div>
                  <RiskBadge score={ev.risk_score}/>
                </div>
              ))
            }
          </div>
          <div className="px-3 py-1.5 border-t border-gray-700 text-gray-600 text-xs">{eventStream?.total||0} total</div>
        </div>

        {/* War Intel */}
        <div className="bg-gray-800 border border-red-900 rounded-xl flex flex-col" style={{maxHeight:320}}>
          <div className="flex items-center justify-between px-3 py-2 border-b border-red-900 text-xs font-bold text-red-400">
            <span className="flex items-center gap-2"><Sword size={11}/>WAR INTELLIGENCE</span>
            <span className="text-red-600">GWI: {warIntel?.global_war_risk_index ? `${Math.round(warIntel.global_war_risk_index*100)}%` : '--'}</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loading ? <div className="text-gray-500 text-xs text-center py-4">Loading…</div> : <>
              <div className="text-gray-500 text-xs px-1 mb-1">TOP WAR ZONES</div>
              {(warIntel?.top_war_zones||[]).slice(0,5).map((z,i)=>(
                <div key={i} className="flex items-center gap-2 px-1 py-0.5">
                  <span className="text-gray-400 text-xs w-3">{i+1}.</span>
                  <span className="text-gray-200 text-xs flex-1">{z.country}</span>
                  <div className="w-14 bg-gray-700 rounded-full h-1.5"><div className="h-1.5 rounded-full bg-red-500" style={{width:`${Math.round(z.war_risk*100)}%`}}/></div>
                  <span className="text-red-400 text-xs w-8 text-right">{Math.round(z.war_risk*100)}%</span>
                </div>
              ))}
              <div className="text-gray-500 text-xs px-1 mt-2 mb-1">SHIPPING DISRUPTIONS</div>
              {(warIntel?.active_shipping_disruptions||[]).map((r,i)=>(
                <div key={i} className="px-1 py-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-yellow-400 text-xs font-medium">{r.route}</span>
                    <RiskBadge score={r.risk}/>
                  </div>
                  <div className="text-gray-500 text-xs truncate">{r.cause}</div>
                </div>
              ))}
            </>}
          </div>
          <div className="px-3 py-1.5 border-t border-red-900 text-gray-600 text-xs">{warIntel?.war_events_detected||0} war events</div>
        </div>

        {/* Risk Map */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl flex flex-col" style={{maxHeight:320}}>
          <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700 text-xs font-bold text-blue-400">
            <span className="flex items-center gap-2"><Globe size={11}/>GLOBAL RISK MAP</span>
            <span className="text-gray-500">{riskMap?.high_risk_regions||0} high-risk</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {loading ? <div className="text-gray-500 text-xs text-center py-4">Loading…</div> : <>
              <div className="grid grid-cols-2 gap-1 mb-2">
                {(riskMap?.risk_regions||[]).slice(0,10).map((r,i)=>(
                  <div key={i} className="flex items-center justify-between px-2 py-1 rounded text-xs"
                    style={{background:(r.color||'#374151')+'22',border:`1px solid ${r.color||'#374151'}44`}}>
                    <span className="text-gray-300 truncate max-w-16">{r.country}</span>
                    <span className="font-bold ml-1" style={{color:r.color||'#9ca3af'}}>{Math.round((r.risk_score||0)*100)}%</span>
                  </div>
                ))}
              </div>
              <div className="text-gray-500 text-xs mb-1">CRITICAL ROUTES</div>
              {(riskMap?.shipping_routes||[]).map((r,i)=>(
                <div key={i} className="flex items-center gap-2 px-1 py-0.5">
                  <span className="text-xs">⚓</span>
                  <span className="text-gray-300 text-xs flex-1 truncate">{r.name}</span>
                  <span className="text-xs font-bold" style={{color:r.color}}>{Math.round(r.disruption_risk*100)}%</span>
                </div>
              ))}
            </>}
          </div>
        </div>
      </div>

      {/* Bottom row: Radar chart + Portfolio Alerts */}
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2 bg-gray-800 border border-gray-700 rounded-xl p-3">
          <div className="flex items-center justify-between mb-3 text-xs">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-purple-400"/>
              <span className="font-bold text-purple-400 text-sm">FORCE MAJEURE RADAR — EVENT BREAKDOWN</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-400">{radar?.total||0} total events · {radar?.high_risk_count||0} high-risk</span>
              <div className="flex items-center gap-2 border-l border-gray-700 pl-3">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{background:'#F16667'}}/>
                  <span className="text-gray-400 text-xs">High</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{background:'#F79767'}}/>
                  <span className="text-gray-400 text-xs">Medium</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{background:'#68BC00'}}/>
                  <span className="text-gray-400 text-xs">Low</span>
                </div>
              </div>
            </div>
          </div>
          {loading ? <div className="text-gray-500 text-xs text-center py-4">Loading…</div> :
            barData.length===0 ? <div className="text-gray-500 text-xs text-center py-4">No events</div> :
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={barData} barSize={24} margin={{top:10,right:10,bottom:5,left:0}}>
                <defs>
                  <linearGradient id="highRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#F16667" stopOpacity={1}/>
                    <stop offset="100%" stopColor="#D14748" stopOpacity={1}/>
                  </linearGradient>
                  <linearGradient id="mediumRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#F79767" stopOpacity={1}/>
                    <stop offset="100%" stopColor="#E57B4A" stopOpacity={1}/>
                  </linearGradient>
                  <linearGradient id="lowRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#68BC00" stopOpacity={1}/>
                    <stop offset="100%" stopColor="#52A300" stopOpacity={1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3}/>
                <XAxis
                  dataKey="name"
                  tick={{fill:'#9ca3af',fontSize:10,fontWeight:600}}
                  angle={-25}
                  textAnchor="end"
                  height={60}
                  interval={0}
                  stroke="#4B5563"
                />
                <YAxis
                  tick={{fill:'#9ca3af',fontSize:10}}
                  label={{value:'Event Count',angle:-90,position:'insideLeft',fill:'#9ca3af',fontSize:10}}
                  stroke="#4B5563"
                />
                <Tooltip
                  contentStyle={{
                    background:'linear-gradient(135deg, #1F2937 0%, #111827 100%)',
                    border:'1px solid #374151',
                    borderRadius:'8px',
                    color:'#fff',
                    fontSize:11,
                    padding:'8px 12px',
                    boxShadow:'0 4px 12px rgba(0,0,0,0.4)'
                  }}
                  cursor={{fill:'rgba(144, 99, 205, 0.1)'}}
                  formatter={(value, name, props) => {
                    const item = props.payload;
                    return [
                      <div key="tooltip-content">
                        <div style={{fontWeight:'bold',color:item.color,marginBottom:4}}>{item.name}</div>
                        <div style={{color:'#d1d5db'}}>Events: <span style={{fontWeight:'bold',color:'#fff'}}>{value}</span></div>
                        <div style={{color:'#d1d5db'}}>Percentage: <span style={{fontWeight:'bold',color:'#fff'}}>{item.percentage}%</span></div>
                        <div style={{color:'#d1d5db'}}>Risk Level: <span style={{fontWeight:'bold',color:item.color}}>{item.riskLevel}</span></div>
                      </div>,
                      ''
                    ];
                  }}
                  labelFormatter={() => ''}
                />
                <Bar
                  dataKey="count"
                  radius={[6,6,0,0]}
                  fill="#9063CD"
                >
                  {barData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.riskLevel === 'High' ? 'url(#highRisk)' :
                        entry.riskLevel === 'Medium' ? 'url(#mediumRisk)' :
                        'url(#lowRisk)'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          }
        </div>
        <div className="bg-gray-800 border border-yellow-900 rounded-xl flex flex-col" style={{maxHeight:260}}>
          <div className="flex items-center justify-between px-3 py-2 border-b border-yellow-900 text-xs font-bold text-yellow-400">
            <span className="flex items-center gap-2"><AlertTriangle size={11}/>PORTFOLIO ALERTS</span>
            <span className="text-yellow-600">{alerts?.critical_alerts||0} CRITICAL</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {loading ? <div className="text-gray-500 text-xs text-center py-4">Scanning…</div> :
              (alerts?.portfolio_alerts||[]).length===0 ? <div className="text-green-500 text-xs text-center py-4">✓ No critical alerts</div> :
              (alerts?.portfolio_alerts||[]).slice(0,6).map((a,i)=>(
                <div key={i} className="p-2 rounded bg-gray-900 border border-gray-700">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-gray-200 text-xs truncate max-w-28">{a.contract_title||a.contract_id?.slice(0,8)+'…'}</span>
                    <RiskBadge score={a.fm_trigger_probability}/>
                  </div>
                  <div className="flex gap-1 flex-wrap">
                    {(a.triggered_by||[]).slice(0,2).map((t,j)=>(
                      <span key={j} className="text-xs px-1 bg-gray-700 text-gray-400 rounded">{t?.replace(/_/g,' ')}</span>
                    ))}
                  </div>
                </div>
              ))
            }
          </div>
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: COUNTERFACTUAL RISK ENGINE
// ═══════════════════════════════════════════════════════════════════════════════
const CounterfactualTab = ({ contract, prediction }) => {
  const ctx = contract;

  // Auto-build evidence string from top risk drivers
  const autoEvidence = React.useMemo(() => {
    const drivers = prediction?.top_risk_drivers || [];
    if (!drivers.length) return 'war:0.80, trade_sanctions:0.70, energy_crisis:0.60';
    return drivers.slice(0, 5).map(d => {
      const key = (d.node || d.factor || d.name || '').toLowerCase().replace(/\s+/g, '_');
      const val = d.probability !== undefined ? d.probability.toFixed(2) : (d.score !== undefined ? (d.score / 100).toFixed(2) : '0.70');
      return `${key}:${val}`;
    }).filter(s => s.startsWith('_') === false && s.includes(':') && !s.startsWith(':')).join(', ');
  }, [prediction]);

  const autoRemove = React.useMemo(() => {
    const drivers = prediction?.top_risk_drivers || [];
    if (!drivers.length) return 'war';
    const top = drivers[0];
    return (top.node || top.factor || top.name || 'war').toLowerCase().replace(/\s+/g, '_');
  }, [prediction]);

  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');
  const [baseEvents, setBaseEvents] = useState('');
  const [removeEvents, setRemoveEvents] = useState('');

  useEffect(() => { setBaseEvents(autoEvidence); }, [autoEvidence]);
  useEffect(() => { setRemoveEvents(autoRemove); }, [autoRemove]);

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const base_evidence = {};
      baseEvents.split(',').forEach(pair => {
        const [k,v] = pair.split(':').map(s=>s.trim());
        if (k&&v) base_evidence[k] = parseFloat(v);
      });
      const remove = removeEvents.split(',').map(s=>s.trim()).filter(Boolean);
      if (!ctx.contract_text.trim()) { setError('No contract text — go to the Risk Predictor tab and run analysis first.'); setLoading(false); return; }
      setResult(await runCounterfactual({ contract_text: ctx.contract_text.trim(), contract_value: parseFloat(ctx.contract_value) || 0, base_evidence, remove_events: remove }));
    } catch(e) { setError(e?.response?.data?.error||e.message); }
    finally { setLoading(false); }
  };

  const fmtU = v => v ? `$${Number(v).toLocaleString(undefined,{maximumFractionDigits:0})}` : '$0';
  const fmtP = v => v!==undefined ? `${Math.round(v*100)}%` : '—';

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-purple-900">
        <p className="text-gray-400 text-sm mb-3"><em>"What would Force Majeure risk have been if [event] had NOT occurred?"</em> — Isolates causal contribution of each root event.</p>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Base Evidence <span className="text-green-400">(auto-populated from your analysis)</span></label>
            <input value={baseEvents} onChange={e=>setBaseEvents(e.target.value)}
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200"/>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Event to Remove <span className="text-green-400">(top risk driver auto-selected)</span></label>
            <input value={removeEvents} onChange={e=>setRemoveEvents(e.target.value)}
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200"/>
          </div>
        </div>
        {ctx.contract_value && <p className="text-gray-500 text-xs mb-3">Using contract value: ${Number(ctx.contract_value).toLocaleString()}</p>}
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 px-5 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50">
          <Play size={14}/> {loading?'Analyzing…':'Run Counterfactual'}
        </button>
        {error && <div className="mt-2 text-red-400 text-xs">{error}</div>}
      </div>
      {result && (() => {
        const baseRisk = result.baseline?.fm_risk_score || 0;
        const cfRisk = result.counterfactual?.fm_risk_score || 0;
        const pctReduction = result.delta_analysis?.pct_risk_reduction || 0;
        const lossSaved = result.delta_analysis?.loss_reduction_usd || 0;
        const baseLoss = result.baseline?.expected_loss_usd || 0;
        const cfLoss = result.counterfactual?.expected_loss_usd || 0;

        const deltaChartData = Object.entries(result.delta_analysis?.outcome_deltas || {}).map(([k, v]) => ({
          name: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          Baseline: Math.round(v.baseline * 100),
          Counterfactual: Math.round(v.counterfactual * 100),
          Delta: parseFloat((v.delta * 100).toFixed(1)),
        }));

        const causalData = (result.causal_attribution || []).map(a => ({
          name: a.event?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          contribution: parseFloat(a.contribution_pct?.toFixed(1) || 0),
        }));

        const riskCompareData = [
          { name: 'Baseline', value: Math.round(baseRisk * 100), fill: '#F16667' },
          { name: 'Counterfactual', value: Math.round(cfRisk * 100), fill: '#68BC00' },
        ];

        return (
          <div className="space-y-4">
            {/* KPI row */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Baseline Force Majeure Risk',    v: fmtP(baseRisk),    color: 'text-red-400',    border: 'border-red-900',    bg: 'bg-red-950/30' },
                { label: 'Counterfactual Risk', v: fmtP(cfRisk),      color: 'text-green-400',  border: 'border-green-900',  bg: 'bg-green-950/30' },
                { label: 'Risk Reduction',      v: `${pctReduction}%`,color: 'text-purple-400', border: 'border-purple-900', bg: 'bg-purple-950/30' },
                { label: 'Baseline Loss',       v: fmtU(baseLoss),    color: 'text-red-400',    border: 'border-red-900',    bg: 'bg-red-950/30' },
                { label: 'CF Loss',             v: fmtU(cfLoss),      color: 'text-green-400',  border: 'border-green-900',  bg: 'bg-green-950/30' },
                { label: 'Loss Saved',          v: fmtU(lossSaved),   color: 'text-yellow-400', border: 'border-yellow-900', bg: 'bg-yellow-950/30' },
              ].map((k, i) => (
                <div key={i} className={`rounded-xl p-4 border ${k.border} ${k.bg} text-center`}>
                  <div className={`text-2xl font-bold ${k.color}`}>{k.v}</div>
                  <div className="text-gray-500 text-xs mt-1">{k.label}</div>
                </div>
              ))}
            </div>

            {/* AI Insight */}
            <div className="bg-gray-800 border border-purple-800 rounded-xl p-4 flex gap-3">
              <div className="text-purple-400 text-xl">💡</div>
              <div>
                <div className="text-purple-300 text-sm font-semibold mb-1">AI Counterfactual Insight</div>
                <p className="text-gray-300 text-sm leading-relaxed">{result.insight}</p>
              </div>
            </div>

            {/* Two charts side by side */}
            <div className="grid grid-cols-2 gap-4">
              {/* Risk comparison bar */}
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div className="text-gray-300 text-sm font-semibold mb-3">Risk Score: Before vs After</div>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={riskCompareData} barCategoryGap="35%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#9CA3AF', fontSize: 11 }} tickFormatter={v => `${v}%`} />
                    <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8 }} />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]} label={{ position: 'top', fill: '#e5e7eb', fontSize: 12, formatter: v => `${v}%` }}>
                      {riskCompareData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Causal attribution horizontal bar */}
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div className="text-gray-300 text-sm font-semibold mb-3">Causal Attribution by Event</div>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={causalData} layout="vertical" barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis type="number" domain={[0, 'auto']} tick={{ fill: '#9CA3AF', fontSize: 10 }} tickFormatter={v => `${v}%`} />
                    <YAxis type="category" dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 10 }} width={120} />
                    <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8 }} />
                    <Bar dataKey="contribution" fill="#a78bfa" radius={[0, 4, 4, 0]} name="Contribution %" label={{ position: 'right', fill: '#a78bfa', fontSize: 11, formatter: v => `${v}%` }} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Grouped bar: Baseline vs Counterfactual per outcome */}
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3">Outcome Probabilities: Baseline vs Counterfactual</div>
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={deltaChartData} barCategoryGap="20%" barGap={3}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#9CA3AF', fontSize: 11 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={v => `${v}%`} contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8 }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: '#9CA3AF' }} />
                  <Bar dataKey="Baseline" fill="#F16667" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="Counterfactual" fill="#68BC00" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Delta breakdown with visual bars */}
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3">Probability Delta Breakdown</div>
              <div className="space-y-3">
                {deltaChartData.map((row, i) => {
                  const isGood = row.Delta <= 0;
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-gray-400 text-xs w-36 shrink-0">{row.name}</span>
                      <div className="flex gap-1 items-center text-xs shrink-0">
                        <span className="text-red-400 w-10 text-right">{row.Baseline}%</span>
                        <span className="text-gray-600 mx-1">→</span>
                        <span className="text-green-400 w-10 text-right">{row.Counterfactual}%</span>
                      </div>
                      <div className="flex-1 bg-gray-700 rounded-full h-2">
                        <div className={`h-2 rounded-full transition-all ${isGood ? 'bg-green-500' : 'bg-red-500'}`}
                          style={{ width: `${Math.min(100, Math.abs(row.Delta) * 5)}%` }} />
                      </div>
                      <span className={`text-xs font-bold w-14 text-right shrink-0 ${isGood ? 'text-green-400' : 'text-red-400'}`}>
                        {row.Delta >= 0 ? '+' : ''}{row.Delta}pp
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: PORTFOLIO-WIDE FORCE MAJEURE SIMULATION
// ═══════════════════════════════════════════════════════════════════════════════
const PortfolioSimTab = ({ contract, prediction }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');
  const [scenarioType, setScenarioType] = useState('war_escalation');

  const handleRun = async () => {
    if (!contract?.contract_text?.trim()) {
      setError('No contract text — go to the Risk Predictor tab and run analysis first.');
      return;
    }
    setLoading(true); setError(''); setResult(null);
    try {
      const template = FM_SCENARIO_TEMPLATES.find(t => t.id === scenarioType) || FM_SCENARIO_TEMPLATES[0];
      // Use simulatePortfolio for portfolio-wide analysis
      const res = await simulatePortfolio({
        scenario_type: scenarioType,
        contracts: [{
          id: contract.contract_id || 'pasted-contract',
          title: contract.contract_title || 'Taiwan Advanced Semiconductor Fab EPC Contract',
          contract_value: parseFloat(contract.contract_value) || 1500000000,
          text: contract.contract_text,
          industry: contract.industry || 'Semiconductor',
          jurisdiction: contract.jurisdiction || 'Taiwan',
        }],
        iterations: 5000,
      });
      // Extract results from portfolio response
      const portfolioSummary = res.portfolio_summary || {};
      const topContract = (res.contract_results || [])[0] || {};
      const expLoss = portfolioSummary.total_expected_exposure_usd || topContract.expected_loss_usd || 0;
      const p95 = portfolioSummary.total_worst_case_exposure_usd || topContract.p95_loss_usd || 0;
      const fmProb = topContract.fm_risk_score || res.scenario?.scenario_risk_score || 0;
      // Risk label: combine scenario severity tier with Force Majeure probability
      const scenarioTier = {
        war_escalation: 4, pandemic: 3, supply_chain_collapse: 3,
        financial_crisis: 2, commodity_shock: 2, climate_disaster: 2, base_case: 1,
      };
      const tier = scenarioTier[scenarioType] ?? 2;
      // tier 4 = always CRITICAL if fmProb>0.7, tier 1 = cap at HIGH
      // Always compute from scenario tier — never trust backend risk_label
      const computedLabel = (() => {
        if (tier === 4) return fmProb > 0.7 ? 'CRITICAL' : fmProb > 0.5 ? 'HIGH' : 'MEDIUM';
        if (tier === 3) return fmProb > 0.85 ? 'CRITICAL' : fmProb > 0.65 ? 'EXTREME' : fmProb > 0.5 ? 'HIGH' : 'MEDIUM';
        if (tier === 2) return fmProb > 0.90 ? 'CRITICAL' : fmProb > 0.75 ? 'EXTREME' : fmProb > 0.55 ? 'HIGH' : 'MEDIUM';
        // tier 1 = base_case: cap at HIGH regardless of fmProb
        return fmProb > 0.85 ? 'HIGH' : fmProb > 0.65 ? 'MEDIUM' : 'LOW';
      })();
      setResult({ expLoss, p95, fmProb, riskLabel: computedLabel, scenarioName: template.name, raw: res });
    } catch(e) { setError(e?.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };

  const fmtU = v => v ? `$${Number(v).toLocaleString(undefined,{maximumFractionDigits:0})}` : '$0';
  const COLORS = ['#F16667','#F79767','#68BC00','#4C8EDA','#9063CD','#06B6D4'];

  const breakdownData = result?.raw?.loss_breakdown
    ? Object.entries(result.raw.loss_breakdown).map(([k,v]) => ({
        name: k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()),
        value: Math.round(v/1000),
      })).filter(d => d.value > 0)
    : [];

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-blue-900">
        <p className="text-gray-400 text-sm mb-4">
          Simulates a global Force Majeure scenario against <span className="text-white font-semibold">{contract?.contract_title || 'your contract'}</span> — Monte Carlo exposure with 5,000 iterations.
        </p>
        <div className="flex items-center gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Scenario</label>
            <select value={scenarioType} onChange={e=>setScenarioType(e.target.value)}
              className="bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200">
              {FM_SCENARIO_TEMPLATES.map(t=><option key={t.id} value={t.id}>{t.icon} {t.name}</option>)}
            </select>
          </div>
          <button onClick={handleRun} disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50 self-end">
            <Play size={14}/> {loading?'Simulating…':'Run Simulation'}
          </button>
        </div>
        {error && <div className="text-red-400 text-xs">{error}</div>}
      </div>

      {result && (
        <div className="space-y-4">
          {/* Hero Metrics Cards */}
          <div className="grid grid-cols-4 gap-3">
            {[
              {label:'Contract', v: contract?.contract_title?.slice(0,20)+'…' || '—', color:'text-blue-400', icon:'📄', bg:'bg-gradient-to-br from-blue-900/40 to-blue-800/20 border-blue-700'},
              {label:'Risk Level', v: result.riskLabel,
                color: result.riskLabel==='CRITICAL'?'text-red-400':result.riskLabel==='EXTREME'?'text-red-300':result.riskLabel==='HIGH'?'text-orange-400':result.riskLabel==='MEDIUM'?'text-yellow-400':'text-green-400',
                icon: result.riskLabel==='CRITICAL'?'🚨':result.riskLabel==='EXTREME'?'🔥':result.riskLabel==='HIGH'?'⚠️':result.riskLabel==='MEDIUM'?'🟡':'🟢',
                bg: result.riskLabel==='CRITICAL'?'bg-gradient-to-br from-red-900/40 to-red-800/20 border-red-700':result.riskLabel==='EXTREME'?'bg-gradient-to-br from-red-900/60 to-red-700/30 border-red-500':result.riskLabel==='HIGH'?'bg-gradient-to-br from-orange-900/40 to-orange-800/20 border-orange-700':result.riskLabel==='MEDIUM'?'bg-gradient-to-br from-yellow-900/40 to-yellow-800/20 border-yellow-700':'bg-gradient-to-br from-green-900/40 to-green-800/20 border-green-700'},
              {label:'Expected Loss', v: fmtU(result.expLoss), color:'text-yellow-400', icon:'💰', bg:'bg-gradient-to-br from-yellow-900/40 to-yellow-800/20 border-yellow-700'},
              {label:'Stress Test Reserve', v: fmtU(result.p95), color:'text-orange-400', icon:'📊', bg:'bg-gradient-to-br from-orange-900/40 to-orange-800/20 border-orange-700'},
            ].map((k,i)=>(
              <div key={i} className={`${k.bg} rounded-xl p-4 border text-center transform hover:scale-105 transition-all duration-200`}>
                <div className="text-2xl mb-2">{k.icon}</div>
                <div className={`text-xl font-bold truncate ${k.color}`}>{k.v}</div>
                <div className="text-gray-400 text-xs mt-1">{k.label}</div>
              </div>
            ))}
          </div>

          {/* Main Visualization Row */}
          <div className="grid grid-cols-3 gap-4">
            {/* Force Majeure Risk Gauge */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3 flex items-center gap-2">
                <Target size={14} className="text-purple-400"/>
                Force Majeure Invocation Probability
              </div>
              <div className="flex items-center justify-center h-40">
                <div className="relative">
                  <svg width="180" height="180" viewBox="0 0 180 180">
                    <defs>
                      <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor={result.fmProb > 0.8 ? '#F16667' : result.fmProb > 0.6 ? '#F79767' : '#FFD86E'} />
                        <stop offset="100%" stopColor={result.fmProb > 0.8 ? '#D14748' : result.fmProb > 0.6 ? '#E57B4A' : '#FFB84D'} />
                      </linearGradient>
                    </defs>
                    <circle cx="90" cy="90" r="70" fill="none" stroke="#374151" strokeWidth="12"/>
                    <circle cx="90" cy="90" r="70" fill="none" stroke="url(#gaugeGrad)" strokeWidth="12"
                      strokeDasharray={`${2 * Math.PI * 70 * result.fmProb} ${2 * Math.PI * 70}`}
                      strokeLinecap="round" transform="rotate(-90 90 90)"
                      style={{filter:'drop-shadow(0 0 8px rgba(241,102,103,0.5))'}}/>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <div className="text-4xl font-bold" style={{color: result.fmProb > 0.8 ? '#F16667' : result.fmProb > 0.6 ? '#F79767' : '#FFD86E'}}>
                      {Math.round(result.fmProb * 100)}%
                    </div>
                    <div className="text-gray-400 text-xs mt-1">{result.scenarioName}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Loss Distribution Bar Chart */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3 flex items-center gap-2">
                <BarChart2 size={14} className="text-blue-400"/>
                Loss Distribution
              </div>
              <ResponsiveContainer width="100%" height={170}>
                <BarChart data={[
                  {name: 'Expected', value: result.expLoss / 1000000, color: '#FFD86E'},
                  {name: 'Stress Test', value: result.p95 / 1000000, color: '#F79767'},
                ]} margin={{top:10,right:10,bottom:20,left:10}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3}/>
                  <XAxis dataKey="name" tick={{fill:'#9ca3af',fontSize:11}} stroke="#4B5563"/>
                  <YAxis tick={{fill:'#9ca3af',fontSize:10}} stroke="#4B5563" label={{value:'Million USD',angle:-90,position:'insideLeft',fill:'#9ca3af',fontSize:10}}/>
                  <Tooltip contentStyle={{background:'#111827',border:'1px solid #374151',borderRadius:'8px',color:'#fff',fontSize:11}}
                    formatter={(v) => [`$${v.toFixed(1)}M`, 'Loss']}/>
                  <Bar dataKey="value" radius={[8,8,0,0]}>
                    {[{},{},{}].map((_, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? '#FFD86E' : '#F79767'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Loss Breakdown Pie */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3 flex items-center gap-2">
                <Activity size={14} className="text-green-400"/>
                Loss Components
              </div>
              {breakdownData.length > 0 ? (
                <ResponsiveContainer width="100%" height={170}>
                  <PieChart>
                    <Pie data={breakdownData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={65} innerRadius={35}>
                      {breakdownData.map((_,i)=><Cell key={i} fill={COLORS[i % COLORS.length]}/>)}
                    </Pie>
                    <Tooltip contentStyle={{background:'#111827',border:'1px solid #374151',borderRadius:'8px',color:'#fff',fontSize:11}}
                      formatter={(v,n) => [`$${v}K`, n]}/>
                    <Legend wrapperStyle={{fontSize:9,color:'#9ca3af'}} iconSize={8}/>
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-40">
                  <div className="text-center">
                    <div className="text-5xl mb-2">💵</div>
                    <div className="text-gray-400 text-sm">Total Exposure</div>
                    <div className="text-yellow-400 text-2xl font-bold mt-1">{fmtU(result.expLoss)}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Detailed Breakdown Table */}
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3 flex items-center gap-2">
              <Layers size={14} className="text-purple-400"/>
              Scenario Details — {result.scenarioName}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(result.raw?.loss_breakdown || {delay_penalties: result.expLoss * 0.4, idle_labor: result.expLoss * 0.25, equipment_rental: result.expLoss * 0.2, supply_chain_rerouting: result.expLoss * 0.15}).map(([k,v],i) => {
                const maxVal = Math.max(...Object.values(result.raw?.loss_breakdown || {delay_penalties: result.expLoss * 0.4, idle_labor: result.expLoss * 0.25, equipment_rental: result.expLoss * 0.2, supply_chain_rerouting: result.expLoss * 0.15}));
                const pct = (v / maxVal) * 100;
                return (
                  <div key={i} className="bg-gray-900/50 rounded-lg p-3 border border-gray-700">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs text-gray-400">{k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</span>
                      <span className="text-yellow-400 text-sm font-bold">{fmtU(v)}</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div className="h-2 rounded-full transition-all duration-500"
                        style={{width: `${pct}%`, background: `linear-gradient(90deg, ${COLORS[i % COLORS.length]}, ${COLORS[(i+1) % COLORS.length]})`}}/>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Risk Summary Banner */}
          <div className={`rounded-xl p-4 border ${result.riskLabel === 'CRITICAL' ? 'bg-gradient-to-r from-red-900/30 to-orange-900/30 border-red-700' : 'bg-gradient-to-r from-orange-900/30 to-yellow-900/30 border-orange-700'}`}>
            <div className="flex items-center gap-3">
              <div className="text-4xl">{result.riskLabel === 'CRITICAL' ? '🚨' : '⚠️'}</div>
              <div className="flex-1">
                <div className="text-white font-bold text-sm mb-1">
                  {result.riskLabel === 'CRITICAL' ? '🔴 CRITICAL RISK EXPOSURE' : '🟠 HIGH RISK EXPOSURE'}
                </div>
                <div className="text-gray-300 text-xs">
                  Under {result.scenarioName} scenario, this contract has a <span className="text-yellow-400 font-bold">{Math.round(result.fmProb * 100)}% probability</span> of Force Majeure invocation with expected losses of <span className="text-orange-400 font-bold">{fmtU(result.expLoss)}</span>.
                  Stress Test (1-in-20) exposure: <span className="text-red-400 font-bold">{fmtU(result.p95)}</span>.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: FORCE MAJEURE KNOWLEDGE GRAPH
// ═══════════════════════════════════════════════════════════════════════════════
const KnowledgeGraphTab = ({ prediction }) => {
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [focus, setFocus] = useState('all');
  const [depth, setDepth] = useState(3);
  const [fullscreen, setFullscreen] = useState(false);

  const loadGraph = async () => {
    setLoading(true);
    try { setGraphData(await getFMKnowledgeGraph(focus, depth)); }
    catch(e){ console.error(e); }
    finally{ setLoading(false); }
  };
  useEffect(()=>{ loadGraph(); },[]);

  // Build set of active node keys from prediction's top risk drivers + bayesian_nodes
  const activeNodes = React.useMemo(() => {
    const active = new Set();
    (prediction?.top_risk_drivers || []).forEach(d => {
      if (d.node) active.add(d.node.toLowerCase());
    });
    // Also mark high-probability bayesian nodes (>0.5)
    Object.entries(prediction?.bayesian_nodes || {}).forEach(([k, v]) => {
      if (v > 0.5) active.add(k.toLowerCase());
    });
    return active;
  }, [prediction]);

  const graphNodes = React.useMemo(() => {
    if (!graphData?.nodes) return [];
    return graphData.nodes.map(n => {
      const key = (n.data?.label || n.id || '').toLowerCase().replace(/\s+/g, '_');
      const isActive = activeNodes.has(key) || activeNodes.has((n.data?.label||'').toLowerCase());
      if (!isActive) return n;
      return {
        ...n,
        style: {
          ...n.style,
          boxShadow: '0 0 16px 4px #facc15, 0 0 4px 1px #facc15',
          border: '2px solid #facc15',
          zIndex: 10,
        },
      };
    });
  }, [graphData, activeNodes]);

  const graphEdges = (graphData?.edges || []).map(e=>({
    ...e,
    markerEnd:{type:'arrowclosed', color:e.style?.stroke||'#555'},
    labelStyle: { fill: '#fff', fontSize: 10, fontWeight: 700 },
    labelBgStyle: { fill: '#1f2937', fillOpacity: 0.9 },
    labelBgPadding: [4, 4],
    labelBgBorderRadius: 3,
  }));

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 flex-wrap">
        <select value={focus} onChange={e=>setFocus(e.target.value)} className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200">
          <option value="all">All Events</option>
          <option value="war">War & Geopolitical</option>
          <option value="pandemic">Pandemic & Health</option>
          <option value="supply_chain">Supply Chain</option>
        </select>
        <select value={depth} onChange={e=>setDepth(Number(e.target.value))} className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200">
          <option value={1}>Depth 1 — Root Events</option>
          <option value={2}>Depth 2 — Disruptions</option>
          <option value={3}>Depth 3 — Full Graph</option>
        </select>
        <button onClick={loadGraph} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-cyan-700 hover:bg-cyan-800 rounded-lg text-white text-sm transition">
          <RefreshCw size={13} className={loading?'animate-spin':''}/> Load Graph
        </button>
        {graphData && (
          <>
            <span className="text-xs text-gray-500">{graphData.stats?.total_nodes} nodes · {graphData.stats?.total_edges} edges</span>
            <button onClick={()=>setFullscreen(true)} className="flex items-center gap-1 px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-xs transition ml-auto">
              <Maximize2 size={13}/> Fullscreen
            </button>
          </>
        )}
      </div>
      {graphData?.legend && (
        <div className="flex flex-wrap gap-2 items-center">
          {graphData.legend.map((l,i)=>(
            <span key={i} className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full"
              style={{background:l.color+'22',color:l.color,border:`1px solid ${l.color}44`}}>
              <span className="w-2 h-2 rounded-full inline-block" style={{background:l.color}}/>{l.label}
            </span>
          ))}
          {activeNodes.size > 0 && (
            <span className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full"
              style={{background:'#facc1522',color:'#facc15',border:'1px solid #facc1544'}}>
              <span className="w-2 h-2 rounded-full inline-block" style={{background:'#facc15'}}/>
              ⚡ Active in YOUR contract ({activeNodes.size} nodes)
            </span>
          )}
        </div>
      )}

      {fullscreen && (
        <div className="fixed inset-0 z-50 bg-gray-950 flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700">
            <span className="text-white text-sm font-semibold">Force Majeure Knowledge Graph — {graphData?.stats?.total_nodes} nodes · {graphData?.stats?.total_edges} edges</span>
            <button onClick={()=>setFullscreen(false)} className="flex items-center gap-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-xs transition">
              <Minimize2 size={13}/> Exit Fullscreen
            </button>
          </div>
          <div className="flex-1">
            <ReactFlow nodes={graphNodes} edges={graphEdges} fitView attributionPosition="bottom-right">
              <Background color="#374151" gap={20}/><Controls/><MiniMap style={{background:'#111827'}} nodeColor={n=>n.style?.background||'#555'}/>
            </ReactFlow>
          </div>
        </div>
      )}

      <div className="bg-gray-950 border border-gray-700 rounded-xl" style={{height:600}}>
        {loading ? <div className="flex items-center justify-center h-full text-gray-500 text-sm">Loading knowledge graph…</div>
          : graphData ? (
            <ReactFlow nodes={graphNodes} edges={graphEdges} fitView attributionPosition="bottom-right">
              <Background color="#374151" gap={20}/><Controls/><MiniMap style={{background:'#111827'}} nodeColor={n=>n.style?.background||'#555'}/>
            </ReactFlow>
          ) : <div className="flex items-center justify-center h-full text-gray-500 text-sm">Click "Load Graph"</div>}
      </div>

      {/* Data Tables Section */}
      {graphData && (
        <div className="grid grid-cols-2 gap-6 mt-6">
          {/* Nodes Table */}
          <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-blue-900/50 to-cyan-900/50 px-6 py-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Globe className="text-cyan-300" size={20} />
                </div>
                <div>
                  <h3 className="text-white font-bold text-lg">Node Values</h3>
                  <p className="text-gray-400 text-xs">Probability & risk scores for each node</p>
                </div>
              </div>
            </div>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-gray-900 border-b border-gray-700">
                  <tr>
                    <th className="text-left px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">Node</th>
                    <th className="text-left px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">Layer</th>
                    <th className="text-right px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">Probability</th>
                    <th className="text-center px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {(graphData.nodes || []).map((node, i) => {
                    const label = node.data?.label || node.id;
                    const layer = node.data?.layer || 'Unknown';
                    const probability = prediction?.bayesian_nodes?.[label.toLowerCase().replace(/\s+/g, '_')] ||
                                      prediction?.bayesian_nodes?.[label] ||
                                      node.data?.probability ||
                                      0;
                    const isActive = activeNodes.has(label.toLowerCase().replace(/\s+/g, '_'));
                    const color = node.style?.background || '#666';

                    return (
                      <tr key={i} className={`hover:bg-gray-800/50 transition-colors ${isActive ? 'bg-yellow-900/20' : ''}`}>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{background: color}}></div>
                            <span className="text-gray-200 font-semibold">{label}</span>
                            {isActive && <span className="text-xs text-yellow-400">⚡</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-400">{layer}</td>
                        <td className="px-4 py-3 text-right">
                          <span className="font-bold" style={{color: probability > 0.7 ? '#EF4444' : probability > 0.4 ? '#F59E0B' : '#10B981'}}>
                            {(probability * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                            probability > 0.7 ? 'bg-red-600 text-white' :
                            probability > 0.4 ? 'bg-yellow-600 text-white' :
                            'bg-green-600 text-white'
                          }`}>
                            {probability > 0.7 ? 'HIGH' : probability > 0.4 ? 'MEDIUM' : 'LOW'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Edges/Relationships Table */}
          <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 px-6 py-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <GitBranch className="text-purple-300" size={20} />
                </div>
                <div>
                  <h3 className="text-white font-bold text-lg">Causal Relationships</h3>
                  <p className="text-gray-400 text-xs">Edge weights & connection strengths</p>
                </div>
              </div>
            </div>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-gray-900 border-b border-gray-700">
                  <tr>
                    <th className="text-left px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">From</th>
                    <th className="text-center px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">→</th>
                    <th className="text-left px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">To</th>
                    <th className="text-right px-4 py-3 text-gray-300 font-bold uppercase tracking-wider">Weight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {(graphData.edges || []).map((edge, i) => {
                    const sourceNode = (graphData.nodes || []).find(n => n.id === edge.source);
                    const targetNode = (graphData.nodes || []).find(n => n.id === edge.target);
                    const sourceLabel = sourceNode?.data?.label || edge.source;
                    const targetLabel = targetNode?.data?.label || edge.target;
                    const weight = edge.data?.weight || edge.label || '50%';
                    // Parse weight: handle "85%" format or decimal 0.85
                    let numWeight = typeof weight === 'string' ? parseFloat(weight.replace('%', '')) : weight;
                    if (typeof weight === 'string' && weight.includes('%')) {
                      numWeight = numWeight / 100; // Convert "85%" to 0.85
                    }

                    return (
                      <tr key={i} className="hover:bg-gray-800/50 transition-colors">
                        <td className="px-4 py-3">
                          <span className="text-gray-300 font-semibold">{sourceLabel}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="text-gray-500">→</span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-gray-300 font-semibold">{targetLabel}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <div className="h-2 bg-gray-700 rounded-full w-20 overflow-hidden">
                              <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all"
                                style={{width: `${numWeight * 100}%`}}></div>
                            </div>
                            <span className="font-bold text-cyan-300 w-12 text-right">{(numWeight * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Summary Statistics */}
      {graphData && (
        <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden mt-6">
          <div className="bg-gradient-to-r from-indigo-900/50 to-purple-900/50 px-6 py-4 border-b border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/10 rounded-lg">
                <BarChart2 className="text-indigo-300" size={20} />
              </div>
              <h3 className="text-white font-bold text-lg">Graph Statistics & Weights Summary</h3>
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <div className="text-gray-400 text-xs mb-1">Total Nodes</div>
                <div className="text-3xl font-black text-white">{graphData.stats?.total_nodes || graphData.nodes?.length || 0}</div>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <div className="text-gray-400 text-xs mb-1">Total Edges</div>
                <div className="text-3xl font-black text-white">{graphData.stats?.total_edges || graphData.edges?.length || 0}</div>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <div className="text-gray-400 text-xs mb-1">Active Nodes</div>
                <div className="text-3xl font-black text-yellow-400">{activeNodes.size}</div>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <div className="text-gray-400 text-xs mb-1">Avg Edge Weight</div>
                <div className="text-3xl font-black text-cyan-400">
                  {((graphData.edges || []).reduce((sum, e) => {
                    const weight = e.data?.weight || e.label || '50%';
                    let numWeight = typeof weight === 'string' ? parseFloat(weight.replace('%', '')) : weight;
                    if (typeof weight === 'string' && weight.includes('%')) {
                      numWeight = numWeight / 100;
                    }
                    return sum + numWeight;
                  }, 0) / Math.max((graphData.edges || []).length, 1) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: CONTRACT DIGITAL TWIN
// ═══════════════════════════════════════════════════════════════════════════════
const DigitalTwinTab = ({ contract }) => {
  const ctx = contract;
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');
  const [industry, setIndustry] = useState('Energy');
  const fmtU = v => v ? `$${Number(v).toLocaleString(undefined,{maximumFractionDigits:0})}` : '$0';
  const fmtP = v => v!==undefined ? `${Math.round(v*100)}%` : '—';

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      if (!ctx.contract_text.trim()) { setError('No contract text — go to the Risk Predictor tab and run analysis first.'); setLoading(false); return; }
      setResult(await runDigitalTwin({
        contract_text: ctx.contract_text.trim(),
        contract_value: parseFloat(ctx.contract_value) || 0,
        contract_title: ctx.contract_title || 'Contract',
        jurisdiction: ctx.jurisdiction || 'International',
        industry,
        project_location: ctx.project_location || '',
        supplier_locations: ctx.supplier_locations.split(',').map(s=>s.trim()).filter(Boolean),
      }));
    } catch(e){ setError(e?.response?.data?.error||e.message); }
    finally{ setLoading(false); }
  };

  const hc = result ? (result.health?.score>0.7?'#68BC00':result.health?.score>0.4?'#F79767':'#F16667') : '#4C8EDA';

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-green-900">
        <p className="text-gray-400 text-sm mb-3">Creates a real-time digital twin of your contract — pulls live global events and continuously simulates Force Majeure risk impact.</p>
        <div className="flex items-center gap-3 mb-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Industry</label>
            <select value={industry} onChange={e=>setIndustry(e.target.value)}
              className="bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200">
              {['Energy','Construction','Manufacturing','Technology','Logistics','Finance','Healthcare','Agriculture'].map(i=><option key={i}>{i}</option>)}
            </select>
          </div>
          {!ctx.contract_text.trim() && <p className="text-yellow-500 text-xs">⚠ Paste contract text in the Contract Context panel above first</p>}
          {ctx.contract_title && <p className="text-gray-400 text-xs">{ctx.contract_title}{ctx.contract_value ? ` · $${Number(ctx.contract_value).toLocaleString()}` : ''}</p>}
        </div>
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 px-5 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50">
          <Cpu size={14}/> {loading?'Initializing Twin…':'Create Digital Twin'}
        </button>
        {error && <div className="mt-2 text-red-400 text-xs">{error}</div>}
      </div>
      {result && (() => {
        const fe = result.financial_exposure || {};
        const lr = result.live_risk || {};
        const ip = result.industry_profile || {};
        const hs = result.health || {};
        const expLoss = fe.expected_loss_usd || 0;
        const contractVal = fe.contract_value || 1;
        const exposurePct = fe.exposure_pct || 0;
        const fmt = v => v >= 1e9 ? `$${(v/1e9).toFixed(2)}B` : v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : `$${(v/1000).toFixed(0)}K`;
        const hcFull = hs.score > 0.7 ? '#68BC00' : hs.score > 0.4 ? '#F79767' : '#F16667';

        const timelineData = (result.exposure_timeline || []).map(t => ({
          month: t.month,
          loss: Math.round((t.expected_loss_usd || 0) / 1e6),
          risk: Math.round((t.fm_risk || 0) * 100),
          p95: Math.round((t.p95_loss_usd || t.expected_loss_usd * 1.25 || 0) / 1e6),
        }));

        const outcomeData = [
          { name: 'Force Majeure Invocation', value: Math.round((lr.fm_invocation_prob||0)*100), fill: '#F16667' },
          { name: 'Project Delay', value: Math.round((lr.project_delay_prob||0)*100), fill: '#F79767' },
          { name: 'Cost Overrun',  value: Math.round((lr.cost_overrun_prob||0)*100),  fill: '#FFD86E' },
          { name: 'Suspension',    value: Math.round((lr.contract_suspension_prob||0)*100), fill: '#9063CD' },
          { name: 'Termination',   value: Math.round((lr.contract_termination_prob||0)*100), fill: '#F16667' },
        ];

        const stressData = (result.stress_scenarios || []).map(s => ({
          name: s.scenario?.replace(' (Live Data)',''),
          risk: Math.round(s.fm_risk_score * 100),
          loss: Math.round((s.expected_loss_usd||0) / 1e6),
          color: s.color,
        }));

        const clauseStatus = result.clause_status || {};
        const covered = (clauseStatus.covered_events || []).length;
        const missing = (clauseStatus.missing_events || []);

        const liveEvents = result.live_events_affecting || [];

        return (
          <div className="space-y-4">
            {/* ── HERO TWIN HEADER ── */}
            <div className="relative overflow-hidden rounded-2xl border-2 p-5"
              style={{ borderColor: hcFull, background: 'linear-gradient(135deg, #0f172a 0%, #1a2744 100%)' }}>
              <div className="absolute top-0 right-0 w-64 h-64 opacity-5 rounded-full"
                style={{ background: hcFull, transform: 'translate(30%, -30%)' }} />
              <div className="relative flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Cpu size={16} className="text-green-400" />
                    <span className="text-green-400 text-xs uppercase tracking-widest font-semibold">Live Digital Twin</span>
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  </div>
                  <div className="text-white text-xl font-bold">{result.contract_title}</div>
                  <div className="text-gray-400 text-xs mt-1">
                    {result.industry} · {result.jurisdiction} · Twin ID: {result.twin_id}
                  </div>
                  <div className="text-gray-500 text-xs mt-1">
                    {lr.live_events_detected} live global events monitored · Last updated: {new Date().toLocaleTimeString()}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="text-6xl font-black" style={{ color: hcFull }}>{Math.round(hs.score * 100)}</div>
                    <div className="text-gray-400 text-xs">Contract Health Score</div>
                    <div className="text-xs font-bold mt-0.5" style={{ color: hcFull }}>{hs.label}</div>
                    <div className="text-gray-600 text-xs">(100 = perfectly protected)</div>
                  </div>
                </div>
              </div>
              {/* Industry sensitivity badge */}
              <div className="mt-3 flex items-center gap-2 flex-wrap">
                <span className="text-gray-500 text-xs">Industry Sensitivity:</span>
                <span className="px-2 py-0.5 rounded-full text-xs font-bold"
                  style={{ background: ip.sensitivity === 'HIGH' ? '#F1666722' : '#F7976722', color: ip.sensitivity === 'HIGH' ? '#F16667' : '#F79767', border: `1px solid ${ip.sensitivity === 'HIGH' ? '#F16667' : '#F79767'}44` }}>
                  {ip.sensitivity} — {result.industry}
                </span>
                {(ip.boosted_nodes || []).map((n, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-full text-xs bg-gray-800 text-gray-400 border border-gray-700">
                    ⚡ {n.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>

            {/* ── KPI ROW ── */}
            <div className="grid grid-cols-5 gap-3">
              {[
                { label: 'Force Majeure Invocation Risk', val: fmtP(lr.fm_invocation_prob), sub: 'Probability clause triggers', color: 'text-red-400', border: 'border-red-900', bg: 'bg-red-950/20' },
                { label: 'Project Delay Risk',  val: fmtP(lr.project_delay_prob), sub: 'Schedule slippage probability', color: 'text-orange-400', border: 'border-orange-900', bg: 'bg-orange-950/20' },
                { label: 'Expected Loss',        val: fmt(expLoss), sub: `${exposurePct}% of contract value`, color: 'text-yellow-400', border: 'border-yellow-900', bg: 'bg-yellow-950/20' },
                { label: 'Stress Test Reserve',       val: fmt(fe.p95_loss_usd||0), sub: '1-in-20 stress scenario loss', color: 'text-red-400', border: 'border-red-900', bg: 'bg-red-950/20' },
                { label: 'Clause Protection',    val: `${covered}/14`, sub: `${missing.length} events unprotected`, color: covered>=12?'text-green-400':covered>=8?'text-yellow-400':'text-red-400', border: covered>=12?'border-green-900':covered>=8?'border-yellow-900':'border-red-900', bg: covered>=12?'bg-green-950/20':covered>=8?'bg-yellow-950/20':'bg-red-950/20' },
              ].map((k, i) => (
                <div key={i} className={`rounded-xl p-3 border ${k.border} ${k.bg} text-center`}>
                  <div className={`text-lg font-bold ${k.color}`}>{k.val}</div>
                  <div className="text-gray-400 text-xs font-medium mt-0.5">{k.label}</div>
                  <div className="text-gray-600 text-xs mt-0.5">{k.sub}</div>
                </div>
              ))}
            </div>

            {/* ── TIMELINE + OUTCOMES ── */}
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="text-white text-sm font-semibold">12-Month Force Majeure Exposure Forecast</h4>
                  <span className="text-gray-500 text-xs">Loss ($M) + Force Majeure Risk (%)</span>
                </div>
                <p className="text-gray-500 text-xs mb-3">Projected monthly financial exposure and Force Majeure risk probability over the next 12 months based on live global events</p>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={timelineData}>
                    <defs>
                      <linearGradient id="lossArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F79767" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#F79767" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 10 }} />
                    <YAxis yAxisId="left" tick={{ fill: '#6b7280', fontSize: 10 }} tickFormatter={v => `$${v}M`} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6b7280', fontSize: 10 }} tickFormatter={v => `${v}%`} domain={[0, 100]} />
                    <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 11 }}
                      formatter={(v, n) => n === 'loss' || n === 'p95' ? [`$${v}M`, n === 'loss' ? 'Expected Loss' : 'Stress Test Loss'] : [`${v}%`, 'FM Risk']} />
                    <Legend wrapperStyle={{ fontSize: 10, color: '#9CA3AF' }} />
                    <Line yAxisId="left" type="monotone" dataKey="loss" stroke="#F79767" strokeWidth={2} dot={false} name="Expected Loss ($M)" />
                    <Line yAxisId="left" type="monotone" dataKey="p95" stroke="#9063CD" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Stress Test Loss ($M)" />
                    <Line yAxisId="right" type="monotone" dataKey="risk" stroke="#F16667" strokeWidth={2} dot={false} name="Force Majeure Risk (%)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <h4 className="text-white text-sm font-semibold mb-1">Live Outcome Probabilities</h4>
                <p className="text-gray-500 text-xs mb-3">Real-time probabilities driven by live global event feeds + {result.industry} industry boosts</p>
                <div className="space-y-3">
                  {outcomeData.map((d, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400">{d.name}</span>
                        <span className="font-bold" style={{ color: d.fill }}>{d.value}%</span>
                      </div>
                      <div className="bg-gray-900 rounded-full h-3 overflow-hidden">
                        <div className="h-3 rounded-full transition-all"
                          style={{ width: `${d.value}%`, background: `linear-gradient(90deg, ${d.fill}88, ${d.fill})` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* ── STRESS TEST ── */}
            {stressData.length > 0 && (
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="text-white text-sm font-semibold">Stress Test Scenarios</h4>
                  <span className="text-gray-500 text-xs">{result.industry} industry · {result.jurisdiction}</span>
                </div>
                <p className="text-gray-500 text-xs mb-4">How this contract performs under 5 different Force Majeure stress scenarios — FM Risk % and expected financial loss</p>
                <div className="space-y-3">
                  {stressData.map((s, i) => (
                    <div key={i} className="grid grid-cols-12 items-center gap-3 p-2 bg-gray-900 rounded-lg">
                      <span className="col-span-1 w-3 h-3 rounded-full shrink-0" style={{ background: s.color }} />
                      <span className="col-span-2 text-gray-300 text-xs font-medium">{s.name}</span>
                      <div className="col-span-7 bg-gray-700 rounded-full h-4 overflow-hidden">
                        <div className="h-4 rounded-full flex items-center justify-end pr-2 transition-all"
                          style={{ width: `${s.risk}%`, background: `linear-gradient(90deg, ${s.color}88, ${s.color})` }}>
                          <span className="text-white text-xs font-bold">{s.risk}%</span>
                        </div>
                      </div>
                      <span className="col-span-2 text-gray-400 text-xs text-right font-medium">${s.loss}M</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── LIVE EVENTS + CLAUSE GAPS side by side ── */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <h4 className="text-white text-sm font-semibold mb-1">Live Global Events Affecting Contract</h4>
                <p className="text-gray-500 text-xs mb-3">Real-time events from global monitoring feeds that are directly impacting this contract's risk profile</p>
                {liveEvents.length === 0 ? (
                  <div className="text-gray-500 text-xs text-center py-4">No high-impact events detected currently</div>
                ) : (
                  <div className="space-y-2">
                    {liveEvents.slice(0, 6).map((ev, i) => (
                      <div key={i} className="flex items-start gap-2 p-2 bg-gray-900 rounded-lg">
                        <span className="text-sm">{ev.type === 'war' ? '⚔️' : ev.type === 'earthquake' ? '🌍' : ev.type === 'pandemic' ? '🦠' : ev.type === 'sanctions' ? '🚫' : '⚡'}</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-gray-200 text-xs font-medium truncate">{ev.title || ev.description || ev.type}</div>
                          <div className="text-gray-500 text-xs">{ev.location || ev.region || '—'} · Severity: {ev.severity || ev.magnitude || 'Medium'}</div>
                        </div>
                        <span className="shrink-0 text-xs px-1.5 py-0.5 rounded font-bold"
                          style={{ background: '#F1666722', color: '#F16667', border: '1px solid #F1666744' }}>
                          LIVE
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <h4 className="text-white text-sm font-semibold mb-1">Force Majeure Clause Gap Analysis</h4>
                <p className="text-gray-500 text-xs mb-3">Events your Force Majeure clause does NOT cover — these represent unprotected financial exposure</p>
                <div className="grid grid-cols-2 gap-1.5 mb-3">
                  {FM_EVENT_CATEGORIES.map(ev => {
                    const isCovered = (clauseStatus.covered_events || []).includes(ev);
                    return (
                      <div key={ev} className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs ${isCovered ? 'bg-green-950/30 text-green-400' : 'bg-red-950/30 text-red-400'}`}>
                        <span>{isCovered ? '✓' : '✗'}</span>
                        <span className="capitalize truncate">{ev.replace(/_/g, ' ')}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="flex gap-4 text-xs border-t border-gray-700 pt-2">
                  <span className="text-green-400">✓ {covered} Protected</span>
                  <span className="text-red-400">✗ {14 - covered} Exposed</span>
                  <span className="text-gray-400 ml-auto">{Math.round(covered/14*100)}% coverage</span>
                </div>
              </div>
            </div>

            {/* ── RECOMMENDED ACTIONS ── */}
            {(result.recommended_actions || []).length > 0 && (
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
                <h4 className="text-white text-sm font-semibold mb-1">AI-Recommended Actions</h4>
                <p className="text-gray-500 text-xs mb-3">Priority actions specific to {result.industry} industry in {result.jurisdiction} jurisdiction based on current live risk profile</p>
                <div className="grid grid-cols-2 gap-2">
                  {result.recommended_actions.map((a, i) => {
                    const pc = { CRITICAL: '#F16667', HIGH: '#F79767', MEDIUM: '#FFD86E', LOW: '#68BC00' }[a.priority] || '#6b7280';
                    return (
                      <div key={i} className="flex items-start gap-3 p-3 bg-gray-900 rounded-xl border border-gray-800">
                        <span className="text-xs px-2 py-0.5 rounded-full font-bold shrink-0 mt-0.5"
                          style={{ background: pc + '22', color: pc, border: `1px solid ${pc}44` }}>{a.priority}</span>
                        <div>
                          <div className="text-gray-200 text-xs font-semibold">{a.action}</div>
                          <div className="text-gray-500 text-xs mt-0.5 leading-relaxed">{a.description}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: MULTI-AGENT CLAUSE NEGOTIATION
// ═══════════════════════════════════════════════════════════════════════════════
const MultiAgentNegotiationTab = ({ contract, prediction }) => {
  const ctx = contract;

  // Auto-derive defaults from contract + prediction
  const topDriver = useMemo(() => {
    const drivers = prediction?.top_risk_drivers || [];
    if (!drivers.length) return 'war';
    const top = drivers[0]?.node || drivers[0]?.factor || '';
    // Map Bayesian node names to human-readable dispute events
    const nodeMap = { war:'war', trade_sanctions:'sanctions', pandemic:'pandemic',
      epidemic:'pandemic', natural_disaster:'natural_disaster', cyber_warfare:'cyber_attack',
      port_closure:'port_closure', factory_shutdown:'factory_shutdown',
      flood:'flood', drought:'drought', energy_crisis:'energy_crisis',
      commodity_shock:'commodity_shock', government_lockdown:'government_lockdown' };
    return nodeMap[top] || top.replace(/_/g,' ') || 'war';
  }, [prediction]);

  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');
  const [form, setForm] = useState({
    buyer_jurisdiction: ctx.jurisdiction || 'EU',
    seller_jurisdiction: ctx.project_location || ctx.supplier_locations?.split(',')[0]?.trim() || 'Ukraine',
    dispute_event: topDriver,
    rounds: 3,
  });
  // Sync form when prediction/contract data becomes available
  useEffect(() => {
    setForm(f => ({
      ...f,
      buyer_jurisdiction: ctx.jurisdiction || f.buyer_jurisdiction,
      seller_jurisdiction: ctx.project_location || ctx.supplier_locations?.split(',')[0]?.trim() || f.seller_jurisdiction,
      dispute_event: topDriver !== 'war' ? topDriver : f.dispute_event,
    }));
  }, [ctx.jurisdiction, ctx.project_location, topDriver]);

  const upd = k => e => setForm(f=>({...f,[k]:e.target.value}));
  const fmtP = v => v!==undefined ? `${Math.round(v*100)}%` : '—';
  const agentColors = {buyer:'#4C8EDA',seller:'#F79767',insurer:'#9063CD'};

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      if (!ctx.contract_text.trim()) { setError('No contract text — go to the Risk Predictor tab and run analysis first.'); setLoading(false); return; }
      setResult(await runMultiAgentNegotiate({
        clause_text: ctx.contract_text.trim(),
        contract_value: parseFloat(ctx.contract_value) || 0,
        ...form, rounds: parseInt(form.rounds),
      }));
    }
    catch(e){ setError(e?.response?.data?.error||e.message); }
    finally{ setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-yellow-900">
        <p className="text-gray-400 text-sm mb-3">Simulates Buyer, Seller, and Insurer agents negotiating the Force Majeure clause over multiple rounds.</p>
        <div className="grid grid-cols-4 gap-3 mb-3">
          {[['buyer_jurisdiction','Buyer Jurisdiction'],['seller_jurisdiction','Seller Jurisdiction'],['dispute_event','Dispute Event'],['rounds','Rounds']].map(([k,label])=>(
            <div key={k}>
              <label className="text-xs text-gray-400 mb-1 block">{label}</label>
              <input value={form[k]} onChange={upd(k)} className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-xs text-gray-200"/>
            </div>
          ))}
        </div>
        {ctx.contract_value && <p className="text-gray-500 text-xs mb-3">Contract value: ${Number(ctx.contract_value).toLocaleString()}</p>}
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 px-5 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50">
          <Users size={14}/> {loading?'Negotiating…':'Run Negotiation'}
        </button>
        {error && <div className="mt-2 text-red-400 text-xs">{error}</div>}
      </div>
      {result && (
        <div className="space-y-5">

          {/* ── Hero KPIs ── */}
          <div className="grid grid-cols-4 gap-3">
            {[
              {label:'Original Force Majeure Strength',v:fmtP(result.original_strength),sub:'Before negotiation',color:'text-red-400',bg:'border-red-900'},
              {label:'Final Force Majeure Strength',   v:fmtP(result.final_strength),   sub:'After all rounds', color:'text-green-400',bg:'border-green-900'},
              {label:'Clause Improvement',  v:`${result.improvement_pct>0?'+':''}${result.improvement_pct}%`, sub:'Net strength gain', color:result.improvement_pct>0?'text-green-400':'text-red-400',bg:'border-yellow-900'},
              {label:'Consensus Reached',   v:result.consensus_reached?'YES':'NO', sub:`${(result.negotiation_rounds||[]).length} rounds completed`,color:result.consensus_reached?'text-green-400':'text-red-400',bg:result.consensus_reached?'border-green-900':'border-red-900'},
            ].map((k,i)=>(
              <div key={i} className={`bg-gray-800 rounded-xl p-4 border ${k.bg} text-center`}>
                <div className={`text-3xl font-bold ${k.color}`}>{k.v}</div>
                <div className="text-gray-300 text-xs font-medium mt-1">{k.label}</div>
                <div className="text-gray-500 text-xs mt-0.5">{k.sub}</div>
              </div>
            ))}
          </div>

          {/* ── Strength Progression Bar ── */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">📈 Clause Strength Progression</div>
            <div className="flex items-end gap-3">
              {[{label:'Start', val:result.original_strength, color:'#ef4444'}, ...(result.negotiation_rounds||[]).map((r,i)=>({label:`Round ${r.round}`,val:r.clause_strength_after,color:i===((result.negotiation_rounds||[]).length-1)?'#22c55e':'#facc15'}))].map((pt,i)=>(
                <div key={i} className="flex flex-col items-center flex-1">
                  <div className="text-xs font-bold mb-1" style={{color:pt.color}}>{Math.round(pt.val*100)}%</div>
                  <div className="w-full rounded-t-sm" style={{height:`${Math.max(8, pt.val*80)}px`, background:pt.color, opacity:0.85}}/>
                  <div className="text-gray-500 text-xs mt-1">{pt.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Agent Positions ── */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-1">🤝 Agent Alignment Matrix</div>
            <div className="text-gray-500 text-xs mb-3">How each agent's risk tolerance shapes their negotiating position</div>
            <div className="grid grid-cols-5 gap-2">
              {(result.agents||[]).map((a,i)=>{
                const colors = {buyer:'#4C8EDA',seller:'#F79767',insurer:'#9063CD',legal:'#22c55e',finance:'#facc15'};
                const c = colors[a.role]||'#888';
                return (
                  <div key={i} className="rounded-lg p-3 bg-gray-900 border border-gray-700 text-center">
                    <div className="text-xs font-bold mb-1" style={{color:c}}>{a.name}</div>
                    <div className="text-gray-400 text-xs mb-2">{a.objective}</div>
                    <div className="text-gray-500 text-xs mb-1">Risk Tolerance</div>
                    <div className="w-full bg-gray-700 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full" style={{width:`${a.risk_tolerance*100}%`,background:c}}/>
                    </div>
                    <div className="text-xs mt-1" style={{color:c}}>{Math.round(a.risk_tolerance*100)}%</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Round-by-Round ── */}
          {(result.negotiation_rounds||[]).map((round,ri)=>(
            <div key={ri} className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
              {/* Round header */}
              <div className="flex items-center justify-between px-4 py-3 bg-gray-750 border-b border-gray-700" style={{background:'#1e2533'}}>
                <div className="flex items-center gap-3">
                  <span className="bg-yellow-600 text-white text-xs font-bold px-2 py-0.5 rounded">ROUND {round.round}</span>
                  <span className="text-gray-300 text-sm font-medium">{round.round===1?'Opening Positions':round.round===2?'Escalation & Counter-Proposals':'Final Positions & Convergence'}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-gray-500 text-xs">Clause strength after:</span>
                  <span className="text-green-400 font-bold text-sm">{fmtP(round.clause_strength_after)}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${round.round_outcome==='agreement'?'bg-green-900 text-green-400':'bg-blue-900 text-blue-400'}`}>
                    {round.round_outcome==='agreement'?'✓ AGREEMENT':'⟳ ONGOING'}
                  </span>
                </div>
              </div>

              {/* Proposals */}
              <div className="p-4 space-y-3">
                {(round.proposals||[]).map((p,pi)=>{
                  const colors = {buyer:'#4C8EDA',seller:'#F79767',insurer:'#9063CD',legal:'#22c55e',finance:'#facc15'};
                  const c = colors[p.role]||'#888';
                  const isAccepted = p.agent===round.accepted_proposal?.agent;
                  return (
                    <div key={pi} className="rounded-lg bg-gray-900 border border-gray-700 overflow-hidden" style={{borderLeft:`3px solid ${c}`}}>
                      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-800">
                        <span className="text-xs font-bold" style={{color:c}}>{p.agent}</span>
                        <span className="text-xs text-gray-600">·</span>
                        <span className="text-xs text-gray-400 uppercase tracking-wide">{p.stance?.replace(/_/g,' ')}</span>
                        {p.demand && <span className="ml-auto text-xs text-gray-500 italic truncate max-w-xs">"{p.demand}"</span>}
                        {isAccepted && <span className="ml-2 text-xs bg-green-900 text-green-400 px-2 py-0.5 rounded font-bold flex-shrink-0">✓ ACCEPTED</span>}
                      </div>
                      <div className="px-3 py-2">
                        <p className="text-gray-300 text-xs leading-relaxed mb-2">{p.position}</p>
                        {p.clause_fragment && (
                          <div className="bg-gray-800 border border-gray-700 rounded p-2 mt-1">
                            <div className="text-gray-500 text-xs mb-1 font-medium">📝 Proposed clause language:</div>
                            <div className="text-blue-200 text-xs leading-relaxed italic">"{p.clause_fragment}"</div>
                          </div>
                        )}
                        {p.concession && (
                          <div className="mt-2 text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-900 rounded px-2 py-1">
                            🤝 Concession: {p.concession}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Mediator consensus summary */}
                {round.consensus_summary && (
                  <div className="mt-2 p-3 rounded-lg bg-indigo-900/20 border border-indigo-700">
                    <div className="text-indigo-400 text-xs font-bold mb-1">⚖️ MEDIATOR SUMMARY</div>
                    <div className="text-indigo-200 text-xs leading-relaxed">{round.consensus_summary}</div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* ── Negotiated Terms Summary ── */}
          {result.negotiated_terms && (
            <div className="bg-gray-800 rounded-xl p-4 border border-yellow-800">
              <div className="text-yellow-400 text-sm font-semibold mb-3">📋 Key Negotiated Terms — Summary Table</div>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(result.negotiated_terms).map(([k,v],i)=>(
                  <div key={i} className="flex items-start gap-2 bg-gray-900 rounded-lg px-3 py-2">
                    <span className="text-gray-500 text-xs w-32 flex-shrink-0">{k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</span>
                    <span className="text-gray-200 text-xs">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Final Negotiated Clause ── */}
          <div className="bg-gray-800 rounded-xl border border-green-800 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 bg-green-900/20 border-b border-green-800">
              <CheckCircle size={14} className="text-green-400"/>
              <span className="text-green-400 text-sm font-bold">FINAL NEGOTIATED FORCE MAJEURE CLAUSE</span>
              <span className="ml-auto text-xs text-gray-500">Legally synthesized from all {(result.negotiation_rounds||[]).length} rounds</span>
            </div>
            <div className="p-4">
              <pre className="text-gray-300 text-xs leading-relaxed whitespace-pre-wrap font-sans">{result.final_clause}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: SUPPLY CHAIN RISK MAP
// ═══════════════════════════════════════════════════════════════════════════════
const SupplyChainTab = ({ contract }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData]       = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      setData(await getSupplyChainMap({
        contract_text:      contract?.contract_text || '',
        project_location:   contract?.project_location || '',
        supplier_locations: contract?.supplier_locations || '',
        jurisdiction:       contract?.jurisdiction || '',
        industry:           contract?.industry || '',
      }));
    }
    catch(e){ console.error(e); }
    finally{ setLoading(false); }
  };
  useEffect(()=>{ load(); }, [contract?.contract_text, contract?.project_location]);

  const hasContract = data?.contract_analysis?.has_contract;
  const ca = data?.contract_analysis || {};
  const routeBarData = (data?.trade_routes||[]).map(r=>({
    name: r.name?.replace(' Route','').replace(' Canal',''),
    risk: Math.round(r.live_risk*100),
    color: r.contract_relevant ? (r.live_risk>0.65?'#F16667':r.live_risk>0.4?'#F79767':'#68BC00') : '#374151',
    relevant: r.contract_relevant,
  }));

  const fmtUSD = v => v >= 1e9 ? `$${(v/1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v/1e6).toFixed(0)}M` : `$${v.toLocaleString()}`;
  const verdictColor = {'CRITICAL':'text-red-400','HIGH':'text-orange-400','MEDIUM':'text-yellow-400','LOW':'text-green-400'};
  const verdictBorder = {'CRITICAL':'border-red-800','HIGH':'border-orange-800','MEDIUM':'border-yellow-800','LOW':'border-green-800'};

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-300 text-sm font-medium">Supply Chain Disruption Intelligence</p>
          <p className="text-gray-500 text-xs mt-0.5">
            {hasContract ? `Analyzing YOUR contract's supply chain exposure across ${ca.relevant_route_count} relevant routes` : 'Showing global routes — paste a contract in Tab 1 to see YOUR exposure'}
          </p>
        </div>
        <button onClick={load} disabled={loading} className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-300 transition">
          <RefreshCw size={11} className={loading?'animate-spin':''}/> Refresh
        </button>
      </div>

      {loading && <div className="text-gray-500 text-center py-8 text-sm animate-pulse">Analyzing supply chain exposure…</div>}

      {data && (
        <>
          {/* ── Contract Exposure Hero (only when contract is pasted) ── */}
          {hasContract && (
            <div className={`bg-gray-800 rounded-xl p-4 border-2 ${verdictBorder[ca.supply_chain_verdict]||'border-gray-700'}`}>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">YOUR CONTRACT'S SUPPLY CHAIN VERDICT</div>
                  <div className={`text-3xl font-black ${verdictColor[ca.supply_chain_verdict]}`}>{ca.supply_chain_verdict}</div>
                  <div className="text-gray-400 text-xs mt-1">Force Majeure probability boost from supply chain: <span className="text-orange-400 font-bold">+{Math.round((ca.fm_probability_boost||0)*100)}%</span></div>
                </div>
                <div className="text-right">
                  <div className="text-gray-500 text-xs">Daily trade at risk</div>
                  <div className="text-2xl font-bold text-red-400">{fmtUSD(ca.total_daily_trade_at_risk_usd||0)}</div>
                  <div className="text-gray-500 text-xs mt-1">{ca.relevant_route_count} routes · {ca.active_hub_count} supplier hubs</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 mt-2">
                {ca.disrupted_relevant_routes?.length > 0 && (
                  <div className="bg-red-900/20 border border-red-800 rounded-lg p-2">
                    <div className="text-red-400 text-xs font-bold mb-1">🔴 DISRUPTED — Affecting YOUR contract</div>
                    {ca.disrupted_relevant_routes.map((r,i)=><div key={i} className="text-red-300 text-xs">• {r}</div>)}
                  </div>
                )}
                {ca.elevated_relevant_routes?.length > 0 && (
                  <div className="bg-orange-900/20 border border-orange-800 rounded-lg p-2">
                    <div className="text-orange-400 text-xs font-bold mb-1">🟠 ELEVATED — Monitor closely</div>
                    {ca.elevated_relevant_routes.map((r,i)=><div key={i} className="text-orange-300 text-xs">• {r}</div>)}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Global KPIs ── */}
          <div className="grid grid-cols-4 gap-3">
            {[
              {label:'Total Routes Monitored', v:data.summary?.total_routes,           color:'text-blue-400'},
              {label:'Disrupted (>65%)',        v:data.summary?.disrupted_routes,        color:'text-red-400'},
              {label:'Elevated (40–65%)',       v:data.summary?.elevated_routes,         color:'text-yellow-400'},
              {label:'Avg Global Disruption',   v:`${data.summary?.avg_disruption_pct}%`,color:'text-orange-400'},
            ].map((k,i)=>(
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700 text-center">
                <div className={`text-2xl font-bold ${k.color}`}>{k.v}</div>
                <div className="text-gray-500 text-xs mt-1">{k.label}</div>
              </div>
            ))}
          </div>

          {/* ── Bar Chart — contract-relevant routes highlighted ── */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="text-gray-300 text-sm font-semibold">Trade Route Disruption Risk</div>
              {hasContract && <div className="flex items-center gap-3 text-xs text-gray-500">
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm inline-block bg-red-500"/> Active in YOUR contract</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm inline-block bg-gray-600"/> Not in your contract</span>
              </div>}
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={routeBarData} barSize={30}>
                <XAxis dataKey="name" tick={{fill:'#6b7280',fontSize:10}}/>
                <YAxis tick={{fill:'#6b7280',fontSize:10}} tickFormatter={v=>`${v}%`}/>
                <Tooltip contentStyle={{background:'#111827',border:'1px solid #374151',color:'#fff',fontSize:11}}
                  formatter={(v,n,p)=>[`${v}% ${p.payload.relevant?'⚡ Active in YOUR contract':''}`, 'Disruption Risk']}/>
                <Bar dataKey="risk" radius={[4,4,0,0]}>
                  {routeBarData.map((r,i)=><Cell key={i} fill={r.color}/>)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* ── Route Cards ── */}
          <div className="grid grid-cols-2 gap-3">
            {(data.trade_routes||[]).map((r,i)=>(
              <div key={i} className={`bg-gray-800 rounded-xl p-4 border ${r.contract_relevant?'border-yellow-600':'border-gray-700'}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-gray-200 text-sm font-semibold">{r.name}</span>
                  <div className="flex items-center gap-2">
                    {r.contract_relevant && (
                      <div className="flex items-center gap-1 bg-yellow-600/20 border border-yellow-600 rounded px-1.5 py-0.5">
                        <Zap size={9} className="text-yellow-400"/><span className="text-yellow-400 text-xs font-bold">YOUR CONTRACT</span>
                      </div>
                    )}
                    <span className="text-xs px-2 py-0.5 rounded font-bold" style={{background:r.color+'22',color:r.color}}>{r.status}</span>
                  </div>
                </div>
                <div className="text-gray-500 text-xs mb-2">{r.from} → {r.to}</div>
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div className="h-2 rounded-full transition-all" style={{width:`${r.disruption_pct}%`,background:r.color}}/>
                </div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">Risk: <span style={{color:r.color}} className="font-bold">{r.disruption_pct}%</span></span>
                  <span className="text-gray-500">Daily: {fmtUSD(r.cargo_value_bday)}</span>
                </div>
                {r.contract_relevant && r.matched_keywords?.length>0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {r.matched_keywords.map((kw,ki)=>(
                      <span key={ki} className="text-xs bg-yellow-900/30 border border-yellow-800 text-yellow-300 px-1.5 py-0.5 rounded">{kw}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* ── Supplier Hub Risk ── */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-1">Supplier Hub Risk</div>
            <div className="text-gray-500 text-xs mb-3">
              {hasContract ? `${ca.active_hub_count} hubs detected in your contract (highlighted)` : 'Global supplier hubs — paste contract to see your active hubs'}
            </div>
            <div className="grid grid-cols-3 gap-2">
              {(data.supplier_hubs||[]).map((hub,i)=>{
                const rc = hub.risk>0.6?'#F16667':hub.risk>0.35?'#F79767':'#68BC00';
                return (
                  <div key={i} className={`p-3 rounded-lg border ${hub.contract_active?'bg-yellow-900/10 border-yellow-700':'bg-gray-900 border-gray-700'}`}>
                    <div className="flex items-center justify-between mb-0.5">
                      <div className="text-gray-200 text-xs font-medium truncate">{hub.name}</div>
                      {hub.contract_active && <Zap size={10} className="text-yellow-400 flex-shrink-0"/>}
                    </div>
                    <div className="text-gray-500 text-xs mb-1">{hub.type}</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full" style={{width:`${Math.round(hub.risk*100)}%`,background:rc}}/>
                      </div>
                      <span className="text-xs font-bold" style={{color:rc}}>{Math.round(hub.risk*100)}%</span>
                    </div>
                    {hub.contract_active && hub.matched_on?.length>0 && (
                      <div className="mt-1 text-yellow-400 text-xs">via: {hub.matched_on.join(', ')}</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE-2 TAB: DYNAMIC BAYESIAN PRIORS
// ═══════════════════════════════════════════════════════════════════════════════
const DynamicPriorsTab = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(null);

  const load = async () => {
    setLoading(true); setError('');
    try { setData(await getDynamicPriors()); }
    catch (e) { setError(e.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const nodeLabels = {
    war:'War / Armed Conflict', trade_sanctions:'Trade Sanctions', pandemic:'Pandemic / Epidemic',
    natural_disaster:'Natural Disaster', cyber_warfare:'Cyber Warfare', port_closure:'Port Closure',
    factory_shutdown:'Factory Shutdown', energy_crisis:'Energy Crisis', flood:'Flood',
    drought:'Drought', earthquake:'Earthquake', government_lockdown:'Government Lockdown',
    financial_market_crash:'Financial Market Crash', economic_collapse:'Economic Collapse',
    political_coup:'Political Coup', terrorism:'Terrorism', nuclear_incident:'Nuclear Incident',
    labor_shortage:'Labor Shortage', supplier_failure:'Supplier Failure', transport_shutdown:'Transport Shutdown',
    commodity_shock:'Commodity Shock', currency_volatility:'Currency Volatility',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Dynamic Bayesian Prior Update</h2>
          <p className="text-gray-400 text-sm mt-1">Live global events automatically shift the probability priors of each risk node in real-time</p>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-medium transition disabled:opacity-50">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Live
        </button>
      </div>
      {error && <div className="bg-red-900/40 border border-red-700 rounded-lg p-3 text-red-300 text-sm">{error}</div>}
      {loading && <div className="text-center text-gray-400 py-12 animate-pulse">Fetching live events and updating priors…</div>}

      {data && (
        <>
          {/* ── KPIs ── */}
          <div className="grid grid-cols-4 gap-3">
            {[
              {label:'Live Events Fetched',  v:data.live_events_count,  sub:'from global sources', color:'text-blue-400',  icon:'📡'},
              {label:'Bayesian Nodes Boosted',v:data.nodes_boosted,      sub:'of 35 nodes updated',  color:'text-orange-400',icon:'⚡'},
              {label:'Top Mover Node',        v:data.top_movers?.[0]?.node?.replace(/_/g,' ')||'—', sub:'biggest prior shift', color:'text-yellow-400',icon:'📈'},
              {label:'Max Prior Boost',       v:data.top_movers?.[0]?`+${(data.top_movers[0].delta*100).toFixed(1)}%`:'—', sub:'probability increase', color:'text-red-400', icon:'🔺'},
            ].map((k,i)=>(
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700">
                <div className="text-lg mb-1">{k.icon}</div>
                <div className={`text-xl font-bold ${k.color}`}>{k.v}</div>
                <div className="text-gray-300 text-xs font-medium mt-0.5">{k.label}</div>
                <div className="text-gray-500 text-xs">{k.sub}</div>
              </div>
            ))}
          </div>

          {/* ── What This Means ── */}
          <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-4">
            <div className="text-blue-400 text-sm font-bold mb-1">📖 What is a Bayesian Prior?</div>
            <p className="text-blue-200 text-xs leading-relaxed">
              Each of the 35 risk nodes (war, flood, sanctions, etc.) has a <strong>base probability</strong> set from historical data.
              When a live event is detected (e.g. "M6.3 Earthquake in Chile"), the engine <strong>boosts that node's prior</strong> — making
              the Bayesian network more likely to predict Force Majeure risk from that event type. The table below shows which nodes were boosted today,
              by how much, and which live news events triggered the boost.
            </p>
          </div>

          {/* ── Prior Movers — rich cards ── */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <div className="text-gray-300 text-sm font-semibold">Live Prior Movers — Today's Updates</div>
              <div className="text-gray-500 text-xs">Click a row to see triggering events</div>
            </div>

            {(data.top_movers||[]).length === 0 && (
              <div className="px-4 py-8 text-center text-gray-500 text-sm">No prior updates today — no matching live events detected.</div>
            )}

            <div className="divide-y divide-gray-700">
              {(data.top_movers||[]).map((m,i)=>{
                const isOpen = expanded === i;
                const baseP = m.base_prior * 100;
                const updP  = m.updated_prior * 100;
                const deltaP = m.delta * 100;
                const barColor = deltaP > 15 ? '#F16667' : deltaP > 8 ? '#F79767' : '#facc15';
                return (
                  <div key={i}>
                    <div className="px-4 py-3 hover:bg-gray-750 cursor-pointer" style={{background: isOpen?'#1e2533':undefined}}
                      onClick={()=>setExpanded(isOpen?null:i)}>
                      <div className="flex items-center gap-4">
                        {/* Node name */}
                        <div className="w-44 flex-shrink-0">
                          <div className="text-gray-200 text-xs font-semibold">{nodeLabels[m.node]||m.node.replace(/_/g,' ')}</div>
                          <div className="text-gray-500 text-xs font-mono">{m.node}</div>
                        </div>
                        {/* Before → After visual */}
                        <div className="flex-1 flex items-center gap-3">
                          <span className="text-gray-400 text-xs w-10 text-right">{baseP.toFixed(1)}%</span>
                          <div className="flex-1 relative h-4 bg-gray-700 rounded-full overflow-hidden">
                            <div className="absolute left-0 top-0 h-full rounded-full opacity-40" style={{width:`${baseP}%`,background:'#6b7280'}}/>
                            <div className="absolute left-0 top-0 h-full rounded-full transition-all" style={{width:`${updP}%`,background:barColor}}/>
                          </div>
                          <span className="font-bold text-xs w-10" style={{color:barColor}}>{updP.toFixed(1)}%</span>
                        </div>
                        {/* Delta badge */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-xs font-bold px-2 py-0.5 rounded" style={{background:barColor+'22',color:barColor}}>
                            +{deltaP.toFixed(2)}%
                          </span>
                          <span className="text-gray-500 text-xs">+{m.pct_change}% change</span>
                          <span className="text-gray-600 text-xs">{isOpen?'▲':'▼'}</span>
                        </div>
                      </div>
                    </div>
                    {/* Expanded: triggering events */}
                    {isOpen && (
                      <div className="px-4 pb-3 bg-gray-850" style={{background:'#161d2a'}}>
                        <div className="text-gray-500 text-xs mb-2 mt-1 font-medium">🗞️ Live events that triggered this prior boost:</div>
                        {(m.source_events||[]).length === 0
                          ? <div className="text-gray-600 text-xs">No specific events recorded.</div>
                          : (m.source_events||[]).map((ev,ei)=>(
                            <div key={ei} className="flex items-start gap-3 mb-2 bg-gray-800 rounded-lg p-2 border border-gray-700">
                              <div className="flex-1">
                                <div className="text-gray-200 text-xs">{typeof ev === 'object' ? ev.title : ev}</div>
                                {typeof ev === 'object' && ev.source && (
                                  <div className="text-gray-500 text-xs mt-0.5">Source: {ev.source}</div>
                                )}
                              </div>
                              {typeof ev === 'object' && ev.risk_score !== undefined && (
                                <div className="text-xs font-bold flex-shrink-0" style={{color:riskColor(ev.risk_score)}}>
                                  Risk: {(ev.risk_score*100).toFixed(0)}%
                                </div>
                              )}
                            </div>
                          ))
                        }
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── All base priors mini grid ── */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">All 35-Node Base Priors vs Live Priors</div>
            <div className="grid grid-cols-4 gap-2">
              {Object.entries(data.base_priors||{}).map(([node, base],i)=>{
                const upd = data.prior_updates?.[node]?.updated_prior || base;
                const delta = upd - base;
                const rc = delta > 0.1 ? '#F16667' : delta > 0.05 ? '#F79767' : delta > 0 ? '#facc15' : '#6b7280';
                return (
                  <div key={i} className="bg-gray-900 rounded-lg px-2 py-1.5 border border-gray-700">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400 text-xs truncate">{node.replace(/_/g,' ')}</span>
                      {delta > 0 && <span className="text-xs font-bold ml-1 flex-shrink-0" style={{color:rc}}>↑</span>}
                    </div>
                    <div className="flex items-center gap-1 mt-1">
                      <div className="flex-1 bg-gray-700 rounded-full h-1">
                        <div className="h-1 rounded-full" style={{width:`${Math.min(100,upd*100)}%`,background:rc}}/>
                      </div>
                      <span className="text-xs font-bold" style={{color:rc}}>{(upd*100).toFixed(0)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ── Custom ReactFlow node types for the cascade graph ──────────────────────
const CascadeNodeRenderer = ({ data }) => {
  const p = data.probability || 0;
  const pct = Math.round(p * 100);
  const barColor = p > 0.6 ? '#F16667' : p > 0.35 ? '#F79767' : '#68BC00';
  return (
    <>
      <Handle type="target" position={Position.Left} style={{ background: '#555', width: 7, height: 7, border: '1px solid #888' }} />
      <div style={{ fontFamily: 'monospace', lineHeight: 1.3, userSelect: 'none' }}>
        {/* Icon + label row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
          <span style={{ fontSize: 14 }}>{data.icon || '●'}</span>
          <span style={{ fontSize: 10, fontWeight: 700, color: '#fff', letterSpacing: '0.02em' }}>
            {data.label}
          </span>
        </div>
        {/* Layer badge + probability */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <span style={{
            fontSize: 8, padding: '1px 5px', borderRadius: 4,
            background: 'rgba(255,255,255,0.15)', color: '#ddd', letterSpacing: '0.05em',
          }}>
            {data.layerLabel?.toUpperCase()}
          </span>
          <span style={{ fontSize: 11, fontWeight: 800, color: barColor }}>
            {pct}%
          </span>
        </div>
        {/* Probability bar */}
        <div style={{ background: 'rgba(0,0,0,0.35)', borderRadius: 3, height: 5, overflow: 'hidden' }}>
          <div style={{
            width: `${pct}%`, height: '100%',
            background: `linear-gradient(90deg, ${barColor}cc, ${barColor})`,
            borderRadius: 3,
            transition: 'width 0.4s ease',
          }} />
        </div>
        {/* Rank indicator */}
        {data.rank <= 3 && (
          <div style={{ marginTop: 3, fontSize: 8, color: '#fbbf24', fontWeight: 700 }}>
            {data.rank === 1 ? '▲ TOP RISK' : data.rank === 2 ? '▲ HIGH' : '↑ ELEVATED'}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#555', width: 7, height: 7, border: '1px solid #888' }} />
    </>
  );
};

const StageHeaderRenderer = ({ data }) => (
  <div style={{
    textAlign: 'center', fontFamily: 'monospace', fontSize: 9,
    fontWeight: 900, letterSpacing: '0.12em', userSelect: 'none',
  }}>
    {data.label}
  </div>
);

const CASCADE_NODE_TYPES = {
  cascadeNode: CascadeNodeRenderer,
  stageHeader: StageHeaderRenderer,
};

const CascadeGraphPanel = ({ nodes, edges }) => {
  const [fs, setFs] = useState(false);

  // Legend entries
  const LEGEND = [
    { color: '#c0392b', label: '>70% Critical' },
    { color: '#F16667', label: '50–70% High' },
    { color: '#F79767', label: '35–50% Medium' },
    { color: '#F1C40F', label: '20–35% Elevated' },
    { color: '#68BC00', label: '<20% Low' },
  ];

  const renderGraph = () => (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={CASCADE_NODE_TYPES}
      fitView
      fitViewOptions={{ padding: 0.15 }}
      minZoom={0.2}
      maxZoom={2.5}
      defaultEdgeOptions={{ type: 'smoothstep' }}
    >
      <Background color="#1e293b" variant="dots" gap={18} size={1.2} />
      <Controls showInteractive={false} style={{ background: '#1f2937', border: '1px solid #374151' }} />
      <MiniMap
        style={{ background: '#111827', border: '1px solid #374151' }}
        nodeColor={(n) => n.style?.background?.includes('linear') ? n.style.border?.match(/#[0-9a-f]{6}/i)?.[0] || '#4C8EDA' : '#4C8EDA'}
        maskColor="rgba(0,0,0,0.5)"
      />
      {/* Legend overlay */}
      <div style={{
        position: 'absolute', bottom: 60, left: 10, zIndex: 10,
        background: 'rgba(17,24,39,0.92)', border: '1px solid #374151',
        borderRadius: 8, padding: '8px 12px',
      }}>
        <div style={{ color: '#9ca3af', fontSize: 9, fontWeight: 700, marginBottom: 4, letterSpacing: '0.08em' }}>
          RISK LEVEL
        </div>
        {LEGEND.map(l => (
          <div key={l.color} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: l.color }} />
            <span style={{ color: '#d1d5db', fontSize: 9 }}>{l.label}</span>
          </div>
        ))}
        <div style={{ marginTop: 6, borderTop: '1px solid #374151', paddingTop: 4 }}>
          <div style={{ color: '#9ca3af', fontSize: 9, fontWeight: 700, marginBottom: 3 }}>EDGES</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <div style={{ width: 20, height: 2.5, background: '#60a5fa', borderRadius: 2 }} />
            <span style={{ color: '#93c5fd', fontSize: 9 }}>Root → Disruption</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <div style={{ width: 20, height: 2.5, background: '#fb923c', borderRadius: 2 }} />
            <span style={{ color: '#fdba74', fontSize: 9 }}>Disruption → Supply</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 20, height: 2.5, background: '#a78bfa', borderRadius: 2 }} />
            <span style={{ color: '#c4b5fd', fontSize: 9 }}>Supply → Outcome</span>
          </div>
        </div>
      </div>
    </ReactFlow>
  );

  return (
    <>
      <div className="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">4-Stage Bayesian Risk Cascade</span>
            <span className="text-gray-500 text-xs">· {nodes.filter(n=>n.type==='cascadeNode').length} nodes · {edges.length} edges · drag/scroll to explore</span>
          </div>
          <button onClick={()=>setFs(true)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-white bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded transition">
            <Maximize2 size={11}/> Fullscreen
          </button>
        </div>
        <div style={{height:540}}>{renderGraph()}</div>
      </div>
      {fs && (
        <div className="fixed inset-0 z-50 bg-gray-900 flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
            <span className="text-gray-300 text-sm font-semibold">4-Stage Bayesian Risk Cascade — Full Graph</span>
            <button onClick={()=>setFs(false)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-white bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded">
              <Minimize2 size={11}/> Exit Fullscreen
            </button>
          </div>
          <div className="flex-1">{renderGraph()}</div>
        </div>
      )}
    </>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE-2 TAB: RISK CASCADE GRAPH
// ═══════════════════════════════════════════════════════════════════════════════
const RiskCascadeTab = ({ contract, prediction }) => {
  const cv = parseFloat(contract?.contract_value) || 1000000;

  // Auto-build evidence string from prediction's top risk drivers
  const autoEvidence = useMemo(() => {
    const drivers = prediction?.top_risk_drivers || [];
    if (drivers.length > 0) {
      return drivers.slice(0, 4).map(d => `${d.node||d.factor}:${(d.probability||0.6).toFixed(2)}`).join(',');
    }
    return 'war:0.7,trade_sanctions:0.6,energy_crisis:0.5';
  }, [prediction]);

  const [contractValue, setContractValue] = useState(cv);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [evInput, setEvInput] = useState(autoEvidence);

  useEffect(() => { setEvInput(autoEvidence); }, [autoEvidence]);
  useEffect(() => { setContractValue(parseFloat(contract?.contract_value) || 1000000); }, [contract?.contract_value]);

  const parseEvidence = (str) => {
    const ev = {};
    str.split(',').forEach(pair => {
      const [k, v] = pair.split(':');
      if (k && v) ev[k.trim()] = parseFloat(v.trim()) || 0;
    });
    return ev;
  };

  const run = async () => {
    setLoading(true); setError('');
    try { setData(await getRiskCascade(parseEvidence(evInput), contractValue)); }
    catch (e) { setError(e.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };

  const fmtLoss = (v) => {
    // Cap display at 2x contract value to prevent absurd numbers
    const capped = Math.min(v, contractValue * 2);
    if (capped >= 1e9) return `$${(capped/1e9).toFixed(2)}B`;
    if (capped >= 1e6) return `$${(capped/1e6).toFixed(1)}M`;
    return `$${capped.toLocaleString()}`;
  };

  const stageIcons  = ['🌍','⚡','🚢','📋'];
  const stageBorder = ['border-red-800','border-orange-800','border-yellow-800','border-purple-800'];
  const stageGlow   = ['#F16667','#F79767','#FFD86E','#9063CD'];

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-bold text-white">4-Stage Risk Cascade Propagation Engine</h2>
            <p className="text-gray-400 text-sm mt-0.5">Bayesian belief propagation: Root Events → Operational Disruptions → Supply Chain Impacts → Contract Outcomes</p>
          </div>
          {prediction && <span className="text-xs bg-green-900/40 border border-green-700 text-green-400 px-2 py-1 rounded flex items-center gap-1"><Zap size={10}/>Auto-filled from your contract</span>}
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <label className="text-gray-400 text-xs mb-1 block">Evidence Nodes <span className="text-gray-600">(node:probability, ...)</span></label>
            <input value={evInput} onChange={e=>setEvInput(e.target.value)}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm font-mono" />
          </div>
          <div>
            <label className="text-gray-400 text-xs mb-1 block">Contract Value ($)</label>
            <input type="number" value={contractValue} onChange={e=>setContractValue(Number(e.target.value))}
              className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm" />
          </div>
        </div>
        <button onClick={run} disabled={loading}
          className="mt-3 flex items-center gap-2 px-5 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-medium transition disabled:opacity-50">
          <Play size={14}/>{loading?'Computing cascade propagation…':'Run Cascade'}
        </button>
      </div>

      {error && <div className="bg-red-900/40 border border-red-700 rounded-lg p-3 text-red-300 text-sm">{error}</div>}

      {data && (
        <>
          {/* ── Top KPI row ── */}
          <div className="grid grid-cols-5 gap-3">
            {[
              {label:'Force Majeure Risk Score',     v:`${(data.fm_risk_score*100).toFixed(1)}%`,  sub:'Overall Bayesian risk',       color:riskColor(data.fm_risk_score)},
              {label:'Expected Loss',     v:fmtLoss(data.expected_loss_usd||0),          sub:'Monte Carlo mean (5,000 iter)',color:'#F16667'},
              {label:'Stress Test Loss',          v:fmtLoss(data.p95_loss||0),                  sub:'1-in-20 stress scenario scenario',    color:'#F79767'},
              {label:'Cascade Amplifier', v:`${data.cascade_amplification||1}×`,        sub:'Stage 1→4 risk multiplication',color:'#facc15'},
              {label:'Active Risk Nodes', v:data.total_active_nodes||0,                 sub:'Nodes above 40% probability', color:'#9063CD'},
            ].map((k,i)=>(
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700 text-center">
                <div className="text-2xl font-black" style={{color:k.color}}>{k.v}</div>
                <div className="text-gray-300 text-xs font-medium mt-0.5">{k.label}</div>
                <div className="text-gray-500 text-xs mt-0.5">{k.sub}</div>
              </div>
            ))}
          </div>

          {/* ── Critical Path Banner ── */}
          {data.critical_path?.filter(Boolean).length > 0 && (
            <div className="bg-red-900/20 border border-red-800 rounded-xl p-3">
              <div className="text-red-400 text-xs font-bold mb-2">🔴 CRITICAL PROPAGATION PATH — Highest probability chain from root to outcome</div>
              <div className="flex items-center gap-2 flex-wrap">
                {data.critical_path.filter(Boolean).map((node,i)=>(
                  <React.Fragment key={i}>
                    <span className="bg-red-900/40 border border-red-700 text-red-300 text-xs px-3 py-1 rounded-full font-medium">
                      {node.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}
                    </span>
                    {i < data.critical_path.filter(Boolean).length-1 && <span className="text-red-600 text-sm font-bold">→</span>}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* ── 4 Stage Cards with node lists ── */}
          <div className="grid grid-cols-4 gap-3">
            {(data.stages||[]).map((st,i)=>(
              <div key={i} className={`bg-gray-800 rounded-xl border-2 ${stageBorder[i]} p-4`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{stageIcons[i]}</span>
                    <div>
                      <div className="text-gray-500 text-xs font-medium">STAGE {st.stage}</div>
                      <div className="text-gray-200 text-xs font-bold">{st.label}</div>
                    </div>
                  </div>
                  <div className="text-xs px-1.5 py-0.5 rounded font-bold" style={{background:stageGlow[i]+'22',color:stageGlow[i]}}>
                    {st.active_count} active
                  </div>
                </div>
                <div className="text-3xl font-black mt-1" style={{color:riskColor(st.top_prob)}}>{(st.top_prob*100).toFixed(0)}%</div>
                <div className="text-gray-400 text-xs font-semibold">{st.top_node?.replace(/_/g,' ')}</div>
                <div className="text-gray-600 text-xs mt-1 mb-3 leading-relaxed">{st.description}</div>
                {/* Mini node list */}
                <div className="space-y-1.5">
                  {(st.all_nodes||[]).map((n,ni)=>(
                    <div key={ni} className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full" style={{width:`${n.prob*100}%`,background:riskColor(n.prob)}}/>
                      </div>
                      <span className="text-gray-400 text-xs w-20 truncate">{n.node.replace(/_/g,' ')}</span>
                      <span className="text-xs font-bold w-9 text-right" style={{color:riskColor(n.prob)}}>{(n.prob*100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
                {i > 0 && st.amplification && (
                  <div className="mt-3 text-center">
                    <span className="text-xs px-2 py-0.5 rounded" style={{background:stageGlow[i]+'22',color:stageGlow[i]}}>
                      {st.amplification}× amplification from Stage {st.stage-1}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* ── Loss Percentiles ── */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">💸 Monte Carlo Loss Distribution — 5,000 Iterations</div>
            <div className="grid grid-cols-4 gap-3 mb-4">
              {[
                {label:'Expected (Mean)',  v:fmtLoss(data.expected_loss_usd||0), sub:'Average outcome',        color:'#4C8EDA'},
                {label:'Typical Case',     v:fmtLoss(data.p50_loss||0),          sub:'50/50 chance (median outcome)', color:'#68BC00'},
                {label:'Stress Test',      v:fmtLoss(data.p95_loss||0),          sub:'1-in-20 stress scenario',      color:'#F79767'},
                {label:'Catastrophic Risk',   v:fmtLoss(data.p99_loss||0),          sub:'1-in-100 black swan event',           color:'#F16667'},
              ].map((k,i)=>(
                <div key={i} className="bg-gray-900 rounded-lg p-3 text-center border border-gray-700">
                  <div className="text-xl font-bold" style={{color:k.color}}>{k.v}</div>
                  <div className="text-gray-300 text-xs font-medium mt-0.5">{k.label}</div>
                  <div className="text-gray-500 text-xs">{k.sub}</div>
                </div>
              ))}
            </div>
            {/* Visual loss bar */}
            <div className="relative h-6 bg-gray-700 rounded-full overflow-hidden">
              <div className="absolute left-0 top-0 h-full rounded-full bg-blue-600 opacity-60"
                style={{width:`${Math.min(100,(data.expected_loss_usd||0)/contractValue*100)}%`}}/>
              <div className="absolute left-0 top-0 h-full rounded-full bg-orange-500 opacity-40"
                style={{width:`${Math.min(100,(data.p95_loss||0)/contractValue*100)}%`}}/>
              <div className="absolute left-0 top-0 h-full rounded-full bg-red-500 opacity-30"
                style={{width:`${Math.min(100,(data.p99_loss||0)/contractValue*100)}%`}}/>
              <div className="absolute inset-0 flex items-center justify-center text-white text-xs font-bold">
                Loss range: {fmtLoss(data.expected_loss_usd||0)} – {fmtLoss(data.p99_loss||0)} (as % of ${(contractValue/1e9).toFixed(2)}B contract)
              </div>
            </div>
          </div>

          {/* ── Stage-to-Stage Flow ── */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">🔄 Risk Amplification Flow — How Each Stage Multiplies Risk</div>
            <div className="flex items-stretch gap-0">
              {(data.stages||[]).map((st,i)=>(
                <React.Fragment key={i}>
                  <div className="flex-1 text-center p-3 rounded-lg" style={{background:stageGlow[i]+'15',border:`1px solid ${stageGlow[i]}44`}}>
                    <div className="text-xs text-gray-500 mb-1">{stageIcons[i]} Stage {st.stage}</div>
                    <div className="text-xl font-black" style={{color:stageGlow[i]}}>{(st.avg_prob*100).toFixed(1)}%</div>
                    <div className="text-gray-400 text-xs mt-0.5">{st.label}</div>
                    <div className="text-gray-600 text-xs">{st.active_count} nodes active</div>
                  </div>
                  {i < 3 && (
                    <div className="flex flex-col items-center justify-center px-2">
                      <div className="text-gray-500 text-xs font-bold">{(data.stages[i+1]?.amplification||1)}×</div>
                      <div className="text-gray-600 text-lg">→</div>
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* ── Graph ── */}
          <CascadeGraphPanel nodes={data.nodes||[]} edges={data.edges||[]} />
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE-2 TAB: CLAUSE OPTIMIZER
// ═══════════════════════════════════════════════════════════════════════════════
const ClauseOptimizerTab = ({ contract }) => {
  const [evInput, setEvInput] = useState('war:0.6,trade_sanctions:0.5,energy_crisis:0.4');
  const [contractValue, setContractValue] = useState(parseFloat(contract?.contract_value) || 5000000);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    setContractValue(parseFloat(contract?.contract_value) || 5000000);
  }, [contract?.contract_value]);

  const parseEvidence = (str) => {
    const ev = {};
    str.split(',').forEach(pair => {
      const [k, v] = pair.split(':');
      if (k && v) ev[k.trim()] = parseFloat(v.trim()) || 0;
    });
    return ev;
  };

  const run = async () => {
    setLoading(true); setError(''); setSelected(null);
    try { setData(await runClauseOptimizer(parseEvidence(evInput), contractValue)); }
    catch (e) { setError(e.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };

  const REC_META = {
    'STRONGLY RECOMMENDED': { color: '#F16667', bg: 'rgba(241,102,103,0.15)', border: '#F16667', icon: '🔴' },
    'RECOMMENDED':          { color: '#F79767', bg: 'rgba(247,151,103,0.15)', border: '#F79767', icon: '🟠' },
    'OPTIONAL':             { color: '#68BC00', bg: 'rgba(104,188,0,0.15)',    border: '#68BC00', icon: '🟢' },
  };

  const fmtMoney = (v) => {
    if (!v && v !== 0) return '—';
    const abs = Math.abs(v);
    const sign = v < 0 ? '-' : '+';
    if (abs >= 1e9) return `${sign}$${(abs/1e9).toFixed(2)}B`;
    if (abs >= 1e6) return `${sign}$${(abs/1e6).toFixed(1)}M`;
    if (abs >= 1e3) return `${sign}$${(abs/1e3).toFixed(0)}K`;
    return `${sign}$${abs.toLocaleString()}`;
  };

  const recs = data?.clause_recommendations || [];
  const strongly = recs.filter(c => c.recommendation === 'STRONGLY RECOMMENDED');
  const recommended = recs.filter(c => c.recommendation === 'RECOMMENDED');
  const optional = recs.filter(c => !['STRONGLY RECOMMENDED','RECOMMENDED'].includes(c.recommendation));
  const maxReduction = recs.length ? Math.max(...recs.map(c => c.risk_reduction || 0)) : 0;
  const maxLoss = recs.length ? Math.max(...recs.map(c => Math.abs(c.loss_saved_usd || 0))) : 1;

  // Bar chart data for top-5 clauses
  const barData = recs.slice(0, 8).map(c => ({
    name: c.clause.replace('Clause','').replace(/([A-Z])/g,' $1').trim(),
    reduction: parseFloat((c.risk_reduction * 100).toFixed(2)),
    saved: Math.abs(c.loss_saved_usd || 0) / 1e6,
  }));

  return (
    <div className="space-y-5">
      {/* ── Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <CheckCircle size={18} className="text-green-400" /> Counterfactual Clause Optimizer
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Simulates adding each protective Force Majeure clause to your contract and measures expected risk reduction & financial savings.
          </p>
        </div>
        <div className="text-right text-xs text-gray-500">
          <div className="font-mono text-gray-400">{recs.length} clauses tested</div>
          {data && <div className="text-green-400 font-bold mt-0.5">Best: {data.top_recommendation}</div>}
        </div>
      </div>

      {/* ── Inputs ── */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 grid grid-cols-3 gap-4 items-end">
        <div className="col-span-2">
          <label className="text-gray-400 text-xs mb-1 block font-medium uppercase tracking-wider">Evidence (node:prob, ...)</label>
          <input value={evInput} onChange={e=>setEvInput(e.target.value)}
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm font-mono focus:border-blue-500 outline-none transition" />
        </div>
        <div>
          <label className="text-gray-400 text-xs mb-1 block font-medium uppercase tracking-wider">Contract Value ($)</label>
          <input type="number" value={contractValue} onChange={e=>setContractValue(Number(e.target.value))}
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 outline-none transition" />
        </div>
        <div className="col-span-3 flex justify-end">
          <button onClick={run} disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-semibold transition disabled:opacity-50">
            <Play size={14} /> {loading ? 'Optimizing…' : 'Run Optimizer'}
          </button>
        </div>
      </div>

      {error && <div className="bg-red-900/40 border border-red-700 rounded-lg p-3 text-red-300 text-sm">{error}</div>}

      {data && (
        <>
          {/* ── KPI row ── */}
          <div className="grid grid-cols-5 gap-3">
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-1">
              <div className="text-gray-400 text-xs flex items-center gap-1"><Shield size={11}/> Baseline Risk</div>
              <div className="text-2xl font-black" style={{color: riskColor(data.baseline_risk)}}>
                {(data.baseline_risk * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5 mt-1">
                <div className="h-1.5 rounded-full" style={{width:`${data.baseline_risk*100}%`, background: riskColor(data.baseline_risk)}} />
              </div>
            </div>
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-1">
              <div className="text-gray-400 text-xs flex items-center gap-1"><TrendingUp size={11}/> Best Risk After</div>
              <div className="text-2xl font-black text-green-400">
                {(Math.max(0, data.baseline_risk - maxReduction) * 100).toFixed(1)}%
              </div>
              <div className="text-gray-500 text-xs mt-1">with {data.top_recommendation}</div>
            </div>
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-1">
              <div className="text-gray-400 text-xs flex items-center gap-1"><Target size={11}/> Max Risk Reduction</div>
              <div className="text-2xl font-black text-emerald-400">
                -{(data.max_possible_reduction * 100).toFixed(1)}%
              </div>
              <div className="text-gray-500 text-xs mt-1">single best clause</div>
            </div>
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-1">
              <div className="text-gray-400 text-xs flex items-center gap-1"><Zap size={11}/> Max $ Saved</div>
              <div className="text-2xl font-black text-yellow-400">
                {fmtMoney(maxLoss)}
              </div>
              <div className="text-gray-500 text-xs mt-1">per clause added</div>
            </div>
            <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-1">
              <div className="text-gray-400 text-xs flex items-center gap-1"><AlertTriangle size={11}/> Priority Clauses</div>
              <div className="flex gap-2 mt-1">
                <div className="text-center">
                  <div className="text-lg font-black text-red-400">{strongly.length}</div>
                  <div className="text-gray-500 text-xs">Critical</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-black text-orange-400">{recommended.length}</div>
                  <div className="text-gray-500 text-xs">Rec.</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-black text-green-400">{optional.length}</div>
                  <div className="text-gray-500 text-xs">Optional</div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Chart + Table split ── */}
          <div className="grid grid-cols-5 gap-4">
            {/* Bar chart */}
            <div className="col-span-2 bg-gray-800 border border-gray-700 rounded-xl p-4">
              <div className="text-gray-300 text-sm font-semibold mb-3 flex items-center gap-2">
                <BarChart2 size={14} className="text-blue-400" /> Risk Reduction by Clause
              </div>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={barData} layout="vertical" margin={{left:0, right:20}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                  <XAxis type="number" tickFormatter={v=>`${v}%`} tick={{fill:'#9CA3AF',fontSize:10}} />
                  <YAxis type="category" dataKey="name" tick={{fill:'#9CA3AF',fontSize:9}} width={90} />
                  <Tooltip
                    formatter={(v, name) => name === 'reduction' ? [`${v}%`, 'Risk Reduction'] : [`$${v.toFixed(2)}M`, '$ Saved']}
                    contentStyle={{background:'#1f2937',border:'1px solid #374151',borderRadius:'8px',color:'#fff',fontSize:11}}
                  />
                  <Bar dataKey="reduction" fill="#68BC00" radius={[0,4,4,0]} name="reduction">
                    {barData.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? '#F16667' : i === 1 ? '#F79767' : '#68BC00'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Table */}
            <div className="col-span-3 bg-gray-800 border border-gray-700 rounded-xl overflow-hidden flex flex-col">
              <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
                <span className="text-gray-300 text-sm font-semibold">Clause Recommendations</span>
                <span className="text-gray-500 text-xs">{recs.length} clauses · ranked by risk reduction</span>
              </div>
              <div className="overflow-auto flex-1" style={{maxHeight: 310}}>
                <table className="w-full text-xs">
                  <thead className="bg-gray-900 sticky top-0 z-10">
                    <tr>
                      {['#','Clause','Baseline → After','Reduction','$ Saved','Priority'].map(h=>(
                        <th key={h} className="text-left px-3 py-2 text-gray-400 font-semibold">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {recs.map((c, i) => {
                      const meta = REC_META[c.recommendation] || REC_META['OPTIONAL'];
                      const isSelected = selected === i;
                      const reductionPct = (c.risk_reduction || 0) * 100;
                      const barW = maxReduction > 0 ? (c.risk_reduction / maxReduction) * 100 : 0;
                      return (
                        <tr key={i}
                          onClick={() => setSelected(isSelected ? null : i)}
                          className="border-t border-gray-700 cursor-pointer transition"
                          style={{background: isSelected ? 'rgba(76,142,218,0.12)' : 'transparent'}}
                          onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; }}
                          onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                        >
                          <td className="px-3 py-2 text-gray-500 font-mono">{i+1}</td>
                          <td className="px-3 py-2">
                            <div className="font-semibold text-blue-300">{c.clause}</div>
                            {/* Reduction bar */}
                            <div className="mt-1 w-full bg-gray-700 rounded-full h-1">
                              <div className="h-1 rounded-full transition-all" style={{width:`${barW}%`, background: meta.color}} />
                            </div>
                          </td>
                          <td className="px-3 py-2 font-mono">
                            <span className="text-gray-400">{(c.baseline_risk*100).toFixed(1)}%</span>
                            <span className="text-gray-600 mx-1">→</span>
                            <span className="font-bold" style={{color: meta.color}}>{(c.new_risk*100).toFixed(1)}%</span>
                          </td>
                          <td className="px-3 py-2">
                            <span className="font-bold text-emerald-400">-{reductionPct.toFixed(1)}%</span>
                          </td>
                          <td className="px-3 py-2">
                            <span className={c.loss_saved_usd >= 0 ? 'text-yellow-400 font-semibold' : 'text-red-400'}>
                              {fmtMoney(c.loss_saved_usd)}
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            <span className="px-2 py-0.5 rounded text-white text-xs font-bold"
                              style={{background: meta.bg, border: `1px solid ${meta.border}66`, color: meta.color}}>
                              {meta.icon} {c.recommendation}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* ── Priority breakdown cards ── */}
          {strongly.length > 0 && (
            <div className="bg-red-900/20 border border-red-700/50 rounded-xl p-4">
              <div className="text-red-400 text-sm font-bold mb-3 flex items-center gap-2">
                <AlertTriangle size={14}/> Strongly Recommended Clauses — Add Immediately
              </div>
              <div className="grid grid-cols-3 gap-3">
                {strongly.map((c, i) => (
                  <div key={i} className="bg-gray-800 border border-red-800/40 rounded-lg p-3">
                    <div className="text-white text-xs font-bold mb-1">{c.clause}</div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">Risk drop</span>
                      <span className="text-red-300 font-bold">-{(c.risk_reduction*100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-xs mt-0.5">
                      <span className="text-gray-400">$ Saved</span>
                      <span className="text-yellow-400 font-bold">{fmtMoney(c.loss_saved_usd)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE-2 TAB: 12-MONTH TEMPORAL FORECAST
// ═══════════════════════════════════════════════════════════════════════════════
const TemporalForecastTab = ({ contract }) => {
  const [evInput, setEvInput] = useState('war:0.6,trade_sanctions:0.5,energy_crisis:0.4');
  const [startMonth, setStartMonth] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const parseEvidence = (str) => {
    const ev = {};
    str.split(',').forEach(pair => {
      const [k, v] = pair.split(':');
      if (k && v) ev[k.trim()] = parseFloat(v.trim()) || 0;
    });
    return ev;
  };

  const run = async () => {
    setLoading(true); setError('');
    try { setData(await getTemporalForecast(parseEvidence(evInput), startMonth)); }
    catch (e) { setError(e.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };

  const riskLabelColor = (label) => label === 'HIGH' ? '#F16667' : label === 'MEDIUM' ? '#F79767' : '#68BC00';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">12-Month Temporal DBN Forecast</h2>
        <p className="text-gray-400 text-sm mt-1">Dynamic Bayesian Network with time-decay and seasonal boosts per month</p>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <label className="text-gray-400 text-xs mb-1 block">Evidence (node:prob, ...)</label>
          <input value={evInput} onChange={e=>setEvInput(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm" />
        </div>
        <div>
          <label className="text-gray-400 text-xs mb-1 block">Start Month (1-12)</label>
          <input type="number" min={1} max={12} value={startMonth} onChange={e=>setStartMonth(Number(e.target.value))}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm" />
        </div>
      </div>
      <button onClick={run} disabled={loading}
        className="flex items-center gap-2 px-4 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-sm font-medium transition disabled:opacity-50">
        <Play size={14} /> {loading ? 'Forecasting…' : 'Run 12-Month Forecast'}
      </button>
      {error && <div className="bg-red-900/40 border border-red-700 rounded-lg p-3 text-red-300 text-sm">{error}</div>}
      {data && (
        <>
          <div className="grid grid-cols-4 gap-3">
            <MetricCard label="Avg Risk" value={`${(data.avg_risk*100).toFixed(1)}%`} color={riskColor(data.avg_risk)} icon={TrendingUp} />
            <MetricCard label="Peak Month" value={data.peak_month?.month||'—'} color="#F16667" icon={AlertTriangle} sub={`${((data.peak_month?.fm_risk||0)*100).toFixed(1)}% risk`} />
            <MetricCard label="Trough Month" value={data.trough_month?.month||'—'} color="#68BC00" icon={CheckCircle} sub={`${((data.trough_month?.fm_risk||0)*100).toFixed(1)}% risk`} />
            <MetricCard label="High Risk Months" value={data.months_high_risk||0} color="#F79767" icon={Clock} />
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
            <div className="text-gray-300 text-sm font-semibold mb-3">FM Risk by Month</div>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={data.forecast||[]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" tick={{fill:'#9CA3AF',fontSize:11}} />
                <YAxis domain={['auto', 'auto']} tickFormatter={v=>`${(v*100).toFixed(0)}%`} tick={{fill:'#9CA3AF',fontSize:11}} />
                <Tooltip formatter={v=>`${(v*100).toFixed(1)}%`} contentStyle={{background:'#1f2937',border:'1px solid #374151',borderRadius:'8px',color:'#fff'}} />
                <Legend />
                <Line dataKey="fm_risk" stroke="#F16667" name="FM Risk" strokeWidth={2} dot={{r:4}} />
                <Line dataKey="fm_invocation_prob" stroke="#F79767" name="Force Majeure Invocation Prob" strokeWidth={1.5} strokeDasharray="4 2" dot={{r:3}} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-700 text-gray-300 text-sm font-semibold">Monthly Breakdown</div>
            <table className="w-full text-xs">
              <thead className="bg-gray-900">
                <tr>
                  {['Month','FM Risk','Force Majeure Invocation','Project Delay','Risk Label','Dominant Driver'].map(h=>(
                    <th key={h} className="text-left px-3 py-2 text-gray-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(data.forecast||[]).map((m,i)=>(
                  <tr key={i} className="border-t border-gray-700 hover:bg-gray-750">
                    <td className="px-3 py-2 font-semibold text-gray-200">{m.month}</td>
                    <td className="px-3 py-2 font-bold" style={{color:riskColor(m.fm_risk)}}>{(m.fm_risk*100).toFixed(1)}%</td>
                    <td className="px-3 py-2 text-gray-300">{(m.fm_invocation_prob*100).toFixed(1)}%</td>
                    <td className="px-3 py-2 text-gray-300">{(m.project_delay_prob*100).toFixed(1)}%</td>
                    <td className="px-3 py-2">
                      <span className="px-2 py-0.5 rounded text-white text-xs font-bold"
                        style={{background:riskLabelColor(m.risk_label)}}>{m.risk_label}</span>
                    </td>
                    <td className="px-3 py-2 text-gray-400">{m.dominant_driver?.replace(/_/g,' ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE-2 TAB: RISK FORMULA BREAKDOWN
// ═══════════════════════════════════════════════════════════════════════════════
const RiskFormulaTab = ({ contract }) => {
  const [evInput, setEvInput] = useState('war:0.7,pandemic:0.4,trade_sanctions:0.5,energy_crisis:0.3');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const parseEvidence = (str) => {
    const ev = {};
    str.split(',').forEach(pair => {
      const [k, v] = pair.split(':');
      if (k && v) ev[k.trim()] = parseFloat(v.trim()) || 0;
    });
    return ev;
  };

  const run = async () => {
    setLoading(true); setError('');
    try { setData(await getRiskFormula(parseEvidence(evInput))); }
    catch (e) { setError(e.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };

  const getRiskLevelInfo = (score) => {
    if (score > 0.7) return { label: 'CRITICAL RISK', color: 'from-red-600 to-red-800', textColor: '#FF4444', icon: '🔴', glow: 'shadow-red-500/50' };
    if (score > 0.5) return { label: 'HIGH RISK', color: 'from-orange-600 to-red-600', textColor: '#FF6B6B', icon: '🟠', glow: 'shadow-orange-500/50' };
    if (score > 0.3) return { label: 'MEDIUM RISK', color: 'from-yellow-600 to-orange-600', textColor: '#FFB020', icon: '🟡', glow: 'shadow-yellow-500/50' };
    return { label: 'LOW RISK', color: 'from-green-600 to-teal-600', textColor: '#4ADE80', icon: '🟢', glow: 'shadow-green-500/50' };
  };

  const getContributionColor = (index) => {
    const colors = ['#FF6B6B', '#FF8E53', '#FFA726', '#FFCA28', '#66BB6A'];
    return colors[index % colors.length];
  };

  return (
    <div className="space-y-6">
      {/* Header Section with Gradient */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-6 shadow-2xl">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
              <Target className="text-white" size={24} />
            </div>
            <h2 className="text-2xl font-bold text-white">Risk Formula Breakdown</h2>
          </div>
          <p className="text-purple-200 text-sm leading-relaxed mt-3 font-mono bg-black/20 rounded-lg p-3 backdrop-blur-sm">
            <span className="text-white font-bold">Force Majeure Score</span> =
            <span className="text-red-300"> 0.35×P(Force Majeure Invocation)</span> +
            <span className="text-orange-300"> 0.25×P(Project Delay)</span> +
            <span className="text-yellow-300"> 0.20×P(Cost Overrun)</span> +
            <span className="text-blue-300"> 0.12×P(Suspension)</span> +
            <span className="text-purple-300"> 0.08×P(Termination)</span>
          </p>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Input Section */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-5 shadow-xl border border-gray-700">
        <label className="text-gray-300 text-sm font-semibold mb-2 block flex items-center gap-2">
          <Sliders size={16} className="text-indigo-400" />
          Evidence Parameters (node:prob, ...)
        </label>
        <input value={evInput} onChange={e=>setEvInput(e.target.value)}
          className="w-full bg-gray-900/80 border-2 border-gray-600 focus:border-indigo-500 rounded-xl px-4 py-3 text-white text-sm font-mono transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          placeholder="e.g., war:0.7,pandemic:0.4,trade_sanctions:0.5" />
      </div>

      {/* Compute Button */}
      <button onClick={run} disabled={loading}
        className="group relative w-full overflow-hidden bg-gradient-to-r from-red-600 via-red-700 to-red-800 hover:from-red-700 hover:via-red-800 hover:to-red-900 rounded-xl px-6 py-4 text-white font-bold shadow-2xl shadow-red-900/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000"></div>
        <div className="relative flex items-center justify-center gap-3">
          {loading ? (
            <>
              <RefreshCw size={18} className="animate-spin" />
              <span className="text-lg">Computing Risk Formula...</span>
            </>
          ) : (
            <>
              <Zap size={18} className="group-hover:animate-pulse" />
              <span className="text-lg">Compute Formula</span>
            </>
          )}
        </div>
      </button>

      {error && (
        <div className="bg-gradient-to-r from-red-900/60 to-red-800/60 border-2 border-red-500 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-red-200">
            <AlertTriangle size={20} />
            <span className="font-semibold">{error}</span>
          </div>
        </div>
      )}

      {data && (
        <>
          {/* Risk Score Card - Hero Section */}
          <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${getRiskLevelInfo(data.total_fm_risk_score || 0).color} p-8 shadow-2xl ${getRiskLevelInfo(data.total_fm_risk_score || 0).glow} shadow-2xl`}>
            <div className="absolute inset-0 bg-black/30"></div>
            <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>
            <div className="relative z-10 text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-black/40 rounded-full mb-4 backdrop-blur-sm">
                <Activity size={16} className="text-white animate-pulse" />
                <span className="text-white text-xs font-bold tracking-wider uppercase">
                  {getRiskLevelInfo(data.total_fm_risk_score || 0).label}
                </span>
              </div>
              <div className="mb-3">
                <div className="text-8xl font-black text-white drop-shadow-2xl mb-2 animate-pulse">
                  {((data.total_fm_risk_score||0)*100).toFixed(1)}%
                </div>
                <div className="text-white/80 text-sm font-semibold">Force Majeure Risk Score</div>
              </div>
              <div className="mt-6 p-4 bg-black/30 rounded-xl backdrop-blur-sm">
                <div className="text-white/70 text-xs mb-2 uppercase tracking-wide font-semibold">Calculation Formula</div>
                <div className="text-white/90 text-sm font-mono leading-relaxed">
                  {data.formula || 'Formula unavailable'}
                </div>
              </div>
            </div>
          </div>

          {/* Outcome Contributions - Enhanced Chart */}
          <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-indigo-900/50 to-purple-900/50 px-6 py-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <BarChart2 className="text-indigo-300" size={20} />
                </div>
                <h3 className="text-white font-bold text-lg">Outcome Contributions</h3>
              </div>
              <p className="text-gray-400 text-xs mt-1">Weighted impact of each outcome on overall Force Majeure risk</p>
            </div>
            <div className="p-6">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={(data.outcome_breakdown||[]).map((item, idx)=>({
                  name: item.label,
                  value: parseFloat((item.contribution*100).toFixed(2)),
                  probability: parseFloat((item.probability*100).toFixed(1)),
                  weight: item.weight,
                  fill: getContributionColor(idx)
                }))}>
                  <defs>
                    {(data.outcome_breakdown||[]).map((item, idx) => (
                      <linearGradient key={idx} id={`gradient${idx}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={getContributionColor(idx)} stopOpacity={0.9}/>
                        <stop offset="100%" stopColor={getContributionColor(idx)} stopOpacity={0.4}/>
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" strokeOpacity={0.3} />
                  <XAxis dataKey="name" tick={{fill:'#D1D5DB',fontSize:11, fontWeight:600}} angle={-15} textAnchor="end" height={80} />
                  <YAxis tickFormatter={v=>`${v.toFixed(1)}%`} tick={{fill:'#D1D5DB',fontSize:11}}
                    label={{value: 'Contribution to Total Risk (%)', angle: -90, position: 'insideLeft', fill:'#9CA3AF', fontSize:12, fontWeight:600}} />
                  <Tooltip
                    formatter={(v,name)=>{
                      if(name==='value') return [`${v.toFixed(2)}%`, 'Contribution'];
                      if(name==='probability') return [`${v}%`, 'Probability'];
                      if(name==='weight') return [`${v}`, 'Weight'];
                      return v;
                    }}
                    contentStyle={{background:'linear-gradient(135deg, #1f2937 0%, #111827 100%)',border:'2px solid #4B5563',borderRadius:'12px',color:'#fff', padding:'12px', boxShadow:'0 20px 40px rgba(0,0,0,0.5)'}}
                    labelStyle={{color:'#F3F4F6', fontWeight:'bold', marginBottom:'8px'}}
                  />
                  <Bar dataKey="value" radius={[8,8,0,0]} animationDuration={1000}>
                    {(data.outcome_breakdown||[]).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={`url(#gradient${index})`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Event Contribution Table - Modern Design */}
          <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 px-6 py-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <GitBranch className="text-purple-300" size={20} />
                </div>
                <h3 className="text-white font-bold text-lg">Per-Event Risk Contribution</h3>
              </div>
              <p className="text-gray-400 text-xs mt-1">Individual event impact on Force Majeure risk calculation</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gradient-to-r from-gray-900 to-gray-800 border-b border-gray-700">
                    {['Event','Inferred Prob','Evidence Override','Risk Contribution','Impact Level'].map((h,i)=>(
                      <th key={h} className="text-left px-6 py-4 text-gray-300 text-xs font-bold uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {(data.event_contribution||[]).map((item,i)=>(
                    <tr key={i} className="hover:bg-gradient-to-r hover:from-gray-800/50 hover:to-gray-900/50 transition-all duration-200 group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-indigo-500 group-hover:animate-pulse"></div>
                          <span className="font-bold text-white group-hover:text-indigo-300 transition-colors">{item.label}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="h-2 bg-gray-700 rounded-full w-20 overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-500"
                              style={{width: `${item.inferred_prob*100}%`}}></div>
                          </div>
                          <span className="text-cyan-300 font-bold text-sm">{(item.inferred_prob*100).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {item.evidence_override ? (
                          <span className="inline-flex items-center gap-1 px-3 py-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full text-white font-bold text-xs shadow-lg">
                            <Target size={12} />
                            {(item.evidence_override*100).toFixed(0)}%
                          </span>
                        ) : (
                          <span className="text-gray-500 text-sm">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-black text-lg" style={{
                          color: item.risk_contribution>0.05 ? '#FF4444' : item.risk_contribution>0.02 ? '#FFB020' : '#4ADE80',
                          textShadow: item.risk_contribution>0.05 ? '0 0 10px rgba(255,68,68,0.5)' : 'none'
                        }}>
                          {item.risk_contribution?.toFixed(4)||'0.0000'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {item.risk_contribution > 0.05 ? (
                          <span className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 rounded-lg text-white font-bold text-xs shadow-lg shadow-red-900/50 animate-pulse">
                            <TrendingUp size={14} />
                            CRITICAL
                          </span>
                        ) : item.risk_contribution > 0.02 ? (
                          <span className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-orange-700 rounded-lg text-white font-bold text-xs shadow-lg">
                            <TrendingUp size={14} />
                            HIGH
                          </span>
                        ) : item.risk_contribution > 0.005 ? (
                          <span className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-600 to-yellow-700 rounded-lg text-white font-bold text-xs shadow-lg">
                            <Activity size={14} />
                            MEDIUM
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-2 px-3 py-1 bg-gray-700 rounded-lg text-gray-400 font-semibold text-xs">
                            <CheckCircle size={12} />
                            LOW
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE-2 TAB: REAL-TIME ALERT ENGINE
// ═══════════════════════════════════════════════════════════════════════════════
const AlertEngineTab = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');

  const load = async () => {
    setLoading(true); setError('');
    try { setData(await getAlertEngine()); }
    catch (e) { setError(e.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const getSeverityConfig = (severity) => {
    const configs = {
      CRITICAL: {
        color: '#DC2626',
        bg: 'from-red-600 to-red-800',
        glow: 'shadow-red-500/50',
        icon: '🔴',
        pulse: true
      },
      HIGH: {
        color: '#F97316',
        bg: 'from-orange-600 to-red-600',
        glow: 'shadow-orange-500/50',
        icon: '🟠',
        pulse: false
      },
      MEDIUM: {
        color: '#FBBF24',
        bg: 'from-yellow-600 to-orange-600',
        glow: 'shadow-yellow-500/50',
        icon: '🟡',
        pulse: false
      },
      LOW: {
        color: '#10B981',
        bg: 'from-green-600 to-emerald-600',
        glow: 'shadow-green-500/50',
        icon: '🟢',
        pulse: false
      }
    };
    return configs[severity] || configs.MEDIUM;
  };

  const filteredAlerts = selectedSeverity === 'ALL'
    ? (data?.alerts || [])
    : (data?.alerts || []).filter(a => a.severity === selectedSeverity);

  const severityDistribution = (data?.alerts || []).reduce((acc, alert) => {
    acc[alert.severity] = (acc[alert.severity] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Animated Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-red-900 via-orange-900 to-yellow-900 p-6 shadow-2xl">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-3 bg-white/10 rounded-xl backdrop-blur-sm">
                <Bell className="text-white animate-pulse" size={28} />
              </div>
              <div>
                <h2 className="text-2xl font-black text-white">Real-Time Alert Engine</h2>
                <p className="text-orange-200 text-sm mt-1">Live events matched against active contracts — auto-alerts when Force Majeure risk spikes</p>
              </div>
            </div>
          </div>
          <button onClick={load} disabled={loading}
            className="group relative overflow-hidden bg-white/20 hover:bg-white/30 backdrop-blur-sm border-2 border-white/30 rounded-xl px-6 py-3 text-white font-bold shadow-xl transition-all duration-300 disabled:opacity-50 hover:scale-105">
            <div className="flex items-center gap-2">
              <RefreshCw size={16} className={loading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'} />
              <span>{loading ? 'Scanning...' : 'Refresh Alerts'}</span>
            </div>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-gradient-to-r from-red-900/60 to-red-800/60 border-2 border-red-500 rounded-xl p-4 backdrop-blur-sm animate-pulse">
          <div className="flex items-center gap-2 text-red-200">
            <AlertTriangle size={20} />
            <span className="font-semibold">{error}</span>
          </div>
        </div>
      )}

      {data && (
        <>
          {/* Enhanced Metric Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="group relative overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 border border-gray-700 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <Bell className="text-indigo-400" size={24} />
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-bold">Total</span>
                </div>
                <div className="text-4xl font-black text-white mb-1">{data.total_alerts||0}</div>
                <div className="text-gray-400 text-xs font-semibold">Total Alerts</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-red-900/40 to-red-800/40 rounded-2xl p-6 border-2 border-red-600/50 shadow-xl shadow-red-900/30 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/20 to-red-700/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <AlertTriangle className="text-red-400 animate-pulse" size={24} />
                  <span className="text-xs text-red-300 uppercase tracking-wider font-bold">Critical</span>
                </div>
                <div className="text-4xl font-black text-red-300 mb-1">{data.critical_count||0}</div>
                <div className="text-red-200 text-xs font-semibold">Immediate Action Required</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-orange-900/40 to-orange-800/40 rounded-2xl p-6 border-2 border-orange-600/50 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/20 to-orange-700/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <Zap className="text-orange-400" size={24} />
                  <span className="text-xs text-orange-300 uppercase tracking-wider font-bold">High</span>
                </div>
                <div className="text-4xl font-black text-orange-300 mb-1">{data.high_count||0}</div>
                <div className="text-orange-200 text-xs font-semibold">Priority Review Needed</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-blue-900/40 to-cyan-900/40 rounded-2xl p-6 border border-blue-700/50 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <Radio className="text-cyan-400 animate-pulse" size={24} />
                  <span className="text-xs text-cyan-300 uppercase tracking-wider font-bold">Events</span>
                </div>
                <div className="text-4xl font-black text-cyan-300 mb-1">{data.live_events_processed||0}</div>
                <div className="text-cyan-200 text-xs font-semibold">Live Events Processed</div>
              </div>
            </div>
          </div>

          {/* Severity Distribution Chart */}
          {Object.keys(severityDistribution).length > 0 && (
            <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
              <div className="bg-gradient-to-r from-indigo-900/50 to-purple-900/50 px-6 py-4 border-b border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <BarChart2 className="text-purple-300" size={20} />
                  </div>
                  <h3 className="text-white font-bold text-lg">Severity Distribution</h3>
                </div>
              </div>
              <div className="p-6">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={Object.entries(severityDistribution).map(([severity, count]) => ({
                        name: severity,
                        value: count,
                        color: getSeverityConfig(severity).color
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      animationDuration={800}
                    >
                      {Object.entries(severityDistribution).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getSeverityConfig(entry[0]).color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{background:'#1f2937',border:'2px solid #4B5563',borderRadius:'12px',color:'#fff'}} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Event Type Breakdown - Enhanced */}
          {Object.keys(data.event_type_breakdown||{}).length > 0 && (
            <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-900/50 to-blue-900/50 px-6 py-4 border-b border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <Globe className="text-cyan-300" size={20} />
                  </div>
                  <h3 className="text-white font-bold text-lg">Live Event Type Breakdown</h3>
                </div>
                <p className="text-gray-400 text-xs mt-1">Real-time categorization of triggering events</p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(data.event_type_breakdown).map(([k,v])=>(
                    <div key={k} className="group bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-4 border border-gray-700 hover:border-cyan-500 transition-all duration-300 hover:scale-105 shadow-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-300 text-sm font-semibold capitalize">{k.replace(/_/g,' ')}</span>
                        <span className="px-3 py-1 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-full text-white font-black text-sm shadow-lg group-hover:animate-pulse">{v}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Filter Pills */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-gray-400 text-sm font-semibold">Filter by Severity:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-4 py-2 rounded-lg font-bold text-sm transition-all duration-300 ${
                  selectedSeverity === sev
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg scale-105'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                }`}
              >
                {sev}
                {sev !== 'ALL' && ` (${severityDistribution[sev] || 0})`}
              </button>
            ))}
          </div>

          {/* Alert Cards - Premium Design */}
          <div className="space-y-4">
            {filteredAlerts.length === 0 && (
              <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 border-2 border-green-600 rounded-2xl p-8 text-center backdrop-blur-sm">
                <CheckCircle size={48} className="mx-auto mb-4 text-green-400 animate-pulse" />
                <h3 className="text-green-300 text-xl font-bold mb-2">All Clear!</h3>
                <p className="text-green-400 text-sm">No active alerts — Force Majeure risk is within normal parameters</p>
              </div>
            )}
            {filteredAlerts.map((alert,i)=>{
              const config = getSeverityConfig(alert.severity);
              return (
                <div key={i} className={`group relative overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl border-2 shadow-2xl ${config.glow} transition-all duration-300 hover:scale-[1.02]`}
                  style={{borderColor: config.color}}>
                  <div className="absolute inset-0 opacity-5" style={{background: `linear-gradient(135deg, ${config.color} 0%, transparent 100%)`}}></div>
                  <div className="relative z-10 p-6">
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div className={`p-3 rounded-xl shadow-lg ${config.pulse ? 'animate-pulse' : ''}`}
                        style={{background: `${config.color}33`, border: `2px solid ${config.color}66`}}>
                        <AlertTriangle size={24} style={{color: config.color}} />
                      </div>

                      {/* Content */}
                      <div className="flex-1">
                        {/* Header */}
                        <div className="flex items-center gap-3 mb-3 flex-wrap">
                          <span className={`px-4 py-1.5 rounded-lg font-black text-xs shadow-lg ${config.pulse ? 'animate-pulse' : ''}`}
                            style={{background: `linear-gradient(135deg, ${config.color} 0%, ${config.color}CC 100%)`, color: 'white'}}>
                            {config.icon} {alert.severity}
                          </span>
                          <span className="px-3 py-1 bg-gray-700 rounded-lg text-gray-300 text-xs font-mono font-bold">
                            Contract: {alert.contract_id?.slice(0,12)}…
                          </span>
                          <span className="text-gray-500 text-xs">{new Date(alert.created_at).toLocaleString()}</span>
                        </div>

                        {/* Message */}
                        <p className="text-white text-base font-semibold mb-4 leading-relaxed">{alert.alert_message}</p>

                        {/* Metrics */}
                        <div className="grid grid-cols-4 gap-3 mb-3">
                          <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                            <div className="text-gray-400 text-xs mb-1">Baseline Risk</div>
                            <div className="text-blue-300 text-lg font-black">{(alert.baseline_risk*100).toFixed(1)}%</div>
                          </div>
                          <div className="bg-gradient-to-br from-red-900/50 to-orange-900/50 rounded-lg p-3 border border-red-700">
                            <div className="text-red-300 text-xs mb-1">Current Live Risk</div>
                            <div className="text-red-200 text-lg font-black">{(alert.current_live_risk*100).toFixed(1)}%</div>
                          </div>
                          <div className="bg-gradient-to-br from-orange-900/50 to-yellow-900/50 rounded-lg p-3 border border-orange-700">
                            <div className="text-orange-300 text-xs mb-1">Risk Delta</div>
                            <div className="text-orange-200 text-lg font-black">+{(alert.risk_delta*100).toFixed(1)}%</div>
                          </div>
                          <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                            <div className="text-gray-400 text-xs mb-1">Triggered By</div>
                            <div className="text-cyan-300 text-xs font-bold truncate">{(alert.triggered_by||[]).join(', ')}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {loading && (
        <div className="text-center py-16">
          <RefreshCw size={48} className="mx-auto mb-4 text-indigo-500 animate-spin" />
          <p className="text-gray-300 text-lg font-semibold">Scanning live events...</p>
          <p className="text-gray-500 text-sm mt-2">Matching against active contracts</p>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE-2 TAB: BULK AUTO-CORRECT GRID
// ═══════════════════════════════════════════════════════════════════════════════
const BulkAutoCorrectTab = ({ contract }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState({});

  const parseClauses = (text) => {
    return text.split('\n---\n').filter(t=>t.trim()).map((t,i) => ({
      id: `clause_${i+1}`,
      text: t.trim(),
      type: 'GENERAL',
    }));
  };

  const run = async () => {
    const sourceText = contract?.contract_text?.trim();
    if (!sourceText) {
      setError('No contract text — go to the Risk Predictor tab and run analysis first.');
      return;
    }
    const clauses = parseClauses(sourceText);
    if (!clauses.length) { setError('No clauses found in contract text.'); return; }
    setLoading(true); setError('');
    try { setData(await bulkAutoCorrect(clauses)); }
    catch (e) { setError(e.response?.data?.error || e.message); }
    finally { setLoading(false); }
  };

  const statusColors = {
    strong: { color: '#10B981', bg: 'from-green-600 to-emerald-600', border: 'border-green-500', icon: '✓', label: 'Strong' },
    weak: { color: '#F59E0B', bg: 'from-yellow-600 to-orange-600', border: 'border-yellow-500', icon: '⚠', label: 'Weak' },
    missing: { color: '#EF4444', bg: 'from-red-600 to-red-800', border: 'border-red-500', icon: '✗', label: 'Missing' }
  };

  // Invert risk score to protection score (100% protection = 0% risk)
  const protectionScore = data ? 100 - data.risk_score : 0;

  const getProtectionLevel = (score) => {
    if (score >= 90) return { label: 'EXCELLENT', color: '#10B981', bg: 'from-green-600 to-emerald-600', icon: '🛡️' };
    if (score >= 70) return { label: 'GOOD', color: '#3B82F6', bg: 'from-blue-600 to-cyan-600', icon: '✅' };
    if (score >= 50) return { label: 'FAIR', color: '#F59E0B', bg: 'from-yellow-600 to-orange-600', icon: '⚠️' };
    return { label: 'POOR', color: '#EF4444', bg: 'from-red-600 to-red-800', icon: '⛔' };
  };

  return (
    <div className="space-y-6">
      {/* Stunning Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 p-6 shadow-2xl">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-white/10 rounded-xl backdrop-blur-sm">
              <Filter className="text-white" size={28} />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white">Force Majeure Clause Auditor Grid</h2>
              <p className="text-purple-200 text-sm mt-1">Bulk audit all clauses — color-coded by Force Majeure coverage status with one-click auto-fix</p>
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-indigo-700/50 rounded-xl px-5 py-4 shadow-lg">
        <div className="flex items-start gap-3">
          <Info className="text-indigo-400 flex-shrink-0 mt-0.5" size={20} />
          <div className="text-sm">
            <p className="text-gray-300 mb-2">
              Uses contract text from the <span className="text-white font-bold bg-indigo-600/30 px-2 py-0.5 rounded">Risk Predictor</span> tab.
            </p>
            <p className="text-gray-400 text-xs">
              Separate clauses with <code className="bg-yellow-600/20 text-yellow-300 px-2 py-0.5 rounded font-mono">---</code> on its own line, or the entire text will be treated as one clause.
            </p>
          </div>
        </div>
      </div>

      {/* Run Button */}
      <button onClick={run} disabled={loading}
        className="group relative w-full overflow-hidden bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-700 hover:via-indigo-700 hover:to-blue-700 rounded-xl px-6 py-4 text-white font-bold shadow-2xl shadow-indigo-900/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98]">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000"></div>
        <div className="relative flex items-center justify-center gap-3">
          {loading ? (
            <>
              <RefreshCw size={20} className="animate-spin" />
              <span className="text-lg">Auditing Clauses...</span>
            </>
          ) : (
            <>
              <Filter size={20} className="group-hover:animate-pulse" />
              <span className="text-lg">Run Bulk Audit</span>
            </>
          )}
        </div>
      </button>

      {error && (
        <div className="bg-gradient-to-r from-red-900/60 to-red-800/60 border-2 border-red-500 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-red-200">
            <AlertTriangle size={20} />
            <span className="font-semibold">{error}</span>
          </div>
        </div>
      )}

      {data && (
        <>
          {/* Enhanced Metrics Grid */}
          <div className="grid grid-cols-4 gap-4">
            <div className="group relative overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 border border-gray-700 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <FileText className="text-blue-400" size={24} />
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-bold">Total</span>
                </div>
                <div className="text-4xl font-black text-white mb-1">{data.total_clauses}</div>
                <div className="text-gray-400 text-xs font-semibold">Total Clauses</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-green-900/40 to-emerald-900/40 rounded-2xl p-6 border-2 border-green-600/50 shadow-xl shadow-green-900/30 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/20 to-emerald-500/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <CheckCircle className="text-green-400" size={24} />
                  <span className="text-xs text-green-300 uppercase tracking-wider font-bold">Strong</span>
                </div>
                <div className="text-4xl font-black text-green-300 mb-1">{data.stats?.strong||0}</div>
                <div className="text-green-200 text-xs font-semibold">Excellent Protection</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-yellow-900/40 to-orange-900/40 rounded-2xl p-6 border-2 border-yellow-600/50 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/20 to-orange-500/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <AlertTriangle className="text-yellow-400" size={24} />
                  <span className="text-xs text-yellow-300 uppercase tracking-wider font-bold">Weak</span>
                </div>
                <div className="text-4xl font-black text-yellow-300 mb-1">{data.stats?.weak||0}</div>
                <div className="text-yellow-200 text-xs font-semibold">Needs Improvement</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-red-900/40 to-red-800/40 rounded-2xl p-6 border-2 border-red-600/50 shadow-xl shadow-red-900/30 hover:shadow-2xl hover:scale-105 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-red-500/20 to-red-700/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <XCircle className="text-red-400" size={24} />
                  <span className="text-xs text-red-300 uppercase tracking-wider font-bold">Missing</span>
                </div>
                <div className="text-4xl font-black text-red-300 mb-1">{data.stats?.missing||0}</div>
                <div className="text-red-200 text-xs font-semibold">Requires Force Majeure Clause</div>
              </div>
            </div>
          </div>

          {/* Coverage & Protection Score Cards */}
          <div className="grid grid-cols-2 gap-6">
            {/* Coverage Score */}
            <div className="relative overflow-hidden bg-gradient-to-br from-green-900/40 to-emerald-900/40 rounded-2xl p-8 border-2 border-green-500 shadow-2xl shadow-green-900/50">
              <div className="absolute inset-0 bg-black/20"></div>
              <div className="absolute top-0 right-0 w-64 h-64 bg-green-500/10 rounded-full blur-3xl"></div>
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-green-500/20 rounded-xl">
                    <Shield className="text-green-300" size={32} />
                  </div>
                  <div>
                    <div className="text-green-300 text-sm font-bold uppercase tracking-wider">Coverage Score</div>
                    <div className="text-green-200/70 text-xs">Strong clauses / Total clauses</div>
                  </div>
                </div>
                <div className="text-7xl font-black text-white drop-shadow-2xl mb-2">{data.coverage_score}%</div>
                <div className="h-3 bg-green-950 rounded-full overflow-hidden shadow-inner">
                  <div className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all duration-1000 shadow-lg"
                    style={{width: `${data.coverage_score}%`}}></div>
                </div>
                <div className="mt-3 text-green-200 text-xs">Higher is better — measures strong Force Majeure protection</div>
              </div>
            </div>

            {/* Protection Score (Inverted Risk) */}
            <div className={`relative overflow-hidden bg-gradient-to-br ${getProtectionLevel(protectionScore).bg} rounded-2xl p-8 border-2 shadow-2xl`}
              style={{borderColor: getProtectionLevel(protectionScore).color}}>
              <div className="absolute inset-0 bg-black/20"></div>
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl"></div>
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-white/20 rounded-xl">
                    <Activity className="text-white" size={32} />
                  </div>
                  <div>
                    <div className="text-white text-sm font-bold uppercase tracking-wider flex items-center gap-2">
                      <span>Protection Score</span>
                      <span className="text-2xl">{getProtectionLevel(protectionScore).icon}</span>
                    </div>
                    <div className="text-white/70 text-xs">100% - Risk Score (inverted)</div>
                  </div>
                </div>
                <div className="text-7xl font-black text-white drop-shadow-2xl mb-2 animate-pulse">{protectionScore.toFixed(0)}%</div>
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-black/30 rounded-full backdrop-blur-sm">
                  <span className="text-white font-black text-sm uppercase tracking-wider">{getProtectionLevel(protectionScore).label}</span>
                </div>
                <div className="mt-3 text-white/80 text-xs">
                  {protectionScore >= 90 ? '✓ Fully protected against Force Majeure risks' :
                   protectionScore >= 70 ? '⚠ Good protection, minor improvements needed' :
                   protectionScore >= 50 ? '⚠ Fair protection, needs strengthening' :
                   '✗ Poor protection, immediate action required'}
                </div>
                <div className="mt-2 flex items-center gap-2 text-white/60 text-xs">
                  <Info size={12} />
                  <span>Lower risk = Higher protection (0% risk = 100% protection)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Clause Cards - Beautiful Design */}
          <div className="bg-gradient-to-br from-gray-800 via-gray-900 to-black rounded-2xl border border-gray-700 shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-purple-900/50 to-indigo-900/50 px-6 py-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <FileText className="text-purple-300" size={20} />
                </div>
                <h3 className="text-white font-bold text-lg">Clause Analysis Results</h3>
              </div>
              <p className="text-gray-400 text-xs mt-1">Click to expand and view auto-fix suggestions</p>
            </div>
            <div className="p-4 space-y-3">
              {(data.grid||[]).map((row,i)=>{
                const config = statusColors[row.fm_status];
                return (
                  <div key={i} className={`group relative overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border-2 ${config.border} shadow-lg hover:shadow-2xl transition-all duration-300`}>
                    <div className="absolute inset-0 opacity-5" style={{background: `linear-gradient(135deg, ${config.color} 0%, transparent 100%)`}}></div>
                    <div className="relative z-10 p-4 cursor-pointer"
                      onClick={()=>setExpanded(p=>({...p,[i]:!p[i]}))}>
                      <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl shadow-lg" style={{background: `${config.color}33`, border: `2px solid ${config.color}66`}}>
                          <span className="text-2xl">{config.icon}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <span className="px-3 py-1 rounded-lg font-black text-xs text-white shadow-lg"
                              style={{background: `linear-gradient(135deg, ${config.color} 0%, ${config.color}CC 100%)`}}>
                              {config.label.toUpperCase()}
                            </span>
                            <span className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300 font-semibold">{row.type}</span>
                            <span className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-400">
                              Strong: {row.strong_indicators_found} · Weak: {row.weak_indicators_found}
                            </span>
                          </div>
                          <p className="text-gray-300 text-sm leading-relaxed group-hover:text-white transition-colors">
                            {row.text_preview}
                          </p>
                        </div>
                        <ChevronRight size={20} className={`text-gray-500 transition-transform duration-300 ${expanded[i]?'rotate-90':'rotate-0'}`} />
                      </div>
                    </div>
                    {expanded[i] && (
                      <div className="border-t" style={{borderColor: `${config.color}50`}}>
                        <div className="p-5 bg-gradient-to-br from-gray-900/50 to-black/50 space-y-4">
                          {/* Full Clause Text */}
                          <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
                            <div className="flex items-center gap-2 mb-3">
                              <FileText className="text-gray-400" size={16} />
                              <span className="text-gray-300 font-bold text-sm uppercase tracking-wider">Full Clause Text</span>
                            </div>
                            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{row.full_text || row.text_preview}</p>
                          </div>

                          {/* Auto-Fix Suggestion */}
                          <div className="p-4 bg-yellow-900/20 border-l-4 border-yellow-500 rounded-r-lg">
                            <div className="flex items-center gap-2 mb-3">
                              <Zap className="text-yellow-400" size={16} />
                              <span className="text-yellow-300 font-bold text-sm uppercase tracking-wider">Auto-Fix Suggestion</span>
                            </div>
                            <p className="text-gray-300 text-sm leading-relaxed">{row.auto_fix}</p>
                          </div>

                          {/* Priority Badge */}
                          <div className="flex items-center gap-2">
                            <span className="text-gray-400 text-xs font-semibold">Priority:</span>
                            <span className={`px-3 py-1 rounded-lg font-bold text-xs ${
                              row.priority === 'HIGH' ? 'bg-red-600 text-white' :
                              row.priority === 'MEDIUM' ? 'bg-yellow-600 text-white' :
                              'bg-green-600 text-white'
                            }`}>
                              {row.priority}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {loading && (
        <div className="text-center py-16">
          <RefreshCw size={48} className="mx-auto mb-4 text-indigo-500 animate-spin" />
          <p className="text-gray-300 text-lg font-semibold">Analyzing clauses...</p>
          <p className="text-gray-500 text-sm mt-2">Scanning for Force Majeure coverage indicators</p>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════
export default function ForceMajeureDashboard() {
  const [activeTab, setActiveTab] = useState('predict');
  const [liveEvents, setLiveEvents] = useState([]);
  const [liveLoading, setLiveLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // ── Contract inputs (live on Predict tab) ─────────────────────────────────
  const [contract, setContract] = useState({
    contract_text: '', contract_title: '', contract_value: '',
    jurisdiction: '', project_location: '', supplier_locations: '',
  });
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [predError, setPredError] = useState('');

  const handlePredict = async () => {
    if (!contract.contract_text.trim()) { setPredError('Paste contract text first'); return; }
    setPredicting(true); setPredError(''); setPrediction(null);
    try {
      const data = await predictFMRisk({
        contract_text: contract.contract_text,
        contract_title: contract.contract_title,
        contract_value: parseFloat(contract.contract_value) || 0,
        jurisdiction: contract.jurisdiction,
      });
      setPrediction(data);
    } catch (e) {
      setPredError(e.response?.data?.error || e.message);
    } finally {
      setPredicting(false);
    }
  };

  useEffect(() => {
    const fetchLive = async () => {
      setLiveLoading(true);
      try {
        const data = await getLiveEvents('all', '', 0.5);
        setLiveEvents((data.events || []).slice(0, 5));
      } catch (e) {
        // silent
      } finally {
        setLiveLoading(false);
      }
    };
    fetchLive();
  }, []);

  // ── Auto-populate contract from Dashboard navigation ──────────────────────
  useEffect(() => {
    if (location.state) {
      const { contractId, contractTitle, contractText, contractValue, jurisdiction, projectLocation, supplierLocations } = location.state;
      if (contractText) {
        setContract(prev => ({
          ...prev,
          contract_text: contractText || '',
          contract_title: contractTitle || '',
          contract_value: contractValue || '',
          jurisdiction: jurisdiction || '',
          project_location: projectLocation || '',
          supplier_locations: supplierLocations || '',
        }));
        // Auto-run prediction if contract text is provided
        setTimeout(() => {
          if (contractText.trim()) {
            handlePredict();
          }
        }, 500);
      }
    }
  }, [location.state]);

  const cp = contract; // shorthand

  const renderTab = () => {
    switch (activeTab) {
      case 'predict':        return <RiskPredictorTab contract={cp} setContract={setContract} onPredict={handlePredict} loading={predicting} result={prediction} error={predError} />;
      case 'audit':          return <ClauseAuditorTab contract={cp} />;
      case 'war':            return <WarRiskTab contract={cp} />;
      case 'scenario':       return <ScenarioSimTab contract={cp} />;
      case 'graph':          return <RiskGraphTab prediction={prediction} />;
      case 'terminal':       return <LiveTerminalTab />;
      case 'counterfactual': return <CounterfactualTab contract={cp} prediction={prediction} />;
      case 'portfolio_sim':  return <PortfolioSimTab contract={cp} prediction={prediction} />;
      case 'kg':             return <KnowledgeGraphTab prediction={prediction} />;
      case 'twin':           return <DigitalTwinTab contract={cp} />;
      case 'negotiation':    return <MultiAgentNegotiationTab contract={cp} prediction={prediction} />;
      case 'supply':         return <SupplyChainTab contract={cp} />;
      case 'dynamic_priors': return <DynamicPriorsTab />;
      case 'risk_cascade':   return <RiskCascadeTab contract={cp} prediction={prediction} />;
      case 'clause_opt':     return <ClauseOptimizerTab contract={cp} />;
      case 'temporal':       return <TemporalForecastTab contract={cp} />;
      case 'formula':        return <RiskFormulaTab contract={cp} />;
      case 'howit':          return <HowItWorksTab />;
      default:               return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-900">
                <Shield size={20} className="text-red-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Force Majeure Intelligence Engine</h1>
                <p className="text-gray-400 text-sm">Bayesian Risk · Monte Carlo · War Risk · Clause Auditor · Live Terminal · Digital Twin · Multi-Agent Negotiation</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-red-900 text-red-300 text-xs font-bold rounded">NEW</span>
            <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">35-Node Bayesian</span>
            <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">Monte Carlo</span>
          </div>
        </div>
      </div>

      {/* Live Events Ticker */}
      {liveEvents.length > 0 && (
        <div className="bg-gray-950 border-b border-gray-800 px-4 py-1.5 flex items-center gap-3 overflow-hidden">
          <span className="text-red-400 text-xs font-bold shrink-0 flex items-center gap-1">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
            </span>
            LIVE
          </span>
          <div className="flex gap-4 overflow-x-auto text-xs text-gray-400 scrollbar-none">
            {liveEvents.map((ev, i) => (
              <span key={i} className="whitespace-nowrap flex items-center gap-1">
                <span>{ev.event_type === 'war' ? '⚔️' : ev.event_type === 'natural_disaster' ? '🌊' : ev.event_type === 'sanctions' ? '🚫' : '⚡'}</span>
                <span className="text-gray-300">{ev.title?.slice(0, 60)}</span>
                <span className="text-gray-600">· {ev.location}</span>
                {i < liveEvents.length - 1 && <span className="text-gray-700 ml-2">|</span>}
              </span>
            ))}
          </div>
          <button onClick={() => setActiveTab('terminal')}
            className="ml-auto shrink-0 text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition">
            <Radio size={11} /> Live Terminal
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-700 bg-gray-800">
        <div className="flex overflow-x-auto px-6">
          {TABS.map(({ id, label, icon: Icon }) => {
            const isPredictTab = id === 'predict' || id === 'howit' || id === 'terminal' || id === 'dynamic_priors';
            const isLocked = !isPredictTab && !prediction;
            return (
              <button
                key={id}
                onClick={() => {
                  if (isLocked) {
                    alert('🔒 Please run FM Risk Analysis on the Predict tab first to unlock this feature');
                  } else {
                    setActiveTab(id);
                  }
                }}
                title={isLocked ? '🔒 Run Force Majeure Risk Analysis first' : ''}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                  activeTab === id
                    ? 'border-red-500 text-red-400'
                    : isLocked
                    ? 'border-transparent text-gray-600 cursor-not-allowed'
                    : 'border-transparent text-gray-400 hover:text-gray-200'
                }`}
              >
                {isLocked ? <Lock size={12} className="text-gray-600" /> : <Icon size={14} />}
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto p-6">{renderTab()}</div>
    </div>
  );
}
