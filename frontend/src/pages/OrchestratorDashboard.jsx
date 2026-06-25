import React, { useState, useEffect, useRef } from 'react';
import { analyzeContract, fetchContracts } from '../services/aiStudioService';

// ── Design tokens ──────────────────────────────────────────────────────────

const glass = {
  background: 'rgba(13,17,23,0.82)',
  border: '1px solid rgba(99,102,241,0.15)',
  backdropFilter: 'blur(20px)',
};

const RISK_STYLE = {
  CRITICAL: { bg: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.5)',  color: '#fca5a5', dot: '#ef4444' },
  HIGH:     { bg: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',  color: '#f87171', dot: '#f87171' },
  MEDIUM:   { bg: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)',  color: '#fbbf24', dot: '#fbbf24' },
  LOW:      { bg: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)', color: '#6ee7b7', dot: '#10b981' },
};

const DECISION_STYLE = {
  ACCEPT:      { bg: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.5)',  color: '#6ee7b7', label: 'ACCEPT',      icon: '✅' },
  RENEGOTIATE: { bg: 'rgba(234,179,8,0.15)',  border: '1px solid rgba(234,179,8,0.5)',   color: '#fbbf24', label: 'RENEGOTIATE', icon: '🔄' },
  REJECT:      { bg: 'rgba(239,68,68,0.15)',  border: '1px solid rgba(239,68,68,0.5)',   color: '#fca5a5', label: 'REJECT',      icon: '❌' },
};

const STEP_ICON = ['📄', '⚖️', '📊', '🤝', '🎯', '💡', '🧠'];

const REC_COLORS = {
  HIGH:   { bg: 'rgba(239,68,68,0.06)',  border: '1px solid rgba(239,68,68,0.2)',  badge: 'rgba(239,68,68,0.15)',  badgeText: '#f87171' },
  MEDIUM: { bg: 'rgba(234,179,8,0.06)',  border: '1px solid rgba(234,179,8,0.2)',  badge: 'rgba(234,179,8,0.15)',  badgeText: '#fbbf24' },
  LOW:    { bg: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', badge: 'rgba(16,185,129,0.15)', badgeText: '#6ee7b7' },
};

// ── Small components ───────────────────────────────────────────────────────

const Card = ({ children, className = '' }) => (
  <div className={`rounded-2xl p-5 ${className}`} style={glass}>{children}</div>
);

const ScoreRing = ({ score, size = 80 }) => {
  const r = size / 2 - 8;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const color = score >= 70 ? '#10b981' : score >= 45 ? '#fbbf24' : '#ef4444';
  return (
    <svg width={size} height={size}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={7} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={7}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`} style={{ transition: 'stroke-dasharray 1s ease' }} />
      <text x={size / 2} y={size / 2 + 5} textAnchor="middle" fill={color}
        style={{ fontSize: size * 0.20, fontWeight: 700 }}>{Math.round(score)}</text>
    </svg>
  );
};

const MiniBar = ({ value, max = 100, color }) => (
  <div className="h-1.5 rounded-full w-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
    <div className="h-full rounded-full transition-all duration-700"
      style={{ width: `${Math.min((value / max) * 100, 100)}%`, background: color }} />
  </div>
);

const RiskBadge = ({ level }) => {
  const s = RISK_STYLE[level] || RISK_STYLE.MEDIUM;
  return (
    <span className="text-xs px-2 py-0.5 rounded-full font-bold"
      style={{ background: s.bg, border: s.border, color: s.color }}>
      {level}
    </span>
  );
};

// ── Pipeline steps display ─────────────────────────────────────────────────

const PipelineSteps = ({ trace }) => {
  const STEP_NAMES = [
    'Clause Extraction', 'Legal Reasoning', 'CFO Simulation',
    'Negotiation', 'Scoring', 'Recommendations', 'RL Update',
  ];
  return (
    <div className="space-y-2">
      {STEP_NAMES.map((name, idx) => {
        const step = trace?.find(t => t.step === idx + 1);
        const done = !!step;
        return (
          <div key={idx} className="flex items-center gap-3 py-2 px-3 rounded-xl"
            style={{ background: done ? 'rgba(16,185,129,0.05)' : 'rgba(99,102,241,0.04)', border: done ? '1px solid rgba(16,185,129,0.15)' : '1px solid rgba(99,102,241,0.08)' }}>
            <span className="text-lg">{STEP_ICON[idx]}</span>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold" style={{ color: done ? '#e5e7eb' : '#6b7280' }}>{name}</span>
                {done && <span className="text-xs text-gray-500">{step.duration_ms.toFixed(0)}ms</span>}
              </div>
              {done && step.summary && <p className="text-xs text-gray-500 mt-0.5">{step.summary}</p>}
            </div>
            <div className="flex-shrink-0">
              {done
                ? <span className="text-emerald-400 text-sm">✓</span>
                : <span className="w-3 h-3 rounded-full inline-block" style={{ background: 'rgba(99,102,241,0.3)' }} />}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ── Input source tab ───────────────────────────────────────────────────────

const INPUT_TABS = [
  { id: 'contract', label: '🗂️ Select Contract', desc: 'Choose from existing contracts in the database' },
  { id: 'upload',   label: '📤 Upload Document', desc: 'Upload a .txt or .pdf contract file' },
  { id: 'text',     label: '✏️ Paste Text',       desc: 'Paste raw contract or clause text' },
];

// ── Main page ──────────────────────────────────────────────────────────────

const OrchestratorDashboard = () => {
  const [step, setStep]           = useState('config');   // config | running | result
  const [result, setResult]       = useState(null);
  const [error, setError]         = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  // Input mode
  const [inputMode, setInputMode] = useState('contract');  // contract | upload | text

  // Contract selector
  const [contracts, setContracts]         = useState([]);
  const [contractsLoading, setContractsLoading] = useState(false);
  const [selectedContractId, setSelectedContractId] = useState('');
  const [contractSearch, setContractSearch] = useState('');

  // File upload
  const [uploadedFile, setUploadedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Raw text
  const [rawText, setRawText] = useState('');

  // Config params
  const [jurisdiction, setJurisdiction]     = useState('india');
  const [contractValue, setContractValue]   = useState('500000');
  const [durationMonths, setDurationMonths] = useState('12');

  // Load contracts when switching to contract mode
  useEffect(() => {
    if (inputMode === 'contract' && contracts.length === 0) {
      setContractsLoading(true);
      fetchContracts()
        .then(data => {
          const list = Array.isArray(data) ? data : (data?.results || data?.contracts || []);
          setContracts(list);
        })
        .catch(() => setContracts([]))
        .finally(() => setContractsLoading(false));
    }
  }, [inputMode]);

  const filteredContracts = contracts.filter(c => {
    const q = contractSearch.toLowerCase();
    return (
      (c.title || c.name || '').toLowerCase().includes(q) ||
      (c.id || '').toLowerCase().includes(q)
    );
  });

  const handleFileChange = (e) => {
    const file = e.target.files?.[0] || null;
    setUploadedFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0] || null;
    if (file) setUploadedFile(file);
  };

  const handleRun = async () => {
    setError('');

    // Validate input
    if (inputMode === 'contract' && !selectedContractId) {
      setError('Please select a contract from the list.');
      return;
    }
    if (inputMode === 'upload' && !uploadedFile) {
      setError('Please upload a contract document.');
      return;
    }
    if (inputMode === 'text' && !rawText.trim()) {
      setError('Please paste contract text.');
      return;
    }

    setStep('running');
    try {
      const data = await analyzeContract({
        contractId:     inputMode === 'contract' ? selectedContractId : null,
        document:       inputMode === 'upload'   ? uploadedFile       : null,
        rawText:        inputMode === 'text'     ? rawText            : null,
        jurisdiction,
        contractValue:  parseFloat(contractValue) || 500000,
        durationMonths: parseInt(durationMonths) || 12,
      });
      setResult(data);
      setStep('result');
      setActiveTab('overview');
    } catch (err) {
      setError(err?.response?.data?.error || err?.message || 'Pipeline failed.');
      setStep('config');
    }
  };

  const handleReset = () => {
    setStep('config');
    setResult(null);
    setError('');
    setUploadedFile(null);
  };

  const decStyle = result ? (DECISION_STYLE[result.decision] || DECISION_STYLE.RENEGOTIATE) : null;

  // ── Config screen ────────────────────────────────────────────────────────

  if (step === 'config') {
    return (
      <div className="min-h-screen p-4" style={{ background: 'linear-gradient(135deg, #0d1117 0%, #0d1117 60%, #1a0533 100%)' }}>
        <div className="w-full">

          {/* Header */}
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)' }}>🧠</div>
            <div>
              <h1 className="text-2xl font-black text-white">Contract Intelligence Orchestrator</h1>
              <p className="text-gray-400 text-sm">Full AI pipeline · Legal + CFO + Negotiation + RL</p>
            </div>
          </div>

          {/* Architecture diagram */}
          <Card className="mb-6">
            <p className="text-xs text-gray-500 mb-3 font-medium uppercase tracking-wider">Pipeline Architecture</p>
            <div className="flex items-center gap-1 flex-wrap">
              {['Clause Extraction', 'Legal RAG', 'CFO Monte Carlo', 'Multi-Agent Negotiation', 'Scoring Engine', 'Recommendations', 'RL Update'].map((s, i, arr) => (
                <React.Fragment key={s}>
                  <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold"
                    style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                    {STEP_ICON[i]} {s}
                  </div>
                  {i < arr.length - 1 && <span className="text-gray-600 text-xs">→</span>}
                </React.Fragment>
              ))}
            </div>
          </Card>

          {/* Config form */}
          <Card>
            <h2 className="text-white font-bold text-lg mb-5">Configure Analysis</h2>

            {/* Input mode tabs */}
            <div className="flex gap-2 mb-5 p-1 rounded-xl" style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)' }}>
              {INPUT_TABS.map(t => (
                <button key={t.id} onClick={() => { setInputMode(t.id); setError(''); }}
                  className="flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-all"
                  style={inputMode === t.id
                    ? { background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', color: '#fff' }
                    : { color: '#6b7280' }}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Input mode: Contract selector */}
            {inputMode === 'contract' && (
              <div className="mb-4">
                <label className="text-xs text-gray-400 mb-1.5 block font-medium">Select Contract</label>
                <input
                  value={contractSearch}
                  onChange={e => setContractSearch(e.target.value)}
                  placeholder="Search by name or ID…"
                  className="w-full rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 mb-2"
                  style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)' }}
                />
                {contractsLoading ? (
                  <p className="text-xs text-gray-500 py-3 text-center">Loading contracts…</p>
                ) : filteredContracts.length === 0 ? (
                  <p className="text-xs text-gray-500 py-3 text-center">
                    {contracts.length === 0 ? 'No contracts found in database.' : 'No matches.'}
                  </p>
                ) : (
                  <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                    {filteredContracts.map(c => {
                      const cid = c.id || c.contract_id;
                      const label = c.title || c.name || c.contract_name || cid;
                      const sub = c.contract_type || c.type || '';
                      const selected = selectedContractId === cid;
                      return (
                        <button key={cid} onClick={() => setSelectedContractId(cid)}
                          className="w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between transition-all"
                          style={selected
                            ? { background: 'rgba(6,182,212,0.12)', border: '1px solid rgba(6,182,212,0.4)' }
                            : { background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.08)' }}>
                          <div>
                            <p className="text-sm font-semibold" style={{ color: selected ? '#06b6d4' : '#e5e7eb' }}>{label}</p>
                            {sub && <p className="text-xs text-gray-500">{sub}</p>}
                          </div>
                          {selected && <span className="text-cyan-400 text-sm">✓</span>}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Input mode: File upload */}
            {inputMode === 'upload' && (
              <div className="mb-4">
                <label className="text-xs text-gray-400 mb-1.5 block font-medium">Upload Contract Document</label>
                <div
                  onDrop={handleDrop}
                  onDragOver={e => e.preventDefault()}
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-xl p-6 text-center cursor-pointer transition-all"
                  style={{
                    background: uploadedFile ? 'rgba(16,185,129,0.06)' : 'rgba(99,102,241,0.04)',
                    border: uploadedFile ? '2px solid rgba(16,185,129,0.4)' : '2px dashed rgba(99,102,241,0.2)',
                  }}>
                  <input ref={fileInputRef} type="file" accept=".txt,.pdf,.md,.rst" className="hidden" onChange={handleFileChange} />
                  {uploadedFile ? (
                    <>
                      <p className="text-2xl mb-1">📄</p>
                      <p className="text-sm font-semibold text-emerald-400">{uploadedFile.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
                      <button
                        onClick={e => { e.stopPropagation(); setUploadedFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                        className="mt-2 text-xs text-gray-500 hover:text-red-400 transition-colors">
                        Remove file
                      </button>
                    </>
                  ) : (
                    <>
                      <p className="text-2xl mb-2">📤</p>
                      <p className="text-sm text-gray-400">Drag & drop or click to select</p>
                      <p className="text-xs text-gray-600 mt-1">Supports .txt, .pdf, .md</p>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Input mode: Raw text */}
            {inputMode === 'text' && (
              <div className="mb-4">
                <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract / Clause Text</label>
                <textarea rows={7} value={rawText} onChange={e => setRawText(e.target.value)}
                  placeholder="Paste full contract text or individual clauses here…"
                  className="w-full rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }} />
              </div>
            )}

            {/* Jurisdiction + numeric params */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-xs text-gray-400 mb-1.5 block font-medium">Jurisdiction</label>
                <div className="flex gap-2">
                  {[['india', '🇮🇳', 'India'], ['us', '🇺🇸', 'US'], ['uk', '🇬🇧', 'UK']].map(([v, f, l]) => (
                    <button key={v} onClick={() => setJurisdiction(v)}
                      className="flex-1 py-2 rounded-xl text-xs font-semibold transition-all"
                      style={jurisdiction === v
                        ? { background: 'rgba(6,182,212,0.15)', border: '1px solid rgba(6,182,212,0.4)', color: '#06b6d4' }
                        : { background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)', color: '#6b7280' }}>
                      {f} {l}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1.5 block font-medium">Contract Value (USD)</label>
                <input type="number" value={contractValue} onChange={e => setContractValue(e.target.value)}
                  className="w-full rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                  style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)' }} />
              </div>
            </div>

            <div className="mb-5">
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">Duration (months)</label>
              <input type="number" value={durationMonths} onChange={e => setDurationMonths(e.target.value)}
                className="w-full rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)' }} />
            </div>

            {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

            <button onClick={handleRun}
              className="w-full py-3 rounded-xl font-black text-white text-base flex items-center justify-center gap-2 transition-all"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 30px rgba(6,182,212,0.3)' }}>
              🧠 Run Full AI Analysis Pipeline
            </button>
          </Card>
        </div>
      </div>
    );
  }

  // ── Running screen ───────────────────────────────────────────────────────

  if (step === 'running') {
    return (
      <div className="min-h-screen flex items-center justify-center p-6"
        style={{ background: 'linear-gradient(135deg, #0d1117 0%, #0d1117 60%, #1a0533 100%)' }}>
        <div className="text-center max-w-lg">
          <div className="w-20 h-20 mx-auto mb-6 rounded-3xl flex items-center justify-center text-4xl animate-pulse"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', boxShadow: '0 0 40px rgba(6,182,212,0.4)' }}>
            🧠
          </div>
          <h2 className="text-2xl font-black text-white mb-2">Running Pipeline…</h2>
          <p className="text-gray-400 mb-8 text-sm">
            Legal reasoning · CFO simulation · Multi-agent negotiation
          </p>
          <div className="space-y-3 text-left">
            {['Extracting clauses', 'Running legal RAG analysis', 'Running CFO Monte Carlo', 'Negotiating high-risk clauses', 'Computing final score', 'Generating recommendations'].map((s, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-xl"
                style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.1)' }}>
                <span className="w-4 h-4 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin flex-shrink-0" />
                <span className="text-sm text-gray-400">{s}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Result screen ────────────────────────────────────────────────────────

  const tabs = [
    { id: 'overview',        label: '🎯 Overview' },
    { id: 'legal',           label: '⚖️ Legal Risks' },
    { id: 'financial',       label: '📊 Financial' },
    { id: 'negotiation',     label: '🤝 Negotiation' },
    { id: 'pipeline',        label: '🔄 Pipeline' },
    { id: 'recommendations', label: '💡 Actions' },
  ];

  return (
    <div className="min-h-screen p-4" style={{ background: 'linear-gradient(135deg, #0d1117 0%, #0d1117 60%, #1a0533 100%)' }}>
      <div className="w-full">

        {/* ── Top bar ── */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #06b6d4)' }}>🧠</div>
            <div>
              <h1 className="text-xl font-black text-white">Contract Intelligence Analysis</h1>
              <p className="text-xs text-gray-500">
                ID: {result?.analysis_id?.slice(0, 8)} · {result?.total_duration_ms?.toFixed(0)}ms ·
                {result?.input_source && <span className="ml-1 text-indigo-400">{result.input_source.replace(/_/g, ' ')}</span>}
              </p>
            </div>
          </div>
          <button onClick={handleReset}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-gray-400 transition-all"
            style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
            ← New Analysis
          </button>
        </div>

        {/* ── Decision hero ── */}
        {decStyle && (
          <div className="rounded-2xl p-6 mb-6 flex items-center justify-between flex-wrap gap-4"
            style={{ background: decStyle.bg, border: decStyle.border }}>
            <div className="flex items-center gap-4">
              <span className="text-5xl">{decStyle.icon}</span>
              <div>
                <p className="text-xs font-medium uppercase tracking-widest mb-1" style={{ color: decStyle.color }}>Final Decision</p>
                <p className="text-3xl font-black" style={{ color: decStyle.color }}>{decStyle.label}</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <ScoreRing score={result.final_score} size={90} />
              <div className="space-y-2 min-w-40">
                {[
                  ['Legal', result.score_breakdown?.legal_score, '#a5b4fc'],
                  ['Financial', result.score_breakdown?.financial_score, '#6ee7b7'],
                  ['Negotiation', result.score_breakdown?.negotiation_score, '#fbbf24'],
                ].map(([label, val, color]) => (
                  <div key={label}>
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-gray-400">{label}</span>
                      <span style={{ color }}>{val?.toFixed(1)}</span>
                    </div>
                    <MiniBar value={val || 0} max={100} color={color} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Risk summary pills ── */}
        {result?.risk_summary && (
          <div className="flex gap-3 mb-6 flex-wrap">
            {[
              ['CRITICAL', result.risk_summary.critical, '#fca5a5'],
              ['HIGH',     result.risk_summary.high,     '#f87171'],
              ['MEDIUM',   result.risk_summary.medium,   '#fbbf24'],
              ['LOW',      result.risk_summary.low,      '#6ee7b7'],
            ].map(([label, count, color]) => (
              <div key={label} className="px-4 py-2 rounded-xl flex items-center gap-2"
                style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.12)' }}>
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
                <span className="text-xs text-gray-400">{label}</span>
                <span className="text-sm font-black" style={{ color }}>{count}</span>
              </div>
            ))}
            <div className="px-4 py-2 rounded-xl flex items-center gap-2"
              style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.12)' }}>
              <span className="text-xs text-gray-400">Avg Confidence</span>
              <span className="text-sm font-black text-indigo-300">
                {(result.risk_summary.avg_confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}

        {/* ── Tabs ── */}
        <div className="flex gap-1 mb-5 p-1.5 rounded-2xl overflow-x-auto"
          style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)' }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className="flex-shrink-0 py-2 px-4 rounded-xl text-xs font-semibold transition-all"
              style={activeTab === t.id
                ? { background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', color: '#fff' }
                : { color: '#6b7280' }}>
              {t.label}
            </button>
          ))}
        </div>

        {/* ── Tab: Overview ── */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-3 gap-5">
            <div className="col-span-2">
              <Card>
                <h3 className="text-white font-bold mb-4">Top Recommendations</h3>
                <div className="space-y-3">
                  {(result?.recommendations || []).slice(0, 5).map((rec, i) => {
                    const rc = REC_COLORS[rec.priority] || REC_COLORS.MEDIUM;
                    return (
                      <div key={i} className="rounded-xl p-4" style={{ background: rc.bg, border: rc.border }}>
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <span className="text-sm font-semibold text-white">{rec.title}</span>
                          <span className="text-xs px-2 py-0.5 rounded-full font-bold flex-shrink-0"
                            style={{ background: rc.badge, color: rc.badgeText }}>{rec.priority}</span>
                        </div>
                        <p className="text-xs text-gray-400 mb-2">{rec.detail?.slice(0, 180)}</p>
                        {rec.action && <p className="text-xs font-medium" style={{ color: '#06b6d4' }}>→ {rec.action}</p>}
                      </div>
                    );
                  })}
                </div>
              </Card>
            </div>
            <div className="space-y-4">
              <Card>
                <h3 className="text-white font-bold mb-3">Score Breakdown</h3>
                <div className="flex justify-center mb-4">
                  <ScoreRing score={result?.final_score || 0} size={100} />
                </div>
                <div className="space-y-2">
                  {[
                    ['Legal', result?.score_breakdown?.legal_score, '#a5b4fc', '40%'],
                    ['Financial', result?.score_breakdown?.financial_score, '#6ee7b7', '35%'],
                    ['Negotiation', result?.score_breakdown?.negotiation_score, '#fbbf24', '25%'],
                  ].map(([lbl, val, color, weight]) => (
                    <div key={lbl}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-400">{lbl} <span className="text-gray-600">·{weight}</span></span>
                        <span className="font-bold" style={{ color }}>{val?.toFixed(1)}/100</span>
                      </div>
                      <MiniBar value={val || 0} max={100} color={color} />
                    </div>
                  ))}
                </div>
              </Card>
              <Card>
                <h3 className="text-white font-bold mb-3">Financial Snapshot</h3>
                <div className="space-y-2 text-sm">
                  {[
                    ['Contract Value',  `$${Number(result?.cfo_result?.contract_value || 0).toLocaleString()}`],
                    ['Expected Margin', `$${Number(result?.cfo_result?.expected_margin || 0).toLocaleString()} (${(result?.cfo_result?.mean_margin_pct || 0).toFixed(1)}%)`],
                    ['VaR (95%)',       `$${Math.abs(result?.cfo_result?.var_95 || 0).toLocaleString()}`],
                    ['Loss Prob',       `${(result?.cfo_result?.loss_probability_pct || 0).toFixed(1)}%`],
                  ].map(([label, val]) => (
                    <div key={label} className="flex justify-between">
                      <span className="text-gray-400">{label}</span>
                      <span className="font-semibold text-gray-200 text-right ml-2">{val}</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-600 mt-2">
                  {result?.cfo_result?.n_simulations > 0
                    ? `${result.cfo_result.n_simulations.toLocaleString()}-path Monte Carlo`
                    : 'Rule-based estimate'}
                </p>
              </Card>
            </div>
          </div>
        )}

        {/* ── Tab: Legal Risks ── */}
        {activeTab === 'legal' && (
          <div className="space-y-3">
            {(result?.legal_risks || []).map((risk, i) => (
              <Card key={i}>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-bold text-white">{risk.clause_title}</span>
                    {risk.clause_type && risk.clause_type !== 'general' && (
                      <span className="text-xs px-2 py-0.5 rounded-full"
                        style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                        {risk.clause_type.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                  <RiskBadge level={risk.risk_level} />
                </div>
                <p className="text-xs text-gray-400 mb-3 leading-relaxed">{risk.explanation?.slice(0, 300)}</p>
                {risk.issues?.length > 0 && (
                  <div className="space-y-2 mb-3">
                    {risk.issues.slice(0, 2).map((issue, j) => (
                      <div key={j} className="rounded-lg p-2.5"
                        style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.1)' }}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold text-white">{issue.issue || issue.reason}</span>
                          {issue.severity && <RiskBadge level={issue.severity} />}
                        </div>
                        {issue.law_reference && <p className="text-xs text-indigo-300">📜 {issue.law_reference}</p>}
                        {issue.case_reference && !issue.case_reference.toLowerCase().includes('consult') && (
                          <p className="text-xs text-purple-300">⚖️ {issue.case_reference}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {risk.suggested_clause && risk.suggested_clause !== risk.clause_text && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1 font-medium uppercase tracking-wider">Suggested Rewrite</p>
                    <p className="text-xs text-gray-300 font-mono leading-relaxed p-2 rounded-lg"
                      style={{ background: 'rgba(16,185,129,0.04)', border: '1px solid rgba(16,185,129,0.15)' }}>
                      {risk.suggested_clause.slice(0, 300)}
                    </p>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}

        {/* ── Tab: Financial ── */}
        {activeTab === 'financial' && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-5">
              {/* Monte Carlo simulation metrics */}
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white font-bold">Monte Carlo Results</h3>
                  <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
                    style={{ background: result?.cfo_result?.simulation_source === 'monte_carlo' ? 'rgba(16,185,129,0.15)' : 'rgba(234,179,8,0.15)', color: result?.cfo_result?.simulation_source === 'monte_carlo' ? '#6ee7b7' : '#fbbf24' }}>
                    {result?.cfo_result?.n_simulations > 0 ? `${result.cfo_result.n_simulations.toLocaleString()} runs` : 'Rule-based'}
                  </span>
                </div>
                <div className="space-y-3">
                  {[
                    ['Contract Value',    `$${Number(result?.cfo_result?.contract_value || 0).toLocaleString()}`,                      '#a5b4fc'],
                    ['Expected Margin',   `$${Number(result?.cfo_result?.expected_margin || 0).toLocaleString()}`,                     '#6ee7b7'],
                    ['Mean Margin %',     `${(result?.cfo_result?.mean_margin_pct || 0).toFixed(1)}%`,                                 '#6ee7b7'],
                    ['VaR (95%)',         `$${Math.abs(result?.cfo_result?.var_95 || 0).toLocaleString()}`,                            '#fbbf24'],
                    ['Max Loss (P1)',     `$${Math.abs(result?.cfo_result?.max_loss || 0).toLocaleString()}`,                          '#f87171'],
                    ['Loss Probability',  `${(result?.cfo_result?.loss_probability_pct || 0).toFixed(1)}%`,                           result?.cfo_result?.loss_probability_pct > 30 ? '#f87171' : '#fbbf24'],
                    ['Margin Std Dev',    `${(result?.cfo_result?.std_deviation_pct || 0).toFixed(1)}%`,                              '#9ca3af'],
                    ['Delay Probability', `${((result?.cfo_result?.delay_probability || 0) * 100).toFixed(0)}%`,                      '#fbbf24'],
                  ].map(([label, val, color]) => (
                    <div key={label} className="flex items-center justify-between py-1.5"
                      style={{ borderBottom: '1px solid rgba(99,102,241,0.06)' }}>
                      <span className="text-sm text-gray-400">{label}</span>
                      <span className="text-sm font-bold" style={{ color }}>{val}</span>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Risk insights from simulation */}
              <Card>
                <h3 className="text-white font-bold mb-4">Financial Risk Insights</h3>
                <div className="space-y-3">
                  {(result?.cfo_result?.risk_insights || []).map((ins, i) => (
                    <div key={i} className="flex items-start gap-2 p-3 rounded-xl"
                      style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.1)' }}>
                      <span className="text-yellow-400 flex-shrink-0 mt-0.5">⚡</span>
                      <p className="text-sm text-gray-300 leading-relaxed">
                        {typeof ins === 'string' ? ins : ins?.finding || ins?.title || ins?.message || JSON.stringify(ins)}
                      </p>
                    </div>
                  ))}
                  {!result?.cfo_result?.risk_insights?.length && (
                    <p className="text-gray-500 text-sm">No risk insights generated.</p>
                  )}
                </div>

                {/* Penalty stats if available */}
                {result?.cfo_result?.penalty_stats && Object.keys(result.cfo_result.penalty_stats).length > 0 && (
                  <div className="mt-4 pt-4" style={{ borderTop: '1px solid rgba(99,102,241,0.1)' }}>
                    <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Penalty Statistics</p>
                    <div className="space-y-1.5">
                      {[
                        ['Avg Penalty', `$${Number(result.cfo_result.penalty_stats.mean_penalty || 0).toLocaleString()}`],
                        ['P99 Penalty', `$${Number(result.cfo_result.penalty_stats.max_penalty_p99 || 0).toLocaleString()}`],
                        ['Delay Rate',  `${(result.cfo_result.penalty_stats.delay_rate_pct || 0).toFixed(0)}% of paths`],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between text-xs">
                          <span className="text-gray-500">{k}</span>
                          <span className="text-orange-300 font-semibold">{v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            </div>

            {/* Financial score bar */}
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white font-bold">Financial Health Score</h3>
                <span className="text-lg font-black" style={{ color: result?.score_breakdown?.financial_score >= 60 ? '#6ee7b7' : result?.score_breakdown?.financial_score >= 40 ? '#fbbf24' : '#f87171' }}>
                  {result?.score_breakdown?.financial_score?.toFixed(1)}/100
                </span>
              </div>
              <MiniBar value={result?.score_breakdown?.financial_score || 0} max={100}
                color={result?.score_breakdown?.financial_score >= 60 ? '#10b981' : result?.score_breakdown?.financial_score >= 40 ? '#f59e0b' : '#ef4444'} />
              <p className="text-xs text-gray-600 mt-2">
                Derived from mean margin ({(result?.cfo_result?.mean_margin_pct || 0).toFixed(1)}%),
                loss probability ({(result?.cfo_result?.loss_probability_pct || 0).toFixed(1)}%),
                and 95% VaR tail — weighted 35% of final score.
              </p>
            </Card>
          </div>
        )}

        {/* ── Tab: Negotiation ── */}
        {activeTab === 'negotiation' && (
          <div className="space-y-4">
            {(result?.negotiation_results || []).length === 0 ? (
              <Card>
                <p className="text-gray-400 text-sm">No clauses were negotiated (no HIGH/CRITICAL risk clauses found, or negotiation engine unavailable).</p>
              </Card>
            ) : (result?.negotiation_results || []).map((neg, i) => (
              <Card key={i}>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="text-sm font-bold text-white">{neg.clause_title}</span>
                    <p className="text-xs text-gray-500 mt-0.5">Original risk: <RiskBadge level={neg.original_risk} /></p>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-black" style={{ color: neg.final_score >= 0.65 ? '#6ee7b7' : '#fbbf24' }}>
                      {(neg.final_score * 100).toFixed(0)}
                    </div>
                    <div className="text-xs text-gray-500">Final Score</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 mb-3 text-xs">
                  {[['Rounds', neg.rounds], ['Converged', neg.converged ? 'Yes' : 'No'], ['Trend', neg.score_trend]].map(([k, v]) => (
                    <div key={k} className="p-2 rounded-lg text-center" style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.1)' }}>
                      <div className="text-gray-400 mb-1">{k}</div>
                      <div className="font-bold text-white capitalize">{v}</div>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1 font-medium uppercase tracking-wider">Best Negotiated Clause</p>
                  <p className="text-xs text-gray-300 font-mono leading-relaxed p-3 rounded-xl"
                    style={{ background: 'rgba(16,185,129,0.04)', border: '1px solid rgba(16,185,129,0.15)', whiteSpace: 'pre-wrap' }}>
                    {neg.best_clause}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* ── Tab: Pipeline Trace ── */}
        {activeTab === 'pipeline' && (
          <Card>
            <h3 className="text-white font-bold mb-4">Pipeline Execution Trace</h3>
            <PipelineSteps trace={result?.pipeline_trace} />
            <div className="mt-4 pt-4 flex items-center justify-between text-xs text-gray-500"
              style={{ borderTop: '1px solid rgba(99,102,241,0.1)' }}>
              <span>Total: {result?.total_duration_ms?.toFixed(0)}ms</span>
              <span>{result?.created_at ? new Date(result.created_at).toLocaleString() : ''}</span>
            </div>
          </Card>
        )}

        {/* ── Tab: Recommendations ── */}
        {activeTab === 'recommendations' && (
          <div className="space-y-3">
            {(result?.recommendations || []).map((rec, i) => {
              const rc = REC_COLORS[rec.priority] || REC_COLORS.MEDIUM;
              return (
                <Card key={i}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-base">
                        {rec.type === 'legal' ? '⚖️' : rec.type === 'financial' ? '📊' : rec.type === 'negotiation' ? '🤝' : rec.type === 'decision' ? '🎯' : '🏗️'}
                      </span>
                      <span className="text-sm font-bold text-white">{rec.title}</span>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold flex-shrink-0"
                      style={{ background: rc.badge, color: rc.badgeText }}>{rec.priority}</span>
                  </div>
                  <p className="text-sm text-gray-400 mb-2 leading-relaxed">{rec.detail}</p>
                  {rec.law_reference && <p className="text-xs text-indigo-300 mb-1">📜 {rec.law_reference}</p>}
                  {rec.case_reference && !rec.case_reference?.toLowerCase().includes('consult') && (
                    <p className="text-xs text-purple-300 mb-1">⚖️ {rec.case_reference}</p>
                  )}
                  {rec.action && (
                    <div className="mt-2 px-3 py-2 rounded-lg flex items-center gap-2"
                      style={{ background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.15)' }}>
                      <span className="text-xs text-cyan-400">→</span>
                      <span className="text-xs text-cyan-300 font-medium">{rec.action}</span>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrchestratorDashboard;
