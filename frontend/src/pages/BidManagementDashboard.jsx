/**
 * Bid Management Dashboard — Premium Redesign
 * Route: /tenders/:id/bid-management
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import tenderService from '../services/tenderService';
import bidActionsService from '../services/bidActionsService';

// ─── Constants ──────────────────────────────────────────────────────────────
const DEPARTMENTS = [
  { key: 'Civil',       color: 'bg-blue-900/50 text-blue-300 border-blue-700/50',       dot: 'bg-blue-400',    hex: '#3b82f6' },
  { key: 'Mechanical',  color: 'bg-orange-900/50 text-orange-300 border-orange-700/50',  dot: 'bg-orange-400',  hex: '#f97316' },
  { key: 'Electrical',  color: 'bg-yellow-900/50 text-yellow-300 border-yellow-700/50',  dot: 'bg-yellow-400',  hex: '#eab308' },
  { key: 'MEP',         color: 'bg-cyan-900/50 text-cyan-300 border-cyan-700/50',        dot: 'bg-cyan-400',    hex: '#06b6d4' },
  { key: 'Legal',       color: 'bg-red-900/50 text-red-300 border-red-700/50',           dot: 'bg-red-400',     hex: '#ef4444' },
  { key: 'Finance',     color: 'bg-green-900/50 text-green-300 border-green-700/50',     dot: 'bg-green-400',   hex: '#22c55e' },
  { key: 'HSE',         color: 'bg-rose-900/50 text-rose-300 border-rose-700/50',        dot: 'bg-rose-400',    hex: '#f43f5e' },
  { key: 'Planning',    color: 'bg-purple-900/50 text-purple-300 border-purple-700/50',  dot: 'bg-purple-400',  hex: '#a855f7' },
  { key: 'Procurement', color: 'bg-indigo-900/50 text-indigo-300 border-indigo-700/50',  dot: 'bg-indigo-400',  hex: '#6366f1' },
  { key: 'QA/QC',       color: 'bg-teal-900/50 text-teal-300 border-teal-700/50',        dot: 'bg-teal-400',    hex: '#14b8a6' },
  { key: 'Signaling',   color: 'bg-pink-900/50 text-pink-300 border-pink-700/50',        dot: 'bg-pink-400',    hex: '#ec4899' },
];
const DEPT_MAP = Object.fromEntries(DEPARTMENTS.map(d => [d.key, d]));

const PRIORITY_META = {
  Critical: { cls: 'bg-red-900/60 text-red-300 border border-red-700/50',       dot: 'bg-red-400' },
  High:     { cls: 'bg-orange-900/60 text-orange-300 border border-orange-700/50', dot: 'bg-orange-400' },
  Medium:   { cls: 'bg-amber-900/60 text-amber-300 border border-amber-700/50',  dot: 'bg-amber-400' },
  Low:      { cls: 'bg-slate-700/60 text-slate-300 border border-slate-600/50',  dot: 'bg-slate-400' },
};

const STATUS_CYCLE = ['Pending', 'In Progress', 'Review', 'Completed', 'Blocked'];
const STATUS_META_ITEM = {
  Pending:      { cls: 'bg-slate-700/60 text-slate-300 border-slate-600/50',       dot: 'bg-slate-400' },
  'In Progress':{ cls: 'bg-blue-900/60 text-blue-300 border-blue-700/50',          dot: 'bg-blue-400 animate-pulse' },
  Review:       { cls: 'bg-amber-900/60 text-amber-300 border-amber-700/50',       dot: 'bg-amber-400' },
  Completed:    { cls: 'bg-emerald-900/60 text-emerald-300 border-emerald-700/50', dot: 'bg-emerald-400' },
  Blocked:      { cls: 'bg-red-900/60 text-red-300 border-red-700/50',             dot: 'bg-red-400' },
};

const STATUS_COLORS_TENDER = {
  DRAFT:     'bg-slate-700/60 text-slate-300 border-slate-600',
  ANALYZING: 'bg-amber-900/40 text-amber-300 border-amber-700/50',
  ANALYZED:  'bg-emerald-900/40 text-emerald-300 border-emerald-700/50',
  BIDDING:   'bg-blue-900/40 text-blue-300 border-blue-700/50',
  SUBMITTED: 'bg-purple-900/40 text-purple-300 border-purple-700/50',
  WON:       'bg-green-900/40 text-green-300 border-green-700/50',
  LOST:      'bg-red-900/40 text-red-300 border-red-700/50',
};

const RISK_CASCADE = {
  Civil:       [{ to: 'Mechanical', weight: 0.7 }, { to: 'Planning', weight: 0.5 }],
  Mechanical:  [{ to: 'Electrical', weight: 0.6 }, { to: 'MEP', weight: 0.5 }],
  Electrical:  [{ to: 'MEP', weight: 0.5 }, { to: 'Finance', weight: 0.4 }],
  MEP:         [{ to: 'QA/QC', weight: 0.4 }, { to: 'HSE', weight: 0.3 }],
  Legal:       [{ to: 'Finance', weight: 0.7 }, { to: 'Procurement', weight: 0.4 }],
  Planning:    [{ to: 'Procurement', weight: 0.5 }, { to: 'Finance', weight: 0.4 }],
  Procurement: [{ to: 'Finance', weight: 0.5 }],
  HSE:         [{ to: 'QA/QC', weight: 0.4 }],
};

// ─── Logic helpers ───────────────────────────────────────────────────────────
function propagateRisk(deptSummary) {
  const riskMap = {};
  deptSummary.forEach(d => { riskMap[d.key] = d.avgRisk; });
  const visited = new Set();
  function dfs(deptKey, accumulated) {
    if (visited.has(deptKey)) return;
    visited.add(deptKey);
    (RISK_CASCADE[deptKey] || []).forEach(({ to, weight }) => {
      const propagated = accumulated * weight;
      if (riskMap[to] !== undefined) riskMap[to] = Math.min(0.99, riskMap[to] + propagated);
      dfs(to, propagated);
    });
  }
  Object.keys(riskMap).sort((a, b) => riskMap[b] - riskMap[a]).forEach(k => dfs(k, riskMap[k]));
  return riskMap;
}

function generateActionItemsFromTender(tender) {
  const items = [];
  let idx = 1;
  const mk = (dept, title, desc, priority, risk, exposure) => ({
    id: idx++, department: dept, title, description: desc,
    priority, risk_score: risk, financial_exposure: exposure,
    status: 'Pending', source_type: 'Auto-generated',
  });
  const categoryDeptMap = { CIVIL: 'Civil', MECHANICAL: 'Mechanical', ELECTRICAL: 'Electrical', MEP: 'MEP', PLUMBING: 'MEP', HVAC: 'Mechanical', OTHER: 'Civil' };
  const tenderValue = parseFloat(tender.estimated_value || 0);
  (tender.work_items || []).forEach(wi => {
    const dept = categoryDeptMap[wi.category] || 'Civil';
    const itemCost = parseFloat(wi.estimated_cost || wi.final_unit_cost || 0);
    const capPerItem = tenderValue > 0 ? tenderValue * 0.30 : 1e9;
    const exp = Math.min(itemCost * 0.10, capPerItem);
    items.push(mk(dept, `BOQ: ${wi.description?.slice(0, 60) || 'Work Item'}`,
      `Prepare ${dept} BOQ submission for: ${wi.description || wi.item_code}`,
      itemCost > 5000000 ? 'High' : itemCost > 1000000 ? 'Medium' : 'Low',
      Math.min(0.9, itemCost / 50000000), exp));
  });
  const riskDeptMap = { UNLIMITED_LIABILITY: 'Legal', HIGH_LD: 'Legal', TERMINATION: 'Legal', PAYMENT_TERMS: 'Finance', PRICE_ESCALATION: 'Finance', FORCE_MAJEURE: 'Legal', INDEMNITY: 'Legal', INSURANCE: 'HSE', SAFETY: 'HSE', ENVIRONMENTAL: 'HSE', TECHNICAL: 'QA/QC', QUALITY: 'QA/QC' };
  (tender.risks || []).forEach(r => {
    const dept = riskDeptMap[r.risk_type] || 'Legal';
    const sevPriority = { CRITICAL: 'Critical', HIGH: 'High', MEDIUM: 'Medium', LOW: 'Low' };
    items.push(mk(dept, `Risk: ${r.risk_type?.replace(/_/g, ' ')}`,
      r.description || r.mitigation_suggestion || 'Review and mitigate identified risk',
      sevPriority[r.severity] || 'Medium',
      r.severity === 'CRITICAL' ? 0.9 : r.severity === 'HIGH' ? 0.7 : r.severity === 'MEDIUM' ? 0.4 : 0.2,
      parseFloat(r.financial_exposure || 0)));
  });
  (tender.negotiations || []).forEach(n => {
    items.push(mk('Finance', `Negotiation: ${n.issue_type?.replace(/_/g, ' ')}`,
      n.description || 'Prepare counter-proposal for negotiation point',
      n.acceptance_probability < 0.4 ? 'High' : 'Medium',
      1 - (n.acceptance_probability || 0.5), 0));
  });
  if (tender.eligibility) {
    const e = tender.eligibility;
    if (e.min_turnover) items.push(mk('Finance', 'Eligibility: Turnover Certificate', 'Prepare annual turnover documentation', 'High', 0.6, 0));
    if (e.similar_projects_required) items.push(mk('Procurement', 'Eligibility: Similar Work Experience', 'Compile similar project completion certificates', 'High', 0.6, 0));
    if (e.certifications) items.push(mk('QA/QC', 'Eligibility: Certifications', 'Gather required certifications and registrations', 'Medium', 0.3, 0));
  }
  items.push(mk('Planning', 'Prepare Bid Schedule Baseline', 'Develop CPM schedule baseline for bid submission using Primavera P6', 'High', 0.5, 0));
  items.push(mk('Procurement', 'Identify Long Lead Items', 'List imported/long-lead equipment and initiate vendor queries', 'Medium', 0.4, 0));
  items.push(mk('HSE', 'Prepare HSE Method Statement', 'Draft safety method statement and risk assessment matrix', 'Medium', 0.3, 0));
  items.push(mk('Legal', 'Review FIDIC Contract Conditions', 'Review general conditions of contract and flag deviations from FIDIC standard', 'Critical', 0.85, 0));
  items.push(mk('Signaling', 'Telecom & Signaling Scope Review', 'Identify ATC, telecom, fiber, and SCADA scope items for specialist subcontract', 'Medium', 0.4, 0));
  items.push(mk('Civil', 'Geotechnical Report Review', 'Analyse soil investigation reports and assess piling/foundation risks', 'High', 0.65, 0));
  items.push(mk('Electrical', 'Power Distribution Design Review', 'Review traction power, substation, and cable tray scope for bid costing', 'High', 0.6, 0));
  return items;
}

function computeReadiness(tender, actionItems) {
  const completedCount = actionItems.filter(a => a.status === 'Completed').length;
  const actionPct = actionItems.length > 0 ? (completedCount / actionItems.length) * 100 : 0;
  const steps = [
    { label: 'BOQ Items Extracted',        done: (tender.work_items?.length || 0) > 0 },
    { label: 'Risk Analysis Complete',     done: (tender.risks?.length || 0) > 0 },
    { label: 'Win Probability Calculated', done: (tender.bid_scenarios?.length || 0) > 0 },
    { label: 'Proposal Generated',         done: !!tender.proposal },
    { label: 'Negotiations Initiated',     done: (tender.negotiations?.length || 0) > 0 },
  ];
  const dataPct = Math.round((steps.filter(s => s.done).length / steps.length) * 100);
  const pct = Math.round(dataPct * 0.6 + actionPct * 0.4);
  return { steps, pct, dataPct, actionPct: Math.round(actionPct) };
}

function predictDelay(dept, avgRisk, count) {
  const BASE_DAYS = { Civil: 14, Mechanical: 10, Electrical: 8, MEP: 7, Legal: 5, Finance: 3, HSE: 4, Planning: 6, Procurement: 12, 'QA/QC': 5, Signaling: 10 };
  return Math.round((BASE_DAYS[dept] || 7) * (1 + avgRisk) * (1 + count * 0.02));
}

const fmtCr = (v) => `₹${(parseFloat(v || 0) / 10000000).toFixed(2)} Cr`;

// ─── Sub-components ──────────────────────────────────────────────────────────

const ReadinessGauge = ({ pct }) => {
  const r = 56, cx = 70, cy = 70;
  const circ = Math.PI * r;
  const dash = (pct / 100) * circ;
  const color = pct >= 80 ? '#10b981' : pct >= 50 ? '#f59e0b' : pct >= 25 ? '#f97316' : '#ef4444';
  const glow = pct >= 80 ? '#10b98140' : pct >= 50 ? '#f59e0b40' : '#f9731640';
  return (
    <div className="relative flex flex-col items-center">
      <svg width="140" height="90" viewBox="0 0 140 90">
        <defs>
          <filter id="gaugeglow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        {/* Track */}
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke="#1e293b" strokeWidth="10" strokeLinecap="round" />
        {/* Glow */}
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke={glow} strokeWidth="16" strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`} />
        {/* Fill */}
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`} filter="url(#gaugeglow)" style={{ transition: 'stroke-dasharray 0.8s ease' }} />
      </svg>
      <div className="absolute bottom-0 flex flex-col items-center">
        <span className="text-3xl font-bold text-white" style={{ color }}>{pct}%</span>
      </div>
    </div>
  );
};

