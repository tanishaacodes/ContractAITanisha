import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useToast } from '../components/ToastNotification';
import * as d3 from 'd3';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LineChart,
  Line,
  Legend,
  ScatterChart,
  Scatter,
  ZAxis,
  AreaChart,
  Area,
  ReferenceLine,
} from 'recharts';
import {
  buildStrategyMemory,
  searchMemory,
  createMonitorEvent,
  getMonitorAlerts,
  scanForEvents,
  recordOutcome,
  getRLExperiences,
  getRLInsights,
  getRLRecommendation,
  submitRLHFFeedback,
  getRLHFFeedback,
  getIndustryBenchmarking,
  getBenchmarkingContracts,
  getBenchmarkingInsights,
  getBenchmarkingClauses,
  getBenchmarkingRecommendations,
  getTemporalEvolution,
  getRiskMarginFrontier,
  getSupplierHeatmap,
  getDisputeTimeline,
  triggerERPAction,
  getERPExecutionLog,
  bulkERPExecute,
  getERPContracts,
  trainRLModel,
  getClauseVolatility,
  triggerAutoAction,
  getAutoActionLog,
  bulkAutoAction,
} from '../services/contractSuiteService';

// Inject global keyframes once
const GLOBAL_STYLES = `
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 20px rgba(6,182,212,0.3); }
    50% { box-shadow: 0 0 40px rgba(6,182,212,0.6), 0 0 60px rgba(124,58,237,0.3); }
  }
  @keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.15; }
    33% { transform: translateY(-20px) rotate(120deg); opacity: 0.3; }
    66% { transform: translateY(-10px) rotate(240deg); opacity: 0.2; }
  }
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
  @keyframes countUp {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
  }
  @keyframes progressFill {
    from { width: 0%; }
    to { width: 100%; }
  }
  @keyframes tabEnter {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  @keyframes neonPulse {
    0%, 100% { box-shadow: 0 0 8px rgba(239,68,68,0.4); }
    50% { box-shadow: 0 0 24px rgba(239,68,68,0.8), 0 0 40px rgba(239,68,68,0.3); }
  }
  @keyframes rewardPop {
    0% { transform: scale(0.6); opacity: 0; }
    60% { transform: scale(1.15); opacity: 1; }
    100% { transform: scale(1); opacity: 1; }
  }
  @keyframes confidenceFill {
    from { width: 0%; }
    to { width: var(--conf-w); }
  }
  @keyframes exploreGlow {
    0%, 100% { box-shadow: 0 0 12px rgba(168,85,247,0.4); }
    50% { box-shadow: 0 0 28px rgba(168,85,247,0.8), 0 0 50px rgba(6,182,212,0.3); }
  }
`;
if (typeof document !== 'undefined' && !document.getElementById('contract-suite-styles')) {
  const style = document.createElement('style');
  style.id = 'contract-suite-styles';
  style.textContent = GLOBAL_STYLES;
  document.head.appendChild(style);
}

const TABS = [
  { id: 'memory', label: '🧠 Strategy Memory' },
  { id: 'monitoring', label: '📡 Live Monitoring' },
  { id: 'rl', label: '🤖 RL Learning' },
  { id: 'benchmarking', label: '📊 Benchmarking' },
  { id: 'temporal', label: '⏱ Temporal' },
  { id: 'risk-margin', label: '⚖️ Risk vs Margin' },
  { id: 'supplier-heatmap', label: '🔥 Supplier Heatmap' },
  { id: 'dispute-timeline', label: '📅 Dispute Timeline' },
  { id: 'clause-volatility', label: '📈 Clause Volatility' },
  { id: 'erp-execution', label: '⚙️ ERP Execution' },
];

const SEVERITY_STYLES = {
  critical: 'bg-red-600/20 border-red-500/50 text-red-300',
  high: 'bg-red-500/10 border-red-500/30 text-red-400',
  medium: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400',
  low: 'bg-green-500/10 border-green-500/30 text-green-400',
};

const SEVERITY_BADGE = {
  critical: 'bg-red-600 text-white',
  high: 'bg-red-500/70 text-white',
  medium: 'bg-yellow-600/70 text-white',
  low: 'bg-green-600/70 text-white',
};

const EVENT_TYPES = [
  { value: 'war', label: 'Armed Conflict / War' },
  { value: 'supplier_risk', label: 'Supplier Risk' },
  { value: 'fx_spike', label: 'FX Spike' },
  { value: 'policy_change', label: 'Policy Change' },
  { value: 'weather', label: 'Weather Event' },
];

const ACTION_OPTIONS = [
  { value: 'accept_redline', label: 'Accept Redline' },
  { value: 'reject_clause', label: 'Reject Clause' },
  { value: 'negotiate', label: 'Negotiate' },
  { value: 'approve_as_is', label: 'Approve As-Is' },
  { value: 'escalate', label: 'Escalate' },
  { value: 'counter_propose', label: 'Counter Propose' },
];

const RISK_BUCKET_OPTIONS = [
  { value: 'low', label: '🟢 Low Risk' },
  { value: 'medium', label: '🟡 Medium Risk' },
  { value: 'high', label: '🔴 High Risk' },
];

const CLAUSE_CATEGORY_OPTIONS = [
  { value: 'payment_terms', label: 'Payment Terms' },
  { value: 'liability', label: 'Liability' },
  { value: 'indemnification', label: 'Indemnification' },
  { value: 'force_majeure', label: 'Force Majeure' },
  { value: 'termination', label: 'Termination' },
  { value: 'confidentiality', label: 'Confidentiality' },
  { value: 'dispute_resolution', label: 'Dispute Resolution' },
  { value: 'governing_law', label: 'Governing Law' },
  { value: 'intellectual_property', label: 'Intellectual Property' },
  { value: 'warranty', label: 'Warranty' },
  { value: 'penalty', label: 'Penalty' },
  { value: 'general', label: 'General' },
];

const ACTION_COLOR_MAP = {
  accept_redline: '#06b6d4',
  reject_clause:  '#ef4444',
  negotiate:      '#10b981',
  approve_as_is:  '#8b5cf6',
  escalate:       '#f59e0b',
  counter_propose:'#ec4899',
};

const CLAUSE_TYPE_COLORS = {
  'Payment Terms':          '#4C8EDA',
  Liability:                '#F16667',
  'Limitation of Liability':'#F16667',
  Termination:              '#F79767',
  Indemnification:          '#E8A838',
  Confidentiality:          '#9063CD',
  'Force Majeure':          '#10b981',
  'Governing Law':          '#06B6D4',
  'Dispute Resolution':     '#8b5cf6',
  Arbitration:              '#7c3aed',
  'Intellectual Property':  '#ec4899',
  IP:                       '#ec4899',
  Warranty:                 '#14b8a6',
  Penalty:                  '#ef4444',
  Insurance:                '#f59e0b',
  Assignment:               '#64748b',
  Notice:                   '#0ea5e9',
  'Entire Agreement':       '#6366f1',
  Amendment:                '#84cc16',
  General:                  '#94a3b8',
};

// ─── Reusable UI Components ───────────────────────────────────────

const glassCard = {
  background: 'rgba(13, 17, 23, 0.8)',
  border: '1px solid rgba(99, 102, 241, 0.15)',
  backdropFilter: 'blur(20px)',
};

