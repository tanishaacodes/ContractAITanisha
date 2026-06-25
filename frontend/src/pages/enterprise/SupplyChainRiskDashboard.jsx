import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, Activity, Loader2, AlertTriangle, Users,
  Package, AlertCircle, Globe, Shield, TrendingUp,
  TrendingDown, Zap, ChevronDown, ChevronUp, X
} from 'lucide-react';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
import ContractSelector from '../../components/enterprise/ContractSelector';
import CytoscapeComponent from 'react-cytoscapejs';
import enterpriseRiskService from '../../services/enterpriseRiskService';

// Risk colours
const riskColor  = (score) => score >= 0.7 ? '#ef4444' : score >= 0.4 ? '#f59e0b' : '#10b981';
const riskLabel  = (score) => score >= 0.7 ? 'HIGH'    : score >= 0.4 ? 'MEDIUM'  : 'LOW';
const riskBg     = (score) => score >= 0.7
  ? 'bg-red-500/15 text-red-400 border-red-500/30'
  : score >= 0.4
  ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
  : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';

const TIER_COLOR  = { 1: '#06b6d4', 2: '#8b5cf6', 3: '#f59e0b' };
const TIER_LABEL  = { 1: 'Direct', 2: 'Indirect', 3: 'Deep-tier' };

export default function SupplyChainRiskDashboard() {
  const navigate   = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';

  const handleContractSelect = (id) => {
    if (id) setSearchParams({ contractId: id });
    else    setSearchParams({});
  };

  const [loading,         setLoading]         = useState(true);
  const [error,           setError]           = useState('');
  const [data,            setData]            = useState(null);
  const [selectedNode,    setSelectedNode]    = useState(null);
  const [sortBy,          setSortBy]          = useState('risk');   // risk | exposure | tier
  const [sortAsc,         setSortAsc]         = useState(false);
  const [filterRisk,      setFilterRisk]      = useState('ALL');    // ALL | HIGH | MEDIUM | LOW
  const cyRef   = useRef(null);
  useEffect(() => { load(); }, [contractId]);

  useEffect(() => () => {
    if (cyRef.current && !cyRef.current.destroyed()) {
      try { cyRef.current.destroy(); } catch {}
    }
  }, []);

  const load = async () => {
    try {
      setLoading(true);
      setError('');
      setSelectedNode(null);

      const api = await enterpriseRiskService.getSupplyChainRisk(contractId);

      const rawSuppliers = (api.nodes || [])
        .filter(n => n.type === 'supplier')
        .map(n => ({
          ...n,
          risk_score: n.risk === 'CRITICAL' ? 0.95
                    : n.risk === 'HIGH'     ? 0.78
                    : n.risk === 'MEDIUM'   ? 0.48
                    : 0.2,
          dependency_score: n.dependency_level === 'CRITICAL' ? 0.9
                          : n.dependency_level === 'HIGH'     ? 0.7
                          : 0.4,
          tier_num: n.tier || 1,
        }));

      const td = api.tier_distribution || {};

      setData({
        total_suppliers:    api.total_suppliers || rawSuppliers.length,
        high_risk:          rawSuppliers.filter(s => s.risk_score >= 0.7).length,
        single_source:      api.single_source_count || 0,
        avg_risk:           rawSuppliers.length
                              ? rawSuppliers.reduce((s, x) => s + x.risk_score, 0) / rawSuppliers.length
                              : 0,
        total_exposure:     rawSuppliers.reduce((s, x) => s + (x.exposure || 0), 0),
        tier_breakdown:     { tier1: td.tier_1 || 0, tier2: td.tier_2 || 0, tier3: td.tier_3 || 0 },
        single_source_list: api.single_source_suppliers || [],
        suppliers:          rawSuppliers,
        contract_node:      (api.nodes || []).find(n => n.type === 'contract') || null,
        links:              api.links || [],
      });
    } catch (err) {
      setError(err.message || 'Failed to load supply chain data');
    } finally {
      setLoading(false);
    }
  };

  // ── Build Cytoscape elements ─────────────────────────────────────────────
  const buildElements = () => {
    if (!data) return [];
    const elems = [];

    // Always create a central hub node
    const hubId = data.contract_node ? data.contract_node.id : '__hub__';
    const hubLabel = data.contract_node
      ? (data.contract_node.name || 'Contract').substring(0, 16)
      : (contractId ? 'Hub' : 'Portfolio');
    elems.push({ data: { id: hubId, label: hubLabel, type: 'contract', _color: '#a78bfa', _size: 70 }});

    data.suppliers.forEach(s => {
      const color = riskColor(s.risk_score);
      const tier  = s.tier_num || 1;
      // Scale node size by risk: high risk = bigger, min 32px max 52px
      const sz    = Math.round(32 + s.risk_score * 20);
      elems.push({ data: {
        id:      s.id,
        label:   (s.name || '').substring(0, 14),
        type:    'supplier',
        tier,
        risk:    s.risk_score,
        exposure: s.exposure || 0,
        country: s.country || '',
        single:  s.is_single_source || false,
        _color:  color,
        _size:   sz,
      }});
      // Always connect every supplier to hub
      elems.push({ data: { id: `hub-${s.id}`, source: hubId, target: s.id, _tier: tier }});
    });

    // Also add any original links (tier-to-tier connections)
    data.links.forEach((l, i) => {
      if (l.source !== hubId && l.target !== hubId) {
        elems.push({ data: { id: `link-${i}`, source: l.source, target: l.target, _tier: 0 }});
      }
    });

    return elems;
  };

  const cytoscapeStylesheet = [
    // Kill Cytoscape's built-in fade-on-select for every state
    { selector: 'node',            style: { opacity: 1 } },
    { selector: 'node:selected',   style: { opacity: 1 } },
    { selector: 'node:unselected', style: { opacity: 1 } },
    { selector: 'edge',            style: { opacity: 1 } },
    { selector: 'edge:selected',   style: { opacity: 1 } },
    { selector: 'edge:unselected', style: { opacity: 1 } },
    // Base node
    {
      selector: 'node',
      style: {
        'background-color': 'data(_color)',
        'label': 'data(label)',
        'color': '#e2e8f0',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': 8,
        'font-size': 11,
        'font-weight': '700',
        'font-family': 'Inter, system-ui, sans-serif',
        'width': 'data(_size)',
        'height': 'data(_size)',
        'border-width': 2,
        'border-color': 'rgba(255,255,255,0.18)',
        'text-wrap': 'wrap',
        'text-max-width': 80,
        'overlay-opacity': 0,
        'opacity': 1,
      }
    },
    // Contract hub node
    {
      selector: 'node[type="contract"]',
      style: {
        'background-color': '#a78bfa',
        'border-color': '#7c3aed',
        'border-width': 4,
        'font-size': 12,
        'font-weight': '900',
        'color': '#ffffff',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-margin-y': 0,
        'overlay-opacity': 0,
        'opacity': 1,
      }
    },
    // Tier border rings — rgba (Cytoscape doesn't support 8-digit hex)
    { selector: 'node[tier=1]', style: { 'border-color': 'rgba(6,182,212,0.67)',  'border-width': 3, opacity: 1 } },
    { selector: 'node[tier=2]', style: { 'border-color': 'rgba(139,92,246,0.67)', 'border-width': 3, opacity: 1 } },
    { selector: 'node[tier=3]', style: { 'border-color': 'rgba(245,158,11,0.67)', 'border-width': 3, opacity: 1 } },
    // Single-source gold ring
    {
      selector: 'node[?single]',
      style: { 'border-width': 5, 'border-color': '#fbbf24', 'overlay-opacity': 0, opacity: 1 }
    },
    // Selected — white ring only, no fade ever
    {
      selector: 'node:selected',
      style: { 'border-width': 4, 'border-color': '#ffffff', 'overlay-opacity': 0, opacity: 1 }
    },
    { selector: 'node:unselected', style: { 'overlay-opacity': 0, opacity: 1 } },
    // Edges
    {
      selector: 'edge',
      style: {
        'width': 1.5,
        'line-color': '#334155',
        'target-arrow-shape': 'none',
        'curve-style': 'straight',
        'opacity': 1,
      }
    },
    // Tier-colored edges — rgba instead of 8-digit hex
    { selector: 'edge[_tier=1]', style: { 'line-color': 'rgba(6,182,212,0.33)',  width: 1.5, opacity: 1 } },
    { selector: 'edge[_tier=2]', style: { 'line-color': 'rgba(139,92,246,0.33)', width: 1.5, opacity: 1 } },
    { selector: 'edge[_tier=3]', style: { 'line-color': 'rgba(245,158,11,0.33)', width: 1.5, opacity: 1 } },
    { selector: 'edge[_tier=0]', style: { 'line-color': '#475569',               width: 1,   opacity: 1 } },
  ];

  const layout = {
    name: 'breadthfirst',
    animate: false,
    fit: true,
    padding: 50,
    directed: false,
    spacingFactor: 1.5,
    circle: true,
    roots: (elements) => elements.filter(n => n.isNode() && n.data('type') === 'contract'),
  };

  // ── Table helpers ──────────────────────────────────────────────────────────
  const sortedSuppliers = () => {
    if (!data) return [];
    let list = [...data.suppliers];
    if (filterRisk !== 'ALL') {
      list = list.filter(s => riskLabel(s.risk_score) === filterRisk);
    }
    list.sort((a, b) => {
      let va, vb;
      if (sortBy === 'risk')     { va = a.risk_score; vb = b.risk_score; }
      else if (sortBy === 'exposure') { va = a.exposure || 0; vb = b.exposure || 0; }
      else                       { va = a.tier_num; vb = b.tier_num; }
      return sortAsc ? va - vb : vb - va;
    });
    return list;
  };

  const toggleSort = (col) => {
    if (sortBy === col) setSortAsc(p => !p);
    else { setSortBy(col); setSortAsc(false); }
  };

  // ── Loading / Error ────────────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="text-center">
        <div className="relative mx-auto mb-6 w-20 h-20">
          <div className="absolute inset-0 rounded-full border-4 border-emerald-500/20 animate-ping" />
          <div className="absolute inset-2 rounded-full border-4 border-cyan-400/30 animate-pulse" />
          <Activity className="w-8 h-8 text-emerald-400 absolute inset-0 m-auto" />
        </div>
        <p className="text-white font-bold text-xl mb-1">Mapping Supply Chain</p>
        <p className="text-slate-400 text-sm">Analysing supplier risk across all tiers…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="text-center max-w-md">
        <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Error</h2>
        <p className="text-slate-400 mb-6">{error}</p>
        <button onClick={load} className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-semibold">Retry</button>
      </div>
    </div>
  );

  const elements = buildElements();
  const rows     = sortedSuppliers();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-[#0a1628] to-slate-900 p-6">

      {/* ── Header ── */}
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-emerald-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
              <Activity className="w-8 h-8 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-emerald-200 to-cyan-300">
                Supply Chain Risk Network
              </h1>
              <p className="text-slate-400 text-sm">
                {contractId ? 'Contract-Specific Supply Chain' : 'Global View — All Suppliers'}
                {' · '}{data.total_suppliers} supplier{data.total_suppliers !== 1 ? 's' : ''} mapped
              </p>
            </div>
          </div>
        </div>
        <ContractSelector
          selectedContractId={contractId}
          onSelect={handleContractSelect}
          accentColor="emerald"
        />
      </div>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <ExposureCard title="Total Suppliers"     value={data.total_suppliers}   subtitle="Across all tiers"         icon={Users}         color="cyan"    />
        <ExposureCard title="High Risk Suppliers" value={data.high_risk}         subtitle="Risk score > 70%"         icon={AlertTriangle} color="red"     />
        <ExposureCard title="Single-Source Risks" value={data.single_source}     subtitle="Critical dependencies"    icon={AlertCircle}   color="amber"   />
        <ExposureCard
          title="Avg Risk Score"
          value={`${(data.avg_risk * 100).toFixed(0)}%`}
          subtitle={`₹${(data.total_exposure / 1_000_000).toFixed(1)}M total exposure`}
          icon={Activity}
          color="emerald"
        />
      </div>

      {/* ── Main Layout: Graph left, Inspector right ── */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5 mb-5">

        {/* Network Graph */}
        <div className="lg:col-span-3">
          <div className="relative bg-gradient-to-br from-slate-900/80 to-[#0a1628]/80 backdrop-blur-xl border border-emerald-500/20 rounded-2xl shadow-[0_0_50px_rgba(16,185,129,0.12)] overflow-hidden">
            {/* Terminal bar */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/50">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="ml-3 text-xs text-slate-500 font-mono">supply-chain-network · {data.total_suppliers} nodes</span>
              </div>
              <div className="flex items-center gap-4">
                {/* Legend inline */}
                {[
                  { label: 'Low (<40%)',   color: '#10b981' },
                  { label: 'Medium',       color: '#f59e0b' },
                  { label: 'High (>70%)',  color: '#ef4444' },
                  { label: 'Single-source (gold ring)', color: '#fbbf24' },
                ].map(l => (
                  <div key={l.label} className="hidden sm:flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: l.color }} />
                    <span className="text-[10px] text-slate-400">{l.label}</span>
                  </div>
                ))}
                <div className="flex items-center gap-1.5 ml-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs text-emerald-400 font-semibold">LIVE</span>
                </div>
              </div>
            </div>

            {/* Cytoscape canvas */}
            <div className="bg-[#060d1a]" style={{ height: '520px' }}>
              {data.suppliers.length > 0 ? (
                <CytoscapeComponent
                  key={`sc-${contractId}-${data.suppliers.length}`}
                  elements={elements}
                  stylesheet={cytoscapeStylesheet}
                  layout={layout}
                  style={{ width: '100%', height: '100%', background: 'transparent' }}
                  boxSelectionEnabled={false}
                  autounselectify={true}
                  cy={(cy) => {
                    if (!cy) return;
                    cyRef.current = cy;
                    // Disable all built-in Cytoscape selection visuals
                    cy.autounselectify(true);
                    cy.on('tap', 'node', (evt) => {
                      const d = evt.target.data();
                      if (d.type === 'supplier') {
                        const sup = data.suppliers.find(s => s.id === d.id);
                        setSelectedNode(sup || d);
                      }
                    });
                    cy.on('tap', (evt) => {
                      if (evt.target === cy) setSelectedNode(null);
                    });
                  }}
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full gap-3">
                  <Activity className="w-16 h-16 text-slate-700" />
                  <p className="text-slate-500 text-sm">No supplier network data available for this contract</p>
                </div>
              )}
            </div>

            <div className="px-5 py-2 border-t border-slate-700/50 flex items-center gap-4 flex-wrap">
              <p className="text-xs text-slate-600">
                Concentric layout · Hub center → Tier 1 → Tier 2 → Tier 3 · Node size ∝ exposure · Gold ring = single-source
              </p>
              <div className="ml-auto flex items-center gap-3 text-xs text-slate-500 flex-shrink-0">
                {[1, 2, 3].map(t => (
                  <span key={t} className="flex items-center gap-1">
                    <span className="inline-block w-3 h-3 rounded-full border-2" style={{ borderColor: TIER_COLOR[t] }} />
                    Tier {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Inspector Panel */}
        <div className="lg:col-span-1 space-y-4">

          {/* Selected Node */}
          <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-5 shadow-[0_0_30px_rgba(16,185,129,0.1)]">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Package className="w-4 h-4 text-emerald-400" />
              Supplier Inspector
            </h3>

            {selectedNode && selectedNode.type !== 'contract' ? (
              <div className="space-y-3">
                {/* Name + badges */}
                <div>
                  <p className="text-sm font-bold text-white leading-tight">{selectedNode.name}</p>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    <span className={`px-2 py-0.5 text-[10px] font-black rounded-full border ${riskBg(selectedNode.risk_score)}`}>
                      {riskLabel(selectedNode.risk_score)} RISK
                    </span>
                    {selectedNode.is_single_source && (
                      <span className="px-2 py-0.5 text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full font-black">
                        SINGLE SOURCE
                      </span>
                    )}
                    <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full border"
                      style={{ color: TIER_COLOR[selectedNode.tier_num || 1], borderColor: TIER_COLOR[selectedNode.tier_num || 1] + '50', backgroundColor: TIER_COLOR[selectedNode.tier_num || 1] + '15' }}>
                      TIER {selectedNode.tier_num || 1} · {TIER_LABEL[selectedNode.tier_num || 1]}
                    </span>
                  </div>
                </div>

                {/* Risk bar */}
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-slate-400">Risk Score</span>
                    <span className="text-xs font-bold" style={{ color: riskColor(selectedNode.risk_score) }}>
                      {(selectedNode.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${selectedNode.risk_score * 100}%`, backgroundColor: riskColor(selectedNode.risk_score), boxShadow: `0 0 8px ${riskColor(selectedNode.risk_score)}88` }}
                    />
                  </div>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  {[
                    { label: 'Exposure', val: `₹${((selectedNode.exposure || 0)/1_000_000).toFixed(1)}M`, color: 'text-cyan-400' },
                    { label: 'Country',  val: selectedNode.country || '—',  color: 'text-emerald-400' },
                    { label: 'Dependency', val: `${((selectedNode.dependency_score || 0)*100).toFixed(0)}%`, color: 'text-violet-400' },
                    { label: 'Risk Level', val: selectedNode.risk || riskLabel(selectedNode.risk_score), color: riskColor(selectedNode.risk_score) === '#ef4444' ? 'text-red-400' : riskColor(selectedNode.risk_score) === '#f59e0b' ? 'text-amber-400' : 'text-emerald-400' },
                  ].map(({ label, val, color }) => (
                    <div key={label} className="bg-slate-900/60 rounded-xl p-2.5 border border-slate-700/50">
                      <p className="text-[10px] text-slate-500 mb-0.5">{label}</p>
                      <p className={`text-sm font-bold ${color} truncate`}>{val}</p>
                    </div>
                  ))}
                </div>

                <button onClick={() => setSelectedNode(null)}
                  className="mt-1 w-full text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center justify-center gap-1">
                  <X className="w-3 h-3" /> Clear
                </button>
              </div>
            ) : selectedNode?.type === 'contract' ? (
              <div className="text-center py-4">
                <div className="w-10 h-10 rounded-full bg-violet-500/20 flex items-center justify-center mx-auto mb-2">
                  <Package className="w-5 h-5 text-violet-400" />
                </div>
                <p className="text-sm font-bold text-white">{selectedNode.label}</p>
                <p className="text-xs text-slate-400 mt-1">Contract hub node</p>
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">Click any supplier node in the graph</p>
              </div>
            )}
          </div>

          {/* Tier Breakdown */}
          <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-5 shadow-[0_0_20px_rgba(139,92,246,0.1)]">
            <h3 className="text-base font-bold text-white mb-4">Tier Breakdown</h3>
            <div className="space-y-3">
              {[
                { tier: 1, count: data.tier_breakdown.tier1, label: 'Direct', color: TIER_COLOR[1] },
                { tier: 2, count: data.tier_breakdown.tier2, label: 'Indirect', color: TIER_COLOR[2] },
                { tier: 3, count: data.tier_breakdown.tier3, label: 'Deep-tier', color: TIER_COLOR[3] },
              ].map(({ tier, count, label, color }) => {
                const pct = data.total_suppliers > 0 ? (count / data.total_suppliers) * 100 : 0;
                return (
                  <div key={tier}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                        <span className="text-sm text-slate-300">Tier {tier} <span className="text-slate-500 text-xs">· {label}</span></span>
                      </div>
                      <span className="text-sm font-bold text-white">{count}</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color, transition: 'width 0.8s ease' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Single-source alerts */}
          {data.single_source_list.length > 0 && (
            <div className="bg-gradient-to-br from-amber-900/20 to-slate-900/70 backdrop-blur-xl border border-amber-500/30 rounded-2xl p-5 shadow-[0_0_20px_rgba(245,158,11,0.15)]">
              <h3 className="text-base font-bold text-amber-400 mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" /> Single-Source Risks
              </h3>
              <div className="space-y-2">
                {data.single_source_list.slice(0, 4).map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 bg-amber-500/10 rounded-xl border border-amber-500/20">
                    <span className="text-sm text-white font-medium truncate flex-1">{s.name}</span>
                    <span className="text-xs font-bold text-amber-400 flex-shrink-0 ml-2">₹{((s.exposure || 0) / 1_000_000).toFixed(1)}M</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Supplier Table ── */}
      <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.1)]">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-400" />
            Supplier Risk Registry
            <span className="ml-2 px-2 py-0.5 text-xs bg-emerald-500/15 text-emerald-400 rounded-full border border-emerald-500/30 font-semibold">
              {rows.length} suppliers
            </span>
          </h3>

          {/* Risk filter */}
          <div className="flex items-center gap-2">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(r => (
              <button
                key={r}
                onClick={() => setFilterRisk(r)}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                  filterRisk === r
                    ? r === 'HIGH'   ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                    : r === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                    : r === 'LOW'    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-slate-700 text-white border border-slate-600'
                    : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {rows.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500">No suppliers found for this filter</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/60">
                  {[
                    { key: 'name',     label: 'Supplier',  sortable: false },
                    { key: 'tier',     label: 'Tier',      sortable: true  },
                    { key: 'country',  label: 'Country',   sortable: false },
                    { key: 'risk',     label: 'Risk Score', sortable: true  },
                    { key: 'exposure', label: 'Exposure',  sortable: true  },
                    { key: 'dep',      label: 'Dependency', sortable: false },
                    { key: 'flag',     label: 'Flags',     sortable: false },
                  ].map(col => (
                    <th
                      key={col.key}
                      onClick={() => col.sortable && toggleSort(col.key === 'risk' ? 'risk' : col.key === 'exposure' ? 'exposure' : 'tier')}
                      className={`text-left py-3 px-4 text-xs font-bold text-slate-400 uppercase tracking-wider select-none ${col.sortable ? 'cursor-pointer hover:text-white' : ''}`}
                    >
                      <span className="flex items-center gap-1">
                        {col.label}
                        {col.sortable && sortBy === (col.key === 'risk' ? 'risk' : col.key === 'exposure' ? 'exposure' : 'tier') && (
                          sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((s, i) => {
                  const rc = riskColor(s.risk_score);
                  const rl = riskLabel(s.risk_score);
                  const isSelected = selectedNode?.id === s.id;
                  return (
                    <tr
                      key={s.id || i}
                      onClick={() => setSelectedNode(isSelected ? null : s)}
                      className={`border-b border-slate-700/40 transition-all cursor-pointer ${
                        isSelected ? 'bg-emerald-500/10' : 'hover:bg-slate-700/30'
                      }`}
                    >
                      <td className="py-3 px-4">
                        <p className="text-sm font-semibold text-white">{s.name}</p>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full"
                          style={{ color: TIER_COLOR[s.tier_num || 1], backgroundColor: TIER_COLOR[s.tier_num || 1] + '18', border: `1px solid ${TIER_COLOR[s.tier_num || 1]}40` }}>
                          T{s.tier_num || 1}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5">
                          <Globe className="w-3 h-3 text-slate-500" />
                          <span className="text-sm text-slate-300">{s.country || '—'}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2 min-w-[120px]">
                          <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div className="h-full rounded-full" style={{ width: `${s.risk_score * 100}%`, backgroundColor: rc }} />
                          </div>
                          <span className="text-xs font-bold w-8 text-right" style={{ color: rc }}>
                            {(s.risk_score * 100).toFixed(0)}%
                          </span>
                          <span className={`text-[10px] font-black px-1.5 py-0.5 rounded border ${riskBg(s.risk_score)}`}>{rl}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm font-semibold text-white">
                        ₹{((s.exposure || 0) / 1_000_000).toFixed(1)}M
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2 min-w-[80px]">
                          <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div className="h-full rounded-full bg-violet-500" style={{ width: `${(s.dependency_score || 0) * 100}%` }} />
                          </div>
                          <span className="text-xs text-slate-400 w-8 text-right">{((s.dependency_score || 0) * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-1 flex-wrap">
                          {s.is_single_source && (
                            <span className="px-1.5 py-0.5 text-[10px] font-black bg-amber-500/15 text-amber-400 rounded border border-amber-500/30">
                              SOLO
                            </span>
                          )}
                          {s.risk_score >= 0.7 && (
                            <span className="px-1.5 py-0.5 text-[10px] font-black bg-red-500/15 text-red-400 rounded border border-red-500/30">
                              ⚠ HIGH
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
