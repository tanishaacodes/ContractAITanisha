/**
 * Force Majeure — Advanced Features Dashboard
 * =============================================
 * Tabs:
 *   1. Counterfactual Risk Engine
 *   2. Portfolio Simulation
 *   3. FM Knowledge Graph
 *   4. Contract Digital Twin
 *   5. Multi-Agent Negotiation
 *   6. Supply Chain Map
 */
import React, { useState, useEffect } from 'react';
import {
  GitBranch, Globe, Activity, Cpu, Users, Truck,
  Play, RefreshCw, AlertTriangle, CheckCircle, Info,
  TrendingDown, TrendingUp, BarChart2, Zap, Shield,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, PieChart, Pie, Cell, Legend,
} from 'recharts';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import {
  runCounterfactual,
  simulatePortfolio,
  getFMKnowledgeGraph,
  runDigitalTwin,
  runMultiAgentNegotiate,
  getSupplyChainMap,
  FM_SCENARIO_TEMPLATES,
} from '../services/forceMajeureService';

const TABS = [
  { id: 'counterfactual', label: 'Counterfactual', icon: GitBranch, color: 'text-purple-400' },
  { id: 'portfolio_sim', label: 'Portfolio Sim', icon: BarChart2, color: 'text-blue-400' },
  { id: 'knowledge_graph', label: 'Knowledge Graph', icon: Globe, color: 'text-cyan-400' },
  { id: 'digital_twin', label: 'Digital Twin', icon: Cpu, color: 'text-green-400' },
  { id: 'negotiation', label: 'Multi-Agent Nego', icon: Users, color: 'text-yellow-400' },
  { id: 'supply_chain', label: 'Supply Chain', icon: Truck, color: 'text-orange-400' },
];

const RISK_COLORS = {
  CRITICAL: '#F16667', HIGH: '#F79767', MEDIUM: '#FFD86E', LOW: '#68BC00',
};
const PIE_COLORS = ['#F16667', '#F79767', '#FFD86E', '#68BC00', '#4C8EDA', '#9063CD'];

