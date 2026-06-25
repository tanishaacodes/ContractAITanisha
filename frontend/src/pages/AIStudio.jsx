import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  BarChart, Bar, Cell,
} from 'recharts';
import {
  generateRedlines,
  acceptRedline,
  startNegotiation,
  startAdvancedNegotiation,
  evaluateNegotiationOutcome,
  runCFOSimulation,
  simulateContract,
  getRiskInsights,
  runScenarioAnalysis,
  analyzeLegalClause,
  fetchContracts,
} from '../services/aiStudioService';

// Inject styles
if (typeof document !== 'undefined' && !document.getElementById('ai-studio-styles')) {
  const style = document.createElement('style');
  style.id = 'ai-studio-styles';
  style.textContent = `
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes tabEnter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes glowPulse { 0%, 100% { box-shadow: 0 0 20px rgba(6,182,212,0.3); } 50% { box-shadow: 0 0 40px rgba(6,182,212,0.6); } }
    @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
    @keyframes float { 0%,100% { transform: translateY(0) rotate(0deg); opacity:0.15; } 50% { transform: translateY(-15px) rotate(180deg); opacity:0.25; } }
  `;
  document.head.appendChild(style);
}

const TABS = [
  { id: 'redlining', label: '✏️ Redlining AI' },
  { id: 'negotiation', label: '🤝 Negotiation Agents' },
  { id: 'cfo', label: '📊 CFO Simulator' },
  { id: 'legal', label: '⚖️ Legal Reasoning' },
];

const RISK_COLOR = (score) => {
  if (score > 0.7) return 'text-red-400';
  if (score > 0.4) return 'text-yellow-400';
  return 'text-emerald-400';
};

const RISK_BG = (score) => {
  if (score > 0.7) return 'bg-red-500/20 border-red-500/40 text-red-300';
  if (score > 0.4) return 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300';
  return 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300';
};

const CHANGE_TYPE_COLOR = {
  major: 'bg-red-500/20 text-red-300 border border-red-500/30',
  moderate: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
  minor: 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
};

const AGENT_COLORS = {
  Buyer: { bg: 'bg-blue-600', text: 'text-blue-200', border: 'border-blue-500/40', glow: 'rgba(59,130,246,0.3)' },
  Supplier: { bg: 'bg-emerald-600', text: 'text-emerald-200', border: 'border-emerald-500/40', glow: 'rgba(16,185,129,0.3)' },
  Legal: { bg: 'bg-purple-600', text: 'text-purple-200', border: 'border-purple-500/40', glow: 'rgba(139,92,246,0.3)' },
  CFO: { bg: 'bg-orange-600', text: 'text-orange-200', border: 'border-orange-500/40', glow: 'rgba(249,115,22,0.3)' },
};

// ─── Reusable Components ───────────────────────────────────────────

const glassCard = {
  background: 'rgba(13, 17, 23, 0.8)',
  border: '1px solid rgba(99, 102, 241, 0.15)',
  backdropFilter: 'blur(20px)',
};

