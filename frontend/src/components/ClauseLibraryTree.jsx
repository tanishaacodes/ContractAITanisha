import { useState } from 'react';
import {
  ChevronRight, ChevronDown, FileText, Folder, FolderOpen, Sparkles,
  CheckCircle, XCircle, Brain, GitBranch, Shield, Users, DollarSign,
  AlertTriangle, Copy, X, TrendingUp, Hash, Tag, Activity, Eye, EyeOff
} from 'lucide-react';
import useThemeStore from '../store/themeStore';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const RISK_COLOR = {
  HIGH:   { bg: 'bg-red-900/40',    text: 'text-red-300',    border: 'border-red-700',    dot: 'bg-red-400' },
  MEDIUM: { bg: 'bg-yellow-900/40', text: 'text-yellow-300', border: 'border-yellow-700', dot: 'bg-yellow-400' },
  LOW:    { bg: 'bg-green-900/40',  text: 'text-green-300',  border: 'border-green-700',  dot: 'bg-green-400' },
};

const TYPE_COLOR = {
  OBLIGATION: { bg: 'bg-orange-900/40', text: 'text-orange-300', border: 'border-orange-700' },
  RISK:       { bg: 'bg-red-900/40',    text: 'text-red-300',    border: 'border-red-700' },
  RIGHT:      { bg: 'bg-green-900/40',  text: 'text-green-300',  border: 'border-green-700' },
  DEFINITION: { bg: 'bg-blue-900/40',   text: 'text-blue-300',   border: 'border-blue-700' },
  HEADING:    { bg: 'bg-slate-700/40',  text: 'text-slate-300',  border: 'border-slate-600' },
};

function Badge({ label, color }) {
  const c = color || { bg: 'bg-slate-700/40', text: 'text-slate-300', border: 'border-slate-600' };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold border ${c.bg} ${c.text} ${c.border}`}>
      {label}
    </span>
  );
}

function RiskBar({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color = pct >= 70 ? 'bg-red-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-green-500';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-semibold ${pct >= 70 ? 'text-red-400' : pct >= 40 ? 'text-yellow-400' : 'text-green-400'}`}>
        {pct}%
      </span>
    </div>
  );
}

