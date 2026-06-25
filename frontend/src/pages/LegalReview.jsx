/**
 * Adv. Legal Review – AI-powered legal review page (Full 18-feature edition)
 * =========================================================================
 * Accessible via the "Legal Review" (Scale) button in the contract grid.
 * Route: /contracts/:contractId/legal-review
 *
 * Tabs:
 *  1. Summary           – contract-level stats + risk distribution
 *  2. Clause Review     – per-clause cards with radar, cases, sentences
 *  3. Knowledge Graph   – React Flow: Contract → Clauses → Cases
 *  4. Case Law          – browse 100-record case law store
 *  5. Live Feed         – real-time legal events (polling)
 *  6. Legal Co-Pilot    – 3-agent NL query chat
 *  7. RAG Search        – retrieval-augmented clause Q&A
 *  8. GraphRAG          – entity-aware graph RAG analysis
 *  9. Precedents        – Westlaw-style precedent similarity
 * 10. How It Works      – system explainer
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, Cell,
  PieChart, Pie, Legend
} from 'recharts';
import ReactFlow, {
  Background, Controls, MiniMap,
  useNodesState, useEdgesState,
  Handle, Position
} from 'reactflow';
import 'reactflow/dist/style.css';

import {
  Scale, AlertTriangle, BookOpen, Network, ChevronDown, ChevronUp,
  Loader2, RefreshCw, ArrowLeft, ArrowRight, FileText, Gavel, Brain, Search,
  CheckCircle, XCircle, Info, Sparkles, Shield, TrendingUp, List,
  Zap, MessageSquare, Globe, Clock, BookMarked, Cpu, Radio, Lightbulb,
  Edit2, Copy, ThumbsUp, ThumbsDown, GitCompare
} from 'lucide-react';

import {
  runLegalReview, explainClause, getLegalReviewStats, getCaseLaw,
  ragSearch, graphRagSearch, queryCopilot, getLiveEvents,
  findPrecedents, triggerCrawler, pollSSEEvents, simulateEvent,
  autoRedline
} from '../services/legalReviewService';

import EnhancedSummaryTab from '../components/EnhancedSummaryTab';
import EnhancedClauseReview from '../components/EnhancedClauseReview';

// ─────────────────────────────────────────────────────────
// CONSTANTS & HELPERS
// ─────────────────────────────────────────────────────────

const RISK_COLORS = { HIGH: '#F16667', MEDIUM: '#FFD86E', LOW: '#68BC00' };
const RISK_BG = {
  HIGH: 'bg-red-500/20 text-red-400 border-red-500/40',
  MEDIUM: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  LOW: 'bg-green-500/20 text-green-400 border-green-500/40',
};

const TABS = [
  { id: 'summary',    label: 'Summary',        icon: TrendingUp },
  { id: 'clauses',   label: 'Clause Review',   icon: FileText },
  { id: 'graph',     label: 'Knowledge Graph', icon: Network },
  { id: 'caselaw',   label: 'Case Law',        icon: BookOpen },
  { id: 'livefeed',  label: 'Live Feed',       icon: Radio },
  { id: 'copilot',   label: 'Legal Co-Pilot',  icon: MessageSquare },
  { id: 'rag',       label: 'RAG Search',      icon: Search },
  { id: 'graphrag',  label: 'GraphRAG',        icon: Cpu },
  { id: 'precedents',label: 'Precedents',      icon: BookMarked },
  { id: 'redline',   label: 'Auto-Redline',    icon: GitCompare },
  { id: 'howit',     label: 'How It Works',    icon: Info },
];

const RiskBadge = ({ level }) => (
  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold border ${RISK_BG[level] || RISK_BG.LOW}`}>
    <AlertTriangle size={10} /> {level}
  </span>
);

// ─────────────────────────────────────────────────────────
// RISK RADAR
// ─────────────────────────────────────────────────────────

const RiskRadar = ({ risk }) => {
  const data = [
    { axis: 'Probability', value: Math.round((risk.probability || 0) * 100) },
    { axis: 'Impact',      value: Math.round(Math.min((risk.impact || 0) * 6, 100)) },
    { axis: 'Risk Score',  value: Math.round(Math.min((risk.risk_score || 0) * 5, 100)) },
  ];
  const color = RISK_COLORS[risk.risk_level] || '#4C8EDA';
  return (
    <ResponsiveContainer width="100%" height={160}>
      <RadarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
        <PolarGrid stroke="#334155" />
        <PolarAngleAxis dataKey="axis" tick={{ fill: '#94a3b8', fontSize: 10 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
        <Radar name="Risk" dataKey="value" stroke={color} fill={color} fillOpacity={0.25} strokeWidth={2} />
        <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', fontSize: '11px' }} />
      </RadarChart>
    </ResponsiveContainer>
  );
};

// ─────────────────────────────────────────────────────────
// CASE LIST
// ─────────────────────────────────────────────────────────

const CaseList = ({ cases, showScore = false, contractKeywords = [], onViewAnalysis }) => {
  const [expandedCase, setExpandedCase] = useState(null);

  if (!cases?.length) return <p className="text-slate-500 text-xs">No cases retrieved.</p>;

  const getCaseImportance = (c) => {
    const year = parseInt(c.year);
    const currentYear = new Date().getFullYear();

    // Landmark cases (UK Supreme Court, House of Lords, etc.)
    if (c.court?.toLowerCase().includes('supreme') ||
        c.court?.toLowerCase().includes('house of lords')) {
      return { label: 'Landmark', color: 'from-amber-500 to-orange-600', icon: '⭐' };
    }

    // Recent cases (last 5 years)
    if (year >= currentYear - 5) {
      return { label: 'Recent', color: 'from-green-500 to-emerald-600', icon: '🆕' };
    }

    // High-impact cases (many tags indicate complex/important case)
    if (c.tags?.length >= 4) {
      return { label: 'High Impact', color: 'from-purple-500 to-pink-600', icon: '💎' };
    }

    return null;
  };

  return (
    <div className="space-y-3">
      {cases.map((c, i) => {
        const isExpanded = expandedCase === i;
        const importance = getCaseImportance(c);

        // Parse citation and holding from text field
        let citation, holding;
        if (c.text) {
          // Format 1: "Case Name [Year]: holding text"
          if (c.text.includes(':')) {
            const parts = c.text.split(':');
            citation = parts[0].trim();
            holding = parts.slice(1).join(':').trim();
          }
          // Format 2: "In Case Name [Year], holding text" or "Case Name v. Another [Year] text"
          else {
            const match = c.text.match(/^(?:In\s+)?([^,]+?\s+(?:v\.?|vs\.?)\s+[^,\[]+(?:\s+\[\d{4}\])?)/i);
            if (match) {
              citation = match[1].trim();
              holding = c.text.substring(match[0].length).replace(/^[,\s]+/, '');
            } else {
              // Fallback: first sentence as citation, rest as holding
              const sentences = c.text.split(/[.!?]\s+/);
              citation = sentences[0];
              holding = sentences.slice(1).join('. ');
            }
          }
        }

        // Fallbacks
        citation = citation || c.case_name || c.name || `${c.court} [${c.year}]`;
        holding = holding || c.holding || c.summary || 'No detailed holding available for this case.';

        return (
          <div
            key={i}
            className={`bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-xl p-4 border transition-all cursor-pointer ${
              isExpanded ? 'border-blue-500/50 shadow-lg shadow-blue-500/20' : 'border-slate-700/40 hover:border-slate-600/60'
            }`}
            onClick={() => setExpandedCase(isExpanded ? null : i)}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {importance && (
                    <span className={`px-2 py-0.5 bg-gradient-to-r ${importance.color} text-white text-[10px] font-bold rounded-full flex items-center gap-1`}>
                      <span>{importance.icon}</span>
                      {importance.label}
                    </span>
                  )}
                  {showScore && c._score > 0 && (
                    <span className="px-2 py-0.5 bg-violet-500/20 text-violet-300 text-[10px] rounded-full border border-violet-500/30 font-semibold">
                      {c._score} keyword match{c._score !== 1 ? 'es' : ''}
                    </span>
                  )}
                  {typeof c.score === 'number' && (
                    <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-[10px] rounded-full">
                      Relevance: {(c.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                <h4 className="text-blue-300 font-bold text-sm mb-1">{citation}</h4>
                <p className="text-slate-400 text-xs flex items-center gap-2">
                  <span className="font-semibold">{c.court}</span>
                  <span>•</span>
                  <span>{c.year}</span>
                  <span>•</span>
                  <span className="px-1.5 py-0.5 bg-slate-700/50 rounded text-[10px]">{c.jurisdiction}</span>
                </p>
              </div>
              <div className="text-slate-500 text-xs">
                {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
            </div>

            {/* Key Finding - Always Visible */}
            <div className="bg-slate-900/50 border border-slate-700/30 rounded-lg p-3 mb-3">
              <p className="text-slate-500 text-[10px] uppercase tracking-wider mb-1 font-semibold">Key Finding</p>
              <p className={`text-slate-300 text-sm leading-relaxed ${!isExpanded ? 'line-clamp-2' : ''}`}>
                {holding}
              </p>
            </div>

            {/* Topics */}
            {c.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {c.tags.map((t, ti) => (
                  <span
                    key={ti}
                    className="bg-violet-500/20 text-violet-300 text-[10px] px-2 py-1 rounded-md border border-violet-500/30 font-medium"
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}

            {/* Expanded Details */}
            {isExpanded && (
              <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-3 animate-fadeIn">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <p className="text-slate-500 text-[10px] uppercase mb-1">Jurisdiction</p>
                    <p className="text-slate-200 text-xs font-semibold">{c.jurisdiction}</p>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <p className="text-slate-500 text-[10px] uppercase mb-1">Year Decided</p>
                    <p className="text-slate-200 text-xs font-semibold">{c.year}</p>
                  </div>
                </div>

                <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
                  <p className="text-blue-300 text-[10px] uppercase mb-2 font-semibold">💡 Why This Case Matters</p>
                  <p className="text-slate-300 text-xs leading-relaxed">
                    This case is relevant for <strong>{c.tags?.[0] || 'contract law'}</strong> analysis.
                    {importance?.label === 'Landmark' && ' As a landmark decision, it sets binding precedent in this jurisdiction.'}
                    {importance?.label === 'Recent' && ' Being a recent case, it reflects current judicial thinking.'}
                    {importance?.label === 'High Impact' && ' This high-impact case addresses multiple legal issues.'}
                    {showScore && c._score > 0 && (() => {
                      const matched = contractKeywords.filter(k => (c.text + ' ' + (c.tags || []).join(' ')).toLowerCase().includes(k));
                      return matched.length > 0 ? ` Matched your contract on: ${matched.slice(0, 5).join(', ')}.` : '';
                    })()}
                  </p>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Case ID: {c.case_id || `CL${String(i + 1).padStart(3, '0')}`}</span>
                  {onViewAnalysis && (
                    <button
                      onClick={e => { e.stopPropagation(); onViewAnalysis(c); }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-[11px] font-semibold transition-colors"
                    >
                      <Sparkles size={11} /> Analyse for My Contract
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// SENTENCE BREAKDOWN
// ─────────────────────────────────────────────────────────

const SentenceBreakdown = ({ sentences }) => {
  if (!sentences?.length) return null;
  return (
    <div className="space-y-1 mt-2">
      {sentences.map((s, i) => {
        const rawRisk = typeof s.risk === 'string' ? s.risk : (s.risk_level || s.level || 'LOW');
        const risk = rawRisk.toUpperCase();
        const color = RISK_COLORS[risk] || '#68BC00';
        return (
          <div key={i} className="flex items-start gap-2 text-xs">
            <span className="shrink-0 mt-0.5 w-2 h-2 rounded-full" style={{ background: color }} />
            <span className="text-slate-300">{s.text}</span>
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// CLAUSE CARD
// ─────────────────────────────────────────────────────────

const ClauseCard = ({ clause, idx }) => {
  const [open, setOpen] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState(null);

  const risk = clause.risk || {};
  const level = (risk.risk_level || 'LOW').toUpperCase();

  const handleExplain = async () => {
    setExplaining(true);
    try {
      const res = await explainClause(clause.text, risk, clause.cases || []);
      setExplanation(res.explanation || res.error || 'No explanation returned.');
    } catch {
      setExplanation('Failed to get explanation.');
    } finally {
      setExplaining(false);
    }
  };

  return (
    <div className={`rounded-xl border ${level === 'HIGH' ? 'border-red-500/40' : level === 'MEDIUM' ? 'border-yellow-500/40' : 'border-green-500/30'} bg-slate-800/50`}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="shrink-0 text-slate-400 text-xs">#{idx + 1}</span>
          <RiskBadge level={level} />
          <p className="text-slate-200 text-sm truncate">{clause.type || 'Clause'}</p>
          <span className="text-slate-500 text-xs shrink-0">
            Score: {typeof risk.risk_score === 'number' ? risk.risk_score.toFixed(2) : '—'}
          </span>
        </div>
        {open ? <ChevronUp size={16} className="text-slate-400 shrink-0" /> : <ChevronDown size={16} className="text-slate-400 shrink-0" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3">
          <p className="text-slate-300 text-sm leading-relaxed border-l-2 border-slate-600 pl-3">
            {clause.text}
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <RiskRadar risk={risk} />
            </div>
            <div className="space-y-2">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-700/50 rounded-lg p-2">
                  <p className="text-slate-400 text-xs">Probability</p>
                  <p className="text-white font-bold text-sm">{((risk.probability || 0) * 100).toFixed(0)}%</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-2">
                  <p className="text-slate-400 text-xs">Impact</p>
                  <p className="text-white font-bold text-sm">{(risk.impact || 0).toFixed(1)}</p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-2">
                  <p className="text-slate-400 text-xs">Score</p>
                  <p className="text-white font-bold text-sm">{(risk.risk_score || 0).toFixed(2)}</p>
                </div>
              </div>
              {risk.reason && (
                <p className="text-slate-400 text-xs bg-slate-700/30 rounded p-2">{risk.reason}</p>
              )}
            </div>
          </div>

          {/* Sentence breakdown */}
          {clause.sentences?.length > 0 && (
            <div>
              <p className="text-slate-400 text-xs font-semibold mb-1">Sentence-Level Risk</p>
              <SentenceBreakdown sentences={clause.sentences} />
            </div>
          )}

          {/* Cases */}
          {clause.cases?.length > 0 && (
            <div>
              <p className="text-slate-400 text-xs font-semibold mb-1">Supporting Case Law</p>
              <CaseList cases={clause.cases.slice(0, 3)} />
            </div>
          )}

          {/* AI Explanation */}
          <div>
            <button
              onClick={handleExplain}
              disabled={explaining}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-violet-600/80 hover:bg-violet-600 text-white text-xs font-medium disabled:opacity-50"
            >
              {explaining ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
              AI Explanation
            </button>
            {explanation && (
              <div className="mt-2 bg-violet-900/20 border border-violet-500/30 rounded-lg p-3 text-slate-300 text-xs leading-relaxed">
                {explanation}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// REACT FLOW CUSTOM NODES
// ─────────────────────────────────────────────────────────

const ContractNode = ({ data }) => (
  <div className="px-4 py-3 rounded-xl bg-gradient-to-br from-green-900/80 to-green-800/60 border-2 border-green-500/60 min-w-[140px] text-center shadow-lg shadow-green-900/30">
    <Handle type="source" position={Position.Bottom} className="!bg-green-400" />
    <Scale size={18} className="text-green-400 mx-auto mb-1" />
    <p className="text-white text-xs font-bold">{data.label}</p>
    <p className="text-green-300 text-[10px]">{data.sub}</p>
  </div>
);

const ClauseNode = ({ data }) => {
  const color = RISK_COLORS[data.risk] || '#4C8EDA';
  return (
    <div
      className="px-3 py-2 rounded-lg min-w-[120px] text-center border relative"
      style={{ background: `${color}15`, borderColor: `${color}60`, boxShadow: `0 0 10px ${color}20` }}
    >
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      {data.isNew && (
        <span className="absolute -top-2 -right-2 px-1.5 py-0.5 bg-violet-500 text-white text-[8px] font-bold rounded-full animate-pulse">
          NEW
        </span>
      )}
      <FileText size={12} className="mx-auto mb-0.5" style={{ color }} />
      <p className="text-white text-[10px] font-semibold">{data.label}</p>
      <p className="text-[10px]" style={{ color }}>{data.risk}</p>
      <p className="text-slate-400 text-[9px]">Score: {data.score}</p>
    </div>
  );
};

const CaseNode = ({ data }) => (
  <div className="px-3 py-2 rounded-lg min-w-[120px] text-center bg-blue-900/50 border border-blue-500/40">
    <Handle type="target" position={Position.Top} />
    <Gavel size={12} className="text-blue-400 mx-auto mb-0.5" />
    <p className="text-blue-200 text-[10px] font-semibold truncate max-w-[120px]">{data.label}</p>
    <p className="text-blue-400 text-[9px]">{data.court} · {data.year}</p>
  </div>
);

const nodeTypes = { contractNode: ContractNode, clauseNode: ClauseNode, caseNode: CaseNode };

// ─────────────────────────────────────────────────────────
// SENTENCE NODE (for drill-down)
// ─────────────────────────────────────────────────────────

const SentenceNode = ({ data }) => {
  const color = RISK_COLORS[data.risk] || '#64748b';
  return (
    <div className="px-2 py-1 rounded text-center border max-w-[150px]"
      style={{ background: `${color}12`, borderColor: `${color}50` }}>
      <Handle type="target" position={Position.Top} />
      <p className="text-[9px]" style={{ color }} title={data.fullText}>
        {(data.label || '').slice(0, 40)}{data.label?.length > 40 ? '…' : ''}
      </p>
    </div>
  );
};

const RiskNode = ({ data }) => {
  const color = RISK_COLORS[data.risk] || '#F16667';
  return (
    <div className="px-2 py-1.5 rounded-full border text-center"
      style={{ background: `${color}20`, borderColor: color, minWidth: 70 }}>
      <Handle type="target" position={Position.Top} />
      <p className="text-[9px] font-bold" style={{ color }}>⚠ {data.label}</p>
      <p className="text-[8px] text-slate-400">{data.score}</p>
    </div>
  );
};

const extendedNodeTypes = {
  contractNode: ContractNode,
  clauseNode: ClauseNode,
  caseNode: CaseNode,
  sentenceNode: SentenceNode,
  riskNode: RiskNode,
};

// ─────────────────────────────────────────────────────────
// KNOWLEDGE GRAPH TAB — Full-featured (7 features)
// ─────────────────────────────────────────────────────────

const KnowledgeGraph = ({ data, contractId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Controls
  const [heatOverlay, setHeatOverlay] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState(new Set());
  const [selectedNode, setSelectedNode] = useState(null);
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [timeVersion, setTimeVersion] = useState(100); // 0-100 slider
  const [isFullscreen, setIsFullscreen] = useState(false);
  const graphContainerRef = useRef(null);

  // Build base graph data
  const baseClauseData = (data?.clauses || []).map((cl, ci) => ({
    ci,
    clauseId: `clause-${ci}`,
    clause: cl,
    risk: (cl.risk?.risk_level || 'LOW').toUpperCase(),
    score: cl.risk?.risk_score || 0,
    x: 100 + ci * 180,
  }));

  const rebuildGraph = (expanded, heat, version) => {
    const ns = [];
    const es = [];
    const contractId_ = 'contract-root';
    const timelineThreshold = version / 100; // 0.0 to 1.0

    // Filter clauses based on timeline: simulate clauses being added progressively
    // Each clause has an "added_at" timestamp (0.0 = initial draft, 1.0 = final version)
    const visibleClauses = baseClauseData.filter(({ ci }) => {
      const clauseAddedAt = (ci + 1) / baseClauseData.length; // Clause 0 at 0%, last clause at 100%
      return clauseAddedAt <= timelineThreshold;
    });

    // Update contract node with visible clause count
    ns.push({
      id: contractId_,
      type: 'contractNode',
      position: { x: baseClauseData.length * 90, y: 20 },
      data: {
        label: 'Contract',
        sub: `${visibleClauses.length}/${baseClauseData.length} clauses`
      },
    });

    visibleClauses.forEach(({ ci, clauseId, clause, risk, score, x }) => {
      const displayRisk = heat ? risk : risk;
      const displayScore = heat ? score : score;

      // Check if this clause was recently added (within last 10% of timeline)
      const clauseAddedAt = (ci + 1) / baseClauseData.length;
      const isRecentlyAdded = clauseAddedAt > (timelineThreshold - 0.1) && clauseAddedAt <= timelineThreshold;

      ns.push({
        id: clauseId,
        type: 'clauseNode',
        position: { x, y: 200 },
        data: {
          label: clause.type || `Clause ${ci + 1}`,
          risk: displayRisk,
          score: displayScore.toFixed ? displayScore.toFixed(2) : displayScore,
          isNew: isRecentlyAdded // Visual indicator for recently added clauses
        },
        className: isRecentlyAdded ? 'animate-pulse' : '', // Pulse animation for new clauses
      });
      // Calculate edge weight based on risk score (0.0 - 4.0, normalized to 0-1)
      const clauseWeight = Math.min(displayScore / 4.0, 1.0);
      const edgeThickness = 2 + (clauseWeight * 6); // Range: 2-8px based on risk
      const edgeOpacity = 0.4 + (clauseWeight * 0.6); // Range: 0.4-1.0 opacity

      es.push({
        id: `e-contract-${ci}`,
        source: contractId_,
        target: clauseId,
        label: `${(clauseWeight * 100).toFixed(0)}%`, // Always show weight
        labelStyle: { fill: '#a78bfa', fontSize: 10, fontWeight: 'bold' },
        labelBgStyle: { fill: '#1e1b4b', fillOpacity: 0.9 },
        labelBgPadding: [4, 6],
        labelBgBorderRadius: 4,
        style: {
          stroke: heat ? RISK_COLORS[displayRisk] || '#64748b' : '#475569',
          strokeWidth: edgeThickness,
          strokeOpacity: edgeOpacity
        },
        animated: heat && displayRisk === 'HIGH',
      });

      // ── Risk Node (always shown) ──
      const riskNodeId = `risk-${ci}`;
      ns.push({
        id: riskNodeId,
        type: 'riskNode',
        position: { x: x - 30, y: 330 },
        data: { label: displayRisk, risk: displayRisk, score: displayScore.toFixed ? displayScore.toFixed(2) : displayScore },
      });

      // Risk edge weight: emphasize higher risk connections
      const riskWeight = Math.min(displayScore / 4.0, 1.0);
      const riskEdgeThickness = 1.5 + (riskWeight * 5); // Range: 1.5-6.5px

      es.push({
        id: `e-risk-${ci}`,
        source: clauseId,
        target: riskNodeId,
        label: `${displayScore.toFixed ? displayScore.toFixed(1) : displayScore}`, // Always show risk score
        labelStyle: { fill: RISK_COLORS[displayRisk] || '#64748b', fontSize: 10, fontWeight: 'bold' },
        labelBgStyle: { fill: '#0f172a', fillOpacity: 0.9 },
        labelBgPadding: [3, 5],
        labelBgBorderRadius: 4,
        style: {
          stroke: RISK_COLORS[displayRisk] || '#64748b',
          strokeDasharray: '3 2',
          strokeWidth: riskEdgeThickness,
          strokeOpacity: 0.5 + (riskWeight * 0.5) // Range: 0.5-1.0
        },
      });

      // ── Case nodes ──
      (clause.cases || []).slice(0, 2).forEach((c, cai) => {
        const caseId = `case-${ci}-${cai}`;
        ns.push({
          id: caseId,
          type: 'caseNode',
          position: { x: x + cai * 150 - 60, y: 440 },
          data: {
            label: c.citation || c.case_name || c.name || (c.text ? c.text.split(':')[0].trim() : 'Case'),
            court: c.court || '',
            year: c.year || '',
            key_finding: c.key_finding || c.relevance || (c.text ? c.text.split(':').slice(1).join(':').trim() : ''),
            tags: c.topics || c.tags || [],
            jurisdiction: c.jurisdiction || '',
            text: c.text || '',
          },
        });

        // Case relevance weight: Supreme Court = 1.0, High Court = 0.7, others = 0.5
        const isSupreme = (c.court || '').toLowerCase().includes('supreme');
        const isHighCourt = (c.court || '').toLowerCase().includes('high');
        const caseRelevance = isSupreme ? 1.0 : (isHighCourt ? 0.7 : 0.5);
        const caseEdgeThickness = 1.5 + (caseRelevance * 3); // Range: 1.5-4.5px

        es.push({
          id: `e-cl-case-${ci}-${cai}`,
          source: clauseId,
          target: caseId,
          label: isSupreme ? `⭐ ${(caseRelevance * 100).toFixed(0)}%` : `${(caseRelevance * 100).toFixed(0)}%`,
          labelStyle: { fill: isSupreme ? '#fbbf24' : '#60a5fa', fontSize: 10, fontWeight: 'bold' },
          labelBgStyle: { fill: '#0f172a', fillOpacity: 0.9 },
          labelBgPadding: [3, 5],
          labelBgBorderRadius: 4,
          style: {
            stroke: isSupreme ? '#fbbf24' : '#3b82f6',
            strokeDasharray: '4 2',
            strokeWidth: caseEdgeThickness,
            strokeOpacity: 0.6 + (caseRelevance * 0.4) // Range: 0.6-1.0
          },
        });
      });

      // ── Sentence sub-nodes (drill-down, only if clause expanded) ──
      if (expanded.has(ci)) {
        (clause.sentences || []).slice(0, 4).forEach((s, si) => {
          const sentId = `sent-${ci}-${si}`;
          const rawRisk = typeof s.risk === 'string' ? s.risk : (s.risk_level || 'LOW');
          const sRisk = rawRisk.toUpperCase();
          const sentScore = s.risk_score || (sRisk === 'HIGH' ? 3.5 : sRisk === 'MEDIUM' ? 2.0 : 0.8);

          ns.push({
            id: sentId,
            type: 'sentenceNode',
            position: { x: x - 60 + si * 80, y: 570 },
            data: {
              label: s.text || `Sentence ${si + 1}`,
              fullText: s.text || '',
              risk: sRisk,
            },
          });

          // Sentence edge weight: based on sentence-level risk
          const sentWeight = Math.min(sentScore / 4.0, 1.0);
          const sentEdgeThickness = 1 + (sentWeight * 3); // Range: 1-4px

          es.push({
            id: `e-sent-${ci}-${si}`,
            source: clauseId,
            target: sentId,
            label: `${(sentWeight * 100).toFixed(0)}%`, // Always show weight
            labelStyle: { fill: RISK_COLORS[sRisk] || '#94a3b8', fontSize: 9, fontWeight: 'bold' },
            labelBgStyle: { fill: '#0f172a', fillOpacity: 0.9 },
            labelBgPadding: [3, 4],
            labelBgBorderRadius: 4,
            style: {
              stroke: RISK_COLORS[sRisk] || '#64748b',
              strokeDasharray: '2 2',
              strokeWidth: sentEdgeThickness,
              opacity: 0.4 + (sentWeight * 0.6) // Range: 0.4-1.0
            },
          });
        });
      }
    });

    setNodes(ns);
    setEdges(es);
  };

  useEffect(() => {
    if (!data) return;
    rebuildGraph(expandedClauses, heatOverlay, timeVersion);
  }, [data, expandedClauses, heatOverlay, timeVersion]);

  const onNodeClick = useCallback((_, node) => {
    setSelectedNode(node);
    setExplanation('');

    // Toggle drill-down for clause nodes
    if (node.type === 'clauseNode') {
      const ciMatch = node.id.match(/clause-(\d+)/);
      if (ciMatch) {
        const ci = parseInt(ciMatch[1]);
        setExpandedClauses(prev => {
          const next = new Set(prev);
          if (next.has(ci)) next.delete(ci); else next.add(ci);
          return next;
        });
      }
    }
  }, []);

  const toggleFullscreen = () => {
    if (!graphContainerRef.current) return;

    if (!document.fullscreenElement) {
      graphContainerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.error('Fullscreen request failed:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const handleExplainNode = async () => {
    if (!selectedNode) return;
    setExplaining(true);
    setExplanation('');
    try {
      const ciMatch = selectedNode.id.match(/clause-(\d+)/);
      if (ciMatch) {
        const ci = parseInt(ciMatch[1]);
        const clause = data?.clauses?.[ci];
        if (clause) {
          const res = await explainClause(clause.text, clause.risk || {}, clause.cases || []);
          setExplanation(res.explanation || 'No explanation returned.');
        }
      } else if (selectedNode.type === 'caseNode') {
        const d = selectedNode.data;
        // Find the parent clause this case belongs to
        const caseMatch = selectedNode.id.match(/case-(\d+)-(\d+)/);
        const parentClause = caseMatch ? data?.clauses?.[parseInt(caseMatch[1])] : null;
        const tags = d.tags || [];
        const lines = [];
        lines.push(`📋 ${d.label}`);
        lines.push(`🏛 ${d.court} · ${d.year} · ${d.jurisdiction || 'N/A'}`);
        if (d.key_finding) lines.push(`\n⚖️ Key Finding:\n${d.key_finding}`);
        if (parentClause) {
          lines.push(`\n🔗 Linked to: ${parentClause.clause_type || 'Clause'} (${(parentClause.risk?.risk_level || parentClause.risk_level || '').toUpperCase()} risk)`);
          if (parentClause.risk_reason) lines.push(`Reason: ${parentClause.risk_reason}`);
        }
        if (tags.length > 0) lines.push(`\n🏷 Topics: ${tags.join(', ')}`);
        lines.push(`\n💡 This case was retrieved because its legal topics match this clause's content. It provides precedent for how courts have interpreted similar ${tags[0] || 'contractual'} provisions.`);
        setExplanation(lines.join('\n'));
      } else if (selectedNode.type === 'riskNode') {
        setExplanation(`Risk Level: ${selectedNode.data.risk}\nRisk Score: ${selectedNode.data.score}\nThis risk node reflects the Bayesian Noisy-OR computed probability × impact score for the linked clause.`);
      } else {
        setExplanation('Select a Clause node for AI explanation.');
      }
    } catch {
      setExplanation('Failed to get explanation.');
    } finally {
      setExplaining(false);
    }
  };

  const nodeColor = (n) => {
    if (n.type === 'contractNode') return '#68BC00';
    if (n.type === 'clauseNode') return RISK_COLORS[n.data?.risk] || '#4C8EDA';
    if (n.type === 'riskNode') return RISK_COLORS[n.data?.risk] || '#F16667';
    if (n.type === 'sentenceNode') return RISK_COLORS[n.data?.risk] || '#64748b';
    return '#4C8EDA';
  };

  return (
    <div className="space-y-3" ref={graphContainerRef}>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Heat overlay */}
        <button
          onClick={() => setHeatOverlay(h => !h)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
            heatOverlay
              ? 'bg-orange-500/20 border-orange-500/50 text-orange-300'
              : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
          }`}
        >
          <span className="w-2.5 h-2.5 rounded-full bg-orange-400" />
          Risk Heat Overlay {heatOverlay ? 'ON' : 'OFF'}
        </button>

        {/* Fullscreen Button */}
        <button
          onClick={toggleFullscreen}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-violet-500/50 transition-all"
          title="Toggle Fullscreen"
        >
          {isFullscreen ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
              </svg>
              Exit Fullscreen
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
              </svg>
              Fullscreen
            </>
          )}
        </button>

        {/* Legend with better explanation */}
        <div className="flex items-center gap-3 text-xs bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-700/50">
          <span className="text-slate-400 font-semibold">Legend:</span>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-slate-300">Contract</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-slate-300">Clause</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-400" />
            <span className="text-slate-300">Case</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="text-slate-300">Risk</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-slate-500" />
            <span className="text-slate-300">Sentence</span>
          </div>
          <span className="text-slate-600 text-xs ml-2">• Line thickness + opacity = Connection strength</span>
        </div>

        <span className="text-amber-400 text-xs ml-auto flex items-center gap-1">
          <Info size={12} />
          Click Clause nodes to expand sentences
        </span>
      </div>

      {/* Help Box - How to Read the Graph */}
      <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-3 flex items-start gap-3">
        <Sparkles size={16} className="text-blue-400 mt-0.5 shrink-0" />
        <div className="flex-1">
          <p className="text-blue-300 text-xs font-semibold mb-1">📊 How to Read This Graph:</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-slate-300 text-xs">
            <p>• <strong>Line thickness</strong> = Risk/relevance weight (2-8px)</p>
            <p>• <strong>Line opacity</strong> = Connection strength (40-100%)</p>
            <p>• <strong>% labels</strong> = High-risk connections (&gt;70%)</p>
            <p>• <strong>⭐ gold lines</strong> = Supreme Court precedents</p>
            <p>• <strong>Timeline slider</strong> = See contract evolution</p>
            <p>• <strong>Pulsing clauses</strong> = Recently added</p>
            <p>• <strong>Click clauses</strong> = Expand sentences</p>
            <p>• <strong>Heat Overlay</strong> = Risk hotspots</p>
          </div>
        </div>
      </div>

      {/* Contract Timeline Slider */}
      <div className="bg-gradient-to-r from-violet-900/20 to-purple-900/20 border border-violet-500/30 rounded-xl px-4 py-3">
        <div className="flex items-center gap-3 mb-2">
          <Clock size={16} className="text-violet-400 shrink-0" />
          <span className="text-violet-300 text-sm font-semibold shrink-0">📜 Contract Timeline</span>
          <span className="text-slate-500 text-xs ml-auto">
            Showing {Math.round((timeVersion / 100) * (data?.clauses?.length || 0))} of {data?.clauses?.length || 0} clauses
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-slate-400 text-xs shrink-0 w-20">Initial Draft</span>
          <input
            type="range" min={10} max={100} value={timeVersion}
            onChange={e => setTimeVersion(parseInt(e.target.value))}
            className="flex-1 accent-violet-500 h-2"
            style={{
              background: `linear-gradient(to right, #8b5cf6 0%, #8b5cf6 ${timeVersion}%, #334155 ${timeVersion}%, #334155 100%)`
            }}
          />
          <span className="text-slate-400 text-xs shrink-0 w-20 text-right">Final Version</span>
          <span className="text-violet-300 text-sm font-mono font-bold shrink-0 w-12 text-right">{timeVersion}%</span>
        </div>
        <div className="flex items-center gap-2 mt-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
          <span>Recently added clauses pulse</span>
        </div>
      </div>

      <div className="flex gap-3">
        {/* Graph */}
        <div className={`flex-1 rounded-xl overflow-hidden border border-slate-700/50 ${isFullscreen ? 'h-screen' : 'h-[520px]'}`}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={extendedNodeTypes}
            onNodeClick={onNodeClick}
            defaultEdgeOptions={{
              type: 'default',
              animated: false,
              labelShowBg: true,
              labelBgBorderRadius: 4,
            }}
            fitView
            minZoom={0.1}
            maxZoom={2}
          >
            <Background color="#1e293b" gap={20} />
            <Controls />
            <MiniMap nodeColor={nodeColor} style={{ background: '#0f172a', border: '1px solid #334155' }} />
          </ReactFlow>
        </div>

        {/* Side panel — selected node detail + Explain Node */}
        {selectedNode && (() => {
          // Get full clause data for clause nodes
          const clauseIndex = selectedNode.type === 'clauseNode' ? parseInt(selectedNode.id.replace('clause-', '')) : null;
          const clause = clauseIndex !== null ? (data?.clauses || [])[clauseIndex] : null;
          const isExpanded = clauseIndex !== null && expandedClauses.has(clauseIndex);

          return (
            <div className="w-80 shrink-0 bg-gradient-to-br from-slate-800/95 to-slate-900/95 border border-slate-700/50 rounded-xl p-4 space-y-3 overflow-y-auto max-h-[520px]">
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {selectedNode.type === 'clauseNode' && <FileText size={14} className="text-violet-400" />}
                  {selectedNode.type === 'caseNode' && <Gavel size={14} className="text-blue-400" />}
                  {selectedNode.type === 'riskNode' && <AlertTriangle size={14} className="text-red-400" />}
                  <p className="text-violet-300 text-sm font-bold uppercase tracking-wide">
                    {selectedNode.type?.replace('Node', '')} Details
                  </p>
                </div>
                <button onClick={() => setSelectedNode(null)} className="text-slate-500 hover:text-slate-300 transition-colors">
                  ✕
                </button>
              </div>

              {/* Clause Node - Comprehensive Info */}
              {selectedNode.type === 'clauseNode' && clause && (
                <div className="space-y-3">
                  {/* Basic Info */}
                  <div className="bg-slate-900/50 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-xs font-semibold">Risk Level</span>
                      <RiskBadge level={selectedNode.data?.risk} />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-xs">Risk Score</span>
                      <span className="text-red-300 font-mono text-sm font-bold">{selectedNode.data?.score}</span>
                    </div>
                    {clause.risk?.probability !== undefined && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-xs">Probability</span>
                        <span className="text-purple-300 text-xs font-semibold">{clause.risk.probability}%</span>
                      </div>
                    )}
                    {clause.risk?.impact !== undefined && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-xs">Impact</span>
                        <span className="text-orange-300 text-xs font-semibold">{clause.risk.impact?.toFixed?.(1) || clause.risk.impact}/10</span>
                      </div>
                    )}
                  </div>

                  {/* Timeline Info */}
                  <div className="bg-violet-900/20 border border-violet-500/30 rounded-lg p-2">
                    <div className="flex items-center gap-2 mb-1">
                      <Clock size={12} className="text-violet-400" />
                      <span className="text-violet-300 text-xs font-semibold">Timeline Position</span>
                    </div>
                    <p className="text-slate-300 text-xs">
                      Added at ~{Math.round(((clauseIndex + 1) / (data?.clauses?.length || 1)) * 100)}% of contract lifecycle
                      {selectedNode.data?.isNew && <span className="ml-2 text-violet-400 font-bold">🆕 NEW</span>}
                    </p>
                  </div>

                  {/* Clause Text */}
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <p className="text-slate-400 text-xs font-semibold mb-2">📄 Clause Text</p>
                    <p className="text-slate-300 text-xs leading-relaxed line-clamp-4">
                      {clause.text || clause.clause_text || 'No text available'}
                    </p>
                  </div>

                  {/* Case Law Support */}
                  {clause.cases && clause.cases.length > 0 && (
                    <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Gavel size={12} className="text-blue-400" />
                        <span className="text-blue-300 text-xs font-semibold">Supporting Cases</span>
                        <span className="ml-auto text-blue-400 text-xs font-bold">{clause.cases.length}</span>
                      </div>
                      <div className="space-y-1.5">
                        {clause.cases.slice(0, 2).map((c, idx) => (
                          <div key={idx} className="text-xs bg-slate-800/50 rounded p-2">
                            <p className="text-blue-300 font-semibold">{c.case_name || c.name || `Case ${idx + 1}`}</p>
                            <p className="text-slate-400 text-[10px]">{c.court} - {c.year}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Insights */}
                  {clause.insights?.recommendations && clause.insights.recommendations.length > 0 && (
                    <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Lightbulb size={12} className="text-green-400" />
                        <span className="text-green-300 text-xs font-semibold">Key Recommendations</span>
                      </div>
                      <ul className="space-y-1">
                        {clause.insights.recommendations.slice(0, 2).map((rec, idx) => (
                          <li key={idx} className="text-slate-300 text-[10px] leading-relaxed flex items-start gap-1">
                            <CheckCircle size={10} className="text-green-400 mt-0.5 shrink-0" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Sentence Expansion Status */}
                  {clause.sentences && clause.sentences.length > 0 && (
                    <div className="bg-slate-700/30 rounded-lg p-2 flex items-center justify-between">
                      <span className="text-slate-400 text-xs">Sentences</span>
                      <span className="text-slate-300 text-xs">
                        {clause.sentences.length} {isExpanded ? '(expanded below)' : '(click to expand)'}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Case Node Info */}
              {selectedNode.type === 'caseNode' && (
                <div className="space-y-2">
                  <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 space-y-2">
                    <p className="text-blue-300 font-semibold text-sm leading-snug">{selectedNode.data?.label}</p>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      {selectedNode.data?.court && <span>🏛 {selectedNode.data.court}</span>}
                      {selectedNode.data?.year && <span>📅 {selectedNode.data.year}</span>}
                      {selectedNode.data?.jurisdiction && (
                        <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">{selectedNode.data.jurisdiction}</span>
                      )}
                    </div>
                    {selectedNode.data?.key_finding && (
                      <div className="bg-slate-800/60 rounded p-2">
                        <p className="text-slate-500 text-[10px] uppercase tracking-wider mb-1">Key Finding</p>
                        <p className="text-slate-300 text-xs leading-relaxed">{selectedNode.data.key_finding}</p>
                      </div>
                    )}
                    {selectedNode.data?.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {selectedNode.data.tags.map((t, i) => (
                          <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/20">{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Risk Node Info */}
              {selectedNode.type === 'riskNode' && (
                <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-red-300 text-sm font-bold">Risk Assessment</span>
                    <RiskBadge level={selectedNode.data?.risk} />
                  </div>
                  <p className="text-slate-300 text-xs">
                    This risk node reflects the Bayesian Noisy-OR computed probability × impact score for the linked clause.
                  </p>
                  <div className="mt-3 p-2 bg-slate-800/50 rounded">
                    <p className="text-red-400 font-mono text-lg font-bold text-center">{selectedNode.data?.score}</p>
                    <p className="text-slate-500 text-[10px] text-center">Risk Score (0-4 scale)</p>
                  </div>
                </div>
              )}

              {/* AI Explain Button */}
              <button
                onClick={handleExplainNode}
                disabled={explaining}
                className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white text-xs font-semibold disabled:opacity-50 transition-all"
              >
                {explaining ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                Explain with AI
              </button>

              {explanation && (
                <div className="bg-violet-900/30 border border-violet-500/40 rounded-lg p-3">
                  <p className="text-violet-300 text-xs font-semibold mb-2">💬 AI Explanation:</p>
                  <p className="text-slate-300 text-xs leading-relaxed whitespace-pre-line">{explanation}</p>
                </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* Instructions */}
      <div className="flex flex-wrap gap-3 text-[10px] text-slate-500">
        <span>🖱 <strong className="text-slate-400">Click clause</strong> → drill-down sentence nodes</span>
        <span>🔥 <strong className="text-slate-400">Heat overlay</strong> → color edges by risk intensity</span>
        <span>⏱ <strong className="text-slate-400">Time slider</strong> → simulate risk evolution over contract lifecycle</span>
        <span>🧠 <strong className="text-slate-400">Explain Node</strong> → AI explanation for selected node</span>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// LIVE FEED TAB
// ─────────────────────────────────────────────────────────

const LiveFeedTab = ({ contractId }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [jurisdiction, setJurisdiction] = useState('');
  const [crawling, setCrawling] = useState(false);
  const [sseIndex, setSseIndex] = useState(0);
  const [newCount, setNewCount] = useState(0);

  // Auto-simulation state
  const [simDesc, setSimDesc] = useState('');
  const [simType, setSimType] = useState('regulatory');
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [showSim, setShowSim] = useState(false);

  const intervalRef = useRef(null);
  const sseRef = useRef(null);

  const fetchEvents = async () => {
    try {
      const res = await getLiveEvents(jurisdiction, 30);
      setEvents(res.events || []);
    } catch { /* silent */ } finally {
      setLoading(false);
    }
  };

  // SSE-style polling for pushed events
  const pollSSE = async () => {
    try {
      const res = await pollSSEEvents(sseIndex);
      if (res.has_more) {
        setSseIndex(res.next_since);
        setNewCount(c => c + res.events.length);
        setEvents(prev => [...res.events, ...prev].slice(0, 50));
      }
    } catch { /* silent */ }
  };

  useEffect(() => {
    fetchEvents();
    intervalRef.current = setInterval(fetchEvents, 15000);
    sseRef.current = setInterval(pollSSE, 5000); // SSE poll every 5s
    return () => {
      clearInterval(intervalRef.current);
      clearInterval(sseRef.current);
    };
  }, [jurisdiction]);

  const handleCrawl = async () => {
    setCrawling(true);
    try {
      await triggerCrawler(jurisdiction || 'IN');
      setTimeout(fetchEvents, 2000);
    } catch { /* silent */ } finally {
      setCrawling(false);
    }
  };

  const handleSimulate = async () => {
    if (!simDesc.trim()) return;
    setSimLoading(true);
    setSimResult(null);
    try {
      const res = await simulateEvent(simDesc, simType, [], contractId);
      setSimResult(res);
    } catch {
      setSimResult({ error: 'Simulation failed.' });
    } finally {
      setSimLoading(false);
    }
  };

  const severityColor = (s) => {
    const sv = typeof s === 'number' ? (s > 0.7 ? 'HIGH' : s > 0.4 ? 'MEDIUM' : 'LOW') : (s || '').toUpperCase();
    if (sv === 'HIGH' || sv === 'CRITICAL') return 'text-red-400';
    if (sv === 'MEDIUM') return 'text-yellow-400';
    return 'text-green-400';
  };

  const severityLabel = (s) => {
    if (typeof s === 'number') return s > 0.7 ? 'HIGH' : s > 0.4 ? 'MEDIUM' : 'LOW';
    return s || 'INFO';
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2 border border-slate-700">
          <Globe size={14} className="text-slate-400" />
          <select value={jurisdiction} onChange={e => setJurisdiction(e.target.value)}
            className="bg-transparent text-slate-200 text-sm outline-none">
            <option value="">All Jurisdictions</option>
            <option value="IN">India</option>
            <option value="US">United States</option>
          </select>
        </div>
        <button onClick={fetchEvents}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
        <button onClick={handleCrawl} disabled={crawling}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-violet-600/80 hover:bg-violet-600 text-white text-sm disabled:opacity-50">
          {crawling ? <Loader2 size={14} className="animate-spin" /> : <Radio size={14} />}
          Trigger Crawler
        </button>
        <button onClick={() => setShowSim(s => !s)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition-all ${showSim ? 'bg-amber-500/20 border-amber-500/50 text-amber-300' : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'}`}>
          <Zap size={14} /> Auto-Simulate
        </button>
        <div className="flex items-center gap-2 ml-auto">
          {newCount > 0 && (
            <span className="bg-red-500/20 text-red-400 text-[10px] px-2 py-0.5 rounded-full border border-red-500/30 font-bold animate-pulse">
              +{newCount} new
            </span>
          )}
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-green-400 text-xs">SSE Live</span>
        </div>
      </div>

      {/* Auto What-If Simulation Panel (Feature 7) */}
      {showSim && (
        <div className="bg-amber-900/10 border border-amber-500/30 rounded-xl p-4 space-y-3">
          <p className="text-amber-300 text-sm font-semibold flex items-center gap-2">
            <Zap size={14} /> Auto What-If Simulation
          </p>
          <p className="text-slate-400 text-xs">Describe a legal event and the system will automatically simulate its impact on your contract's clauses using the Bayesian risk engine.</p>
          <div className="flex gap-2">
            <input
              value={simDesc}
              onChange={e => setSimDesc(e.target.value)}
              placeholder="E.g. RBI issues new payment regulation affecting vendor indemnity clauses…"
              className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500"
            />
            <select value={simType} onChange={e => setSimType(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500">
              <option value="regulatory">Regulatory</option>
              <option value="court_ruling">Court Ruling</option>
              <option value="geopolitical">Geopolitical</option>
              <option value="financial">Financial</option>
              <option value="arbitration">Arbitration</option>
            </select>
            <button onClick={handleSimulate} disabled={simLoading || !simDesc.trim()}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium disabled:opacity-50">
              {simLoading ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />} Simulate
            </button>
          </div>

          {simResult && (
            <div className="space-y-3 mt-2">
              {simResult.error ? (
                <p className="text-red-400 text-sm">{simResult.error}</p>
              ) : (
                <>
                  {/* Event Type Auto-Correction Warning */}
                  {simResult.warning && (
                    <div className="bg-orange-900/20 border border-orange-500/40 rounded-xl p-3 flex items-start gap-2">
                      <AlertTriangle size={16} className="text-orange-400 mt-0.5 shrink-0" />
                      <div>
                        <p className="text-orange-300 text-xs font-semibold mb-1">Event Type Auto-Corrected</p>
                        <p className="text-orange-200 text-xs">{simResult.warning}</p>
                      </div>
                    </div>
                  )}

                  <div className={`rounded-xl border p-3 ${simResult.overall_risk === 'HIGH' ? 'bg-red-500/10 border-red-500/40' : simResult.overall_risk === 'MEDIUM' ? 'bg-yellow-500/10 border-yellow-500/40' : 'bg-green-500/10 border-green-500/40'}`}>
                    <p className="text-slate-200 text-sm font-medium">{simResult.summary}</p>
                    <div className="flex gap-4 mt-2">
                      <div><p className="text-slate-500 text-xs">Overall Risk</p><p className={`font-bold text-sm ${simResult.overall_risk === 'HIGH' ? 'text-red-400' : simResult.overall_risk === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400'}`}>{simResult.overall_risk}</p></div>
                      <div><p className="text-slate-500 text-xs">Exposure Units</p><p className="text-amber-400 font-bold text-sm">{simResult.total_exposure_units}</p></div>
                      <div><p className="text-slate-500 text-xs">Base Weight</p><p className="text-slate-300 font-bold text-sm">{((simResult.base_risk_weight || 0) * 100).toFixed(0)}%</p></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {(simResult.clause_simulations || []).map((cs, i) => (
                      <div key={i} className="bg-slate-800/60 border border-slate-700/40 rounded-lg p-3 flex items-center gap-3">
                        <RiskBadge level={cs.risk_level} />
                        <div className="flex-1">
                          <p className="text-slate-200 text-xs font-medium">{cs.clause_type}</p>
                          <p className="text-slate-500 text-[10px]">{cs.recommended_action}</p>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-amber-400 text-xs font-mono">{cs.risk_score}</p>
                          <p className="text-slate-600 text-[9px]">
                            {Array.isArray(cs.supporting_cases) ? cs.supporting_cases.length : (cs.supporting_cases || 0)} cases
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Events list */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-violet-400" />
        </div>
      ) : events.length === 0 ? (
        <p className="text-slate-500 text-center py-8">No events found.</p>
      ) : (
        <div className="space-y-2">
          {events.map((ev, i) => (
            <div key={i} className={`bg-slate-800/60 rounded-xl border border-slate-700/50 p-4 ${i === 0 && newCount > 0 ? 'ring-1 ring-green-500/30' : ''}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-bold ${severityColor(ev.severity)}`}>{severityLabel(ev.severity)}</span>
                    <span className="text-slate-500 text-xs">·</span>
                    <span className="text-slate-400 text-xs">{ev.jurisdiction || '—'}</span>
                    <span className="text-slate-500 text-xs">·</span>
                    <span className="text-slate-400 text-xs">{ev.event_type || ev.type || '—'}</span>
                    {i === 0 && newCount > 0 && <span className="bg-green-500/20 text-green-400 text-[9px] px-1.5 py-0.5 rounded-full">NEW</span>}
                  </div>
                  <p className="text-slate-200 text-sm font-medium">{ev.title || ev.headline}</p>
                  <p className="text-slate-400 text-xs mt-1 line-clamp-2">{ev.summary || ev.description}</p>
                  {ev.clauses_affected?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {ev.clauses_affected.map((t, ti) => {
                        // Handle both string and object formats
                        const displayText = typeof t === 'string' ? t : (t?.clause_type || t?.case_name || t?.type || JSON.stringify(t));
                        return (
                          <span key={ti} className="bg-amber-500/20 text-amber-300 text-[10px] px-1.5 py-0.5 rounded">
                            {displayText}
                          </span>
                        );
                      })}
                    </div>
                  )}
                  {ev.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {ev.tags.map((t, ti) => {
                        // Handle both string and object formats
                        const tagText = typeof t === 'string' ? t : (t?.name || t?.tag || String(t));
                        return (
                          <span key={ti} className="bg-blue-500/20 text-blue-300 text-[10px] px-1.5 py-0.5 rounded">{tagText}</span>
                        );
                      })}
                    </div>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <p className="text-slate-500 text-xs">{ev.source || '—'}</p>
                  <p className="text-slate-600 text-[10px] mt-0.5">
                    {ev.published_at ? new Date(ev.published_at).toLocaleDateString() : ev.timestamp ? new Date(ev.timestamp).toLocaleDateString() : '—'}
                  </p>
                  {ev.auto_simulated && (
                    <span className="text-amber-400 text-[9px]">⚡ simulated</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// LEGAL CO-PILOT TAB
// ─────────────────────────────────────────────────────────

// ─── Agent config ────────────────────────────────────────
const AGENTS = [
  {
    key: 'risk_agent',
    label: 'Risk Agent',
    short: 'RA',
    icon: Shield,
    color: 'text-red-400',
    border: 'border-red-500/40',
    bg: 'bg-red-500/10',
    dot: 'bg-red-400',
    badge: 'bg-red-500/20 text-red-300',
    glow: 'shadow-red-500/20',
  },
  {
    key: 'negotiation_agent',
    label: 'Negotiation Agent',
    short: 'NA',
    icon: TrendingUp,
    color: 'text-amber-400',
    border: 'border-amber-500/40',
    bg: 'bg-amber-500/10',
    dot: 'bg-amber-400',
    badge: 'bg-amber-500/20 text-amber-300',
    glow: 'shadow-amber-500/20',
  },
  {
    key: 'litigation_agent',
    label: 'Litigation Agent',
    short: 'LA',
    icon: Gavel,
    color: 'text-blue-400',
    border: 'border-blue-500/40',
    bg: 'bg-blue-500/10',
    dot: 'bg-blue-400',
    badge: 'bg-blue-500/20 text-blue-300',
    glow: 'shadow-blue-500/20',
  },
];

const SUGGESTED_PROMPTS = [
  { icon: AlertTriangle, text: 'Which clauses pose the highest liability exposure?' },
  { icon: Shield,        text: 'What indemnity risks should I be aware of?' },
  { icon: TrendingUp,    text: 'How can I negotiate better termination terms?' },
  { icon: Gavel,         text: 'What is the litigation probability for this contract?' },
  { icon: Globe,         text: 'Are there any jurisdictional risks?' },
  { icon: Lightbulb,     text: 'Are there any ambiguous terms that need clarification?' },
];

const AgentResponseCard = ({ agentCfg, text }) => {
  const Icon = agentCfg.icon;
  const renderLines = (t) =>
    t.split('\n').map((line, i) => {
      if (!line.trim()) return <div key={i} className="h-2" />;
      if (line.includes('**')) {
        const parts = line.split('**');
        return (
          <p key={i} className="leading-relaxed">
            {parts.map((p, pi) =>
              pi % 2 === 1
                ? <strong key={pi} className={`${agentCfg.color} font-semibold`}>{p}</strong>
                : <span key={pi} className="text-slate-300">{p}</span>
            )}
          </p>
        );
      }
      // bullet-like lines starting with (1), (2)…
      if (/^\(\d+\)/.test(line)) {
        return (
          <div key={i} className="flex gap-2 items-start mt-1">
            <span className={`mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${agentCfg.dot}`} />
            <p className="text-slate-300 leading-relaxed">{line}</p>
          </div>
        );
      }
      return <p key={i} className="text-slate-300 leading-relaxed">{line}</p>;
    });

  return (
    <div className={`rounded-xl border ${agentCfg.border} ${agentCfg.bg} p-4 shadow-lg ${agentCfg.glow}`}>
      {/* Agent header */}
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${agentCfg.bg} border ${agentCfg.border}`}>
          <Icon size={14} className={agentCfg.color} />
        </div>
        <span className={`text-xs font-bold uppercase tracking-widest ${agentCfg.color}`}>{agentCfg.label}</span>
        <span className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-semibold ${agentCfg.badge}`}>AI</span>
      </div>
      {/* Content */}
      <div className="text-sm space-y-1">{renderLines(text)}</div>
    </div>
  );
};

const CopilotTab = ({ contractId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingDots, setLoadingDots] = useState('');
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Animated loading dots
  useEffect(() => {
    if (!loading) return;
    const iv = setInterval(() => setLoadingDots(d => d.length >= 3 ? '' : d + '.'), 400);
    return () => clearInterval(iv);
  }, [loading]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (override) => {
    const q = (override || input).trim();
    if (!q || loading) return;
    setInput('');
    setMessages(m => [...m, { role: 'user', text: q }]);
    setLoading(true);
    try {
      const res = await queryCopilot(q, contractId);
      const agents = res.agents || {};
      setMessages(m => [...m, { role: 'assistant', agents }]);
    } catch {
      setMessages(m => [...m, { role: 'error', text: 'Failed to reach Legal Co-Pilot. Please try again.' }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-[620px] relative">

      {/* ── Header bar ───────────────────────────────────── */}
      <div className="flex items-center gap-3 px-1 pb-4 border-b border-slate-700/60 mb-4 flex-shrink-0">
        <div className="w-9 h-9 rounded-xl bg-violet-600/20 border border-violet-500/40 flex items-center justify-center shadow-lg shadow-violet-500/10">
          <Brain size={18} className="text-violet-400" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-none">Legal Co-Pilot</p>
          <p className="text-[11px] text-slate-400 mt-0.5">3 specialized AI agents · Risk · Negotiation · Litigation</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {AGENTS.map(a => (
            <div key={a.key} title={a.label}
              className={`w-6 h-6 rounded-lg flex items-center justify-center ${a.bg} border ${a.border}`}>
              <a.icon size={11} className={a.color} />
            </div>
          ))}
          <span className="ml-1 flex items-center gap-1 text-[10px] text-emerald-400 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Online
          </span>
        </div>
      </div>

      {/* ── Messages area ────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto space-y-5 pr-1 pb-2"
        style={{ scrollbarWidth: 'thin', scrollbarColor: '#334155 transparent' }}>

        {/* Empty state */}
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center px-6 gap-6">
            <div className="w-16 h-16 rounded-2xl bg-violet-600/15 border border-violet-500/30 flex items-center justify-center shadow-xl shadow-violet-500/10">
              <Sparkles size={28} className="text-violet-400" />
            </div>
            <div>
              <p className="text-white font-semibold text-base mb-1">Ask anything about this contract</p>
              <p className="text-slate-400 text-sm">Three specialized agents will analyse risks, negotiation strategy, and litigation exposure in parallel.</p>
            </div>
            {/* Suggested prompts */}
            <div className="w-full grid grid-cols-2 gap-2 mt-2">
              {SUGGESTED_PROMPTS.map((sp, i) => (
                <button key={i} onClick={() => send(sp.text)}
                  className="flex items-start gap-2 text-left px-3 py-2.5 rounded-xl bg-slate-800/70 border border-slate-700/60 hover:border-violet-500/50 hover:bg-violet-500/10 transition-all text-xs text-slate-300 hover:text-white group">
                  <sp.icon size={13} className="text-violet-400 mt-0.5 flex-shrink-0 group-hover:scale-110 transition-transform" />
                  {sp.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((m, i) => (
          <div key={i}>
            {/* User bubble */}
            {m.role === 'user' && (
              <div className="flex justify-end">
                <div className="max-w-[72%] flex flex-col items-end gap-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] text-slate-500">You</span>
                    <div className="w-5 h-5 rounded-full bg-violet-600 flex items-center justify-center">
                      <span className="text-[9px] font-bold text-white">U</span>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-violet-600 to-violet-700 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-2.5 shadow-lg shadow-violet-500/20 leading-relaxed">
                    {m.text}
                  </div>
                </div>
              </div>
            )}

            {/* Assistant multi-agent response */}
            {m.role === 'assistant' && (
              <div className="flex justify-start">
                <div className="w-full max-w-[96%]">
                  <div className="flex items-center gap-2 mb-2 ml-1">
                    <div className="w-5 h-5 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center">
                      <Brain size={10} className="text-violet-400" />
                    </div>
                    <span className="text-[10px] text-slate-500">Legal Co-Pilot · 3 Agents</span>
                  </div>
                  <div className="space-y-3">
                    {AGENTS.map(agentCfg =>
                      m.agents?.[agentCfg.key] ? (
                        <AgentResponseCard key={agentCfg.key} agentCfg={agentCfg} text={m.agents[agentCfg.key]} />
                      ) : null
                    )}
                    {!m.agents && m.text && (
                      <div className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-300">{m.text}</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {m.role === 'error' && (
              <div className="flex justify-center">
                <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-2.5 text-xs text-red-400">
                  <XCircle size={13} /> {m.text}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="w-full max-w-[96%]">
              <div className="flex items-center gap-2 mb-2 ml-1">
                <div className="w-5 h-5 rounded-full bg-violet-500/20 border border-violet-500/40 flex items-center justify-center">
                  <Brain size={10} className="text-violet-400" />
                </div>
                <span className="text-[10px] text-slate-500">Legal Co-Pilot · Agents thinking{loadingDots}</span>
              </div>
              <div className="space-y-3">
                {AGENTS.map(agentCfg => (
                  <div key={agentCfg.key} className={`rounded-xl border ${agentCfg.border} ${agentCfg.bg} p-4 animate-pulse`}>
                    <div className="flex items-center gap-2 mb-3">
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${agentCfg.bg} border ${agentCfg.border}`}>
                        <agentCfg.icon size={14} className={agentCfg.color} />
                      </div>
                      <span className={`text-xs font-bold uppercase tracking-widest ${agentCfg.color}`}>{agentCfg.label}</span>
                    </div>
                    <div className="space-y-2">
                      <div className="h-2.5 bg-slate-700/60 rounded w-4/5" />
                      <div className="h-2.5 bg-slate-700/60 rounded w-3/5" />
                      <div className="h-2.5 bg-slate-700/60 rounded w-2/3" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ────────────────────────────────────── */}
      <div className="flex-shrink-0 pt-3 border-t border-slate-700/60 mt-2">
        <div className={`flex items-end gap-2 bg-slate-800/80 border rounded-2xl px-3 py-2 transition-all ${
          input ? 'border-violet-500/60 shadow-lg shadow-violet-500/10' : 'border-slate-700'
        }`}>
          <Sparkles size={15} className="text-violet-500 mb-1.5 flex-shrink-0" />
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={e => {
              setInput(e.target.value);
              // auto-grow
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 96) + 'px';
            }}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
            }}
            placeholder="Ask about risks, negotiation strategy, litigation exposure…"
            className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none resize-none leading-relaxed py-1"
            style={{ minHeight: '24px', maxHeight: '96px' }}
          />
          <button
            onClick={() => send()}
            disabled={loading || !input.trim()}
            className="flex-shrink-0 mb-0.5 w-8 h-8 rounded-xl flex items-center justify-center bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-violet-500/30"
          >
            <ArrowRight size={15} className="text-white" />
          </button>
        </div>
        <p className="text-[10px] text-slate-600 text-center mt-2">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// RAG SEARCH TAB
// ─────────────────────────────────────────────────────────

// ── RAG answer parser ─────────────────────────────────────
const parseRAGAnswer = (raw = '') => {
  // Strip leading **Query:** echo if present
  let text = raw.replace(/^\*\*Query:\*\*.*?((\*\*Analysis)|(\*\*Relevant)|(\*\*Risk)|(\*\*Recommendation))/s, '$1').trim();
  if (!text) text = raw;

  const result = { analysis: '', cases: [], riskLevel: '', recommendation: '', raw: '' };

  // Extract Analysis block
  const analysisMatch = text.match(/\*\*Analysis:\*\*\s*([\s\S]*?)(?=\*\*Relevant Case|\*\*Risk Level|\*\*Recommendation|$)/i);
  if (analysisMatch) result.analysis = analysisMatch[1].trim();

  // Extract all Relevant Cases
  const caseRegex = /\*\*Relevant Case \d+:\*\*\s*([\s\S]*?)(?=\*\*Relevant Case \d+|\*\*Risk Level|\*\*Recommendation|$)/gi;
  let m;
  while ((m = caseRegex.exec(text)) !== null) {
    const caseText = m[1].trim();

    // Helper: does this string look like a case name?
    // Matches: "Penney v. Arcuri [2018]", "Laidlaw Environmental Services v Aon [2008]", "Photo Production Ltd v Securicor [1980]"
    const CASE_NAME_RE = /^([A-Z][A-Za-z\s.,&'()]+(?:\[|\()\d{4}(?:\]|\)))/;

    // Pattern 1: "[CL016] Case Name [year]: desc" — bracketed ID then name
    const bracketNameColon = caseText.match(/^\[([A-Z]{2}\d{3,4})\]\s*(.+?):\s*([\s\S]+)$/);
    if (bracketNameColon) {
      result.cases.push({ title: bracketNameColon[2].trim(), id: bracketNameColon[1], desc: bracketNameColon[3].trim() });
    }
    // Pattern 2: "Case Name [year], where/which desc" — name ends at comma
    else if (CASE_NAME_RE.test(caseText)) {
      const nameMatch = caseText.match(/^([A-Z][A-Za-z\s.,&'()]+(?:\[|\()\d{4}(?:\]|\)))[,:\s—]+(.+)$/s);
      if (nameMatch) {
        result.cases.push({ title: nameMatch[1].trim(), desc: nameMatch[2].trim() });
      } else {
        result.cases.push({ title: caseText, desc: '' });
      }
    }
    // Pattern 3: "[CL016] desc only"
    else if (/^\[[A-Z]{2}\d{3,4}\]/.test(caseText)) {
      const bracketOnly = caseText.match(/^\[([A-Z]{2}\d{3,4})\]\s*([\s\S]+)$/);
      result.cases.push({ title: bracketOnly[1], id: bracketOnly[1], desc: bracketOnly[2].trim() });
    }
    // Pattern 4: "CL016 Name [year]: desc"
    else if (/^[A-Z]{2}\d{3,4}\s/.test(caseText)) {
      const bareId = caseText.match(/^([A-Z]{2}\d{3,4})\s+(.+?)(?::\s*([\s\S]+))?$/);
      if (bareId && bareId[3]) {
        result.cases.push({ title: bareId[2].trim(), id: bareId[1], desc: bareId[3].trim() });
      } else if (bareId) {
        result.cases.push({ title: bareId[1], id: bareId[1], desc: bareId[2].trim() });
      } else {
        result.cases.push({ title: `Case ${result.cases.length + 1}`, desc: caseText });
      }
    }
    // Fallback
    else {
      result.cases.push({ title: `Case ${result.cases.length + 1}`, desc: caseText });
    }
  }

  // Extract Risk Level
  const riskMatch = text.match(/\*\*Risk Level:\*\*\s*([^\n*]+)/i);
  if (riskMatch) result.riskLevel = riskMatch[1].trim();

  // Extract Recommendation
  const recMatch = text.match(/\*\*Recommendation:\*\*\s*([\s\S]+?)(?=$|\*\*)/i);
  if (recMatch) result.recommendation = recMatch[1].trim();

  // Fallback: if nothing parsed, keep raw
  if (!result.analysis && !result.cases.length && !result.riskLevel) result.raw = raw;
  return result;
};

const RAG_SUGGESTIONS = [
  'Show me all payment terms and schedules',
  'What indemnity clauses are present?',
  'Find all termination provisions',
  'Identify jurisdiction and governing law clauses',
  'What are the liability caps in this contract?',
  'List all obligation clauses',
];

const RAGSearchTab = ({ contractId }) => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState('');
  const [expandedClauses, setExpandedClauses] = useState({});
  const [allExpanded, setAllExpanded] = useState(false);

  const toggleClause = (idx) => setExpandedClauses(prev => ({ ...prev, [idx]: !prev[idx] }));
  const toggleAll = (clauses) => {
    const next = !allExpanded;
    setAllExpanded(next);
    const all = {};
    clauses.forEach((_, i) => { all[i] = next; });
    setExpandedClauses(all);
  };

  const search = async (override) => {
    const q = (override || query).trim();
    if (!q) return;
    if (override) setQuery(override);
    setLoading(true);
    setResult(null);
    setExpandedClauses({});
    setAllExpanded(false);
    setSearched(q);
    try {
      const res = await ragSearch(q, contractId);
      setResult(res);
    } catch {
      setResult({ error: 'Search failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const parsed = result?.answer ? parseRAGAnswer(result.answer) : null;
  const riskColor = parsed?.riskLevel?.toUpperCase().includes('HIGH')
    ? { text: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/40' }
    : parsed?.riskLevel?.toUpperCase().includes('MEDIUM')
    ? { text: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/40' }
    : { text: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/40' };

  return (
    <div className="space-y-5">

      {/* ── Header ─────────────────────────────────────── */}
      <div className="flex items-center gap-3 pb-4 border-b border-slate-700/60">
        <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center shadow-lg shadow-blue-500/10">
          <Search size={17} className="text-blue-400" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-none">RAG Search</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Retrieval-Augmented Generation · AI hybrid retrieval</p>
        </div>
      </div>

      {/* ── Search bar ─────────────────────────────────── */}
      <div className={`flex items-center gap-2 bg-slate-800/80 border rounded-2xl px-4 py-2.5 transition-all ${
        query ? 'border-blue-500/60 shadow-lg shadow-blue-500/10' : 'border-slate-700'
      }`}>
        <Search size={15} className="text-blue-400 flex-shrink-0" />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          placeholder="Ask about indemnity clauses, payment terms, jurisdiction risks…"
          className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none py-1"
        />
        <button
          onClick={() => search()}
          disabled={loading || !query.trim()}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold disabled:opacity-40 transition-all shadow-md shadow-blue-500/30 flex-shrink-0"
        >
          {loading ? <Loader2 size={12} className="animate-spin" /> : <Search size={12} />}
          Search
        </button>
      </div>

      {/* ── Suggestion chips (shown when no result yet) ── */}
      {!result && !loading && (
        <div>
          <p className="text-[11px] text-slate-500 mb-2 font-medium uppercase tracking-wider">Suggested queries</p>
          <div className="flex flex-wrap gap-2">
            {RAG_SUGGESTIONS.map((s, i) => (
              <button key={i} onClick={() => search(s)}
                className="text-xs px-3 py-1.5 rounded-full border border-slate-700 bg-slate-800/60 text-slate-300 hover:border-blue-500/50 hover:bg-blue-500/10 hover:text-blue-300 transition-all">
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Loading skeleton ────────────────────────────── */}
      {loading && (
        <div className="space-y-4 animate-pulse">
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 space-y-3">
            <div className="h-3 bg-slate-700/60 rounded w-24" />
            <div className="h-2.5 bg-slate-700/60 rounded w-full" />
            <div className="h-2.5 bg-slate-700/60 rounded w-4/5" />
            <div className="h-2.5 bg-slate-700/60 rounded w-3/5" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[1,2,3,4].map(n => (
              <div key={n} className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4 space-y-2">
                <div className="h-2.5 bg-slate-700/60 rounded w-3/4" />
                <div className="h-2 bg-slate-700/40 rounded w-full" />
                <div className="h-2 bg-slate-700/40 rounded w-5/6" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Result ─────────────────────────────────────── */}
      {result && !loading && (
        <div className="space-y-4">
          {result.error ? (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400">
              <XCircle size={14} /> {result.error}
            </div>
          ) : parsed && !parsed.raw ? (
            <>
              {/* Query echo */}
              <div className="flex items-center gap-2 bg-blue-500/8 border border-blue-500/20 rounded-xl px-4 py-2.5">
                <Search size={12} className="text-blue-400 flex-shrink-0" />
                <p className="text-xs text-blue-300"><span className="text-slate-500 mr-1">Query:</span>{searched}</p>
              </div>

              {/* Analysis block */}
              {parsed.analysis && (
                <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-violet-500/20 border border-violet-500/40 flex items-center justify-center">
                      <Brain size={12} className="text-violet-400" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-widest text-violet-400">Analysis</span>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">{parsed.analysis}</p>
                </div>
              )}

              {/* Relevant Cases grid */}
              {parsed.cases.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
                      <BookOpen size={12} className="text-amber-400" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-widest text-amber-400">Relevant Cases</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold">{parsed.cases.length}</span>
                  </div>
                  <div className="grid grid-cols-1 gap-3">
                    {parsed.cases.map((c, i) => {
                      // If title is just a bare ID (e.g. "CL001"), try to pull case name from start of desc
                      const isBareId = /^[A-Z]{2}\d{3,4}$/.test(c.title.trim()) && !c.desc;
                      const caseNameMatch = c.desc?.match(/^((?:In\s+)?[A-Z][^:.]{5,80}(?:\[\d{4}\]|\(\d{4}\)))[:\s—]/);
                      const displayTitle = isBareId
                        ? (caseNameMatch ? caseNameMatch[1].trim() : c.title)
                        : c.title;
                      const caseId = c.id || (isBareId ? c.title : null);
                      const displayDesc = (isBareId && caseNameMatch)
                        ? c.desc.slice(caseNameMatch[0].length).trim()
                        : c.desc;
                      return (
                        <div key={i} className="bg-slate-800/50 border border-amber-500/20 rounded-xl p-4 flex gap-3">
                          <div className="w-7 h-7 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-[10px] font-bold text-amber-400">{i + 1}</span>
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                              <p className="text-xs font-semibold text-amber-300">{displayTitle}</p>
                              {caseId && (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 font-mono">{caseId}</span>
                              )}
                            </div>
                            <p className="text-xs text-slate-300 leading-relaxed">{displayDesc}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Risk Level + Recommendation row */}
              <div className="grid grid-cols-2 gap-3">
                {parsed.riskLevel && (
                  <div className={`rounded-xl border ${riskColor.border} ${riskColor.bg} p-4`}>
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={13} className={riskColor.text} />
                      <span className={`text-xs font-bold uppercase tracking-widest ${riskColor.text}`}>Risk Level</span>
                    </div>
                    <p className={`text-sm font-semibold ${riskColor.text}`}>{parsed.riskLevel}</p>
                  </div>
                )}
                {parsed.recommendation && (
                  <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle size={13} className="text-emerald-400" />
                      <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">Recommendation</span>
                    </div>
                    <p className="text-xs text-emerald-200 leading-relaxed">{parsed.recommendation}</p>
                  </div>
                )}
              </div>

              {/* Retrieved Clauses */}
              {result.retrieved_clauses?.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center">
                      <FileText size={12} className="text-blue-400" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-widest text-blue-400">Retrieved Clauses</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-semibold">{result.retrieved_clauses.length}</span>
                    <button
                      onClick={() => toggleAll(result.retrieved_clauses)}
                      className="ml-auto flex items-center gap-1 text-[10px] px-2.5 py-1 rounded-lg bg-slate-700/60 hover:bg-slate-600/60 text-slate-300 hover:text-white border border-slate-600/50 transition-all font-medium"
                    >
                      {allExpanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                      {allExpanded ? 'Collapse All' : 'Expand All'}
                    </button>
                  </div>
                  <div className="space-y-2">
                    {result.retrieved_clauses.map((cl, i) => {
                      const isRelevant = cl.score > 0;
                      const isExpanded = !!expandedClauses[i];
                      const isLong = (cl.text || '').length > 200;
                      return (
                        <div key={i} className={`border rounded-xl transition-all ${
                          isRelevant ? 'bg-blue-500/5 border-blue-500/25' : 'bg-slate-800/40 border-slate-700/40'
                        }`}>
                          <div className="flex gap-3 p-3">
                            <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                              isRelevant ? 'bg-blue-500/20 border border-blue-500/40' : 'bg-slate-700/50 border border-slate-600/40'
                            }`}>
                              <span className={`text-[9px] font-bold ${isRelevant ? 'text-blue-400' : 'text-slate-500'}`}>{i + 1}</span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                <span className={`text-xs font-semibold ${isRelevant ? 'text-blue-300' : 'text-slate-400'}`}>
                                  {cl.clause_type || `Clause ${i + 1}`}
                                </span>
                                {isRelevant && (
                                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-semibold">Relevant</span>
                                )}
                                {isLong && (
                                  <button
                                    onClick={() => toggleClause(i)}
                                    className={`ml-auto flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-md transition-all font-medium ${
                                      isExpanded
                                        ? 'text-blue-400 bg-blue-500/10 hover:bg-blue-500/20'
                                        : 'text-slate-400 hover:text-blue-300 bg-slate-700/40 hover:bg-slate-600/60'
                                    }`}
                                  >
                                    {isExpanded ? <><ChevronUp size={10} /> Show less</> : <><ChevronDown size={10} /> View full text</>}
                                  </button>
                                )}
                              </div>
                              <p className={`text-slate-300 text-xs leading-relaxed ${isExpanded ? '' : 'line-clamp-3'}`}>
                                {cl.text}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Fallback: plain answer if parsing yields nothing structured */
            <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Brain size={13} className="text-blue-400" />
                <span className="text-xs font-bold uppercase tracking-widest text-blue-400">RAG Answer</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{result.answer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// GRAPHRAG TAB
// ─────────────────────────────────────────────────────────

const GRAPHRAG_EXAMPLES = [
  { label: 'Indemnity obligations', query: 'What are the indemnity obligations under English law in this contract?' },
  { label: 'Liability caps', query: 'What limitation of liability clauses exist and how are damages capped?' },
  { label: 'Termination rights', query: 'What are the termination rights and notice requirements for both parties?' },
  { label: 'Governing law', query: 'What jurisdiction and governing law applies to disputes in this contract?' },
  { label: 'Confidentiality scope', query: 'What are the confidentiality obligations and how long do they survive termination?' },
  { label: 'Payment obligations', query: 'What are the payment terms and consequences of non-payment?' },
];

const ENTITY_COLORS = {
  clause_types: { bg: 'bg-violet-500/20', text: 'text-violet-300', border: 'border-violet-500/30', label: 'Clause' },
  jurisdiction:  { bg: 'bg-blue-500/20',   text: 'text-blue-300',   border: 'border-blue-500/30',   label: 'Jurisdiction' },
  parties:       { bg: 'bg-emerald-500/20', text: 'text-emerald-300',border: 'border-emerald-500/30',label: 'Party' },
  event_type:    { bg: 'bg-amber-500/20',   text: 'text-amber-300',  border: 'border-amber-500/30',  label: 'Event' },
};

const GraphRAGTab = ({ contractId }) => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState('');

  const search = async (override) => {
    const q = (override || query).trim();
    if (!q) return;
    if (override) setQuery(override);
    setLoading(true);
    setResult(null);
    setSearched(q);
    try {
      const res = await graphRagSearch(q, contractId);
      setResult(res);
    } catch {
      setResult({ error: 'GraphRAG search failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const hasEntities = result?.entities && Object.values(result.entities).some(v =>
    Array.isArray(v) ? v.length > 0 : !!v
  );

  return (
    <div className="space-y-5">

      {/* ── Header ─────────────────────────────────────── */}
      <div className="flex items-center gap-3 pb-4 border-b border-slate-700/60">
        <div className="w-9 h-9 rounded-xl bg-violet-600/20 border border-violet-500/40 flex items-center justify-center shadow-lg shadow-violet-500/10">
          <Cpu size={17} className="text-violet-400" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-none">GraphRAG Analysis</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Entity extraction · Knowledge graph traversal · Grounded answers</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          {['Entities', 'Graph', 'Cases', 'Answer'].map((s, i) => (
            <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-700/60 text-slate-400 font-mono">{s}</span>
          ))}
          <span className="text-slate-600 text-xs ml-1">→ pipeline</span>
        </div>
      </div>

      {/* ── Search bar ─────────────────────────────────── */}
      <div className={`flex items-center gap-2 bg-slate-800/80 border rounded-2xl px-4 py-2.5 transition-all ${
        query ? 'border-violet-500/60 shadow-lg shadow-violet-500/10' : 'border-slate-700'
      }`}>
        <Cpu size={15} className="text-violet-400 flex-shrink-0" />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          placeholder="e.g. What are the indemnity obligations under English law?"
          className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none py-1"
        />
        <button
          onClick={() => search()}
          disabled={loading || !query.trim()}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold disabled:opacity-40 transition-all shadow-md shadow-violet-500/30 flex-shrink-0"
        >
          {loading ? <Loader2 size={12} className="animate-spin" /> : <Cpu size={12} />}
          Analyze
        </button>
      </div>

      {/* ── Example queries ────────────────────────────── */}
      {!result && !loading && (
        <div>
          <p className="text-[11px] text-slate-500 mb-2 font-medium uppercase tracking-wider">Example queries — click to run</p>
          <div className="grid grid-cols-2 gap-2">
            {GRAPHRAG_EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => search(ex.query)}
                className="text-left px-3 py-2.5 rounded-xl border border-slate-700 bg-slate-800/60 hover:border-violet-500/50 hover:bg-violet-500/10 transition-all group">
                <p className="text-xs font-semibold text-violet-400 group-hover:text-violet-300 mb-0.5">{ex.label}</p>
                <p className="text-[11px] text-slate-400 group-hover:text-slate-300 leading-relaxed">{ex.query}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Loading ────────────────────────────────────── */}
      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-4 space-y-2">
            <div className="h-2.5 bg-slate-700/60 rounded w-32" />
            <div className="flex gap-2 flex-wrap">
              {[1,2,3].map(n => <div key={n} className="h-5 w-20 bg-slate-700/60 rounded-full" />)}
            </div>
          </div>
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 space-y-3">
            <div className="h-3 bg-slate-700/60 rounded w-28" />
            <div className="h-2.5 bg-slate-700/60 rounded w-full" />
            <div className="h-2.5 bg-slate-700/60 rounded w-4/5" />
            <div className="h-2.5 bg-slate-700/60 rounded w-3/5" />
          </div>
        </div>
      )}

      {/* ── Results ────────────────────────────────────── */}
      {result && !loading && (
        <div className="space-y-4">
          {result.error ? (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400">
              <XCircle size={14} /> {result.error}
            </div>
          ) : (
            <>
              {/* Query echo */}
              <div className="flex items-center gap-2 bg-violet-500/8 border border-violet-500/20 rounded-xl px-4 py-2.5">
                <Cpu size={12} className="text-violet-400 flex-shrink-0" />
                <p className="text-xs text-violet-300"><span className="text-slate-500 mr-1">Query:</span>{searched}</p>
              </div>

              {/* Extracted Entities */}
              {hasEntities && (
                <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-violet-500/20 border border-violet-500/40 flex items-center justify-center">
                      <Sparkles size={11} className="text-violet-400" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-widest text-violet-400">Extracted Entities</span>
                    <span className="text-[10px] text-slate-500 ml-1">from your query</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(result.entities).map(([type, vals]) => {
                      const cfg = ENTITY_COLORS[type] || ENTITY_COLORS.clause_types;
                      const items = Array.isArray(vals) ? vals.filter(Boolean) : (vals ? [vals] : []);
                      return items.map((v, i) => (
                        <span key={`${type}-${i}`} className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
                          <span className="text-[9px] opacity-60 uppercase">{cfg.label}</span>
                          <span className="font-semibold">{v}</span>
                        </span>
                      ));
                    })}
                  </div>
                </div>
              )}

              {/* Answer — parsed structured rendering */}
              {result.answer && (() => {
                const raw = result.answer;
                // Parse sections: **Summary:**, **Risk:**, **Key Cases:**, **Recommendation:**
                const getSection = (label) => {
                  const re = new RegExp(`\\*\\*${label}:\\*\\*\\s*([\\s\\S]*?)(?=\\*\\*[A-Z]|$)`, 'i');
                  const m = raw.match(re);
                  return m ? m[1].trim() : null;
                };
                const summary = getSection('Summary');
                const risk = getSection('Risk');
                const keyCases = getSection('Key Cases');
                const recommendation = getSection('Recommendation');
                const hasSections = summary || risk || keyCases || recommendation;

                const riskWord = risk?.match(/^(LOW|MEDIUM|HIGH)/i)?.[1]?.toUpperCase();
                const riskStyle = riskWord === 'HIGH'
                  ? 'text-red-400 bg-red-500/10 border-red-500/30'
                  : riskWord === 'LOW'
                  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                  : 'text-amber-400 bg-amber-500/10 border-amber-500/30';

                if (!hasSections) {
                  // Plain text fallback
                  return (
                    <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                          <Brain size={12} className="text-emerald-400" />
                        </div>
                        <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">GraphRAG Answer</span>
                      </div>
                      <p className="text-sm text-slate-200 leading-relaxed">{raw}</p>
                    </div>
                  );
                }

                return (
                  <div className="space-y-3">
                    {/* Summary */}
                    {summary && (
                      <div className="bg-slate-800/70 border border-slate-700/60 rounded-2xl p-5">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-6 h-6 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                            <Brain size={12} className="text-emerald-400" />
                          </div>
                          <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">Summary</span>
                        </div>
                        <p className="text-sm text-slate-200 leading-relaxed">{summary}</p>
                      </div>
                    )}

                    {/* Risk + Recommendation side by side */}
                    {(risk || recommendation) && (
                      <div className="grid grid-cols-2 gap-3">
                        {risk && (
                          <div className={`rounded-xl border p-4 ${riskStyle}`}>
                            <div className="flex items-center gap-2 mb-2">
                              <AlertTriangle size={13} />
                              <span className="text-xs font-bold uppercase tracking-widest">Risk Level</span>
                            </div>
                            <p className="text-sm font-semibold">{risk}</p>
                          </div>
                        )}
                        {recommendation && (
                          <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <CheckCircle size={13} className="text-violet-400" />
                              <span className="text-xs font-bold uppercase tracking-widest text-violet-400">Recommendation</span>
                            </div>
                            <p className="text-xs text-violet-200 leading-relaxed">{recommendation}</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Key Cases */}
                    {keyCases && (
                      <div className="bg-slate-800/60 border border-amber-500/20 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-3">
                          <BookOpen size={12} className="text-amber-400" />
                          <span className="text-xs font-bold uppercase tracking-widest text-amber-400">Key Cases</span>
                        </div>
                        <div className="space-y-2">
                          {keyCases.split('\n')
                            .map(l => l.trim())
                            .filter(l => l.length > 2)
                            .map((line, i) => {
                              // Strip leading bullet chars: -, *, •, numbers like "1.", "Case 1:"
                              const content = line
                                .replace(/^[-*•]\s*/, '')
                                .replace(/^\d+\.\s*/, '')
                                .replace(/^Case\s+\d+:\s*/i, '')
                                .trim();
                              if (!content) return null;
                              // Split on first colon to get case name vs description
                              const colonIdx = content.indexOf(':');
                              const rawName = colonIdx > 0 ? content.slice(0, colonIdx).trim() : '';
                              const caseDesc = colonIdx > 0 ? content.slice(colonIdx + 1).trim() : content;
                              // Strip ** from name — if rawName looks like a real case name (has v or [year])
                              const cleanedName = rawName.replace(/\*\*/g, '');
                              const isRealCaseName = /\bv\b|vs\.|\[\d{4}\]|\(\d{4}\)/i.test(cleanedName);
                              const caseName = isRealCaseName ? cleanedName : (caseDesc ? '' : cleanedName);
                              if (!caseDesc && !rawName) return null;
                              const displayText = caseName ? `${caseName}: ${caseDesc}` : (caseDesc || content);
                              return (
                                <div key={i} className="flex gap-2 items-start">
                                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0 mt-1.5" />
                                  <p className="text-xs text-slate-300 leading-relaxed">
                                    {caseName && <span className="text-amber-300 font-semibold">{caseName}: </span>}
                                    {caseName ? caseDesc : displayText}
                                  </p>
                                </div>
                              );
                            }).filter(Boolean)}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Graph Context nodes */}
              {result.graph_context?.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center">
                      <Network size={12} className="text-blue-400" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-widest text-blue-400">Graph Context</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-semibold">{result.graph_context.length} nodes</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {result.graph_context.slice(0, 6).map((n, i) => (
                      <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-3">
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-400 font-bold uppercase">{n.type || 'Node'}</span>
                          <span className="text-xs text-slate-300 font-medium truncate">{n.label || n.id}</span>
                        </div>
                        {n.properties?.text && (
                          <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{n.properties.text}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cases used */}
              {result.cases_used?.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
                      <BookOpen size={12} className="text-amber-400" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-widest text-amber-400">Case Law Used</span>
                  </div>
                  <div className="space-y-2">
                    {result.cases_used.slice(0, 3).map((c, i) => {
                      const cText = c.text || '';
                      const colonIdx = cText.indexOf(':');
                      const rawTitle = colonIdx > 0 ? cText.slice(0, colonIdx).trim() : '';
                      // Only use as title if it looks like a real case name (has v / [year] / year)
                      const isRealTitle = rawTitle && /\bv\b|vs\.|\[\d{4}\]|\(\d{4}\)|\d{4}/.test(rawTitle);
                      const title = isRealTitle ? rawTitle : (c.case_id || `Case ${i+1}`);
                      const desc = isRealTitle ? cText.slice(colonIdx + 1).trim() : cText;
                      return (
                        <div key={i} className="bg-slate-800/50 border border-amber-500/20 rounded-xl p-3 flex gap-3">
                          <div className="w-6 h-6 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
                            <span className="text-[9px] font-bold text-amber-400">{i+1}</span>
                          </div>
                          <div>
                            <p className="text-xs font-semibold text-amber-300 mb-0.5">{title}</p>
                            <p className="text-[11px] text-slate-400 leading-relaxed">{desc.slice(0, 180)}{desc.length > 180 ? '...' : ''}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// PRECEDENTS TAB
// ─────────────────────────────────────────────────────────

const PrecedentsTab = ({ data }) => {
  const [clauseText, setClauseText] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedClause, setSelectedClause] = useState('');

  const clauses = data?.clauses || [];

  const handleClauseSelect = (e) => {
    const idx = e.target.value;
    setSelectedClause(idx);
    if (idx !== '') {
      setClauseText(clauses[parseInt(idx)]?.text || '');
      setResults(null);
    }
  };

  const search = async () => {
    if (!clauseText.trim()) return;
    setLoading(true);
    setResults(null);
    try {
      const res = await findPrecedents(clauseText, jurisdiction, 5);
      setResults(res);
    } catch {
      setResults({ error: 'Precedent search failed.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-3 flex items-start gap-2">
        <BookMarked size={14} className="text-amber-400 shrink-0 mt-0.5" />
        <p className="text-slate-400 text-xs">
          Westlaw-style precedent finder. Pick a clause from your contract or paste custom text — we retrieve the most similar court judgements with win probability estimates from our 100-case legal corpus.
        </p>
      </div>

      {clauses.length > 0 && (
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-400 font-medium px-1">Pick a clause from your contract</label>
          <select
            value={selectedClause}
            onChange={handleClauseSelect}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500"
          >
            <option value="">— Select a clause —</option>
            {clauses.map((cl, i) => (
              <option key={i} value={i}>
                {cl.clause_name || cl.clause_type || `Clause ${i + 1}`}
                {cl.risk_level ? ` · ${cl.risk_level}` : ''}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="flex flex-col gap-1">
        <label className="text-xs text-slate-400 font-medium px-1">Or paste custom clause text</label>
        <textarea
          value={clauseText}
          onChange={e => { setClauseText(e.target.value); setSelectedClause(''); }}
          placeholder="Paste clause text here to find similar legal precedents…"
          rows={4}
          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 outline-none focus:border-amber-500 resize-none"
        />
      </div>

      <div className="flex gap-2">
        <select
          value={jurisdiction}
          onChange={e => setJurisdiction(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500"
        >
          <option value="">All Jurisdictions</option>
          <option value="IN">India</option>
          <option value="US">United States</option>
          <option value="UK">United Kingdom</option>
          <option value="SG">Singapore</option>
        </select>
        <button
          onClick={search}
          disabled={loading || !clauseText.trim()}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium disabled:opacity-50"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <BookMarked size={14} />} Find Precedents
        </button>
      </div>

      {results && (
        <div className="space-y-3">
          {results.error ? (
            <p className="text-red-400 text-sm">{results.error}</p>
          ) : (() => {
            // Backend returns: { similar_cases, win_probability, risk_assessment, jurisdiction, retrieval_method }
            const cases = results.similar_cases || results.precedents || [];
            const winProb = results.win_probability;
            const riskLevel = results.risk_assessment?.risk_level || '';
            const method = results.retrieval_method || '';
            return (
              <>
                {/* Stats bar */}
                <div className="flex items-center gap-3 flex-wrap">
                  {winProb !== undefined && (
                    <div className="flex items-center gap-2 bg-slate-800/60 border border-slate-700/50 rounded-xl px-4 py-2.5">
                      <span className="text-slate-400 text-xs">Win Probability</span>
                      <span className={`text-sm font-bold ${winProb > 0.6 ? 'text-green-400' : winProb > 0.4 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {(winProb * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                  {riskLevel && (
                    <div className={`flex items-center gap-2 rounded-xl px-4 py-2.5 border text-xs font-bold
                      ${riskLevel === 'HIGH' ? 'bg-red-500/10 border-red-500/30 text-red-400'
                        : riskLevel === 'LOW' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'bg-amber-500/10 border-amber-500/30 text-amber-400'}`}>
                      <AlertTriangle size={11} /> {riskLevel} RISK
                    </div>
                  )}
                  {method && (
                    <span className="text-[10px] px-2 py-1 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30 font-semibold">
                      {method}
                    </span>
                  )}
                  <span className="text-xs text-slate-500">{cases.length} precedents found</span>
                </div>

                {/* Precedent cards */}
                {cases.length > 0 && (
                  <div className="space-y-2">
                    {cases.map((p, i) => {
                      const cText = p.text || '';
                      const colonIdx = cText.indexOf(':');
                      const isRealTitle = colonIdx > 0 && /\bv\b|vs\.|\[\d{4}\]|\(\d{4}\)|\d{4}/.test(cText.slice(0, colonIdx));
                      const caseName = isRealTitle ? cText.slice(0, colonIdx).trim() : (p.case_name || p.name || p.case_id || `Case ${i+1}`);
                      const holding = isRealTitle ? cText.slice(colonIdx + 1).trim() : (p.holding || p.summary || cText);
                      const score = p.score ?? p.similarity ?? p.fusion_score;
                      const outcome = p.outcome;
                      return (
                        <div key={i} className="bg-slate-800/60 rounded-xl border border-amber-500/20 p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <div className="w-5 h-5 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
                                  <span className="text-[9px] font-bold text-amber-400">{i+1}</span>
                                </div>
                                <p className="text-amber-300 text-sm font-semibold">{caseName}</p>
                              </div>
                              {(p.court || p.year || p.jurisdiction) && (
                                <p className="text-slate-500 text-xs mb-1.5 ml-7">
                                  {[p.court, p.year, p.jurisdiction].filter(Boolean).join(' · ')}
                                </p>
                              )}
                              <p className="text-slate-300 text-xs leading-relaxed ml-7">{holding.slice(0, 220)}{holding.length > 220 ? '...' : ''}</p>
                            </div>
                            <div className="text-right shrink-0 space-y-1">
                              {score !== undefined && (
                                <div>
                                  <p className="text-slate-500 text-[10px]">Similarity</p>
                                  <p className="text-amber-400 font-bold text-sm">{(score * 100).toFixed(0)}%</p>
                                </div>
                              )}
                              {outcome && (
                                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold block
                                  ${outcome === 'WIN' ? 'bg-green-500/20 text-green-400'
                                    : outcome === 'LOSS' ? 'bg-red-500/20 text-red-400'
                                    : 'bg-slate-500/20 text-slate-400'}`}>
                                  {outcome}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// AUTO-REDLINE TAB
// ─────────────────────────────────────────────────────────

const AutoRedlineTab = ({ contractId }) => {
  const [loading, setLoading] = useState(false);
  const [redlines, setRedlines] = useState(null);
  const [accepted, setAccepted] = useState({});
  const [rejected, setRejected] = useState({});
  const [copied, setCopied] = useState({});
  const [expanded, setExpanded] = useState({});

  const run = async () => {
    setLoading(true);
    setRedlines(null);
    setAccepted({});
    setRejected({});
    try {
      const res = await autoRedline(contractId);
      setRedlines(res.redlines || []);
    } catch (e) {
      setRedlines([]);
    } finally {
      setLoading(false);
    }
  };

  const copyText = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopied(prev => ({ ...prev, [id]: true }));
    setTimeout(() => setCopied(prev => ({ ...prev, [id]: false })), 2000);
  };

  const RISK_COLOR = { CRITICAL: 'text-red-400 bg-red-500/20 border-red-500/40', HIGH: 'text-red-400 bg-red-500/20 border-red-500/40', MEDIUM: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/40' };
  const METHOD_COLOR = { llm: 'text-violet-400 bg-violet-500/15 border-violet-500/30', fallback: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30', template: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30' };

  // Highlight diff words
  const diffHighlight = (original, rewritten) => {
    const origWords = new Set(original.toLowerCase().split(/\s+/));
    return rewritten.split(/\s+/).map((word, i) => {
      const clean = word.toLowerCase().replace(/[^a-z0-9]/g, '');
      const isNew = clean.length > 3 && !origWords.has(clean);
      return <span key={i} className={isNew ? 'bg-green-500/25 text-green-300 rounded px-0.5' : 'text-slate-200'}>{word} </span>;
    });
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/60 border border-slate-700/50 rounded-2xl p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <GitCompare size={18} className="text-violet-400" />
              <p className="text-white font-bold text-sm">AI Clause Auto-Redlining</p>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30 font-bold">BETA</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed max-w-2xl">
              Automatically detects high-risk clauses and generates safer rewritten alternatives.
              Review each suggestion, accept what works, reject what doesn't, and copy the new language directly.
            </p>
          </div>
          <button
            onClick={run}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm font-semibold transition-all shadow-lg shadow-violet-900/30 shrink-0"
          >
            {loading ? <Loader2 size={15} className="animate-spin" /> : <Edit2 size={15} />}
            {loading ? 'Analyzing…' : redlines ? 'Re-run' : 'Run Auto-Redline'}
          </button>
        </div>

        {/* Info banner */}
        <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-green-500/25 border border-green-500/30 inline-block" /> New / changed words highlighted green</span>
          <span className="flex items-center gap-1.5"><ThumbsUp size={11} className="text-green-400" /> Accept to mark clause as reviewed</span>
          <span className="flex items-center gap-1.5"><Copy size={11} className="text-blue-400" /> Copy rewritten text to clipboard</span>
          <span className="flex items-center gap-1.5"><span className="text-emerald-400 font-bold">TEMPLATE</span> = Professionally drafted standard clause</span>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-full border-4 border-violet-500/20 border-t-violet-500 animate-spin" />
            <GitCompare size={20} className="text-violet-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          </div>
          <p className="text-slate-300 text-sm font-medium">Analyzing clauses and generating rewrites…</p>
          <p className="text-slate-500 text-xs">This runs all rewrites in parallel — typically 20–35 seconds</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && redlines && redlines.length === 0 && (
        <div className="text-center py-16">
          <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
          <p className="text-slate-300 font-semibold">No high-risk clauses found</p>
          <p className="text-slate-500 text-sm mt-1">All clauses appear to be low risk or haven't been analyzed yet. Run the full legal review first.</p>
        </div>
      )}

      {/* Prompt to run */}
      {!loading && !redlines && (
        <div className="text-center py-16 bg-slate-800/30 border border-slate-700/40 rounded-2xl">
          <GitCompare size={48} className="text-violet-400/50 mx-auto mb-4" />
          <p className="text-slate-300 font-semibold text-lg">Ready to Redline</p>
          <p className="text-slate-500 text-sm mt-2 max-w-md mx-auto">Click "Run Auto-Redline" to scan all high and medium risk clauses in this contract and generate AI-suggested safer alternatives.</p>
        </div>
      )}

      {/* Stats bar */}
      {!loading && redlines && redlines.length > 0 && (
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Total Redlines', value: redlines.length, color: 'text-white' },
            { label: 'Accepted', value: Object.values(accepted).filter(Boolean).length, color: 'text-green-400' },
            { label: 'Rejected', value: Object.values(rejected).filter(Boolean).length, color: 'text-red-400' },
            { label: 'AI Rewrites', value: redlines.filter(r => r.method === 'llm').length, color: 'text-violet-400' },
          ].map(s => (
            <div key={s.label} className="bg-slate-800/60 border border-slate-700/40 rounded-xl p-3 text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-slate-500 text-xs mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Redline cards */}
      {!loading && redlines && redlines.map((r, idx) => {
        const isAccepted = accepted[r.clause_id];
        const isRejected = rejected[r.clause_id];
        const isExpanded = expanded[r.clause_id] !== false; // default expanded

        return (
          <div key={r.clause_id}
            className={`border rounded-2xl overflow-hidden transition-all ${
              isAccepted ? 'border-green-500/40 bg-green-500/5'
              : isRejected ? 'border-red-500/30 bg-slate-900/40 opacity-60'
              : 'border-slate-700/50 bg-slate-800/40'
            }`}
          >
            {/* Card header */}
            <div
              className="flex items-center justify-between gap-3 p-4 cursor-pointer"
              onClick={() => setExpanded(prev => ({ ...prev, [r.clause_id]: !isExpanded }))}
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-slate-500 text-xs font-mono shrink-0">#{idx + 1}</span>
                <div className="min-w-0">
                  <p className="text-white text-sm font-semibold truncate">{r.clause_type}</p>
                  {r.risk_reason && <p className="text-slate-500 text-xs truncate">{r.risk_reason}</p>}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${RISK_COLOR[r.risk_level] || RISK_COLOR.MEDIUM}`}>{r.risk_level}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${METHOD_COLOR[r.method] || METHOD_COLOR.fallback}`}>{r.method === 'llm' ? 'AI' : 'TEMPLATE'}</span>
                <span className="text-slate-400 text-xs">{Math.round((r.confidence || 0.7) * 100)}%</span>
                {isAccepted && <CheckCircle size={16} className="text-green-400" />}
                {isRejected && <XCircle size={16} className="text-red-400" />}
                {isExpanded ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
              </div>
            </div>

            {/* Diff body */}
            {isExpanded && (
              <div className="px-4 pb-4 space-y-3">
                {/* Original */}
                <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-red-400 text-[10px] font-bold uppercase tracking-wider">Original (Risky)</span>
                  </div>
                  <p className="text-slate-300 text-xs leading-relaxed font-mono">{r.original}</p>
                </div>

                {/* Rewritten */}
                <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-3">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-green-400 text-[10px] font-bold uppercase tracking-wider">AI Rewrite (Safer)</span>
                    <button
                      onClick={() => copyText(r.clause_id, r.rewritten)}
                      className="flex items-center gap-1 text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      <Copy size={10} />
                      {copied[r.clause_id] ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <p className="text-xs leading-relaxed font-mono">{diffHighlight(r.original, r.rewritten)}</p>
                </div>

                {/* Action buttons */}
                {!isAccepted && !isRejected && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAccepted(prev => ({ ...prev, [r.clause_id]: true }))}
                      className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 text-green-400 text-sm font-medium transition-all"
                    >
                      <ThumbsUp size={14} /> Accept Rewrite
                    </button>
                    <button
                      onClick={() => setRejected(prev => ({ ...prev, [r.clause_id]: true }))}
                      className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl bg-red-600/10 hover:bg-red-600/20 border border-red-500/20 text-red-400 text-sm font-medium transition-all"
                    >
                      <ThumbsDown size={14} /> Reject
                    </button>
                  </div>
                )}
                {isAccepted && (
                  <div className="flex items-center gap-2 text-green-400 text-sm py-1">
                    <CheckCircle size={14} /> Accepted — Use the rewritten clause above in your contract
                  </div>
                )}
                {isRejected && (
                  <button
                    onClick={() => setRejected(prev => ({ ...prev, [r.clause_id]: false }))}
                    className="text-xs text-slate-500 hover:text-slate-300 underline"
                  >
                    Undo rejection
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// SUMMARY TAB
// ─────────────────────────────────────────────────────────

const SummaryTab = ({ data }) => {
  if (!data) return null;
  const clauses = data.clauses || [];
  const high   = clauses.filter(c => (c.risk?.risk_level || '').toUpperCase() === 'HIGH').length;
  const medium = clauses.filter(c => (c.risk?.risk_level || '').toUpperCase() === 'MEDIUM').length;
  const low    = clauses.length - high - medium;
  const avgScore = clauses.length
    ? (clauses.reduce((a, c) => a + (c.risk?.risk_score || 0), 0) / clauses.length)
    : 0;
  const maxScore = clauses.length
    ? Math.max(...clauses.map(c => c.risk?.risk_score || 0))
    : 0;
  const totalCases = clauses.reduce((a, c) => a + (c.cases?.length || 0), 0);

  // Verdict
  const verdict = high > 2 ? { label: 'HIGH RISK', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/40', icon: XCircle }
    : high > 0 || medium > 3 ? { label: 'MEDIUM RISK', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/40', icon: AlertTriangle }
    : { label: 'LOW RISK', color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/40', icon: CheckCircle };

  const pieData = [
    { name: 'HIGH',   value: high,   fill: '#F16667' },
    { name: 'MEDIUM', value: medium, fill: '#FFD86E' },
    { name: 'LOW',    value: low,    fill: '#68BC00' },
  ].filter(d => d.value > 0);

  const barData = clauses.map((c, i) => ({
    name: c.type ? c.type.replace(/_/g, ' ').slice(0, 14) : `C${i + 1}`,
    score: parseFloat((c.risk?.risk_score || 0).toFixed(2)),
    fill: RISK_COLORS[(c.risk?.risk_level || 'LOW').toUpperCase()] || '#68BC00',
  }));

  // Top risky clauses (sorted)
  const topRisky = [...clauses]
    .sort((a, b) => (b.risk?.risk_score || 0) - (a.risk?.risk_score || 0))
    .slice(0, 5);

  // Jurisdiction breakdown
  const jurMap = {};
  clauses.forEach(c => {
    (c.cases || []).forEach(cas => {
      const j = cas.jurisdiction || 'Unknown';
      jurMap[j] = (jurMap[j] || 0) + 1;
    });
  });
  const jurData = Object.entries(jurMap).map(([name, count]) => ({ name, count })).sort((a,b) => b.count - a.count);

  return (
    <div className="space-y-4">

      {/* Verdict Banner */}
      <div className={`rounded-xl border p-4 flex items-center gap-4 ${verdict.bg}`}>
        <verdict.icon size={32} className={verdict.color} />
        <div className="flex-1">
          <p className={`text-lg font-bold ${verdict.color}`}>Overall Contract Verdict: {verdict.label}</p>
          <p className="text-slate-400 text-sm mt-0.5">
            {high} high-risk · {medium} medium-risk · {low} low-risk clause{clauses.length !== 1 ? 's' : ''} · {totalCases} supporting cases retrieved
          </p>
        </div>
        <div className="text-right hidden md:block">
          <p className="text-slate-400 text-xs">Max Risk Score</p>
          <p className={`text-2xl font-bold ${verdict.color}`}>{maxScore.toFixed(2)}</p>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Clauses',  value: clauses.length,       color: 'text-blue-400',   sub: 'parsed' },
          { label: 'High Risk',      value: high,                  color: 'text-red-400',    sub: 'clauses' },
          { label: 'Medium Risk',    value: medium,                color: 'text-yellow-400', sub: 'clauses' },
          { label: 'Low Risk',       value: low,                   color: 'text-green-400',  sub: 'clauses' },
          { label: 'Avg Risk Score', value: avgScore.toFixed(2),   color: 'text-violet-400', sub: 'Bayesian' },
          { label: 'Cases Cited',    value: totalCases,            color: 'text-cyan-400',   sub: 'retrieved' },
        ].map(kpi => (
          <div key={kpi.label} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-3 text-center">
            <p className="text-slate-500 text-[10px] uppercase tracking-wide">{kpi.label}</p>
            <p className={`text-2xl font-bold mt-1 ${kpi.color}`}>{kpi.value}</p>
            <p className="text-slate-600 text-[10px] mt-0.5">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Pie */}
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
          <p className="text-slate-300 text-sm font-semibold mb-3">Risk Distribution</p>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData} dataKey="value" nameKey="name"
                cx="50%" cy="50%" outerRadius={75} innerRadius={35}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine
              >
                {pieData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', fontSize: '11px' }} />
              <Legend iconType="circle" />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar */}
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
          <p className="text-slate-300 text-sm font-semibold mb-3">Clause Risk Scores</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData} margin={{ top: 5, right: 10, bottom: 40, left: 0 }}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 8 }} angle={-40} textAnchor="end" interval={0} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', fontSize: '11px' }} />
              <Bar dataKey="score" barSize={18} radius={[3,3,0,0]}>
                {barData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Top Risky Clauses */}
        <div className="lg:col-span-2 bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
          <p className="text-slate-300 text-sm font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle size={14} className="text-red-400" /> Top Risky Clauses
          </p>
          <div className="space-y-2">
            {topRisky.map((c, i) => {
              const lvl = (c.risk?.risk_level || 'LOW').toUpperCase();
              const score = c.risk?.risk_score || 0;
              const pct = maxScore > 0 ? (score / maxScore) * 100 : 0;
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-slate-500 text-xs w-4 shrink-0">#{i+1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-slate-200 text-xs truncate">{c.type || `Clause ${i+1}`}</span>
                      <RiskBadge level={lvl} />
                    </div>
                    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${pct}%`, background: RISK_COLORS[lvl] || '#68BC00' }}
                      />
                    </div>
                  </div>
                  <span className="text-slate-300 text-xs font-mono shrink-0">{score.toFixed(2)}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right column: jurisdiction + contract meta */}
        <div className="space-y-4">
          {/* Jurisdiction breakdown */}
          {jurData.length > 0 && (
            <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
              <p className="text-slate-300 text-sm font-semibold mb-3 flex items-center gap-2">
                <Globe size={13} className="text-amber-400" /> Case Law by Jurisdiction
              </p>
              <div className="space-y-2">
                {jurData.slice(0, 5).map((j, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-slate-300 text-xs w-6 shrink-0 font-mono">{j.name}</span>
                    <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${(j.count / (jurData[0]?.count || 1)) * 100}%` }}
                      />
                    </div>
                    <span className="text-slate-400 text-xs">{j.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Contract metadata */}
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
            <p className="text-slate-300 text-sm font-semibold mb-3 flex items-center gap-2">
              <FileText size={13} className="text-slate-400" /> Contract Details
            </p>
            <div className="space-y-2">
              {[
                ['Title',        data.contract?.title],
                ['Counterparty', data.contract?.counterparty],
                ['Jurisdiction', data.contract?.jurisdiction],
                ['Status',       data.contract?.status],
                ['Analyzed',     new Date().toLocaleDateString()],
              ].filter(([, v]) => v).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2">
                  <span className="text-slate-500 text-xs shrink-0">{k}</span>
                  <span className="text-slate-200 text-xs text-right truncate">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// HOW IT WORKS TAB
// ─────────────────────────────────────────────────────────

const HowItWorksTab = () => {
  const sections = [
    { icon: Brain, title: 'Legal-BERT Case Retrieval', color: 'text-violet-400', desc: 'CaseLaw-BERT (nlpaueb/legal-bert-base-uncased) encodes clauses into 768-dim embeddings. FAISS IndexFlatL2 performs sub-millisecond similarity search over 100 curated Indian & US legal cases. Falls back to BM25 keyword scoring when BERT is unavailable.' },
    { icon: Shield, title: 'Bayesian Noisy-OR Risk Engine', color: 'text-red-400', desc: 'Full multi-node Bayesian network: EventType → ClauseStrength → Jurisdiction → Counterparty → LegalRisk → Litigation → FinancialRisk. CPT tables encode expert priors. Online CPT Learner updates from litigation outcomes via frequency-based estimation.' },
    { icon: Network, title: 'RAG & GraphRAG Pipelines', color: 'text-blue-400', desc: 'RAG: BM25 retrieval → PromptBuilder → Qwen 2.5 generation. GraphRAG: EntityExtractor → Graph traversal (parties, dates, obligations) → Context-aware prompting. Both pipelines provide grounded, citation-backed answers.' },
    { icon: MessageSquare, title: 'Legal Co-Pilot (3 Agents)', color: 'text-green-400', desc: 'Three specialized Qwen 2.5 agents run in parallel: Risk Agent (Bayesian exposure analysis), Negotiation Agent (counter-proposal strategy), Litigation Agent (win probability & case law). Responses are merged into a unified answer.' },
    { icon: Globe, title: 'Live Legal Events Crawler', color: 'text-amber-400', desc: '60 legal sources (30 India + 30 US) including Supreme Court, High Courts, SEBI, MCA, SCOTUS, SEC, FTC, CFPB. Events are classified by severity (CRITICAL/HIGH/MEDIUM/LOW) and jurisdiction. Polling every 15 seconds in the Live Feed tab.' },
    { icon: BookMarked, title: 'Westlaw-Style Precedent Finder', color: 'text-amber-400', desc: 'Paste any clause text to retrieve the top-5 most similar court judgements with cosine similarity scores, outcome labels (WIN/LOSS/SETTLED), and an estimated win probability derived from the precedent outcomes.' },
    { icon: Cpu, title: 'Neo4j Knowledge Graph', color: 'text-cyan-400', desc: 'Contract, Clause, CaseLaw, Court, and LegalEvent nodes stored in Neo4j. Relationships: HAS_CLAUSE, SUPPORTED_BY, CITED_IN, DECIDED_BY, SIMILAR_TO (cross-case similarity edges). GraphRAG traverses this graph for multi-hop reasoning.' },
  ];

  return (
    <div className="space-y-3">
      {sections.map((s, i) => (
        <div key={i} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 flex gap-3">
          <s.icon size={20} className={`${s.color} shrink-0 mt-0.5`} />
          <div>
            <p className={`text-sm font-semibold ${s.color}`}>{s.title}</p>
            <p className="text-slate-400 text-xs leading-relaxed mt-1">{s.desc}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────

export default function LegalReview() {
  const { contractId } = useParams();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('summary');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [caseLawSearch, setCaseLawSearch] = useState('');
  const [caseLaw, setCaseLaw] = useState([]);
  const [caseLawLoading, setCaseLawLoading] = useState(false);
  const [allCaseLaw, setAllCaseLaw] = useState([]);
  const [caseModal, setCaseModal] = useState(null); // { case: {...}, analysis: '', loading: true }

  const analyze = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runLegalReview(contractId);
      setData(res);
    } catch (e) {
      setError(e?.response?.data?.error || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [contractId]);

  useEffect(() => { analyze(); }, [analyze]);

  // Extract keywords from the analyzed contract to filter relevant cases
  const getContractKeywords = () => {
    if (!data) return [];
    const keywords = new Set();
    // From clause types
    (data.clauses || []).forEach(cl => {
      if (cl.clause_type) {
        cl.clause_type.toLowerCase().split(/[\s_/]+/).forEach(w => w.length > 3 && keywords.add(w));
      }
      // From risk reasons
      if (cl.risk_reason) {
        cl.risk_reason.toLowerCase().split(/\s+/).forEach(w => w.length > 4 && keywords.add(w));
      }
      // From risk category
      if (cl.risk_category) keywords.add(cl.risk_category.toLowerCase());
    });
    // From contract-level risk factors
    (data.risk_factors || []).forEach(rf => {
      if (typeof rf === 'string') rf.toLowerCase().split(/\s+/).forEach(w => w.length > 4 && keywords.add(w));
    });
    return [...keywords];
  };

  const scoreCase = (c, keywords) => {
    const text = (c.text + ' ' + (c.tags || []).join(' ')).toLowerCase();
    return keywords.filter(k => text.includes(k)).length;
  };

  const fetchCaseLaw = async (searchOverride) => {
    setCaseLawLoading(true);
    try {
      const search = searchOverride !== undefined ? searchOverride : caseLawSearch;
      const res = await getCaseLaw(search);
      const cases = res.cases || [];
      setAllCaseLaw(cases);
      if (!search) {
        // Sort by relevance to this contract
        const keywords = getContractKeywords();
        const scored = cases
          .map(c => ({ ...c, _score: scoreCase(c, keywords) }))
          .sort((a, b) => b._score - a._score);
        setCaseLaw(scored);
      } else {
        setCaseLaw(cases);
      }
    } finally {
      setCaseLawLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'caselaw') fetchCaseLaw('');
  }, [activeTab, data]);

  const openCaseAnalysis = (caseItem) => {
    // Build analysis from existing contract data — no Ollama needed, instant
    const caseTags = caseItem.tags || [];
    const caseText = caseItem.text || '';

    // Find matching clauses from already-analyzed data
    const matchingClauses = (data?.clauses || []).filter(cl => {
      const clText = ((cl.clause_type || '') + ' ' + (cl.risk_reason || '') + ' ' + (cl.text || '')).toLowerCase();
      return caseTags.some(t => clText.includes(t.toLowerCase()));
    });

    // Build structured analysis
    const lines = [];

    // 1. What the case establishes
    lines.push(`**What this case establishes:**\n${caseText.includes(':') ? caseText.split(':').slice(1).join(':').trim() : caseText}`);

    // 2. Matching clauses
    if (matchingClauses.length > 0) {
      lines.push(`\n**Clauses in your contract affected by this precedent:**`);
      matchingClauses.slice(0, 4).forEach(cl => {
        const riskLabel = cl.risk_level ? ` [${cl.risk_level} risk]` : '';
        lines.push(`• ${cl.clause_type || 'Clause'}${riskLabel}: ${cl.risk_reason || 'Review against this precedent.'}`);
      });
    } else {
      lines.push(`\n**Clause match:** No direct clause match found, but this precedent may apply to general contractual obligations in this contract.`);
    }

    // 3. Risk implication
    const topTag = caseTags[0] || 'contract terms';
    lines.push(`\n**Risk implication:**\nBased on this precedent, any ${topTag} provisions in your contract should be reviewed to ensure they are clearly defined and enforceable. Courts in ${caseItem.jurisdiction} have applied this principle strictly.`);

    // 4. Recommended action
    const highRiskClauses = matchingClauses.filter(cl => ['HIGH', 'CRITICAL'].includes((cl.risk_level || '').toUpperCase()));
    if (highRiskClauses.length > 0) {
      lines.push(`\n**Recommended action:**\n${highRiskClauses.length} high/critical risk clause(s) in your contract directly overlap with this precedent. Consider legal counsel review of: ${highRiskClauses.map(cl => cl.clause_type).join(', ')}.`);
    } else {
      lines.push(`\n**Recommended action:**\nEnsure ${topTag} clauses are explicitly drafted, with clear scope, duration, and jurisdiction applicability. This precedent suggests ambiguous wording may be construed against the drafter.`);
    }

    setCaseModal({ case: caseItem, analysis: lines.join('\n'), loading: false });
  };

  // ── LOADING ──
  if (loading) {
    return (
      <div className="px-4 lg:px-8 py-6 flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 size={40} className="animate-spin text-violet-400" />
        <p className="text-slate-400 text-sm">Running Legal Review Pipeline…</p>
        <p className="text-slate-600 text-xs">Parsing clauses · Retrieving case law · Computing Bayesian risk</p>
      </div>
    );
  }

  // ── ERROR ──
  if (error) {
    return (
      <div className="px-4 lg:px-8 py-6 flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <XCircle size={40} className="text-red-400" />
        <p className="text-red-400 text-sm">{error}</p>
        <button onClick={analyze} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm">
          <RefreshCw size={14} /> Retry
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 lg:px-8 py-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <Scale size={20} className="text-violet-400" />
              <h1 className="text-xl font-bold text-white">Adv. Legal Review</h1>
              <span className="bg-violet-500/20 text-violet-300 text-xs px-2 py-0.5 rounded-full border border-violet-500/30 font-medium">AI-Powered</span>
            </div>
            <p className="text-slate-400 text-xs mt-0.5">Contract ID: {contractId?.slice(0, 8)}…</p>
          </div>
        </div>
        <button
          onClick={analyze}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm"
        >
          <RefreshCw size={14} /> Re-analyze
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-slate-700/50">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'bg-violet-600/80 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <tab.icon size={13} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'summary' && <EnhancedSummaryTab data={data} />}

        {activeTab === 'clauses' && (
          <div className="space-y-8">
            {data?.clauses?.length > 0 ? (
              data.clauses.map((cl, i) => <EnhancedClauseReview key={i} clause={cl} index={i} />)
            ) : (
              <p className="text-slate-500 text-center py-8">No clauses found. Try re-analyzing.</p>
            )}
          </div>
        )}

        {activeTab === 'graph' && <KnowledgeGraph data={data} contractId={contractId} />}

        {activeTab === 'caselaw' && (
          <div className="space-y-4">
            {/* Search bar */}
            <div className="flex gap-2">
              <div className="flex items-center gap-2 flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 focus-within:border-violet-500/60 transition-colors">
                <Search size={14} className="text-slate-400" />
                <input
                  value={caseLawSearch}
                  onChange={e => setCaseLawSearch(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && fetchCaseLaw()}
                  placeholder="Search case law by keyword, clause type, tag…"
                  className="flex-1 bg-transparent text-slate-200 text-sm outline-none placeholder-slate-500"
                />
                {caseLawSearch && (
                  <button onClick={() => { setCaseLawSearch(''); fetchCaseLaw(''); }} className="text-slate-500 hover:text-slate-300 text-xs">✕ Clear</button>
                )}
              </div>
              <button
                onClick={() => fetchCaseLaw()}
                disabled={caseLawLoading}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-sm disabled:opacity-50"
              >
                {caseLawLoading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />} Search
              </button>
            </div>

            {caseLawLoading ? (
              <div className="flex items-center justify-center py-16 gap-3">
                <Loader2 size={24} className="animate-spin text-violet-400" />
                <p className="text-slate-400 text-sm">Finding relevant precedents…</p>
              </div>
            ) : (
              <>
                {/* Contract-relevant cases */}
                {!caseLawSearch && (() => {
                  const contractKeywords = getContractKeywords();
                  const relevant = caseLaw.filter(c => c._score > 0);
                  const irrelevant = caseLaw.filter(c => !c._score);
                  return (
                    <>
                      {/* Info banner */}
                      <div className="flex items-start gap-3 bg-gradient-to-r from-violet-900/30 to-blue-900/20 border border-violet-500/30 rounded-xl px-4 py-3">
                        <Sparkles size={14} className="text-violet-400 mt-0.5 shrink-0" />
                        <div>
                          <p className="text-slate-200 text-xs font-semibold mb-0.5">Ranked by relevance to this contract</p>
                          <p className="text-slate-400 text-xs">
                            Matched against {contractKeywords.length} keywords extracted from your contract's clause types and risk factors.
                            {' '}<span className="text-violet-300 font-semibold">{relevant.length} relevant</span> · {irrelevant.length} other cases in corpus.
                          </p>
                          {contractKeywords.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {contractKeywords.slice(0, 12).map((k, i) => (
                                <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/20">{k}</span>
                              ))}
                              {contractKeywords.length > 12 && <span className="text-[10px] text-slate-500">+{contractKeywords.length - 12} more</span>}
                            </div>
                          )}
                        </div>
                      </div>

                      {relevant.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-3">
                            <Gavel size={14} className="text-violet-400" />
                            <p className="text-slate-200 text-sm font-semibold">Relevant to Your Contract</p>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30">{relevant.length} cases</span>
                          </div>
                          <CaseList cases={relevant} showScore contractKeywords={contractKeywords} onViewAnalysis={openCaseAnalysis} />
                        </div>
                      )}

                      {irrelevant.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-3 mt-2">
                            <BookOpen size={14} className="text-slate-500" />
                            <p className="text-slate-500 text-sm font-semibold">Other Cases in Corpus</p>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700/50 text-slate-500 border border-slate-700">{irrelevant.length} cases</span>
                          </div>
                          <CaseList cases={irrelevant} onViewAnalysis={openCaseAnalysis} />
                        </div>
                      )}
                    </>
                  );
                })()}

                {/* Search results */}
                {caseLawSearch && (
                  <>
                    <p className="text-slate-500 text-xs">{caseLaw.length} result{caseLaw.length !== 1 ? 's' : ''} for "{caseLawSearch}"</p>
                    {caseLaw.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-16 gap-3">
                        <BookOpen size={32} className="text-slate-600" />
                        <p className="text-slate-500 text-sm">No cases found for "{caseLawSearch}"</p>
                        <button onClick={() => { setCaseLawSearch(''); fetchCaseLaw(''); }} className="text-violet-400 text-xs hover:text-violet-300">Show all cases</button>
                      </div>
                    ) : (
                      <CaseList cases={caseLaw} onViewAnalysis={openCaseAnalysis} />
                    )}
                  </>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'livefeed' && <LiveFeedTab contractId={contractId} />}
        {activeTab === 'copilot' && <CopilotTab contractId={contractId} />}
        {activeTab === 'rag' && <RAGSearchTab contractId={contractId} />}
        {activeTab === 'graphrag' && <GraphRAGTab contractId={contractId} />}
        {activeTab === 'precedents' && <PrecedentsTab data={data} />}
        {activeTab === 'redline' && <AutoRedlineTab contractId={contractId} />}
        {activeTab === 'howit' && <HowItWorksTab />}
      </div>

      {/* Case Analysis Modal */}
      {caseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setCaseModal(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl shadow-violet-900/20"
            onClick={e => e.stopPropagation()}>

            {/* Modal header */}
            <div className="flex items-start justify-between gap-3 p-5 border-b border-slate-700/50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-violet-600/20 border border-violet-500/40 flex items-center justify-center shrink-0">
                  <Gavel size={17} className="text-violet-400" />
                </div>
                <div>
                  <p className="text-white font-bold text-sm">Case Analysis for Your Contract</p>
                  <p className="text-slate-400 text-xs mt-0.5">{caseModal.case.case_id} · {caseModal.case.court} · {caseModal.case.year} · {caseModal.case.jurisdiction}</p>
                </div>
              </div>
              <button onClick={() => setCaseModal(null)} className="text-slate-500 hover:text-slate-300 text-lg leading-none">✕</button>
            </div>

            <div className="p-5 space-y-4">
              {/* Case text */}
              <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                <p className="text-slate-500 text-[10px] uppercase tracking-wider mb-2 font-semibold">Case Holding</p>
                <p className="text-slate-200 text-sm leading-relaxed">{caseModal.case.text}</p>
                {caseModal.case.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {caseModal.case.tags.map((t, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded-md bg-violet-500/20 text-violet-300 border border-violet-500/30">{t}</span>
                    ))}
                  </div>
                )}
              </div>

              {/* AI analysis */}
              <div className="bg-gradient-to-br from-violet-900/20 to-blue-900/10 border border-violet-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles size={14} className="text-violet-400" />
                  <p className="text-violet-300 text-xs font-semibold uppercase tracking-wider">AI Analysis — How This Applies to Your Contract</p>
                </div>
                {caseModal.loading ? (
                  <div className="flex items-center gap-3 py-6 justify-center">
                    <Loader2 size={20} className="animate-spin text-violet-400" />
                    <p className="text-slate-400 text-sm">Building analysis…</p>
                  </div>
                ) : (
                  <div className="space-y-3 text-sm leading-relaxed">
                    {caseModal.analysis.split('\n').map((line, i) => {
                      if (!line.trim()) return null;
                      if (line.startsWith('**') && line.endsWith('**')) {
                        return <p key={i} className="text-violet-300 font-semibold text-xs uppercase tracking-wider mt-2">{line.replace(/\*\*/g, '')}</p>;
                      }
                      if (line.startsWith('**') && line.includes(':**')) {
                        const [label, ...rest] = line.split(':**');
                        return <p key={i} className="text-slate-200"><span className="text-violet-300 font-semibold">{label.replace(/\*\*/g, '')}:</span> {rest.join(':**')}</p>;
                      }
                      if (line.startsWith('•')) {
                        return <p key={i} className="text-slate-300 pl-3 border-l-2 border-violet-500/40">{line.slice(1).trim()}</p>;
                      }
                      return <p key={i} className="text-slate-300">{line}</p>;
                    })}
                  </div>
                )}
              </div>
            </div>

            <div className="px-5 pb-5">
              <button onClick={() => setCaseModal(null)}
                className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm font-medium transition-colors">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