const TabBar = ({ activeTab, onTabChange }) => (
  <div className="flex gap-2 p-1.5 mb-6" style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)', borderRadius: 16 }}>
    {TABS.map((tab) => (
      <button
        key={tab.id}
        onClick={() => onTabChange(tab.id)}
        className="flex-1 py-2 px-3 rounded-xl text-sm font-semibold transition-all duration-200"
        style={
          activeTab === tab.id
            ? { background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', color: '#fff', boxShadow: '0 0 20px rgba(6,182,212,0.35)' }
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
    className={`rounded-2xl p-5 transition-all duration-300 ${className}`}
    style={{ ...glassCard, ...style, animation: 'fadeInUp 0.3s ease-out' }}
    onMouseEnter={(e) => { e.currentTarget.style.border = '1px solid rgba(99,102,241,0.4)'; e.currentTarget.style.boxShadow = '0 0 30px rgba(99,102,241,0.1), inset 0 1px 0 rgba(255,255,255,0.03)'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
    onMouseLeave={(e) => { e.currentTarget.style.border = '1px solid rgba(99,102,241,0.15)'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none'; }}
  >
    {children}
  </div>
);

const Skeleton = ({ className = '', style = {} }) => (
  <div
    className={`rounded-xl ${className}`}
    style={{
      background: 'linear-gradient(90deg, rgba(99,102,241,0.05) 25%, rgba(99,102,241,0.1) 50%, rgba(99,102,241,0.05) 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
      border: '1px solid rgba(99,102,241,0.08)',
      ...style,
    }}
  />
);

const Button = ({ onClick, disabled, loading, children, variant = 'primary', className = '' }) => {
  const base = 'px-4 py-2 rounded-xl font-semibold transition-all duration-200 flex items-center gap-2 text-sm disabled:opacity-50';
  const variants = {
    primary: { background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', color: '#fff', boxShadow: '0 0 16px rgba(6,182,212,0.25)' },
    success: { background: 'linear-gradient(135deg, #059669, #10b981)', color: '#fff' },
    danger: { background: 'linear-gradient(135deg, #dc2626, #ef4444)', color: '#fff' },
    outline: { background: 'transparent', border: '1px solid rgba(99,102,241,0.3)', color: '#9ca3af' },
    cyan: { background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.3)', color: '#06b6d4' },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${className}`}
      style={variants[variant] || variants.primary}
    >
      {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
      {children}
    </button>
  );
};

const ContractSelector = ({ contracts, value, onChange, placeholder = 'Select a contract' }) => (
  <select
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="w-full rounded-xl px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
    style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }}
  >
    <option value="">{placeholder}</option>
    {contracts.map((c) => (
      <option key={c.id} value={c.id}>
        {c.original_filename || c.filename || c.id}
      </option>
    ))}
  </select>
);

const KPICard = ({ label, value, suffix = '', colorClass = 'text-cyan-400', icon = '', trend }) => (
  <div className="rounded-2xl p-4 text-center transition-all duration-200" style={{ background: 'rgba(13,17,23,0.9)', border: '1px solid rgba(99,102,241,0.15)' }}>
    {icon && <div className="text-xl mb-1">{icon}</div>}
    <div className={`text-2xl font-black ${colorClass}`} style={{ textShadow: '0 0 16px currentColor' }}>
      {value}{suffix}
    </div>
    {trend && <div className={`text-xs mt-0.5 ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>{trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%</div>}
    <div className="text-xs text-gray-500 mt-1">{label}</div>
  </div>
);

const inputStyle = { background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' };
const inputClass = "w-full rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all";

// ─── Word-level Diff Highlighting ──────────────────────────────────

function diffWords(original, suggested) {
  const origWords = original.split(/\s+/);
  const suggWords = suggested.split(/\s+/);
  const origSet = new Set(origWords);
  const suggSet = new Set(suggWords);

  const origResult = origWords.map((word) => ({
    word,
    deleted: !suggSet.has(word),
  }));
  const suggResult = suggWords.map((word) => ({
    word,
    added: !origSet.has(word),
  }));
  return { origResult, suggResult };
}

const DiffText = ({ words, type }) => (
  <span>
    {words.map((item, i) =>
      item.deleted ? (
        <span key={i} className="bg-red-500/30 text-red-300 line-through mx-0.5">{item.word}</span>
      ) : item.added ? (
        <span key={i} className="bg-emerald-500/30 text-emerald-300 mx-0.5">{item.word}</span>
      ) : (
        <span key={i} className="mx-0.5">{item.word}</span>
      )
    )}
  </span>
);

// ─── Simulate Impact Modal ──────────────────────────────────────

const SimulateImpactModal = ({ redline, onClose }) => {
  if (!redline) return null;
  const riskReduction = Math.max(5, Math.round(redline.risk_score * 100) - Math.round(redline.risk_score * 60));
  const savingsEstimate = Math.round(redline.risk_score * 180000 + 20000);
  const newRisk = Math.max(5, Math.round(redline.risk_score * 100) - riskReduction);

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }} onClick={onClose}>
      <div className="rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl" style={{ background: 'rgba(13,17,23,0.95)', border: '1px solid rgba(6,182,212,0.3)', boxShadow: '0 0 40px rgba(6,182,212,0.15)' }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-white font-bold text-lg">⚡ Simulated Impact</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl leading-none transition-colors">×</button>
        </div>
        <div className="space-y-4">
          <div className="p-4 rounded-xl" style={{ background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.2)' }}>
            <p className="text-sm text-cyan-300 font-semibold mb-3">Accepting this redline:</p>
            <div className="grid grid-cols-2 gap-3 text-center">
              <div>
                <div className="text-xs text-gray-500 mb-1">Risk Score Change</div>
                <div className="text-sm font-bold">
                  <span className="text-red-400">{Math.round(redline.risk_score * 100)}%</span>
                  <span className="text-gray-500 mx-2">→</span>
                  <span className="text-emerald-400">{newRisk}%</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Risk Reduction</div>
                <div className="text-sm font-black text-emerald-400">−{riskReduction} pts</div>
              </div>
            </div>
          </div>
          <div className="p-4 rounded-xl" style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)' }}>
            <p className="text-xs text-gray-500 mb-1">Estimated Financial Impact</p>
            <p className="text-2xl font-black text-emerald-400" style={{ textShadow: '0 0 20px rgba(16,185,129,0.4)' }}>
              Saves ~${savingsEstimate.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">in reduced liability exposure over contract term</p>
          </div>
          <div className="text-xs text-gray-600 p-3 rounded-xl" style={{ background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.1)' }}>
            Clause Type: {redline.clause_type} • Change Type: {redline.change_type}
          </div>
        </div>
        <button
          onClick={onClose}
          className="mt-4 w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all"
          style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 16px rgba(6,182,212,0.2)' }}
        >
          Close
        </button>
      </div>
    </div>
  );
};

// ─── Tab 1: Redlining AI ──────────────────────────────────────────

const RedliningTab = ({ contracts }) => {
  const [contractId, setContractId] = useState('');
  const [jurisdiction, setJurisdiction] = useState('india');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [redlineStatuses, setRedlineStatuses] = useState({});
  const [showDiff, setShowDiff] = useState({});
  const [simulateTarget, setSimulateTarget] = useState(null);

  const handleGenerate = async () => {
    if (!contractId) { setError('Please select a contract first.'); return; }
    setLoading(true);
    setError('');
    try {
      const data = await generateRedlines(contractId, jurisdiction);
      setResult(data);
      const statuses = {};
      data.redlines.forEach((r) => { statuses[r.id] = r.status; });
      setRedlineStatuses(statuses);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to generate redlines. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (redlineId, action) => {
    setRedlineStatuses((prev) => ({ ...prev, [redlineId]: action }));
    try {
      await acceptRedline(redlineId, action);
    } catch {
      // Status update is optimistic; silently handle error
    }
  };

  const toggleDiff = (id) => setShowDiff((prev) => ({ ...prev, [id]: !prev[id] }));

  return (
    <div className="space-y-5">
      {simulateTarget && (
        <SimulateImpactModal redline={simulateTarget} onClose={() => setSimulateTarget(null)} />
      )}

      <Card>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">✏️</span>
          <h3 className="text-white font-bold text-lg">Autonomous Redlining AI</h3>
        </div>
        <p className="text-gray-400 text-sm mb-5 ml-7">
          Select a contract and jurisdiction to automatically analyze clauses using AI. The system identifies
          risks, suggests jurisdiction-aware rewrites, and classifies each change.
        </p>
        <div className="flex gap-3 items-end flex-wrap mb-4">
          <div className="flex-1 min-w-48">
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract</label>
            <ContractSelector contracts={contracts} value={contractId} onChange={setContractId} />
          </div>
          <div className="w-52">
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Jurisdiction</label>
            <div className="flex gap-2">
              {[
                { value: 'india', flag: '🇮🇳', label: 'India' },
                { value: 'us', flag: '🇺🇸', label: 'US' },
                { value: 'uk', flag: '🇬🇧', label: 'UK' },
              ].map((j) => (
                <button
                  key={j.value}
                  onClick={() => setJurisdiction(j.value)}
                  className="flex-1 py-2 px-2 rounded-xl text-xs font-semibold transition-all duration-200"
                  style={
                    jurisdiction === j.value
                      ? { background: 'rgba(6,182,212,0.15)', border: '1px solid rgba(6,182,212,0.4)', color: '#06b6d4' }
                      : { background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.15)', color: '#6b7280' }
                  }
                >
                  {j.flag} {j.label}
                </button>
              ))}
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading || !contractId}
            className="px-6 py-2 rounded-xl font-semibold text-white text-sm flex items-center gap-2 transition-all disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 20px rgba(6,182,212,0.25)' }}
          >
            {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
            ⚡ {loading ? 'Analyzing…' : 'Generate Redlines'}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </Card>

      {result && (
        <Card>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h4 className="text-white font-bold text-lg">{result.total_clauses_analyzed} Clauses Analyzed</h4>
              <p className="text-gray-500 text-xs mt-0.5">{new Date(result.generated_at).toLocaleString()}</p>
            </div>
            <div className="flex gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-semibold" style={{ background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.25)', color: '#06b6d4' }}>
                {result.redlines?.length} redlines
              </span>
            </div>
          </div>
          <div className="space-y-4">
            {result.redlines.map((redline) => {
              const diff = showDiff[redline.id]
                ? diffWords(redline.original_clause, redline.suggested_clause)
                : null;
              const riskPct = Math.round(redline.risk_score * 100);
              return (
                <div key={redline.id} className="rounded-2xl p-4 transition-all duration-200"
                  style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.12)' }}>
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-3 flex-wrap">
                    <span className="text-sm font-bold text-white">{redline.clause_name || 'Unnamed Clause'}</span>
                    {redline.clause_type && (
                      <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                        {redline.clause_type}
                      </span>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded-full ${CHANGE_TYPE_COLOR[redline.change_type] || CHANGE_TYPE_COLOR.minor}`}>
                      {redline.change_type}
                    </span>
                    <span className={`ml-auto text-xs px-2.5 py-1 rounded-full border font-bold ${RISK_BG(redline.risk_score)}`}>
                      Risk {riskPct}%
                    </span>
                  </div>

                  {/* Diff toggle */}
                  <div className="flex gap-2 mb-3">
                    <button
                      onClick={() => toggleDiff(redline.id)}
                      className="text-xs px-3 py-1.5 rounded-lg transition-colors font-medium"
                      style={showDiff[redline.id]
                        ? { background: 'rgba(6,182,212,0.15)', border: '1px solid rgba(6,182,212,0.35)', color: '#06b6d4' }
                        : { background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)', color: '#6b7280' }
                      }
                    >
                      {showDiff[redline.id] ? '👁 Word Diff ON' : '👁 Show Diff'}
                    </button>
                    <button
                      onClick={() => setSimulateTarget(redline)}
                      className="text-xs px-3 py-1.5 rounded-lg font-medium transition-colors"
                      style={{ background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.25)', color: '#fbbf24' }}
                    >
                      ⚡ Simulate Impact
                    </button>
                  </div>

                  {showDiff[redline.id] && diff ? (
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div>
                        <p className="text-xs text-gray-600 mb-1.5 font-medium uppercase tracking-wider">Original</p>
                        <div className="rounded-xl p-3 text-xs text-gray-300 leading-relaxed max-h-28 overflow-y-auto"
                          style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.15)' }}>
                          <DiffText words={diff.origResult} type="original" />
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1.5 font-medium uppercase tracking-wider">Suggested</p>
                        <div className="rounded-xl p-3 text-xs text-gray-300 leading-relaxed max-h-28 overflow-y-auto"
                          style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.15)' }}>
                          <DiffText words={diff.suggResult} type="suggested" />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div>
                        <p className="text-xs text-gray-600 mb-1.5 font-medium uppercase tracking-wider">Original</p>
                        <div className="rounded-xl p-3 text-xs text-gray-300 leading-relaxed max-h-28 overflow-y-auto"
                          style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.12)' }}>
                          {redline.original_clause}
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1.5 font-medium uppercase tracking-wider">Suggested</p>
                        <div className="rounded-xl p-3 text-xs text-gray-300 leading-relaxed max-h-28 overflow-y-auto"
                          style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.12)' }}>
                          {redline.suggested_clause}
                        </div>
                      </div>
                    </div>
                  )}

                  {redline.explanation && (
                    <p className="text-xs text-gray-400 mb-3 italic leading-relaxed">{redline.explanation}</p>
                  )}

                  <div className="flex gap-2">
                    {redlineStatuses[redline.id] === 'pending' ? (
                      <>
                        <button
                          className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white transition-all"
                          style={{ background: 'linear-gradient(135deg, #059669, #10b981)', boxShadow: '0 0 10px rgba(16,185,129,0.2)' }}
                          onClick={() => handleAction(redline.id, 'accepted')}
                        >
                          ✓ Accept
                        </button>
                        <button
                          className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white transition-all"
                          style={{ background: 'linear-gradient(135deg, #dc2626, #ef4444)' }}
                          onClick={() => handleAction(redline.id, 'rejected')}
                        >
                          ✗ Reject
                        </button>
                      </>
                    ) : (
                      <span
                        className={`text-xs px-3 py-1.5 rounded-xl font-bold ${
                          redlineStatuses[redline.id] === 'accepted'
                            ? 'text-emerald-300'
                            : 'text-red-300'
                        }`}
                        style={{
                          background: redlineStatuses[redline.id] === 'accepted' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                          border: `1px solid ${redlineStatuses[redline.id] === 'accepted' ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
                        }}
                      >
                        {redlineStatuses[redline.id] === 'accepted' ? '✓ Accepted' : '✗ Rejected'}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
};

// ─── Tab 2: Advanced Multi-Agent Negotiation Engine ──────────────────

const SCORE_COLORS = {
  composite: '#a78bfa',
  risk:      '#f87171',
  financial: '#34d399',
  compliance:'#60a5fa',
  balance:   '#fbbf24',
};

const ScoreBar = ({ label, value, color }) => (
  <div className="flex items-center gap-2 mb-1.5">
    <span className="text-xs text-gray-500 w-20 flex-shrink-0">{label}</span>
    <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
      <div className="h-1.5 rounded-full transition-all" style={{ width: `${Math.round((value || 0) * 100)}%`, background: color }} />
    </div>
    <span className="text-xs font-mono w-9 text-right" style={{ color }}>{Math.round((value || 0) * 100)}%</span>
  </div>
);

const AgentCard = ({ resp, roundScore }) => {
  const [expanded, setExpanded] = useState(false);
  const colors = AGENT_COLORS[resp.agent_name] || AGENT_COLORS.Buyer;
  const emojis = { Buyer: '🛒', Supplier: '🏭', Legal: '⚖️', CFO: '💰' };

  return (
    <div className="rounded-2xl p-3 mb-2" style={{ background: 'rgba(13,17,23,0.55)', border: `1px solid ${colors.glow}` }}>
      <div className="flex items-start gap-2">
        <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-black text-white ${colors.bg}`}
          style={{ boxShadow: `0 0 12px ${colors.glow}` }}>
          {emojis[resp.agent_name] || resp.agent_name[0]}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full text-white ${colors.bg}`}>{resp.agent_name}</span>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.12)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.2)' }}>
              Round {resp.round}
            </span>
            {roundScore !== undefined && (
              <span className="ml-auto text-xs font-mono" style={{ color: SCORE_COLORS.composite }}>
                score {Math.round(roundScore * 100)}%
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400 leading-relaxed mb-2">{resp.justification}</p>

          {/* Mini score bars */}
          <div className="mb-2">
            <ScoreBar label="Risk↓"     value={resp.risk_impact}      color={SCORE_COLORS.risk} />
            <ScoreBar label="Financial" value={(resp.financial_impact + 1) / 2} color={SCORE_COLORS.financial} />
            <ScoreBar label="Comply"    value={resp.compliance_score}  color={SCORE_COLORS.compliance} />
          </div>

          <button
            onClick={() => setExpanded(e => !e)}
            className="text-xs underline transition-colors"
            style={{ color: colors.glow }}
          >
            {expanded ? 'Hide proposal' : 'View proposed clause'}
          </button>
          {expanded && (
            <div className="mt-2 p-2 rounded-xl text-xs text-gray-300 leading-relaxed"
              style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)' }}>
              {resp.proposed_clause}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const NegotiationTab = ({ contracts }) => {
  const [contractId,    setContractId]    = useState('');
  const [clauseText,    setClauseText]    = useState('');
  const [rounds,        setRounds]        = useState(3);
  const [loading,       setLoading]       = useState(false);
  const [result,        setResult]        = useState(null);
  const [error,         setError]         = useState('');
  const [activeRound,   setActiveRound]   = useState(1);
  const [showOutcome,   setShowOutcome]   = useState(false);
  const [outcomeSubmit, setOutcomeSubmit] = useState({ deal_outcome: 'SUCCESS', profit_margin: 15, delay_days: 0, dispute_count: 0 });
  const [rlResult,      setRlResult]      = useState(null);

  const handleNegotiate = async () => {
    if (!clauseText.trim()) { setError('Please enter clause text.'); return; }
    setLoading(true); setError(''); setResult(null); setRlResult(null);
    try {
      const data = await startAdvancedNegotiation({ clauseText, contractId, rounds });
      setResult(data);
      setActiveRound(data.rounds_completed || 1);
    } catch (err) {
      setError(err?.response?.data?.error || 'Negotiation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateOutcome = async () => {
    if (!result?.session_id) return;
    try {
      const r = await evaluateNegotiationOutcome({
        sessionId:     result.session_id,
        dealOutcome:   outcomeSubmit.deal_outcome,
        profitMargin:  outcomeSubmit.profit_margin,
        delayDays:     outcomeSubmit.delay_days,
        disputeCount:  outcomeSubmit.dispute_count,
      });
      setRlResult(r);
      setShowOutcome(false);
    } catch (err) {
      setError('Outcome evaluation failed.');
    }
  };

  const roundResponses = result
    ? result.agent_responses.filter(r => r.round === activeRound)
    : [];
  const scoreMap = result
    ? Object.fromEntries((result.round_scores || []).map(s => [s.round, s]))
    : {};
  const trendColor = { improving: '#34d399', stable: '#a78bfa', degrading: '#f87171' };

  return (
    <div className="space-y-5">
      {/* ── Input Card ─────────────────────────────────────────────── */}
      <Card>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xl">🤝</span>
          <h3 className="text-white font-bold text-lg">Multi-Agent Negotiation</h3>
          <span className="ml-auto text-xs px-2 py-1 rounded-full font-semibold"
            style={{ background: 'rgba(167,139,250,0.12)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.25)' }}>
            Engine v2 · Memory · RL
          </span>
        </div>
        <p className="text-gray-400 text-sm mb-5 ml-7">
          Four AI agents (Buyer, Supplier, Legal, CFO) negotiate over multiple rounds with scoring,
          clause evolution, convergence detection, and RL strategy adaptation.
        </p>

        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract (optional)</label>
            <ContractSelector contracts={contracts} value={contractId} onChange={setContractId} />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1.5 block font-medium">Negotiation Rounds</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((r) => (
                <button key={r} onClick={() => setRounds(r)}
                  className="flex-1 py-2 rounded-xl text-xs font-bold transition-all"
                  style={rounds === r
                    ? { background: 'linear-gradient(135deg,#7c3aed,#06b6d4)', color: '#fff', boxShadow: '0 0 12px rgba(6,182,212,0.3)' }
                    : { background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.15)', color: '#6b7280' }
                  }>{r}</button>
              ))}
            </div>
          </div>
        </div>

        <div className="mb-3">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs text-gray-400 font-medium">Clause Text *</label>
            <span className="text-xs text-gray-600">{clauseText.length} chars</span>
          </div>
          <textarea rows={4} value={clauseText} onChange={e => setClauseText(e.target.value)}
            placeholder="Paste the contract clause you want to negotiate…"
            className="w-full rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none transition-all"
            style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }} />
        </div>

        <div className="flex gap-2 mb-4 flex-wrap">
          {[
            { name: 'Buyer', emoji: '🛒' }, { name: 'Supplier', emoji: '🏭' },
            { name: 'Legal', emoji: '⚖️' }, { name: 'CFO', emoji: '💰' },
          ].map(({ name, emoji }) => (
            <div key={name}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ${AGENT_COLORS[name].bg} text-white`}
              style={{ boxShadow: `0 0 10px ${AGENT_COLORS[name].glow}` }}>
              <span className="w-2 h-2 rounded-full bg-white/40 animate-pulse" />
              {emoji} {name}
            </div>
          ))}
        </div>

        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

        <button onClick={handleNegotiate} disabled={loading || !clauseText.trim()}
          className="px-6 py-2.5 rounded-xl font-semibold text-white text-sm flex items-center gap-2 transition-all disabled:opacity-50"
          style={{ background: 'linear-gradient(135deg,#7c3aed,#06b6d4)', boxShadow: '0 0 20px rgba(6,182,212,0.25)' }}>
          {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
          🤝 {loading ? `Running engine (${rounds} rounds × 4 agents)…` : 'Start Negotiation'}
        </button>
      </Card>

      {result && (
        <>
          {/* ── Summary KPIs ───────────────────────────────────────── */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Final Score',  value: `${Math.round(result.final_score * 100)}%`,      color: '#a78bfa' },
              { label: 'Rounds Run',   value: result.rounds_completed,                          color: '#60a5fa' },
              { label: 'Best Round',   value: `Round ${result.best_round}`,                     color: '#34d399' },
              { label: 'Trend',        value: result.score_trend,                               color: trendColor[result.score_trend] || '#a78bfa' },
            ].map(({ label, value, color }) => (
              <div key={label} className="rounded-2xl p-3 text-center" style={glassCard}>
                <p className="text-xs text-gray-500 mb-1">{label}</p>
                <p className="text-lg font-bold" style={{ color }}>{value}</p>
              </div>
            ))}
          </div>

          {/* ── Convergence / trend banner ──────────────────────────── */}
          {result.converged ? (
            <div className="p-4 rounded-2xl flex items-center gap-3"
              style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.25)' }}>
              <span className="text-2xl">✅</span>
              <div>
                <p className="text-emerald-300 font-bold">Agents converged at Round {result.convergence_round}</p>
                <p className="text-emerald-400/70 text-xs mt-0.5">{result.reasoning}</p>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-2xl flex items-center gap-3"
              style={{ background: 'rgba(234,179,8,0.05)', border: '1px solid rgba(234,179,8,0.25)' }}>
              <span className="text-2xl">⚠️</span>
              <div>
                <p className="text-yellow-300 font-bold">No convergence — manual review needed</p>
                <p className="text-yellow-400/70 text-xs mt-0.5">{result.reasoning}</p>
              </div>
            </div>
          )}

          {/* ── Score chart per round ───────────────────────────────── */}
          {result.round_scores && result.round_scores.length > 0 && (
            <Card>
              <h4 className="text-white font-bold mb-4">Score Evolution per Round</h4>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={result.round_scores} margin={{ top: 4, right: 16, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="round" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={v => `R${v}`} />
                  <YAxis domain={[0, 1]} tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={v => `${Math.round(v * 100)}%`} />
                  <Tooltip
                    contentStyle={{ background: 'rgba(13,17,23,0.95)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 12, fontSize: 12 }}
                    formatter={(v, name) => [`${Math.round(v * 100)}%`, name]}
                  />
                  <Line type="monotone" dataKey="composite_score" stroke={SCORE_COLORS.composite} strokeWidth={2.5} dot={{ r: 4, fill: SCORE_COLORS.composite }} name="Composite" />
                  <Line type="monotone" dataKey="financial_score"  stroke={SCORE_COLORS.financial}  strokeWidth={1.5} dot={false} name="Financial" strokeDasharray="4 2" />
                  <Line type="monotone" dataKey="compliance_score" stroke={SCORE_COLORS.compliance} strokeWidth={1.5} dot={false} name="Compliance" strokeDasharray="4 2" />
                  <Line type="monotone" dataKey="risk_score"       stroke={SCORE_COLORS.risk}       strokeWidth={1.5} dot={false} name="Risk↑" strokeDasharray="2 2" />
                </LineChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-2 justify-center flex-wrap">
                {[['Composite', SCORE_COLORS.composite], ['Financial', SCORE_COLORS.financial],
                  ['Compliance', SCORE_COLORS.compliance], ['Risk↑', SCORE_COLORS.risk]].map(([l, c]) => (
                  <span key={l} className="flex items-center gap-1 text-xs text-gray-400">
                    <span className="w-3 h-0.5 inline-block rounded" style={{ background: c }} />{l}
                  </span>
                ))}
              </div>
            </Card>
          )}

          {/* ── Round selector + agent cards ────────────────────────── */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-white font-bold">Agent Proposals by Round</h4>
              <div className="flex gap-1">
                {Array.from({ length: result.rounds_completed }, (_, i) => i + 1).map(r => (
                  <button key={r} onClick={() => setActiveRound(r)}
                    className="px-3 py-1 rounded-lg text-xs font-bold transition-all"
                    style={activeRound === r
                      ? { background: 'linear-gradient(135deg,#7c3aed,#06b6d4)', color: '#fff' }
                      : { background: 'rgba(99,102,241,0.1)', color: '#6b7280', border: '1px solid rgba(99,102,241,0.15)' }
                    }>R{r}</button>
                ))}
              </div>
            </div>

            {/* Round score summary */}
            {scoreMap[activeRound] && (
              <div className="mb-4 p-3 rounded-xl" style={{ background: 'rgba(167,139,250,0.06)', border: '1px solid rgba(167,139,250,0.15)' }}>
                <p className="text-xs text-gray-400 mb-2 font-medium">Round {activeRound} Score Breakdown</p>
                <ScoreBar label="Composite"  value={scoreMap[activeRound].composite_score} color={SCORE_COLORS.composite} />
                <ScoreBar label="Financial"  value={scoreMap[activeRound].financial_score}  color={SCORE_COLORS.financial} />
                <ScoreBar label="Compliance" value={scoreMap[activeRound].compliance_score} color={SCORE_COLORS.compliance} />
                <ScoreBar label="Balance"    value={scoreMap[activeRound].balance_score}    color={SCORE_COLORS.balance} />
                <ScoreBar label="Risk↑"      value={scoreMap[activeRound].risk_score}       color={SCORE_COLORS.risk} />
              </div>
            )}

            {/* Agent cards for selected round */}
            {roundResponses.length > 0 ? (
              roundResponses.map(resp => (
                <AgentCard key={resp.id} resp={resp} roundScore={scoreMap[resp.round]?.composite_score} />
              ))
            ) : (
              <p className="text-gray-500 text-sm text-center py-6">No data for Round {activeRound}</p>
            )}
          </Card>

          {/* ── Clause Evolution ────────────────────────────────────── */}
          {result.clause_history && result.clause_history.length > 1 && (
            <Card>
              <h4 className="text-white font-bold mb-4">Clause State Evolution</h4>
              <div className="space-y-2">
                {result.clause_history.map((cv, i) => (
                  <div key={cv.round} className="rounded-xl p-3"
                    style={{ background: i === result.clause_history.length - 1 ? 'rgba(167,139,250,0.06)' : 'rgba(13,17,23,0.4)', border: `1px solid ${i === result.clause_history.length - 1 ? 'rgba(167,139,250,0.25)' : 'rgba(255,255,255,0.05)'}` }}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs font-bold" style={{ color: i === result.clause_history.length - 1 ? '#a78bfa' : '#6b7280' }}>
                        {cv.round === 0 ? 'Original' : `Round ${cv.round}`}
                      </span>
                      {cv.changed_by !== 'Original' && (
                        <span className={`text-xs px-2 py-0.5 rounded-full text-white ${AGENT_COLORS[cv.changed_by]?.bg || 'bg-gray-600'}`}>
                          driven by {cv.changed_by}
                        </span>
                      )}
                      <span className="ml-auto text-xs text-gray-600">{cv.diff_summary}</span>
                      {i === result.clause_history.length - 1 && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
                          style={{ background: 'rgba(167,139,250,0.15)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.3)' }}>FINAL</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">{cv.clause_text}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ── Best / Optimised Clause ─────────────────────────────── */}
          <Card>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🏆</span>
              <h4 className="text-white font-bold">Optimised Clause (Best Round {result.best_round})</h4>
              <span className="ml-auto text-xs font-mono px-2 py-1 rounded-full"
                style={{ background: 'rgba(52,211,153,0.1)', color: '#34d399', border: '1px solid rgba(52,211,153,0.25)' }}>
                Score {Math.round(result.final_score * 100)}%
              </span>
            </div>
            <div className="p-4 rounded-2xl text-sm text-gray-200 leading-relaxed"
              style={{ background: 'rgba(13,17,23,0.7)', border: '1px solid rgba(167,139,250,0.2)', boxShadow: '0 0 30px rgba(167,139,250,0.05)' }}>
              {result.best_clause || result.final_clause}
            </div>
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => navigator.clipboard?.writeText(result.best_clause || result.final_clause)}
                className="text-xs px-3 py-1.5 rounded-lg transition-all"
                style={{ background: 'rgba(99,102,241,0.12)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.2)' }}>
                Copy Clause
              </button>
              {!showOutcome && (
                <button onClick={() => setShowOutcome(true)}
                  className="text-xs px-3 py-1.5 rounded-lg transition-all"
                  style={{ background: 'rgba(52,211,153,0.1)', color: '#34d399', border: '1px solid rgba(52,211,153,0.2)' }}>
                  Evaluate Outcome → RL Update
                </button>
              )}
            </div>
          </Card>

          {/* ── RL Outcome Evaluation ───────────────────────────────── */}
          {showOutcome && (
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">🧠</span>
                <h4 className="text-white font-bold">Outcome Feedback → RL Weight Update</h4>
              </div>
              <p className="text-gray-400 text-xs mb-4">
                Record the real-world deal outcome. The RL loop will update agent strategy weights
                for future negotiations based on this signal.
              </p>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Deal Outcome</label>
                  <select value={outcomeSubmit.deal_outcome}
                    onChange={e => setOutcomeSubmit(s => ({ ...s, deal_outcome: e.target.value }))}
                    className="w-full rounded-xl px-3 py-2 text-sm"
                    style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }}>
                    <option value="SUCCESS">SUCCESS</option>
                    <option value="PARTIAL">PARTIAL</option>
                    <option value="FAILURE">FAILURE</option>
                    <option value="ONGOING">ONGOING</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Profit Margin (%)</label>
                  <input type="number" value={outcomeSubmit.profit_margin} min={-100} max={100}
                    onChange={e => setOutcomeSubmit(s => ({ ...s, profit_margin: Number(e.target.value) }))}
                    className="w-full rounded-xl px-3 py-2 text-sm"
                    style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }} />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Delay Days</label>
                  <input type="number" value={outcomeSubmit.delay_days} min={0}
                    onChange={e => setOutcomeSubmit(s => ({ ...s, delay_days: Number(e.target.value) }))}
                    className="w-full rounded-xl px-3 py-2 text-sm"
                    style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }} />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Disputes</label>
                  <input type="number" value={outcomeSubmit.dispute_count} min={0}
                    onChange={e => setOutcomeSubmit(s => ({ ...s, dispute_count: Number(e.target.value) }))}
                    className="w-full rounded-xl px-3 py-2 text-sm"
                    style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }} />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={handleEvaluateOutcome}
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white"
                  style={{ background: 'linear-gradient(135deg,#7c3aed,#06b6d4)' }}>
                  Submit & Update Weights
                </button>
                <button onClick={() => setShowOutcome(false)}
                  className="px-4 py-2 rounded-xl text-sm text-gray-400"
                  style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
                  Cancel
                </button>
              </div>
            </Card>
          )}

          {/* ── RL Update Result ────────────────────────────────────── */}
          {rlResult && (
            <Card>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">✅</span>
                <h4 className="text-white font-bold">RL Weights Updated</h4>
                <span className="ml-auto text-xs text-gray-500">{rlResult.deal_outcome}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(rlResult.updated_weights || {}).map(([agent, weights]) => (
                  <div key={agent} className="rounded-xl p-3" style={{ background: 'rgba(13,17,23,0.5)', border: `1px solid ${AGENT_COLORS[agent]?.glow || 'rgba(255,255,255,0.08)'}` }}>
                    <p className={`text-xs font-bold mb-2 ${AGENT_COLORS[agent]?.text || 'text-gray-300'}`}>{agent}</p>
                    {Object.entries(weights).map(([k, v]) => (
                      <ScoreBar key={k} label={k.replace(/_/g, ' ')} value={v} color={AGENT_COLORS[agent]?.glow || '#a78bfa'} />
                    ))}
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

// ─── CFO Scenario Presets ─────────────────────────────────────────

const CFO_PRESETS = [
  { label: 'Base Case',     oil: 0,   inflation: 0,  fx: 0,  icon: '📊', color: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.25)', text: '#10b981' },
  { label: '💥 War',        oil: 35,  inflation: 18, fx: 12, icon: '💥', color: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.25)',  text: '#f87171' },
  { label: '🦠 Pandemic',   oil: -15, inflation: 10, fx: 8,  icon: '🦠', color: 'rgba(249,115,22,0.1)',  border: 'rgba(249,115,22,0.25)', text: '#fb923c' },
  { label: '🚢 Supply Chain', oil: 20, inflation: 15, fx: 8, icon: '🚢', color: 'rgba(234,179,8,0.1)',   border: 'rgba(234,179,8,0.25)',  text: '#fbbf24' },
];

const SEVERITY_STYLE = {
  CRITICAL: { bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.35)',   text: '#f87171', badge: 'bg-red-900/60 text-red-300' },
  HIGH:     { bg: 'rgba(245,158,11,0.10)',  border: 'rgba(245,158,11,0.30)',  text: '#fbbf24', badge: 'bg-yellow-900/60 text-yellow-300' },
  MEDIUM:   { bg: 'rgba(99,102,241,0.08)',  border: 'rgba(99,102,241,0.25)',  text: '#a5b4fc', badge: 'bg-indigo-900/60 text-indigo-300' },
  LOW:      { bg: 'rgba(16,185,129,0.08)',  border: 'rgba(16,185,129,0.25)', text: '#6ee7b7', badge: 'bg-emerald-900/60 text-emerald-300' },
};

const fmt = (v) => {
  const n = Number(v);
  if (isNaN(n)) return v;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
};

// ─── Tab 3: CFO Simulator (Enterprise) ───────────────────────────

const CFOSimTab = ({ contracts }) => {
  const [contractId, setContractId]         = useState('');
  const [oilShock, setOilShock]             = useState(10);
  const [inflation, setInflation]           = useState(5);
  const [fxShock, setFxShock]               = useState(8);
  const [activePreset, setActivePreset]     = useState(null);
  const [showAdvanced, setShowAdvanced]     = useState(false);
  const [activeResultTab, setActiveResultTab] = useState('kpis');

  // Advanced contract params
  const [contractValue, setContractValue]         = useState('');
  const [durationMonths, setDurationMonths]       = useState(12);
  const [paymentTermsDays, setPaymentTermsDays]   = useState(30);
  const [costBaseRatio, setCostBaseRatio]         = useState(70);
  const [delayProbability, setDelayProbability]   = useState(25);
  const [avgDelayDays, setAvgDelayDays]           = useState(30);
  const [penaltyRateDaily, setPenaltyRateDaily]   = useState(0.1);

  const [loading, setLoading]           = useState(false);
  const [loadingScenario, setLoadingScenario] = useState(false);
  const [result, setResult]             = useState(null);
  const [insights, setInsights]         = useState(null);
  const [scenarios, setScenarios]       = useState(null);
  const [error, setError]               = useState('');

  const applyPreset = (preset) => {
    setOilShock(Math.max(0, preset.oil));
    setInflation(Math.max(0, preset.inflation));
    setFxShock(Math.max(0, preset.fx));
    setActivePreset(preset.label);
  };

  const commonParams = () => ({
    contractId:        contractId || undefined,
    contractValue:     contractValue ? parseFloat(contractValue) : undefined,
    durationMonths,
    paymentTermsDays,
    costBaseRatio:     costBaseRatio / 100,
    delayProbability:  delayProbability / 100,
    avgDelayDays,
    penaltyRateDaily:  penaltyRateDaily / 1000,
    oilShock:          oilShock / 100,
    inflation:         inflation / 100,
    fxShock:           fxShock / 100,
  });

  const handleSimulate = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    setInsights(null);
    try {
      const params = commonParams();
      const [simData, insightData] = await Promise.all([
        simulateContract({ ...params, simulations: 2000 }),
        getRiskInsights({ ...params }),
      ]);
      setResult(simData);
      setInsights(insightData);
      setActiveResultTab('kpis');
    } catch (err) {
      setError(err?.response?.data?.error || 'Simulation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioAnalysis = async () => {
    setLoadingScenario(true);
    setError('');
    try {
      const params = commonParams();
      const data = await runScenarioAnalysis({
        contractId: params.contractId,
        contractValue: params.contractValue,
        durationMonths: params.durationMonths,
        costBaseRatio: params.costBaseRatio,
      });
      setScenarios(data.scenarios);
      setActiveResultTab('scenarios');
    } catch (err) {
      setError(err?.response?.data?.error || 'Scenario analysis failed.');
    } finally {
      setLoadingScenario(false);
    }
  };

  const SliderInput = ({ label, value, onChange, min = 0, max = 50, accentColor = '#06b6d4', emoji = '' }) => (
    <div>
      <div className="flex justify-between mb-1.5">
        <label className="text-xs text-gray-400 font-medium">{emoji} {label}</label>
        <span className="text-sm font-black" style={{ color: accentColor, textShadow: `0 0 10px ${accentColor}` }}>{value}%</span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 rounded-full appearance-none cursor-pointer"
        style={{ accentColor }}
      />
    </div>
  );

  const mc = result?.monte_carlo;

  return (
    <div className="space-y-5">
      {/* ── Input Panel ── */}
      <Card>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">📊</span>
            <h3 className="text-white font-bold text-lg">CFO Contract Intelligence Engine</h3>
          </div>
          <button
            onClick={() => setShowAdvanced(v => !v)}
            className="text-xs px-3 py-1 rounded-lg font-semibold transition-all"
            style={{ background: showAdvanced ? 'rgba(99,102,241,0.25)' : 'rgba(99,102,241,0.08)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.2)' }}
          >
            {showAdvanced ? '▲ Basic' : '▼ Advanced'}
          </button>
        </div>
        <p className="text-gray-400 text-sm mb-5 ml-7">
          Contract-aware Monte Carlo simulation with correlated macro shocks, time-series cashflow, penalty analysis, and AI-generated CFO insights.
        </p>

        {/* Quick Presets */}
        <div className="mb-5">
          <p className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wider">Quick Scenarios</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {CFO_PRESETS.map((p) => (
              <button key={p.label} onClick={() => applyPreset(p)}
                className="py-3 px-3 rounded-2xl text-xs font-bold transition-all duration-200 text-left"
                style={activePreset === p.label
                  ? { background: p.color, border: `1px solid ${p.border}`, color: p.text, boxShadow: `0 0 14px ${p.color}` }
                  : { background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)', color: '#6b7280' }}>
                <div className="text-lg mb-1">{p.icon}</div>
                <div style={{ color: activePreset === p.label ? p.text : '#9ca3af' }}>{p.label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Contract selector */}
        <div className="mb-4">
          <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract (optional)</label>
          <ContractSelector contracts={contracts} value={contractId} onChange={setContractId} />
        </div>

        {/* Macro sliders */}
        <div className="space-y-4 mb-5 p-4 rounded-2xl" style={{ background: 'rgba(99,102,241,0.03)', border: '1px solid rgba(99,102,241,0.08)' }}>
          <SliderInput label="Oil Shock"     value={oilShock}   onChange={(v) => { setOilShock(v);   setActivePreset(null); }} min={0} max={50} accentColor="#06b6d4" emoji="🛢️" />
          <SliderInput label="Inflation Rate" value={inflation}  onChange={(v) => { setInflation(v);  setActivePreset(null); }} min={0} max={30} accentColor="#eab308" emoji="📈" />
          <SliderInput label="FX Rate Shift"  value={fxShock}   onChange={(v) => { setFxShock(v);    setActivePreset(null); }} min={0} max={25} accentColor="#8b5cf6" emoji="💱" />
        </div>

        {/* Advanced contract params */}
        {showAdvanced && (
          <div className="mb-5 p-4 rounded-2xl space-y-4" style={{ background: 'rgba(6,182,212,0.03)', border: '1px solid rgba(6,182,212,0.1)' }}>
            <p className="text-xs text-cyan-400 font-semibold uppercase tracking-wider mb-3">Contract Structure Parameters</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { label: 'Contract Value ($)', value: contractValue, set: setContractValue, placeholder: 'e.g. 5000000', type: 'text' },
                { label: 'Duration (months)',   value: durationMonths,    set: (v) => setDurationMonths(Number(v)),    type: 'number', min: 1,  max: 60 },
                { label: 'Payment Terms (days)', value: paymentTermsDays, set: (v) => setPaymentTermsDays(Number(v)), type: 'number', min: 7,  max: 120 },
              ].map(({ label, value, set, placeholder, type, min, max }) => (
                <div key={label}>
                  <label className="text-xs text-gray-400 mb-1 block">{label}</label>
                  <input
                    type={type} value={value} onChange={(e) => set(e.target.value)}
                    placeholder={placeholder} min={min} max={max}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500"
                  />
                </div>
              ))}
            </div>
            <div className="space-y-3">
              <SliderInput label={`Cost Base Ratio: ${costBaseRatio}%`} value={costBaseRatio} onChange={setCostBaseRatio} min={30} max={95} accentColor="#10b981" emoji="💰" />
              <SliderInput label={`Delay Probability: ${delayProbability}%`} value={delayProbability} onChange={setDelayProbability} min={0} max={80} accentColor="#f59e0b" emoji="⏱️" />
              <SliderInput label={`Avg Delay Days: ${avgDelayDays}`}    value={avgDelayDays} onChange={setAvgDelayDays} min={5} max={120} accentColor="#ef4444" emoji="📅" />
              <SliderInput label={`Daily Penalty Rate: ${penaltyRateDaily}‰`} value={penaltyRateDaily} onChange={setPenaltyRateDaily} min={0} max={5} accentColor="#a855f7" emoji="⚡" />
            </div>
          </div>
        )}

        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

        <div className="flex gap-3 flex-wrap">
          <button onClick={handleSimulate} disabled={loading}
            className="px-6 py-2.5 rounded-xl font-semibold text-white text-sm flex items-center gap-2 disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 20px rgba(6,182,212,0.25)' }}>
            {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
            📊 {loading ? 'Simulating…' : 'Run Full Simulation'}
          </button>
          <button onClick={handleScenarioAnalysis} disabled={loadingScenario || loading}
            className="px-5 py-2.5 rounded-xl font-semibold text-sm flex items-center gap-2 disabled:opacity-50 transition-all"
            style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171' }}>
            {loadingScenario && <span className="w-4 h-4 border-2 border-red-400/30 border-t-red-400 rounded-full animate-spin" />}
            💥 {loadingScenario ? 'Analyzing…' : 'All Scenarios'}
          </button>
        </div>
      </Card>

      {/* ── Results ── */}
      {(result || scenarios) && (
        <>
          {/* Result tabs */}
          <div className="flex gap-2 flex-wrap">
            {[
              { id: 'kpis',      label: '📊 KPIs',             show: !!result },
              { id: 'cashflow',  label: '💵 Cashflow Timeline', show: !!result },
              { id: 'distribution', label: '📉 Distribution',  show: !!result },
              { id: 'insights',  label: '🧠 AI Insights',      show: !!insights },
              { id: 'scenarios', label: '💥 Scenarios',        show: !!scenarios },
            ].filter(t => t.show).map(t => (
              <button key={t.id} onClick={() => setActiveResultTab(t.id)}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold transition-all"
                style={activeResultTab === t.id
                  ? { background: 'linear-gradient(135deg,#7c3aed,#06b6d4)', color: '#fff' }
                  : { background: 'rgba(99,102,241,0.08)', color: '#6b7280', border: '1px solid rgba(99,102,241,0.1)' }}>
                {t.label}
              </button>
            ))}
          </div>

          {/* ── KPIs Tab ── */}
          {activeResultTab === 'kpis' && mc && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Mean Margin',      value: `${mc.summary.mean_margin > 0 ? '+' : ''}${mc.summary.mean_margin}%`,   color: mc.summary.mean_margin >= 0 ? 'text-emerald-400' : 'text-red-400', icon: '📊' },
                  { label: 'Loss Probability', value: `${mc.summary.loss_probability}%`,  color: mc.summary.loss_probability > 30 ? 'text-red-400' : 'text-yellow-400', icon: '⚠️' },
                  { label: '95% VaR',          value: `${mc.summary.var_95}%`,            color: mc.summary.var_95 < -10 ? 'text-red-400' : 'text-orange-400', icon: '📉' },
                  { label: 'Expected Shortfall', value: `${mc.summary.expected_shortfall}%`, color: 'text-purple-400', icon: '🔻' },
                  { label: 'Std Deviation',    value: `±${mc.summary.std_deviation}%`,    color: 'text-cyan-400',    icon: '〰️' },
                  { label: 'Min Margin (P1)',  value: `${mc.summary.min_margin}%`,        color: 'text-red-400',    icon: '⬇️' },
                  { label: 'Max Margin (P99)', value: `${mc.summary.max_margin}%`,        color: 'text-emerald-400', icon: '⬆️' },
                  { label: 'Simulations',      value: result.inputs.simulations.toLocaleString(), color: 'text-blue-400', icon: '🔁' },
                ].map(k => (
                  <KPICard key={k.label} label={k.label} value={k.value} colorClass={k.color} icon={k.icon} />
                ))}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { label: 'Contract Value',    value: fmt(result.params.contract_value),  color: 'text-white',      bg: 'rgba(99,102,241,0.05)' },
                  { label: 'Mean Penalty Cost', value: fmt(mc.penalty.mean_penalty),       color: 'text-orange-400', bg: 'rgba(249,115,22,0.05)' },
                  { label: 'Penalty Cap',       value: fmt(mc.penalty.penalty_cap),        color: 'text-red-400',    bg: 'rgba(239,68,68,0.05)' },
                  { label: 'Delay Rate',        value: `${mc.penalty.delay_rate}%`,        color: 'text-yellow-400', bg: 'rgba(234,179,8,0.05)' },
                  { label: 'Max Penalty (P99)', value: fmt(mc.penalty.max_penalty_p99),    color: 'text-red-300',    bg: 'rgba(239,68,68,0.05)' },
                  { label: 'Duration',          value: `${result.params.duration_months} months`, color: 'text-cyan-400', bg: 'rgba(6,182,212,0.05)' },
                ].map(k => (
                  <div key={k.label} className="p-3 rounded-xl" style={{ background: k.bg, border: '1px solid rgba(99,102,241,0.1)' }}>
                    <p className="text-gray-500 text-xs mb-1">{k.label}</p>
                    <p className={`font-bold text-sm ${k.color}`}>{k.value}</p>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* ── Cashflow Timeline Tab ── */}
          {activeResultTab === 'cashflow' && result?.cashflow_timeline && (
            <Card>
              <h4 className="text-white font-semibold mb-1">Monthly Cashflow Timeline</h4>
              <p className="text-gray-500 text-xs mb-4">Mean cashflow with P10/P90 confidence band across 300 simulated paths</p>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={result.cashflow_timeline}>
                  <defs>
                    <linearGradient id="cfGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#06b6d4" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="cumGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                  <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 10 }} label={{ value: 'Month', position: 'insideBottom', fill: '#6b7280', fontSize: 10, dy: 8 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} tickFormatter={(v) => fmt(v)} width={70} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }}
                    formatter={(v, n) => [fmt(v), n]}
                  />
                  <Area type="monotone" dataKey="cashflow_p90" stroke="transparent" fill="rgba(6,182,212,0.08)" name="P90 Band" />
                  <Area type="monotone" dataKey="cashflow"     stroke="#06b6d4" fill="url(#cfGrad)" strokeWidth={2} name="Mean Cashflow" />
                  <Area type="monotone" dataKey="cashflow_p10" stroke="transparent" fill="rgba(239,68,68,0.06)" name="P10 Band" />
                  <Area type="monotone" dataKey="cumulative"   stroke="#8b5cf6" fill="url(#cumGrad)" strokeWidth={2} strokeDasharray="5 3" name="Cumulative P&L" />
                </AreaChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-3 text-xs text-gray-500 flex-wrap">
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-cyan-400 inline-block" /> Mean Cashflow</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-purple-400 inline-block" style={{ borderTop: '2px dashed #8b5cf6' }} /> Cumulative P&L</span>
                <span className="flex items-center gap-1"><span className="w-3 h-2 bg-cyan-400/20 inline-block rounded" /> P10–P90 Band</span>
              </div>
            </Card>
          )}

          {/* ── Distribution Tab ── */}
          {activeResultTab === 'distribution' && mc && (
            <Card>
              <h4 className="text-white font-semibold mb-1">Margin Distribution Histogram</h4>
              <p className="text-gray-500 text-xs mb-4">
                Distribution of simulated margin outcomes across {result.inputs.simulations.toLocaleString()} runs
              </p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={mc.distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                  <XAxis dataKey="margin" tick={{ fill: '#6b7280', fontSize: 9 }} tickFormatter={(v) => `${v}%`} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0d1117', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '12px' }}
                    formatter={(v, _, p) => [v, `Margin: ${p.payload.margin}%`]}
                  />
                  <Bar dataKey="count" name="Simulations" radius={[2, 2, 0, 0]}>
                    {mc.distribution.map((entry, i) => (
                      <Cell key={i} fill={entry.margin < 0 ? '#ef4444' : entry.margin < 5 ? '#f59e0b' : '#10b981'} fillOpacity={0.8} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-3 text-xs text-gray-500">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-red-500 inline-block" /> Loss (&lt;0%)</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-yellow-500 inline-block" /> Thin (0–5%)</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-emerald-500 inline-block" /> Healthy (&gt;5%)</span>
              </div>
            </Card>
          )}

          {/* ── AI Insights Tab ── */}
          {activeResultTab === 'insights' && insights?.insights && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">🧠</span>
                <h4 className="text-white font-semibold">CFO Decision Intelligence</h4>
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-900/60 text-indigo-300">{insights.insights.length} findings</span>
              </div>
              {insights.insights.map((ins, i) => {
                const s = SEVERITY_STYLE[ins.severity] || SEVERITY_STYLE.LOW;
                return (
                  <div key={i} className="rounded-2xl p-4" style={{ background: s.bg, border: `1px solid ${s.border}` }}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-base">{ins.icon}</span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.text }}>{ins.severity}</span>
                      <span className="text-xs text-gray-400">{ins.category}</span>
                    </div>
                    <p className="text-sm font-medium mb-2" style={{ color: s.text }}>{ins.finding}</p>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      <span className="text-gray-500 font-semibold">Recommendation: </span>
                      {ins.recommendation}
                    </p>
                  </div>
                );
              })}
            </div>
          )}

          {/* ── Scenarios Tab ── */}
          {activeResultTab === 'scenarios' && scenarios && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">💥</span>
                <h4 className="text-white font-semibold">Cascading Scenario Analysis</h4>
                <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/60 text-red-300">vs Baseline</span>
              </div>
              {scenarios.map((sc) => (
                <Card key={sc.scenario}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{sc.icon}</span>
                      <span className="text-white font-bold text-sm">{sc.label}</span>
                    </div>
                    <div className="flex gap-3 text-xs">
                      <span className={`font-bold ${sc.delta.margin_change < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        Margin: {sc.delta.margin_change > 0 ? '+' : ''}{sc.delta.margin_change}%
                      </span>
                      <span className="text-orange-400 font-bold">
                        Loss Prob: +{sc.delta.loss_prob_change.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Cascade chain */}
                  <div className="flex gap-2 flex-wrap mb-4">
                    {sc.cascade_chain.map((step, i) => (
                      <div key={i} className="flex items-center gap-1">
                        <div className="text-xs px-2 py-1 rounded-lg text-center" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)', maxWidth: 160 }}>
                          <p className="text-gray-300 font-medium leading-tight">{step.event}</p>
                          <p className="text-gray-500 leading-tight mt-0.5">{step.impact}</p>
                        </div>
                        {i < sc.cascade_chain.length - 1 && <span className="text-gray-600 text-xs">→</span>}
                      </div>
                    ))}
                  </div>

                  {/* Baseline vs Stressed grid */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    {[
                      { label: 'Baseline Margin',  value: `${sc.baseline.mean_margin}%`,        color: 'text-emerald-400' },
                      { label: 'Stressed Margin',  value: `${sc.stressed.mean_margin}%`,        color: sc.stressed.mean_margin < 0 ? 'text-red-400' : 'text-yellow-400' },
                      { label: 'Baseline Loss Prob', value: `${sc.baseline.loss_probability}%`, color: 'text-gray-300' },
                      { label: 'Stressed Loss Prob', value: `${sc.stressed.loss_probability}%`, color: 'text-red-400' },
                    ].map(k => (
                      <div key={k.label} className="p-2 rounded-lg" style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.08)' }}>
                        <p className="text-gray-500 mb-0.5">{k.label}</p>
                        <p className={`font-bold ${k.color}`}>{k.value}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

// ─── Tab 4: Legal Reasoning ───────────────────────────────────────

const RISK_LEVEL_STYLES = {
  CRITICAL: { bg: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.5)', color: '#fca5a5', glow: 'rgba(239,68,68,0.3)', dot: '#ef4444' },
  HIGH:     { bg: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',  color: '#f87171', glow: 'rgba(239,68,68,0.2)',  dot: '#f87171' },
  MEDIUM:   { bg: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)', color: '#fbbf24', glow: 'rgba(234,179,8,0.2)',  dot: '#fbbf24' },
  LOW:      { bg: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)', color: '#6ee7b7', glow: 'rgba(16,185,129,0.2)', dot: '#10b981' },
};

const SEV_ICON = { CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🟢' };
const TYPE_ICON = { statute: '📜', case: '⚖️' };

const IssuePill = ({ severity }) => {
  const s = RISK_LEVEL_STYLES[severity] || RISK_LEVEL_STYLES.MEDIUM;
  return (
    <span className="text-xs px-2 py-0.5 rounded-full font-bold"
      style={{ background: s.bg, border: s.border, color: s.color }}>
      {severity}
    </span>
  );
};

const ConfidenceBar = ({ score }) => {
  const pct = Math.round(score * 100);
  const color = pct >= 70 ? '#10b981' : pct >= 45 ? '#fbbf24' : '#f87171';
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <div className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-xs font-bold" style={{ color }}>{pct}%</span>
    </div>
  );
};

const LegalTab = () => {
  const [clauseText, setClauseText] = useState('');
  const [jurisdiction, setJurisdiction] = useState('india');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [rewriteAccepted, setRewriteAccepted] = useState(false);
  const [showPassages, setShowPassages] = useState(false);

  const handleAnalyze = async () => {
    if (!clauseText.trim()) { setError('Please enter clause text.'); return; }
    setLoading(true);
    setError('');
    setRewriteAccepted(false);
    try {
      const data = await analyzeLegalClause(clauseText, jurisdiction);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.error || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const jurisdictions = [
    { value: 'india', flag: '🇮🇳', label: 'India', subtitle: 'ICA 1872' },
    { value: 'us',    flag: '🇺🇸', label: 'United States', subtitle: 'UCC' },
    { value: 'uk',    flag: '🇬🇧', label: 'United Kingdom', subtitle: 'UCTA 1977' },
  ];

  const riskStyle = result ? (RISK_LEVEL_STYLES[result.risk_level] || RISK_LEVEL_STYLES.MEDIUM) : null;

  return (
    <div className="space-y-5">
      {/* ── Input Card ── */}
      <Card>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xl">⚖️</span>
          <h3 className="text-white font-bold text-lg">Legal Reasoning Engine</h3>
          <span className="ml-auto text-xs px-2 py-0.5 rounded-full font-semibold"
            style={{ background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.3)', color: '#06b6d4' }}>
            RAG + Rules + AI
          </span>
        </div>
        <p className="text-gray-400 text-sm mb-5 ml-7">
          Retrieves relevant statutes &amp; case law, runs 11+ rule checks, then reasons with AI
          to cite laws, flag risks, and suggest compliant rewrites.
        </p>

        <div className="mb-4">
          <label className="text-xs text-gray-400 mb-2 block font-medium">Jurisdiction</label>
          <div className="grid grid-cols-3 gap-3">
            {jurisdictions.map((j) => (
              <button key={j.value} onClick={() => setJurisdiction(j.value)}
                className="py-3 px-3 rounded-2xl text-left transition-all duration-200"
                style={jurisdiction === j.value
                  ? { background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.4)', boxShadow: '0 0 16px rgba(6,182,212,0.1)' }
                  : { background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)' }}>
                <div className="text-2xl mb-1">{j.flag}</div>
                <div className="text-sm font-semibold" style={{ color: jurisdiction === j.value ? '#06b6d4' : '#9ca3af' }}>{j.label}</div>
                <div className="text-xs text-gray-600">{j.subtitle}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs text-gray-400 font-medium">Clause Text *</label>
            <span className="text-xs text-gray-600">{clauseText.length} chars</span>
          </div>
          <textarea rows={5} value={clauseText} onChange={(e) => setClauseText(e.target.value)}
            placeholder="Paste the clause text to analyze for legal risks…"
            className="w-full rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none transition-all"
            style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }} />
        </div>

        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

        <button onClick={handleAnalyze} disabled={loading || !clauseText.trim()}
          className="px-6 py-2.5 rounded-xl font-semibold text-white text-sm flex items-center gap-2 transition-all disabled:opacity-50"
          style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 20px rgba(6,182,212,0.25)' }}>
          {loading && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
          ⚖️ {loading ? 'Analyzing…' : 'Analyze Clause'}
        </button>
      </Card>

      {result && riskStyle && (
        <>
          {/* ── Risk Header ── */}
          <Card>
            <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
              <div className="flex items-center gap-3">
                <h4 className="text-white font-bold text-lg">Legal Analysis Result</h4>
                <span className="text-sm px-4 py-1.5 rounded-full font-black"
                  style={{ background: riskStyle.bg, border: riskStyle.border, color: riskStyle.color, boxShadow: `0 0 16px ${riskStyle.glow}` }}>
                  {result.risk_level} RISK
                </span>
                <span className="text-xs px-3 py-1 rounded-full"
                  style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                  {result.compliance_status}
                </span>
              </div>
              <div className="text-xs text-gray-500">{result.jurisdiction?.name} · {new Date(result.analyzed_at).toLocaleTimeString()}</div>
            </div>

            {/* Confidence */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Analysis Confidence</span>
                <span className="text-xs text-gray-500">Based on RAG retrieval + rule coverage + AI</span>
              </div>
              <ConfidenceBar score={result.confidence_score} />
            </div>

            {/* Applicable Laws */}
            <div>
              <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Applicable Laws</p>
              <div className="flex flex-wrap gap-2">
                {(result.jurisdiction?.applicable_laws || []).map((law, i) => (
                  <span key={i} className="text-xs px-3 py-1.5 rounded-full font-medium"
                    style={{ background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.25)', color: '#06b6d4' }}>
                    📜 {law}
                  </span>
                ))}
              </div>
            </div>
          </Card>

          {/* ── Issues ── */}
          {result.issues?.length > 0 && (
            <Card>
              <h4 className="text-white font-bold mb-3">
                Legal Issues <span className="text-gray-500 font-normal">({result.issues.length})</span>
              </h4>
              <div className="space-y-3">
                {result.issues.map((issue, i) => (
                  <div key={i} className="rounded-xl p-4"
                    style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.12)' }}>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <span className="text-sm font-semibold text-white flex items-center gap-2">
                        {SEV_ICON[issue.severity] || '🔵'} {issue.issue}
                      </span>
                      <IssuePill severity={issue.severity} />
                    </div>
                    <p className="text-xs text-gray-400 mb-3 leading-relaxed">{issue.reason}</p>
                    <div className="grid grid-cols-1 gap-1.5">
                      {issue.law_reference && issue.law_reference !== 'N/A' && (
                        <div className="flex items-start gap-2">
                          <span className="text-xs text-indigo-400 font-semibold flex-shrink-0">Law:</span>
                          <span className="text-xs text-indigo-300">{issue.law_reference}</span>
                        </div>
                      )}
                      {issue.case_reference && issue.case_reference !== 'N/A' && !issue.case_reference.toLowerCase().includes('consult') && (
                        <div className="flex items-start gap-2">
                          <span className="text-xs text-purple-400 font-semibold flex-shrink-0">Case:</span>
                          <span className="text-xs text-purple-300">{issue.case_reference}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* ── Explanation ── */}
          <Card>
            <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Legal Explanation</p>
            <p className="text-sm text-gray-300 leading-relaxed">{result.explanation}</p>
          </Card>

          {/* ── Rule-Based Flags ── */}
          {result.rule_flags?.length > 0 && (
            <Card>
              <h4 className="text-white font-bold mb-3">
                Rule-Based Flags <span className="text-gray-500 font-normal">({result.rule_flags.length})</span>
              </h4>
              <div className="space-y-2">
                {result.rule_flags.map((flag, i) => {
                  const s = RISK_LEVEL_STYLES[flag.severity] || RISK_LEVEL_STYLES.MEDIUM;
                  return (
                    <div key={i} className="rounded-xl p-3"
                      style={{ background: `${s.bg}`, border: s.border }}>
                      <div className="flex items-start gap-2 mb-1">
                        <span className="text-sm flex-shrink-0">{SEV_ICON[flag.severity]}</span>
                        <span className="text-sm font-semibold" style={{ color: s.color }}>{flag.flag_message}</span>
                        <IssuePill severity={flag.severity} />
                      </div>
                      <p className="text-xs text-gray-400 ml-6 mb-1">{flag.explanation}</p>
                      <p className="text-xs ml-6" style={{ color: '#818cf8' }}>Ref: {flag.law_hint}</p>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* ── Compliant Rewrite ── */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Suggested Compliant Rewrite</p>
              <div className="flex gap-2">
                <button onClick={() => { navigator.clipboard.writeText(result.suggested_clause); }}
                  className="text-xs px-3 py-1 rounded-lg font-medium transition-all"
                  style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                  Copy
                </button>
                <button onClick={() => setRewriteAccepted(!rewriteAccepted)}
                  className="text-xs px-3 py-1 rounded-lg font-medium transition-all"
                  style={rewriteAccepted
                    ? { background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.4)', color: '#6ee7b7' }
                    : { background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.3)', color: '#06b6d4' }}>
                  {rewriteAccepted ? '✓ Accepted' : 'Accept'}
                </button>
              </div>
            </div>
            <div className="rounded-xl p-4 font-mono text-xs leading-relaxed text-gray-300"
              style={{ background: 'rgba(16,185,129,0.04)', border: `1px solid ${rewriteAccepted ? 'rgba(16,185,129,0.4)' : 'rgba(16,185,129,0.2)'}`, whiteSpace: 'pre-wrap' }}>
              {result.suggested_clause}
            </div>
          </Card>

          {/* ── Retrieved Legal Passages (RAG) ── */}
          {result.retrieved_passages?.length > 0 && (
            <Card>
              <button className="w-full flex items-center justify-between"
                onClick={() => setShowPassages(!showPassages)}>
                <h4 className="text-white font-bold">
                  Retrieved Legal Knowledge <span className="text-gray-500 font-normal">({result.retrieved_passages.length} passages)</span>
                </h4>
                <span className="text-gray-500 text-xs">{showPassages ? '▲ Hide' : '▼ Show'}</span>
              </button>
              {showPassages && (
                <div className="mt-3 space-y-3">
                  {result.retrieved_passages.map((p, i) => (
                    <div key={i} className="rounded-xl p-3"
                      style={{ background: 'rgba(13,17,23,0.5)', border: '1px solid rgba(99,102,241,0.1)' }}>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span>{TYPE_ICON[p.type] || '📄'}</span>
                        <span className="text-xs font-semibold text-white">{p.title}</span>
                        <span className="ml-auto text-xs px-2 py-0.5 rounded-full"
                          style={{ background: 'rgba(99,102,241,0.1)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.2)' }}>
                          {p.type}
                        </span>
                      </div>
                      <p className="text-xs text-indigo-400 mb-1.5 font-medium">{p.citation}</p>
                      <p className="text-xs text-gray-400 leading-relaxed">{p.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}
        </>
      )}
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────

export default function AIStudio() {
  const [activeTab, setActiveTab] = useState('redlining');
  const [tabKey, setTabKey] = useState(0);
  const [contracts, setContracts] = useState([]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setTabKey((k) => k + 1);
  };

  const loadContracts = useCallback(async () => {
    try {
      const data = await fetchContracts();
      if (Array.isArray(data)) setContracts(data);
      else if (data?.contracts) setContracts(data.contracts);
    } catch {
      // silently fail; contracts list is optional
    }
  }, []);

  useEffect(() => {
    loadContracts();
  }, [loadContracts]);

  return (
    <div className="min-h-screen text-gray-100 p-6" style={{ background: 'linear-gradient(135deg, #0a0f1e 0%, #0d1117 50%, #111827 100%)' }}>
      {/* Animated grid overlay */}
      <div className="fixed inset-0 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px)',
        backgroundSize: '60px 60px',
        zIndex: 0,
      }} />

      <div className="max-w-5xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-xl font-black text-white" style={{ background: 'linear-gradient(135deg, #0891b2, #7c3aed)', boxShadow: '0 0 30px rgba(6,182,212,0.35)' }}>
              AI
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight" style={{ background: 'linear-gradient(135deg, #06b6d4, #7c3aed)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                AI Studio
              </h1>
              <p className="text-gray-500 text-sm mt-0.5">Contract-Specific AI Intelligence</p>
            </div>
            <div className="ml-auto flex items-center gap-3">
              <span className="text-xs px-3 py-1.5 rounded-full font-semibold flex items-center gap-1.5"
                style={{ background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.25)', color: '#06b6d4' }}>
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                4 AI Modules
              </span>
              <span className="text-xs px-3 py-1.5 rounded-full font-semibold"
                style={{ background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.25)', color: '#a78bfa' }}>
                ContractAI
              </span>
            </div>
          </div>

          {/* Tabs */}
          <TabBar activeTab={activeTab} onTabChange={handleTabChange} />
        </div>

        {/* Tab Content with animation */}
        <div key={tabKey} style={{ animation: 'tabEnter 0.3s ease-out' }}>
          {activeTab === 'redlining' && <RedliningTab contracts={contracts} />}
          {activeTab === 'negotiation' && <NegotiationTab contracts={contracts} />}
          {activeTab === 'cfo' && <CFOSimTab contracts={contracts} />}
          {activeTab === 'legal' && <LegalTab />}
        </div>
      </div>
    </div>
  );
}