export default function ClauseLibraryTree({ library, onClauseSelect, selectedClauseId }) {
  const { theme } = useThemeStore();
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [expandedClauses, setExpandedClauses] = useState(new Set());
  const [evolutionData, setEvolutionData] = useState({});
  const [showingEvolution, setShowingEvolution] = useState(null);
  const [loadingEvolution, setLoadingEvolution] = useState(null);
  const [loadingFullText, setLoadingFullText] = useState({});
  const [fullTexts, setFullTexts] = useState({});
  const [copied, setCopied] = useState(null);

  const toggleCategory = (cat) => {
    const s = new Set(expandedCategories);
    s.has(cat) ? s.delete(cat) : s.add(cat);
    setExpandedCategories(s);
  };

  const toggleClause = async (clause) => {
    const s = new Set(expandedClauses);
    if (s.has(clause.id)) {
      s.delete(clause.id);
      setExpandedClauses(s);
      return;
    }
    s.add(clause.id);
    setExpandedClauses(s);

    // Fetch full text if not already loaded
    if (!fullTexts[clause.id]) {
      setLoadingFullText(p => ({ ...p, [clause.id]: true }));
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API_BASE_URL}/clauses/${clause.id}/full-text/`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        setFullTexts(p => ({ ...p, [clause.id]: res.data }));
      } catch {
        setFullTexts(p => ({ ...p, [clause.id]: { error: true, extracted_text: clause.extracted_text } }));
      } finally {
        setLoadingFullText(p => ({ ...p, [clause.id]: false }));
      }
    }
  };

  const fetchEvolution = async (clauseId) => {
    if (evolutionData[clauseId]) {
      setShowingEvolution(showingEvolution === clauseId ? null : clauseId);
      return;
    }
    setLoadingEvolution(clauseId);
    try {
      const res = await axios.get(`${API_BASE_URL}/graph/evolution/${clauseId}/`);
      setEvolutionData(p => ({ ...p, [clauseId]: res.data }));
      setShowingEvolution(clauseId);
    } catch {
      setEvolutionData(p => ({ ...p, [clauseId]: { error: 'Failed to load' } }));
    } finally {
      setLoadingEvolution(null);
    }
  };

  const copyText = async (id, text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(id);
      setTimeout(() => setCopied(null), 2000);
    } catch {}
  };

  const expandAll = () => setExpandedCategories(new Set(Object.keys(library)));
  const collapseAll = () => setExpandedCategories(new Set());

  if (!library || Object.keys(library).length === 0) {
    return (
      <div className="text-center py-16">
        <Brain className="w-14 h-14 text-purple-400 mx-auto mb-4 opacity-40" />
        <p className="text-slate-400 font-medium">No clause library data</p>
        <p className="text-slate-500 text-sm mt-1">Process contract to generate clause library</p>
      </div>
    );
  }

  const totalClauses = Object.values(library).reduce((a, c) => a + c.length, 0);
  const totalFound = Object.values(library).reduce((a, c) => a + c.filter(x => x.found).length, 0);
  const totalHigh = Object.values(library).reduce((a, c) => a + c.filter(x => x.risk_level === 'HIGH').length, 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-600/20 border border-purple-500/30 flex items-center justify-center">
            <Brain className="w-4 h-4 text-purple-400" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Clause Library</h3>
            <p className="text-xs text-slate-400">{Object.keys(library).length} categories · {totalClauses} clauses</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={expandAll} className="px-3 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition">
            Expand All
          </button>
          <button onClick={collapseAll} className="px-3 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition">
            Collapse All
          </button>
        </div>
      </div>

      {/* Summary Stats Bar */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center">
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400">Total Clauses</p>
            <p className="text-lg font-bold text-white">{totalClauses}</p>
          </div>
        </div>
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-green-600/20 flex items-center justify-center">
            <CheckCircle className="w-4 h-4 text-green-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400">Matched</p>
            <p className="text-lg font-bold text-green-400">{totalFound}</p>
          </div>
        </div>
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-red-600/20 flex items-center justify-center">
            <AlertTriangle className="w-4 h-4 text-red-400" />
          </div>
          <div>
            <p className="text-xs text-slate-400">High Risk</p>
            <p className="text-lg font-bold text-red-400">{totalHigh}</p>
          </div>
        </div>
      </div>

      {/* Category Tree */}
      <div className="space-y-3">
        {Object.entries(library).map(([category, clauses]) => {
          const isExpanded = expandedCategories.has(category);
          const foundCount = clauses.filter(c => c.found).length;
          const highRisk = clauses.filter(c => c.risk_level === 'HIGH').length;
          const avgConfidence = clauses.length
            ? Math.round(clauses.reduce((a, c) => a + (c.confidence || 0), 0) / clauses.length)
            : 0;

          return (
            <div key={category} className="border border-slate-700/60 rounded-xl overflow-hidden bg-slate-800/30">
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/30 transition"
              >
                <div className="flex items-center gap-3">
                  {isExpanded
                    ? <ChevronDown className="w-4 h-4 text-blue-400" />
                    : <ChevronRight className="w-4 h-4 text-slate-400" />}
                  {isExpanded
                    ? <FolderOpen className="w-5 h-5 text-yellow-400" />
                    : <Folder className="w-5 h-5 text-yellow-600" />}
                  <span className="font-semibold text-white text-sm">{category}</span>
                  <span className="flex items-center gap-1 px-2 py-0.5 bg-purple-900/30 text-purple-300 border border-purple-700/40 rounded text-xs">
                    <Sparkles className="w-3 h-3" /> AI-Generated
                  </span>
                  {highRisk > 0 && (
                    <span className="px-2 py-0.5 bg-red-900/40 text-red-300 border border-red-700/40 rounded text-xs font-semibold">
                      {highRisk} HIGH RISK
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-slate-400">{foundCount}/{clauses.length} found</span>
                  <span className="text-xs text-slate-500">avg {avgConfidence}% conf</span>
                  <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                      style={{ width: `${(foundCount / clauses.length) * 100}%` }}
                    />
                  </div>
                </div>
              </button>

              {/* Clauses */}
              {isExpanded && (
                <div className="divide-y divide-slate-700/40">
                  {clauses.map((clause, idx) => {
                    const isSelected = selectedClauseId === clause.id;
                    const isOpen = expandedClauses.has(clause.id);
                    const fullData = fullTexts[clause.id];
                    const isLoadingFT = loadingFullText[clause.id];
                    const riskC = RISK_COLOR[clause.risk_level] || RISK_COLOR.LOW;
                    const typeC = TYPE_COLOR[clause.sentence_type] || { bg: 'bg-slate-700/40', text: 'text-slate-300', border: 'border-slate-600' };
                    const isShowingEvo = showingEvolution === clause.id;
                    const evo = evolutionData[clause.id];

                    return (
                      <div
                        key={clause.id}
                        className={`transition-all ${isSelected ? 'bg-blue-900/20 border-l-2 border-blue-500' : 'hover:bg-slate-700/20'}`}
                      >
                        {/* Clause Row */}
                        <div className="px-4 py-3">
                          {/* Top row: number, name, badges, actions */}
                          <div className="flex items-start gap-3">
                            {/* Index + status */}
                            <div className="flex-shrink-0 flex flex-col items-center gap-1 pt-0.5">
                              <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
                                {idx + 1}
                              </div>
                              {clause.found
                                ? <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                                : <XCircle className="w-3.5 h-3.5 text-red-400" />}
                            </div>

                            {/* Main content */}
                            <div className="flex-1 min-w-0">
                              {/* Clause name + badges */}
                              <div className="flex items-center gap-2 flex-wrap mb-2">
                                <button
                                  onClick={() => onClauseSelect && onClauseSelect(clause)}
                                  className="font-semibold text-white hover:text-blue-300 transition text-sm"
                                >
                                  {clause.clause_name}
                                </button>
                                {clause.sentence_type && (
                                  <Badge label={clause.sentence_type} color={typeC} />
                                )}
                                {clause.party && (
                                  <Badge label={clause.party} color={{ bg: 'bg-cyan-900/40', text: 'text-cyan-300', border: 'border-cyan-700' }} />
                                )}
                                {clause.risk_level && (
                                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold border ${riskC.bg} ${riskC.text} ${riskC.border}`}>
                                    <span className={`w-1.5 h-1.5 rounded-full ${riskC.dot}`} />
                                    {clause.risk_level}
                                  </span>
                                )}
                                {clause.has_embedding && (
                                  <span className="px-2 py-0.5 bg-purple-900/30 text-purple-300 border border-purple-700/40 rounded text-xs">
                                    Vector
                                  </span>
                                )}
                              </div>

                              {/* Metrics row */}
                              <div className="flex items-center gap-4 flex-wrap mb-2">
                                {clause.confidence != null && (
                                  <div className="flex items-center gap-1.5">
                                    <Activity className="w-3 h-3 text-slate-500" />
                                    <span className="text-xs text-slate-400">Confidence</span>
                                    <span className={`text-xs font-bold ${clause.confidence >= 80 ? 'text-green-400' : clause.confidence >= 60 ? 'text-yellow-400' : 'text-orange-400'}`}>
                                      {Math.round(clause.confidence)}%
                                    </span>
                                  </div>
                                )}
                                {clause.risk_score > 0 && (
                                  <div className="flex items-center gap-1.5">
                                    <TrendingUp className="w-3 h-3 text-slate-500" />
                                    <span className="text-xs text-slate-400">Risk</span>
                                    <RiskBar score={clause.risk_score} />
                                  </div>
                                )}
                                {clause.financial_impact > 0 && (
                                  <div className="flex items-center gap-1">
                                    <DollarSign className="w-3 h-3 text-red-400" />
                                    <span className="text-xs font-semibold text-red-300">
                                      ₹{clause.financial_impact.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                    </span>
                                  </div>
                                )}
                                {clause.match_count > 0 && (
                                  <div className="flex items-center gap-1">
                                    <Hash className="w-3 h-3 text-slate-500" />
                                    <span className="text-xs text-slate-400">{clause.match_count} matches</span>
                                  </div>
                                )}
                                {clause.clause_label && (
                                  <div className="flex items-center gap-1">
                                    <Tag className="w-3 h-3 text-slate-500" />
                                    <span className="text-xs text-slate-500">{clause.clause_label}</span>
                                  </div>
                                )}
                              </div>

                              {/* Preview text (always shown) */}
                              {clause.extracted_text && !isOpen && (
                                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed bg-slate-800/40 rounded-lg px-3 py-2 border border-slate-700/40">
                                  {clause.extracted_text}
                                </p>
                              )}

                              {/* Action buttons */}
                              <div className="flex items-center gap-2 mt-2">
                                <button
                                  onClick={() => toggleClause(clause)}
                                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                                    isOpen
                                      ? 'bg-blue-600/20 text-blue-300 border-blue-600/40 hover:bg-blue-600/30'
                                      : 'bg-slate-700/60 text-slate-300 border-slate-600/40 hover:bg-slate-700'
                                  }`}
                                >
                                  {isOpen ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                                  {isOpen ? 'Hide Text' : 'View Clause Text'}
                                </button>
                                <button
                                  onClick={() => fetchEvolution(clause.id)}
                                  disabled={loadingEvolution === clause.id}
                                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                                    isShowingEvo
                                      ? 'bg-cyan-600/20 text-cyan-300 border-cyan-600/40'
                                      : 'bg-slate-700/60 text-slate-300 border-slate-600/40 hover:bg-slate-700'
                                  }`}
                                >
                                  {loadingEvolution === clause.id
                                    ? <span className="animate-spin">◌</span>
                                    : <GitBranch className="w-3 h-3" />}
                                  Evolution
                                </button>
                              </div>
                            </div>
                          </div>

                          {/* Expanded full clause text */}
                          {isOpen && (
                            <div className="mt-3 ml-9">
                              <div className="bg-slate-900/60 border border-slate-600/40 rounded-xl overflow-hidden">
                                {/* Text header */}
                                <div className="flex items-center justify-between px-4 py-2 border-b border-slate-700/40 bg-slate-800/40">
                                  <div className="flex items-center gap-2">
                                    <FileText className="w-3.5 h-3.5 text-blue-400" />
                                    <span className="text-xs font-semibold text-slate-300">Full Clause Text</span>
                                  </div>
                                  {fullData && fullData.extracted_text && (
                                    <button
                                      onClick={() => copyText(clause.id, fullData.extracted_text)}
                                      className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-white hover:bg-slate-700 rounded transition"
                                    >
                                      <Copy className="w-3 h-3" />
                                      {copied === clause.id ? 'Copied!' : 'Copy'}
                                    </button>
                                  )}
                                </div>

                                {/* Text body */}
                                <div className="px-4 py-3">
                                  {isLoadingFT ? (
                                    <div className="flex items-center gap-2 py-4 text-slate-400 text-sm">
                                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" />
                                      Loading clause text...
                                    </div>
                                  ) : fullData ? (
                                    <>
                                      <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                                        {fullData.extracted_text || 'No text available for this clause.'}
                                      </p>
                                      {/* Extra metadata from full fetch */}
                                      {(fullData.keywords && Object.keys(fullData.keywords).length > 0) && (
                                        <div className="mt-3 pt-3 border-t border-slate-700/40">
                                          <p className="text-xs text-slate-500 mb-1.5">Keywords</p>
                                          <div className="flex flex-wrap gap-1.5">
                                            {Object.entries(fullData.keywords).slice(0, 8).map(([k, v]) => (
                                              <span key={k} className="px-2 py-0.5 bg-slate-700/60 text-slate-300 rounded text-xs border border-slate-600/40">
                                                {k} {v > 1 && <span className="text-slate-500">×{v}</span>}
                                              </span>
                                            ))}
                                          </div>
                                        </div>
                                      )}
                                    </>
                                  ) : (
                                    <p className="text-sm text-slate-400 italic">
                                      {clause.extracted_text || 'No text available.'}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Evolution panel */}
                          {isShowingEvo && evo && (
                            <div className="mt-3 ml-9 bg-slate-900/60 border border-cyan-700/30 rounded-xl p-4">
                              <div className="flex items-center gap-2 mb-3">
                                <GitBranch className="w-4 h-4 text-cyan-400" />
                                <span className="text-sm font-semibold text-white">Clause Evolution</span>
                              </div>
                              {evo.error ? (
                                <p className="text-red-400 text-sm">{evo.error}</p>
                              ) : evo.nodes && evo.nodes.length > 0 ? (
                                <div className="space-y-2">
                                  <p className="text-xs text-slate-400 mb-2">{evo.nodes.length} version(s) in graph</p>
                                  {evo.nodes.map((node, i) => (
                                    <div key={i} className="bg-slate-800/60 rounded-lg p-3 border border-slate-700/40">
                                      <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-semibold text-white">Version {node.version}</span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${node.risk_score > 0.7 ? 'bg-red-900/50 text-red-300' : node.risk_score > 0.4 ? 'bg-yellow-900/50 text-yellow-300' : 'bg-green-900/50 text-green-300'}`}>
                                          Risk: {(node.risk_score * 100).toFixed(0)}%
                                        </span>
                                      </div>
                                      {node.text_preview && (
                                        <p className="text-xs text-slate-400 line-clamp-2">{node.text_preview}</p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-slate-400">No evolution data available</p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-3 bg-slate-800/40 rounded-xl border border-slate-700/40 text-sm">
        <div className="flex items-center gap-4">
          <span className="text-slate-400">Categories: <span className="text-white font-semibold">{Object.keys(library).length}</span></span>
          <span className="text-slate-400">Clauses: <span className="text-white font-semibold">{totalClauses}</span></span>
          <span className="text-slate-400">Matched: <span className="text-green-400 font-semibold">{totalFound}</span></span>
          <span className="text-slate-400">High Risk: <span className="text-red-400 font-semibold">{totalHigh}</span></span>
        </div>
        <div className="flex items-center gap-2 text-purple-400">
          <Sparkles className="w-4 h-4" />
          <span className="text-xs">Powered by AI Clustering</span>
        </div>
      </div>
    </div>
  );
}
