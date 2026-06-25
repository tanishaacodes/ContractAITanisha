import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  BookOpen, Search, BarChart2, Network, Sparkles, ChevronRight,
  ChevronDown, RefreshCw, Loader, AlertTriangle, CheckCircle,
  Layers, Zap, Database, FileText, Brain, Shield, MessageSquare,
  TrendingUp, Building2, AlertCircle, ArrowRight, Copy, Check,
  GitBranch, Activity, Target, Cpu, Lock, Globe, Clock,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie, Legend, AreaChart, Area,
} from 'recharts';
import ReactFlow, {
  MiniMap, Controls, Background, BackgroundVariant,
  useNodesState, useEdgesState,
  MarkerType, Handle, Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import svc from '../services/advancedClauseLibraryService';

// ── Design tokens ─────────────────────────────────────────────────────────────
const RISK_COLOR = { HIGH: '#f43f5e', MEDIUM: '#f59e0b', LOW: '#10b981', UNKNOWN: '#6b7280' };
const RISK_BG    = { HIGH: 'rgba(244,63,94,0.12)', MEDIUM: 'rgba(245,158,11,0.12)', LOW: 'rgba(16,185,129,0.12)', UNKNOWN: 'rgba(107,114,128,0.12)' };
const BAR_PALETTE = ['#8b5cf6','#6366f1','#3b82f6','#06b6d4','#10b981','#f59e0b','#f97316','#f43f5e','#ec4899','#a855f7'];
const CAT_COLORS  = ['#8b5cf6','#6366f1','#3b82f6','#06b6d4','#10b981','#f59e0b','#f97316','#f43f5e','#ec4899','#a855f7','#14b8a6','#84cc16','#0ea5e9','#d946ef','#fb923c'];

const TABS = [
  { id: 'explorer',  label: 'Taxonomy Explorer', icon: Layers      },
  { id: 'search',    label: 'AI Search',          icon: Search      },
  { id: 'negotiate', label: 'Clause Negotiator',  icon: MessageSquare, badge: 'NEW' },
  { id: 'analytics', label: 'Analytics',           icon: BarChart2   },
  { id: 'graph',     label: 'Knowledge Graph',     icon: Network     },
  { id: 'howto',     label: 'How It Works',        icon: Sparkles    },
];

// ── Shared micro-components ────────────────────────────────────────────────────
const GlowDot = ({ color = '#8b5cf6', size = 8 }) => (
  <span style={{
    display: 'inline-block', width: size, height: size,
    borderRadius: '50%', background: color,
    boxShadow: `0 0 6px ${color}, 0 0 12px ${color}66`,
  }} />
);

const RiskBadge = ({ level }) => {
  const k = (level || 'UNKNOWN').toUpperCase();
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 20,
      background: RISK_BG[k] || RISK_BG.UNKNOWN,
      color: RISK_COLOR[k] || RISK_COLOR.UNKNOWN,
      border: `1px solid ${RISK_COLOR[k] || RISK_COLOR.UNKNOWN}44`,
      letterSpacing: '0.05em',
    }}>{k}</span>
  );
};

const GlassCard = ({ children, className = '', style = {} }) => (
  <div style={{
    background: 'rgba(15,23,42,0.7)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(148,163,184,0.08)',
    borderRadius: 16,
    ...style,
  }} className={className}>
    {children}
  </div>
);

const GradientBorder = ({ children, gradient = 'linear-gradient(135deg, #8b5cf6, #6366f1)', radius = 14, padding = 1, style = {} }) => (
  <div style={{ background: gradient, borderRadius: radius + padding, padding, ...style }}>
    <div style={{ background: '#0f172a', borderRadius: radius }}>
      {children}
    </div>
  </div>
);

// ── Custom Tooltip for charts ─────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: '8px 14px' }}>
      {label && <p style={{ color: '#94a3b8', fontSize: 11, marginBottom: 4 }}>{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || '#fff', fontSize: 13, fontWeight: 600 }}>{p.value?.toLocaleString()}</p>
      ))}
    </div>
  );
};