const TabBar = ({ activeTab, onTabChange }) => (
  <div className="flex flex-wrap gap-1.5 p-1.5 mb-6 overflow-x-auto" style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)', borderRadius: 16 }}>
    {TABS.map((tab) => (
      <button
        key={tab.id}
        onClick={() => onTabChange(tab.id)}
        className="py-1.5 px-3 rounded-xl text-xs font-medium transition-all duration-200 whitespace-nowrap"
        style={
          activeTab === tab.id
            ? { background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', color: '#fff', boxShadow: '0 0 16px rgba(6,182,212,0.35)' }
            : { color: '#6b7280' }
        }
        onMouseEnter={(e) => { if (activeTab !== tab.id) e.currentTarget.style.color = '#e5e7eb'; }}
        onMouseLeave={(e) => { if (activeTab !== tab.id) e.currentTarget.style.color = '#6b7280'; }}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

const Card = ({ children, className = '', style = {} }) => (
  <div
    className={`rounded-2xl p-5 transition-all duration-200 ${className}`}
    style={{ ...glassCard, borderRadius: 16, ...style }}
    onMouseEnter={(e) => { e.currentTarget.style.border = '1px solid rgba(99,102,241,0.35)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(99,102,241,0.08)'; }}
    onMouseLeave={(e) => { e.currentTarget.style.border = '1px solid rgba(99,102,241,0.15)'; e.currentTarget.style.boxShadow = 'none'; }}
  >
    {children}
  </div>
);

const Button = ({ onClick, disabled, loading, children, variant = 'primary', className = '' }) => {
  const base = 'px-4 py-2 rounded-xl font-medium transition-all duration-200 flex items-center gap-2 text-sm';
  const variants = {
    primary: { background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', color: '#fff', boxShadow: '0 0 16px rgba(6,182,212,0.25)' },
    success: { background: 'linear-gradient(135deg, #059669, #10b981)', color: '#fff' },
    outline: { background: 'transparent', border: '1px solid rgba(99,102,241,0.3)', color: '#9ca3af' },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${className} disabled:opacity-50`}
      style={variants[variant] || variants.primary}
      onMouseEnter={(e) => { if (!disabled && !loading && variant === 'primary') { e.currentTarget.style.boxShadow = '0 0 30px rgba(6,182,212,0.5), 0 0 60px rgba(124,58,237,0.2)'; e.currentTarget.style.transform = 'translateY(-1px)'; } }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = variants[variant]?.boxShadow || 'none'; e.currentTarget.style.transform = 'none'; }}
    >
      {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
      {children}
    </button>
  );
};

const KPICard = ({ label, value, colorClass = 'text-cyan-400', suffix = '', icon = '' }) => {
  const numericVal = parseFloat(String(value).replace(/[^0-9.-]/g, ''));
  const isNumeric = !isNaN(numericVal) && String(value).replace(/[^0-9.-]/g, '') !== '';
  const prefix = isNumeric ? String(value).match(/^[^0-9-]*/)?.[0] || '' : '';
  const postfix = isNumeric ? String(value).replace(/^[^0-9-]*[\d.]+/, '') || '' : '';
  const animated = useAnimatedValue(isNumeric ? numericVal : 0);
  return (
    <div
      className="rounded-2xl p-4 text-center transition-all duration-300 group"
      style={{
        background: 'rgba(13,17,23,0.9)',
        border: '1px solid rgba(99,102,241,0.15)',
        animation: 'fadeInUp 0.4s ease-out',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.border = '1px solid rgba(99,102,241,0.4)';
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 8px 32px rgba(99,102,241,0.12)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.border = '1px solid rgba(99,102,241,0.15)';
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {icon && <div className="text-2xl mb-1 group-hover:scale-110 transition-transform">{icon}</div>}
      <div className={`text-2xl font-bold ${colorClass}`} style={{ textShadow: '0 0 20px currentColor', animation: 'countUp 0.5s ease-out' }}>
        {prefix}{isNumeric ? animated : value}{postfix || suffix}
      </div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
};

const SectionHeader = ({ title, subtitle, icon }) => (
  <div className="mb-5">
    <div className="flex items-center gap-2 mb-1">
      {icon && <span className="text-xl">{icon}</span>}
      <h3 className="text-lg font-bold text-white">{title}</h3>
    </div>
    {subtitle && <p className="text-sm text-gray-400 ml-7">{subtitle}</p>}
  </div>
);

const inputClass = "w-full rounded-xl px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all";
const inputStyle = { background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' };

const StyledInput = (props) => (
  <input {...props} className={`${inputClass} ${props.className || ''}`} style={{ ...inputStyle, ...props.style }} />
);
const StyledSelect = ({ children, ...props }) => (
  <select {...props} className={`${inputClass} ${props.className || ''}`} style={{ ...inputStyle, ...props.style }}>{children}</select>
);
const StyledTextarea = (props) => (
  <textarea {...props} className={`${inputClass} resize-none ${props.className || ''}`} style={{ ...inputStyle, ...props.style }} />
);

// Animated counter for KPI values
const useAnimatedValue = (target) => {
  const [display, setDisplay] = React.useState(0);
  const prevTarget = useRef(null);
  useEffect(() => {
    if (prevTarget.current === target) return;
    prevTarget.current = target;
    const numTarget = parseFloat(String(target).replace(/[^0-9.-]/g, '')) || 0;
    if (isNaN(numTarget)) { setDisplay(target); return; }
    let start = 0;
    const duration = 800;
    const startTime = performance.now();
    const update = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(start + (numTarget - start) * eased);
      setDisplay(current);
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }, [target]);
  return display;
};

// ─── Tab 1: Strategy Memory ───────────────────────────────────────

// ── helpers ──────────────────────────────────────────────────────
const riskBadge = (score) => {
  if (score > 0.6) return { label: 'HIGH RISK', bg: 'rgba(239,68,68,0.2)', border: '#ef4444', color: '#fca5a5' };
  if (score > 0.3) return { label: 'MEDIUM', bg: 'rgba(234,179,8,0.15)', border: '#ca8a04', color: '#fde68a' };
  return { label: 'LOW RISK', bg: 'rgba(16,185,129,0.12)', border: '#059669', color: '#6ee7b7' };
};

const simColor = (sim) => {
  if (sim >= 0.85) return '#10b981';
  if (sim >= 0.75) return '#06b6d4';
  return '#818cf8';
};

// ── D3 Type-Level Knowledge Graph ────────────────────────────────────────
const ClauseKnowledgeGraph = ({ nodes, edges }) => {
  const containerRef = useRef(null);
  const svgRef       = useRef(null);
  const simRef       = useRef(null);
  const [selectedType, setSelectedType] = useState(null);
  const [dims, setDims] = useState({ w: 0, h: 460 });

  // Measure container size accurately via ResizeObserver
  useEffect(() => {
    if (!containerRef.current) return;
    const measure = () => {
      const rect = containerRef.current.getBoundingClientRect();
      if (rect.width > 10) setDims({ w: Math.floor(rect.width), h: Math.max(400, Math.floor(rect.height)) });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Draw when we have real width + data
  useEffect(() => {
    if (!svgRef.current || !nodes || nodes.length === 0 || dims.w === 0) return;
    if (simRef.current) { simRef.current.stop(); simRef.current = null; }

    // 1) Aggregate clause nodes → type-level nodes
    const typeMap = {};
    nodes.forEach((n) => {
      const t = n.clause_type || 'General';
      if (!typeMap[t]) typeMap[t] = { id: t, type: t, count: 0, riskSum: 0, clauses: [] };
      typeMap[t].count++;
      typeMap[t].riskSum += n.risk_score || 0;
      typeMap[t].clauses.push(n);
    });
    const typeNodes = Object.values(typeMap).map((t) => ({
      ...t,
      avgRisk: t.count > 0 ? t.riskSum / t.count : 0,
    }));

    // 2) Build type-level edges (cross-type only)
    const edgeMap = {};
    edges.forEach((e) => {
      const src = nodes.find((n) => n.id === e.source);
      const tgt = nodes.find((n) => n.id === e.target);
      if (!src || !tgt || src.clause_type === tgt.clause_type) return;
      const key = [src.clause_type, tgt.clause_type].sort().join('\x00');
      if (!edgeMap[key]) edgeMap[key] = { source: src.clause_type, target: tgt.clause_type, count: 0, simSum: 0 };
      edgeMap[key].count++;
      edgeMap[key].simSum += e.similarity || 0.75;
    });
    const typeEdges = Object.values(edgeMap).map((e) => ({ ...e, avgSim: e.simSum / e.count }));

    // 3) Dimensions
    const W = dims.w;
    const H = dims.h;
    const maxCount = Math.max(1, ...typeNodes.map((n) => n.count));
    const getR = (n) => 26 + (n.count / maxCount) * 22;
    const safeId = (s) => s.replace(/[^a-zA-Z0-9]/g, '-');

    // 4) Clear + setup SVG
    const svgEl = d3.select(svgRef.current);
    svgEl.selectAll('*').remove();
    svgEl.attr('width', W).attr('height', H);

    // 5) Defs
    const defs = svgEl.append('defs');
    typeNodes.forEach((n) => {
      const flt = defs.append('filter').attr('id', `glow-${safeId(n.id)}`)
        .attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
      flt.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur');
      const fm = flt.append('feMerge');
      fm.append('feMergeNode').attr('in', 'blur');
      fm.append('feMergeNode').attr('in', 'SourceGraphic');
    });
    const bgGrad = defs.append('radialGradient').attr('id', 'kg-bg2').attr('cx', '50%').attr('cy', '50%').attr('r', '65%');
    bgGrad.append('stop').attr('offset', '0%').attr('stop-color', '#0d1224');
    bgGrad.append('stop').attr('offset', '100%').attr('stop-color', '#05080f');

    // 6) Background
    svgEl.append('rect').attr('width', W).attr('height', H).attr('fill', 'url(#kg-bg2)');
    const dotG = svgEl.append('g').attr('pointer-events', 'none');
    for (let xi = 0; xi <= W; xi += 48) {
      for (let yi = 0; yi <= H; yi += 48) {
        dotG.append('circle').attr('cx', xi).attr('cy', yi).attr('r', 0.8).attr('fill', 'rgba(99,102,241,0.07)');
      }
    }

    // 7) Pre-position nodes in a circle so they start spread across the full canvas
    const angleStep = (2 * Math.PI) / typeNodes.length;
    const initRadius = Math.min(W, H) * 0.34;
    typeNodes.forEach((n, i) => {
      n.x = W / 2 + initRadius * Math.cos(angleStep * i - Math.PI / 2);
      n.y = H / 2 + initRadius * Math.sin(angleStep * i - Math.PI / 2);
    });

    // 8) Zoom group
    const g = svgEl.append('g').attr('class', 'zoom-root');
    svgEl.call(d3.zoom().scaleExtent([0.3, 4]).on('zoom', (ev) => g.attr('transform', ev.transform)));

    // 9) Simulation — moderate charge + strong centering to keep nodes spread across full canvas
    const linkDist = Math.min(W * 0.18, H * 0.22, 160);
    const sim = d3.forceSimulation(typeNodes)
      .force('link', d3.forceLink(typeEdges).id((d) => d.id).distance(linkDist).strength(0.4))
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(W / 2, H / 2).strength(0.06))
      .force('x', d3.forceX(W / 2).strength(0.04))
      .force('y', d3.forceY(H / 2).strength(0.06))
      .force('collide', d3.forceCollide().radius((d) => getR(d) + 20).strength(0.9))
      .alphaDecay(0.022);
    simRef.current = sim;

    // 9) Edges
    const linkG = g.append('g').attr('class', 'links');
    const linkSel = linkG.selectAll('g.link-item').data(typeEdges).enter().append('g').attr('class', 'link-item');
    linkSel.append('line').attr('class', 'edge-line')
      .attr('stroke', (d) => {
        const sid = typeof d.source === 'object' ? d.source.id : d.source;
        return (CLAUSE_TYPE_COLORS[sid] || '#6366f1') + '40';
      })
      .attr('stroke-width', (d) => Math.min(4, 1.5 + d.count * 0.4))
      .attr('stroke-dasharray', '5,4');
    linkSel.append('text').attr('class', 'edge-label')
      .attr('text-anchor', 'middle').attr('font-size', 9)
      .attr('font-family', 'Inter, sans-serif').attr('fill', 'rgba(99,102,241,0.45)')
      .text((d) => d.count > 1 ? `${d.count}` : '');

    // 10) Nodes
    const nodeG = g.append('g').attr('class', 'nodes')
      .selectAll('g.type-node').data(typeNodes).enter()
      .append('g').attr('class', 'type-node').style('cursor', 'pointer')
      .call(
        d3.drag()
          .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
          .on('end',   (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    nodeG.append('circle').attr('class', 'node-ring')
      .attr('r', (d) => getR(d) + 10).attr('fill', 'none')
      .attr('stroke', (d) => (CLAUSE_TYPE_COLORS[d.type] || '#94a3b8') + '20').attr('stroke-width', 1.5);

    nodeG.append('circle').attr('class', 'node-main')
      .attr('r', (d) => getR(d))
      .attr('fill', (d) => (CLAUSE_TYPE_COLORS[d.type] || '#94a3b8') + '1c')
      .attr('stroke', (d) => CLAUSE_TYPE_COLORS[d.type] || '#94a3b8').attr('stroke-width', 2)
      .attr('filter', (d) => `url(#glow-${safeId(d.id)})`);

    nodeG.append('text').attr('class', 'node-count')
      .attr('text-anchor', 'middle').attr('dominant-baseline', 'central').attr('dy', '-0.25em')
      .attr('font-size', (d) => Math.max(14, getR(d) * 0.5)).attr('font-weight', '800')
      .attr('font-family', 'Inter, ui-sans-serif, sans-serif')
      .attr('fill', (d) => CLAUSE_TYPE_COLORS[d.type] || '#94a3b8').text((d) => d.count);

    nodeG.append('text').attr('class', 'node-sub')
      .attr('text-anchor', 'middle').attr('dominant-baseline', 'central').attr('dy', '1.1em')
      .attr('font-size', 8).attr('font-weight', '500').attr('font-family', 'Inter, sans-serif')
      .attr('fill', (d) => (CLAUSE_TYPE_COLORS[d.type] || '#94a3b8') + '88').text('clauses');

    nodeG.append('text').attr('class', 'node-label')
      .attr('text-anchor', 'middle').attr('dominant-baseline', 'hanging')
      .attr('dy', (d) => getR(d) + 8)
      .attr('font-size', 10).attr('font-weight', '600').attr('font-family', 'Inter, sans-serif')
      .attr('fill', '#94a3b8').text((d) => d.type.length > 14 ? d.type.slice(0, 12) + '…' : d.type);

    nodeG.filter((d) => d.avgRisk > 0.3).append('circle').attr('class', 'risk-dot')
      .attr('cx', (d) => getR(d) * 0.65).attr('cy', (d) => -getR(d) * 0.65)
      .attr('r', 5.5).attr('fill', (d) => d.avgRisk > 0.6 ? '#ef4444' : '#f59e0b')
      .attr('stroke', '#05080f').attr('stroke-width', 1.5);

    // 11) Hover + click
    nodeG
      .on('mouseenter', function(ev, d) {
        d3.select(this).select('.node-main').attr('fill', (CLAUSE_TYPE_COLORS[d.type] || '#94a3b8') + '38').attr('stroke-width', 3);
        d3.select(this).select('.node-ring').attr('stroke', (CLAUSE_TYPE_COLORS[d.type] || '#94a3b8') + '42').attr('stroke-width', 2.5);
      })
      .on('mouseleave', function(ev, d) {
        d3.select(this).select('.node-main').attr('fill', (CLAUSE_TYPE_COLORS[d.type] || '#94a3b8') + '1c').attr('stroke-width', 2);
        d3.select(this).select('.node-ring').attr('stroke', (CLAUSE_TYPE_COLORS[d.type] || '#94a3b8') + '20').attr('stroke-width', 1.5);
      })
      .on('click', function(ev, d) { ev.stopPropagation(); setSelectedType((prev) => prev?.id === d.id ? null : d); });

    svgEl.on('click', () => setSelectedType(null));

    // 12) Tick — clamp positions to stay within bounds
    sim.on('tick', () => {
      typeNodes.forEach((d) => {
        const r = getR(d) + 14;
        d.x = Math.max(r, Math.min(W - r, d.x ?? W / 2));
        d.y = Math.max(r, Math.min(H - r, d.y ?? H / 2));
      });
      linkG.selectAll('.edge-line')
        .attr('x1', (d) => d.source.x).attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x).attr('y2', (d) => d.target.y);
      linkG.selectAll('.edge-label')
        .attr('x', (d) => (d.source.x + d.target.x) / 2)
        .attr('y', (d) => (d.source.y + d.target.y) / 2);
      g.selectAll('.type-node').attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    return () => { sim.stop(); };
  }, [nodes, edges, dims]);

  const typeCount = nodes ? Object.keys(nodes.reduce((a, n) => ({ ...a, [n.clause_type]: 1 }), {})).length : 0;

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', flex: 1, minHeight: 400, background: '#05080f', overflow: 'hidden' }}>
      {dims.w > 0 && <svg ref={svgRef} style={{ display: 'block', position: 'absolute', top: 0, left: 0 }} />}

      {/* Stats overlay */}
      <div style={{
        position: 'absolute', top: 10, left: 10, zIndex: 10,
        background: 'rgba(5,8,15,0.90)', border: '1px solid rgba(99,102,241,0.2)',
        borderRadius: 10, padding: '9px 13px', backdropFilter: 'blur(14px)',
        pointerEvents: 'none',
      }}>
        <div style={{ fontSize: 9, color: '#64748b', fontWeight: 800, letterSpacing: 1.2, marginBottom: 5, textTransform: 'uppercase' }}>Clause Type Network</div>
        <div style={{ fontSize: 11, color: '#94a3b8', display: 'flex', gap: 12 }}>
          <span><span style={{ color: '#818cf8', fontWeight: 700 }}>{nodes?.length || 0}</span> clauses</span>
          <span><span style={{ color: '#06b6d4', fontWeight: 700 }}>{typeCount}</span> types</span>
        </div>
        <div style={{ fontSize: 9, color: '#64748b', marginTop: 4 }}>Click type · Scroll to zoom · Drag to pan</div>
      </div>

      {/* Selected type slide-in panel */}
      {selectedType && (
        <div style={{
          position: 'absolute', top: 0, right: 0, bottom: 0, width: 272, zIndex: 20,
          background: 'rgba(5,8,15,0.97)',
          borderLeft: `2px solid ${CLAUSE_TYPE_COLORS[selectedType.type] || '#94a3b8'}50`,
          display: 'flex', flexDirection: 'column',
          boxShadow: '-6px 0 32px rgba(0,0,0,0.6)',
          backdropFilter: 'blur(20px)',
        }}>
          {/* Panel header */}
          <div style={{ padding: '13px 14px 11px', borderBottom: '1px solid rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: CLAUSE_TYPE_COLORS[selectedType.type] || '#94a3b8', boxShadow: `0 0 8px ${CLAUSE_TYPE_COLORS[selectedType.type] || '#94a3b8'}` }} />
              <span style={{ fontSize: 13, fontWeight: 800, color: CLAUSE_TYPE_COLORS[selectedType.type] || '#e2e8f0' }}>{selectedType.type}</span>
            </div>
            <button onClick={() => setSelectedType(null)}
              style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 6, color: '#94a3b8', cursor: 'pointer', fontSize: 13, width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >✕</button>
          </div>

          {/* Stats row */}
          <div style={{ padding: '10px 14px', display: 'flex', gap: 8, borderBottom: '1px solid rgba(99,102,241,0.08)', flexShrink: 0 }}>
            <div style={{ flex: 1, textAlign: 'center', padding: '7px 4px', background: `${CLAUSE_TYPE_COLORS[selectedType.type] || '#818cf8'}12`, border: `1px solid ${CLAUSE_TYPE_COLORS[selectedType.type] || '#818cf8'}25`, borderRadius: 8 }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: CLAUSE_TYPE_COLORS[selectedType.type] || '#818cf8' }}>{selectedType.count}</div>
              <div style={{ fontSize: 9, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.8 }}>Clauses</div>
            </div>
            <div style={{ flex: 1, textAlign: 'center', padding: '7px 4px', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.1)', borderRadius: 8 }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: selectedType.avgRisk > 0.6 ? '#f87171' : selectedType.avgRisk > 0.3 ? '#fbbf24' : '#34d399' }}>
                {Math.round(selectedType.avgRisk * 100)}%
              </div>
              <div style={{ fontSize: 9, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.8 }}>Avg Risk</div>
            </div>
          </div>

          {/* Clause list */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '10px 10px', display: 'flex', flexDirection: 'column', gap: 7 }}>
            <div style={{ fontSize: 9, color: '#64748b', fontWeight: 800, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4, paddingLeft: 2 }}>
              All {selectedType.count} Clause{selectedType.count !== 1 ? 's' : ''}
            </div>
            {selectedType.clauses.map((clause, i) => {
              const rb = riskBadge(clause.risk_score || 0);
              const typeC = CLAUSE_TYPE_COLORS[clause.clause_type] || '#94a3b8';
              return (
                <div key={i} style={{
                  padding: '9px 11px', borderRadius: 10,
                  background: 'rgba(10,14,26,0.9)',
                  border: `1px solid ${typeC}20`,
                  borderLeft: `3px solid ${typeC}`,
                }}>
                  {(clause.contract_name || clause.contract_id) && (
                    <div style={{ fontSize: 9, color: '#7dd3fc', fontWeight: 600, marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      📄 {clause.contract_name || clause.contract_id}
                    </div>
                  )}
                  <p style={{ fontSize: 11, color: '#cbd5e1', lineHeight: 1.6, margin: '0 0 5px' }}>
                    {(clause.text_snippet || 'No text available').slice(0, 115)}
                    {(clause.text_snippet?.length || 0) > 115 ? '…' : ''}
                  </p>
                  {(clause.risk_score || 0) > 0.1 && (
                    <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 20, background: rb.bg, border: `1px solid ${rb.border}44`, color: rb.color, fontWeight: 700 }}>
                      {rb.label} {Math.round((clause.risk_score || 0) * 100)}%
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Pipeline step indicator ───────────────────────────────────────────────
const PipelineStep = ({ label, icon, active, done }) => (
  <div className="flex flex-col items-center gap-1 flex-1 min-w-0">
    <div
      className="w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-500"
      style={{
        background: done
          ? 'linear-gradient(135deg,#059669,#10b981)'
          : active
            ? 'linear-gradient(135deg,#7c3aed,#06b6d4)'
            : 'rgba(99,102,241,0.08)',
        border: done || active ? 'none' : '1px solid rgba(99,102,241,0.2)',
        boxShadow: active ? '0 0 16px rgba(6,182,212,0.5)' : 'none',
      }}
    >
      {done ? '✓' : icon}
    </div>
    <span className="text-xs text-center text-gray-400 leading-tight">{label}</span>
  </div>
);

const SEVERITY_COLOR = {
  critical: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.25)', text: '#f87171' },
  high:     { bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.25)', text: '#fb923c' },
  warning:  { bg: 'rgba(234,179,8,0.08)', border: 'rgba(234,179,8,0.25)', text: '#facc15' },
  medium:   { bg: 'rgba(234,179,8,0.08)', border: 'rgba(234,179,8,0.25)', text: '#facc15' },
  info:     { bg: 'rgba(6,182,212,0.06)', border: 'rgba(6,182,212,0.2)', text: '#22d3ee' },
  success:  { bg: 'rgba(16,185,129,0.06)', border: 'rgba(16,185,129,0.2)', text: '#34d399' },
};

const StrategyMemoryTab = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [pipelineStep, setPipelineStep] = useState(-1); // -1=idle, 0-3=active steps

  const handleBuild = async () => {
    setLoading(true);
    setError('');
    setSearchResults(null);
    setPipelineStep(0);
    try {
      // Animate pipeline steps
      const stepDelay = (ms) => new Promise((r) => setTimeout(r, ms));
      await stepDelay(400); setPipelineStep(1);
      await stepDelay(400); setPipelineStep(2);
      const data = await buildStrategyMemory();
      setPipelineStep(3);
      await stepDelay(300); setPipelineStep(4); // all done
      setResult(data);
    } catch (err) {
      setPipelineStep(-1);
      setError(err?.response?.data?.error || 'Failed to build memory graph.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setSearchResults(null);
    try {
      const data = await searchMemory(searchQuery.trim(), 8);
      setSearchResults(data);
    } catch (err) {
      setSearchResults({ error: err?.response?.data?.error || 'Search failed.' });
    } finally {
      setSearchLoading(false);
    }
  };

  const typeDistribution = result
    ? Object.entries(
        result.nodes.reduce((acc, n) => { acc[n.clause_type] = (acc[n.clause_type] || 0) + 1; return acc; }, {})
      ).sort((a, b) => b[1] - a[1])
    : [];

  const PIPELINE = [
    { label: 'Fetch Clauses', icon: '📄' },
    { label: 'Generate Embeddings', icon: '🔢' },
    { label: 'Build FAISS Index', icon: '⚡' },
    { label: 'Construct Graph', icon: '🌐' },
  ];

  return (
    <div className="space-y-5">
      {/* ── Header + Pipeline ───────────────────────────────────────── */}
      <Card>
        <SectionHeader
          title="Contract Strategy Memory"
          subtitle="AI embeddings connect similar clauses across contracts into a live knowledge graph. Similarity threshold: 75%."
          icon="🧠"
        />

        {/* Pipeline visualization */}
        <div className="mb-5 p-4 rounded-2xl" style={{ background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.1)' }}>
          <div className="text-xs text-gray-500 mb-3 font-semibold uppercase tracking-wider">Intelligence Pipeline</div>
          <div className="flex items-center gap-2">
            {PIPELINE.map((step, idx) => (
              <React.Fragment key={step.label}>
                <PipelineStep
                  label={step.label}
                  icon={step.icon}
                  active={pipelineStep === idx}
                  done={pipelineStep > idx}
                />
                {idx < PIPELINE.length - 1 && (
                  <div className="flex-1 relative h-1 rounded-full overflow-hidden" style={{ background: 'rgba(99,102,241,0.1)', minWidth: 20 }}>
                    <div
                      className="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
                      style={{
                        width: pipelineStep > idx ? '100%' : pipelineStep === idx ? '60%' : '0%',
                        background: pipelineStep > idx ? 'linear-gradient(90deg, #10b981, #06b6d4)' : 'linear-gradient(90deg, #7c3aed, #06b6d4)',
                        boxShadow: pipelineStep >= idx ? '0 0 8px rgba(6,182,212,0.5)' : 'none',
                      }}
                    />
                  </div>
                )}
              </React.Fragment>
            ))}
            <div className="flex flex-col items-center gap-1 flex-1 min-w-0">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all"
                style={{
                  background: pipelineStep === 4 ? 'linear-gradient(135deg,#7c3aed,#06b6d4)' : 'rgba(99,102,241,0.08)',
                  border: pipelineStep === 4 ? 'none' : '1px solid rgba(99,102,241,0.2)',
                  boxShadow: pipelineStep === 4 ? '0 0 20px rgba(6,182,212,0.5)' : 'none',
                }}
              >
                {pipelineStep === 4 ? '🎯' : '💡'}
              </div>
              <span className="text-xs text-center text-gray-400">Generate Insights</span>
            </div>
          </div>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          {[
            { icon: '🔗', title: 'Semantic Linking', desc: 'MiniLM connects similar clauses' },
            { icon: '🌐', title: 'Knowledge Graph', desc: 'NetworkX graph with FAISS search' },
            { icon: '📐', title: '75% Threshold', desc: 'High-confidence connections only' },
            { icon: '⚡', title: 'Real-Time Build', desc: 'Processes your full portfolio' },
          ].map((f) => (
            <div key={f.title} className="flex items-start gap-2 p-3 rounded-xl" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }}>
              <span className="text-lg">{f.icon}</span>
              <div>
                <p className="text-xs font-semibold text-white">{f.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleBuild}
            disabled={loading}
            className="px-6 py-3 rounded-xl font-semibold text-white flex items-center gap-2 transition-all duration-200 disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 24px rgba(6,182,212,0.3)' }}
          >
            {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
            🧠 {loading ? 'Building Contract Intelligence…' : 'Analyze Contract Intelligence'}
          </button>
          {result && (
            <span className="text-xs text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Built in {result.stats.build_time_seconds}s · {result.stats.clauses_analyzed} clauses · {result.stats.total_contracts} contracts
            </span>
          )}
        </div>
        {error && (
          <div className="mt-3 flex items-center gap-2 px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171', animation: 'fadeInUp 0.3s ease-out' }}>
            <span>⚠️</span>
            <span>{error}</span>
            <button onClick={() => setError('')} style={{ marginLeft: 'auto', color: '#9ca3af', cursor: 'pointer', background: 'none', border: 'none', fontSize: 16 }}>✕</button>
          </div>
        )}
      </Card>

      {result && (
        <>
          {/* ── KPI Row ──────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <KPICard label="Clause Nodes" value={result.stats.total_nodes} icon="⬡" />
            <KPICard label="Connections" value={result.stats.total_connections} colorClass="text-blue-400" icon="🔗" />
            <KPICard label="Avg Similarity" value={`${Math.round(result.stats.avg_similarity * 100)}%`} colorClass="text-emerald-400" icon="📐" />
            <KPICard label="Clusters Found" value={result.stats.clusters_found || 0} colorClass="text-violet-400" icon="🔵" />
            <KPICard label="Total Contracts" value={result.stats.total_contracts} colorClass="text-cyan-400" icon="📁" />
          </div>

          {/* ── Knowledge Graph + Insights Panel ─────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Graph (2/3 width) — self-contained with internal slide-in panel */}
            <Card style={{ padding: 0, overflow: 'hidden', gridColumn: 'span 2', display: 'flex', flexDirection: 'column' }}>
              <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid rgba(99,102,241,0.12)', flexShrink: 0 }}>
                <h4 className="text-white font-semibold flex items-center gap-2 text-sm">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  Clause Type Knowledge Graph
                </h4>
                <span className="text-xs text-gray-500">Click type node to inspect all clauses</span>
              </div>
              {result.nodes.length > 0 ? (
                <ClauseKnowledgeGraph nodes={result.nodes} edges={result.edges} />
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">No clause nodes found.</div>
              )}
            </Card>

            {/* ── Insights Panel (1/3 width) ──────────────────────────── */}
            <div className="space-y-3">
              <Card>
                <div className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  AI Insights
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {(result.insights || []).length === 0 && (
                    <p className="text-xs text-gray-600">No insights generated yet.</p>
                  )}
                  {(result.insights || []).map((ins, i) => {
                    const col = SEVERITY_COLOR[ins.severity] || SEVERITY_COLOR.info;
                    return (
                      <div
                        key={i}
                        className="p-2.5 rounded-xl text-xs leading-relaxed"
                        style={{ background: col.bg, border: `1px solid ${col.border}`, color: col.text }}
                      >
                        <span className="mr-1">{ins.icon}</span>{ins.message}
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Risk Patterns */}
              {(result.risk_patterns || []).length > 0 && (
                <Card>
                  <div className="text-xs font-bold text-white uppercase tracking-wider mb-3">Risk Patterns</div>
                  <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                    {result.risk_patterns.map((p, i) => {
                      const col = SEVERITY_COLOR[p.severity] || SEVERITY_COLOR.warning;
                      return (
                        <div
                          key={i}
                          className="p-2.5 rounded-xl"
                          style={{ background: col.bg, border: `1px solid ${col.border}` }}
                        >
                          <div className="flex items-center gap-1.5 mb-1">
                            <span>{p.icon}</span>
                            <span className="text-xs font-bold" style={{ color: col.text }}>{p.clause_type}</span>
                            <span className="ml-auto text-xs px-1.5 py-0.5 rounded-full" style={{ background: col.border, color: col.text }}>
                              {p.severity}
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 leading-relaxed">{p.description}</p>
                          <p className="text-xs mt-1" style={{ color: col.text }}>→ {p.recommendation}</p>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Clusters */}
              {(result.clusters || []).length > 0 && (
                <Card>
                  <div className="text-xs font-bold text-white uppercase tracking-wider mb-3">Clause Clusters</div>
                  <div className="space-y-2">
                    {result.clusters.slice(0, 4).map((cl, i) => (
                      <div key={i} className="p-2 rounded-xl" style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.12)' }}>
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-xs font-semibold" style={{ color: CLAUSE_TYPE_COLORS[cl.dominant_type] || '#94a3b8' }}>
                            {cl.dominant_type}
                          </span>
                          <span className="text-xs text-gray-500">{cl.size} clauses</span>
                        </div>
                        {cl.avg_risk_score > 0 && (
                          <div className="text-xs text-gray-500">
                            Avg risk: <span className={cl.avg_risk_score > 0.6 ? 'text-red-400' : 'text-emerald-400'}>
                              {Math.round(cl.avg_risk_score * 100)}%
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          </div>

          {/* ── Semantic Search ───────────────────────────────────────── */}
          <Card>
            <div className="text-xs font-bold text-white uppercase tracking-wider mb-3">Semantic Clause Search</div>
            <div className="flex gap-2 mb-4">
              <StyledInput
                placeholder="Search similar clauses… e.g. 'force majeure pandemic relief'"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button onClick={handleSearch} loading={searchLoading} variant="primary">
                🔍 Search
              </Button>
            </div>
            {searchResults && !searchResults.error && (
              <div className="space-y-3 mt-2">
                {searchResults.results?.length === 0 && (
                  <p style={{ fontSize: 12, color: '#475569' }}>No similar clauses found above 50% threshold. Try a broader query.</p>
                )}
                {(searchResults.results || []).map((r, i) => {
                  const sc   = simColor(r.similarity);
                  const pct  = Math.round(r.similarity * 100);
                  const typeC = CLAUSE_TYPE_COLORS[r.clause_type] || '#94a3b8';
                  return (
                    <div
                      key={i}
                      style={{
                        padding: '12px 14px', borderRadius: 12, display: 'flex', gap: 12, alignItems: 'flex-start',
                        background: 'rgba(8,12,24,0.8)',
                        border: `1px solid ${typeC}28`,
                        borderLeft: `3px solid ${typeC}`,
                        boxShadow: '0 2px 12px rgba(0,0,0,0.3)',
                      }}
                    >
                      {/* Rank */}
                      <div style={{ fontSize: 11, color: '#374151', fontWeight: 700, minWidth: 20, paddingTop: 1 }}>#{i + 1}</div>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        {/* Top row */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, flexWrap: 'wrap' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ width: 9, height: 9, borderRadius: '50%', background: typeC, flexShrink: 0, boxShadow: `0 0 6px ${typeC}` }} />
                            <span style={{ fontSize: 12, fontWeight: 700, color: typeC }}>{r.clause_type}</span>
                          </div>
                          {r.contract_name && (
                            <span style={{ fontSize: 10, color: '#7dd3fc', background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.15)', padding: '1px 7px', borderRadius: 20, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              📄 {r.contract_name}
                            </span>
                          )}
                          {/* Similarity badge */}
                          <span style={{
                            marginLeft: 'auto', fontSize: 11, fontWeight: 700, padding: '3px 10px',
                            borderRadius: 20, flexShrink: 0,
                            background: `${sc}18`, border: `1px solid ${sc}44`, color: sc,
                          }}>
                            {pct}% match
                          </span>
                        </div>

                        {/* Similarity bar */}
                        <div style={{ height: 3, borderRadius: 4, background: 'rgba(99,102,241,0.1)', marginBottom: 8, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${pct}%`, background: `linear-gradient(90deg, ${sc}88, ${sc})`, borderRadius: 4, transition: 'width 0.6s ease' }} />
                        </div>

                        {/* Clause text */}
                        <p style={{ fontSize: 11, color: '#94a3b8', lineHeight: 1.65, margin: 0 }}>
                          {r.text_snippet?.slice(0, 140)}{(r.text_snippet?.length || 0) > 140 ? '…' : ''}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            {searchResults?.error && (
              <div style={{ marginTop: 8, padding: '10px 14px', borderRadius: 10, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5', fontSize: 12 }}>
                ⚠ {searchResults.error}
              </div>
            )}
          </Card>

          {/* ── Risk Patterns (full-width breakdown) ─────────────────── */}
          {(result.type_stats || []).length > 0 && (
            <Card>
              <h4 className="text-white font-semibold mb-4 text-sm flex items-center gap-2">📊 Clause Intelligence Breakdown</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(99,102,241,0.12)' }}>
                      {['Clause Type', 'Count', 'Coverage', 'Avg Risk', 'Variation', 'Status'].map((h) => (
                        <th key={h} className="text-left pb-2 pr-4 text-gray-500 font-semibold uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.type_stats.sort((a, b) => b.contract_coverage_pct - a.contract_coverage_pct).map((ts, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(99,102,241,0.06)' }}>
                        <td className="py-2 pr-4">
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: ts.color }} />
                            <span className="text-gray-200 font-medium">{ts.clause_type}</span>
                          </div>
                        </td>
                        <td className="py-2 pr-4 text-gray-400">{ts.count}</td>
                        <td className="py-2 pr-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 rounded-full" style={{ background: 'rgba(99,102,241,0.15)' }}>
                              <div className="h-full rounded-full" style={{ width: `${ts.contract_coverage_pct}%`, background: ts.contract_coverage_pct >= 75 ? '#10b981' : ts.contract_coverage_pct >= 40 ? '#06b6d4' : '#6b7280' }} />
                            </div>
                            <span className="text-gray-400">{ts.contract_coverage_pct}%</span>
                          </div>
                        </td>
                        <td className="py-2 pr-4">
                          <span className={ts.avg_risk_score > 0.6 ? 'text-red-400' : ts.avg_risk_score > 0.3 ? 'text-yellow-400' : 'text-emerald-400'}>
                            {Math.round(ts.avg_risk_score * 100)}%
                          </span>
                        </td>
                        <td className="py-2 pr-4">
                          <span className={ts.variation_score > 0.4 ? 'text-orange-400' : 'text-gray-400'}>
                            {Math.round(ts.variation_score * 100)}%
                          </span>
                        </td>
                        <td className="py-2">
                          {ts.is_high_risk ? (
                            <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>High Risk</span>
                          ) : ts.avg_degree >= 3 ? (
                            <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(16,185,129,0.1)', color: '#34d399', border: '1px solid rgba(16,185,129,0.2)' }}>Standardized</span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(99,102,241,0.08)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.15)' }}>Normal</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* ── Cross-Module Integration ──────────────────────────────── */}
          {result.integration && (
            <Card>
              <h4 className="text-white font-semibold mb-4 text-sm flex items-center gap-2">🔌 Cross-Module Integration Signals</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { key: 'redlining',   icon: '✏️', label: 'Redlining AI',      color: '#f87171' },
                  { key: 'negotiation', icon: '🤝', label: 'Negotiation Agents', color: '#fb923c' },
                  { key: 'legal',       icon: '⚖️', label: 'Legal Engine',       color: '#818cf8' },
                  { key: 'cfo',         icon: '📊', label: 'CFO Simulator',      color: '#34d399' },
                ].map(({ key, icon, label, color }) => {
                  const sig = result.integration[key];
                  return (
                    <div key={key} className="p-3 rounded-xl" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }}>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span>{icon}</span>
                        <span className="text-xs font-semibold" style={{ color }}>{label}</span>
                      </div>
                      <p className="text-xs text-gray-500 leading-relaxed">{sig?.message || '—'}</p>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* ── Clause Type Distribution ──────────────────────────────── */}
          <Card>
            <h4 className="text-white font-semibold mb-3 text-sm flex items-center gap-2">🏷️ Clause Type Distribution</h4>
            <div className="flex flex-wrap gap-2">
              {typeDistribution.map(([type, count]) => (
                <div
                  key={type}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
                  style={{
                    background: `${CLAUSE_TYPE_COLORS[type] || '#94a3b8'}18`,
                    border: `1px solid ${CLAUSE_TYPE_COLORS[type] || '#94a3b8'}44`,
                    color: CLAUSE_TYPE_COLORS[type] || '#94a3b8',
                  }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: CLAUSE_TYPE_COLORS[type] || '#94a3b8' }} />
                  {type} <span className="opacity-60 ml-0.5">({count})</span>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
};

// ─── Tab 2: Live Monitoring ───────────────────────────────────────

const AUTO_ACTION_META = {
  war:           { label: 'Suggest Renegotiation', icon: '⚔️', color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.25)', confidence: 94 },
  supplier_risk: { label: 'Flag Payment Hold',    icon: '🏦', color: '#f97316', bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.25)', confidence: 87 },
  fx_spike:      { label: 'Reprice Contract',     icon: '💱', color: '#eab308', bg: 'rgba(234,179,8,0.08)',  border: 'rgba(234,179,8,0.25)', confidence: 91 },
  policy_change: { label: 'Compliance Review',    icon: '📋', color: '#8b5cf6', bg: 'rgba(139,92,246,0.08)', border: 'rgba(139,92,246,0.25)', confidence: 82 },
  weather:       { label: 'Monitor Delivery',     icon: '🌦️', color: '#06b6d4', bg: 'rgba(6,182,212,0.08)',  border: 'rgba(6,182,212,0.25)', confidence: 78 },
};

const AI_REASONING = {
  war: {
    reasoning: 'Force majeure clause triggered by armed conflict in contract region. Delivery timelines and payment terms require immediate renegotiation with counterparty to prevent breach of contract obligations.',
    clauses: ['Force Majeure', 'Delivery Terms', 'Payment Terms', 'Termination'],
  },
  supplier_risk: {
    reasoning: 'Supplier financial distress indicators detected. Holding scheduled payments prevents exposure to potential default while a full risk assessment is conducted on the counterparty.',
    clauses: ['Payment Terms', 'Indemnification', 'Assignment'],
  },
  fx_spike: {
    reasoning: 'Currency volatility exceeds contract tolerance threshold. Contract obligations must be revalued at current FX rate to maintain margin targets and avoid adverse financial exposure.',
    clauses: ['Payment Terms', 'Pricing', 'Governing Law'],
  },
  policy_change: {
    reasoning: 'Regulatory framework change requires immediate compliance clause audit. Amendments may be required to maintain legal standing and avoid regulatory penalties.',
    clauses: ['Compliance', 'Governing Law', 'Termination'],
  },
  weather: {
    reasoning: 'Extreme weather event may affect delivery milestones. Force majeure applicability assessment recommended to protect against penalty clauses.',
    clauses: ['Force Majeure', 'Delivery Terms'],
  },
};

const EVENT_TYPE_ICONS = {
  war: '⚔️', supplier_risk: '🏦', fx_spike: '💱', policy_change: '📋', weather: '🌦️',
};

const SEVERITY_LEFT_BORDER = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' };
const SEVERITY_GLOW = { critical: 'rgba(239,68,68,0.18)', high: 'rgba(249,115,22,0.13)', medium: 'rgba(234,179,8,0.08)', low: 'rgba(34,197,94,0.07)' };

// ─── Alert Detail Modal ───────────────────────────────────────────
const AlertDetailModal = ({ alert, onClose }) => {
  if (!alert) return null;
  const eventIcon = EVENT_TYPE_ICONS[alert.alert_type] || '📡';
  const reasoning = AI_REASONING[alert.alert_type];
  const sc = {
    critical: { glow: 'rgba(239,68,68,0.35)', border: 'rgba(239,68,68,0.45)', text: '#ef4444' },
    high:     { glow: 'rgba(249,115,22,0.28)', border: 'rgba(249,115,22,0.38)', text: '#f97316' },
    medium:   { glow: 'rgba(234,179,8,0.2)',   border: 'rgba(234,179,8,0.32)',  text: '#eab308' },
    low:      { glow: 'rgba(34,197,94,0.18)',  border: 'rgba(34,197,94,0.28)', text: '#22c55e' },
  }[alert.severity] || { glow: 'rgba(99,102,241,0.2)', border: 'rgba(99,102,241,0.35)', text: '#a5b4fc' };

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.72)', backdropFilter: 'blur(10px)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
      onClick={onClose}
    >
      <div
        style={{ background: 'rgba(10,13,20,0.98)', border: `1px solid ${sc.border}`, borderRadius: 20, padding: 28, maxWidth: 560, width: '100%', boxShadow: `0 0 70px ${sc.glow}`, animation: 'fadeInUp 0.22s ease-out' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 46, height: 46, borderRadius: 12, background: sc.glow, border: `1px solid ${sc.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>
              {eventIcon}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ color: sc.text, fontWeight: 800, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em' }}>{alert.severity}</span>
                <span style={{ color: '#374151', fontSize: 10 }}>•</span>
                <span style={{ color: '#9ca3af', fontSize: 11 }}>{(alert.alert_type || '').replace(/_/g, ' ').toUpperCase()}</span>
              </div>
              <p style={{ color: '#f3f4f6', fontWeight: 600, fontSize: 14, margin: 0 }}>{alert.headline || alert.message}</p>
            </div>
          </div>
          <button onClick={onClose} style={{ color: '#6b7280', fontSize: 22, lineHeight: 1, background: 'none', border: 'none', cursor: 'pointer', padding: '2px 8px', borderRadius: 6 }}>×</button>
        </div>

        {/* Alert body */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10, padding: '12px 14px', marginBottom: 16 }}>
          <p style={{ color: '#d1d5db', fontSize: 13, lineHeight: 1.65, margin: 0 }}>{alert.message}</p>
        </div>

        {/* AI Reasoning */}
        {reasoning && (
          <div style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.18)', borderRadius: 10, padding: '12px 14px', marginBottom: 16 }}>
            <p style={{ color: '#a5b4fc', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 7 }}>🤖 AI Reasoning</p>
            <p style={{ color: '#d1d5db', fontSize: 12, lineHeight: 1.65, marginBottom: 10 }}>{reasoning.reasoning}</p>
            <p style={{ color: '#6b7280', fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Impacted Clauses</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {reasoning.clauses.map((c, i) => (
                <span key={i} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 6, background: 'rgba(139,92,246,0.13)', border: '1px solid rgba(139,92,246,0.28)', color: '#c4b5fd' }}>{c}</span>
              ))}
            </div>
          </div>
        )}

        {/* Meta row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 18 }}>
          {[
            { label: 'Severity', value: (alert.severity || 'medium').toUpperCase(), color: sc.text },
            { label: 'Contract', value: alert.contract_id ? alert.contract_id.slice(0, 10) + '…' : 'Platform-wide', color: '#06b6d4' },
            { label: 'Detected', value: alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : '—', color: '#a5b4fc' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 9, padding: '10px 12px', textAlign: 'center' }}>
              <p style={{ color: '#6b7280', fontSize: 9, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>{label}</p>
              <p style={{ color, fontSize: 12, fontWeight: 700, margin: 0 }}>{value}</p>
            </div>
          ))}
        </div>

        <button onClick={onClose} style={{ width: '100%', padding: '11px', borderRadius: 10, background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', border: 'none', color: 'white', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
          Close
        </button>
      </div>
    </div>
  );
};

const AutoActionPanel = () => {
  const [selectedEvent, setSelectedEvent] = useState('war');
  const [headline, setHeadline] = useState('');
  const [loading, setLoading] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [log, setLog] = useState([]);
  const [error, setError] = useState('');
  const { showToast } = useToast();

  const loadLog = useCallback(async () => {
    try {
      const data = await getAutoActionLog();
      setLog(data.actions || []);
    } catch { /* silently fail */ }
  }, []);

  useEffect(() => { loadLog(); }, [loadLog]);

  const handleTrigger = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const data = await triggerAutoAction({ event_type: selectedEvent, headline });
      setResult(data);
      await loadLog();
      showToast(`Action triggered: ${AUTO_ACTION_META[selectedEvent]?.label}`, 'success');
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to trigger action.');
      showToast('Failed to trigger action', 'error');
    } finally { setLoading(false); }
  };

  const handleBulk = async () => {
    setBulkLoading(true); setError('');
    try {
      const data = await bulkAutoAction({ event_type: selectedEvent, headline: headline || `Bulk ${selectedEvent} action` });
      setResult(data);
      await loadLog();
      showToast('Bulk action triggered across all contracts', 'success');
    } catch (err) {
      setError(err?.response?.data?.error || 'Bulk action failed.');
      showToast('Bulk action failed', 'error');
    } finally { setBulkLoading(false); }
  };

  const meta = AUTO_ACTION_META[selectedEvent] || AUTO_ACTION_META.war;
  const reasoning = AI_REASONING[selectedEvent] || AI_REASONING.war;

  return (
    <Card>
      <SectionHeader title="Auto-Action Engine" subtitle="AI-triggered actions based on event type — war, supplier risk, FX spike, policy changes." icon="🤖" />

      {/* Event Type Selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        {Object.entries(AUTO_ACTION_META).map(([key, m]) => (
          <button
            key={key}
            onClick={() => setSelectedEvent(key)}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200"
            style={selectedEvent === key
              ? { background: m.bg, border: `1px solid ${m.border}`, color: m.color, boxShadow: `0 0 14px ${m.bg}` }
              : { background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)', color: '#6b7280' }}
          >
            {m.icon} {m.label}
          </button>
        ))}
      </div>

      {/* Selected Action + AI Reasoning */}
      <div className="p-4 rounded-xl mb-4" style={{ background: meta.bg, border: `1px solid ${meta.border}` }}>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xl">{meta.icon}</span>
          <span className="font-bold text-sm" style={{ color: meta.color }}>{meta.label}</span>
          <span className="text-xs text-gray-500 ml-auto capitalize">{selectedEvent.replace(/_/g, ' ')}</span>
          {/* Confidence badge */}
          <div style={{ background: 'rgba(0,0,0,0.35)', border: `1px solid ${meta.border}`, borderRadius: 7, padding: '3px 9px', display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ color: '#6b7280', fontSize: 9, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>AI Confidence</span>
            <span style={{ color: meta.color, fontWeight: 800, fontSize: 13 }}>{meta.confidence}%</span>
          </div>
        </div>
        <p className="text-gray-400 text-xs mb-3" style={{ lineHeight: 1.6 }}>{reasoning.reasoning}</p>
        <div>
          <p style={{ color: '#6b7280', fontSize: 9, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Impacted Clauses</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {reasoning.clauses.map((clause, i) => (
              <span key={i} style={{ fontSize: 10, padding: '2px 8px', borderRadius: 5, background: `${meta.border}22`, border: `1px solid ${meta.border}`, color: meta.color }}>{clause}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-1.5 block font-medium">Event Headline (optional)</label>
        <StyledInput type="text" value={headline} onChange={(e) => setHeadline(e.target.value)} placeholder="e.g. USD/INR surges 8% after Fed announcement…" />
      </div>

      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

      <div className="flex gap-3 mb-4">
        <Button onClick={handleTrigger} loading={loading}>{meta.icon} Trigger Action</Button>
        <Button onClick={handleBulk} loading={bulkLoading} variant="outline">⚡ Bulk — All Contracts</Button>
      </div>

      {/* Result */}
      {result && result.action && (
        <div className="p-4 rounded-xl mb-4 space-y-2" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
          <p className="text-emerald-400 text-sm font-semibold">✅ {result.message}</p>
          {result.action?.steps && (
            <ol className="text-xs text-gray-400 space-y-1 pl-4 list-decimal">
              {result.action.steps.map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          )}
          {result.contracts_affected !== undefined && (
            <p className="text-cyan-400 text-xs mt-1">📊 {result.contracts_affected} contracts affected</p>
          )}
        </div>
      )}

      {/* Recent Actions Log */}
      {log.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-widest">Recent Actions ({log.length})</p>
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {log.slice(0, 12).map((a) => {
              const m = AUTO_ACTION_META[a.event_type] || AUTO_ACTION_META.war;
              const isExecuted = a.status === 'executed';
              return (
                <div key={a.id} className="flex items-center gap-3 p-3 rounded-xl text-xs" style={{ background: 'rgba(13,17,23,0.6)', border: `1px solid ${m.border}`, transition: 'all 0.2s' }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = `${m.bg}`; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(13,17,23,0.6)'; }}
                >
                  <span style={{ fontSize: 16 }}>{m.icon}</span>
                  <div className="flex-1 min-w-0">
                    <span className="font-semibold" style={{ color: m.color }}>{a.label}</span>
                    {a.contract_info?.name && (
                      <span className="text-gray-500 ml-2 truncate"> — {a.contract_info.name.slice(0, 28)}</span>
                    )}
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 20, background: isExecuted ? 'rgba(16,185,129,0.15)' : 'rgba(6,182,212,0.12)', color: isExecuted ? '#34d399' : '#67e8f9', border: `1px solid ${isExecuted ? 'rgba(16,185,129,0.3)' : 'rgba(6,182,212,0.25)'}` }}>
                    {isExecuted ? '● Executed' : '○ Pending'}
                  </span>
                  <span className="text-gray-600 whitespace-nowrap">{a.created_at ? new Date(a.created_at).toLocaleTimeString() : ''}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
};

const MonitoringTab = () => {
  const [alerts, setAlerts] = useState([]);
  const [scanLoading, setScanLoading] = useState(false);
  const [eventLoading, setEventLoading] = useState(false);
  const [eventType, setEventType] = useState('fx_spike');
  const [headline, setHeadline] = useState('');
  const [error, setError] = useState('');
  const [scanMessage, setScanMessage] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [secondsAgo, setSecondsAgo] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [expandedAlerts, setExpandedAlerts] = useState(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterEventType, setFilterEventType] = useState('all');
  const [filterTimeRange, setFilterTimeRange] = useState('all');
  const intervalRef = useRef(null);
  const tickRef = useRef(null);
  const { showToast } = useToast();

  const loadAlerts = useCallback(async () => {
    try {
      const data = await getMonitorAlerts();
      setAlerts(data.alerts || []);
      setLastUpdated(new Date());
      setSecondsAgo(0);
    } catch { /* silently fail */ }
  }, []);

  useEffect(() => { loadAlerts(); }, [loadAlerts]);

  // Auto-refresh toggle
  useEffect(() => {
    clearInterval(intervalRef.current);
    if (autoRefresh) intervalRef.current = setInterval(loadAlerts, 15000);
    return () => clearInterval(intervalRef.current);
  }, [autoRefresh, loadAlerts]);

  // Live seconds-ago ticker
  useEffect(() => {
    tickRef.current = setInterval(() => setSecondsAgo((s) => s + 1), 1000);
    return () => clearInterval(tickRef.current);
  }, []);

  // Filtered + paginated alerts
  const filteredAlerts = useMemo(() => {
    let list = [...alerts];
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter((a) =>
        (a.headline || '').toLowerCase().includes(q) ||
        (a.message || '').toLowerCase().includes(q) ||
        (a.alert_type || '').toLowerCase().includes(q)
      );
    }
    if (filterSeverity !== 'all') list = list.filter((a) => a.severity === filterSeverity);
    if (filterEventType !== 'all') list = list.filter((a) => a.alert_type === filterEventType);
    if (filterTimeRange !== 'all') {
      const ms = { '1h': 3600000, '24h': 86400000, '7d': 604800000 }[filterTimeRange];
      if (ms) list = list.filter((a) => !a.created_at || Date.now() - new Date(a.created_at).getTime() < ms);
    }
    return list.slice(0, 50);
  }, [alerts, searchQuery, filterSeverity, filterEventType, filterTimeRange]);

  const handleScan = async () => {
    setScanLoading(true); setScanMessage('');
    try {
      const data = await scanForEvents();
      const msg = `Scan complete: ${data.events_detected} events detected, ${data.alerts_created} alerts created.`;
      setScanMessage(msg);
      await loadAlerts();
      showToast(`${data.alerts_created} new alerts created`, 'success');
    } catch {
      setScanMessage('Scan failed. Please try again.');
      showToast('Scan failed', 'error');
    } finally { setScanLoading(false); }
  };

  const handleCreateEvent = async () => {
    if (!headline.trim()) { setError('Headline is required.'); return; }
    setEventLoading(true); setError('');
    try {
      await createMonitorEvent({ eventType, headline, contractIds: [] });
      setHeadline('');
      await loadAlerts();
      showToast('Event alert created and broadcast to all contracts', 'success');
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to create event.');
    } finally { setEventLoading(false); }
  };

  const toggleExpand = (id) => {
    setExpandedAlerts((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const clearFilters = () => { setSearchQuery(''); setFilterSeverity('all'); setFilterEventType('all'); setFilterTimeRange('all'); };
  const hasFilters = searchQuery || filterSeverity !== 'all' || filterEventType !== 'all' || filterTimeRange !== 'all';

  // Analytics
  const today = new Date().toDateString();
  const eventsToday = alerts.filter((a) => a.created_at && new Date(a.created_at).toDateString() === today).length;
  const highRiskCount = alerts.filter((a) => a.severity === 'critical' || a.severity === 'high').length;

  const MiniSelect = ({ value, onChange, children }) => (
    <select value={value} onChange={onChange} style={{ background: 'rgba(13,17,23,0.85)', border: '1px solid rgba(99,102,241,0.15)', borderRadius: 8, color: '#d1d5db', fontSize: 11, padding: '5px 9px', outline: 'none', cursor: 'pointer' }}>
      {children}
    </select>
  );

  return (
    <div className="space-y-5">
      {/* ── LIVE HEADER ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderRadius: 16, background: 'rgba(239,68,68,0.04)', border: '1px solid rgba(239,68,68,0.18)', backdropFilter: 'blur(12px)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Pulsing dot */}
          <div style={{ position: 'relative', width: 14, height: 14, flexShrink: 0 }}>
            <span style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: 'rgba(239,68,68,0.4)', animation: 'pulseGlow 1.4s ease-in-out infinite' }} />
            <span style={{ position: 'absolute', inset: 3, borderRadius: '50%', background: '#ef4444' }} />
          </div>
          <span style={{ color: '#ef4444', fontWeight: 800, fontSize: 12, letterSpacing: '0.12em' }}>LIVE</span>
          <span style={{ color: '#6b7280', fontSize: 11 }}>
            {lastUpdated ? `Updated ${secondsAgo}s ago` : 'Connecting…'}
          </span>
          <div style={{ width: 1, height: 14, background: 'rgba(99,102,241,0.25)' }} />
          {/* Auto-refresh toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <span style={{ color: '#6b7280', fontSize: 11 }}>Auto-refresh</span>
            <div
              onClick={() => setAutoRefresh((v) => !v)}
              style={{ width: 38, height: 21, borderRadius: 11, background: autoRefresh ? 'linear-gradient(135deg, #06b6d4, #7c3aed)' : 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)', cursor: 'pointer', position: 'relative', transition: 'all 0.3s', flexShrink: 0 }}
            >
              <div style={{ position: 'absolute', top: 3, left: autoRefresh ? 19 : 3, width: 13, height: 13, borderRadius: '50%', background: '#fff', transition: 'left 0.3s', boxShadow: '0 1px 4px rgba(0,0,0,0.4)' }} />
            </div>
            <span style={{ color: autoRefresh ? '#06b6d4' : '#4b5563', fontSize: 10, fontWeight: 700 }}>{autoRefresh ? 'ON' : 'OFF'}</span>
          </div>
        </div>
        <button
          onClick={handleScan}
          disabled={scanLoading}
          style={{ padding: '8px 18px', borderRadius: 12, background: 'linear-gradient(135deg, #0891b2, #06b6d4)', border: 'none', color: 'white', fontWeight: 700, fontSize: 13, cursor: scanLoading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 7, opacity: scanLoading ? 0.6 : 1, boxShadow: scanLoading ? 'none' : '0 0 20px rgba(6,182,212,0.4)', transition: 'all 0.2s' }}
        >
          {scanLoading && <span style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', display: 'inline-block', animation: 'spin 0.7s linear infinite' }} />}
          📡 {scanLoading ? 'Scanning…' : 'Scan for Events'}
        </button>
      </div>

      {scanMessage && (
        <div style={{ padding: '10px 16px', borderRadius: 10, color: '#67e8f9', fontSize: 13, background: 'rgba(6,182,212,0.07)', border: '1px solid rgba(6,182,212,0.2)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: '#22c55e', fontWeight: 700 }}>✓</span> {scanMessage}
        </div>
      )}

      {/* ── ANALYTICS DASHBOARD ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { label: 'Events Today',     value: eventsToday,    sub: 'since midnight',          color: '#06b6d4', bg: 'rgba(6,182,212,0.07)',   border: 'rgba(6,182,212,0.2)',   glow: '' },
          { label: 'High-Risk Alerts', value: highRiskCount,  sub: 'critical + high severity', color: '#ef4444', bg: 'rgba(239,68,68,0.07)',   border: 'rgba(239,68,68,0.22)',  glow: highRiskCount > 0 ? '0 0 22px rgba(239,68,68,0.14)' : '' },
          { label: 'Total Alerts',     value: alerts.length,  sub: 'across all contracts',     color: '#10b981', bg: 'rgba(16,185,129,0.07)', border: 'rgba(16,185,129,0.2)',  glow: '' },
          { label: 'Refresh Interval', value: autoRefresh ? '15s' : 'OFF', sub: autoRefresh ? '● Live polling active' : '● Polling paused', color: autoRefresh ? '#8b5cf6' : '#4b5563', bg: 'rgba(139,92,246,0.07)', border: 'rgba(139,92,246,0.2)', glow: '' },
        ].map(({ label, value, sub, color, bg, border, glow }) => (
          <div key={label} style={{ background: bg, border: `1px solid ${border}`, borderRadius: 14, padding: '14px 16px', boxShadow: glow }}>
            <p style={{ color: '#6b7280', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 5 }}>{label}</p>
            <p style={{ color, fontSize: 28, fontWeight: 900, lineHeight: 1, marginBottom: 4 }}>{value}</p>
            <p style={{ color: '#4b5563', fontSize: 10 }}>{sub}</p>
          </div>
        ))}
      </div>

      {/* ── MANUAL EVENT CREATOR ── */}
      <Card>
        <SectionHeader title="Create Manual Event Alert" subtitle="Broadcast an event across all contracts on the platform." icon="⚡" />
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Event Type</label>
            <StyledSelect value={eventType} onChange={(e) => setEventType(e.target.value)}>
              {EVENT_TYPES.map((et) => <option key={et.value} value={et.value}>{et.label}</option>)}
            </StyledSelect>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Headline *</label>
            <StyledInput
              type="text"
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="News headline or event description…"
              onKeyDown={(e) => e.key === 'Enter' && handleCreateEvent()}
            />
          </div>
        </div>
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <Button onClick={handleCreateEvent} loading={eventLoading} disabled={!headline.trim()}>⚡ Create Alert</Button>
      </Card>

      {/* ── AUTO-ACTION ENGINE ── */}
      <AutoActionPanel />

      {/* ── ALERTS FEED ── */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: '#f3f4f6', fontWeight: 700, fontSize: 15 }}>Alerts Feed</span>
            <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 20, background: 'rgba(6,182,212,0.15)', color: '#06b6d4', border: '1px solid rgba(6,182,212,0.3)' }}>
              {filteredAlerts.length}{alerts.length !== filteredAlerts.length ? `/${alerts.length}` : ''}
            </span>
          </div>
          <button onClick={loadAlerts} style={{ fontSize: 11, padding: '5px 10px', borderRadius: 8, background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)', color: '#a5b4fc', cursor: 'pointer' }}>↻ Refresh</button>
        </div>

        {/* ── FILTERS ROW ── */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: '10px 12px', borderRadius: 10, background: 'rgba(13,17,23,0.55)', border: '1px solid rgba(99,102,241,0.08)', marginBottom: 14 }}>
          <div style={{ flex: '1 1 150px', position: 'relative' }}>
            <span style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', fontSize: 12, pointerEvents: 'none' }}>🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search alerts…"
              style={{ width: '100%', background: 'rgba(13,17,23,0.85)', border: '1px solid rgba(99,102,241,0.15)', borderRadius: 8, color: '#d1d5db', fontSize: 11, padding: '5px 9px 5px 27px', outline: 'none', boxSizing: 'border-box' }}
            />
          </div>
          <MiniSelect value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </MiniSelect>
          <MiniSelect value={filterEventType} onChange={(e) => setFilterEventType(e.target.value)}>
            <option value="all">All Event Types</option>
            {EVENT_TYPES.map((et) => <option key={et.value} value={et.value}>{et.label}</option>)}
          </MiniSelect>
          <MiniSelect value={filterTimeRange} onChange={(e) => setFilterTimeRange(e.target.value)}>
            <option value="all">All Time</option>
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24h</option>
            <option value="7d">Last 7 Days</option>
          </MiniSelect>
          {hasFilters && (
            <button onClick={clearFilters} style={{ fontSize: 11, padding: '5px 10px', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171', cursor: 'pointer' }}>✕ Clear</button>
          )}
        </div>

        {filteredAlerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <div style={{ fontSize: 40, marginBottom: 10, opacity: 0.25 }}>📡</div>
            <p style={{ color: '#6b7280', fontSize: 13 }}>
              {alerts.length === 0 ? 'No alerts yet. Click "Scan for Events" to populate.' : 'No alerts match your filters.'}
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 540, overflowY: 'auto', paddingRight: 4 }}>
            {filteredAlerts.map((alert) => {
              const sev = alert.severity || 'medium';
              const isExpanded = expandedAlerts.has(alert.id);
              const isHighRisk = sev === 'critical' || sev === 'high';
              const eventIcon = EVENT_TYPE_ICONS[alert.alert_type] || '📡';
              const reasoning = AI_REASONING[alert.alert_type];
              const borderColor = SEVERITY_LEFT_BORDER[sev] || SEVERITY_LEFT_BORDER.medium;

              return (
                <div
                  key={alert.id}
                  style={{ borderRadius: 12, background: 'rgba(13,17,23,0.65)', border: '1px solid rgba(99,102,241,0.1)', borderLeft: `3px solid ${borderColor}`, boxShadow: isHighRisk ? `0 0 18px ${SEVERITY_GLOW[sev]}` : 'none', transition: 'all 0.2s' }}
                  onMouseEnter={(e) => { e.currentTarget.style.border = `1px solid ${borderColor}44`; e.currentTarget.style.borderLeft = `3px solid ${borderColor}`; }}
                  onMouseLeave={(e) => { e.currentTarget.style.border = '1px solid rgba(99,102,241,0.1)'; e.currentTarget.style.borderLeft = `3px solid ${borderColor}`; }}
                >
                  {/* Card main row — click to open modal */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '14px 14px 14px 14px', cursor: 'pointer' }} onClick={() => setSelectedAlert(alert)}>
                    {/* Icon bubble */}
                    <div style={{ width: 38, height: 38, borderRadius: 10, flexShrink: 0, background: SEVERITY_GLOW[sev], border: `1px solid ${borderColor}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>
                      {eventIcon}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6, marginBottom: 5 }}>
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${SEVERITY_BADGE[sev] || SEVERITY_BADGE.medium}`}>{sev.toUpperCase()}</span>
                        <span style={{ fontSize: 11, padding: '2px 7px', borderRadius: 20, background: 'rgba(99,102,241,0.1)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.2)' }}>
                          {(alert.alert_type || '').replace(/_/g, ' ')}
                        </span>
                        {alert.contract_id && (
                          <span style={{ fontSize: 11, padding: '2px 7px', borderRadius: 20, background: 'rgba(6,182,212,0.08)', color: '#67e8f9', border: '1px solid rgba(6,182,212,0.15)' }}>
                            📄 {alert.contract_id.slice(0, 8)}…
                          </span>
                        )}
                        <span style={{ marginLeft: 'auto', color: '#4b5563', fontSize: 10, whiteSpace: 'nowrap' }}>
                          {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : ''}
                        </span>
                      </div>
                      {alert.headline && <p style={{ color: '#f3f4f6', fontWeight: 600, fontSize: 13, marginBottom: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{alert.headline}</p>}
                      <p style={{ color: '#9ca3af', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{alert.message}</p>
                    </div>
                    {/* Expand chevron */}
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleExpand(alert.id); }}
                      style={{ color: '#6b7280', fontSize: 11, padding: '6px', background: 'none', border: 'none', cursor: 'pointer', flexShrink: 0, transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
                    >▼</button>
                  </div>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div style={{ borderTop: '1px solid rgba(99,102,241,0.08)', padding: '12px 14px 14px' }}>
                      <p style={{ color: '#9ca3af', fontSize: 12, lineHeight: 1.6, marginBottom: 10 }}>{alert.message}</p>
                      {reasoning && (
                        <div style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.14)', borderRadius: 9, padding: '10px 12px', marginBottom: 10 }}>
                          <p style={{ color: '#a5b4fc', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>🤖 AI Reasoning</p>
                          <p style={{ color: '#9ca3af', fontSize: 11, lineHeight: 1.6, marginBottom: 8 }}>{reasoning.reasoning}</p>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                            {reasoning.clauses.map((c, i) => (
                              <span key={i} style={{ fontSize: 10, padding: '2px 6px', borderRadius: 5, background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)', color: '#c4b5fd' }}>{c}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: '#4b5563', fontSize: 10 }}>{alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}</span>
                        <button onClick={() => setSelectedAlert(alert)} style={{ fontSize: 11, padding: '5px 11px', borderRadius: 7, background: 'linear-gradient(135deg, rgba(124,58,237,0.18), rgba(6,182,212,0.18))', border: '1px solid rgba(99,102,241,0.28)', color: '#a5b4fc', cursor: 'pointer' }}>
                          View Full Details →
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Alert Detail Modal */}
      {selectedAlert && <AlertDetailModal alert={selectedAlert} onClose={() => setSelectedAlert(null)} />}
    </div>
  );
};

// ─── Tab 3: RL Learning System ────────────────────────────────────

// Confidence bar with animation
const ConfidenceBar = ({ value, color = '#06b6d4', label }) => {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="w-full">
      {label && <div className="flex justify-between text-xs mb-1"><span className="text-gray-500">{label}</span><span style={{ color }}>{pct}%</span></div>}
      <div className="w-full h-1.5 rounded-full" style={{ background: 'rgba(99,102,241,0.12)' }}>
        <div
          className="h-1.5 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}88, ${color})`, boxShadow: `0 0 8px ${color}66` }}
        />
      </div>
    </div>
  );
};

const RLTab = () => {
  // Form state
  const [contractId, setContractId] = useState('');
  const [action, setAction] = useState('accept_redline');
  const [profit, setProfit] = useState(10);
  const [dispute, setDispute] = useState(false);
  const [delayDays, setDelayDays] = useState(0);
  // State fields
  const [riskBucket, setRiskBucket] = useState('medium');
  const [clauseCategory, setClauseCategory] = useState('general');
  const [region, setRegion] = useState('global');
  const [supplierRiskScore, setSupplierRiskScore] = useState(0.5);
  // UI state
  const [loading, setLoading] = useState(false);
  const [lastReward, setLastReward] = useState(null);
  const [experiences, setExperiences] = useState([]);
  const [insights, setInsights] = useState(null);
  const [error, setError] = useState('');
  // Recommendation
  const [recommendation, setRecommendation] = useState(null);
  const [recLoading, setRecLoading] = useState(false);
  // Filters for experience table
  const [filterAction, setFilterAction] = useState('all');
  const [filterOutcome, setFilterOutcome] = useState('all');

  const loadData = useCallback(async () => {
    try {
      const [expData, insData] = await Promise.all([getRLExperiences(), getRLInsights()]);
      setExperiences(expData.experiences || []);
      setInsights(insData);
    } catch {
      // silently fail
    }
  }, []);

  const fetchRecommendation = useCallback(async (rb, cc, rg) => {
    setRecLoading(true);
    try {
      const data = await getRLRecommendation({ riskBucket: rb, clauseCategory: cc, region: rg });
      setRecommendation(data);
    } catch {
      // silently fail
    } finally {
      setRecLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Refresh recommendation whenever state inputs change
  useEffect(() => {
    fetchRecommendation(riskBucket, clauseCategory, region);
  }, [riskBucket, clauseCategory, region, fetchRecommendation]);

  const handleRecord = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await recordOutcome({
        contractId, action, profit, dispute, delayDays,
        riskBucket, clauseCategory, region, supplierRiskScore,
      });
      setLastReward(data);
      await loadData();
      // Refresh recommendation post-record
      fetchRecommendation(riskBucket, clauseCategory, region);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to record outcome.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = insights?.action_stats
    ? Object.entries(insights.action_stats).map(([act, stats]) => ({
        name: act.replace(/_/g, ' '),
        avgReward: stats.avg_reward,
        count: stats.count,
      }))
    : [];

  const rewardTrend = insights?.reward_trend || [];
  const exploration = insights?.exploration || {};

  const filteredExperiences = useMemo(() => {
    return experiences.filter((exp) => {
      if (filterAction !== 'all' && exp.action !== filterAction) return false;
      if (filterOutcome === 'dispute' && !exp.dispute) return false;
      if (filterOutcome === 'no_dispute' && exp.dispute) return false;
      if (filterOutcome === 'positive' && exp.reward <= 0) return false;
      if (filterOutcome === 'negative' && exp.reward > 0) return false;
      return true;
    });
  }, [experiences, filterAction, filterOutcome]);

  const isExploring = recommendation?.mode === 'explore';

  return (
    <div className="space-y-5">

      {/* ── Recommendation Banner ── */}
      <div className="rounded-2xl p-5" style={{
        background: isExploring
          ? 'linear-gradient(135deg, rgba(168,85,247,0.1), rgba(6,182,212,0.08))'
          : 'linear-gradient(135deg, rgba(6,182,212,0.1), rgba(16,185,129,0.08))',
        border: `1px solid ${isExploring ? 'rgba(168,85,247,0.35)' : 'rgba(6,182,212,0.35)'}`,
        animation: isExploring ? 'exploreGlow 2.5s ease-in-out infinite' : 'pulseGlow 3s ease-in-out infinite',
      }}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">{isExploring ? '🔬' : '🤖'}</span>
            <span className="text-sm font-bold text-white uppercase tracking-widest">
              {isExploring ? 'Exploration Mode Active' : 'AI Recommendation'}
            </span>
            {isExploring && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ background: 'rgba(168,85,247,0.2)', color: '#c4b5fd', border: '1px solid rgba(168,85,247,0.3)' }}>
                ε-greedy: 20% explore
              </span>
            )}
          </div>
          {recLoading && <span className="w-4 h-4 border-2 border-cyan-400/40 border-t-cyan-400 rounded-full animate-spin" />}
        </div>

        {recommendation ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-gray-500 mb-1">Recommended Action</p>
              <p className="text-xl font-black" style={{ color: ACTION_COLOR_MAP[recommendation.recommended_action] || '#06b6d4', textShadow: `0 0 20px ${ACTION_COLOR_MAP[recommendation.recommended_action] || '#06b6d4'}88` }}>
                {recommendation.recommended_action?.replace(/_/g, ' ').toUpperCase()}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                State: <span className="text-gray-300">{recommendation.state_key}</span>
              </p>
            </div>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">Confidence</span>
                  <span className="text-cyan-400">{Math.round((recommendation.confidence || 0) * 100)}%</span>
                </div>
                <ConfidenceBar value={recommendation.confidence} color="#06b6d4" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Expected Reward</p>
                <p className={`text-lg font-bold ${(recommendation.expected_reward || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {(recommendation.expected_reward || 0) > 0 ? '+' : ''}{recommendation.expected_reward ?? 0}
                </p>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-2">Action Comparison</p>
              <div className="space-y-1.5">
                {(recommendation.alternatives || []).slice(0, 3).map((alt) => (
                  <div key={alt.action} className="flex items-center justify-between text-xs">
                    <span className={alt.is_best ? 'text-white font-semibold' : 'text-gray-400'}>
                      {alt.is_best ? '★ ' : ''}{alt.action.replace(/_/g, ' ')}
                    </span>
                    <span className={alt.expected_reward >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                      {alt.expected_reward > 0 ? '+' : ''}{alt.expected_reward}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500">Set contract context below to get an AI-driven action recommendation.</p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Record Form */}
        <Card>
          <SectionHeader title="Record Contract Outcome" subtitle="Log real outcomes — the RL reward function learns which actions maximize profit." icon="🎯" />

          {/* State fields */}
          <div className="mb-3 p-3 rounded-xl" style={{ background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.12)' }}>
            <p className="text-xs text-gray-500 mb-2 font-semibold uppercase tracking-wider">Contract State (for Q-learning)</p>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Risk Bucket</label>
                <StyledSelect value={riskBucket} onChange={(e) => setRiskBucket(e.target.value)}>
                  {RISK_BUCKET_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </StyledSelect>
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Clause Category</label>
                <StyledSelect value={clauseCategory} onChange={(e) => setClauseCategory(e.target.value)}>
                  {CLAUSE_CATEGORY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </StyledSelect>
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Region</label>
                <StyledInput
                  type="text"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  placeholder="e.g. US, EU, APAC"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Supplier Risk (0–1)</label>
                <StyledInput
                  type="number"
                  min="0" max="1" step="0.1"
                  value={supplierRiskScore}
                  onChange={(e) => setSupplierRiskScore(Number(e.target.value))}
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract ID (optional)</label>
              <StyledInput type="text" value={contractId} onChange={(e) => setContractId(e.target.value)} placeholder="Paste contract UUID" />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Action Taken</label>
              <StyledSelect value={action} onChange={(e) => setAction(e.target.value)}>
                {ACTION_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
              </StyledSelect>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Profit / Margin Score</label>
              <StyledInput type="number" value={profit} onChange={(e) => setProfit(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Delay Days</label>
              <StyledInput type="number" min="0" value={delayDays} onChange={(e) => setDelayDays(Number(e.target.value))} />
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer mb-4 p-3 rounded-xl" style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.1)' }}>
            <input type="checkbox" checked={dispute} onChange={(e) => setDispute(e.target.checked)} className="w-4 h-4 rounded accent-red-500" />
            <span className="text-sm text-gray-300">Dispute occurred <span className="text-red-400 text-xs">(−50 reward penalty)</span></span>
          </label>

          <div className="text-xs text-gray-500 mb-4 p-3 rounded-xl" style={{ background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.1)' }}>
            Reward formula: <code className="text-cyan-400">profit × 0.5 − (50 if dispute) − delay_days × 2</code>
          </div>

          {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
          <Button onClick={handleRecord} loading={loading}>
            🎯 {loading ? 'Recording…' : 'Record & Update Q-Table'}
          </Button>
        </Card>

        {/* Reward Panel + Exploration Stats */}
        <div className="flex flex-col gap-4">
          {lastReward ? (
            <div className="rounded-2xl p-6" style={{
              background: 'linear-gradient(135deg, rgba(6,182,212,0.08), rgba(124,58,237,0.08))',
              border: '1px solid rgba(6,182,212,0.25)',
              boxShadow: '0 0 30px rgba(6,182,212,0.1)',
              animation: 'rewardPop 0.4s ease-out',
            }}>
              <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-widest">Reward Score</p>
              <div className="flex items-end gap-3 mb-4">
                <div className="text-5xl font-black" style={{
                  color: (lastReward.reward || 0) >= 0 ? '#22d3ee' : '#f87171',
                  textShadow: (lastReward.reward || 0) >= 0 ? '0 0 30px rgba(6,182,212,0.8)' : '0 0 30px rgba(248,113,113,0.8)',
                  animation: 'rewardPop 0.5s ease-out',
                }}>
                  {lastReward.reward > 0 ? '+' : ''}{lastReward.reward}
                </div>
                <div className="text-gray-400 text-sm pb-2">points</div>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="text-xs px-3 py-1.5 rounded-full" style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)', color: '#6ee7b7' }}>
                  💰 Profit +{lastReward.reward_breakdown?.profit_component}
                </span>
                <span className="text-xs px-3 py-1.5 rounded-full" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}>
                  ⚠️ Dispute {lastReward.reward_breakdown?.dispute_penalty}
                </span>
                <span className="text-xs px-3 py-1.5 rounded-full" style={{ background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.2)', color: '#fde047' }}>
                  ⏱ Delay {lastReward.reward_breakdown?.delay_penalty}
                </span>
              </div>
              {lastReward.q_update && (
                <div className="text-xs p-2 rounded-lg" style={{ background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.15)' }}>
                  <span className="text-gray-500">Q-update: </span>
                  <span className="text-indigo-300">{lastReward.q_update.state_key}</span>
                  <span className="text-gray-500"> → </span>
                  <span className="text-cyan-300">{lastReward.q_update.updated_action?.replace(/_/g, ' ')}</span>
                  <span className="text-gray-500"> = </span>
                  <span className="text-emerald-400">{lastReward.q_update.new_q_value}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)', minHeight: 180 }}>
              <div className="text-center text-gray-600">
                <div className="text-4xl mb-2 opacity-30">🤖</div>
                <p className="text-sm">Submit an outcome to see reward score</p>
              </div>
            </div>
          )}

          {/* Exploration vs Exploitation */}
          {insights && (
            <div className="rounded-2xl p-4" style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.15)' }}>
              <p className="text-xs text-gray-500 mb-3 font-semibold uppercase tracking-wider">Explore vs Exploit</p>
              <div className="flex gap-3 mb-3">
                <div className="flex-1 text-center">
                  <div className="text-lg font-bold text-purple-400">{exploration.explore_pct ?? 0}%</div>
                  <div className="text-xs text-gray-500">Exploration</div>
                </div>
                <div className="w-px" style={{ background: 'rgba(99,102,241,0.2)' }} />
                <div className="flex-1 text-center">
                  <div className="text-lg font-bold text-cyan-400">{exploration.exploit_pct ?? 0}%</div>
                  <div className="text-xs text-gray-500">Exploitation</div>
                </div>
                <div className="w-px" style={{ background: 'rgba(99,102,241,0.2)' }} />
                <div className="flex-1 text-center">
                  <div className="text-lg font-bold text-indigo-400">{insights.q_table_states ?? 0}</div>
                  <div className="text-xs text-gray-500">Q-States</div>
                </div>
              </div>
              <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: 'rgba(99,102,241,0.12)' }}>
                <div
                  className="h-2 rounded-full transition-all duration-700"
                  style={{
                    width: `${exploration.exploit_pct ?? 50}%`,
                    background: 'linear-gradient(90deg, #a855f7, #06b6d4)',
                  }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1 text-gray-600">
                <span>← Explore</span>
                <span>Exploit →</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Insights KPIs */}
      {insights && insights.total_experiences > 0 && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPICard label="Total Experiences" value={insights.total_experiences} icon="📚" />
            <KPICard
              label="Avg Reward"
              value={insights.avg_reward > 0 ? `+${insights.avg_reward}` : insights.avg_reward}
              colorClass={insights.avg_reward >= 0 ? 'text-emerald-400' : 'text-red-400'}
              icon="⭐"
            />
            <KPICard label="Best Reward" value={insights.max_reward} colorClass="text-cyan-400" icon="🏆" />
            <KPICard label="Dispute Rate" value={`${insights.dispute_rate}%`} colorClass="text-yellow-400" icon="⚠️" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Reward Trend */}
            {rewardTrend.length > 1 && (
              <Card>
                <h4 className="text-white font-semibold mb-4">Reward Trend Over Time</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={rewardTrend} margin={{ left: -10 }}>
                    <defs>
                      <linearGradient id="rewardGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                    <XAxis dataKey="index" tick={{ fill: '#6b7280', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }}
                      labelStyle={{ color: '#9ca3af' }}
                      formatter={(v, _, props) => [`${v > 0 ? '+' : ''}${v}`, `${props?.payload?.action?.replace(/_/g, ' ') || 'reward'}`]}
                    />
                    <ReferenceLine y={0} stroke="rgba(99,102,241,0.3)" strokeDasharray="4 2" />
                    <Area type="monotone" dataKey="reward" stroke="#06b6d4" strokeWidth={2} fill="url(#rewardGrad)" dot={{ r: 3, fill: '#06b6d4' }} />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>
            )}

            {/* Avg Reward by Action */}
            {chartData.length > 0 && (
              <Card>
                <h4 className="text-white font-semibold mb-4">Action Success Rate</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData} margin={{ left: -10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                    <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 9 }} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }}
                      labelStyle={{ color: '#9ca3af' }}
                    />
                    <Bar dataKey="avgReward" name="Avg Reward" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry) => (
                        <Cell key={entry.name} fill={ACTION_COLOR_MAP[entry.name.replace(/ /g, '_')] || '#06b6d4'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            )}
          </div>
        </>
      )}

      {/* Experience History with Filters */}
      {experiences.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <h4 className="text-white font-semibold">
              Experience History <span className="text-gray-500 font-normal">({filteredExperiences.length} / {experiences.length})</span>
            </h4>
            <div className="flex gap-2">
              <StyledSelect value={filterAction} onChange={(e) => setFilterAction(e.target.value)} className="text-xs py-1 px-2" style={{ minWidth: 130 }}>
                <option value="all">All Actions</option>
                {ACTION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </StyledSelect>
              <StyledSelect value={filterOutcome} onChange={(e) => setFilterOutcome(e.target.value)} className="text-xs py-1 px-2" style={{ minWidth: 130 }}>
                <option value="all">All Outcomes</option>
                <option value="positive">Positive Reward</option>
                <option value="negative">Negative Reward</option>
                <option value="dispute">With Dispute</option>
                <option value="no_dispute">No Dispute</option>
              </StyledSelect>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
                  <th className="text-left py-2 pr-3 text-gray-500 font-medium">Contract</th>
                  <th className="text-left py-2 pr-3 text-gray-500 font-medium">Action</th>
                  <th className="text-left py-2 pr-3 text-gray-500 font-medium">State</th>
                  <th className="text-right py-2 pr-3 text-gray-500 font-medium">Profit</th>
                  <th className="text-center py-2 pr-3 text-gray-500 font-medium">Dispute</th>
                  <th className="text-right py-2 pr-3 text-gray-500 font-medium">Delay</th>
                  <th className="text-right py-2 pr-3 text-gray-500 font-medium">Reward</th>
                  <th className="text-right py-2 text-gray-500 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {filteredExperiences.slice(0, 20).map((exp) => (
                  <tr key={exp.id} className="border-b transition-colors" style={{ borderColor: 'rgba(99,102,241,0.05)' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <td className="py-2 pr-3 text-gray-400">{exp.contract_id ? exp.contract_id.slice(0, 8) + '…' : '—'}</td>
                    <td className="py-2 pr-3">
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ background: `${ACTION_COLOR_MAP[exp.action] || '#6b7280'}22`, color: ACTION_COLOR_MAP[exp.action] || '#9ca3af', border: `1px solid ${ACTION_COLOR_MAP[exp.action] || '#6b7280'}44` }}>
                        {exp.action.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-gray-500">{exp.state?.risk_bucket || '—'} / {exp.state?.clause_category?.replace(/_/g, ' ') || '—'}</td>
                    <td className="py-2 pr-3 text-right text-gray-300">{exp.profit}</td>
                    <td className="py-2 pr-3 text-center">
                      {exp.dispute ? <span className="text-red-400">Yes</span> : <span className="text-emerald-400">No</span>}
                    </td>
                    <td className="py-2 pr-3 text-right text-gray-400">{exp.delay_days}d</td>
                    <td className={`py-2 pr-3 text-right font-bold ${exp.reward >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {exp.reward > 0 ? '+' : ''}{exp.reward}
                    </td>
                    <td className="py-2 text-right text-gray-600">
                      {exp.created_at ? new Date(exp.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Train Model Section */}
      <RLTrainSection />

      {/* RLHF Expert Feedback Section */}
      <RLHFSection />
    </div>
  );
};

// ─── RL Train Model ────────────────────────────────────────────────

const RLTrainSection = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleTrain = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await trainRLModel();
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.message || err?.response?.data?.error || 'Training failed.');
    } finally {
      setLoading(false);
    }
  };

  const stats = result?.training_stats || {};
  const converged = stats.converged;

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h4 className="text-white font-bold flex items-center gap-2">
            🧬 Batch Q-Learning: Train Policy
          </h4>
          <p className="text-gray-500 text-xs mt-0.5">
            Rebuilds Q-table from all experiences + RLHF adjustments. Updates recommendation engine.
          </p>
        </div>
        <Button onClick={handleTrain} loading={loading} variant="primary">
          {loading ? 'Training…' : '🚀 Train Model'}
        </Button>
      </div>
      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
      {result && (
        <div className="space-y-4" style={{ animation: 'fadeInUp 0.35s ease-out' }}>
          {result.status === 'insufficient_data' ? (
            <div className="p-4 rounded-xl text-yellow-400 text-sm" style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.2)' }}>
              ⚠️ {result.message}
            </div>
          ) : (
            <>
              {/* Status banner */}
              <div className="p-3 rounded-xl flex items-center gap-3" style={{
                background: converged ? 'rgba(16,185,129,0.06)' : 'rgba(6,182,212,0.06)',
                border: `1px solid ${converged ? 'rgba(16,185,129,0.2)' : 'rgba(6,182,212,0.2)'}`,
              }}>
                <span className="text-lg">{converged ? '✅' : '📈'}</span>
                <div>
                  <p className={`text-sm font-medium ${converged ? 'text-emerald-400' : 'text-cyan-400'}`}>{result.message}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Trained at {result.trained_at ? new Date(result.trained_at).toLocaleTimeString() : '—'} · Q-states: {stats.q_table_states ?? 0} · σ(Q): {stats.q_std ?? '—'}
                  </p>
                </div>
                {converged && (
                  <span className="ml-auto text-xs px-2 py-1 rounded-full font-semibold" style={{ background: 'rgba(16,185,129,0.15)', color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.3)' }}>
                    Converged ✓
                  </span>
                )}
              </div>

              {/* KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <KPICard label="Experiences" value={stats.total_experiences} icon="📚" colorClass="text-cyan-400" />
                <KPICard label="Avg Reward" value={stats.avg_reward >= 0 ? `+${stats.avg_reward}` : stats.avg_reward} colorClass={stats.avg_reward >= 0 ? 'text-emerald-400' : 'text-red-400'} icon="⭐" />
                <KPICard label="Dispute Rate" value={`${stats.dispute_rate}%`} colorClass="text-yellow-400" icon="⚠️" />
                <KPICard label="RLHF Applied" value={stats.rlhf_feedback_incorporated} colorClass="text-purple-400" icon="🧑‍⚖️" />
              </div>

              {/* Best action glowing highlight */}
              {result.best_action && (
                <div className="p-4 rounded-xl" style={{
                  background: `linear-gradient(135deg, ${ACTION_COLOR_MAP[result.best_action] || '#06b6d4'}12, rgba(124,58,237,0.08))`,
                  border: `1px solid ${ACTION_COLOR_MAP[result.best_action] || '#06b6d4'}44`,
                  boxShadow: `0 0 20px ${ACTION_COLOR_MAP[result.best_action] || '#06b6d4'}22`,
                }}>
                  <p className="text-xs text-gray-400 mb-1 uppercase tracking-widest">Best Action (RLHF-adjusted)</p>
                  <p className="text-2xl font-black" style={{ color: ACTION_COLOR_MAP[result.best_action] || '#06b6d4', textShadow: `0 0 20px ${ACTION_COLOR_MAP[result.best_action] || '#06b6d4'}88` }}>
                    {result.best_action.replace(/_/g, ' ').toUpperCase()}
                  </p>
                  <p className="text-gray-500 text-xs mt-1">Highest RLHF-adjusted Q-score from your data</p>
                </div>
              )}

              {/* Policy table with confidence bars */}
              {result.policy && result.policy.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">Learned Policy Table</p>
                  {result.policy.map((p) => (
                    <div
                      key={p.action}
                      className="rounded-xl p-3 transition-all duration-200"
                      style={{
                        background: p.recommended
                          ? `linear-gradient(135deg, ${ACTION_COLOR_MAP[p.action] || '#06b6d4'}10, rgba(13,17,23,0.9))`
                          : 'rgba(13,17,23,0.6)',
                        border: p.recommended
                          ? `1px solid ${ACTION_COLOR_MAP[p.action] || '#06b6d4'}44`
                          : '1px solid rgba(99,102,241,0.08)',
                        boxShadow: p.recommended ? `0 0 16px ${ACTION_COLOR_MAP[p.action] || '#06b6d4'}18` : 'none',
                      }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold" style={{ color: p.recommended ? (ACTION_COLOR_MAP[p.action] || '#06b6d4') : '#9ca3af' }}>
                            {p.recommended ? '★ ' : ''}{p.action.replace(/_/g, ' ').toUpperCase()}
                          </span>
                          {p.recommended && (
                            <span className="text-xs px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(16,185,129,0.15)', color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.25)' }}>
                              Best
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs">
                          <span className="text-gray-500">{p.sample_count} samples</span>
                          <span className={p.rlhf_adjusted_score >= 0 ? 'text-cyan-400 font-bold' : 'text-red-400 font-bold'}>
                            {p.rlhf_adjusted_score > 0 ? '+' : ''}{p.rlhf_adjusted_score}
                          </span>
                          {p.rlhf_feedback_count > 0 && (
                            <span className="text-purple-400 text-xs">+{p.rlhf_feedback_count} feedback</span>
                          )}
                        </div>
                      </div>
                      <ConfidenceBar
                        value={p.confidence}
                        color={ACTION_COLOR_MAP[p.action] || '#6b7280'}
                        label={`Confidence`}
                      />
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </Card>
  );
};

// ─── RLHF Expert Feedback ──────────────────────────────────────────

const RLHFSection = () => {
  const [actionType, setActionType] = useState('accept_redline');
  const [rating, setRating] = useState(3);
  const [comment, setComment] = useState('');
  const [expertName, setExpertName] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [feedbackHistory, setFeedbackHistory] = useState([]);
  const [actionSummary, setActionSummary] = useState({});
  const [error, setError] = useState('');

  const loadHistory = useCallback(async () => {
    try {
      const data = await getRLHFFeedback();
      setFeedbackHistory(data.feedback || []);
      setActionSummary(data.action_summary || {});
    } catch {
      // silently fail
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const handleSubmit = async () => {
    if (!actionType) { setError('Select an action type.'); return; }
    setLoading(true);
    setError('');
    try {
      await submitRLHFFeedback({ actionType, rating, comment, expertName });
      setSubmitted(true);
      setComment('');
      await loadHistory();
      setTimeout(() => setSubmitted(false), 3000);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to submit feedback.');
    } finally {
      setLoading(false);
    }
  };

  // Preview: how this rating will shift the Q-value
  const ratingShift = ((rating - 3) * 0.15).toFixed(2);
  const shiftPositive = ratingShift > 0;

  const StarRating = ({ value, onChange }) => (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => onChange(star)}
          className={`text-2xl transition-all hover:scale-110 ${star <= value ? 'text-yellow-400' : 'text-gray-700 hover:text-gray-500'}`}
        >
          ★
        </button>
      ))}
    </div>
  );

  return (
    <Card>
      <SectionHeader
        title="Expert Feedback (RLHF)"
        subtitle="Rate AI actions to adjust Q-values and improve recommendations over time."
        icon="🧑‍🏫"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Feedback form */}
        <div>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Action Type</label>
              <StyledSelect value={actionType} onChange={(e) => setActionType(e.target.value)}>
                {ACTION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </StyledSelect>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Expert Name (optional)</label>
              <StyledInput
                type="text"
                value={expertName}
                onChange={(e) => setExpertName(e.target.value)}
                placeholder="Your name"
              />
            </div>
          </div>

          <div className="mb-3">
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Rating</label>
            <StarRating value={rating} onChange={setRating} />
          </div>

          {/* Live Q-shift preview */}
          <div className="mb-3 p-2.5 rounded-xl text-xs" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.12)' }}>
            <span className="text-gray-500">Q-value shift preview: </span>
            <span className={shiftPositive ? 'text-emerald-400 font-bold' : ratingShift < 0 ? 'text-red-400 font-bold' : 'text-gray-400'}>
              {shiftPositive ? '+' : ''}{ratingShift}
            </span>
            <span className="text-gray-500"> applied to </span>
            <span style={{ color: ACTION_COLOR_MAP[actionType] || '#9ca3af' }}>{actionType.replace(/_/g, ' ')}</span>
            <span className="text-gray-500"> Q-values across all states</span>
          </div>

          <div className="mb-4">
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Comment (optional)</label>
            <StyledTextarea
              rows={2}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Why did this action work well or poorly?"
            />
          </div>

          {error && <p className="text-red-400 text-xs mb-2">{error}</p>}
          {submitted && (
            <div className="text-emerald-400 text-xs mb-2 flex items-center gap-1" style={{ animation: 'fadeInUp 0.3s ease-out' }}>
              ✓ Feedback recorded — will be applied on next Train Model run
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-white flex items-center gap-2 transition-all disabled:opacity-50 hover:scale-[1.02]"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 16px rgba(6,182,212,0.2)' }}
          >
            {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
            Submit Expert Feedback
          </button>
        </div>

        {/* Action feedback summary */}
        <div>
          {Object.keys(actionSummary).length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-2 font-semibold uppercase tracking-wider">Feedback Impact by Action</p>
              <div className="space-y-2">
                {Object.entries(actionSummary).map(([act, s]) => {
                  const avgRating = s.avg_rating || 3;
                  const shift = ((avgRating - 3) * 0.15).toFixed(2);
                  const positive = shift > 0;
                  return (
                    <div key={act} className="flex items-center gap-3 text-xs p-2.5 rounded-xl" style={{ background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.1)' }}>
                      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: ACTION_COLOR_MAP[act] || '#6b7280' }} />
                      <span className="text-gray-300 flex-1">{act.replace(/_/g, ' ')}</span>
                      <span className="text-yellow-400">{'★'.repeat(Math.round(avgRating))}{'☆'.repeat(5 - Math.round(avgRating))}</span>
                      <span className={`font-bold w-10 text-right ${positive ? 'text-emerald-400' : shift < 0 ? 'text-red-400' : 'text-gray-500'}`}>
                        {positive ? '+' : ''}{shift}
                      </span>
                      <span className="text-gray-600">{s.count}×</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {feedbackHistory.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-gray-500 mb-2">Recent Feedback ({feedbackHistory.length})</p>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {feedbackHistory.slice(0, 8).map((fb) => (
                  <div key={fb.id} className="flex items-center gap-3 text-xs px-3 py-2 rounded-lg" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.08)' }}>
                    <span className="text-yellow-400 flex-shrink-0">{'★'.repeat(fb.rating)}</span>
                    <span style={{ color: ACTION_COLOR_MAP[fb.action_type] || '#9ca3af' }}>{fb.action_type.replace(/_/g, ' ')}</span>
                    {fb.expert_name && fb.expert_name !== 'Anonymous Expert' && (
                      <span className="text-gray-600 text-xs">— {fb.expert_name}</span>
                    )}
                    {fb.comment && <span className="text-gray-500 truncate flex-1">{fb.comment}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

// ─── Benchmarking helpers + Tab 4 ────────────────────────────────

const BENCH_EXTRA_STYLES = `
  @keyframes insightSlide {
    from { opacity: 0; transform: translateX(-12px); }
    to { opacity: 1; transform: translateX(0); }
  }
  @keyframes scoreRing {
    from { stroke-dashoffset: 283; }
    to { stroke-dashoffset: var(--ring-offset); }
  }
  @keyframes recPop {
    0% { opacity: 0; transform: scale(0.95) translateY(6px); }
    100% { opacity: 1; transform: scale(1) translateY(0); }
  }
`;
if (typeof document !== 'undefined' && !document.getElementById('bench-extra-styles')) {
  const s = document.createElement('style');
  s.id = 'bench-extra-styles';
  s.textContent = BENCH_EXTRA_STYLES;
  document.head.appendChild(s);
}

const SEV_CONFIG = {
  critical: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.35)', text: '#f87171', badge: 'bg-red-600', icon: '🚨' },
  high:     { bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.35)', text: '#fb923c', badge: 'bg-orange-500', icon: '⚠️' },
  medium:   { bg: 'rgba(234,179,8,0.06)',  border: 'rgba(234,179,8,0.25)',  text: '#fbbf24', badge: 'bg-yellow-600', icon: '💡' },
  low:      { bg: 'rgba(16,185,129,0.06)', border: 'rgba(16,185,129,0.25)', text: '#34d399', badge: 'bg-emerald-600', icon: '✅' },
};

const PRIORITY_CONFIG = {
  critical: { color: '#f87171', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)', label: 'CRITICAL' },
  high:     { color: '#fb923c', bg: 'rgba(249,115,22,0.1)', border: 'rgba(249,115,22,0.3)', label: 'HIGH' },
  medium:   { color: '#fbbf24', bg: 'rgba(234,179,8,0.08)', border: 'rgba(234,179,8,0.2)',  label: 'MEDIUM' },
  low:      { color: '#34d399', bg: 'rgba(16,185,129,0.06)', border: 'rgba(16,185,129,0.2)', label: 'LOW' },
};

const STATUS_CONFIG = {
  high:    { color: '#f87171', bg: 'rgba(239,68,68,0.12)',   label: 'HIGH RISK' },
  medium:  { color: '#fbbf24', bg: 'rgba(234,179,8,0.1)',    label: 'IN RANGE' },
  low:     { color: '#34d399', bg: 'rgba(16,185,129,0.1)',   label: 'LOW RISK' },
  missing: { color: '#6b7280', bg: 'rgba(107,114,128,0.1)',  label: 'MISSING' },
};

const HealthRing = ({ score }) => {
  const r = 45;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 75 ? '#10b981' : score >= 55 ? '#f59e0b' : '#ef4444';
  return (
    <svg width="120" height="120" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(99,102,241,0.1)" strokeWidth="10" />
      <circle
        cx="60" cy="60" r={r} fill="none"
        stroke={color} strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        transform="rotate(-90 60 60)"
        style={{ transition: 'stroke-dashoffset 1.2s ease' }}
      />
      <text x="60" y="55" textAnchor="middle" fill={color} fontSize="20" fontWeight="bold">{score}</text>
      <text x="60" y="72" textAnchor="middle" fill="#6b7280" fontSize="9">HEALTH</text>
    </svg>
  );
};

const PercentileBar = ({ pctDiff, position }) => {
  // Map position on 0-100 scale: industry median = 50
  const rawScore = position === 'above' ? Math.max(0, 50 - Math.abs(pctDiff) * 0.6) : Math.min(100, 50 + Math.abs(pctDiff) * 0.6);
  const pctScore = Math.round(rawScore);
  const betterThan = pctScore;
  const color = pctScore >= 60 ? '#10b981' : pctScore >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Bottom</span><span>Industry Median</span><span>Top</span>
      </div>
      <div className="relative h-3 rounded-full overflow-hidden" style={{ background: 'rgba(99,102,241,0.1)' }}>
        <div
          className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${pctScore}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }}
        />
        <div className="absolute top-0 left-1/2 h-full w-px" style={{ background: 'rgba(6,182,212,0.6)' }} />
      </div>
      <p className="text-center text-xs font-semibold" style={{ color }}>
        Top {100 - betterThan}% — Better than {betterThan}% of industry peers
      </p>
    </div>
  );
};

// ─── ContractSelector sub-component ──────────────────────────────

const RISK_DOT = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981', UNKNOWN: '#6b7280' };

const ContractSelector = ({ contracts, selectedId, onSelect, mode, onModeChange, compareIds, onCompareToggle }) => {
  const sorted = [...contracts].sort((a, b) => (b.has_risk_data ? 1 : 0) - (a.has_risk_data ? 1 : 0));
  return (
    <div className="p-4 rounded-2xl space-y-3" style={{ background: 'rgba(13,17,23,0.85)', border: '1px solid rgba(99,102,241,0.18)' }}>
      {/* Mode switcher */}
      <div className="flex gap-1.5">
        {[['portfolio','🗂 Portfolio'],['single','📄 Single'],['compare','⚖️ Compare']].map(([m, label]) => (
          <button key={m} onClick={() => onModeChange(m)}
            className="px-3 py-1.5 text-xs rounded-xl font-medium transition-all"
            style={mode === m
              ? { background: 'linear-gradient(135deg,rgba(124,58,237,0.35),rgba(6,182,212,0.25))', color: '#e2e8f0', border: '1px solid rgba(124,58,237,0.5)' }
              : { background: 'transparent', color: '#6b7280', border: '1px solid rgba(99,102,241,0.12)' }}>
            {label}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-600 self-center">{contracts.length} contract{contracts.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Single mode selector */}
      {mode === 'single' && (
        <select
          value={selectedId || ''}
          onChange={e => onSelect(e.target.value)}
          className="w-full text-xs rounded-xl px-3 py-2 outline-none"
          style={{ background: 'rgba(13,17,23,0.9)', border: '1px solid rgba(99,102,241,0.2)', color: '#e2e8f0' }}>
          <option value="">— Select a contract —</option>
          {sorted.map(c => (
            <option key={c.id} value={c.id}>
              {c.name.length > 55 ? c.name.slice(0,52)+'…' : c.name}
              {c.has_risk_data ? ` [${c.risk_level}]` : ' [no risk data]'}
            </option>
          ))}
        </select>
      )}

      {/* Compare mode chips */}
      {mode === 'compare' && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500">Select 2–4 contracts to compare</p>
          <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto">
            {sorted.filter(c => c.has_risk_data).map(c => {
              const selected = compareIds.includes(c.id);
              return (
                <button key={c.id} onClick={() => onCompareToggle(c.id)}
                  className="px-2.5 py-1 text-xs rounded-lg transition-all font-medium flex items-center gap-1.5"
                  style={selected
                    ? { background: 'rgba(124,58,237,0.25)', border: '1px solid rgba(124,58,237,0.5)', color: '#a78bfa' }
                    : { background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.1)', color: '#6b7280' }}>
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: RISK_DOT[c.risk_level] || '#6b7280' }} />
                  {c.name.length > 30 ? c.name.slice(0,28)+'…' : c.name}
                  {selected && ' ✓'}
                </button>
              );
            })}
          </div>
          {compareIds.length > 0 && (
            <p className="text-xs text-purple-400">{compareIds.length} selected — scroll down to see comparison</p>
          )}
        </div>
      )}

      {/* Selected contract info */}
      {mode === 'single' && selectedId && contracts.find(c => c.id === selectedId) && (() => {
        const c = contracts.find(x => x.id === selectedId);
        return (
          <div className="flex flex-wrap gap-3 text-xs">
            {c.party_a && <span className="text-gray-400">Party A: <span className="text-gray-200">{c.party_a}</span></span>}
            {c.party_b && <span className="text-gray-400">Party B: <span className="text-gray-200">{c.party_b}</span></span>}
            {c.contract_type && <span className="text-gray-400">Type: <span className="text-cyan-300">{c.contract_type}</span></span>}
            {c.clause_count > 0 && <span className="text-gray-400">Clauses: <span className="text-purple-300">{c.clause_count}</span></span>}
            {c.risk_score !== null && (
              <span className="text-gray-400">Risk: <span style={{ color: RISK_DOT[c.risk_level] }}>{Math.round(c.risk_score * 100)}% ({c.risk_level})</span></span>
            )}
            {!c.has_risk_data && <span className="text-yellow-400">⚠️ No risk data — run 'Analyze Risk' on this contract</span>}
          </div>
        );
      })()}
    </div>
  );
};

// ─── ComparePanel ─────────────────────────────────────────────────

const ComparePanel = ({ compareData }) => {
  if (!compareData || compareData.length < 2) return (
    <div className="p-6 rounded-2xl text-center" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }}>
      <p className="text-gray-500 text-sm">Select at least 2 contracts above to see comparison</p>
    </div>
  );
  const maxRisk = Math.max(...compareData.map(c => c.avg_risk));
  return (
    <div className="space-y-3" style={{ animation: 'tabEnter 0.25s ease both' }}>
      <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${Math.min(compareData.length, 4)}, 1fr)` }}>
        {compareData.map((c, i) => (
          <div key={i} className="p-4 rounded-2xl space-y-2" style={{ background: 'rgba(13,17,23,0.85)', border: `1px solid ${RISK_DOT[c.risk_level]}33` }}>
            <p className="text-xs text-gray-400 truncate font-medium" title={c.name}>{c.name.length > 28 ? c.name.slice(0,26)+'…' : c.name}</p>
            <div className="text-2xl font-bold" style={{ color: RISK_DOT[c.risk_level] }}>{Math.round(c.avg_risk * 100)}%</div>
            <p className="text-xs" style={{ color: RISK_DOT[c.risk_level] }}>{c.risk_level} RISK</p>
            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(99,102,241,0.1)' }}>
              <div className="h-full rounded-full transition-all duration-700" style={{ width: `${(c.avg_risk / maxRisk) * 100}%`, background: RISK_DOT[c.risk_level] }} />
            </div>
            <div className="text-xs text-gray-500">{c.clause_count} clauses · {c.high_risk_clauses} high-risk</div>
          </div>
        ))}
      </div>
      <Card>
        <h4 className="text-white font-semibold mb-4 text-sm">Risk Comparison</h4>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={compareData.map(c => ({ name: c.name.slice(0,20), risk: Math.round(c.avg_risk * 100), industry: 42 }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
            <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 9 }} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 9 }} unit="%" />
            <Tooltip contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }} formatter={(v) => [`${v}%`]} />
            <Legend />
            <Bar dataKey="risk" name="Avg Risk %" radius={[4, 4, 0, 0]}>
              {compareData.map((c, i) => <Cell key={i} fill={RISK_DOT[c.risk_level]} />)}
            </Bar>
            <Bar dataKey="industry" name="Industry Median" fill="rgba(99,102,241,0.3)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
};

// ─── DataSourceBadge ─────────────────────────────────────────────

const DataSourceBadge = ({ dataSources }) => {
  if (!dataSources) return null;
  const isClause = dataSources.clause_level_scores > 0;
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs" style={{ background: isClause ? 'rgba(16,185,129,0.08)' : 'rgba(234,179,8,0.08)', border: `1px solid ${isClause ? 'rgba(16,185,129,0.2)' : 'rgba(234,179,8,0.2)'}`, color: isClause ? '#34d399' : '#fbbf24' }}>
      <span>{isClause ? '✅' : '⚠️'}</span>
      <span>
        {isClause
          ? `Real data: ${dataSources.clause_level_scores} clause risk scores`
          : `Contract-level: ${dataSources.contract_level_scores} analysis records`}
      </span>
      <span className="text-gray-600 ml-1">via {dataSources.primary_source?.replace(/_/g,' ')}</span>
    </div>
  );
};

// ─── Tab 4: Industry Benchmarking ────────────────────────────────

const BenchmarkingTab = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [insights, setInsights] = useState(null);
  const [clauses, setClauses] = useState(null);
  const [recs, setRecs] = useState(null);
  const [recsLoading, setRecsLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('insights');

  // Contract selection state
  const [contracts, setContracts] = useState([]);
  const [contractsLoading, setContractsLoading] = useState(false);
  const [viewMode, setViewMode] = useState('portfolio');
  const [selectedContractId, setSelectedContractId] = useState('');
  const [compareIds, setCompareIds] = useState([]);

  // Fetch contract list once
  useEffect(() => {
    const load = async () => {
      setContractsLoading(true);
      try {
        const result = await getBenchmarkingContracts();
        setContracts(result.contracts || []);
      } catch (e) {
        // non-fatal: contract selector degrades gracefully
      } finally {
        setContractsLoading(false);
      }
    };
    load();
  }, []);

  const buildParams = useCallback(() => {
    if (viewMode === 'single' && selectedContractId) {
      return { mode: 'single', contract_id: selectedContractId };
    }
    if (viewMode === 'compare' && compareIds.length >= 2) {
      return { mode: 'compare', compare_ids: compareIds.join(',') };
    }
    return { mode: 'portfolio' };
  }, [viewMode, selectedContractId, compareIds]);

  const loadAll = useCallback(async () => {
    const params = buildParams();
    if (viewMode === 'single' && !selectedContractId) return;
    if (viewMode === 'compare' && compareIds.length < 2) return;
    setLoading(true);
    setError('');
    try {
      const summary = await getIndustryBenchmarking(params);
      setData(summary);
      setInsights({
        insights: summary.ai_insights || [],
        insight_count: summary.insight_count || 0,
        portfolio_health: summary.portfolio_health || 'unknown',
        health_score: summary.health_score || 50,
        critical_issues: summary.critical_issues || 0,
      });
      setClauses({
        clauses: summary.clause_benchmarks || [],
        total_clause_types_found: summary.total_clause_types_found || 0,
        total_clause_types_missing: summary.total_clause_types_missing || 0,
      });
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load benchmarking data.');
    } finally {
      setLoading(false);
    }
  }, [buildParams, viewMode, selectedContractId, compareIds]);

  // Auto-load on mode/selection change
  useEffect(() => {
    if (viewMode === 'portfolio') loadAll();
    else if (viewMode === 'single' && selectedContractId) loadAll();
    else if (viewMode === 'compare' && compareIds.length >= 2) loadAll();
  }, [viewMode, selectedContractId, compareIds.join(',')]); // eslint-disable-line

  const handleModeChange = useCallback((m) => {
    setViewMode(m);
    setData(null);
    setInsights(null);
    setClauses(null);
    setRecs(null);
    setSelectedContractId('');
    setCompareIds([]);
  }, []);

  const handleCompareToggle = useCallback((id) => {
    setCompareIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 4 ? [...prev, id] : prev);
  }, []);

  const handleImproveContract = useCallback(async () => {
    setRecsLoading(true);
    setActiveSection('recommendations');
    try {
      const params = buildParams();
      const d = await getIndustryBenchmarking(params);
      setRecs({
        recommendations: d.recommendations || [],
        total_recommendations: d.total_recommendations || 0,
        critical_count: d.rec_critical_count || 0,
        high_count: d.rec_high_count || 0,
        estimated_risk_reduction: d.estimated_risk_reduction || '~0%',
      });
    } catch (err) {
      setError('Failed to generate recommendations.');
    } finally {
      setRecsLoading(false);
    }
  }, [buildParams]);

  const chartData = data?.benchmarks?.map((b) => ({
    metric: b.metric.replace(' (%)', '').replace(' (Days)', ''),
    Your: b.your_value,
    Industry: b.industry_median,
  })) || [];

  const SECTION_TABS = [
    { id: 'insights', label: '🧠 AI Insights' },
    { id: 'clauses', label: '📋 Clause Analysis' },
    { id: 'volatility', label: '📈 Volatility' },
    { id: 'industry', label: '🏆 Top Clauses' },
    { id: 'recommendations', label: '💡 Recommendations' },
  ];

  return (
    <div className="space-y-5">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-2xl"
        style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.15)' }}>
        <div>
          <h3 className="text-white font-bold text-base">AI-Powered Industry Benchmarking</h3>
          <p className="text-gray-500 text-xs mt-0.5">Decision intelligence engine — comparing your portfolio against 2,400 industry contracts</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleImproveContract}
            disabled={recsLoading || loading}
            className="px-4 py-2 text-xs rounded-xl font-bold transition-all disabled:opacity-50 flex items-center gap-1.5"
            style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(6,182,212,0.2))', border: '1px solid rgba(124,58,237,0.4)', color: '#a78bfa' }}
          >
            {recsLoading ? '⏳ Analyzing…' : '👉 Improve My Contract'}
          </button>
          <button
            onClick={loadAll}
            disabled={loading}
            className="px-4 py-2 text-xs rounded-xl font-medium transition-all disabled:opacity-50"
            style={{ background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.25)', color: '#06b6d4' }}
          >
            {loading ? '⏳' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {/* ── Contract Selector ── */}
      {(contractsLoading || contracts.length > 0) && (
        <ContractSelector
          contracts={contracts}
          selectedId={selectedContractId}
          onSelect={setSelectedContractId}
          mode={viewMode}
          onModeChange={handleModeChange}
          compareIds={compareIds}
          onCompareToggle={handleCompareToggle}
        />
      )}

      {/* ── Compare mode: awaiting selection ── */}
      {viewMode === 'compare' && compareIds.length < 2 && !loading && (
        <div className="p-5 rounded-2xl text-center" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }}>
          <p className="text-gray-400 text-sm">Select at least 2 contracts above to run comparison</p>
        </div>
      )}

      {/* ── Single mode: awaiting selection ── */}
      {viewMode === 'single' && !selectedContractId && !loading && (
        <div className="p-5 rounded-2xl text-center" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }}>
          <p className="text-gray-400 text-sm">Select a contract above to analyse it</p>
        </div>
      )}

      {error && <p className="text-red-400 text-sm px-1">⚠️ {error}</p>}

      {loading && !data && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 rounded-2xl animate-pulse" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }} />
          ))}
        </div>
      )}

      {data && !data.user_stats && data.error && (
        <div className="p-4 rounded-2xl text-yellow-400 text-sm" style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.2)' }}>
          ⚠️ {data.error}
        </div>
      )}

      {/* ── Compare view ── */}
      {viewMode === 'compare' && data?.compare_data?.length >= 2 && (
        <ComparePanel compareData={data.compare_data} />
      )}

      {data && data.user_stats && (
        <>
          {/* ── Data source badge ── */}
          <DataSourceBadge dataSources={data.data_sources} />

          {/* ── Portfolio Score Row ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="col-span-2 md:col-span-1 p-4 rounded-2xl flex flex-col items-center justify-center gap-1"
              style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.15)' }}>
              <HealthRing score={insights?.health_score ?? 50} />
              <p className="text-xs text-gray-400 mt-1">
                {viewMode === 'single' && data.contract_meta?.name
                  ? data.contract_meta.name.slice(0, 22) + (data.contract_meta.name.length > 22 ? '…' : '')
                  : 'Portfolio Health'}
              </p>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{
                background: (insights?.portfolio_health === 'strong') ? 'rgba(16,185,129,0.15)' : (insights?.portfolio_health === 'moderate') ? 'rgba(234,179,8,0.1)' : 'rgba(239,68,68,0.1)',
                color: (insights?.portfolio_health === 'strong') ? '#34d399' : (insights?.portfolio_health === 'moderate') ? '#fbbf24' : '#f87171',
              }}>
                {(insights?.portfolio_health ?? 'unknown').toUpperCase()}
              </span>
            </div>
            <KPICard
              label="Avg Risk Score"
              value={data.user_stats?.avg_risk_score > 0 ? data.user_stats.avg_risk_score : '—'}
              colorClass={(data.user_stats?.avg_risk_score ?? 0) > 0.42 ? 'text-red-400' : 'text-emerald-400'}
              icon="🎯"
            />
            <KPICard label="Industry Median" value={data.industry_stats?.avg_risk_score ?? 0.42} colorClass="text-cyan-400" icon="📊" />
            <KPICard
              label="AI Issues Found"
              value={insights?.insight_count ?? '—'}
              colorClass={(insights?.critical_issues ?? 0) > 0 ? 'text-red-400' : 'text-yellow-400'}
              icon={insights?.critical_issues > 0 ? '🚨' : '💡'}
            />
          </div>

          {/* ── Clause count stats (only meaningful when >0) ── */}
          {(data.user_stats?.total_clauses > 0 || data.user_stats?.total_clause_risk_scores > 0) && (
            <div className="grid grid-cols-3 gap-3">
              <KPICard label="Total Clauses" value={data.user_stats.total_clauses} icon="📄" colorClass="text-purple-400" />
              <KPICard label="With Risk Scores" value={data.user_stats.total_clause_risk_scores || data.user_stats.total_contracts_analyzed} icon="📊" colorClass="text-cyan-400" />
              <KPICard label="High-Risk %" value={`${data.user_stats.high_risk_percentage}%`} icon="⚠️" colorClass={data.user_stats.high_risk_percentage > 28 ? 'text-red-400' : 'text-emerald-400'} />
            </div>
          )}

          {/* ── Percentile Ranking ── */}
          {data.user_stats?.avg_risk_score > 0 && (
            <div className="p-4 rounded-2xl" style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.15)' }}>
              <h4 className="text-white text-sm font-semibold mb-3">📊 Percentile Ranking</h4>
              <PercentileBar pctDiff={data.user_stats?.pct_diff_from_median ?? 0} position={data.user_stats?.position ?? 'at'} />
              <p className="text-xs text-gray-500 mt-2 text-center">{data.insight}</p>
            </div>
          )}

          {/* ── Section Tabs ── */}
          <div className="flex flex-wrap gap-1.5 p-1.5 rounded-2xl" style={{ background: 'rgba(13,17,23,0.5)', border: '1px solid rgba(99,102,241,0.08)' }}>
            {SECTION_TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveSection(t.id)}
                className="px-3 py-1.5 text-xs rounded-xl font-medium transition-all"
                style={activeSection === t.id
                  ? { background: 'linear-gradient(135deg, rgba(124,58,237,0.3), rgba(6,182,212,0.2))', color: '#e2e8f0', border: '1px solid rgba(124,58,237,0.4)' }
                  : { background: 'transparent', color: '#6b7280', border: '1px solid transparent' }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* ════════ SECTION: AI INSIGHTS ════════ */}
          {activeSection === 'insights' && (
            <div className="space-y-3" style={{ animation: 'tabEnter 0.25s ease both' }}>
              {!insights && <p className="text-gray-500 text-sm">Loading insights…</p>}
              {insights && insights.insights.length === 0 && (
                <div className="p-6 rounded-2xl text-center" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
                  <p className="text-emerald-400 font-semibold">✅ No critical issues detected.</p>
                  <p className="text-gray-500 text-xs mt-1">Your portfolio aligns well with industry benchmarks.</p>
                </div>
              )}
              {insights?.insights.map((ins, i) => {
                const cfg = SEV_CONFIG[ins.severity] || SEV_CONFIG.medium;
                return (
                  <div key={i} className="p-4 rounded-2xl" style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, animation: `insightSlide 0.3s ease ${i * 0.05}s both` }}>
                    <div className="flex items-start gap-3">
                      <span className="text-xl mt-0.5 flex-shrink-0">{cfg.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                          <span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ background: cfg.border }}>
                            {ins.severity.toUpperCase()}
                          </span>
                          <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>
                            {ins.clause}
                          </span>
                        </div>
                        <p className="text-sm font-semibold mb-1" style={{ color: cfg.text }}>{ins.problem}</p>
                        <p className="text-xs text-gray-400 mb-2">{ins.evidence}</p>
                        <div className="p-2.5 rounded-xl" style={{ background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.15)' }}>
                          <p className="text-xs text-cyan-300"><span className="font-semibold">Recommendation:</span> {ins.recommendation}</p>
                        </div>
                        {ins.impact && (
                          <p className="text-xs text-emerald-400 mt-1.5 font-medium">🎯 {ins.impact}</p>
                        )}
                      </div>
                      {ins.your_score !== null && ins.your_score !== undefined && (
                        <div className="flex-shrink-0 text-right">
                          <div className="text-lg font-bold" style={{ color: cfg.text }}>{Math.round(ins.your_score * 100)}%</div>
                          <div className="text-xs text-gray-500">risk</div>
                          <div className="text-xs text-gray-600">ind: {Math.round(ins.industry_score * 100)}%</div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* ════════ SECTION: CLAUSE ANALYSIS ════════ */}
          {activeSection === 'clauses' && (
            <div className="space-y-4" style={{ animation: 'tabEnter 0.25s ease both' }}>
              {/* Chart */}
              {chartData.length > 0 && (
                <Card>
                  <h4 className="text-white font-semibold mb-4 text-sm">Your Metrics vs Industry Median</h4>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={chartData} margin={{ left: -10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                      <XAxis dataKey="metric" tick={{ fill: '#6b7280', fontSize: 10 }} />
                      <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }} labelStyle={{ color: '#9ca3af' }} />
                      <Legend />
                      <Bar dataKey="Your" fill="#06B6D4" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="Industry" fill="rgba(99,102,241,0.4)" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              )}

              {/* Clause benchmark table */}
              {clauses && (
                <Card>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-semibold text-sm">Clause-Level Benchmark Table</h4>
                    <span className="text-xs text-gray-500">{clauses.total_clause_types_found} found · {clauses.total_clause_types_missing} missing</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
                          {['Clause Type','Your Risk','Ind. Risk','Usage%','Dispute%','Negot.%','Status'].map((h) => (
                            <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium whitespace-nowrap">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {clauses.clauses.map((row, i) => {
                          const st = STATUS_CONFIG[row.status] || STATUS_CONFIG.medium;
                          return (
                            <tr key={i} className="border-b transition-colors hover:bg-white/5" style={{ borderColor: 'rgba(99,102,241,0.05)' }}>
                              <td className="py-2 px-2 text-gray-300 font-medium whitespace-nowrap">{row.clause}</td>
                              <td className="py-2 px-2">
                                {row.your_risk_score !== null ? (
                                  <span className="font-bold" style={{ color: row.your_risk_score > 0.65 ? '#f87171' : row.your_risk_score > 0.45 ? '#fbbf24' : '#34d399' }}>
                                    {Math.round(row.your_risk_score * 100)}%
                                  </span>
                                ) : <span className="text-gray-600">—</span>}
                              </td>
                              <td className="py-2 px-2 text-cyan-400">{Math.round(row.industry_risk_score * 100)}%</td>
                              <td className="py-2 px-2">
                                <div className="flex items-center gap-1.5">
                                  <div className="h-1.5 w-16 rounded-full overflow-hidden" style={{ background: 'rgba(99,102,241,0.1)' }}>
                                    <div className="h-full rounded-full" style={{ width: `${row.usage_rate}%`, background: '#6366f1' }} />
                                  </div>
                                  <span className="text-gray-400">{row.usage_rate}%</span>
                                </div>
                              </td>
                              <td className="py-2 px-2">
                                <span className={row.dispute_rate > 20 ? 'text-red-400' : row.dispute_rate > 12 ? 'text-yellow-400' : 'text-emerald-400'}>
                                  {row.dispute_rate}%
                                </span>
                              </td>
                              <td className="py-2 px-2 text-purple-400">{row.negotiation_rate}%</td>
                              <td className="py-2 px-2">
                                <span className="px-2 py-0.5 rounded-full text-xs font-bold whitespace-nowrap" style={{ background: st.bg, color: st.color }}>
                                  {st.label}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* ════════ SECTION: VOLATILITY ════════ */}
          {activeSection === 'volatility' && (
            <div className="space-y-4" style={{ animation: 'tabEnter 0.25s ease both' }}>
              {data.clause_volatility && data.clause_volatility.length > 0 ? (
                <>
                  <div className="grid grid-cols-3 gap-3">
                    <KPICard label="Clause Types Tracked" value={data.clause_volatility.length} icon="📋" colorClass="text-cyan-400" />
                    <KPICard label="Most Volatile" value={data.clause_volatility[0]?.clause_type?.split(' ')[0] || '—'} icon="🌊" colorClass="text-red-400" />
                    <KPICard label="Total Clauses" value={data.user_stats?.total_clauses || 0} icon="📄" colorClass="text-purple-400" />
                  </div>
                  <Card>
                    <h4 className="text-white font-semibold mb-1 text-sm">Volatility Score by Clause Type</h4>
                    <p className="text-xs text-gray-500 mb-4">Higher score = more variance in risk across renegotiations (deviation from portfolio mean)</p>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={data.clause_volatility} margin={{ left: -10, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                        <XAxis dataKey="clause_type" tick={{ fill: '#6b7280', fontSize: 9 }} angle={-30} textAnchor="end" interval={0} />
                        <YAxis tick={{ fill: '#6b7280', fontSize: 9 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }} labelStyle={{ color: '#9ca3af' }}
                          formatter={(val, name) => [name === 'volatility_index' ? val : `${Math.round(val * 100)}%`, name === 'volatility_index' ? 'Volatility' : 'Avg Risk']} />
                        <ReferenceLine
                          y={data.clause_volatility.reduce((s, c) => s + c.avg_risk, 0) / data.clause_volatility.length}
                          stroke="#06B6D4" strokeDasharray="4 2"
                          label={{ value: 'Portfolio Avg', fill: '#06B6D4', fontSize: 9 }}
                        />
                        <Bar dataKey="avg_risk" name="avg_risk" radius={[4, 4, 0, 0]}>
                          {data.clause_volatility.map((row, i) => (
                            <Cell key={i} fill={row.avg_risk > 0.65 ? '#ef4444' : row.avg_risk > 0.45 ? '#f59e0b' : '#10b981'} />
                          ))}
                        </Bar>
                        <Bar dataKey="volatility_index" name="volatility_index" fill="rgba(139,92,246,0.5)" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Card>
                  <Card>
                    <h4 className="text-white font-semibold mb-3 text-sm">Top 5 Most Volatile Clauses</h4>
                    <div className="space-y-3">
                      {[...data.clause_volatility].sort((a, b) => b.volatility_index - a.volatility_index).slice(0, 5).map((item, i) => (
                        <div key={i} className="flex items-center gap-3 p-3 rounded-xl" style={{
                          background: item.avg_risk > 0.65 ? 'rgba(239,68,68,0.06)' : 'rgba(99,102,241,0.05)',
                          border: `1px solid ${item.avg_risk > 0.65 ? 'rgba(239,68,68,0.2)' : 'rgba(99,102,241,0.1)'}`,
                        }}>
                          <span className="text-sm font-bold" style={{ color: '#6366f1', minWidth: 20 }}>#{i + 1}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between mb-1">
                              <span className="text-xs text-gray-300 font-medium truncate">{item.clause_type}</span>
                              <span className={`text-xs font-bold ${item.avg_risk > 0.65 ? 'text-red-400' : item.avg_risk > 0.45 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                                {Math.round(item.avg_risk * 100)}% risk
                              </span>
                            </div>
                            <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(99,102,241,0.1)' }}>
                              <div className="h-full rounded-full" style={{
                                width: `${Math.min(item.volatility_index * 20, 100)}%`,
                                background: item.avg_risk > 0.65 ? 'linear-gradient(90deg,#ef4444,#f87171)' : 'linear-gradient(90deg,#7c3aed,#06b6d4)',
                              }} />
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <div className="text-sm font-bold text-purple-400">{item.volatility_index}</div>
                            <div className="text-xs text-gray-600">vol. idx</div>
                          </div>
                          {item.avg_risk > 0.65 && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 font-bold flex-shrink-0">HIGH RISK</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </Card>
                </>
              ) : (
                <div className="p-6 rounded-2xl text-center" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }}>
                  <p className="text-gray-500 text-sm">No clause volatility data available. Analyze contracts first.</p>
                </div>
              )}
            </div>
          )}

          {/* ════════ SECTION: TOP INDUSTRY CLAUSES ════════ */}
          {activeSection === 'industry' && (
            <div className="space-y-4" style={{ animation: 'tabEnter 0.25s ease both' }}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {clauses && clauses.clauses.filter(c => c.your_count > 0).slice(0, 8).map((row, i) => (
                  <div key={i} className="p-4 rounded-2xl" style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.12)', transition: 'border-color 0.2s' }}>
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-bold text-white">{row.clause}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ background: STATUS_CONFIG[row.status]?.bg, color: STATUS_CONFIG[row.status]?.color }}>
                        {STATUS_CONFIG[row.status]?.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mb-3 italic">"{row.top_structure}"</p>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {[
                        { label: 'Industry Use', val: `${row.usage_rate}%`, color: '#6366f1' },
                        { label: 'Dispute Rate', val: `${row.dispute_rate}%`, color: row.dispute_rate > 18 ? '#ef4444' : '#10b981' },
                        { label: 'Negotiated', val: `${row.negotiation_rate}%`, color: '#f59e0b' },
                      ].map(({ label, val, color }) => (
                        <div key={label} className="text-center p-2 rounded-lg" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.08)' }}>
                          <div className="text-sm font-bold" style={{ color }}>{val}</div>
                          <div className="text-xs text-gray-600">{label}</div>
                        </div>
                      ))}
                    </div>
                    <div className="p-2 rounded-lg text-xs text-cyan-300" style={{ background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.12)' }}>
                      💡 {row.best_practice}
                    </div>
                  </div>
                ))}
              </div>

              {/* Missing critical clauses */}
              {clauses && clauses.clauses.filter(c => c.your_count === 0 && c.usage_rate >= 65).length > 0 && (
                <Card>
                  <h4 className="text-white font-semibold mb-3 text-sm">⚠️ Missing High-Impact Clauses</h4>
                  <div className="space-y-2">
                    {clauses.clauses.filter(c => c.your_count === 0 && c.usage_rate >= 65).map((row, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-xl"
                        style={{ background: 'rgba(234,179,8,0.05)', border: '1px solid rgba(234,179,8,0.15)' }}>
                        <span className="text-yellow-400 text-lg">⚠️</span>
                        <div className="flex-1 min-w-0">
                          <span className="text-sm font-semibold text-yellow-300">{row.clause}</span>
                          <p className="text-xs text-gray-500 mt-0.5">Used in {row.usage_rate}% of industry contracts · {row.dispute_rate}% dispute rate without it</p>
                        </div>
                        <span className="text-xs text-gray-600 flex-shrink-0">{row.usage_rate}% adoption</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* ════════ SECTION: RECOMMENDATIONS ════════ */}
          {activeSection === 'recommendations' && (
            <div className="space-y-4" style={{ animation: 'tabEnter 0.25s ease both' }}>
              {recsLoading && (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ background: 'rgba(124,58,237,0.05)', border: '1px solid rgba(124,58,237,0.1)' }} />
                  ))}
                </div>
              )}
              {!recsLoading && !recs && (
                <div className="p-8 rounded-2xl text-center" style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.15)' }}>
                  <p className="text-4xl mb-3">👉</p>
                  <p className="text-white font-semibold text-sm mb-1">Click "Improve My Contract" to generate AI recommendations</p>
                  <p className="text-gray-500 text-xs">The AI will analyze your full portfolio and suggest clause improvements, replacements, and risk-reduction actions.</p>
                </div>
              )}
              {recs && !recsLoading && (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <KPICard label="Total Actions" value={recs.total_recommendations} icon="📋" colorClass="text-cyan-400" />
                    <KPICard label="Critical" value={recs.critical_count} icon="🚨" colorClass="text-red-400" />
                    <KPICard label="High Priority" value={recs.high_count} icon="⚠️" colorClass="text-orange-400" />
                    <KPICard label="Est. Risk Reduction" value={recs.estimated_risk_reduction} icon="📉" colorClass="text-emerald-400" />
                  </div>
                  <div className="space-y-3">
                    {recs.recommendations.map((rec, i) => {
                      const cfg = PRIORITY_CONFIG[rec.priority] || PRIORITY_CONFIG.medium;
                      return (
                        <div key={i} className="p-4 rounded-2xl" style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, animation: `recPop 0.3s ease ${i * 0.04}s both` }}>
                          <div className="flex items-start gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                <span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ background: cfg.border }}>{cfg.label}</span>
                                <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>{rec.category}</span>
                                <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.08)', color: '#6b7280' }}>{rec.clause}</span>
                              </div>
                              <p className="text-sm font-semibold mb-1" style={{ color: cfg.color }}>{rec.issue}</p>
                              <div className="p-2.5 rounded-xl mb-2" style={{ background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                <p className="text-xs text-cyan-300"><span className="font-semibold">Recommendation:</span> {rec.recommendation}</p>
                                <p className="text-xs text-gray-400 mt-1">{rec.action}</p>
                              </div>
                              <div className="flex items-center gap-3 flex-wrap">
                                <p className="text-xs text-emerald-400 font-medium">🎯 {rec.impact}</p>
                                <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.1)', color: '#6b7280' }}>
                                  Effort: {rec.effort}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ─── Tab 5: Temporal Evolution ────────────────────────────────────

const CLAUSE_LINE_COLORS = {
  'Payment Terms': '#4C8EDA',
  Liability: '#F16667',
  Termination: '#F79767',
  Indemnification: '#E8A838',
  Confidentiality: '#9063CD',
  'Force Majeure': '#10b981',
  Unknown: '#68BC00',
};

const TemporalTab = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await getTemporalEvolution();
        setData(result);
      } catch (err) {
        setError('Failed to load temporal data.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const pivotData = React.useMemo(() => {
    if (!data?.time_series) return [];
    const months = [...new Set(data.time_series.map((t) => t.month))].sort();
    return months.map((month) => {
      const row = { month };
      data.time_series.filter((t) => t.month === month).forEach((t) => {
        row[t.clause_type] = t.count;
      });
      return row;
    });
  }, [data]);

  const clauseTypes = data ? [...new Set(data.time_series?.map((t) => t.clause_type) || [])] : [];

  return (
    <div className="space-y-5">
      <Card>
        <SectionHeader title="Temporal Clause Evolution" subtitle="How clause types and risk scores evolve month-by-month across your contract portfolio. Supplier intelligence shows which counterparties carry the highest risk." icon="⏱" />
      </Card>

      {loading && (
        <div className="space-y-3">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-32 rounded-2xl animate-pulse" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }} />
          ))}
        </div>
      )}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {data && (
        <>
          {/* If only 1 month — show contract-level risk breakdown instead of flat line chart */}
          {data.total_months <= 1 && data.contract_breakdown?.length > 0 ? (
            <Card>
              <h4 className="text-white font-semibold mb-1 flex items-center gap-2">Contract Risk Snapshot
                <span className="text-xs font-normal text-gray-500 ml-2">All contracts uploaded in {data.contract_breakdown[0]?.month || 'same period'} — temporal trend requires contracts across multiple months</span>
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                {data.contract_breakdown.map((c, i) => {
                  const riskColor = c.risk_level === 'HIGH' ? '#ef4444' : c.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981';
                  return (
                    <div key={i} className="rounded-xl p-4 transition-all" style={{ background: `${riskColor}0d`, border: `1px solid ${riskColor}33` }}>
                      <div className="text-xs text-gray-400 truncate mb-1" title={c.name}>{c.name}</div>
                      <div className="text-2xl font-black" style={{ color: riskColor }}>{Math.round(c.risk_score * 100)}%</div>
                      <div className="text-xs mt-1" style={{ color: riskColor }}>{c.risk_level} RISK</div>
                      <div className="text-xs text-gray-500 mt-1">{c.clause_count} clauses · {c.contract_type}</div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 p-3 rounded-xl text-xs text-gray-500" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }}>
                💡 Upload contracts over multiple months to see clause evolution trends. Risk scores: {data.contract_breakdown.map(c => `${c.name.slice(0,15)}→${Math.round(c.risk_score*100)}%`).join(' · ')}
              </div>
            </Card>
          ) : (
            <Card>
              <h4 className="text-white font-semibold mb-4">Clause Type Counts Over Time</h4>
              {pivotData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={pivotData} margin={{ left: -10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                    <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 9 }} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }} labelStyle={{ color: '#9ca3af' }} />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                    {clauseTypes.slice(0, 6).map((ct) => (
                      <Line key={ct} type="monotone" dataKey={ct} stroke={CLAUSE_LINE_COLORS[ct] || '#94a3b8'} strokeWidth={2} dot={{ r: 4 }} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-48 flex items-center justify-center text-gray-500 text-sm">No temporal data available</div>
              )}
            </Card>
          )}

          {data.supplier_intelligence?.length > 0 && (
            <Card>
              <h4 className="text-white font-semibold mb-3">Supplier Intelligence</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
                      <th className="text-left py-2 pr-4 text-gray-500 font-medium">Supplier / Counterparty</th>
                      <th className="text-right py-2 pr-4 text-gray-500 font-medium">Contracts</th>
                      <th className="text-right py-2 pr-4 text-gray-500 font-medium">Avg Risk</th>
                      <th className="text-right py-2 pr-4 text-gray-500 font-medium">Dispute Likelihood</th>
                      <th className="text-center py-2 pr-4 text-gray-500 font-medium">Trend</th>
                      <th className="text-center py-2 text-gray-500 font-medium">Risk Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.supplier_intelligence.map((s, i) => (
                      <tr key={i} className="border-b transition-colors" style={{ borderColor: 'rgba(99,102,241,0.05)' }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      >
                        <td className="py-2 pr-4 text-gray-200 font-semibold">{s.supplier}</td>
                        <td className="py-2 pr-4 text-right text-gray-400">{s.contract_count}</td>
                        <td className={`py-2 pr-4 text-right font-bold ${s.avg_risk_score > 0.6 ? 'text-red-400' : s.avg_risk_score > 0.35 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                          {Math.round(s.avg_risk_score * 100)}%
                        </td>
                        <td className="py-2 pr-4 text-right text-gray-400">{Math.round(s.dispute_likelihood * 100)}%</td>
                        <td className="py-2 pr-4 text-center">
                          <span className={`${s.trend === 'increasing' ? 'text-red-400' : s.trend === 'decreasing' ? 'text-emerald-400' : 'text-gray-400'}`}>
                            {s.trend === 'increasing' ? '▲' : s.trend === 'decreasing' ? '▼' : '→'}
                          </span>
                        </td>
                        <td className="py-2 text-center">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${s.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-300' : s.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-300' : 'bg-emerald-500/20 text-emerald-300'}`}>
                            {s.risk_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

// ─── Tab 6: Risk vs Margin Frontier ──────────────────────────────

const RiskMarginTab = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await getRiskMarginFrontier();
        setData(result);
      } catch {
        setError('Failed to load risk-margin data.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    const color = payload.risk_score > 0.6 ? '#F16667' : payload.risk_score > 0.35 ? '#F79767' : '#68BC00';
    return (
      <circle
        cx={cx} cy={cy} r={5}
        fill={color} fillOpacity={0.7}
        stroke={color} strokeWidth={1}
        style={{ cursor: 'pointer' }}
        onMouseEnter={() => setTooltip(payload)}
        onMouseLeave={() => setTooltip(null)}
      />
    );
  };

  return (
    <div className="space-y-5">
      <Card>
        <SectionHeader title="Risk vs Margin Frontier" subtitle="Each point represents a contract — plotted by risk score (X) vs estimated margin (Y). The green line shows the efficient frontier (pareto-optimal contracts)." icon="⚖️" />
      </Card>

      {loading && <div className="text-center py-12 text-gray-500 text-sm">Loading frontier data…</div>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {data && data.total_contracts === 0 && (
        <div className="text-center py-12 text-gray-500 text-sm">{data.message || 'No analyzed contracts found.'}</div>
      )}

      {data && data.total_contracts > 0 && (
        <>
          <div className="grid grid-cols-4 gap-3">
            <KPICard label="Contracts Plotted" value={data.total_contracts} colorClass="text-cyan-400" icon="📌" />
            <KPICard label="Avg Risk Score" value={`${Math.round((data.avg_risk || 0) * 100)}%`} colorClass="text-orange-400" icon="⚠️" />
            <KPICard label="Avg Margin" value={`${data.avg_margin}%`} colorClass="text-emerald-400" icon="📈" />
            <KPICard label="Pareto Optimal" value={data.pareto_count} colorClass="text-cyan-300" icon="🎯" />
          </div>

          {tooltip && (
            <div className="px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(13,17,23,0.9)', border: '1px solid rgba(6,182,212,0.25)', boxShadow: '0 0 16px rgba(6,182,212,0.1)' }}>
              <span className="font-bold text-white">{tooltip.contract_name}</span>
              <span className="text-gray-400 ml-3">Risk: {Math.round((tooltip.risk_score || 0) * 100)}%</span>
              <span className="text-gray-400 ml-3">Margin: {tooltip.margin}%</span>
              <span className="text-gray-400 ml-3">Level: {tooltip.risk_level}</span>
              {tooltip.payment_terms && <span className="text-gray-400 ml-3">Terms: {tooltip.payment_terms}</span>}
            </div>
          )}

          <Card>
            <h4 className="text-white font-semibold mb-4">Risk vs Margin Scatter Plot</h4>
            <ResponsiveContainer width="100%" height={340}>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                <XAxis
                  dataKey="risk_score"
                  name="Risk Score"
                  type="number"
                  domain={[0, 1]}
                  tickFormatter={(v) => `${Math.round(v * 100)}%`}
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  label={{ value: 'Risk Score →', position: 'insideBottom', fill: '#4b5563', fontSize: 10, dy: 14 }}
                />
                <YAxis
                  dataKey="margin"
                  name="Margin %"
                  type="number"
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  tickFormatter={(v) => `${v}%`}
                  label={{ value: 'Margin %', angle: -90, position: 'insideLeft', fill: '#4b5563', fontSize: 10 }}
                />
                <ZAxis range={[40, 40]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px', fontSize: '11px' }}
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ payload }) => {
                    if (!payload?.length) return null;
                    const p = payload[0]?.payload;
                    if (!p?.contract_id) return null;
                    return (
                      <div className="rounded-xl p-3 text-xs" style={{ background: '#0d1117', border: '1px solid rgba(99,102,241,0.2)' }}>
                        <p className="text-white font-semibold">{p?.contract_name}</p>
                        <p className="text-gray-400 mt-1">Risk: {Math.round((p?.risk_score || 0) * 100)}%</p>
                        <p className="text-gray-400">Margin: {p?.margin}%</p>
                        <p className="text-gray-400">Level: {p?.risk_level}</p>
                        {p?.payment_terms && <p className="text-gray-400">Terms: {p.payment_terms}</p>}
                        <p className="text-gray-500 text-xs mt-1">ID: {p?.contract_id?.slice(0, 8)}…</p>
                      </div>
                    );
                  }}
                />
                {/* All contracts */}
                <Scatter name="Contracts" data={data.scatter_data} shape={<CustomDot />} />
                {/* Pareto-optimal efficient frontier line */}
                {data.efficient_frontier?.length > 1 && (
                  <Scatter
                    name="Efficient Frontier"
                    data={data.efficient_frontier}
                    line={{ stroke: '#06b6d4', strokeWidth: 2, strokeDasharray: '5 3' }}
                    lineType="joint"
                    shape={({ cx, cy }) => (
                      <circle cx={cx} cy={cy} r={3} fill="#06b6d4" fillOpacity={0.9} stroke="#06b6d4" strokeWidth={1} />
                    )}
                  />
                )}
              </ScatterChart>
            </ResponsiveContainer>

            <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-red-500 opacity-70" />High Risk (&gt;60%)</div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-orange-500 opacity-70" />Medium Risk (35–60%)</div>
              <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-500 opacity-70" />Low Risk (&lt;35%)</div>
              <div className="ml-auto flex items-center gap-1.5"><span className="inline-block w-6 border-t-2 border-dashed border-cyan-400" />Efficient Frontier ({data.pareto_count} contracts)</div>
            </div>
          </Card>
        </>
      )}
    </div>
  );
};

// ─── Tab 7: Supplier Heatmap ──────────────────────────────────────

const SupplierHeatmapTab = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await getSupplierHeatmap();
        setData(result);
      } catch {
        setError('Failed to load supplier heatmap.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const riskColor = (score) => {
    const r = Math.round(score * 220);
    const g = Math.round((1 - score) * 180);
    return `rgb(${r}, ${g}, 40)`;
  };

  const chartData = data?.suppliers?.slice(0, 10).map((s) => ({
    name: s.supplier.length > 12 ? s.supplier.slice(0, 12) + '…' : s.supplier,
    risk: Math.round(s.risk_score * 100),
    contracts: s.contract_count,
  })) || [];

  return (
    <div className="space-y-5">
      <Card>
        <SectionHeader title="Supplier Risk Heatmap" subtitle="Risk intensity by supplier and region. Darker/redder cells indicate higher risk." icon="🔥" />
      </Card>

      {loading && <div className="text-center py-12 text-gray-500 text-sm">Loading heatmap…</div>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {data && (
        <>
          <Card>
            <h4 className="text-white font-semibold mb-4">Supplier Risk Grid</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Supplier</th>
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Region</th>
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Risk Score</th>
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Contracts</th>
                    <th className="text-left py-2 text-gray-500 font-medium">High-Risk Clauses</th>
                  </tr>
                </thead>
                <tbody>
                  {data.suppliers.map((s, i) => (
                    <tr key={i} className="border-b transition-colors" style={{ borderColor: 'rgba(99,102,241,0.05)' }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <td className="py-2 pr-4 text-gray-200 font-semibold">{s.supplier}</td>
                      <td className="py-2 pr-4 text-gray-400">{s.region}</td>
                      <td className="py-2 pr-4">
                        <div
                          className="inline-flex items-center justify-center w-16 h-6 rounded-lg text-white text-xs font-bold"
                          style={{ background: riskColor(s.risk_score), boxShadow: `0 0 10px ${riskColor(s.risk_score)}40` }}
                        >
                          {Math.round(s.risk_score * 100)}%
                        </div>
                      </td>
                      <td className="py-2 pr-4 text-gray-400">{s.contract_count}</td>
                      <td className="py-2 text-gray-400">{s.high_risk_clauses}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {chartData.length > 0 && (
            <Card>
              <h4 className="text-white font-semibold mb-4">Top Risky Suppliers</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                  <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 10 }} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                  <YAxis dataKey="name" type="category" tick={{ fill: '#6b7280', fontSize: 10 }} width={90} />
                  <Tooltip contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }} formatter={(v) => [`${v}%`, 'Risk Score']} />
                  <Bar dataKey="risk" radius={[0, 6, 6, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.risk > 60 ? '#F16667' : entry.risk > 35 ? '#F79767' : '#68BC00'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

// ─── Tab 8: Dispute Probability Timeline ─────────────────────────

const DisputeTimelineTab = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await getDisputeTimeline();
        setData(result);
      } catch {
        setError('Failed to load dispute timeline.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const chartData = data?.timeline?.map((t) => ({
    month: t.month,
    probability: Math.round(t.dispute_probability * 100),
    contracts: t.contracts_at_risk,
    cost: t.projected_cost,
    drivers: t.risk_drivers || [],
  })) || [];

  const peakIdx = chartData.length > 0
    ? chartData.reduce((maxI, d, i, arr) => d.probability > arr[maxI].probability ? i : maxI, 0)
    : -1;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload;
    return (
      <div style={{ background: '#0d1117', border: '1px solid rgba(99,102,241,0.25)', borderRadius: '12px', padding: '12px 14px', maxWidth: 260 }}>
        <p className="text-white font-semibold text-xs mb-1">{label}</p>
        <p className="text-orange-400 text-xs mb-2">Dispute Probability: <span className="font-bold">{d?.probability}%</span></p>
        <p className="text-blue-400 text-xs mb-2">Contracts at Risk: <span className="font-bold">{d?.contracts}</span></p>
        {d?.drivers?.length > 0 && (
          <div>
            <p className="text-gray-500 text-xs mb-1 font-medium">Risk Drivers:</p>
            {d.drivers.map((dr, i) => (
              <p key={i} className="text-gray-300 text-xs leading-relaxed">• {dr}</p>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-5">
      <Card>
        <SectionHeader title="Dispute Probability Timeline" subtitle="12-month event-driven projection based on clause risk scores, contract age, payment cycles, renewal windows, and seasonal patterns." icon="📅" />
      </Card>

      {loading && <div className="text-center py-12 text-gray-500 text-sm">Loading dispute timeline…</div>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {data && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <KPICard label="Base Probability" value={`${Math.round(data.base_dispute_probability * 100)}%`} colorClass="text-orange-400" icon="🎲" />
            <KPICard label="Peak Risk Month" value={data.peak_risk_month} colorClass="text-red-400" icon="📍" />
            <KPICard label="Months Above Threshold" value={data.contracts_above_threshold} colorClass="text-yellow-400" icon="⚠️" />
          </div>

          <Card>
            <h4 className="text-white font-semibold mb-1">Dispute Probability Over 12 Months</h4>
            <p className="text-xs text-gray-500 mb-4">Hover each month to see the risk drivers explaining that month's probability.</p>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={chartData} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 9 }} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={70} stroke="#F16667" strokeDasharray="4 4" label={{ value: '70% Threshold', fill: '#F16667', fontSize: 10, position: 'insideTopRight' }} />
                {peakIdx >= 0 && (
                  <ReferenceLine x={chartData[peakIdx]?.month} stroke="#e879f9" strokeDasharray="3 3" label={{ value: 'Peak', fill: '#e879f9', fontSize: 9, position: 'insideTopLeft' }} />
                )}
                <Area type="monotone" dataKey="probability" stroke="#F79767" fill="rgba(247,151,103,0.15)" strokeWidth={2} dot={(props) => {
                  const { cx, cy, index } = props;
                  if (index !== peakIdx) return null;
                  return <circle key="peak-dot" cx={cx} cy={cy} r={5} fill="#e879f9" stroke="#fff" strokeWidth={1.5} />;
                }} />
                <Line type="monotone" dataKey="contracts" stroke="#4C8EDA" strokeWidth={1.5} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </Card>

          {/* Month-by-month risk driver breakdown */}
          {data.timeline?.some(t => t.risk_drivers?.length > 0) && (
            <Card>
              <h4 className="text-white font-semibold mb-3">Monthly Risk Driver Breakdown</h4>
              <div className="space-y-2">
                {data.timeline.map((t, i) => {
                  const prob = Math.round(t.dispute_probability * 100);
                  const isHigh = prob >= 70;
                  const isMid = prob >= 50 && prob < 70;
                  const isPeak = t.month === data.peak_risk_month;
                  const hasDrivers = t.risk_drivers?.length > 0 && t.risk_drivers[0] !== 'No major risk events — baseline risk period';
                  if (!hasDrivers && !isPeak) return null;
                  return (
                    <div key={i} className="flex items-start gap-3 px-4 py-3 rounded-xl" style={{ background: isPeak ? 'rgba(232,121,249,0.06)' : 'rgba(13,17,23,0.6)', border: `1px solid ${isPeak ? 'rgba(232,121,249,0.2)' : 'rgba(99,102,241,0.08)'}` }}>
                      <div className="flex-shrink-0 mt-0.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${isHigh ? 'bg-red-500/20 text-red-300' : isMid ? 'bg-yellow-500/20 text-yellow-300' : 'bg-emerald-500/20 text-emerald-300'}`}>{prob}%</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-white text-xs font-semibold">{t.month}</span>
                          {isPeak && <span className="text-xs px-1.5 py-0.5 rounded-full font-semibold" style={{ background: 'rgba(232,121,249,0.15)', color: '#e879f9' }}>Peak</span>}
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {t.risk_drivers.map((dr, j) => (
                            <span key={j} className="text-xs px-2 py-0.5 rounded-full text-gray-300" style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.15)' }}>
                              {dr}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {data.high_risk_contracts?.length > 0 && (
            <Card>
              <h4 className="text-white font-semibold mb-3">High-Risk Contracts</h4>
              <div className="space-y-2">
                {data.high_risk_contracts.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all" style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.08)' }}>
                    <span className="text-sm text-gray-200 flex-1 font-medium">{c.name}</span>
                    <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${c.risk_score > 0.6 ? 'bg-red-500/20 text-red-300' : 'bg-yellow-500/20 text-yellow-300'}`}>
                      Risk {Math.round(c.risk_score * 100)}%
                    </span>
                    <span className="text-xs text-orange-400 font-medium">Dispute {Math.round(c.dispute_probability * 100)}%</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

// ─── Tab 9: Clause Volatility Index ──────────────────────────────

const ClauseVolatilityTab = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getClauseVolatility();
      setData(result);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load volatility data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const VOL_COLORS = ['#F16667', '#F79767', '#E8A838', '#06B6D4', '#4C8EDA', '#9063CD', '#10b981', '#8b5cf6'];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between p-4 rounded-2xl" style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.15)' }}>
        <div>
          <h3 className="text-white font-bold">Clause Volatility Index</h3>
          <p className="text-gray-500 text-xs mt-0.5">Which clause types have the highest risk variance across your contracts — indicating unstable or contested terms</p>
        </div>
        <button onClick={loadData} disabled={loading} className="px-4 py-2 text-xs rounded-xl font-medium disabled:opacity-50" style={{ background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.25)', color: '#06b6d4' }}>
          {loading ? 'Loading…' : '↻ Refresh'}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {loading && !data && (
        <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-16 rounded-2xl animate-pulse" style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.1)' }} />)}</div>
      )}

      {data && data.clause_volatility && data.clause_volatility.length > 0 && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-3 gap-3">
            <KPICard label="Clause Types Tracked" value={data.clause_volatility.length} icon="📋" colorClass="text-cyan-400" />
            <KPICard label="Most Volatile" value={data.clause_volatility[0]?.clause_type?.split(' ')[0] || '—'} icon="🌊" colorClass="text-red-400" />
            <KPICard label="Total Clauses" value={data.total_clauses || data.clause_volatility.reduce((s, c) => s + c.count, 0)} icon="📄" colorClass="text-purple-400" />
          </div>

          {/* Bar Chart — show avg_risk per clause type as the primary metric */}
          <Card>
            <h4 className="text-white font-semibold mb-1">Risk Score by Clause Type</h4>
            <p className="text-xs text-gray-500 mb-4">Avg risk score per clause type across your portfolio. Deviation from portfolio mean shows which clause types are riskier or safer than average.</p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.clause_volatility} margin={{ left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                <XAxis dataKey="clause_type" tick={{ fill: '#6b7280', fontSize: 9 }} angle={-20} textAnchor="end" interval={0} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} domain={[0, 1]} tickFormatter={(v) => `${Math.round(v*100)}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }}
                  formatter={(v, name) => [
                    name === 'avg_risk' ? `${Math.round(v*100)}%` : v,
                    name === 'avg_risk' ? 'Avg Risk Score' : 'Volatility Index'
                  ]}
                />
                <ReferenceLine y={data.clause_volatility.reduce((s,c)=>s+c.avg_risk,0)/data.clause_volatility.length} stroke="#06B6D4" strokeDasharray="4 2" label={{ value: 'Portfolio Avg', fill: '#06B6D4', fontSize: 9 }} />
                <Bar dataKey="avg_risk" name="avg_risk" radius={[6,6,0,0]}>
                  {data.clause_volatility.map((row, i) => {
                    const color = row.avg_risk > 0.5 ? '#ef4444' : row.avg_risk > 0.35 ? '#f59e0b' : '#10b981';
                    return <Cell key={i} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Detail Table */}
          <Card>
            <h4 className="text-white font-semibold mb-4">Clause Type Risk Breakdown</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Clause Type</th>
                    <th className="text-right py-2 pr-4 text-gray-500 font-medium">Clauses</th>
                    <th className="text-right py-2 pr-4 text-gray-500 font-medium">Avg Risk</th>
                    <th className="text-right py-2 pr-4 text-gray-500 font-medium">vs Portfolio Avg</th>
                    <th className="text-right py-2 text-gray-500 font-medium">High Risk %</th>
                  </tr>
                </thead>
                <tbody>
                  {data.clause_volatility.map((row, i) => {
                    const dev = row.deviation_from_mean ?? 0;
                    const devColor = dev > 0.02 ? '#ef4444' : dev < -0.02 ? '#10b981' : '#6b7280';
                    const devLabel = dev > 0.02 ? `↑ +${Math.round(dev*100)}%` : dev < -0.02 ? `↓ ${Math.round(dev*100)}%` : '→ avg';
                    return (
                      <tr key={i} className="border-b transition-colors" style={{ borderColor: 'rgba(99,102,241,0.05)' }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                        <td className="py-2 pr-4 text-gray-300 font-medium flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: CLAUSE_TYPE_COLORS[row.clause_type] || '#94a3b8' }} />
                          {row.clause_type}
                        </td>
                        <td className="py-2 pr-4 text-right text-gray-400">{row.count}</td>
                        <td className={`py-2 pr-4 text-right font-bold ${row.avg_risk > 0.5 ? 'text-red-400' : row.avg_risk > 0.35 ? 'text-yellow-400' : 'text-emerald-400'}`}>
                          {Math.round(row.avg_risk * 100)}%
                        </td>
                        <td className="py-2 pr-4 text-right font-semibold" style={{ color: devColor }}>{devLabel}</td>
                        <td className="py-2 text-right text-gray-400">{row.high_risk_pct}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-600 mt-3">* Volatility measures risk deviation from portfolio mean. All contracts uploaded in the same month — add more contracts over time for std-deviation based volatility.</p>
          </Card>

          {/* Insight */}
          {data.clause_volatility[0] && (
            <div className="p-4 rounded-2xl flex items-start gap-3" style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)' }}>
              <span className="text-xl">⚡</span>
              <div>
                <p className="text-red-300 text-sm font-semibold">Highest Risk Clause: {[...data.clause_volatility].sort((a,b)=>b.avg_risk-a.avg_risk)[0]?.clause_type}</p>
                <p className="text-gray-500 text-xs mt-1">
                  {(() => { const top = [...data.clause_volatility].sort((a,b)=>b.avg_risk-a.avg_risk)[0]; return <>Avg risk {Math.round((top?.avg_risk||0)*100)}% across {top?.count} clauses.</>; })()}
                  {' '}Portfolio average: {Math.round(data.clause_volatility.reduce((s,c)=>s+c.avg_risk,0)/data.clause_volatility.length*100)}%.
                  Review this clause type for renegotiation opportunities.
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {data && (!data.clause_volatility || data.clause_volatility.length === 0) && (
        <div className="p-8 text-center rounded-2xl" style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)' }}>
          <div className="text-4xl mb-3 opacity-30">📈</div>
          <p className="text-gray-500">{data.error || 'No clause volatility data available. Run risk analysis on your contracts first.'}</p>
        </div>
      )}
    </div>
  );
};

// ─── Contract Search Dropdown ──────────────────────────────────────

const riskColor = (score) => {
  if (score === null || score === undefined) return '#6b7280';
  if (score > 0.5) return '#f87171';
  if (score > 0.3) return '#fbbf24';
  return '#34d399';
};

const ContractSearchDropdown = ({ value, onChange }) => {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    setLoading(true);
    getERPContracts()
      .then((data) => setContracts(data.contracts || []))
      .catch(() => setContracts([]))
      .finally(() => setLoading(false));
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = contracts.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.id.toLowerCase().includes(search.toLowerCase())
  );

  const selected = contracts.find((c) => c.id === value);

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '8px 12px', borderRadius: '10px', fontSize: '13px', cursor: 'pointer',
          background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.25)',
          color: selected ? '#e2e8f0' : '#6b7280', textAlign: 'left',
        }}
      >
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
          {selected ? selected.name : 'Select Contract'}
        </span>
        {selected && selected.risk_score !== null && (
          <span style={{
            marginLeft: 8, padding: '1px 7px', borderRadius: 9999, fontSize: 11, fontWeight: 600,
            background: riskColor(selected.risk_score) + '22', color: riskColor(selected.risk_score),
            border: `1px solid ${riskColor(selected.risk_score)}44`, flexShrink: 0,
          }}>
            {Math.round(selected.risk_score * 100)}% risk
          </span>
        )}
        <span style={{ marginLeft: 8, opacity: 0.5, flexShrink: 0 }}>▾</span>
      </button>

      {/* Dropdown panel */}
      {open && (
        <div style={{
          position: 'absolute', zIndex: 50, top: 'calc(100% + 4px)', left: 0, right: 0,
          background: '#0f1117', border: '1px solid rgba(99,102,241,0.3)',
          borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.5)', overflow: 'hidden',
        }}>
          {/* Search */}
          <div style={{ padding: '8px 10px', borderBottom: '1px solid rgba(99,102,241,0.12)' }}>
            <input
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search contracts…"
              style={{
                width: '100%', background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
                borderRadius: 8, padding: '6px 10px', fontSize: 12, color: '#e2e8f0', outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Options */}
          <div style={{ maxHeight: 220, overflowY: 'auto' }}>
            {loading && (
              <div style={{ padding: '12px 14px', color: '#6b7280', fontSize: 12 }}>Loading contracts…</div>
            )}
            {!loading && filtered.length === 0 && (
              <div style={{ padding: '12px 14px', color: '#6b7280', fontSize: 12 }}>No contracts found.</div>
            )}
            {!loading && filtered.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => { onChange(c.id); setOpen(false); setSearch(''); }}
                style={{
                  display: 'flex', alignItems: 'center', width: '100%', padding: '9px 14px',
                  background: c.id === value ? 'rgba(99,102,241,0.15)' : 'transparent',
                  border: 'none', cursor: 'pointer', textAlign: 'left', gap: 10,
                  borderBottom: '1px solid rgba(99,102,241,0.06)',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.1)'}
                onMouseLeave={(e) => e.currentTarget.style.background = c.id === value ? 'rgba(99,102,241,0.15)' : 'transparent'}
              >
                <span style={{ flex: 1, fontSize: 12, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {c.name}
                </span>
                <span style={{ fontSize: 10, color: '#6b7280', flexShrink: 0 }}>
                  {c.id.slice(0, 8)}…
                </span>
                {c.risk_score !== null && (
                  <span style={{
                    padding: '1px 7px', borderRadius: 9999, fontSize: 10, fontWeight: 700, flexShrink: 0,
                    background: riskColor(c.risk_score) + '22', color: riskColor(c.risk_score),
                    border: `1px solid ${riskColor(c.risk_score)}44`,
                  }}>
                    {Math.round(c.risk_score * 100)}%
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Clear */}
          {value && (
            <div style={{ padding: '6px 10px', borderTop: '1px solid rgba(99,102,241,0.12)' }}>
              <button
                type="button"
                onClick={() => { onChange(''); setOpen(false); }}
                style={{ fontSize: 11, color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                ✕ Clear selection
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Tab 10: ERP Execution ─────────────────────────────────────────

const TRIGGER_OPTIONS = [
  { value: 'payment_hold', label: 'Payment Hold' },
  { value: 'procurement_change', label: 'Procurement Change' },
  { value: 'vendor_alert', label: 'Vendor Alert' },
  { value: 'contract_execute', label: 'Contract Execute' },
];

const ERPExecutionTab = () => {
  const [log, setLog] = useState([]);
  const [logLoading, setLogLoading] = useState(false);

  // Single trigger
  const [contractId, setContractId] = useState('');
  const [contractMeta, setContractMeta] = useState(null); // { name, risk_score, contract_type }
  const [erpContracts, setErpContracts] = useState([]);
  const [triggerType, setTriggerType] = useState('payment_hold');
  const [reason, setReason] = useState('');
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [triggerResult, setTriggerResult] = useState(null);

  // Bulk
  const [bulkIds, setBulkIds] = useState('');
  const [bulkAction, setBulkAction] = useState('payment_hold');
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);

  const [error, setError] = useState('');

  const loadLog = useCallback(async () => {
    setLogLoading(true);
    try {
      const data = await getERPExecutionLog();
      setLog(data.executions || []);
    } catch {
      // silently fail
    } finally {
      setLogLoading(false);
    }
  }, []);

  useEffect(() => { loadLog(); }, [loadLog]);

  // Load contracts list once for dropdown
  useEffect(() => {
    getERPContracts()
      .then((data) => setErpContracts(data.contracts || []))
      .catch(() => {});
  }, []);

  const handleContractSelect = (id) => {
    setContractId(id);
    if (id) {
      const found = erpContracts.find((c) => c.id === id);
      setContractMeta(found || null);
    } else {
      setContractMeta(null);
    }
  };

  const handleTrigger = async () => {
    setTriggerLoading(true);
    setError('');
    setTriggerResult(null);
    try {
      const result = await triggerERPAction({ contractId, triggerType, reason });
      setTriggerResult(result);
      await loadLog();
    } catch (err) {
      setError(err?.response?.data?.error || 'ERP trigger failed.');
    } finally {
      setTriggerLoading(false);
    }
  };

  const handleBulk = async () => {
    setBulkLoading(true);
    setError('');
    setBulkResult(null);
    try {
      const ids = bulkIds.split('\n').map((id) => id.trim()).filter(Boolean);
      if (!ids.length) { setError('Enter at least one contract ID.'); setBulkLoading(false); return; }
      const result = await bulkERPExecute({ contractIds: ids, action: bulkAction, reason: 'Bulk ERP execution' });
      setBulkResult(result);
      await loadLog();
    } catch (err) {
      setError(err?.response?.data?.error || 'Bulk execution failed.');
    } finally {
      setBulkLoading(false);
    }
  };

  const STATUS_STYLES = {
    executed: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
    failed: 'bg-red-500/20 text-red-300 border border-red-500/30',
    pending: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
  };

  const TRIGGER_COLORS = {
    payment_hold: 'text-red-400',
    procurement_change: 'text-blue-400',
    vendor_alert: 'text-orange-400',
    contract_execute: 'text-emerald-400',
  };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Single Trigger */}
        <Card>
          <SectionHeader title="Auto-Trigger ERP Action" icon="⚙️" />
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract</label>
              <ContractSearchDropdown value={contractId} onChange={handleContractSelect} />
            </div>

            {/* Selected contract summary */}
            {contractMeta && (
              <div style={{
                padding: '8px 12px', borderRadius: 10, fontSize: 12,
                background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.18)',
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <div style={{ flex: 1 }}>
                  <p style={{ color: '#c4b5fd', fontWeight: 600, marginBottom: 2 }}>{contractMeta.name}</p>
                  {contractMeta.contract_type && (
                    <p style={{ color: '#6b7280' }}>{contractMeta.contract_type}</p>
                  )}
                </div>
                {contractMeta.risk_score !== null && (
                  <span style={{
                    padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 700,
                    background: riskColor(contractMeta.risk_score) + '22',
                    color: riskColor(contractMeta.risk_score),
                    border: `1px solid ${riskColor(contractMeta.risk_score)}44`,
                  }}>
                    {Math.round(contractMeta.risk_score * 100)}% risk
                  </span>
                )}
              </div>
            )}

            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Trigger Type</label>
              <StyledSelect value={triggerType} onChange={(e) => setTriggerType(e.target.value)}>
                {TRIGGER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </StyledSelect>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Reason</label>
              <StyledInput
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Reason for triggering this action…"
              />
            </div>
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <button
              onClick={handleTrigger}
              disabled={triggerLoading || !contractId}
              className="w-full py-2.5 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 18px rgba(6,182,212,0.2)' }}
            >
              {triggerLoading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              ⚡ {triggerLoading ? 'Triggering…' : 'Trigger ERP Action'}
            </button>
            {triggerResult && (
              <div className="p-3 rounded-xl text-xs" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
                <p className="text-emerald-300 font-semibold">{triggerResult.action}</p>
                <p className="text-gray-400 mt-1">{triggerResult.erp_system} • {triggerResult.status}</p>
                <p className="text-gray-400 mt-1">{triggerResult.estimated_impact}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Bulk Action */}
        <Card>
          <SectionHeader title="Bulk ERP Action" icon="🔀" />
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract IDs (one per line)</label>
              <StyledTextarea
                rows={5}
                value={bulkIds}
                onChange={(e) => setBulkIds(e.target.value)}
                placeholder={'contract-id-1\ncontract-id-2\ncontract-id-3'}
                className="font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Bulk Action</label>
              <StyledSelect value={bulkAction} onChange={(e) => setBulkAction(e.target.value)}>
                {TRIGGER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </StyledSelect>
            </div>
            <button
              onClick={handleBulk}
              disabled={bulkLoading || !bulkIds.trim()}
              className="w-full py-2.5 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #c2410c, #f97316)', boxShadow: '0 0 18px rgba(249,115,22,0.2)' }}
            >
              {bulkLoading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              🔀 {bulkLoading ? 'Executing…' : 'Execute Bulk Action'}
            </button>
            {bulkResult && (
              <div className="p-3 rounded-xl text-xs" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
                <p className="text-emerald-300 font-semibold">Bulk execution complete</p>
                <p className="text-gray-400 mt-1">{bulkResult.executed}/{bulkResult.total_contracts} contracts executed via {bulkResult.erp_system}</p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Execution Log */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h4 className="text-white font-semibold">Execution Log</h4>
            <span className="px-2 py-0.5 text-xs rounded-full" style={{ background: 'rgba(6,182,212,0.15)', color: '#06b6d4', border: '1px solid rgba(6,182,212,0.3)' }}>{log.length}</span>
          </div>
          <button onClick={loadLog} disabled={logLoading} className="text-xs px-3 py-1.5 rounded-lg transition-all" style={{ color: '#06b6d4', border: '1px solid rgba(6,182,212,0.2)' }}>
            {logLoading ? 'Refreshing…' : '↻ Refresh'}
          </button>
        </div>
        {log.length === 0 ? (
          <div className="text-center py-12 text-gray-600 text-sm">
            <div className="text-4xl mb-3 opacity-30">⚙️</div>
            No ERP executions yet. Trigger an action above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b" style={{ borderColor: 'rgba(99,102,241,0.1)' }}>
                  <th className="text-left py-2 pr-4 text-gray-500 font-medium">Contract</th>
                  <th className="text-left py-2 pr-4 text-gray-500 font-medium">Trigger</th>
                  <th className="text-left py-2 pr-4 text-gray-500 font-medium">ERP System</th>
                  <th className="text-left py-2 pr-4 text-gray-500 font-medium">Status</th>
                  <th className="text-right py-2 text-gray-500 font-medium">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {log.slice(0, 20).map((entry) => (
                  <tr key={entry.id} className="border-b transition-colors" style={{ borderColor: 'rgba(99,102,241,0.05)' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <td className="py-2 pr-4 text-gray-300">{entry.contract_name || entry.contract_id?.slice(0, 8) || '—'}</td>
                    <td className={`py-2 pr-4 font-semibold ${TRIGGER_COLORS[entry.trigger_type] || 'text-gray-300'}`}>
                      {entry.trigger_type?.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2 pr-4 text-gray-400">{entry.erp_system}</td>
                    <td className="py-2 pr-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${STATUS_STYLES[entry.status] || STATUS_STYLES.pending}`}>
                        {entry.status}
                      </span>
                    </td>
                    <td className="py-2 text-right text-gray-600">
                      {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────

const PARTICLES = Array.from({ length: 20 }, (_, i) => ({
  id: i,
  size: 2 + Math.random() * 4,
  x: Math.random() * 100,
  y: Math.random() * 100,
  duration: 8 + Math.random() * 12,
  delay: Math.random() * 8,
}));

export default function ContractAISuite() {
  const [activeTab, setActiveTab] = useState('memory');
  const [tabKey, setTabKey] = useState(0);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setTabKey((k) => k + 1);
  };

  return (
    <div className="min-h-screen text-gray-100 p-6" style={{ background: 'linear-gradient(135deg, #0a0f1e 0%, #0d1117 50%, #111827 100%)' }}>
      {/* Animated grid overlay */}
      <div className="fixed inset-0 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px)',
        backgroundSize: '60px 60px',
        zIndex: 0,
      }} />
      {/* Floating particles */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
        {PARTICLES.map((p) => (
          <div
            key={p.id}
            style={{
              position: 'absolute',
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              background: p.id % 3 === 0 ? 'rgba(6,182,212,0.4)' : p.id % 3 === 1 ? 'rgba(124,58,237,0.4)' : 'rgba(16,185,129,0.3)',
              animation: `float ${p.duration}s ${p.delay}s infinite ease-in-out`,
              filter: 'blur(1px)',
            }}
          />
        ))}
      </div>
      {/* Radial glow top-left */}
      <div className="fixed pointer-events-none" style={{ top: '-200px', left: '-200px', width: 600, height: 600, borderRadius: '50%', background: 'radial-gradient(circle, rgba(124,58,237,0.06) 0%, transparent 70%)', zIndex: 0 }} />
      {/* Radial glow bottom-right */}
      <div className="fixed pointer-events-none" style={{ bottom: '-200px', right: '-200px', width: 600, height: 600, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%)', zIndex: 0 }} />

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-xl" style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 30px rgba(6,182,212,0.3)' }}>
              ✦
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight" style={{ background: 'linear-gradient(135deg, #a78bfa, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Contract AI Suite
              </h1>
              <p className="text-gray-500 text-sm mt-0.5">Platform-wide Intelligence Layer</p>
            </div>
            <div className="ml-auto flex items-center gap-3">
              {[
                { label: '9 AI Modules', color: 'rgba(124,58,237,0.15)', border: 'rgba(124,58,237,0.3)', text: '#a78bfa' },
                { label: 'Platform-Wide', color: 'rgba(6,182,212,0.1)', border: 'rgba(6,182,212,0.25)', text: '#06b6d4' },
                { label: 'Real-Time', color: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.25)', text: '#10b981' },
              ].map((pill) => (
                <span key={pill.label} className="text-xs px-3 py-1.5 rounded-full font-semibold flex items-center gap-1.5"
                  style={{ background: pill.color, border: `1px solid ${pill.border}`, color: pill.text }}>
                  <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: pill.text }} />
                  {pill.label}
                </span>
              ))}
            </div>
          </div>

          {/* Tabs */}
          <TabBar activeTab={activeTab} onTabChange={handleTabChange} />
        </div>

        {/* Tab Content with animation */}
        <div key={tabKey} style={{ animation: 'tabEnter 0.3s ease-out' }}>
          {activeTab === 'memory' && <StrategyMemoryTab />}
          {activeTab === 'monitoring' && <MonitoringTab />}
          {activeTab === 'rl' && <RLTab />}
          {activeTab === 'benchmarking' && <BenchmarkingTab />}
          {activeTab === 'temporal' && <TemporalTab />}
          {activeTab === 'risk-margin' && <RiskMarginTab />}
          {activeTab === 'supplier-heatmap' && <SupplierHeatmapTab />}
          {activeTab === 'dispute-timeline' && <DisputeTimelineTab />}
          {activeTab === 'clause-volatility' && <ClauseVolatilityTab />}
          {activeTab === 'erp-execution' && <ERPExecutionTab />}
        </div>
      </div>
    </div>
  );
}