const fmt = (v) => (v === undefined || v === null ? '—' : typeof v === 'number' ? v.toLocaleString() : v);
const fmtUSD = (v) => v ? `$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '$0';
const fmtPct = (v) => v !== undefined ? `${Math.round(v * 100)}%` : '—';

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 1: COUNTERFACTUAL RISK ENGINE
// ═══════════════════════════════════════════════════════════════════════════════
function CounterfactualTab() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [contractText, setContractText] = useState('This construction contract governs EPC works in Ukraine. The contractor shall supply materials via Black Sea ports. In case of war, hostilities, trade sanctions, or embargo, either party may suspend performance.');
  const [contractValue, setContractValue] = useState(5000000);
  const [baseEvents, setBaseEvents] = useState('war:0.80, trade_sanctions:0.70, energy_crisis:0.60');
  const [removeEvents, setRemoveEvents] = useState('war');

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const base_evidence = {};
      baseEvents.split(',').forEach(pair => {
        const [k, v] = pair.split(':').map(s => s.trim());
        if (k && v) base_evidence[k] = parseFloat(v);
      });
      const remove = removeEvents.split(',').map(s => s.trim()).filter(Boolean);
      const res = await runCounterfactual({
        contract_text: contractText,
        contract_value: contractValue,
        base_evidence,
        remove_events: remove,
      });
      setResult(res);
    } catch (e) {
      setError(e?.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-purple-900">
        <p className="text-gray-400 text-sm mb-4">
          Answers: <em>"What would FM risk have been if [event] had NOT occurred?"</em> — isolates causal contribution of each root event.
        </p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Contract Text</label>
            <textarea value={contractText} onChange={e => setContractText(e.target.value)}
              className="w-full h-24 bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200 resize-none" />
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Contract Value (USD)</label>
              <input type="number" value={contractValue} onChange={e => setContractValue(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Base Evidence (key:value, comma-sep)</label>
              <input value={baseEvents} onChange={e => setBaseEvents(e.target.value)}
                placeholder="war:0.8, trade_sanctions:0.7"
                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Events to Remove (counterfactual)</label>
              <input value={removeEvents} onChange={e => setRemoveEvents(e.target.value)}
                placeholder="war, trade_sanctions"
                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200" />
            </div>
          </div>
        </div>
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 px-5 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50">
          <Play size={14} /> {loading ? 'Analyzing…' : 'Run Counterfactual'}
        </button>
        {error && <div className="mt-2 text-red-400 text-xs">{error}</div>}
      </div>

      {result && (
        <div className="space-y-4">
          {/* Comparison KPIs */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Baseline FM Risk', v: fmtPct(result.baseline?.fm_risk_score), color: 'text-red-400' },
              { label: 'Counterfactual Risk', v: fmtPct(result.counterfactual?.fm_risk_score), color: 'text-green-400' },
              { label: 'Risk Reduction', v: `${result.delta_analysis?.pct_risk_reduction}%`, color: 'text-purple-400' },
              { label: 'Baseline Loss', v: fmtUSD(result.baseline?.expected_loss_usd), color: 'text-red-400' },
              { label: 'CF Loss', v: fmtUSD(result.counterfactual?.expected_loss_usd), color: 'text-green-400' },
              { label: 'Loss Saved', v: fmtUSD(result.delta_analysis?.loss_reduction_usd), color: 'text-yellow-400' },
            ].map((kpi, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700 text-center">
                <div className={`text-xl font-bold ${kpi.color}`}>{kpi.v}</div>
                <div className="text-gray-500 text-xs mt-1">{kpi.label}</div>
              </div>
            ))}
          </div>

          {/* Insight */}
          <div className="bg-gray-800 border border-purple-800 rounded-xl p-4">
            <div className="text-purple-300 text-sm font-medium mb-1">AI Insight</div>
            <p className="text-gray-300 text-sm">{result.insight}</p>
          </div>

          {/* Causal attribution */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">Causal Attribution</div>
            <div className="space-y-2">
              {(result.causal_attribution || []).map((a, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-gray-400 text-xs w-36 capitalize">{a.event?.replace(/_/g,' ')}</span>
                  <div className="flex-1 bg-gray-700 rounded-full h-2">
                    <div className="h-2 rounded-full bg-purple-500" style={{ width: `${Math.min(100, a.contribution_pct)}%` }} />
                  </div>
                  <span className="text-purple-400 text-xs w-12 text-right">{a.contribution_pct?.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Outcome deltas table */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">Outcome Probability Deltas</div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-gray-300">
                <thead><tr className="text-gray-500 border-b border-gray-700">
                  <th className="text-left py-1">Outcome</th>
                  <th className="text-right">Baseline</th>
                  <th className="text-right">Counterfactual</th>
                  <th className="text-right">Delta</th>
                </tr></thead>
                <tbody>
                  {Object.entries(result.delta_analysis?.outcome_deltas || {}).map(([k, v]) => (
                    <tr key={k} className="border-b border-gray-800">
                      <td className="py-1 capitalize">{k.replace(/_/g,' ')}</td>
                      <td className="text-right text-red-400">{fmtPct(v.baseline)}</td>
                      <td className="text-right text-green-400">{fmtPct(v.counterfactual)}</td>
                      <td className={`text-right font-bold ${v.delta < 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {v.delta >= 0 ? '+' : ''}{(v.delta * 100).toFixed(1)}pp
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// TAB 2: PORTFOLIO SIMULATION
// ═══════════════════════════════════════════════════════════════════════════════
function PortfolioSimTab() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [scenarioType, setScenarioType] = useState('war_escalation');

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await simulatePortfolio({ scenario_type: scenarioType, iterations: 1000 });
      setResult(res);
    } catch (e) {
      setError(e?.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  const pieData = result ? [
    { name: 'Critical', value: result.portfolio_summary?.critical_risk_contracts || 0 },
    { name: 'High', value: result.portfolio_summary?.high_risk_contracts || 0 },
    { name: 'Others', value: Math.max(0, (result.portfolio_summary?.total_contracts || 0) - (result.portfolio_summary?.critical_risk_contracts || 0) - (result.portfolio_summary?.high_risk_contracts || 0)) },
  ] : [];

  const barData = result ? Object.entries(result.industry_breakdown || {}).map(([k, v]) => ({
    name: k,
    exposure: Math.round((v.total_exposure || 0) / 1e6 * 10) / 10,
    risk: Math.round((v.avg_risk || 0) * 100),
  })) : [];

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-blue-900">
        <p className="text-gray-400 text-sm mb-4">Simulates a global FM event across your entire portfolio — calculates per-contract exposure and industry breakdown.</p>
        <div className="flex items-center gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Scenario</label>
            <select value={scenarioType} onChange={e => setScenarioType(e.target.value)}
              className="bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200">
              {FM_SCENARIO_TEMPLATES.map(t => (
                <option key={t.id} value={t.id}>{t.icon} {t.name}</option>
              ))}
            </select>
          </div>
          <button onClick={handleRun} disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50 self-end">
            <Play size={14} /> {loading ? 'Simulating…' : 'Run Portfolio Sim'}
          </button>
        </div>
        {error && <div className="text-red-400 text-xs">{error}</div>}
      </div>

      {result && (
        <div className="space-y-4">
          {/* KPIs */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Total Contracts', v: result.portfolio_summary?.total_contracts, color: 'text-blue-400' },
              { label: 'Critical Risk', v: result.portfolio_summary?.critical_risk_contracts, color: 'text-red-400' },
              { label: 'Total Exposure', v: fmtUSD(result.portfolio_summary?.total_expected_exposure_usd), color: 'text-yellow-400' },
              { label: 'Worst Case', v: fmtUSD(result.portfolio_summary?.total_worst_case_exposure_usd), color: 'text-orange-400' },
            ].map((kpi, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700 text-center">
                <div className={`text-2xl font-bold ${kpi.color}`}>{kpi.v}</div>
                <div className="text-gray-500 text-xs mt-1">{kpi.label}</div>
              </div>
            ))}
          </div>

          {/* Pie + Bar */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-2">Risk Distribution</div>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70}>
                    {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', color: '#fff', fontSize: 11 }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-2">Exposure by Industry (M USD)</div>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={barData} barSize={18}>
                  <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 9 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 9 }} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', color: '#fff', fontSize: 11 }} />
                  <Bar dataKey="exposure" fill="#4C8EDA" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top 5 at risk */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">Top 5 Contracts at Risk</div>
            <div className="space-y-2">
              {(result.top_5_at_risk || []).map((c, i) => (
                <div key={i} className="flex items-center gap-3 p-2 bg-gray-900 rounded-lg">
                  <span className="text-gray-500 text-xs w-4">{i + 1}</span>
                  <span className="text-gray-200 text-xs flex-1 truncate">{c.contract_title}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded font-bold" style={{ background: (RISK_COLORS[c.risk_label] || '#374151') + '33', color: RISK_COLORS[c.risk_label] || '#9ca3af' }}>
                    {c.risk_label}
                  </span>
                  <span className="text-yellow-400 text-xs w-16 text-right">{fmtUSD(c.expected_loss_usd)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// TAB 3: FM KNOWLEDGE GRAPH
// ═══════════════════════════════════════════════════════════════════════════════
function KnowledgeGraphTab() {
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [focus, setFocus] = useState('all');
  const [depth, setDepth] = useState(3);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const res = await getFMKnowledgeGraph(focus, depth);
      setGraphData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadGraph(); }, []);

  const handleEdgesForReactFlow = (edges) => edges.map(e => ({
    ...e,
    markerEnd: { type: 'arrowclosed', color: e.style?.stroke || '#555' },
  }));

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <select value={focus} onChange={e => setFocus(e.target.value)}
          className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200">
          <option value="all">All Events</option>
          <option value="war">War & Geopolitical</option>
          <option value="pandemic">Pandemic & Health</option>
          <option value="supply_chain">Supply Chain</option>
        </select>
        <select value={depth} onChange={e => setDepth(Number(e.target.value))}
          className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200">
          <option value={1}>Depth 1 — Root Events</option>
          <option value={2}>Depth 2 — Disruptions</option>
          <option value={3}>Depth 3 — Full Graph</option>
        </select>
        <button onClick={loadGraph} disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-700 hover:bg-cyan-800 rounded-lg text-white text-sm transition">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Load Graph
        </button>
        {graphData && (
          <div className="text-xs text-gray-500 ml-auto">
            {graphData.stats?.total_nodes} nodes · {graphData.stats?.total_edges} edges
          </div>
        )}
      </div>

      {/* Legend */}
      {graphData?.legend && (
        <div className="flex flex-wrap gap-2">
          {graphData.legend.map((l, i) => (
            <span key={i} className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full"
              style={{ background: l.color + '22', color: l.color, border: `1px solid ${l.color}44` }}>
              <span className="w-2 h-2 rounded-full inline-block" style={{ background: l.color }} />
              {l.label}
            </span>
          ))}
        </div>
      )}

      {/* React Flow Graph */}
      <div className="bg-gray-950 border border-gray-700 rounded-xl" style={{ height: 650 }}>
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">Loading knowledge graph…</div>
        ) : graphData ? (
          <ReactFlow
            nodes={graphData.nodes || []}
            edges={handleEdgesForReactFlow(graphData.edges || [])}
            fitView
            attributionPosition="bottom-right"
          >
            <Background color="#374151" gap={20} />
            <Controls />
            <MiniMap style={{ background: '#111827' }} nodeColor={(n) => n.style?.background || '#555'} />
          </ReactFlow>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm">Click "Load Graph" to visualize</div>
        )}
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// TAB 4: CONTRACT DIGITAL TWIN
// ═══════════════════════════════════════════════════════════════════════════════
function DigitalTwinTab() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    contract_text: 'This EPC contract for oil refinery construction in Ukraine requires delivery of equipment via Black Sea ports and European supply chains. The contract value is USD 10,000,000. Force majeure events include war, sanctions, and pandemic.',
    contract_value: 10000000,
    contract_title: 'EPC Ukraine Refinery',
    jurisdiction: 'Ukraine',
    industry: 'Energy',
    project_location: 'Ukraine',
    supplier_locations: 'Germany, Poland',
  });

  const upd = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await runDigitalTwin({
        ...form,
        contract_value: parseFloat(form.contract_value),
        supplier_locations: form.supplier_locations.split(',').map(s => s.trim()).filter(Boolean),
      });
      setResult(res);
    } catch (e) {
      setError(e?.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  const healthColor = result ? (result.health?.score > 0.7 ? '#68BC00' : result.health?.score > 0.4 ? '#F79767' : '#F16667') : '#4C8EDA';

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-green-900">
        <p className="text-gray-400 text-sm mb-4">
          Creates a real-time digital twin of your contract — pulls live global events and continuously simulates FM risk impact.
        </p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Contract Text</label>
            <textarea value={form.contract_text} onChange={upd('contract_text')}
              className="w-full h-28 bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              ['contract_title', 'Contract Title', 'text'],
              ['contract_value', 'Value (USD)', 'number'],
              ['industry', 'Industry', 'text'],
              ['jurisdiction', 'Jurisdiction', 'text'],
              ['project_location', 'Project Location', 'text'],
              ['supplier_locations', 'Supplier Locations (CSV)', 'text'],
            ].map(([k, label, type]) => (
              <div key={k}>
                <label className="text-xs text-gray-400 mb-1 block">{label}</label>
                <input type={type} value={form[k]} onChange={upd(k)}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-xs text-gray-200" />
              </div>
            ))}
          </div>
        </div>
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 px-5 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50">
          <Cpu size={14} /> {loading ? 'Initializing Twin…' : 'Create Digital Twin'}
        </button>
        {error && <div className="mt-2 text-red-400 text-xs">{error}</div>}
      </div>

      {result && (
        <div className="space-y-4">
          {/* Health gauge */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 flex items-center gap-6">
            <div className="text-center">
              <div className="text-5xl font-bold" style={{ color: healthColor }}>
                {Math.round(result.health?.score * 100)}
              </div>
              <div className="text-gray-500 text-xs mt-1">Health Score</div>
            </div>
            <div className="flex-1">
              <div className="text-white font-semibold text-lg mb-1">{result.contract_title}</div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs px-2 py-0.5 rounded font-bold"
                  style={{ background: healthColor + '22', color: healthColor }}>
                  {result.health?.label}
                </span>
                <span className="text-gray-500 text-xs">Twin ID: {result.twin_id}</span>
              </div>
              <div className="text-xs text-gray-400">
                {result.live_risk?.live_events_detected} live events detected · FM Risk: {fmtPct(result.live_risk?.fm_risk_score)}
              </div>
            </div>
          </div>

          {/* Risk KPIs */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'FM Invocation', v: fmtPct(result.live_risk?.fm_invocation_prob), color: 'text-red-400' },
              { label: 'Project Delay', v: fmtPct(result.live_risk?.project_delay_prob), color: 'text-orange-400' },
              { label: 'Expected Loss', v: fmtUSD(result.financial_exposure?.expected_loss_usd), color: 'text-yellow-400' },
              { label: 'P95 Loss', v: fmtUSD(result.financial_exposure?.p95_loss_usd), color: 'text-red-400' },
            ].map((k, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700 text-center">
                <div className={`text-xl font-bold ${k.color}`}>{k.v}</div>
                <div className="text-gray-500 text-xs mt-1">{k.label}</div>
              </div>
            ))}
          </div>

          {/* Exposure timeline */}
          {result.exposure_timeline && (
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3">12-Month FM Exposure Forecast</div>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={result.exposure_timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 10 }} />
                  <YAxis yAxisId="left" tick={{ fill: '#6b7280', fontSize: 10 }} tickFormatter={v => `${(v/1e6).toFixed(1)}M`} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6b7280', fontSize: 10 }} tickFormatter={v => `${Math.round(v*100)}%`} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', color: '#fff', fontSize: 11 }}
                    formatter={(v, name) => name === 'expected_loss_usd' ? [fmtUSD(v), 'Exp. Loss'] : [fmtPct(v), 'FM Risk']} />
                  <Line yAxisId="left" type="monotone" dataKey="expected_loss_usd" stroke="#F79767" strokeWidth={2} dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="fm_risk" stroke="#F16667" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Stress scenarios */}
          {result.stress_scenarios && (
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3">Stress Test Scenarios</div>
              <div className="space-y-2">
                {result.stress_scenarios.map((s, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 bg-gray-900 rounded-lg">
                    <span className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                    <span className="text-gray-300 text-xs w-40">{s.scenario}</span>
                    <div className="flex-1 bg-gray-700 rounded-full h-2">
                      <div className="h-2 rounded-full" style={{ width: `${Math.round(s.fm_risk_score * 100)}%`, background: s.color }} />
                    </div>
                    <span className="text-xs font-bold w-10 text-right" style={{ color: s.color }}>
                      {Math.round(s.fm_risk_score * 100)}%
                    </span>
                    <span className="text-gray-400 text-xs w-24 text-right">{fmtUSD(s.expected_loss_usd)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          {result.recommended_actions && (
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="text-gray-300 text-sm font-semibold mb-3">Recommended Actions</div>
              <div className="space-y-2">
                {result.recommended_actions.map((a, i) => {
                  const pc = { CRITICAL: '#F16667', HIGH: '#F79767', MEDIUM: '#FFD86E', LOW: '#68BC00' }[a.priority] || '#6b7280';
                  return (
                    <div key={i} className="flex items-start gap-3 p-2 bg-gray-900 rounded-lg">
                      <span className="text-xs px-1.5 py-0.5 rounded font-bold shrink-0"
                        style={{ background: pc + '22', color: pc }}>{a.priority}</span>
                      <div>
                        <div className="text-gray-200 text-xs font-medium">{a.action}</div>
                        <div className="text-gray-500 text-xs">{a.description}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// TAB 5: MULTI-AGENT CLAUSE NEGOTIATION
// ═══════════════════════════════════════════════════════════════════════════════
function MultiAgentNegotiationTab() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    clause_text: 'Force majeure events include acts of God and natural disasters. Notice must be given within 30 days.',
    contract_value: 5000000,
    buyer_jurisdiction: 'EU',
    seller_jurisdiction: 'Ukraine',
    dispute_event: 'war',
    rounds: 3,
  });

  const upd = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleRun = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await runMultiAgentNegotiate({ ...form, rounds: parseInt(form.rounds), contract_value: parseFloat(form.contract_value) });
      setResult(res);
    } catch (e) {
      setError(e?.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  const agentColors = { buyer: '#4C8EDA', seller: '#F79767', insurer: '#9063CD' };

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-xl p-4 border border-yellow-900">
        <p className="text-gray-400 text-sm mb-4">
          Simulates multi-party FM clause negotiation: Buyer, Seller, and Insurer agents each propose improvements over {form.rounds} rounds.
        </p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Original FM Clause</label>
            <textarea value={form.clause_text} onChange={upd('clause_text')}
              className="w-full h-24 bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-200 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              ['buyer_jurisdiction', 'Buyer Jurisdiction'],
              ['seller_jurisdiction', 'Seller Jurisdiction'],
              ['dispute_event', 'Dispute Event'],
              ['rounds', 'Negotiation Rounds'],
            ].map(([k, label]) => (
              <div key={k}>
                <label className="text-xs text-gray-400 mb-1 block">{label}</label>
                <input value={form[k]} onChange={upd(k)}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-xs text-gray-200" />
              </div>
            ))}
          </div>
        </div>
        <button onClick={handleRun} disabled={loading}
          className="flex items-center gap-2 px-5 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-white text-sm font-medium transition disabled:opacity-50">
          <Users size={14} /> {loading ? 'Negotiating…' : 'Run Negotiation'}
        </button>
        {error && <div className="mt-2 text-red-400 text-xs">{error}</div>}
      </div>

      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Original Strength', v: fmtPct(result.original_strength), color: 'text-red-400' },
              { label: 'Final Strength', v: fmtPct(result.final_strength), color: 'text-green-400' },
              { label: 'Improvement', v: `+${result.improvement_pct}%`, color: 'text-yellow-400' },
            ].map((k, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700 text-center">
                <div className={`text-2xl font-bold ${k.color}`}>{k.v}</div>
                <div className="text-gray-500 text-xs mt-1">{k.label}</div>
              </div>
            ))}
          </div>

          {/* Negotiation rounds */}
          {(result.negotiation_rounds || []).map((round, ri) => (
            <div key={ri} className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <div className="text-gray-300 text-sm font-semibold">Round {round.round}</div>
                <div className="text-xs text-gray-500">
                  Clause strength after: <span className="text-green-400 font-bold">{fmtPct(round.clause_strength_after)}</span>
                </div>
              </div>
              <div className="space-y-2">
                {(round.proposals || []).map((p, pi) => (
                  <div key={pi} className="p-3 rounded-lg bg-gray-900 border-l-2"
                    style={{ borderColor: agentColors[p.role] || '#555' }}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold" style={{ color: agentColors[p.role] }}>{p.agent}</span>
                      <span className="text-xs text-gray-500">· {p.stance?.replace(/_/g,' ')}</span>
                      {p.agent === round.accepted_proposal?.agent && (
                        <span className="ml-auto text-xs bg-green-900 text-green-400 px-1.5 py-0.5 rounded">ACCEPTED</span>
                      )}
                    </div>
                    <div className="text-gray-400 text-xs">{p.position}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Final clause */}
          <div className="bg-gray-800 rounded-xl p-4 border border-green-800">
            <div className="text-green-400 text-sm font-semibold mb-2">Final Negotiated Clause</div>
            <div className="text-gray-300 text-xs leading-relaxed bg-gray-900 p-3 rounded-lg">
              {result.final_clause}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// TAB 6: SUPPLY CHAIN RISK MAP
// ═══════════════════════════════════════════════════════════════════════════════
function SupplyChainTab() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await getSupplyChainMap();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const routeBarData = (data?.trade_routes || []).map(r => ({
    name: r.name?.replace(' Route', '').replace(' Canal', ''),
    risk: Math.round(r.live_risk * 100),
    color: r.color,
  }));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-gray-400 text-sm">Live supply chain disruption scoring across major global trade routes.</div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-300 transition">
          <RefreshCw size={11} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {data && (
        <>
          {/* Summary KPIs */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Total Routes', v: data.summary?.total_routes, color: 'text-blue-400' },
              { label: 'Disrupted', v: data.summary?.disrupted_routes, color: 'text-red-400' },
              { label: 'Elevated', v: data.summary?.elevated_routes, color: 'text-yellow-400' },
              { label: 'Avg Disruption', v: `${data.summary?.avg_disruption_pct}%`, color: 'text-orange-400' },
            ].map((k, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-3 border border-gray-700 text-center">
                <div className={`text-2xl font-bold ${k.color}`}>{k.v}</div>
                <div className="text-gray-500 text-xs mt-1">{k.label}</div>
              </div>
            ))}
          </div>

          {/* Routes bar chart */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">Trade Route Disruption Risk</div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={routeBarData} barSize={28}>
                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} tickFormatter={v => `${v}%`} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', color: '#fff', fontSize: 11 }}
                  formatter={v => [`${v}%`, 'Disruption Risk']} />
                <Bar dataKey="risk" radius={[4, 4, 0, 0]}>
                  {routeBarData.map((r, i) => <Cell key={i} fill={r.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Routes detail */}
          <div className="grid grid-cols-2 gap-3">
            {(data.trade_routes || []).map((r, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-200 text-sm font-semibold">{r.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded font-bold"
                    style={{ background: r.color + '22', color: r.color }}>
                    {r.status}
                  </span>
                </div>
                <div className="text-gray-500 text-xs mb-2">{r.from} → {r.to}</div>
                <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                  <div className="h-2 rounded-full" style={{ width: `${r.disruption_pct}%`, background: r.color }} />
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Risk: <span style={{ color: r.color }} className="font-bold">{r.disruption_pct}%</span></span>
                  <span className="text-gray-500">Daily cargo: ${(r.cargo_value_bday / 1e9).toFixed(1)}B</span>
                </div>
              </div>
            ))}
          </div>

          {/* Supplier hubs */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="text-gray-300 text-sm font-semibold mb-3">Global Supplier Hub Risk</div>
            <div className="grid grid-cols-3 gap-2">
              {(data.supplier_hubs || []).map((hub, i) => {
                const riskColor = hub.risk > 0.6 ? '#F16667' : hub.risk > 0.35 ? '#F79767' : '#68BC00';
                return (
                  <div key={i} className="p-3 bg-gray-900 rounded-lg">
                    <div className="text-gray-200 text-xs font-medium truncate">{hub.name}</div>
                    <div className="text-gray-500 text-xs mb-1">{hub.type}</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full" style={{ width: `${Math.round(hub.risk * 100)}%`, background: riskColor }} />
                      </div>
                      <span className="text-xs font-bold" style={{ color: riskColor }}>{Math.round(hub.risk * 100)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
      {loading && <div className="text-gray-500 text-center py-8 text-sm">Loading supply chain data…</div>}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════
export default function FMAdvancedFeatures() {
  const [activeTab, setActiveTab] = useState('counterfactual');

  const tabContent = {
    counterfactual: <CounterfactualTab />,
    portfolio_sim: <PortfolioSimTab />,
    knowledge_graph: <KnowledgeGraphTab />,
    digital_twin: <DigitalTwinTab />,
    negotiation: <MultiAgentNegotiationTab />,
    supply_chain: <SupplyChainTab />,
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="mb-6 flex items-center gap-4">
        <div className="p-3 bg-gradient-to-br from-orange-600 to-red-600 rounded-xl">
          <Shield size={24} className="text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Force Majeure — Advanced Intelligence</h1>
          <p className="text-gray-400 text-sm">Counterfactual · Portfolio Simulation · Digital Twin · Multi-Agent Negotiation · Supply Chain</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs px-2 py-1 bg-red-900 text-red-400 rounded-full font-medium">LIVE DATA</span>
          <span className="text-xs px-2 py-1 bg-purple-900 text-purple-400 rounded-full font-medium">AI POWERED</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-800 rounded-xl p-1 overflow-x-auto">
        {TABS.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition whitespace-nowrap ${
                activeTab === tab.id ? 'bg-gray-700 text-white shadow' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Icon size={14} className={activeTab === tab.id ? tab.color : ''} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div>{tabContent[activeTab]}</div>
    </div>
  );
}