// ── TreeNode ───────────────────────────────────────────────────────────────────
function TreeNode({ node, onSelect, selected, depth = 0 }) {
  const [open, setOpen] = useState(depth === 0);
  const hasChildren = node.children?.length > 0;
  const isSelected = selected?.id === node.id;
  const riskHue = '#8b5cf6';

  return (
    <div style={{ marginLeft: depth > 0 ? 12 : 0 }}>
      <button
        onClick={() => { setOpen(o => !o); onSelect(node); }}
        style={{
          display: 'flex', alignItems: 'center', gap: 6, width: '100%',
          padding: '6px 10px', borderRadius: 10, transition: 'all 0.18s ease',
          background: isSelected
            ? 'linear-gradient(90deg, rgba(139,92,246,0.18) 0%, rgba(99,102,241,0.08) 100%)'
            : 'transparent',
          border: isSelected ? '1px solid rgba(139,92,246,0.3)' : '1px solid transparent',
          boxShadow: isSelected ? '0 0 12px rgba(139,92,246,0.15)' : 'none',
          cursor: 'pointer',
        }}
        onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'rgba(148,163,184,0.05)'; }}
        onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
      >
        <span style={{ width: 14, flexShrink: 0, color: '#64748b' }}>
          {hasChildren ? (
            open
              ? <ChevronDown size={12} style={{ color: isSelected ? riskHue : '#64748b' }} />
              : <ChevronRight size={12} style={{ color: isSelected ? riskHue : '#64748b' }} />
          ) : <span style={{ width: 12, display: 'inline-block' }} />}
        </span>

        {!hasChildren && <GlowDot color={node.isStandard ? '#6366f1' : '#8b5cf6'} size={5} />}

        <span style={{
          flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          fontSize: 12.5, fontWeight: isSelected ? 600 : 400,
          color: isSelected ? '#e2e8f0' : '#94a3b8',
        }}>
          {node.name}
        </span>

        {(node.ownCount > 0 || node.count > 0) && (
          <span style={{
            fontSize: 10, fontWeight: 700, minWidth: 20, textAlign: 'center',
            padding: '1px 6px', borderRadius: 10,
            background: node.isStandard ? 'rgba(99,102,241,0.15)' : 'rgba(139,92,246,0.15)',
            color: node.isStandard ? '#818cf8' : '#a78bfa',
          }}>
            {node.ownCount > 0 ? node.ownCount : node.count}
          </span>
        )}
      </button>

      {open && hasChildren && (
        <div style={{ borderLeft: '1px solid rgba(100,116,139,0.2)', marginLeft: 18, paddingLeft: 2 }}>
          {node.children.map(ch => (
            <TreeNode key={ch.id} node={ch} onSelect={onSelect} selected={selected} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── ClauseCard ─────────────────────────────────────────────────────────────────
function ClauseCard({ clause }) {
  const [scored, setScored] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [copied, setCopied] = useState(false);
  const risk = (clause.risk_level || 'UNKNOWN').toUpperCase();
  const rColor = RISK_COLOR[risk] || RISK_COLOR.UNKNOWN;

  const handleScore = async () => {
    setScoring(true);
    try { const r = await svc.scoreRisk(clause.text); setScored(r.data); }
    catch { setScored({ risk: 'Unknown', reason: 'Scoring failed', fix: '' }); }
    finally { setScoring(false); }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(clause.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div style={{
      background: 'rgba(15,23,42,0.8)',
      border: '1px solid rgba(148,163,184,0.07)',
      borderLeft: `3px solid ${rColor}`,
      borderRadius: 12,
      padding: '12px 14px',
      transition: 'all 0.2s ease',
    }}
    onMouseEnter={e => e.currentTarget.style.borderColor = `rgba(148,163,184,0.15)`}
    onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(148,163,184,0.07)'}
    >
      <p style={{ color: '#cbd5e1', fontSize: 12.5, lineHeight: 1.7, marginBottom: 8 }}>{clause.text}</p>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <RiskBadge level={risk} />
        {clause.risk_score != null && (
          <span style={{ fontSize: 11, color: '#64748b' }}>
            {Number(clause.risk_score).toFixed(2)}
          </span>
        )}
        {clause.contract_title && (
          <span style={{ fontSize: 11, color: '#475569', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {clause.contract_title}
          </span>
        )}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
          <button onClick={handleCopy} style={{ padding: '3px 8px', borderRadius: 6, background: 'rgba(100,116,139,0.12)', border: 'none', cursor: 'pointer', color: copied ? '#10b981' : '#64748b', transition: 'all 0.15s' }}>
            {copied ? <Check size={11} /> : <Copy size={11} />}
          </button>
          <button onClick={handleScore} disabled={scoring} style={{
            display: 'flex', alignItems: 'center', gap: 4,
            padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: 'pointer',
            background: 'rgba(139,92,246,0.12)', color: '#a78bfa',
            border: '1px solid rgba(139,92,246,0.2)', transition: 'all 0.15s',
            opacity: scoring ? 0.6 : 1,
          }}>
            {scoring ? <Loader size={9} style={{ animation: 'spin 1s linear infinite' }} /> : <Shield size={9} />}
            Score
          </button>
        </div>
      </div>
      {scored && (
        <div style={{
          marginTop: 10, padding: '10px 12px', borderRadius: 8,
          background: RISK_BG[(scored.risk || 'UNKNOWN').toUpperCase()] || RISK_BG.UNKNOWN,
          border: `1px solid ${RISK_COLOR[(scored.risk || 'UNKNOWN').toUpperCase()] || RISK_COLOR.UNKNOWN}33`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <Shield size={11} style={{ color: RISK_COLOR[(scored.risk || 'UNKNOWN').toUpperCase()] || '#6b7280' }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: RISK_COLOR[(scored.risk || 'UNKNOWN').toUpperCase()] || '#6b7280' }}>
              AI Risk: {scored.risk}
            </span>
          </div>
          <p style={{ fontSize: 11, color: '#94a3b8', marginBottom: scored.fix ? 4 : 0 }}>{scored.reason}</p>
          {scored.fix && <p style={{ fontSize: 11, color: '#10b981' }}>Fix: {scored.fix}</p>}
        </div>
      )}
    </div>
  );
}

// ── ClauseInsightsPanel ────────────────────────────────────────────────────────
function ClauseInsightsPanel({ node }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState('clauses');

  useEffect(() => {
    if (!node) return;
    setLoading(true); setData(null);
    svc.getInsights(node.name)
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [node?.id]);

  if (!node) return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, padding: 40 }}>
      <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Layers size={22} style={{ color: '#7c3aed', opacity: 0.5 }} />
      </div>
      <p style={{ color: '#475569', fontSize: 13, textAlign: 'center', maxWidth: 200 }}>
        Select a category from the tree to explore its clauses
      </p>
    </div>
  );

  const riskBreakdown = data ? Object.entries(data.risk_breakdown || {}) : [];

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '16px 20px 12px', borderBottom: '1px solid rgba(148,163,184,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 8 }}>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#f1f5f9', marginBottom: 3 }}>{node.name}</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 11, color: '#64748b' }}>
                {node.count} clause{node.count !== 1 ? 's' : ''}
              </span>
              <span style={{ fontSize: 11, color: '#334155' }}>·</span>
              <span style={{ fontSize: 11, color: node.isStandard ? '#818cf8' : '#a78bfa' }}>
                {node.isStandard ? '⬡ Standard' : '✦ Auto-discovered'}
              </span>
              {data && (
                <>
                  <span style={{ fontSize: 11, color: '#334155' }}>·</span>
                  <span style={{ fontSize: 11, color: '#64748b' }}>
                    {data.unique_contracts} contract{data.unique_contracts !== 1 ? 's' : ''}
                  </span>
                </>
              )}
            </div>
          </div>
          {riskBreakdown.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              {riskBreakdown.map(([risk, count]) => (
                <span key={risk} style={{
                  fontSize: 10, fontWeight: 700, padding: '3px 8px', borderRadius: 10,
                  background: RISK_BG[risk] || RISK_BG.UNKNOWN,
                  color: RISK_COLOR[risk] || RISK_COLOR.UNKNOWN,
                  border: `1px solid ${RISK_COLOR[risk] || RISK_COLOR.UNKNOWN}33`,
                }}>
                  {risk} {count}
                </span>
              ))}
            </div>
          )}
        </div>

        {data && data.unique_contracts > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <div style={{ flex: 1, height: 4, borderRadius: 4, background: 'rgba(148,163,184,0.08)', overflow: 'hidden' }}>
              {riskBreakdown.map(([risk]) => {
                const pct = data.total_clauses > 0
                  ? ((data.risk_breakdown[risk] || 0) / data.total_clauses) * 100 : 0;
                return pct > 0 ? (
                  <div key={risk} style={{
                    display: 'inline-block', height: '100%', width: `${pct}%`,
                    background: RISK_COLOR[risk] || '#6b7280',
                  }} />
                ) : null;
              })}
            </div>
            <span style={{ fontSize: 10, color: '#475569', whiteSpace: 'nowrap' }}>
              {data.total_clauses} total
            </span>
          </div>
        )}

        <div style={{ display: 'flex', gap: 4 }}>
          {[{ id: 'clauses', label: 'Sample Clauses' }, { id: 'insights', label: 'Contract Distribution' }].map(v => (
            <button key={v.id} onClick={() => setActiveView(v.id)} style={{
              padding: '4px 12px', borderRadius: 8, fontSize: 11, fontWeight: 500, cursor: 'pointer',
              transition: 'all 0.15s',
              background: activeView === v.id ? 'rgba(139,92,246,0.15)' : 'transparent',
              color: activeView === v.id ? '#a78bfa' : '#64748b',
              border: activeView === v.id ? '1px solid rgba(139,92,246,0.25)' : '1px solid transparent',
            }}>
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '32px 0' }}>
            <Loader size={20} style={{ color: '#8b5cf6', animation: 'spin 1s linear infinite' }} />
          </div>
        )}

        {!loading && activeView === 'clauses' && (
          <>
            {(!data || !data.sample_clauses?.length) && (
              <p style={{ color: '#475569', fontSize: 13, textAlign: 'center', padding: '32px 0' }}>
                No extracted clauses in this category yet.
              </p>
            )}
            {data?.sample_clauses?.map((c, i) => <ClauseCard key={i} clause={c} />)}
          </>
        )}

        {!loading && activeView === 'insights' && (
          <>
            {(!data || !data.contract_distribution?.length) && (
              <p style={{ color: '#475569', fontSize: 13, textAlign: 'center', padding: '32px 0' }}>
                No contract data available.
              </p>
            )}
            {data?.contract_distribution?.map((c, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 14px', borderRadius: 10,
                background: 'rgba(15,23,42,0.6)',
                border: '1px solid rgba(148,163,184,0.07)',
              }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#334155', width: 20, textAlign: 'right' }}>{i + 1}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 12.5, color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {c.title || c.contract_id}
                  </p>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '2px 9px', borderRadius: 10,
                  background: 'rgba(99,102,241,0.12)', color: '#818cf8',
                }}>
                  {c.clause_count} clause{c.clause_count !== 1 ? 's' : ''}
                </span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

// ── SearchTab ──────────────────────────────────────────────────────────────────
function SearchTab() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [focused, setFocused] = useState(false);

  const doSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true); setError(''); setResults([]);
    try {
      const r = await svc.search(query.trim(), 20);
      setResults(r.data.results || []);
    } catch (e) {
      setError(e?.response?.data?.error || 'Search failed');
    } finally { setLoading(false); }
  }, [query]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Search bar */}
      <div style={{
        position: 'relative',
        background: focused ? 'rgba(139,92,246,0.06)' : 'rgba(15,23,42,0.8)',
        border: `1px solid ${focused ? 'rgba(139,92,246,0.5)' : 'rgba(148,163,184,0.1)'}`,
        borderRadius: 14,
        boxShadow: focused ? '0 0 0 3px rgba(139,92,246,0.1), 0 0 24px rgba(139,92,246,0.08)' : 'none',
        transition: 'all 0.2s ease',
        display: 'flex', alignItems: 'center',
      }}>
        <Search size={16} style={{ position: 'absolute', left: 16, color: focused ? '#8b5cf6' : '#475569', transition: 'color 0.2s' }} />
        <input
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            padding: '14px 16px 14px 44px', fontSize: 14, color: '#f1f5f9',
            fontFamily: 'inherit',
          }}
          placeholder="Search clauses… e.g. indemnification third party, liability cap, governing law"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && doSearch()}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
        <button
          onClick={doSearch}
          disabled={loading || !query.trim()}
          style={{
            margin: 6, padding: '8px 20px', borderRadius: 10, fontSize: 13, fontWeight: 600,
            background: loading || !query.trim() ? 'rgba(139,92,246,0.3)' : 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            color: '#fff', border: 'none', cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 7, transition: 'all 0.2s',
            boxShadow: !loading && query.trim() ? '0 4px 14px rgba(139,92,246,0.35)' : 'none',
          }}
        >
          {loading ? <Loader size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Zap size={13} />}
          Search
        </button>
      </div>

      {/* Hint chips */}
      {!results.length && !loading && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {['indemnification', 'limitation of liability', 'governing law', 'force majeure', 'IP ownership'].map(hint => (
            <button key={hint} onClick={() => { setQuery(hint); }}
              style={{
                padding: '4px 12px', borderRadius: 20, fontSize: 11, cursor: 'pointer',
                background: 'rgba(99,102,241,0.08)', color: '#818cf8',
                border: '1px solid rgba(99,102,241,0.15)', transition: 'all 0.15s',
              }}>
              {hint}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderRadius: 10, background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)', color: '#fb7185', fontSize: 13 }}>
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      {/* Results */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {results.map((r, i) => (
          <div key={i} style={{
            background: 'rgba(15,23,42,0.7)',
            border: '1px solid rgba(148,163,184,0.07)',
            borderRadius: 14, padding: '14px 16px',
            transition: 'all 0.18s ease',
          }}
          onMouseEnter={e => { e.currentTarget.style.border = '1px solid rgba(139,92,246,0.2)'; e.currentTarget.style.background = 'rgba(139,92,246,0.03)'; }}
          onMouseLeave={e => { e.currentTarget.style.border = '1px solid rgba(148,163,184,0.07)'; e.currentTarget.style.background = 'rgba(15,23,42,0.7)'; }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 8 }}>
              <span style={{
                width: 22, height: 22, borderRadius: 6, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'rgba(99,102,241,0.12)', color: '#818cf8', fontSize: 10, fontWeight: 700,
              }}>{i + 1}</span>
              <p style={{ flex: 1, color: '#cbd5e1', fontSize: 13, lineHeight: 1.7 }}>{r.text}</p>
              <div style={{ flexShrink: 0, textAlign: 'right' }}>
                <div style={{ fontSize: 11, color: '#475569', fontFamily: 'monospace', marginBottom: 2 }}>
                  {(r.score * 100).toFixed(1)}%
                </div>
                {r.qwen_score > 0 && (
                  <div style={{ fontSize: 11, color: '#a78bfa', fontFamily: 'monospace' }}>
                    ✦ {r.qwen_score}/100
                  </div>
                )}
              </div>
            </div>
            {r.qwen_reason && (
              <p style={{ fontSize: 11.5, color: '#475569', marginBottom: 8, paddingLeft: 12, borderLeft: '2px solid rgba(139,92,246,0.3)', fontStyle: 'italic' }}>
                {r.qwen_reason}
              </p>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', paddingLeft: 34 }}>
              <span style={{ fontSize: 11, padding: '2px 9px', borderRadius: 10, background: 'rgba(139,92,246,0.12)', color: '#a78bfa' }}>
                {r.category}
              </span>
              <RiskBadge level={r.risk_level} />
            </div>
          </div>
        ))}
        {!loading && !results.length && query && (
          <div style={{ textAlign: 'center', padding: '48px 0', color: '#475569', fontSize: 13 }}>
            No results — try a different query
          </div>
        )}
      </div>
    </div>
  );
}

// ── Clause Negotiator Tab ──────────────────────────────────────────────────────
const NEGOTIATE_MODES = [
  { id: 'safer',      label: 'Safer',       icon: Shield,      color: '#10b981', desc: 'Reduce liability, add protections'       },
  { id: 'market',     label: 'Market Std',  icon: Globe,       color: '#3b82f6', desc: 'Balanced commercial standard language'   },
  { id: 'aggressive', label: 'Aggressive',  icon: Target,      color: '#f43f5e', desc: 'Maximum protection for drafting party'   },
  { id: 'explain',    label: 'Explain',     icon: Brain,       color: '#a855f7', desc: 'Plain English explanation of clause'     },
];

function NegotiateTab({ prefillText = '', onPrefillUsed }) {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('safer');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [riskScore, setRiskScore] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (prefillText) { setText(prefillText); onPrefillUsed?.(); }
  }, [prefillText]);

  const doNegotiate = async () => {
    if (!text.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try { const r = await svc.negotiate(text.trim(), mode); setResult(r.data); }
    catch (e) { setError(e?.response?.data?.error || 'Negotiation failed'); }
    finally { setLoading(false); }
  };

  const doScore = async () => {
    if (!text.trim()) return;
    setScoring(true); setRiskScore(null);
    try { const r = await svc.scoreRisk(text.trim()); setRiskScore(r.data); }
    catch { setRiskScore({ risk: 'Unknown', reason: 'Scoring unavailable', fix: '' }); }
    finally { setScoring(false); }
  };

  const handleCopy = () => {
    if (result?.output) {
      navigator.clipboard.writeText(result.output);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  const selectedMode = NEGOTIATE_MODES.find(m => m.id === mode);

  return (
    <div style={{ maxWidth: 820, display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Hero banner */}
      <div style={{
        padding: '16px 20px',
        background: 'linear-gradient(135deg, rgba(139,92,246,0.12) 0%, rgba(99,102,241,0.06) 100%)',
        border: '1px solid rgba(139,92,246,0.2)',
        borderRadius: 14,
        display: 'flex', alignItems: 'center', gap: 14,
      }}>
        <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, #8b5cf6, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 4px 14px rgba(139,92,246,0.4)' }}>
          <MessageSquare size={18} style={{ color: '#fff' }} />
        </div>
        <div>
          <h2 style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', marginBottom: 3 }}>Clause Negotiation AI</h2>
          <p style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>
            Paste any contract clause · Choose a rewrite mode · AI generates a safer, market-standard, or aggressive variant with key change analysis.
          </p>
        </div>
      </div>

      {/* Mode selector */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        {NEGOTIATE_MODES.map(m => {
          const Icon = m.icon;
          const active = mode === m.id;
          return (
            <button key={m.id} onClick={() => setMode(m.id)} style={{
              padding: '12px 14px', borderRadius: 12, textAlign: 'left', cursor: 'pointer',
              background: active ? `${m.color}18` : 'rgba(15,23,42,0.6)',
              border: `1px solid ${active ? m.color + '44' : 'rgba(148,163,184,0.08)'}`,
              boxShadow: active ? `0 0 16px ${m.color}22` : 'none',
              transition: 'all 0.2s ease',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5 }}>
                <Icon size={13} style={{ color: m.color }} />
                <span style={{ fontSize: 12.5, fontWeight: 700, color: active ? m.color : '#94a3b8' }}>{m.label}</span>
              </div>
              <p style={{ fontSize: 10.5, color: '#475569', lineHeight: 1.4 }}>{m.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Input area */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Original Clause</span>
          <span style={{ fontSize: 11, color: '#334155' }}>{text.length} chars</span>
        </div>
        <textarea
          rows={6}
          style={{
            width: '100%', background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(148,163,184,0.1)',
            borderRadius: 12, padding: '14px 16px', fontSize: 13, color: '#cbd5e1',
            outline: 'none', resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.7,
            boxSizing: 'border-box',
          }}
          placeholder="Paste the contract clause text here…"
          value={text}
          onChange={e => setText(e.target.value)}
          onFocus={e => { e.target.style.border = '1px solid rgba(139,92,246,0.4)'; e.target.style.boxShadow = '0 0 0 3px rgba(139,92,246,0.08)'; }}
          onBlur={e => { e.target.style.border = '1px solid rgba(148,163,184,0.1)'; e.target.style.boxShadow = 'none'; }}
        />
        <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
          <button onClick={doNegotiate} disabled={loading || !text.trim()} style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', borderRadius: 10,
            fontSize: 13, fontWeight: 600, cursor: loading || !text.trim() ? 'not-allowed' : 'pointer',
            background: loading || !text.trim() ? 'rgba(139,92,246,0.3)' : 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            color: '#fff', border: 'none',
            boxShadow: !loading && text.trim() ? '0 4px 14px rgba(139,92,246,0.35)' : 'none',
            transition: 'all 0.2s',
          }}>
            {loading ? <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <ArrowRight size={14} />}
            Generate {selectedMode?.label} Version
          </button>
          <button onClick={doScore} disabled={scoring || !text.trim()} style={{
            display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10,
            fontSize: 13, fontWeight: 500, cursor: scoring || !text.trim() ? 'not-allowed' : 'pointer',
            background: 'rgba(148,163,184,0.07)', color: '#94a3b8',
            border: '1px solid rgba(148,163,184,0.1)', transition: 'all 0.2s',
          }}>
            {scoring ? <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Shield size={14} />}
            Score Risk
          </button>
        </div>
      </div>

      {/* Risk score */}
      {riskScore && (
        <div style={{
          padding: '12px 16px', borderRadius: 12,
          background: RISK_BG[(riskScore.risk || 'UNKNOWN').toUpperCase()] || RISK_BG.UNKNOWN,
          border: `1px solid ${RISK_COLOR[(riskScore.risk || 'UNKNOWN').toUpperCase()] || RISK_COLOR.UNKNOWN}33`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
            <AlertCircle size={14} style={{ color: RISK_COLOR[(riskScore.risk || 'UNKNOWN').toUpperCase()] || '#6b7280' }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: RISK_COLOR[(riskScore.risk || 'UNKNOWN').toUpperCase()] || '#6b7280' }}>
              Risk: {riskScore.risk}
            </span>
          </div>
          <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: riskScore.fix ? 5 : 0 }}>{riskScore.reason}</p>
          {riskScore.fix && <p style={{ fontSize: 12, color: '#10b981' }}>Suggested fix: {riskScore.fix}</p>}
        </div>
      )}

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)', color: '#fb7185', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertTriangle size={14} /> {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div style={{ border: '1px solid rgba(139,92,246,0.25)', borderRadius: 14, overflow: 'hidden' }}>
          <div style={{
            padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(139,92,246,0.12) 0%, rgba(99,102,241,0.06) 100%)',
            borderBottom: '1px solid rgba(139,92,246,0.15)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Brain size={14} style={{ color: '#a78bfa' }} />
              <span style={{ fontSize: 13, fontWeight: 700, color: '#c4b5fd' }}>
                {NEGOTIATE_MODES.find(m => m.id === result.mode)?.label || result.mode} Version
              </span>
              {result.risk_delta && (
                <span style={{
                  fontSize: 11, padding: '2px 9px', borderRadius: 10, fontWeight: 600,
                  background: result.risk_delta === 'improved' ? 'rgba(16,185,129,0.12)' : result.risk_delta === 'worsened' ? 'rgba(244,63,94,0.12)' : 'rgba(148,163,184,0.1)',
                  color: result.risk_delta === 'improved' ? '#10b981' : result.risk_delta === 'worsened' ? '#f43f5e' : '#94a3b8',
                }}>
                  {result.risk_delta === 'improved' ? '↑' : result.risk_delta === 'worsened' ? '↓' : '~'} {result.risk_delta}
                </span>
              )}
            </div>
            <button onClick={handleCopy} style={{
              display: 'flex', alignItems: 'center', gap: 5, padding: '5px 12px', borderRadius: 8,
              background: 'rgba(148,163,184,0.07)', border: '1px solid rgba(148,163,184,0.1)',
              color: copied ? '#10b981' : '#64748b', fontSize: 11, fontWeight: 500, cursor: 'pointer', transition: 'all 0.15s',
            }}>
              {copied ? <Check size={11} /> : <Copy size={11} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div style={{ padding: '16px 18px', background: 'rgba(9,14,25,0.8)' }}>
            <p style={{ color: '#cbd5e1', fontSize: 13, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{result.output}</p>
          </div>
          {result.key_changes?.length > 0 && (
            <div style={{ padding: '12px 18px', background: 'rgba(15,23,42,0.5)', borderTop: '1px solid rgba(148,163,184,0.06)' }}>
              <p style={{ fontSize: 10, fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Key Changes</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {result.key_changes.map((change, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                    <CheckCircle size={12} style={{ color: '#10b981', marginTop: 2, flexShrink: 0 }} />
                    <span style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5 }}>{change}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── AnalyticsTab ───────────────────────────────────────────────────────────────
function AnalyticsTab() {
  const [data, setData] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('overview');

  useEffect(() => {
    Promise.all([svc.getAnalytics(), svc.getContractRisk()])
      .then(([aRes, rRes]) => { setData(aRes.data); setRiskData(rRes.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
        <div style={{ width: 40, height: 40, borderRadius: '50%', border: '2px solid rgba(139,92,246,0.3)', borderTop: '2px solid #8b5cf6', animation: 'spin 0.8s linear infinite' }} />
        <span style={{ color: '#475569', fontSize: 12 }}>Loading analytics…</span>
      </div>
    </div>
  );
  if (!data) return <p style={{ color: '#475569', textAlign: 'center', padding: '64px 0' }}>Could not load analytics</p>;

  const kpis = [
    { label: 'Total Categories', value: data.total_categories,      icon: Layers,     color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)'  },
    { label: 'Clauses Indexed',  value: data.total_clauses_indexed,  icon: FileText,   color: '#3b82f6', bg: 'rgba(59,130,246,0.1)'  },
    { label: 'Standard Nodes',   value: data.standard_categories,    icon: CheckCircle,color: '#10b981', bg: 'rgba(16,185,129,0.1)'  },
    { label: 'Auto-Discovered',  value: data.auto_discovered,        icon: Sparkles,   color: '#f59e0b', bg: 'rgba(245,158,11,0.1)'  },
  ];

  const contracts = riskData?.contracts || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid rgba(148,163,184,0.06)', paddingBottom: 4 }}>
        {[{ id: 'overview', label: 'Library Overview' }, { id: 'contracts', label: 'Contract Risk View' }].map(v => (
          <button key={v.id} onClick={() => setActiveView(v.id)} style={{
            padding: '6px 16px', borderRadius: 8, fontSize: 12.5, fontWeight: 500, cursor: 'pointer',
            background: activeView === v.id ? 'rgba(139,92,246,0.12)' : 'transparent',
            color: activeView === v.id ? '#a78bfa' : '#64748b',
            border: activeView === v.id ? '1px solid rgba(139,92,246,0.2)' : '1px solid transparent',
            transition: 'all 0.15s',
          }}>
            {v.label}
          </button>
        ))}
      </div>

      {activeView === 'overview' && (
        <>
          {/* KPI row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {kpis.map(k => {
              const Icon = k.icon;
              return (
                <div key={k.label} style={{
                  background: k.bg, border: `1px solid ${k.color}22`,
                  borderRadius: 14, padding: '16px 18px',
                  boxShadow: `0 4px 20px ${k.color}10`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <div style={{ width: 32, height: 32, borderRadius: 8, background: `${k.color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon size={15} style={{ color: k.color }} />
                    </div>
                    <span style={{ fontSize: 11, color: '#64748b', fontWeight: 500 }}>{k.label}</span>
                  </div>
                  <p style={{ fontSize: 28, fontWeight: 800, color: '#f1f5f9', lineHeight: 1 }}>
                    {(k.value || 0).toLocaleString()}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Charts row */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
            <GlassCard style={{ padding: '16px 20px' }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8', marginBottom: 16 }}>Top Categories by Clause Count</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data.top_categories} barSize={20} margin={{ bottom: 30 }}>
                  <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 10 }} interval={0} angle={-30} textAnchor="end" height={55} />
                  <YAxis tick={{ fill: '#475569', fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(139,92,246,0.06)' }} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {data.top_categories.map((_, i) => <Cell key={i} fill={BAR_PALETTE[i % BAR_PALETTE.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </GlassCard>

            <GlassCard style={{ padding: '16px 20px' }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8', marginBottom: 12 }}>Taxonomy Composition</p>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Standard', value: data.standard_categories },
                      { name: 'Auto-Discovered', value: data.auto_discovered },
                    ]}
                    cx="50%" cy="50%" outerRadius={72} innerRadius={36} dataKey="value"
                    stroke="none"
                  >
                    <Cell fill="#6366f1" />
                    <Cell fill="#a855f7" />
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
                </PieChart>
              </ResponsiveContainer>
            </GlassCard>
          </div>
        </>
      )}

      {activeView === 'contracts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0' }}>
            <TrendingUp size={12} style={{ color: '#475569' }} />
            <span style={{ fontSize: 11, color: '#475569' }}>
              Ranked by weighted risk score (High×3 + Medium×1) ÷ total clauses
            </span>
          </div>

          {contracts.length === 0 && (
            <p style={{ color: '#475569', textAlign: 'center', padding: '48px 0', fontSize: 13 }}>No contract risk data available.</p>
          )}

          {contracts.map((c, i) => {
            const highPct = c.total_clauses > 0 ? (c.high_risk / c.total_clauses) * 100 : 0;
            const medPct  = c.total_clauses > 0 ? (c.medium_risk / c.total_clauses) * 100 : 0;
            const lowPct  = c.total_clauses > 0 ? (c.low_risk / c.total_clauses) * 100 : 0;
            const rColor  = c.risk_score >= 1.5 ? '#f43f5e' : c.risk_score >= 0.8 ? '#f59e0b' : '#10b981';
            return (
              <div key={c.contract_id} style={{
                background: 'rgba(15,23,42,0.7)',
                border: '1px solid rgba(148,163,184,0.07)',
                borderRadius: 12, padding: '14px 16px', transition: 'all 0.18s',
              }}
              onMouseEnter={e => e.currentTarget.style.border = '1px solid rgba(148,163,184,0.12)'}
              onMouseLeave={e => e.currentTarget.style.border = '1px solid rgba(148,163,184,0.07)'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <span style={{ fontSize: 11, color: '#334155', width: 20, textAlign: 'right' }}>{i + 1}</span>
                  <span style={{ flex: 1, fontSize: 13, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 15, fontWeight: 800, color: rColor, fontFamily: 'monospace' }}>
                      {c.risk_score.toFixed(2)}
                    </span>
                    <span style={{ fontSize: 11, color: '#475569' }}>{c.total_clauses} clauses</span>
                  </div>
                </div>
                <div style={{ height: 6, borderRadius: 3, background: 'rgba(148,163,184,0.06)', display: 'flex', overflow: 'hidden', marginBottom: 6 }}>
                  {highPct > 0 && <div style={{ width: `${highPct}%`, background: '#f43f5e' }} />}
                  {medPct  > 0 && <div style={{ width: `${medPct}%`, background: '#f59e0b' }} />}
                  {lowPct  > 0 && <div style={{ width: `${lowPct}%`, background: '#10b981' }} />}
                </div>
                <div style={{ display: 'flex', gap: 14, paddingLeft: 28 }}>
                  <span style={{ fontSize: 11, color: '#f87171' }}>⚠ {c.high_risk} high</span>
                  <span style={{ fontSize: 11, color: '#fbbf24' }}>◑ {c.medium_risk} medium</span>
                  <span style={{ fontSize: 11, color: '#34d399' }}>✓ {c.low_risk} low</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── GraphTab ───────────────────────────────────────────────────────────────────
const ACLNode = ({ data }) => (
  <>
    {[Position.Top, Position.Bottom, Position.Left, Position.Right].map(p => (
      <Handle key={`t${p}`} type="target" position={p} style={{ opacity: 0 }} />
    ))}
    <div
      style={{
        background: `radial-gradient(circle at 32% 32%, ${data.color}ff 0%, ${data.color}cc 55%, ${data.color}88 100%)`,
        border: `2.5px solid ${data.color}`,
        borderRadius: '50%',
        width: data.size, height: data.size,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff', fontWeight: 700,
        fontSize: `${Math.max(data.size / 7.5, 8)}px`,
        textAlign: 'center', padding: 6, cursor: 'pointer',
        boxShadow: `0 0 18px ${data.color}88, 0 0 40px ${data.color}44, inset 0 0 12px ${data.color}33`,
        transition: 'all 0.22s ease', lineHeight: 1.2,
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.18)'; e.currentTarget.style.boxShadow = `0 0 32px ${data.color}cc, 0 0 70px ${data.color}66`; }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)';    e.currentTarget.style.boxShadow = `0 0 18px ${data.color}88, 0 0 40px ${data.color}44`; }}
    >
      <span style={{ overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
        {data.label}
      </span>
    </div>
    {[Position.Top, Position.Bottom, Position.Left, Position.Right].map(p => (
      <Handle key={`s${p}`} type="source" position={p} style={{ opacity: 0 }} />
    ))}
  </>
);
const aclNodeTypes = { aclNode: ACLNode };

function buildReactFlowGraph(apiNodes, apiEdges) {
  const cats    = apiNodes.filter(n => n.type === 'category');
  const clauses = apiNodes.filter(n => n.type === 'clause');
  const clauseCatId = {};
  apiEdges.forEach(e => { if (e.label === 'BELONGS_TO') clauseCatId[e.source] = e.target; });
  const byCat = {};
  clauses.forEach(n => { const cid = clauseCatId[n.id] || '__none__'; if (!byCat[cid]) byCat[cid] = []; byCat[cid].push(n); });
  const CX = 0, CY = 0, R_CAT = 420, R_CL = 110;
  const rfNodes = []; const catPositions = {};
  cats.forEach((n, i) => {
    const angle = (i / cats.length) * 2 * Math.PI - Math.PI / 2;
    const x = CX + R_CAT * Math.cos(angle), y = CY + R_CAT * Math.sin(angle);
    catPositions[n.id] = { x, y };
    rfNodes.push({ id: n.id, type: 'aclNode', position: { x: x - 38, y: y - 38 }, data: { label: n.label, type: 'category', color: CAT_COLORS[i % CAT_COLORS.length], size: 76 } });
  });
  clauses.forEach(n => {
    const catId = clauseCatId[n.id] || '__none__'; const siblings = byCat[catId] || [n];
    const localIdx = siblings.indexOf(n); const cp = catPositions[catId] || { x: 0, y: 0 };
    const catIdx = cats.findIndex(c => c.id === catId);
    const baseAngle = catIdx >= 0 ? (catIdx / cats.length) * 2 * Math.PI - Math.PI / 2 : 0;
    const spread = Math.min(Math.PI * 0.6, (siblings.length / 6) * Math.PI);
    const angle = siblings.length > 1 ? (baseAngle - spread / 2) + (localIdx / (siblings.length - 1)) * spread : baseAngle;
    const x = cp.x + R_CL * Math.cos(angle), y = cp.y + R_CL * Math.sin(angle);
    const risk = n.risk || 'UNKNOWN';
    rfNodes.push({ id: n.id, type: 'aclNode', position: { x: x - 22, y: y - 22 }, data: { label: n.label || 'Clause', type: 'clause', color: RISK_COLOR[risk] || RISK_COLOR.UNKNOWN, size: 44, risk } });
  });
  const rfEdges = apiEdges.map((e, i) => {
    const isSim = e.label === 'SIMILAR_TO'; const catIdx = cats.findIndex(c => c.id === e.target);
    const color = isSim ? '#a855f7' : (catIdx >= 0 ? CAT_COLORS[catIdx % CAT_COLORS.length] : '#4C8EDA');
    return { id: `e${i}`, source: e.source, target: e.target, type: 'smoothstep', animated: !isSim, label: e.label, markerEnd: { type: MarkerType.ArrowClosed, color, width: 16, height: 16 }, style: { stroke: color, strokeWidth: isSim ? 1.5 : 2, strokeOpacity: 0.75 }, labelStyle: { fill: '#94a3b8', fontSize: 10 }, labelBgStyle: { fill: '#0a0f1a', fillOpacity: 0.9 }, labelBgPadding: [4, 3], labelBgBorderRadius: 3 };
  });
  return { rfNodes, rfEdges };
}

function GraphNodePanel({ selected, graphData, onClose, onNegotiate }) {
  const [scored, setScored] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [copied, setCopied] = useState(false);

  const nodeRaw = useMemo(() => {
    if (!selected) return null;
    return (graphData.nodes || []).find(n => n.id === selected.id) || null;
  }, [selected, graphData]);

  const categoryName = useMemo(() => {
    if (!nodeRaw || nodeRaw.type !== 'clause') return null;
    const edge = (graphData.edges || []).find(e => e.source === nodeRaw.id && e.label === 'BELONGS_TO');
    return edge ? ((graphData.nodes || []).find(n => n.id === edge.target))?.label || null : null;
  }, [nodeRaw, graphData]);

  const similarIds = useMemo(() => {
    if (!nodeRaw || nodeRaw.type !== 'clause') return [];
    return (graphData.edges || []).filter(e => (e.source === nodeRaw.id || e.target === nodeRaw.id) && e.label === 'SIMILAR_TO').map(e => e.source === nodeRaw.id ? e.target : e.source).slice(0, 3);
  }, [nodeRaw, graphData]);

  const similarClauses = useMemo(() => similarIds.map(id => (graphData.nodes || []).find(n => n.id === id)).filter(Boolean), [similarIds, graphData]);

  useEffect(() => { setScored(null); }, [selected?.id]);

  if (!selected || !nodeRaw) return null;

  const isCategory = nodeRaw.type === 'category';
  const risk = (nodeRaw.risk || 'UNKNOWN').toUpperCase();
  const rColor = RISK_COLOR[risk] || '#6b7280';
  const fullText = nodeRaw.fullText || nodeRaw.label || '';
  const clauseCount = isCategory ? (graphData.edges || []).filter(e => e.target === nodeRaw.id && e.label === 'BELONGS_TO').length : null;

  return (
    <div style={{ background: 'rgba(9,14,25,0.95)', border: '1px solid rgba(139,92,246,0.25)', borderRadius: 14, overflow: 'hidden', marginTop: 12 }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(148,163,184,0.06)', background: `${selected.data?.color}0d`, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ width: 38, height: 38, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: selected.data?.color, boxShadow: `0 0 14px ${selected.data?.color}88`, fontSize: 10, fontWeight: 800, color: '#fff' }}>
          {isCategory ? 'CAT' : 'CL'}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 2 }}>
            <span style={{ fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: selected.data?.color }}>
              {isCategory ? 'Category Node' : 'Clause Node'}
            </span>
            {!isCategory && <RiskBadge level={risk} />}
            {isCategory && clauseCount != null && (
              <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: 'rgba(99,102,241,0.12)', color: '#818cf8' }}>
                {clauseCount} clause{clauseCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <p style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {isCategory ? nodeRaw.label : (categoryName ? `in ${categoryName}` : 'Unclassified')}
          </p>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#475569', fontSize: 16, cursor: 'pointer', padding: 4 }}>✕</button>
      </div>

      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div>
          <p style={{ fontSize: 10, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
            {isCategory ? 'Category Name' : 'Full Clause Text'}
          </p>
          <div style={{ background: 'rgba(15,23,42,0.6)', borderRadius: 8, padding: '10px 12px', border: '1px solid rgba(148,163,184,0.06)' }}>
            <p style={{ fontSize: 12.5, color: '#cbd5e1', lineHeight: 1.7 }}>
              {fullText || <span style={{ color: '#334155', fontStyle: 'italic' }}>No text available</span>}
            </p>
          </div>
        </div>

        {!isCategory && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div style={{ background: 'rgba(15,23,42,0.5)', borderRadius: 8, padding: '10px 12px' }}>
              <p style={{ fontSize: 10, color: '#475569', marginBottom: 4 }}>Category</p>
              <p style={{ fontSize: 12.5, fontWeight: 600, color: '#a78bfa' }}>{categoryName || 'Unclassified'}</p>
            </div>
            <div style={{ background: 'rgba(15,23,42,0.5)', borderRadius: 8, padding: '10px 12px' }}>
              <p style={{ fontSize: 10, color: '#475569', marginBottom: 4 }}>Risk Level</p>
              <p style={{ fontSize: 12.5, fontWeight: 700, color: rColor }}>{risk}</p>
            </div>
          </div>
        )}

        {scored && (
          <div style={{ padding: '10px 12px', borderRadius: 8, background: RISK_BG[(scored.risk || 'UNKNOWN').toUpperCase()] || RISK_BG.UNKNOWN, border: `1px solid ${RISK_COLOR[(scored.risk || 'UNKNOWN').toUpperCase()] || RISK_COLOR.UNKNOWN}33` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <Shield size={11} style={{ color: RISK_COLOR[(scored.risk || 'UNKNOWN').toUpperCase()] || '#6b7280' }} />
              <span style={{ fontSize: 11, fontWeight: 700, color: RISK_COLOR[(scored.risk || 'UNKNOWN').toUpperCase()] || '#6b7280' }}>AI: {scored.risk}</span>
            </div>
            <p style={{ fontSize: 11, color: '#94a3b8' }}>{scored.reason}</p>
            {scored.fix && <p style={{ fontSize: 11, color: '#10b981', marginTop: 4 }}>Fix: {scored.fix}</p>}
          </div>
        )}

        {!isCategory && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={async () => { setScoring(true); try { const r = await svc.scoreRisk(fullText); setScored(r.data); } catch { setScored({ risk: 'Unknown', reason: 'Unavailable', fix: '' }); } finally { setScoring(false); } }} disabled={scoring || !fullText} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 8, fontSize: 11, fontWeight: 500, cursor: 'pointer', background: 'rgba(148,163,184,0.08)', color: '#94a3b8', border: '1px solid rgba(148,163,184,0.1)', transition: 'all 0.15s' }}>
              {scoring ? <Loader size={10} style={{ animation: 'spin 1s linear infinite' }} /> : <Shield size={10} />}
              {scored ? 'Re-score' : 'Score Risk'}
            </button>
            <button onClick={() => onNegotiate(fullText)} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 8, fontSize: 11, fontWeight: 500, cursor: 'pointer', background: 'rgba(139,92,246,0.12)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.2)', transition: 'all 0.15s' }}>
              <MessageSquare size={10} /> Negotiate
            </button>
            <button onClick={() => { navigator.clipboard.writeText(fullText); setCopied(true); setTimeout(() => setCopied(false), 1500); }} disabled={!fullText} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px', borderRadius: 8, fontSize: 11, fontWeight: 500, cursor: 'pointer', background: 'rgba(148,163,184,0.08)', color: copied ? '#10b981' : '#94a3b8', border: '1px solid rgba(148,163,184,0.1)', transition: 'all 0.15s' }}>
              {copied ? <Check size={10} /> : <Copy size={10} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        )}

        {similarClauses.length > 0 && (
          <div>
            <p style={{ fontSize: 10, fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Similar Clauses ({similarClauses.length})</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              {similarClauses.map((sc, i) => (
                <div key={i} style={{ background: 'rgba(15,23,42,0.5)', borderRadius: 7, padding: '7px 10px', border: '1px solid rgba(148,163,184,0.05)' }}>
                  <p style={{ fontSize: 11.5, color: '#94a3b8', lineHeight: 1.6 }}>{sc.label}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function GraphTab({ onNegotiate }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    svc.getGraph(200).then(r => {
      const data = r.data;
      setGraphData({ ...data, nodes: (data.nodes || []).map(n => ({ ...n, fullText: n.fullLabel || n.label || '' })) });
    }).catch(() => setError('Failed to load graph')).finally(() => setLoading(false));
  }, []);

  const { rfNodes, rfEdges } = useMemo(() => buildReactFlowGraph(graphData.nodes || [], graphData.edges || []), [graphData]);
  const [nodes, setNodes, onNodesChange] = useNodesState(rfNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(rfEdges);
  useEffect(() => { setNodes(rfNodes); setEdges(rfEdges); }, [rfNodes, rfEdges]);

  const cats    = (graphData.nodes || []).filter(n => n.type === 'category');
  const clauses = (graphData.nodes || []).filter(n => n.type === 'clause');
  const onNodeClick = useCallback((_, node) => setSelected(node), []);

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
        <div style={{ width: 40, height: 40, borderRadius: '50%', border: '2px solid rgba(139,92,246,0.3)', borderTop: '2px solid #8b5cf6', animation: 'spin 0.8s linear infinite' }} />
        <span style={{ color: '#475569', fontSize: 12 }}>Building knowledge graph…</span>
      </div>
    </div>
  );
  if (error) return <p style={{ color: '#f43f5e', textAlign: 'center', padding: '48px 0' }}>{error}</p>;
  if (!graphData.nodes?.length) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 240, gap: 12 }}>
      <Network size={36} style={{ color: '#334155' }} />
      <p style={{ color: '#475569', fontSize: 13, textAlign: 'center' }}>No clause data found.<br />Upload and extract clauses first.</p>
    </div>
  );

  const legend = [
    { label: `Category (${cats.length})`, color: '#6366f1' },
    { label: `Clause (${clauses.length})`, color: '#4C8EDA' },
    { label: 'High Risk', color: '#f43f5e' },
    { label: 'Medium Risk', color: '#f59e0b' },
    { label: 'Low Risk', color: '#10b981' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        {legend.map(l => (
          <span key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#64748b' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: l.color, boxShadow: `0 0 6px ${l.color}` }} />
            {l.label}
          </span>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: '#334155' }}>
          {(graphData.edges || []).length} edges · drag · zoom · click to inspect
        </span>
      </div>

      {/* Graph canvas */}
      <div style={{ borderRadius: 14, overflow: 'hidden', border: '1px solid rgba(148,163,184,0.08)', height: selected ? 460 : 600, background: '#04080f', transition: 'height 0.3s ease' }}>
        <ReactFlow
          nodes={nodes} edges={edges}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={aclNodeTypes}
          fitView fitViewOptions={{ padding: 0.18 }}
          minZoom={0.2} maxZoom={2.5}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} color="#0f172a" gap={24} size={1} />
          <Controls style={{ background: '#0f172a', border: '1px solid rgba(148,163,184,0.1)', borderRadius: 10, boxShadow: '0 4px 20px rgba(0,0,0,0.4)' }} />
          <MiniMap style={{ background: '#0a0f1a', border: '1px solid rgba(148,163,184,0.08)', borderRadius: 10 }} nodeColor={n => n.data?.color || '#334155'} maskColor="rgba(0,0,0,0.65)" />
        </ReactFlow>
      </div>

      <GraphNodePanel selected={selected} graphData={graphData} onClose={() => setSelected(null)} onNegotiate={onNegotiate} />
    </div>
  );
}

// ── HowItWorksTab ──────────────────────────────────────────────────────────────
function HowItWorksTab() {
  const steps = [
    { n: '01', icon: Zap,        color: '#8b5cf6', title: 'Contract Upload → Signal',    body: 'A Django post_save signal fires when a Contract is created, queuing a Celery background task with a 90-second retry window to wait for clause extraction.' },
    { n: '02', icon: Brain,      color: '#6366f1', title: 'LDA Topic Discovery',         body: 'scikit-learn LDA (10 topics, online learning) runs across all clause texts, surfacing candidate new taxonomy category names not yet in the ontology.' },
    { n: '03', icon: Database,   color: '#3b82f6', title: 'AI Similarity Assignment',    body: 'Each clause is semantically encoded and matched to the nearest category. Score ≥ 0.72 → assign; 0.55–0.72 → sub-node; <0.55 → AI names a new root.' },
    { n: '04', icon: Sparkles,   color: '#06b6d4', title: 'AI Category Naming',          body: 'When a new category node is created, AI summarises the clause into a 2–5 word legal name like "Indemnification – Third Party".' },
    { n: '05', icon: Network,    color: '#10b981', title: 'Neo4j Ingestion',             body: 'Every clause gets a LibraryClause node and a BELONGS_TO edge to its category. Within-contract clause pairs with cosine ≥ 0.85 get SIMILAR_TO edges for relationship discovery.' },
    { n: '06', icon: Search,     color: '#f59e0b', title: 'Hybrid Search + AI Rerank',  body: 'Search blends keyword and semantic embeddings, then AI reranks the top 10 with 0–100 score + reason. Results are cached for 1 hour.' },
    { n: '07', icon: MessageSquare, color: '#f97316', title: 'Clause Negotiation AI',    body: 'Paste any clause and choose Safer / Market-Standard / Aggressive / Explain. AI rewrites the clause with key change bullets and a risk delta assessment.' },
    { n: '08', icon: Shield,     color: '#ef4444', title: 'Clause Risk Scoring',         body: 'AI scores any clause for legal risk (High/Medium/Low) with a one-sentence reason and a suggested fix. Available inline on every clause card throughout the UI.' },
    { n: '09', icon: TrendingUp, color: '#ec4899', title: 'Contract Risk View',          body: 'The Analytics tab shows every live contract ranked by weighted risk score (High×3 + Medium×1) / total clauses, with stacked bars for visual comparison.' },
    { n: '10', icon: Activity,   color: '#a855f7', title: 'Taxonomy Auto-Cleaning',      body: 'A daily Celery beat task merges near-duplicate category nodes (cosine similarity ≥ 0.88), keeping the ontology compact and accurate over time.' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0, position: 'relative', maxWidth: 780 }}>
      {/* Timeline line */}
      <div style={{ position: 'absolute', left: 27, top: 20, bottom: 20, width: 2, background: 'linear-gradient(180deg, #8b5cf6 0%, #6366f1 50%, rgba(99,102,241,0.1) 100%)', borderRadius: 2 }} />

      {steps.map((s, idx) => {
        const Icon = s.icon;
        return (
          <div key={s.n} style={{ display: 'flex', gap: 20, padding: '16px 0', position: 'relative' }}>
            {/* Step circle */}
            <div style={{
              width: 56, height: 56, borderRadius: '50%', flexShrink: 0,
              background: `${s.color}18`, border: `2px solid ${s.color}44`,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              boxShadow: `0 0 16px ${s.color}22`,
              position: 'relative', zIndex: 1,
            }}>
              <Icon size={16} style={{ color: s.color }} />
              <span style={{ fontSize: 9, fontWeight: 800, color: s.color, marginTop: 2, letterSpacing: '0.05em' }}>{s.n}</span>
            </div>

            {/* Content card */}
            <div style={{
              flex: 1, background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(148,163,184,0.07)',
              borderRadius: 12, padding: '14px 18px',
              borderLeft: `2px solid ${s.color}33`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 13.5, fontWeight: 700, color: '#e2e8f0' }}>{s.title}</span>
                <span style={{ fontSize: 10, padding: '1px 7px', borderRadius: 10, background: `${s.color}18`, color: s.color, fontWeight: 700 }}>
                  Step {s.n}
                </span>
              </div>
              <p style={{ fontSize: 12.5, color: '#64748b', lineHeight: 1.7 }}>{s.body}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AdvancedClauseLibrary() {
  const [activeTab, setActiveTab] = useState('explorer');
  const [tree, setTree] = useState([]);
  const [treeLoading, setTreeLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [seeding, setSeeding] = useState(false);
  const [seedMsg, setSeedMsg] = useState('');
  const [processing, setProcessing] = useState(false);
  const [processMsg, setProcessMsg] = useState('');
  const [negotiatePrefill, setNegotiatePrefill] = useState('');

  const loadTree = useCallback(() => {
    setTreeLoading(true);
    svc.getTree().then(r => setTree(r.data.tree || [])).catch(() => setTree([])).finally(() => setTreeLoading(false));
  }, []);

  useEffect(() => { loadTree(); }, [loadTree]);

  const handleSeed = async () => {
    setSeeding(true); setSeedMsg('');
    try { const r = await svc.seedTaxonomy(); setSeedMsg(r.data.message); loadTree(); }
    catch { setSeedMsg('Seed failed — check server logs'); }
    finally { setSeeding(false); }
  };

  const handleProcessAll = async () => {
    setProcessing(true); setProcessMsg('');
    try { const r = await svc.processAll(); setProcessMsg(r.data.message); loadTree(); }
    catch (e) { setProcessMsg(e?.response?.data?.error || 'Processing failed'); }
    finally { setProcessing(false); }
  };

  // Compute tree stats
  const totalClauses = useMemo(() => tree.reduce((a, n) => a + (n.count || 0), 0), [tree]);

  return (
    <div style={{ minHeight: '100vh', background: '#030712', color: '#f1f5f9', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.15); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(148,163,184,0.25); }
      `}</style>

      {/* ── Header ── */}
      <div style={{
        borderBottom: '1px solid rgba(148,163,184,0.06)',
        padding: '16px 24px 0',
        background: 'linear-gradient(180deg, rgba(139,92,246,0.04) 0%, transparent 100%)',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
          {/* Title */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 12, flexShrink: 0,
              background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 20px rgba(124,58,237,0.4)',
            }}>
              <BookOpen size={20} style={{ color: '#fff' }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h1 style={{ fontSize: 18, fontWeight: 800, background: 'linear-gradient(90deg, #e2e8f0 0%, #a78bfa 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  Advanced Clause Library
                </h1>
                {tree.length > 0 && (
                  <span style={{ fontSize: 11, padding: '2px 9px', borderRadius: 10, background: 'rgba(139,92,246,0.12)', color: '#a78bfa', fontWeight: 600 }}>
                    {tree.length} categories · {totalClauses.toLocaleString()} clauses
                  </span>
                )}
              </div>
              <p style={{ fontSize: 11.5, color: '#475569', marginTop: 2 }}>
                Self-learning ontology · AI-powered search · Pattern discovery · Clause Negotiation AI
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {seedMsg && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: '#10b981', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '5px 10px' }}>
                <CheckCircle size={11} /> {seedMsg}
              </span>
            )}
            {processMsg && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: '#60a5fa', background: 'rgba(96,165,250,0.08)', border: '1px solid rgba(96,165,250,0.2)', borderRadius: 8, padding: '5px 10px' }}>
                <CheckCircle size={11} /> {processMsg}
              </span>
            )}
            <button onClick={loadTree} style={{ padding: 8, borderRadius: 8, background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.08)', color: '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', transition: 'all 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.color = '#f1f5f9'}
              onMouseLeave={e => e.currentTarget.style.color = '#64748b'}
              title="Refresh tree">
              <RefreshCw size={14} />
            </button>
            <button onClick={handleProcessAll} disabled={processing} style={{
              display: 'flex', alignItems: 'center', gap: 7, padding: '7px 14px', borderRadius: 9, fontSize: 12.5, fontWeight: 600, cursor: processing ? 'not-allowed' : 'pointer',
              background: processing ? 'rgba(16,185,129,0.2)' : 'linear-gradient(135deg, #059669, #10b981)',
              color: '#fff', border: 'none',
              boxShadow: !processing ? '0 4px 14px rgba(16,185,129,0.3)' : 'none',
              opacity: processing ? 0.7 : 1, transition: 'all 0.2s',
            }}>
              {processing ? <Loader size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Zap size={13} />}
              {processing ? 'Processing…' : 'Process All Contracts'}
            </button>
            <button onClick={handleSeed} disabled={seeding} style={{
              display: 'flex', alignItems: 'center', gap: 7, padding: '7px 14px', borderRadius: 9, fontSize: 12.5, fontWeight: 600, cursor: seeding ? 'not-allowed' : 'pointer',
              background: seeding ? 'rgba(99,102,241,0.2)' : 'linear-gradient(135deg, #4f46e5, #6366f1)',
              color: '#fff', border: 'none',
              boxShadow: !seeding ? '0 4px 14px rgba(99,102,241,0.3)' : 'none',
              opacity: seeding ? 0.7 : 1, transition: 'all 0.2s',
            }}>
              {seeding ? <Loader size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Database size={13} />}
              Seed Taxonomy
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 2, overflowX: 'auto', paddingBottom: 1 }}>
          {TABS.map(t => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                display: 'flex', alignItems: 'center', gap: 7, padding: '9px 16px',
                fontSize: 12.5, fontWeight: active ? 600 : 400, cursor: 'pointer', whiteSpace: 'nowrap',
                borderRadius: '10px 10px 0 0',
                background: active ? 'rgba(139,92,246,0.1)' : 'transparent',
                color: active ? '#c4b5fd' : '#64748b',
                border: active ? '1px solid rgba(139,92,246,0.2)' : '1px solid transparent',
                borderBottom: active ? '2px solid #8b5cf6' : '2px solid transparent',
                transition: 'all 0.18s ease',
                boxShadow: active ? '0 -4px 14px rgba(139,92,246,0.08)' : 'none',
              }}>
                <Icon size={13} />
                {t.label}
                {t.badge && (
                  <span style={{ fontSize: 9, fontWeight: 800, padding: '1px 5px', borderRadius: 6, background: 'linear-gradient(135deg, #7c3aed, #4f46e5)', color: '#fff', letterSpacing: '0.04em' }}>
                    {t.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Body ── */}
      <div style={{ padding: '20px 24px' }}>
        {/* Taxonomy Explorer */}
        {activeTab === 'explorer' && (
          <div style={{ display: 'flex', gap: 14, minHeight: 580 }}>
            {/* Left: Tree */}
            <div style={{
              width: 280, flexShrink: 0,
              background: 'rgba(15,23,42,0.7)', backdropFilter: 'blur(8px)',
              border: '1px solid rgba(148,163,184,0.07)',
              borderRadius: 14, overflow: 'hidden', display: 'flex', flexDirection: 'column',
            }}>
              <div style={{ padding: '12px 14px', borderBottom: '1px solid rgba(148,163,184,0.06)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 24, height: 24, borderRadius: 6, background: 'rgba(139,92,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <GitBranch size={12} style={{ color: '#8b5cf6' }} />
                </div>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8' }}>Clause Ontology</span>
                {tree.length > 0 && (
                  <span style={{ marginLeft: 'auto', fontSize: 10, color: '#334155', fontWeight: 600 }}>
                    {tree.length} roots
                  </span>
                )}
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: '8px 6px' }}>
                {treeLoading && (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
                    <div style={{ width: 20, height: 20, borderRadius: '50%', border: '2px solid rgba(139,92,246,0.3)', borderTop: '2px solid #8b5cf6', animation: 'spin 0.8s linear infinite' }} />
                  </div>
                )}
                {!treeLoading && tree.length === 0 && (
                  <div style={{ padding: '32px 12px', textAlign: 'center' }}>
                    <Database size={24} style={{ color: '#1e293b', margin: '0 auto 8px' }} />
                    <p style={{ fontSize: 12, color: '#334155' }}>No categories yet</p>
                    <p style={{ fontSize: 11, color: '#1e293b', marginTop: 4 }}>Click "Seed Taxonomy" to start</p>
                  </div>
                )}
                {!treeLoading && tree.map(n => (
                  <TreeNode key={n.id} node={n} onSelect={setSelectedNode} selected={selectedNode} depth={0} />
                ))}
              </div>
            </div>

            {/* Right: Insights */}
            <div style={{
              flex: 1,
              background: 'rgba(15,23,42,0.7)', backdropFilter: 'blur(8px)',
              border: '1px solid rgba(148,163,184,0.07)',
              borderRadius: 14, overflow: 'hidden', display: 'flex', flexDirection: 'column',
            }}>
              <ClauseInsightsPanel node={selectedNode} />
            </div>
          </div>
        )}

        {activeTab === 'search' && <SearchTab />}
        {activeTab === 'negotiate' && <NegotiateTab prefillText={negotiatePrefill} onPrefillUsed={() => setNegotiatePrefill('')} />}
        {activeTab === 'analytics' && <AnalyticsTab />}
        {activeTab === 'graph' && <GraphTab onNegotiate={text => { setNegotiatePrefill(text); setActiveTab('negotiate'); }} />}
        {activeTab === 'howto' && <HowItWorksTab />}
      </div>
    </div>
  );
}