const KpiCard = ({ title, value, sub, gradient, icon, badge }) => (
  <div className={`relative overflow-hidden rounded-2xl p-5 border border-white/5 ${gradient}`}>
    <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_white_0%,_transparent_60%)] pointer-events-none" />
    <div className="flex items-start justify-between gap-2">
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-white/50 mb-1.5">{title}</p>
        <p className="text-2xl font-bold text-white leading-none truncate">{value}</p>
        {sub && <p className="text-xs text-white/40 mt-1.5">{sub}</p>}
      </div>
      <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center shrink-0 text-lg">{icon}</div>
    </div>
    {badge && (
      <div className="absolute top-2 right-2">
        <span className="text-[10px] bg-white/10 text-white/70 px-1.5 py-0.5 rounded font-medium">{badge}</span>
      </div>
    )}
  </div>
);

const DependencyGraph = ({ deptSummary, propagatedRisk, selectedNode, setSelectedNode }) => {
  const W = 700, H = 420, CX = W / 2, CY = H / 2;
  const n = deptSummary.length;
  const nodes = deptSummary.map((dept, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    const radius = n <= 4 ? 130 : n <= 7 ? 150 : 170;
    return { ...dept, x: CX + radius * Math.cos(angle), y: CY + radius * Math.sin(angle), size: 18 + Math.min(dept.count * 2, 22) };
  });
  const nodeMap = Object.fromEntries(nodes.map(n => [n.key, n]));
  const edges = [];
  nodes.forEach(src => {
    (RISK_CASCADE[src.key] || []).forEach(({ to, weight }) => {
      if (nodeMap[to]) edges.push({ from: src.key, to, weight, src: nodeMap[src.key], tgt: nodeMap[to] });
    });
  });
  const selected = selectedNode ? nodeMap[selectedNode] : null;

  return (
    <div className="space-y-4">
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white">Department Dependency Graph</h2>
            <p className="text-xs text-slate-500 mt-0.5">Nodes sized by task count · Edges show risk propagation · Click to inspect</p>
          </div>
          {selectedNode && (
            <button onClick={() => setSelectedNode(null)} className="text-xs text-slate-400 hover:text-white px-3 py-1.5 bg-slate-700/50 border border-slate-600/40 rounded-xl transition-all">
              Clear selection
            </button>
          )}
        </div>
        {deptSummary.length === 0 ? (
          <div className="text-center py-16 text-slate-600">No departments with action items yet</div>
        ) : (
          <div className="overflow-x-auto">
            <svg width={W} height={H} className="mx-auto" style={{ maxWidth: '100%' }}>
              <defs>
                <marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill="#475569" />
                </marker>
                <marker id="arrowhl" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill="#a855f7" />
                </marker>
              </defs>
              {edges.map((e, i) => {
                const dx = e.tgt.x - e.src.x, dy = e.tgt.y - e.src.y;
                const len = Math.sqrt(dx*dx + dy*dy);
                const ux = dx/len, uy = dy/len;
                const isHL = selectedNode === e.from || selectedNode === e.to;
                return (
                  <g key={i}>
                    <line x1={e.src.x + ux*e.src.size} y1={e.src.y + uy*e.src.size}
                      x2={e.tgt.x - ux*(e.tgt.size+6)} y2={e.tgt.y - uy*(e.tgt.size+6)}
                      stroke={isHL ? '#a855f7' : '#334155'} strokeWidth={isHL ? 2.5 : 1.5}
                      strokeOpacity={isHL ? 1 : 0.6} strokeDasharray={e.weight < 0.5 ? '5,4' : undefined}
                      markerEnd={isHL ? 'url(#arrowhl)' : 'url(#arrow)'} />
                    <text x={(e.src.x+e.tgt.x)/2} y={(e.src.y+e.tgt.y)/2 - 5}
                      textAnchor="middle" fontSize="9" fill={isHL ? '#a855f7' : '#475569'}>
                      {Math.round(e.weight * 100)}%
                    </text>
                  </g>
                );
              })}
              {nodes.map(node => {
                const risk = propagatedRisk[node.key] || node.avgRisk;
                const isSelected = selectedNode === node.key;
                const ringColor = risk > 0.7 ? '#ef4444' : risk > 0.4 ? '#f97316' : '#22c55e';
                return (
                  <g key={node.key} onClick={() => setSelectedNode(isSelected ? null : node.key)} style={{ cursor: 'pointer' }}>
                    {isSelected && <circle cx={node.x} cy={node.y} r={node.size+10} fill="none" stroke="#a855f7" strokeWidth="1.5" strokeOpacity="0.4" strokeDasharray="3,3" />}
                    <circle cx={node.x} cy={node.y} r={node.size+4} fill="none" stroke={ringColor} strokeWidth="1.5" strokeOpacity="0.35" />
                    <circle cx={node.x} cy={node.y} r={node.size} fill={node.hex+'25'} stroke={node.hex} strokeWidth={isSelected ? 2.5 : 1.5} />
                    <text x={node.x} y={node.y-3} textAnchor="middle" dominantBaseline="middle" fontSize="10" fontWeight="600" fill="#e2e8f0">{node.key}</text>
                    <text x={node.x} y={node.y+10} textAnchor="middle" fontSize="8" fill="#64748b">{node.count}t</text>
                  </g>
                );
              })}
            </svg>
          </div>
        )}
      </div>

      {selected && (
        <div className="bg-slate-800/50 border border-purple-600/30 rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-4">
            <span className={`w-3 h-3 rounded-full ${selected.dot}`} />
            <h3 className="text-sm font-semibold text-white">{selected.key} Department</h3>
            <span className="ml-auto text-xs text-slate-500">Selected node</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {[
              { label: 'Action Items', val: selected.count, color: 'text-white' },
              { label: 'Completed',    val: selected.completed, color: 'text-emerald-400' },
              { label: 'Prop. Risk',   val: `${Math.round((propagatedRisk[selected.key] || 0) * 100)}%`, color: (propagatedRisk[selected.key]||0) > 0.7 ? 'text-red-400' : 'text-orange-400' },
              { label: 'Delay Est.',   val: `~${predictDelay(selected.key, propagatedRisk[selected.key]||selected.avgRisk, selected.count)}d`, color: 'text-amber-400' },
            ].map(item => (
              <div key={item.label} className="bg-slate-900/50 rounded-xl p-3">
                <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-1">{item.label}</p>
                <p className={`text-xl font-bold ${item.color}`}>{item.val}</p>
              </div>
            ))}
          </div>
          {(RISK_CASCADE[selected.key] || []).length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-2">Cascades risk to:</p>
              <div className="flex gap-2 flex-wrap">
                {(RISK_CASCADE[selected.key] || []).map(e => {
                  const td = DEPT_MAP[e.to];
                  return <span key={e.to} className={`text-xs px-3 py-1 rounded-full border ${td?.color || 'bg-slate-700 text-slate-300'}`}>{e.to} — {Math.round(e.weight*100)}%</span>;
                })}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-4">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-3">Legend</p>
        <div className="flex flex-wrap gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1.5"><span className="w-6 h-px bg-slate-500 inline-block" />Solid = strong cascade (≥50%)</span>
          <span className="flex items-center gap-1.5"><span className="w-6 h-px border-t border-dashed border-slate-500 inline-block" />Dashed = weak (&lt;50%)</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-red-500 inline-block" />High risk</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-orange-500 inline-block" />Med risk</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-emerald-500 inline-block" />Low risk</span>
        </div>
      </div>
    </div>
  );
};

// ─── Main Component ──────────────────────────────────────────────────────────
const BidManagementDashboard = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [tender, setTender]           = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [activeTab, setActiveTab]     = useState(0);
  const [deptFilter, setDeptFilter]   = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [statusFilter, setStatusFilter]     = useState('All');
  const [itemStatuses, setItemStatuses]     = useState({});
  const [selectedNode, setSelectedNode]     = useState(null);
  const [allTenders, setAllTenders]         = useState([]);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioSort, setPortfolioSort]   = useState('value');
  const [portfolioSearch, setPortfolioSearch] = useState('');
  const [backendActions, setBackendActions] = useState([]);
  const [useBackend, setUseBackend]         = useState(false);
  const [generating, setGenerating]         = useState(false);

  useEffect(() => { if (id) loadTender(); }, [id]);
  useEffect(() => { if (id && useBackend) loadBackendActions(); }, [id, useBackend]);
  useEffect(() => {
    if (!id) return;
    try { const s = sessionStorage.getItem(`bid_statuses_${id}`); if (s) setItemStatuses(JSON.parse(s)); } catch (_) {}
  }, [id]);

  const saveStatuses = useCallback((ns) => {
    setItemStatuses(ns);
    try { sessionStorage.setItem(`bid_statuses_${id}`, JSON.stringify(ns)); } catch (_) {}
  }, [id]);

  const loadTender = async () => {
    try { setLoading(true); const d = await tenderService.getTenderDetails(id); setTender(d); }
    catch { setError('Failed to load tender details'); }
    finally { setLoading(false); }
  };

  const loadPortfolio = async () => {
    if (allTenders.length > 0) return;
    try {
      setPortfolioLoading(true);
      const data = await tenderService.getAllTenders();
      const list = Array.isArray(data) ? data : (data.results || []);
      const detailed = await Promise.all(list.map(t => tenderService.getTenderDetails(t.id).catch(() => t)));
      setAllTenders(detailed);
    } catch { setAllTenders([]); }
    finally { setPortfolioLoading(false); }
  };

  const generateBackendActions = async () => {
    try {
      setGenerating(true);
      await bidActionsService.generateTenderActions(id);
      await loadBackendActions();
      setUseBackend(true);
    } catch { alert('Failed to generate actions. Using local generation.'); }
    finally { setGenerating(false); }
  };

  const loadBackendActions = async () => {
    try { const a = await bidActionsService.getTenderActions(id); setBackendActions(a); }
    catch { setBackendActions([]); }
  };

  // ── Loading ──
  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-4">
          <div className="absolute inset-0 rounded-full border-2 border-violet-500/20" />
          <div className="absolute inset-0 rounded-full border-t-2 border-violet-500 animate-spin" />
        </div>
        <p className="text-slate-500 text-sm">Loading Bid Management…</p>
      </div>
    </div>
  );

  if (error || !tender) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="bg-red-900/20 border border-red-700/30 rounded-2xl p-8 text-center">
        <p className="text-red-400 mb-4">{error || 'Tender not found'}</p>
        <button onClick={() => navigate('/tenders')} className="px-5 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-xl text-sm">Back to Tenders</button>
      </div>
    </div>
  );

  // ── Derived data ──
  const rawItems = generateActionItemsFromTender(tender);
  const actionItems = rawItems.map(item => ({ ...item, status: itemStatuses[item.id] || item.status }));
  const cycleStatus = (itemId) => {
    const cur = itemStatuses[itemId] || 'Pending';
    saveStatuses({ ...itemStatuses, [itemId]: STATUS_CYCLE[(STATUS_CYCLE.indexOf(cur) + 1) % STATUS_CYCLE.length] });
  };

  const { steps: readinessSteps, pct: readinessPct, dataPct, actionPct } = computeReadiness(tender, actionItems);
  const deptSummary = DEPARTMENTS.map(dept => {
    const di = actionItems.filter(a => a.department === dept.key);
    const exposure = di.reduce((s, a) => s + (a.financial_exposure || 0), 0);
    const avgRisk  = di.length ? di.reduce((s, a) => s + a.risk_score, 0) / di.length : 0;
    return { ...dept, count: di.length, exposure, avgRisk, completed: di.filter(a => a.status === 'Completed').length };
  }).filter(d => d.count > 0);

  const propagatedRisk = propagateRisk(deptSummary);
  const filteredActions = actionItems.filter(a =>
    (deptFilter === 'All' || a.department === deptFilter) &&
    (priorityFilter === 'All' || a.priority === priorityFilter) &&
    (statusFilter === 'All' || a.status === statusFilter)
  );

  const bestWinProb = tender.bid_scenarios?.length
    ? Math.max(...tender.bid_scenarios.map(s => parseFloat(s.win_probability || 0))) : 0;
  const rawTotalExposure = actionItems.reduce((s, a) => s + (a.financial_exposure || 0), 0);
  const tenderEstValue = parseFloat(tender.estimated_value || 0);
  const totalExposure = tenderEstValue > 0 ? Math.min(rawTotalExposure, tenderEstValue) : rawTotalExposure;
  const completedCount = actionItems.filter(a => a.status === 'Completed').length;
  const criticalCount  = actionItems.filter(a => a.priority === 'Critical' && a.status !== 'Completed').length;

  const TABS = [
    { label: 'Overview',      icon: <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg> },
    { label: 'Action Items',  icon: <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>, badge: actionItems.filter(a=>a.status!=='Completed').length },
    { label: 'Analytics',     icon: <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg> },
    { label: 'Risk Cascade',  icon: <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg> },
    { label: 'Dep. Graph',    icon: <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg> },
    { label: 'How It Works',  icon: <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> },
    { label: 'Portfolio',     icon: <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg> },
  ];

  return (
    <div className="min-h-screen bg-slate-950">

      {/* ══ Hero Header ══════════════════════════════════════════════ */}
      <div className="relative overflow-hidden bg-gradient-to-b from-violet-950/60 via-slate-900 to-slate-950 border-b border-slate-800/60">
        <div className="absolute -top-32 -left-16 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-0 right-0 w-80 h-80 bg-purple-600/8 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-6 pt-5 pb-0">
          {/* Breadcrumb */}
          <button onClick={() => navigate(`/tenders/${id}`)}
            className="flex items-center gap-1.5 text-slate-500 hover:text-violet-400 text-sm mb-4 transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Tender
          </button>

          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-5">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center shadow-lg shadow-violet-900/50">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <span className="text-violet-400 text-xs font-bold uppercase tracking-widest">Bid Management</span>
                {tender.reference_number && (
                  <span className="text-[11px] text-slate-500 font-mono bg-slate-800/60 border border-slate-700/40 px-2.5 py-1 rounded-lg">{tender.reference_number}</span>
                )}
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${STATUS_COLORS_TENDER[tender.status] || STATUS_COLORS_TENDER.DRAFT}`}>
                  {tender.status}
                </span>
              </div>
              <h1 className="text-xl lg:text-2xl font-bold text-white leading-tight truncate">{tender.title}</h1>
              <p className="text-slate-500 text-sm mt-1">Enterprise bid orchestration — departments, actions, risk propagation &amp; dependency graph</p>
            </div>

            <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
              {tender.estimated_value && (
                <div className="bg-emerald-900/30 border border-emerald-700/30 rounded-xl px-3.5 py-2 text-center">
                  <p className="text-[10px] text-emerald-500 uppercase tracking-wider">Contract Value</p>
                  <p className="text-base font-bold text-emerald-300">{fmtCr(tender.estimated_value)}</p>
                </div>
              )}
              <button onClick={() => { setActiveTab(6); loadPortfolio(); }}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all ${
                  activeTab === 6 ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-800/60 border-slate-700/40 text-slate-400 hover:text-white hover:bg-slate-700/60'
                }`}>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Portfolio
              </button>
              <button onClick={generateBackendActions} disabled={generating}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all shadow-md ${
                  generating ? 'bg-slate-700 text-slate-400 cursor-not-allowed' :
                  useBackend ? 'bg-gradient-to-r from-emerald-600 to-green-600 text-white shadow-emerald-900/40' :
                  'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-900/40'
                }`}>
                {generating ? (
                  <><div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />Generating…</>
                ) : useBackend ? (
                  <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>Backend Active</>
                ) : (
                  <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>Generate Actions</>
                )}
              </button>
            </div>
          </div>

          {/* ── Tabs ── */}
          <div className="flex items-center gap-0.5 overflow-x-auto pb-0 scrollbar-none">
            {TABS.map((tab, i) => (
              <button key={i} onClick={() => setActiveTab(i)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-xs font-semibold whitespace-nowrap transition-all relative
                  ${activeTab === i
                    ? 'bg-slate-950 text-white border-t border-l border-r border-slate-700/60 -mb-px z-10'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/40'
                  }`}>
                <span className={activeTab === i ? 'text-violet-400' : ''}>{tab.icon}</span>
                {tab.label}
                {tab.badge > 0 && (
                  <span className="w-4 h-4 rounded-full bg-violet-500/30 text-violet-300 text-[10px] font-bold flex items-center justify-center">
                    {tab.badge > 9 ? '9+' : tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ══ Content ══════════════════════════════════════════════════ */}
      <div className="max-w-7xl mx-auto px-6 py-6">

        {/* ── TAB 0: Overview ── */}
        {activeTab === 0 && (
          <div className="space-y-6">
            {/* Top row: gauge + KPIs */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Readiness */}
              <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-6 flex flex-col items-center ring-1 ring-violet-500/10">
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-3">Bid Readiness Index</p>
                <ReadinessGauge pct={readinessPct} />
                <div className="flex gap-6 mt-3 text-center">
                  <div><div className="text-sm font-bold text-blue-400">{dataPct}%</div><div className="text-[10px] text-slate-600">Data Ready</div></div>
                  <div><div className="text-sm font-bold text-violet-400">{actionPct}%</div><div className="text-[10px] text-slate-600">Tasks Done</div></div>
                </div>
                <div className="w-full mt-5 space-y-2">
                  {readinessSteps.map((step, i) => (
                    <div key={i} className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs ${step.done ? 'bg-emerald-900/20 border border-emerald-700/20' : 'bg-slate-700/20'}`}>
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${step.done ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-500'}`}>
                        {step.done ? '✓' : i+1}
                      </div>
                      <span className={step.done ? 'text-emerald-300' : 'text-slate-600'}>{step.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* KPI grid */}
              <div className="lg:col-span-2 grid grid-cols-2 gap-3">
                <KpiCard title="Total Actions"      value={actionItems.length}               sub={`${completedCount} completed`}    gradient="bg-gradient-to-br from-blue-900/50 to-slate-900"    icon="📋" />
                <KpiCard title="Win Probability"    value={`${bestWinProb.toFixed(1)}%`}     sub="Best bid scenario"                gradient="bg-gradient-to-br from-emerald-900/50 to-slate-900"  icon="🎯" />
                <KpiCard title="Financial Exposure" value={fmtCr(totalExposure)}             sub="BOQ risk contingency (10%)"       gradient="bg-gradient-to-br from-amber-900/50 to-slate-900"    icon="💰" />
                <KpiCard title="Critical Pending"   value={criticalCount}                    sub={criticalCount > 0 ? 'Need urgent attention' : 'All critical done'} gradient={criticalCount > 0 ? 'bg-gradient-to-br from-red-900/50 to-slate-900' : 'bg-gradient-to-br from-green-900/40 to-slate-900'} icon="🚨" />
              </div>
            </div>

            {/* Progress bar */}
            <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-white">Overall Task Completion</span>
                <span className="text-sm font-bold text-slate-300">{completedCount} / {actionItems.length}</span>
              </div>
              <div className="h-2.5 bg-slate-700/60 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-violet-600 via-purple-500 to-emerald-500 rounded-full transition-all duration-700"
                  style={{ width: `${actionItems.length > 0 ? (completedCount / actionItems.length) * 100 : 0}%` }} />
              </div>
              <div className="flex gap-2 mt-3 flex-wrap">
                {STATUS_CYCLE.map(s => {
                  const cnt = actionItems.filter(a => a.status === s).length;
                  return cnt > 0 ? (
                    <span key={s} className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border ${STATUS_META_ITEM[s]?.cls}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${STATUS_META_ITEM[s]?.dot}`} />{s}: {cnt}
                    </span>
                  ) : null;
                })}
              </div>
            </div>

            {/* Department cards */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-white">Department Breakdown</h2>
                <p className="text-xs text-slate-500">Click a department to filter Action Items</p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
                {deptSummary.map(dept => {
                  const propRisk = propagatedRisk[dept.key] || dept.avgRisk;
                  const riskColor = propRisk > 0.7 ? 'text-red-400' : propRisk > 0.4 ? 'text-orange-400' : 'text-emerald-400';
                  const pct = dept.count > 0 ? (dept.completed / dept.count) * 100 : 0;
                  return (
                    <div key={dept.key} onClick={() => { setDeptFilter(dept.key); setActiveTab(1); }}
                      className="group bg-slate-800/50 border border-slate-700/40 rounded-2xl p-4 hover:border-violet-500/40 hover:bg-slate-800/70 cursor-pointer transition-all hover:shadow-lg hover:shadow-violet-950/30">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className={`w-2.5 h-2.5 rounded-full ${dept.dot}`} />
                          <span className="text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">{dept.key}</span>
                        </div>
                        <span className={`text-xs font-semibold ${riskColor}`}>{Math.round(propRisk * 100)}%</span>
                      </div>
                      <div className="text-2xl font-bold text-white mb-0.5">{dept.count}</div>
                      <div className="text-[11px] text-slate-500 mb-3">
                        {dept.completed}/{dept.count} done
                        {dept.exposure > 0 && <> · <span className="text-emerald-500">{fmtCr(dept.exposure)}</span></>}
                      </div>
                      <div className="h-1.5 bg-slate-700/60 rounded-full overflow-hidden">
                        <div className="h-full bg-violet-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 1: Action Items ── */}
        {activeTab === 1 && (
          <div className="space-y-4">
            {/* Filters */}
            <div className="flex flex-wrap gap-2 items-center bg-slate-800/40 border border-slate-700/40 rounded-2xl p-4">
              {[
                { val: deptFilter, set: setDeptFilter, opts: ['All', ...DEPARTMENTS.map(d=>d.key)], label: 'Department' },
                { val: priorityFilter, set: setPriorityFilter, opts: ['All','Critical','High','Medium','Low'], label: 'Priority' },
                { val: statusFilter, set: setStatusFilter, opts: ['All', ...STATUS_CYCLE], label: 'Status' },
              ].map(f => (
                <select key={f.label} value={f.val} onChange={e => f.set(e.target.value)}
                  className="px-3 py-2 bg-slate-900/60 border border-slate-700/50 text-white text-xs rounded-xl focus:ring-2 focus:ring-violet-500/50">
                  <option value="All">All {f.label}s</option>
                  {f.opts.filter(o=>o!=='All').map(o=><option key={o} value={o}>{o}</option>)}
                </select>
              ))}
              <span className="text-xs text-slate-500 ml-1">{filteredActions.length} items</span>
              <button onClick={() => saveStatuses({})}
                className="ml-auto text-xs px-3 py-2 bg-slate-700/50 hover:bg-slate-600/60 text-slate-400 hover:text-white border border-slate-600/30 rounded-xl transition-all">
                Reset Statuses
              </button>
            </div>

            <p className="text-xs text-slate-600 px-1">Click the status badge on any item to cycle: Pending → In Progress → Review → Completed → Blocked</p>

            <div className="space-y-2">
              {filteredActions.length === 0 ? (
                <div className="text-center py-16 text-slate-600 bg-slate-800/30 rounded-2xl border border-slate-700/30">No action items match your filters</div>
              ) : filteredActions.map(item => {
                const deptCfg = DEPT_MAP[item.department];
                const smItem = STATUS_META_ITEM[item.status] || STATUS_META_ITEM.Pending;
                const pmItem = PRIORITY_META[item.priority] || PRIORITY_META.Low;
                const isCompleted = item.status === 'Completed';
                const isBlocked   = item.status === 'Blocked';
                return (
                  <div key={item.id} className={`group bg-slate-800/50 border rounded-2xl p-4 transition-all ${
                    isCompleted ? 'border-emerald-700/20 opacity-70' :
                    isBlocked   ? 'border-red-700/30 bg-red-950/10' :
                    'border-slate-700/40 hover:border-slate-600/60'
                  }`}>
                    <div className="flex items-start gap-3">
                      <span className={`mt-1.5 w-2.5 h-2.5 rounded-full shrink-0 ${deptCfg?.dot || 'bg-slate-500'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${deptCfg?.color || 'bg-slate-700 text-slate-300'}`}>
                            {item.department}
                          </span>
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${pmItem.cls}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${pmItem.dot}`} />{item.priority}
                          </span>
                          <button onClick={() => cycleStatus(item.id)}
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border cursor-pointer hover:opacity-80 transition-opacity ${smItem.cls}`}
                            title="Click to change status">
                            <span className={`w-1.5 h-1.5 rounded-full ${smItem.dot}`} />{item.status} ↻
                          </button>
                          <span className="text-[10px] text-slate-600 bg-slate-800/60 border border-slate-700/30 px-1.5 py-0.5 rounded">{item.source_type}</span>
                        </div>
                        <h4 className={`text-sm font-semibold mb-1 ${isCompleted ? 'line-through text-slate-600' : 'text-white'}`}>{item.title}</h4>
                        <p className="text-xs text-slate-500 line-clamp-2 mb-2">{item.description}</p>
                        <div className="flex items-center gap-4 flex-wrap">
                          <span className="text-xs text-slate-600">
                            Risk: <span className={item.risk_score > 0.7 ? 'text-red-400 font-semibold' : item.risk_score > 0.4 ? 'text-amber-400' : 'text-emerald-400'}>
                              {Math.round(item.risk_score * 100)}%
                            </span>
                          </span>
                          {item.financial_exposure > 0 && (
                            <span className="text-xs text-slate-600">
                              Exposure: <span className="text-emerald-400 font-semibold">{fmtCr(item.financial_exposure)}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── TAB 2: Analytics ── */}
        {activeTab === 2 && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Win Probability */}
              <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                <h3 className="text-sm font-bold text-white mb-4">Win Probability by Scenario</h3>
                {(tender.bid_scenarios || []).length === 0 ? (
                  <div className="text-center py-10 text-slate-600 text-sm">Run Win Simulation in Tender Analysis tab</div>
                ) : (
                  <div className="space-y-3">
                    {tender.bid_scenarios.map((s, i) => {
                      const wp = parseFloat(s.win_probability || 0);
                      const color = wp >= 70 ? 'from-emerald-600 to-green-500' : wp >= 50 ? 'from-blue-600 to-cyan-500' : 'from-orange-600 to-amber-500';
                      return (
                        <div key={i}>
                          <div className="flex justify-between text-xs mb-1.5">
                            <span className="text-slate-400">Margin {s.margin_percentage}%</span>
                            <span className="text-white font-bold">{wp.toFixed(1)}%</span>
                          </div>
                          <div className="h-2 bg-slate-700/60 rounded-full overflow-hidden">
                            <div className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-700`} style={{ width: `${Math.min(100, wp)}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Risk Heatmap */}
              <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                <h3 className="text-sm font-bold text-white mb-4">Risk Heatmap by Department</h3>
                <div className="space-y-2.5">
                  {deptSummary.map(dept => {
                    const rColor = dept.avgRisk > 0.7 ? 'from-red-600 to-red-500' : dept.avgRisk > 0.5 ? 'from-orange-600 to-orange-500' : dept.avgRisk > 0.3 ? 'from-amber-600 to-yellow-500' : 'from-emerald-600 to-green-500';
                    return (
                      <div key={dept.key} className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5 w-24 shrink-0">
                          <span className={`w-2 h-2 rounded-full ${dept.dot}`} />
                          <span className="text-xs text-slate-400">{dept.key}</span>
                        </div>
                        <div className="flex-1 h-2 bg-slate-700/60 rounded-full overflow-hidden">
                          <div className={`h-full bg-gradient-to-r ${rColor} rounded-full transition-all duration-700`} style={{ width: `${Math.max(4, Math.round(dept.avgRisk * 100))}%` }} />
                        </div>
                        <span className="text-xs font-semibold text-slate-400 w-8 text-right">{Math.round(dept.avgRisk * 100)}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Financial Exposure */}
              <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                <h3 className="text-sm font-bold text-white mb-4">Financial Exposure by Department</h3>
                {deptSummary.filter(d => d.exposure > 0).length === 0 ? (
                  <div className="text-center py-10 text-slate-600 text-sm">No BOQ cost data available yet</div>
                ) : (() => {
                  const sorted = deptSummary.filter(d => d.exposure > 0).sort((a, b) => b.exposure - a.exposure);
                  const maxExp = sorted[0]?.exposure || 1;
                  return (
                    <div className="space-y-2.5">
                      {sorted.map(dept => (
                        <div key={dept.key} className="flex items-center gap-3">
                          <div className="flex items-center gap-1.5 w-24 shrink-0">
                            <span className={`w-2 h-2 rounded-full ${dept.dot}`} />
                            <span className="text-xs text-slate-400">{dept.key}</span>
                          </div>
                          <div className="flex-1 h-2 bg-slate-700/60 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full transition-all duration-700" style={{ width: `${Math.max(4, (dept.exposure / maxExp) * 100)}%` }} />
                          </div>
                          <span className="text-xs font-semibold text-emerald-400 w-20 text-right">{fmtCr(dept.exposure)}</span>
                        </div>
                      ))}
                    </div>
                  );
                })()}
              </div>

              {/* Readiness checklist */}
              <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                <h3 className="text-sm font-bold text-white mb-4">Bid Readiness Checklist</h3>
                <div className="space-y-2">
                  {readinessSteps.map((step, i) => (
                    <div key={i} className={`flex items-center gap-3 px-3 py-2.5 rounded-xl ${step.done ? 'bg-emerald-900/20 border border-emerald-700/20' : 'bg-slate-700/20 border border-slate-600/20'}`}>
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 ${step.done ? 'bg-emerald-600 text-white' : 'bg-slate-600/60 text-slate-500'}`}>
                        {step.done ? '✓' : i+1}
                      </div>
                      <span className={`text-xs flex-1 ${step.done ? 'text-emerald-300' : 'text-slate-500'}`}>{step.label}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${step.done ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-700/30' : 'bg-slate-700/40 text-slate-600'}`}>
                        {step.done ? 'Done' : 'Pending'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 3: Risk Cascade ── */}
        {activeTab === 3 && (
          <div className="space-y-5">
            <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
              <div className="flex items-start gap-3 mb-5">
                <div className="w-9 h-9 rounded-xl bg-red-900/40 border border-red-700/30 flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white">Cross-Department Risk Propagation</h2>
                  <p className="text-xs text-slate-500 mt-0.5">Civil foundation delays → Mechanical shifts → Electrical commissioning shifts → Finance cashflow impact. Risk cascades and amplifies downstream.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
                {deptSummary.map(dept => {
                  const propagated = propagatedRisk[dept.key] || dept.avgRisk;
                  const amplified  = propagated - dept.avgRisk;
                  const edges      = RISK_CASCADE[dept.key] || [];
                  const delayDays  = predictDelay(dept.key, propagated, dept.count);
                  return (
                    <div key={dept.key} className="bg-slate-900/50 border border-slate-700/30 rounded-2xl p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className={`w-2.5 h-2.5 rounded-full ${dept.dot}`} />
                          <span className="text-sm font-semibold text-white">{dept.key}</span>
                        </div>
                        <span className="text-xs text-slate-500">{dept.count} tasks</span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        {[
                          { label: 'Base Risk', val: dept.avgRisk, color: dept.avgRisk > 0.7 ? 'from-red-600 to-red-500' : dept.avgRisk > 0.4 ? 'from-amber-600 to-yellow-500' : 'from-emerald-600 to-green-500', textColor: 'text-slate-300' },
                          { label: 'Propagated', val: propagated, color: propagated > 0.7 ? 'from-red-600 to-red-500' : propagated > 0.4 ? 'from-orange-600 to-orange-500' : 'from-amber-600 to-yellow-500', textColor: amplified > 0.01 ? 'text-red-400' : 'text-orange-400' },
                        ].map(item => (
                          <div key={item.label}>
                            <div className="text-[10px] text-slate-600 mb-1">{item.label}</div>
                            <div className="h-1.5 bg-slate-700/60 rounded-full overflow-hidden mb-1">
                              <div className={`h-full bg-gradient-to-r ${item.color} rounded-full`} style={{ width: `${Math.max(3, item.val * 100)}%` }} />
                            </div>
                            <div className={`text-xs font-semibold ${item.textColor}`}>{Math.round(item.val * 100)}%
                              {item.label === 'Propagated' && amplified > 0.01 && <span className="text-red-400 ml-1 text-[10px]">+{Math.round(amplified*100)}%</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="flex items-center justify-between text-xs mb-3">
                        <span className="text-slate-600">Predicted delay impact</span>
                        <span className={`font-bold ${delayDays > 14 ? 'text-red-400' : delayDays > 7 ? 'text-amber-400' : 'text-emerald-400'}`}>~{delayDays} days</span>
                      </div>
                      {edges.length > 0 && (
                        <div className="pt-2 border-t border-slate-700/30">
                          <p className="text-[10px] text-slate-600 mb-1.5">Cascades to:</p>
                          <div className="flex gap-1.5 flex-wrap">
                            {edges.map(e => {
                              const td = DEPT_MAP[e.to];
                              return <span key={e.to} className={`text-[11px] px-2 py-0.5 rounded-full border ${td?.color || 'bg-slate-700 text-slate-300'}`}>→ {e.to} ({Math.round(e.weight*100)}%)</span>;
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Summary table */}
              <div className="bg-slate-900/60 rounded-2xl border border-slate-700/40 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-700/40">
                  <h3 className="text-xs font-bold text-white">Risk Amplification Summary</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-700/40">
                        {['Department','Base Risk','Propagated','Amplification','Delay Est.'].map(h => (
                          <th key={h} className={`py-2.5 px-4 ${h==='Department' ? 'text-left' : 'text-right'}`}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {deptSummary.map(dept => {
                        const propagated = propagatedRisk[dept.key] || dept.avgRisk;
                        const amp   = propagated - dept.avgRisk;
                        const delay = predictDelay(dept.key, propagated, dept.count);
                        return (
                          <tr key={dept.key} className="border-b border-slate-700/20 hover:bg-slate-800/30 transition-colors">
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${dept.dot}`} />
                                <span className="text-slate-300 font-medium">{dept.key}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-right text-slate-500">{Math.round(dept.avgRisk*100)}%</td>
                            <td className={`py-3 px-4 text-right font-semibold ${propagated > 0.7 ? 'text-red-400' : propagated > 0.4 ? 'text-orange-400' : 'text-amber-400'}`}>{Math.round(propagated*100)}%</td>
                            <td className={`py-3 px-4 text-right font-semibold ${amp > 0.1 ? 'text-red-400' : amp > 0.02 ? 'text-orange-400' : 'text-slate-600'}`}>{amp > 0.005 ? `+${Math.round(amp*100)}%` : '—'}</td>
                            <td className={`py-3 px-4 text-right font-bold ${delay > 14 ? 'text-red-400' : delay > 7 ? 'text-amber-400' : 'text-emerald-400'}`}>~{delay}d</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 4: Dependency Graph ── */}
        {activeTab === 4 && (
          <DependencyGraph deptSummary={deptSummary} propagatedRisk={propagatedRisk} selectedNode={selectedNode} setSelectedNode={setSelectedNode} />
        )}

        {/* ── TAB 5: How It Works ── */}
        {activeTab === 5 && (
          <div className="space-y-5 max-w-4xl">
            <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-6">
              <h2 className="text-base font-bold text-white mb-1.5">Bid Management Architecture</h2>
              <p className="text-slate-500 text-sm mb-5">UniContractAI's Bid Management orchestrates cross-functional departments from tender analysis to final submission.</p>
              <div className="bg-slate-900/70 rounded-xl p-5 font-mono text-xs text-slate-400 mb-6 border border-slate-700/30 overflow-x-auto">
                <pre className="whitespace-pre leading-6">{`Tender Document (PDF)
       │
       ▼
┌──────────────────────────────┐
│   Clause + BOQ Extraction    │  ← LegalBERT + Table Parser
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Department Mapping Engine   │  ← Keyword rules + Risk categories
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│   Action Item Generator      │  ← BOQ + Risks + Negotiations
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Risk Propagation Engine     │  ← DFS cascade: Civil→Mechanical
│  Cross-Dept Cascade          │    →Electrical→MEP→Finance
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Bid Readiness Calculator    │  ← Data(60%) + Tasks(40%)
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Executive Dashboard (7 tabs)│  ← This page
└──────────────────────────────┘`}</pre>
              </div>
              <h3 className="text-sm font-bold text-white mb-4">Tab Guide</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  { step:'1', title:'Overview',      desc:'Bid Readiness gauge (data 60% + tasks 40%), department breakdown cards with task count, exposure and completion bars.', color:'bg-blue-600' },
                  { step:'2', title:'Action Items',  desc:'Auto-generated tasks from BOQ, Risks, Negotiations and Eligibility. Click status badge to cycle through 5 workflow states.', color:'bg-violet-600' },
                  { step:'3', title:'Analytics',     desc:'Win probability bars, risk heatmap, financial exposure per department, and readiness checklist.', color:'bg-emerald-600' },
                  { step:'4', title:'Risk Cascade',  desc:'DFS cross-department risk propagation. Civil delay cascades to Mechanical → Electrical → Finance with amplification % and delay estimates.', color:'bg-red-600' },
                  { step:'5', title:'Dep. Graph',    desc:'SVG network showing departments as nodes (sized by task count) connected by propagation edges. Click nodes for details.', color:'bg-orange-600' },
                  { step:'6', title:'Portfolio',     desc:'Cross-tender comparison showing pipeline value, exposure, risk, readiness and win probability across all tenders.', color:'bg-indigo-600' },
                ].map(item => (
                  <div key={item.step} className="flex gap-3 p-4 bg-slate-700/20 border border-slate-600/20 rounded-xl">
                    <span className={`w-7 h-7 rounded-lg ${item.color} flex items-center justify-center text-white text-xs font-bold shrink-0`}>{item.step}</span>
                    <div>
                      <h4 className="text-xs font-bold text-white mb-1">{item.title}</h4>
                      <p className="text-[11px] text-slate-500 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
              <h3 className="text-xs font-bold text-white mb-4 uppercase tracking-wider">Department Reference</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {DEPARTMENTS.map(dept => (
                  <div key={dept.key} className={`flex items-center gap-2 px-3 py-2 rounded-xl border ${dept.color}`}>
                    <span className={`w-2 h-2 rounded-full ${dept.dot}`} />
                    <span className="text-xs font-semibold">{dept.key}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 6: Portfolio ── */}
        {activeTab === 6 && (() => {
          if (portfolioLoading) return (
            <div className="flex items-center justify-center py-24">
              <div className="text-center">
                <div className="relative w-12 h-12 mx-auto mb-4">
                  <div className="absolute inset-0 rounded-full border-2 border-indigo-500/20" />
                  <div className="absolute inset-0 rounded-full border-t-2 border-indigo-500 animate-spin" />
                </div>
                <p className="text-slate-500 text-sm">Loading Portfolio…</p>
              </div>
            </div>
          );

          if (!allTenders.length) return (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/60 border border-slate-700/40 flex items-center justify-center text-3xl mb-4">🏛</div>
              <p className="text-slate-500 mb-4">No portfolio data loaded.</p>
              <button onClick={loadPortfolio} className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-900/30">
                Load Portfolio
              </button>
            </div>
          );

          const computeStats = (t) => {
            const items = generateActionItemsFromTender(t);
            const totalExposure = items.reduce((s, a) => s + a.financial_exposure, 0);
            const avgRisk = items.length ? items.reduce((s, a) => s + a.risk_score, 0) / items.length : 0;
            const criticalCount = items.filter(a => a.priority === 'Critical').length;
            const bestWinProb = t.bid_scenarios?.length ? Math.max(...t.bid_scenarios.map(s => parseFloat(s.win_probability || 0))) : 0;
            const checks = [(t.work_items?.length||0)>0,(t.risks?.length||0)>0,(t.bid_scenarios?.length||0)>0,!!t.proposal,(t.negotiations?.length||0)>0];
            const readiness = Math.round((checks.filter(Boolean).length / checks.length) * 100);
            return { totalExposure, avgRisk, criticalCount, bestWinProb, readiness, actionCount: items.length };
          };

          const tenderStats = allTenders.map(t => ({ tender: t, stats: computeStats(t) }));
          const totalValue  = allTenders.reduce((s, t) => s + parseFloat(t.estimated_value || 0), 0);
          const totalExpAll = tenderStats.reduce((s, ts) => s + ts.stats.totalExposure, 0);
          const avgRiskAll  = tenderStats.length ? tenderStats.reduce((s, ts) => s + ts.stats.avgRisk, 0) / tenderStats.length : 0;
          const avgReadAll  = tenderStats.length ? Math.round(tenderStats.reduce((s, ts) => s + ts.stats.readiness, 0) / tenderStats.length) : 0;
          const avgWinAll   = tenderStats.length ? tenderStats.reduce((s, ts) => s + ts.stats.bestWinProb, 0) / tenderStats.length : 0;
          const totalActAll = tenderStats.reduce((s, ts) => s + ts.stats.actionCount, 0);
          const totalCritAll= tenderStats.reduce((s, ts) => s + ts.stats.criticalCount, 0);
          const statusDist  = allTenders.reduce((acc, t) => { acc[t.status] = (acc[t.status]||0)+1; return acc; }, {});

          const deptRiskMap = {};
          tenderStats.forEach(ts => {
            generateActionItemsFromTender(ts.tender).forEach(item => {
              if (!deptRiskMap[item.department]) deptRiskMap[item.department] = [];
              deptRiskMap[item.department].push(item.risk_score);
            });
          });
          const deptRiskSummary = Object.entries(deptRiskMap)
            .map(([dept, scores]) => ({ dept, avgRisk: scores.reduce((a,b)=>a+b,0)/scores.length, count: scores.length }))
            .sort((a,b) => b.avgRisk - a.avgRisk).slice(0, 8);

          const portFiltered = tenderStats
            .filter(ts => !portfolioSearch || ts.tender.title?.toLowerCase().includes(portfolioSearch.toLowerCase()))
            .sort((a,b) => {
              if (portfolioSort === 'value')     return parseFloat(b.tender.estimated_value||0) - parseFloat(a.tender.estimated_value||0);
              if (portfolioSort === 'risk')      return b.stats.avgRisk - a.stats.avgRisk;
              if (portfolioSort === 'readiness') return b.stats.readiness - a.stats.readiness;
              if (portfolioSort === 'win')       return b.stats.bestWinProb - a.stats.bestWinProb;
              return new Date(b.tender.created_at) - new Date(a.tender.created_at);
            });

          return (
            <div className="space-y-5">
              {/* Portfolio Header */}
              <div className="relative overflow-hidden bg-gradient-to-r from-indigo-900/40 via-violet-900/30 to-slate-900 border border-indigo-700/20 rounded-2xl p-5">
                <div className="absolute inset-0 opacity-5 bg-[radial-gradient(ellipse_at_top_right,_white_0%,_transparent_60%)]" />
                <div className="relative flex items-center justify-between flex-wrap gap-3">
                  <div>
                    <div className="flex items-center gap-2.5 mb-1">
                      <span className="text-indigo-400 text-xs font-bold uppercase tracking-widest">Portfolio Intelligence</span>
                      <span className="text-[11px] bg-indigo-900/60 border border-indigo-700/40 text-indigo-300 px-2 py-0.5 rounded-full">{allTenders.length} Tenders</span>
                    </div>
                    <p className="text-slate-500 text-sm">Cross-tender risk, readiness and win probability intelligence</p>
                  </div>
                  <button onClick={() => { setAllTenders([]); loadPortfolio(); }}
                    className="flex items-center gap-1.5 px-3 py-2 bg-slate-700/50 hover:bg-slate-600/60 border border-slate-600/30 text-slate-400 hover:text-white rounded-xl text-xs transition-all">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                    Refresh
                  </button>
                </div>
              </div>

              {/* KPI strip */}
              <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
                {[
                  { label: 'Total Tenders',  value: allTenders.length,                          gradient: 'bg-gradient-to-br from-slate-800 to-slate-900' },
                  { label: 'Pipeline Value', value: fmtCr(totalValue),                          gradient: 'bg-gradient-to-br from-emerald-900/50 to-slate-900' },
                  { label: 'Total Exposure', value: fmtCr(totalExpAll),                         gradient: 'bg-gradient-to-br from-amber-900/50 to-slate-900' },
                  { label: 'Avg Risk',       value: `${Math.round(avgRiskAll*100)}%`,            gradient: avgRiskAll>0.6 ? 'bg-gradient-to-br from-red-900/50 to-slate-900' : 'bg-gradient-to-br from-orange-900/40 to-slate-900' },
                  { label: 'Avg Readiness',  value: `${avgReadAll}%`,                           gradient: 'bg-gradient-to-br from-blue-900/50 to-slate-900' },
                  { label: 'Avg Win Prob',   value: `${avgWinAll.toFixed(1)}%`,                 gradient: 'bg-gradient-to-br from-violet-900/50 to-slate-900' },
                  { label: 'Total Actions',  value: totalActAll,                                 gradient: 'bg-gradient-to-br from-slate-800 to-slate-900' },
                ].map(k => (
                  <div key={k.label} className={`relative overflow-hidden rounded-2xl p-4 border border-white/5 ${k.gradient}`}>
                    <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_white_0%,_transparent_60%)]" />
                    <p className="text-[10px] font-semibold uppercase tracking-widest text-white/50 mb-1">{k.label}</p>
                    <p className="text-xl font-bold text-white">{k.value}</p>
                  </div>
                ))}
              </div>

              {/* Analytics 2x2 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Status distribution */}
                <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                  <h3 className="text-sm font-bold text-white mb-4">Status Distribution</h3>
                  <div className="space-y-2.5">
                    {Object.entries(statusDist).map(([status, count]) => (
                      <div key={status} className="flex items-center gap-3">
                        <span className={`text-[11px] px-2 py-0.5 rounded-full border w-20 text-center font-semibold ${STATUS_COLORS_TENDER[status] || STATUS_COLORS_TENDER.DRAFT}`}>{status}</span>
                        <div className="flex-1 h-2 bg-slate-700/60 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-indigo-600 to-violet-500 rounded-full" style={{ width: `${(count/allTenders.length)*100}%` }} />
                        </div>
                        <span className="text-xs font-bold text-slate-400 w-5 text-right">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Portfolio risk by dept */}
                <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                  <h3 className="text-sm font-bold text-white mb-4">Portfolio Risk by Department</h3>
                  <div className="space-y-2.5">
                    {deptRiskSummary.map(d => {
                      const rColor = d.avgRisk>0.7?'from-red-600 to-red-500':d.avgRisk>0.5?'from-orange-600 to-orange-500':d.avgRisk>0.3?'from-amber-600 to-yellow-500':'from-emerald-600 to-green-500';
                      return (
                        <div key={d.dept} className="flex items-center gap-3">
                          <span className="text-xs text-slate-400 w-24 shrink-0">{d.dept}</span>
                          <div className="flex-1 h-2 bg-slate-700/60 rounded-full overflow-hidden">
                            <div className={`h-full bg-gradient-to-r ${rColor} rounded-full`} style={{ width: `${Math.max(4, Math.round(d.avgRisk*100))}%` }} />
                          </div>
                          <span className="text-xs font-semibold text-slate-400 w-8 text-right">{Math.round(d.avgRisk*100)}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Scatter */}
                <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                  <h3 className="text-sm font-bold text-white mb-3">Value vs. Bid Readiness</h3>
                  <div className="relative h-44 bg-slate-900/60 rounded-xl border border-slate-700/30 p-3">
                    <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] text-slate-600">Readiness →</span>
                    <svg width="100%" height="100%" className="overflow-visible">
                      {tenderStats.map(ts => {
                        const xPct = ts.stats.readiness;
                        const maxVal = Math.max(...tenderStats.map(t=>parseFloat(t.tender.estimated_value||0)))||1;
                        const yPct = 100 - ((parseFloat(ts.tender.estimated_value||0)/maxVal)*85);
                        const risk = ts.stats.avgRisk;
                        const color = risk>0.6?'#ef4444':risk>0.4?'#f97316':'#10b981';
                        return (
                          <g key={ts.tender.id} onClick={() => navigate(`/tenders/${ts.tender.id}/bid-management`)} style={{ cursor:'pointer' }}>
                            <circle cx={`${xPct}%`} cy={`${yPct}%`} r="8" fill={color} fillOpacity="0.7" stroke={color} strokeWidth="1.5" />
                            <title>{ts.tender.title} — {ts.stats.readiness}% ready — {fmtCr(ts.tender.estimated_value)}</title>
                          </g>
                        );
                      })}
                    </svg>
                  </div>
                  <div className="flex gap-4 mt-2 text-[11px] text-slate-600">
                    {[['bg-red-500','High risk'],['bg-orange-500','Med risk'],['bg-emerald-500','Low risk']].map(([c,l]) => (
                      <span key={l} className="flex items-center gap-1"><span className={`w-2 h-2 rounded-full ${c} inline-block`}/>{l}</span>
                    ))}
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
                  <h3 className="text-sm font-bold text-white mb-4">Portfolio Summary</h3>
                  <div className="space-y-2.5">
                    {[
                      { label:'Total Action Items',  value:totalActAll,             color:'text-white' },
                      { label:'Critical Risk Items',  value:totalCritAll,            color:'text-red-400',    bg:'bg-red-900/20 border border-red-700/20' },
                      { label:'Avg Win Probability',  value:`${avgWinAll.toFixed(1)}%`, color:'text-violet-400' },
                      { label:'Avg Bid Readiness',    value:`${avgReadAll}%`,        color:'text-blue-400' },
                    ].map(row => (
                      <div key={row.label} className={`flex justify-between items-center p-3 rounded-xl ${row.bg || 'bg-slate-700/20'}`}>
                        <span className="text-xs text-slate-400">{row.label}</span>
                        <span className={`text-base font-bold ${row.color}`}>{row.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Tender table */}
              <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl overflow-hidden">
                <div className="flex items-center justify-between p-5 border-b border-slate-700/40 flex-wrap gap-3">
                  <h3 className="text-sm font-bold text-white">All Tenders — Portfolio View</h3>
                  <div className="flex gap-2">
                    <div className="relative">
                      <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                      <input value={portfolioSearch} onChange={e => setPortfolioSearch(e.target.value)}
                        placeholder="Search…" className="pl-8 pr-3 py-1.5 bg-slate-900/60 border border-slate-700/40 text-white text-xs rounded-xl focus:ring-1 focus:ring-violet-500 w-40" />
                    </div>
                    <select value={portfolioSort} onChange={e => setPortfolioSort(e.target.value)}
                      className="px-3 py-1.5 bg-slate-900/60 border border-slate-700/40 text-white text-xs rounded-xl focus:ring-1 focus:ring-violet-500">
                      <option value="value">By Value</option>
                      <option value="risk">By Risk</option>
                      <option value="readiness">By Readiness</option>
                      <option value="win">By Win Prob</option>
                      <option value="date">Newest</option>
                    </select>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-[10px] text-slate-500 uppercase tracking-wider border-b border-slate-700/40">
                        {['Tender','Status','Value','Exposure','Avg Risk','Win Prob','Readiness','Actions',''].map((h,i) => (
                          <th key={i} className={`py-3 px-4 ${i===0 ? 'text-left' : i===6 ? 'text-center' : i===8 ? '' : 'text-right'}`}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {portFiltered.length === 0 ? (
                        <tr><td colSpan={9} className="text-center py-12 text-slate-600">No tenders found</td></tr>
                      ) : portFiltered.map(({ tender: t, stats }) => (
                        <tr key={t.id} className={`border-b border-slate-700/20 hover:bg-slate-700/20 transition-colors ${t.id === id ? 'bg-indigo-950/20' : ''}`}>
                          <td className="px-4 py-3">
                            <div className={`font-semibold max-w-[200px] truncate ${t.id===id ? 'text-indigo-300' : 'text-white'}`}>{t.title}</div>
                            {t.reference_number && <div className="text-[10px] text-slate-600 font-mono mt-0.5">{t.reference_number}</div>}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`text-[11px] px-2 py-0.5 rounded-full border font-semibold ${STATUS_COLORS_TENDER[t.status]||STATUS_COLORS_TENDER.DRAFT}`}>{t.status}</span>
                          </td>
                          <td className="px-4 py-3 text-right text-emerald-400 font-semibold">{t.estimated_value ? fmtCr(t.estimated_value) : '—'}</td>
                          <td className="px-4 py-3 text-right text-amber-400">{stats.totalExposure > 0 ? fmtCr(stats.totalExposure) : '—'}</td>
                          <td className="px-4 py-3 text-right">
                            <span className={`font-bold ${stats.avgRisk>0.7?'text-red-400':stats.avgRisk>0.4?'text-orange-400':'text-emerald-400'}`}>{Math.round(stats.avgRisk*100)}%</span>
                          </td>
                          <td className="px-4 py-3 text-right text-violet-400 font-semibold">{stats.bestWinProb > 0 ? `${stats.bestWinProb.toFixed(1)}%` : '—'}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              <div className="flex-1 h-1.5 bg-slate-700/60 rounded-full overflow-hidden min-w-[50px]">
                                <div className={`h-full rounded-full ${stats.readiness>=80?'bg-emerald-500':stats.readiness>=50?'bg-blue-500':'bg-amber-500'}`} style={{ width:`${stats.readiness}%` }} />
                              </div>
                              <span className="text-[10px] text-slate-500 w-7">{stats.readiness}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right text-slate-500">{stats.actionCount}</td>
                          <td className="px-4 py-3">
                            <button onClick={() => navigate(`/tenders/${t.id}/bid-management`)}
                              className={`px-3 py-1.5 text-white text-[11px] rounded-xl font-semibold transition-all whitespace-nowrap ${t.id===id ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-violet-600 hover:bg-violet-700'}`}>
                              {t.id === id ? 'Current' : 'Open →'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="px-5 py-3 border-t border-slate-700/40 flex items-center justify-between text-[11px] text-slate-600">
                  <span>{portFiltered.length} of {allTenders.length} tenders</span>
                  <span>Pipeline: {fmtCr(totalValue)}</span>
                </div>
              </div>
            </div>
          );
        })()}
      </div>
    </div>
  );
};

export default BidManagementDashboard;
