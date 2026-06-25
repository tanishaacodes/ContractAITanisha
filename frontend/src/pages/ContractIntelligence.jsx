/**
 * Contract Intelligence Page
 * ============================
 * AutoRAG-powered contract Q&A + ingestion pipeline UI.
 * Fully theme-aware — works with dark / light / tokyo themes.
 *
 * Connects to:
 *   POST /api/ingestion/upload/
 *   POST /api/autorag/ask/
 *   GET  /api/autorag/clauses/risk/
 *   GET  /api/autorag/clauses/flags/?type=...
 *   GET  /api/ingestion/status/
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import ForceGraph2D from 'react-force-graph-2d';
import {
  Brain, Upload, Send, AlertTriangle, Shield,
  FileText, Clock, DollarSign, Scale, RefreshCw,
  CheckCircle, XCircle, Loader, ChevronDown, ChevronRight,
  Zap, MessageCircle, Activity, Search, Network,
} from 'lucide-react';
import useThemeStore from '../store/themeStore';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const getHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ─── Risk colours (always vivid, theme-independent) ──────────────────────────
const RISK_STYLES = {
  CRITICAL: { bg: 'bg-red-500/15',    border: 'border-red-500/30',    text: 'text-red-400',    dot: 'bg-red-500' },
  HIGH:     { bg: 'bg-orange-500/15', border: 'border-orange-500/30', text: 'text-orange-400', dot: 'bg-orange-500' },
  MEDIUM:   { bg: 'bg-yellow-500/15', border: 'border-yellow-500/30', text: 'text-yellow-400', dot: 'bg-yellow-500' },
  LOW:      { bg: 'bg-green-500/15',  border: 'border-green-500/30',  text: 'text-green-400',  dot: 'bg-green-500' },
};

const RiskBadge = ({ level }) => {
  const s = RISK_STYLES[level] || RISK_STYLES.LOW;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold border ${s.bg} ${s.border} ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {level}
    </span>
  );
};

// ─── Status pill ─────────────────────────────────────────────────────────────
const StatusPill = ({ label, ok }) => {
  if (ok === null) return (
    <span className="text-xs px-2.5 py-1 rounded-full bg-slate-700/50 border border-slate-600/50 text-slate-400 flex items-center gap-1.5">
      <Loader className="w-3 h-3 animate-spin" />{label}
    </span>
  );
  return (
    <span className={`text-xs px-2.5 py-1 rounded-full flex items-center gap-1.5 border font-medium
      ${ok ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-green-400' : 'bg-red-400'}`} />
      {label}
    </span>
  );
};

// ─── Chat bubble ─────────────────────────────────────────────────────────────
const Bubble = ({ role, text, isDark }) => (
  <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'}`}>
    <div className={`max-w-[82%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
      ${role === 'user'
        ? 'bg-cyan-500/20 border border-cyan-500/30 text-cyan-100'
        : isDark
          ? 'bg-slate-700/60 border border-slate-600/50 text-slate-200'
          : 'bg-slate-100 border border-slate-200 text-slate-700'
      }`}
    >
      {text}
    </div>
  </div>
);

// ─── Clause card ─────────────────────────────────────────────────────────────
const ClauseCard = ({ clause, isDark }) => {
  const [open, setOpen] = useState(false);
  const flags = [
    clause.obligation  && 'Obligation',
    clause.indemnity   && 'Indemnity',
    clause.termination && 'Termination',
    clause.payment     && 'Payment',
  ].filter(Boolean);

  const cardCls = isDark
    ? 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600/70'
    : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm';

  return (
    <div className={`border rounded-xl overflow-hidden transition-colors ${cardCls}`}>
      <button
        onClick={() => setOpen(o => !o)}
        className={`w-full flex items-center justify-between px-4 py-3 transition-colors
          ${isDark ? 'hover:bg-slate-700/30' : 'hover:bg-slate-50'}`}
      >
        <div className="flex items-center gap-3 min-w-0">
          <FileText className="w-4 h-4 text-slate-400 shrink-0" />
          <div className="text-left min-w-0">
            <p className={`text-sm font-medium truncate ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
              {clause.clause_number ? `Clause ${clause.clause_number}` : 'Clause'}
              {clause.document && <span className="text-slate-400 font-normal"> — {clause.document}</span>}
            </p>
            <p className="text-slate-400 text-xs truncate mt-0.5">
              {clause.text_preview || clause.text?.slice(0, 100)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-3">
          <RiskBadge level={clause.risk_level || 'LOW'} />
          {open ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
        </div>
      </button>

      {open && (
        <div className={`px-4 pb-4 border-t ${isDark ? 'border-slate-700/50' : 'border-slate-200'}`}>
          <p className={`text-sm mt-3 leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
            {clause.text || clause.text_preview}
          </p>
          {flags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {flags.map(f => (
                <span key={f} className="text-xs px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-500/25 text-violet-300">{f}</span>
              ))}
            </div>
          )}
          {clause.temporal_refs?.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {clause.temporal_refs.map((t, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-blue-500/15 border border-blue-500/25 text-blue-300">
                  <Clock className="w-3 h-3 inline mr-1" />{t}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ContractIntelligence() {
  const { theme } = useThemeStore();
  const isDark = theme?.id === 'dark';
  const chatEndRef = useRef(null);

  // ── Pipeline status
  const [status, setStatus] = useState({ neo4j_connected: null, embeddings_ready: null });

  // ── Ingest panel
  const [docName, setDocName]         = useState('');
  const [docText, setDocText]         = useState('');
  const [file, setFile]               = useState(null);
  const [indexing, setIndexing]       = useState(false);
  const [indexResult, setIndexResult] = useState(null);
  const [indexError, setIndexError]   = useState('');

  // ── Chat panel
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Hello! I'm UniContractAI.\n\nIndex a contract on the left, then ask me anything — risks, obligations, termination terms, payment conditions, or specific clauses." }
  ]);
  const [query, setQuery]   = useState('');
  const [asking, setAsking] = useState(false);

  // ── Clause browser
  const [activeTab, setActiveTab]         = useState('risk');
  const [clauses, setClauses]             = useState([]);
  const [clauseLoading, setClauseLoading] = useState(false);

  // ── Knowledge Graph
  const [graphData, setGraphData]           = useState({ nodes: [], links: [] });
  const [graphLoading, setGraphLoading]     = useState(false);
  const [graphStats, setGraphStats]         = useState(null);
  const [selectedNode, setSelectedNode]     = useState(null);
  const [graphExpanded, setGraphExpanded]   = useState(false);
  const [graphDocFilter, setGraphDocFilter] = useState('');   // '' = all documents
  const [graphDocList, setGraphDocList]     = useState([]);   // all known document names
  const graphRef                            = useRef();

  useEffect(() => {
    axios.get(`${API_BASE}/api/ingestion/status/`).then(r => setStatus(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => { fetchClauses(activeTab); }, [activeTab]);

  const fetchGraph = useCallback(async (docFilter) => {
    setGraphLoading(true);
    setSelectedNode(null);
    try {
      const params = docFilter ? `?document=${encodeURIComponent(docFilter)}` : '';
      const r = await axios.get(`${API_BASE}/api/autorag/graph/${params}`, { headers: getHeaders() });
      const nodes = r.data.nodes || [];
      setGraphData({ nodes, links: r.data.links || [] });
      setGraphStats(r.data.stats || null);
      // Keep a running list of all document names (union across filter calls)
      const docNames = nodes.filter(n => n.type === 'Document').map(n => n.label);
      if (docNames.length > 0) {
        setGraphDocList(prev => {
          const merged = Array.from(new Set([...prev, ...docNames])).sort();
          return merged;
        });
      }
    } catch {
      setGraphData({ nodes: [], links: [] });
    } finally { setGraphLoading(false); }
  }, []);

  useEffect(() => { fetchGraph(graphDocFilter); }, [fetchGraph, graphDocFilter]);

  const fetchClauses = async (tab) => {
    setClauseLoading(true);
    setClauses([]);
    try {
      const url = tab === 'risk'
        ? `${API_BASE}/api/autorag/clauses/risk/?limit=20`
        : `${API_BASE}/api/autorag/clauses/flags/?type=${tab}&limit=20`;
      const r = await axios.get(url, { headers: getHeaders() });
      setClauses(r.data.clauses || []);
    } catch { setClauses([]); }
    finally { setClauseLoading(false); }
  };

  const handleIndex = async () => {
    if (!docName.trim() && !file) { setIndexError('Enter a document name.'); return; }
    if (!docText.trim() && !file) { setIndexError('Paste contract text or upload a file.'); return; }
    setIndexing(true); setIndexError(''); setIndexResult(null);
    try {
      let response;
      if (file) {
        const fd = new FormData();
        fd.append('file', file);
        if (docName.trim()) fd.append('name', docName.trim());
        response = await axios.post(`${API_BASE}/api/ingestion/upload/`, fd, {
          headers: { ...getHeaders(), 'Content-Type': 'multipart/form-data' },
        });
      } else {
        response = await axios.post(
          `${API_BASE}/api/ingestion/upload/`,
          { name: docName.trim(), text: docText.trim() },
          { headers: getHeaders() }
        );
      }
      setIndexResult(response.data);
      const rs = response.data.risk_summary || {};
      setMessages(m => [...m, {
        role: 'ai',
        text: `Indexed "${response.data.document}" — ${response.data.clauses_extracted} clauses extracted.\n\nRisk breakdown: ${Object.entries(rs).map(([k, v]) => `${k}: ${v}`).join(' | ')}\n\nAsk me anything about this contract.`
      }]);
      fetchClauses(activeTab);
      fetchGraph(graphDocFilter);
      setDocText(''); setDocName(''); setFile(null);
    } catch (e) {
      const errData = e.response?.data || {};
      const msg = errData.error || 'Indexing failed.';
      const hint = errData.hint ? `\n${errData.hint}` : '';
      setIndexError(msg + hint);
    } finally { setIndexing(false); }
  };

  const handleAsk = async () => {
    if (!query.trim() || asking) return;
    const q = query.trim(); setQuery('');
    setMessages(m => [...m, { role: 'user', text: q }]);
    setAsking(true);
    try {
      const r = await axios.post(`${API_BASE}/api/autorag/ask/`, { query: q }, { headers: getHeaders() });
      const d = r.data;
      const suffix = d.clauses_retrieved > 0 ? `\n\n${d.clauses_retrieved} clauses retrieved (intent: ${d.intent})` : '';
      setMessages(m => [...m, { role: 'ai', text: (d.answer || 'No answer.') + suffix }]);
      if (d.clauses_retrieved > 0) fetchClauses(activeTab);
    } catch (e) {
      setMessages(m => [...m, { role: 'ai', text: e.response?.data?.error || 'Failed. Index a contract first.' }]);
    } finally { setAsking(false); }
  };

  const onKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk(); }
  };

  const SUGGESTIONS = [
    'What are the termination conditions?',
    'List all HIGH risk clauses',
    'What payment terms are defined?',
    'Which obligations does the vendor have?',
    'Are there indemnity clauses?',
  ];

  const TABS = [
    { id: 'risk',        label: 'High Risk',   icon: AlertTriangle },
    { id: 'obligation',  label: 'Obligations', icon: Scale },
    { id: 'indemnity',   label: 'Indemnity',   icon: Shield },
    { id: 'termination', label: 'Termination', icon: XCircle },
    { id: 'payment',     label: 'Payment',     icon: DollarSign },
    { id: 'temporal',    label: 'Dates',       icon: Clock },
  ];

  // ── Theme-derived classes ────────────────────────────────────────────────────
  const card      = isDark ? 'bg-slate-800/50 border-slate-700/50'  : 'bg-white border-slate-200 shadow-sm';
  const input     = isDark
    ? 'bg-slate-700/40 border-slate-600/50 text-white placeholder-slate-500 focus:border-cyan-500/60 focus:bg-slate-700/60'
    : 'bg-slate-50 border-slate-300 text-slate-800 placeholder-slate-400 focus:border-cyan-500 focus:bg-white';
  const divider   = isDark ? 'border-slate-700/50'  : 'border-slate-200';
  const heading   = isDark ? 'text-white'            : 'text-slate-800';
  const subtext   = isDark ? 'text-slate-400'        : 'text-slate-500';
  const tabActive = isDark ? 'border-cyan-500 text-cyan-400' : 'border-cyan-600 text-cyan-600';
  const tabIdle   = isDark
    ? 'border-transparent text-slate-400 hover:text-slate-200'
    : 'border-transparent text-slate-500 hover:text-slate-700';
  const uploadZone = isDark
    ? 'bg-slate-700/30 border-slate-600/50 border-dashed text-slate-400 hover:border-cyan-500/50 hover:bg-slate-700/50'
    : 'bg-slate-50 border-slate-300 border-dashed text-slate-500 hover:border-cyan-500 hover:bg-slate-100';
  const chipBase  = isDark
    ? 'bg-slate-700/50 border-slate-600/50 text-slate-400 hover:text-cyan-300 hover:border-cyan-500/40'
    : 'bg-slate-100 border-slate-200 text-slate-500 hover:text-cyan-600 hover:border-cyan-400';

  return (
    <div className="space-y-6">

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h1 className={`text-2xl font-bold ${heading}`}>Contract Intelligence</h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/15 border border-cyan-500/25 text-cyan-400 font-semibold">
              AutoRAG
            </span>
          </div>
          <p className={`text-sm ${subtext} pl-[52px]`}>
            Index contracts &rarr; semantic clause extraction &rarr; Qwen2.5 Q&amp;A over Neo4j Graph + Vector Index
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <StatusPill label="Neo4j"      ok={status.neo4j_connected} />
          <StatusPill label="Embeddings" ok={status.embeddings_ready} />
        </div>
      </div>

      {/* ── Index + Chat grid ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

        {/* LEFT — Index */}
        <div className={`border rounded-2xl p-6 flex flex-col gap-4 ${card}`}>
          <div className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-cyan-400" />
            <h2 className={`font-semibold ${heading}`}>Index a Contract</h2>
          </div>

          <input
            className={`w-full border rounded-xl px-4 py-2.5 text-sm outline-none transition-colors ${input}`}
            placeholder="Document name (e.g. MSA_Vendor_2024.pdf)"
            value={docName}
            onChange={e => setDocName(e.target.value)}
          />

          <textarea
            rows={6}
            className={`w-full border rounded-xl px-4 py-3 text-sm resize-none outline-none transition-colors ${input}`}
            placeholder={`Paste contract text here…\n\nExample:\n1. Payment Terms. The Buyer shall pay within 30 days.\n2. Termination. Either party may terminate with 90 days notice.`}
            value={docText}
            onChange={e => setDocText(e.target.value)}
          />

          <div className="flex items-center gap-3">
            <label className="flex-1 cursor-pointer">
              <div className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-colors ${uploadZone}`}>
                <Upload className="w-4 h-4 shrink-0" />
                <span className="text-sm truncate">{file ? file.name : 'Or upload PDF / DOCX / TXT'}</span>
              </div>
              <input type="file" accept=".pdf,.docx,.txt" className="hidden"
                onChange={e => setFile(e.target.files[0] || null)} />
            </label>
            {file && (
              <button onClick={() => setFile(null)} className="text-slate-500 hover:text-red-400 transition-colors">
                <XCircle className="w-5 h-5" />
              </button>
            )}
          </div>

          {indexError && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <p className="text-red-300 text-sm whitespace-pre-wrap leading-relaxed">{indexError}</p>
            </div>
          )}

          <button
            onClick={handleIndex}
            disabled={indexing}
            className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 text-white font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-opacity shadow-lg shadow-cyan-500/20"
          >
            {indexing ? <Loader className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {indexing ? 'Indexing…' : 'Index Contract'}
          </button>

          {indexResult && (
            <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-green-300 font-semibold text-sm">Indexed: {indexResult.document}</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div>
                  <p className="text-white font-bold text-2xl">{indexResult.clauses_extracted}</p>
                  <p className={`text-xs ${subtext}`}>Clauses</p>
                </div>
                <div>
                  <p className="text-white font-bold text-2xl">{indexResult.neo4j?.entities ?? '—'}</p>
                  <p className={`text-xs ${subtext}`}>Entities</p>
                </div>
              </div>
              {indexResult.risk_summary && (
                <div className="grid grid-cols-4 gap-1.5">
                  {Object.entries(indexResult.risk_summary).map(([k, v]) => {
                    const s = RISK_STYLES[k] || RISK_STYLES.LOW;
                    return (
                      <div key={k} className={`text-center py-2 rounded-lg border ${s.bg} ${s.border}`}>
                        <p className={`font-bold text-lg ${s.text}`}>{v}</p>
                        <p className={`text-xs ${s.text} opacity-70`}>{k}</p>
                      </div>
                    );
                  })}
                </div>
              )}
              {indexResult.flag_summary && (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(indexResult.flag_summary)
                    .filter(([, v]) => v > 0)
                    .map(([k, v]) => (
                      <span key={k} className="text-xs px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-500/25 text-violet-300">
                        {k}: {v}
                      </span>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT — Chat */}
        <div className={`border rounded-2xl flex flex-col ${card}`} style={{ minHeight: '520px' }}>
          <div className={`flex items-center gap-2 px-6 py-4 border-b ${divider}`}>
            <MessageCircle className="w-4 h-4 text-cyan-400" />
            <h2 className={`font-semibold ${heading}`}>Ask UniContractAI</h2>
            {asking && <Loader className="w-3 h-3 text-cyan-400 animate-spin ml-auto" />}
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" style={{ maxHeight: '340px' }}>
            {messages.map((m, i) => (
              <Bubble key={i} role={m.role} text={m.text} isDark={isDark} />
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className={`px-4 pt-3 pb-2 flex gap-2 overflow-x-auto border-t ${divider}`}
            style={{ scrollbarWidth: 'none' }}>
            {SUGGESTIONS.map(s => (
              <button key={s} onClick={() => setQuery(s)}
                className={`shrink-0 text-xs px-3 py-1.5 rounded-full border whitespace-nowrap transition-colors ${chipBase}`}>
                {s}
              </button>
            ))}
          </div>

          <div className="px-4 pb-4 pt-2">
            <div className="flex gap-2">
              <textarea
                rows={2}
                className={`flex-1 border rounded-xl px-4 py-2.5 text-sm resize-none outline-none transition-colors ${input}`}
                placeholder="Ask about risks, obligations, termination, payment…"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={onKeyDown}
              />
              <button
                onClick={handleAsk}
                disabled={asking || !query.trim()}
                className="px-4 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-white transition-colors flex items-center justify-center"
              >
                {asking ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
            <p className={`text-xs mt-1.5 pl-1 ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
              Enter to send &middot; Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>

      {/* ── Knowledge Graph ───────────────────────────────────────────────── */}
      <div className={`border rounded-2xl overflow-hidden ${card}`}>
        {/* Header */}
        <div className={`flex items-center flex-wrap gap-3 px-6 py-4 border-b ${divider}`}>
          <Network className="w-4 h-4 text-cyan-400 shrink-0" />
          <h2 className={`font-semibold ${heading}`}>Knowledge Graph</h2>
          {graphStats && (
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/15 border border-cyan-500/25 text-cyan-400">
                {graphStats.documents} docs
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/15 border border-violet-500/25 text-violet-400">
                {graphStats.clauses} clauses
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/15 border border-orange-500/25 text-orange-400">
                {graphStats.entities} entities
              </span>
            </div>
          )}

          {/* Document filter dropdown */}
          {graphDocList.length > 0 && (
            <select
              value={graphDocFilter}
              onChange={e => setGraphDocFilter(e.target.value)}
              className={`ml-auto text-xs px-3 py-1.5 rounded-lg border outline-none cursor-pointer transition-colors
                ${isDark
                  ? 'bg-slate-700/60 border-slate-600/50 text-slate-300 hover:border-cyan-500/40'
                  : 'bg-white border-slate-300 text-slate-700 hover:border-cyan-500'}`}
            >
              <option value="">All Documents ({graphDocList.length})</option>
              {graphDocList.map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          )}

          <div className={`flex items-center gap-2 ${graphDocList.length > 0 ? '' : 'ml-auto'}`}>
            <button onClick={() => fetchGraph(graphDocFilter)} title="Refresh graph"
              className={`transition-colors ${isDark ? 'text-slate-500 hover:text-cyan-400' : 'text-slate-400 hover:text-cyan-600'}`}>
              <RefreshCw className={`w-4 h-4 ${graphLoading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
            <button onClick={() => setGraphExpanded(e => !e)}
              className={`text-xs px-3 py-1 rounded-lg border transition-colors ${isDark ? 'border-slate-600/50 text-slate-400 hover:text-cyan-300 hover:border-cyan-500/40' : 'border-slate-200 text-slate-500 hover:text-cyan-600'}`}>
              {graphExpanded ? 'Collapse' : 'Expand'}
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className={`flex flex-wrap gap-x-5 gap-y-1.5 px-6 py-3 border-b ${divider} text-xs ${subtext}`}>
          {[
            { color: '#22d3ee', label: 'Document' },
            { color: '#ef4444', label: 'Critical Clause' },
            { color: '#f97316', label: 'High Clause / ORG' },
            { color: '#eab308', label: 'Medium Clause' },
            { color: '#22c55e', label: 'Low Clause / GPE' },
            { color: '#a78bfa', label: 'PERSON' },
            { color: '#60a5fa', label: 'LAW' },
            { color: '#fbbf24', label: 'MONEY / DATE' },
          ].map(({ color, label }) => (
            <span key={label} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: color }} />
              {label}
            </span>
          ))}
        </div>

        {/* Graph canvas */}
        <div className="relative" style={{ height: graphExpanded ? 600 : 380 }}>
          {graphLoading ? (
            <div className="absolute inset-0 flex items-center justify-center gap-3 text-slate-400">
              <Loader className="w-5 h-5 animate-spin text-cyan-400" />
              <span className="text-sm">Building graph…</span>
            </div>
          ) : graphData.nodes.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <Network className={`w-10 h-10 ${subtext} opacity-30`} />
              <p className={`text-sm ${subtext}`}>No graph data yet — index a contract above.</p>
            </div>
          ) : (
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              width={undefined}
              height={graphExpanded ? 600 : 380}
              backgroundColor={isDark ? '#0f172a' : '#f8fafc'}
              nodeLabel={n => `${n.type}: ${n.label}${n.preview ? `\n${n.preview}` : ''}`}
              nodeColor={n => n.color || '#94a3b8'}
              nodeRelSize={5}
              nodeVal={n => n.type === 'Document' ? 4 : n.type === 'Clause' ? 2 : 1}
              linkColor={() => isDark ? 'rgba(148,163,184,0.25)' : 'rgba(100,116,139,0.3)'}
              linkWidth={1}
              linkDirectionalArrowLength={4}
              linkDirectionalArrowRelPos={1}
              onNodeClick={node => setSelectedNode(node)}
              cooldownTicks={120}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const r = node.type === 'Document' ? 8 : node.type === 'Clause' ? 5 : 3.5;
                ctx.beginPath();
                ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
                ctx.fillStyle = node.color || '#94a3b8';
                ctx.fill();
                if (globalScale >= 1.5) {
                  ctx.font = `${11 / globalScale}px Sans-Serif`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'top';
                  ctx.fillStyle = isDark ? '#e2e8f0' : '#1e293b';
                  ctx.fillText(node.label.slice(0, 18), node.x, node.y + r + 2);
                }
              }}
            />
          )}
        </div>

        {/* Selected node detail */}
        {selectedNode && (
          <div className={`px-6 py-3 border-t ${divider} flex items-start justify-between gap-4`}>
            <div>
              <p className={`text-xs font-semibold uppercase tracking-wide ${subtext} mb-1`}>{selectedNode.type}</p>
              <p className={`text-sm font-medium ${heading}`}>{selectedNode.label}</p>
              {selectedNode.risk && (
                <span className="mt-1 inline-block"><RiskBadge level={selectedNode.risk} /></span>
              )}
              {selectedNode.preview && (
                <p className={`text-xs mt-1 ${subtext} italic`}>{selectedNode.preview}…</p>
              )}
            </div>
            <button onClick={() => setSelectedNode(null)}
              className={`text-xs transition-colors ${isDark ? 'text-slate-500 hover:text-red-400' : 'text-slate-400 hover:text-red-500'}`}>
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* ── Clause Browser ────────────────────────────────────────────────── */}
      <div className={`border rounded-2xl overflow-hidden ${card}`}>
        <div className={`flex items-center gap-2 px-6 py-4 border-b ${divider}`}>
          <Search className="w-4 h-4 text-cyan-400" />
          <h2 className={`font-semibold ${heading}`}>Clause Browser</h2>
          {!clauseLoading && clauses.length > 0 && (
            <span className={`text-xs ml-1 ${subtext}`}>{clauses.length} clauses</span>
          )}
          <button onClick={() => fetchClauses(activeTab)} title="Refresh"
            className={`ml-auto transition-colors ${isDark ? 'text-slate-500 hover:text-cyan-400' : 'text-slate-400 hover:text-cyan-600'}`}>
            <RefreshCw className={`w-4 h-4 ${clauseLoading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>

        <div className={`flex overflow-x-auto border-b ${divider}`} style={{ scrollbarWidth: 'none' }}>
          {TABS.map(t => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button key={t.id} onClick={() => setActiveTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors
                  ${active ? tabActive : tabIdle}`}>
                <Icon className="w-3.5 h-3.5" />
                {t.label}
                {!clauseLoading && clauses.length > 0 && active && (
                  <span className="ml-1 text-xs px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400">
                    {clauses.length}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="p-4 space-y-3 max-h-[480px] overflow-y-auto">
          {clauseLoading ? (
            <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
              <Loader className="w-5 h-5 animate-spin text-cyan-400" />
              <span className="text-sm">Loading clauses…</span>
            </div>
          ) : clauses.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Activity className={`w-8 h-8 ${subtext} opacity-40`} />
              <p className={`text-sm ${subtext}`}>No clauses found. Index a contract above first.</p>
            </div>
          ) : (
            clauses.map((c, i) => (
              <ClauseCard key={c.clause_id || i} clause={c} isDark={isDark} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
