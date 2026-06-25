import React, { useState, useRef } from 'react';
import { uploadVoiceContract, uploadDocument, parseEmail } from '../services/multiModalService';

const TABS = [
  { id: 'voice',    label: '🎙️ Voice Contracts' },
  { id: 'document', label: '📄 Document Scanner' },
  { id: 'email',    label: '✉️ Email Parser' },
];

// ─── Design tokens ────────────────────────────────────────────────

const glassCard = {
  background: 'rgba(13, 17, 23, 0.8)',
  border: '1px solid rgba(99, 102, 241, 0.15)',
  backdropFilter: 'blur(20px)',
};

// ─── Reusable UI Components ───────────────────────────────────────

const Card = ({ children, className = '', style = {} }) => (
  <div
    className={`rounded-2xl p-5 transition-all duration-200 ${className}`}
    style={{ ...glassCard, ...style }}
    onMouseEnter={(e) => { e.currentTarget.style.border = '1px solid rgba(99,102,241,0.35)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(99,102,241,0.06)'; }}
    onMouseLeave={(e) => { e.currentTarget.style.border = '1px solid rgba(99,102,241,0.15)'; e.currentTarget.style.boxShadow = 'none'; }}
  >
    {children}
  </div>
);

const Button = ({ onClick, disabled, loading, children, variant = 'primary', className = '' }) => {
  const base = 'px-4 py-2 rounded-xl font-semibold transition-all duration-200 flex items-center gap-2 text-sm disabled:opacity-50';
  const variants = {
    primary: { background: 'linear-gradient(135deg, #7c3aed, #06b6d4)', color: '#fff', boxShadow: '0 0 16px rgba(6,182,212,0.25)' },
    outline: { background: 'transparent', border: '1px solid rgba(99,102,241,0.3)', color: '#9ca3af' },
    success: { background: 'linear-gradient(135deg, #059669, #10b981)', color: '#fff' },
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

const Badge = ({ children, color = 'cyan' }) => {
  const colors = {
    cyan:   { background: 'rgba(6,182,212,0.1)',   border: '1px solid rgba(6,182,212,0.25)',   color: '#67e8f9' },
    green:  { background: 'rgba(16,185,129,0.1)',  border: '1px solid rgba(16,185,129,0.25)',  color: '#6ee7b7' },
    yellow: { background: 'rgba(234,179,8,0.1)',   border: '1px solid rgba(234,179,8,0.25)',   color: '#fde047' },
    red:    { background: 'rgba(239,68,68,0.1)',   border: '1px solid rgba(239,68,68,0.25)',   color: '#fca5a5' },
    purple: { background: 'rgba(139,92,246,0.1)',  border: '1px solid rgba(139,92,246,0.25)',  color: '#c4b5fd' },
    blue:   { background: 'rgba(59,130,246,0.1)',  border: '1px solid rgba(59,130,246,0.25)',  color: '#93c5fd' },
    orange: { background: 'rgba(249,115,22,0.1)',  border: '1px solid rgba(249,115,22,0.25)',  color: '#fdba74' },
  };
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold" style={colors[color] || colors.cyan}>
      {children}
    </span>
  );
};

const KPICard = ({ label, value, colorClass = 'text-cyan-400', icon = '' }) => (
  <div className="rounded-2xl p-4 text-center" style={{ background: 'rgba(13,17,23,0.9)', border: '1px solid rgba(99,102,241,0.15)' }}>
    {icon && <div className="text-xl mb-1">{icon}</div>}
    <div className={`text-2xl font-black ${colorClass}`} style={{ textShadow: '0 0 16px currentColor' }}>{value}</div>
    <div className="text-xs text-gray-500 mt-1">{label}</div>
  </div>
);

const CLAUSE_TYPE_COLORS = {
  'Payment Terms':      'blue',
  'Liability':          'red',
  'Termination':        'yellow',
  'Indemnification':    'yellow',
  'Confidentiality':    'purple',
  'Force Majeure':      'green',
  'Governing Law':      'cyan',
  'Dispute Resolution': 'purple',
  'Warranty':           'cyan',
};

// ─── Drag & Drop File Upload ──────────────────────────────────────

const FileDropZone = ({ accept, onFile, label, hint }) => {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState('');
  const inputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) { setFileName(file.name); onFile(file); }
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) { setFileName(file.name); onFile(file); }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className="rounded-2xl p-8 text-center cursor-pointer transition-all duration-200"
      style={dragging
        ? { background: 'rgba(6,182,212,0.08)', border: '2px dashed rgba(6,182,212,0.6)', boxShadow: '0 0 20px rgba(6,182,212,0.15)' }
        : { background: 'rgba(13,17,23,0.4)', border: '2px dashed rgba(99,102,241,0.2)' }
      }
      onMouseEnter={(e) => { if (!dragging) e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)'; }}
      onMouseLeave={(e) => { if (!dragging) e.currentTarget.style.borderColor = 'rgba(99,102,241,0.2)'; }}
    >
      <input ref={inputRef} type="file" accept={accept} onChange={handleChange} className="hidden" />
      <div className="text-5xl mb-3">{label}</div>
      {fileName
        ? <p className="text-sm font-semibold" style={{ color: '#06b6d4' }}>{fileName}</p>
        : <>
            <p className="text-sm text-gray-300 mb-1 font-medium">Drag and drop or click to upload</p>
            <p className="text-xs text-gray-600">{hint}</p>
          </>
      }
    </div>
  );
};

// ─── Analysis Panel (shared across all 3 modalities) ─────────────

function decisionColor(decision) {
  if (!decision) return 'yellow';
  const d = decision.toUpperCase();
  if (d === 'APPROVE') return 'green';
  if (d === 'REJECT') return 'red';
  return 'yellow';
}

function scoreColor(score) {
  if (score == null) return 'text-gray-400';
  if (score >= 75) return 'text-emerald-400';
  if (score >= 50) return 'text-yellow-400';
  return 'text-red-400';
}

function riskLevelColor(level) {
  const l = (level || '').toUpperCase();
  if (l === 'LOW') return 'green';
  if (l === 'HIGH' || l === 'CRITICAL') return 'red';
  return 'yellow';
}

const AnalysisPanel = ({ analysis }) => {
  if (!analysis) return null;
  if (analysis.error) {
    return (
      <Card>
        <p className="text-sm text-yellow-400">⚠️ Downstream analysis unavailable: {analysis.error}</p>
      </Card>
    );
  }

  const {
    final_score, decision, score_breakdown = {},
    risk_summary = {}, cfo_result = {},
    legal_risks = [], negotiation_results = [],
    recommendations = [],
  } = analysis;

  const cfo = cfo_result?.monte_carlo?.summary || {};
  const riskCats = Object.entries(risk_summary).slice(0, 6);

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="rounded-2xl p-4 flex items-center gap-4 flex-wrap"
        style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.12), rgba(6,182,212,0.08))', border: '1px solid rgba(99,102,241,0.2)' }}>
        <div className="flex items-center gap-2">
          <span className="text-lg">🤖</span>
          <span className="text-white font-bold text-sm">AI Engine Analysis</span>
        </div>
        <div className="flex items-center gap-3 ml-auto flex-wrap">
          <div className="text-center">
            <div className={`text-3xl font-black ${scoreColor(final_score)}`} style={{ textShadow: '0 0 20px currentColor' }}>
              {final_score != null ? Math.round(final_score) : '—'}
            </div>
            <div className="text-xs text-gray-500">Overall Score</div>
          </div>
          {decision && (
            <Badge color={decisionColor(decision)}>
              {decision === 'APPROVE' ? '✅' : decision === 'REJECT' ? '❌' : '⚠️'} {decision}
            </Badge>
          )}
        </div>
      </div>

      {/* Score breakdown + Risk categories */}
      <div className="grid grid-cols-2 gap-4">
        {Object.keys(score_breakdown).length > 0 && (
          <Card>
            <h4 className="text-white font-semibold text-sm mb-3">Score Breakdown</h4>
            <div className="space-y-2">
              {Object.entries(score_breakdown).map(([key, val]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 capitalize w-24 flex-shrink-0">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(99,102,241,0.1)' }}>
                    <div className="h-full rounded-full transition-all"
                      style={{ width: `${Math.min(100, Math.max(0, Number(val) || 0))}%`, background: 'linear-gradient(90deg,#7c3aed,#06b6d4)' }} />
                  </div>
                  <span className="text-xs font-bold text-gray-300 w-8 text-right">{Math.round(Number(val) || 0)}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {riskCats.length > 0 && (
          <Card>
            <h4 className="text-white font-semibold text-sm mb-3">Risk Categories</h4>
            <div className="space-y-1.5">
              {riskCats.map(([cat, score]) => (
                <div key={cat} className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 capitalize w-28 flex-shrink-0">{cat.replace(/_/g, ' ')}</span>
                  <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(99,102,241,0.1)' }}>
                    <div className="h-full rounded-full"
                      style={{
                        width: `${Math.min(100, (Number(score) / 5) * 100)}%`,
                        background: Number(score) >= 4 ? '#ef4444' : Number(score) >= 3 ? '#eab308' : '#10b981',
                      }} />
                  </div>
                  <span className="text-xs font-bold w-6 text-right"
                    style={{ color: Number(score) >= 4 ? '#fca5a5' : Number(score) >= 3 ? '#fde047' : '#6ee7b7' }}>
                    {score}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* CFO Monte Carlo */}
      {Object.keys(cfo).length > 0 && (
        <Card>
          <h4 className="text-white font-semibold text-sm mb-3">💰 CFO Monte Carlo Simulation</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPICard
              label="Expected Margin"
              value={cfo.mean_margin != null ? `${(cfo.mean_margin * 100).toFixed(1)}%` : '—'}
              colorClass={cfo.mean_margin > 0.1 ? 'text-emerald-400' : 'text-yellow-400'}
              icon="📈"
            />
            <KPICard
              label="Value at Risk (95%)"
              value={cfo.var_95 != null ? `${(cfo.var_95 * 100).toFixed(1)}%` : '—'}
              colorClass="text-red-400"
              icon="⚠️"
            />
            <KPICard
              label="Loss Probability"
              value={cfo.loss_probability != null ? `${(cfo.loss_probability * 100).toFixed(0)}%` : '—'}
              colorClass={cfo.loss_probability < 0.2 ? 'text-emerald-400' : 'text-yellow-400'}
              icon="🎲"
            />
            <KPICard
              label="Expected Shortfall"
              value={cfo.expected_shortfall != null ? `${(cfo.expected_shortfall * 100).toFixed(1)}%` : '—'}
              colorClass="text-orange-400"
              icon="📉"
            />
          </div>
        </Card>
      )}

      {/* Legal Risks */}
      {legal_risks.length > 0 && (
        <Card>
          <h4 className="text-white font-semibold text-sm mb-3">
            ⚖️ Legal Risk Assessment <span className="text-gray-500 font-normal">({legal_risks.length} clauses)</span>
          </h4>
          <div className="space-y-2">
            {legal_risks.map((risk, i) => (
              <div key={i} className="rounded-xl p-3"
                style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.08)' }}>
                <div className="flex items-center gap-2 mb-1">
                  <Badge color={riskLevelColor(risk.risk_level)}>{risk.risk_level || 'MEDIUM'}</Badge>
                  <span className="text-sm text-gray-200 font-medium">{risk.clause_title || `Clause ${i + 1}`}</span>
                  {risk.compliance_status && (
                    <Badge color={risk.compliance_status === 'COMPLIANT' ? 'green' : 'yellow'} >
                      {risk.compliance_status}
                    </Badge>
                  )}
                </div>
                {risk.explanation && (
                  <p className="text-xs text-gray-400 leading-relaxed">{risk.explanation}</p>
                )}
                {risk.suggested_clause && (
                  <div className="mt-2 px-2 py-1.5 rounded-lg text-xs text-emerald-300"
                    style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)' }}>
                    <span className="font-semibold text-emerald-400">Suggested: </span>{risk.suggested_clause}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Negotiation Results */}
      {negotiation_results.length > 0 && (
        <Card>
          <h4 className="text-white font-semibold text-sm mb-3">🤝 Multi-Agent Negotiation</h4>
          <div className="space-y-3">
            {negotiation_results.map((neg, i) => (
              <div key={i} className="rounded-xl p-3"
                style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.08)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs text-gray-400 font-medium">{neg.clause_title || `Clause ${i + 1}`}</span>
                  <div className="ml-auto flex items-center gap-2">
                    {neg.converged && <Badge color="green">Converged</Badge>}
                    {neg.final_score != null && (
                      <span className={`text-xs font-bold ${scoreColor(neg.final_score)}`}>
                        Score: {Math.round(neg.final_score)}
                      </span>
                    )}
                  </div>
                </div>
                {neg.best_clause && (
                  <p className="text-xs text-gray-300 leading-relaxed">{neg.best_clause}</p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <h4 className="text-white font-semibold text-sm mb-3">💡 Recommendations</h4>
          <div className="space-y-2">
            {recommendations.map((rec, i) => {
              const text = typeof rec === 'string' ? rec : (rec.text || rec.recommendation || JSON.stringify(rec));
              const priority = typeof rec === 'object' ? (rec.priority || rec.severity || '') : '';
              return (
                <div key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="mt-0.5 flex-shrink-0" style={{ color: '#a78bfa' }}>→</span>
                  <span className="leading-relaxed">
                    {priority && <Badge color={priority === 'high' ? 'red' : priority === 'medium' ? 'yellow' : 'green'} >{priority}</Badge>}
                    {priority && ' '}
                    {text}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
};

// ─── Tab 1: Voice Contracts ───────────────────────────────────────

const VoiceTab = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleUpload = async () => {
    if (!file) { setError('Please select an audio file.'); return; }
    setLoading(true);
    setError('');
    try {
      const data = await uploadVoiceContract(file);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.error || 'Voice processing failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">🎙️</span>
          <h3 className="text-white font-bold text-lg">Voice Contract Processing</h3>
        </div>
        <p className="text-gray-400 text-sm mb-5 ml-7">
          Upload an audio recording of a contract discussion. The system transcribes via Whisper,
          extracts key terms, detects clause types, and runs the full AI analysis pipeline.
        </p>
        <FileDropZone
          accept=".wav,.mp3,.m4a,.ogg,.flac"
          onFile={(f) => { setFile(f); setError(''); }}
          label="🎙️"
          hint="Accepts WAV, MP3, M4A, OGG, FLAC"
        />
        {error && <p className="mt-3 text-red-400 text-sm">{error}</p>}
        <Button onClick={handleUpload} loading={loading} disabled={!file} className="mt-4">
          🎙️ {loading ? 'Transcribing & Analyzing…' : 'Process Voice Recording'}
        </Button>
      </Card>

      {result && (
        <>
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-white font-bold">Transcription</h4>
              <div className="flex gap-2 flex-wrap">
                <Badge color="cyan">{result.word_count} words</Badge>
                <Badge color="green">{result.transcription_engine || 'transcribed'}</Badge>
                <Badge color="blue">{result.contract_type}</Badge>
              </div>
            </div>
            <div className="rounded-xl p-4 text-sm text-gray-300 leading-relaxed max-h-48 overflow-y-auto"
              style={{ background: 'rgba(99,102,241,0.04)', border: '1px solid rgba(99,102,241,0.1)' }}>
              {result.transcription}
            </div>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            <Card>
              <h4 className="text-white font-semibold mb-3 text-sm">Key Terms Extracted</h4>
              <div className="flex flex-wrap gap-2">
                {(result.key_terms || []).map((term, i) => (
                  <Badge key={i} color="cyan">{term}</Badge>
                ))}
              </div>
            </Card>
            <Card>
              <h4 className="text-white font-semibold mb-3 text-sm">Detected Clause Types</h4>
              <div className="flex flex-wrap gap-2">
                {(result.detected_clause_types || []).map((ct, i) => (
                  <Badge key={i} color={CLAUSE_TYPE_COLORS[ct] || 'cyan'}>{ct}</Badge>
                ))}
              </div>
            </Card>
          </div>

          {result.suggested_clauses?.length > 0 && (
            <Card>
              <h4 className="text-white font-semibold mb-3 text-sm">Suggested Clauses</h4>
              <div className="space-y-2">
                {result.suggested_clauses.map((sc, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-xl"
                    style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.08)' }}>
                    <Badge color={sc.priority === 'high' ? 'red' : 'yellow'}>{sc.priority}</Badge>
                    <div>
                      <p className="text-sm font-semibold text-white">{sc.clause_type}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{sc.suggestion}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <AnalysisPanel analysis={result.analysis} />
        </>
      )}
    </div>
  );
};

// ─── Tab 2: Document Scanner ──────────────────────────────────────

const DocumentTab = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleUpload = async () => {
    if (!file) { setError('Please select a document file.'); return; }
    setLoading(true);
    setError('');
    try {
      const data = await uploadDocument(file);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.error || 'Document scanning failed.');
    } finally {
      setLoading(false);
    }
  };

  const confidenceColor = (score) => {
    if (score >= 0.85) return 'text-emerald-400';
    if (score >= 0.6)  return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">📄</span>
          <h3 className="text-white font-bold text-lg">Document Scanner & OCR</h3>
        </div>
        <p className="text-gray-400 text-sm mb-5 ml-7">
          Upload a scanned contract image or PDF. Text is extracted via pdfplumber or OCR,
          then piped through risk scoring, CFO simulation, and negotiation engines.
        </p>
        <FileDropZone
          accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
          onFile={(f) => { setFile(f); setError(''); }}
          label="📄"
          hint="Accepts PDF, PNG, JPG, TIFF, BMP"
        />
        {error && <p className="mt-3 text-red-400 text-sm">{error}</p>}
        <Button onClick={handleUpload} loading={loading} disabled={!file} className="mt-4">
          🔍 {loading ? 'Scanning & Analyzing…' : 'Scan Document'}
        </Button>
      </Card>

      {result && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <KPICard
              label="Confidence Score"
              value={`${Math.round(result.confidence_score * 100)}%`}
              colorClass={confidenceColor(result.confidence_score)}
              icon="🎯"
            />
            <KPICard label="Characters Extracted" value={(result.total_characters || 0).toLocaleString()} colorClass="text-cyan-400" icon="📝" />
            <KPICard label="Clauses Detected" value={result.clauses_detected?.length || 0} colorClass="text-blue-400" icon="🔍" />
          </div>

          <Card>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-white font-semibold text-sm">Extracted Text</h4>
              <div className="flex gap-2">
                <Badge color="cyan">{result.file_type?.toUpperCase()}</Badge>
                <Badge color="green">{result.extraction_method}</Badge>
              </div>
            </div>
            <div className="rounded-xl p-4 text-xs text-gray-300 font-mono leading-relaxed max-h-64 overflow-y-auto whitespace-pre-wrap"
              style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)' }}>
              {result.extracted_text}
            </div>
          </Card>

          {result.clauses_detected?.length > 0 && (
            <Card>
              <h4 className="text-white font-semibold mb-4 text-sm">
                Detected Clauses <span className="text-gray-500 font-normal">({result.clauses_detected.length})</span>
              </h4>
              <div className="space-y-3">
                {result.clauses_detected.map((clause, i) => (
                  <div key={i} className="rounded-xl p-3"
                    style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.08)' }}>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge color={CLAUSE_TYPE_COLORS[clause.clause_type] || 'cyan'}>{clause.clause_type}</Badge>
                      <div className="ml-auto flex items-center gap-2">
                        <div className="h-1.5 rounded-full overflow-hidden" style={{ width: 60, background: 'rgba(99,102,241,0.1)' }}>
                          <div className="h-full rounded-full" style={{ width: `${clause.confidence * 100}%`, background: 'linear-gradient(90deg, #7c3aed, #06b6d4)' }} />
                        </div>
                        <span className={`text-xs font-bold ${confidenceColor(clause.confidence)}`}>
                          {Math.round(clause.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed">{clause.text_snippet}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <AnalysisPanel analysis={result.analysis} />
        </>
      )}
    </div>
  );
};

// ─── Tab 3: Email Parser ──────────────────────────────────────────

const EmailTab = () => {
  const [emailText, setEmailText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleParse = async () => {
    if (!emailText.trim()) { setError('Please enter email content.'); return; }
    setLoading(true);
    setError('');
    try {
      const data = await parseEmail(emailText);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.error || 'Email parsing failed.');
    } finally {
      setLoading(false);
    }
  };

  const SAMPLE_EMAIL = `From: john.smith@acme.com
To: procurement@supplier.com
Subject: Supply Agreement – Q2 2026

Dear Team,

This is to confirm our agreement for the supply of 500 units of industrial components
worth USD 75,000 by March 31, 2026. Payment shall be made within 30 days of delivery
and acceptance.

Both parties shall keep all pricing and technical details confidential.
Either party may terminate this arrangement with 60 days written notice.
All disputes shall be resolved by arbitration under Indian law.

Please confirm your acceptance.

Best regards,
John Smith
ACME Corporation`;

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">✉️</span>
          <h3 className="text-white font-bold text-lg">Email Contract Parser</h3>
        </div>
        <p className="text-gray-400 text-sm mb-5 ml-7">
          Paste an email containing contract discussions. The AI extracts parties, obligations,
          payment terms, generates draft clauses, and runs full risk and financial analysis.
        </p>
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs text-gray-400 font-medium">Email Content *</label>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-600">{emailText.length} chars</span>
              <button
                onClick={() => setEmailText(SAMPLE_EMAIL)}
                className="text-xs font-medium transition-colors"
                style={{ color: '#06b6d4' }}
                onMouseEnter={(e) => e.currentTarget.style.color = '#67e8f9'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#06b6d4'}
              >
                Load sample email →
              </button>
            </div>
          </div>
          <textarea
            rows={10}
            value={emailText}
            onChange={(e) => setEmailText(e.target.value)}
            placeholder="Paste the email content here…"
            className="w-full rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none font-mono transition-all"
            style={{ background: 'rgba(13,17,23,0.8)', border: '1px solid rgba(99,102,241,0.2)', color: '#e5e7eb' }}
          />
        </div>
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <div className="flex gap-3">
          <Button onClick={handleParse} loading={loading} disabled={!emailText.trim()}>
            ✉️ {loading ? 'Parsing & Analyzing…' : 'Parse Email'}
          </Button>
          <Button variant="outline" onClick={() => { setEmailText(''); setResult(null); }}>
            Clear
          </Button>
        </div>
      </Card>

      {result && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KPICard label="Parties Detected" value={result.parties?.length || 0} colorClass="text-cyan-400" icon="👥" />
            <KPICard label="Obligations" value={result.obligations?.length || 0} colorClass="text-emerald-400" icon="📋" />
            <KPICard label="Draft Clauses" value={result.draft_clauses?.length || 0} colorClass="text-blue-400" icon="📝" />
            <KPICard label="Words Parsed" value={result.word_count} colorClass="text-purple-400" icon="📊" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Card>
              <h4 className="text-white font-semibold mb-3 text-sm">Detected Parties</h4>
              {result.parties?.length > 0 ? (
                <div className="space-y-2">
                  {result.parties.map((party, i) => (
                    <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-xl"
                      style={{ background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.08)' }}>
                      <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-black"
                        style={{ background: 'rgba(6,182,212,0.15)', color: '#06b6d4', border: '1px solid rgba(6,182,212,0.25)' }}>
                        {typeof party === 'string' ? party[0]?.toUpperCase() : 'P'}
                      </span>
                      <span className="text-sm text-gray-300">
                        {typeof party === 'string' ? party : JSON.stringify(party)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-sm">No parties detected</p>
              )}

              {result.payment_terms && (
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Payment Terms</p>
                  <div className="px-3 py-2 rounded-xl" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
                    <p className="text-sm text-emerald-300">{result.payment_terms}</p>
                  </div>
                </div>
              )}
            </Card>

            <Card>
              <h4 className="text-white font-semibold mb-3 text-sm">Key Obligations</h4>
              {result.obligations?.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {result.obligations.map((ob, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-gray-300 leading-relaxed">
                      <span className="mt-0.5 flex-shrink-0" style={{ color: '#06b6d4' }}>•</span>
                      <span>{ob}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-sm">No explicit obligations found</p>
              )}

              {result.key_dates?.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Key Dates</p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.key_dates.map((date, i) => (
                      <Badge key={i} color="yellow">{date}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </div>

          <Card>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-white font-semibold text-sm">
                Draft Contract Clauses <span className="text-gray-500 font-normal">({result.draft_clauses?.length || 0})</span>
              </h4>
              <Badge color="blue">{result.suggested_contract_type}</Badge>
            </div>
            <div className="space-y-3">
              {(result.draft_clauses || []).map((clause, i) => (
                <div key={i} className="rounded-xl p-4"
                  style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.08)' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge color={CLAUSE_TYPE_COLORS[clause.clause_type] || 'cyan'}>{clause.clause_type}</Badge>
                  </div>
                  <p className="text-sm text-gray-300 leading-relaxed">{clause.draft_text}</p>
                </div>
              ))}
            </div>
          </Card>

          {result.amounts_detected?.length > 0 && (
            <Card>
              <h4 className="text-white font-semibold mb-3 text-sm">💰 Financial Values Detected</h4>
              <div className="flex flex-wrap gap-2">
                {result.amounts_detected.map((amount, i) => (
                  <Badge key={i} color="green">{amount}</Badge>
                ))}
              </div>
            </Card>
          )}

          <AnalysisPanel analysis={result.analysis} />
        </>
      )}
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────

export default function MultiModalAI() {
  const [activeTab, setActiveTab] = useState('voice');

  return (
    <div className="min-h-screen text-gray-100 p-6" style={{ background: 'linear-gradient(135deg, #0a0f1e 0%, #0d1117 50%, #111827 100%)' }}>
      {/* Subtle grid overlay */}
      <div className="fixed inset-0 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px)',
        backgroundSize: '60px 60px',
        zIndex: 0,
      }} />

      <div className="max-w-5xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-xl"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #a855f7)', boxShadow: '0 0 30px rgba(139,92,246,0.35)' }}>
              🎤
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight"
                style={{ background: 'linear-gradient(135deg, #a78bfa, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Multi-Modal AI
              </h1>
              <p className="text-gray-500 text-sm mt-0.5">Voice, Document & Email → Risk Scoring + CFO + Negotiation</p>
            </div>
            <div className="ml-auto flex items-center gap-3">
              <span className="text-xs px-3 py-1.5 rounded-full font-semibold flex items-center gap-1.5"
                style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.3)', color: '#a78bfa' }}>
                <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
                NEW
              </span>
              <span className="text-xs px-3 py-1.5 rounded-full font-semibold"
                style={{ background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)', color: '#67e8f9' }}>
                3 Modalities
              </span>
            </div>
          </div>

          {/* Tab Bar */}
          <div className="flex gap-2 p-1.5 mb-6"
            style={{ background: 'rgba(13,17,23,0.6)', border: '1px solid rgba(99,102,241,0.1)', borderRadius: 16 }}>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="flex-1 py-2 px-3 rounded-xl text-sm font-semibold transition-all duration-200"
                style={activeTab === tab.id
                  ? { background: 'linear-gradient(135deg, #7c3aed, #a855f7)', color: '#fff', boxShadow: '0 0 20px rgba(139,92,246,0.35)' }
                  : { color: '#6b7280' }
                }
                onMouseEnter={(e) => { if (activeTab !== tab.id) e.currentTarget.style.color = '#e5e7eb'; }}
                onMouseLeave={(e) => { if (activeTab !== tab.id) e.currentTarget.style.color = '#6b7280'; }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {activeTab === 'voice'    && <VoiceTab />}
        {activeTab === 'document' && <DocumentTab />}
        {activeTab === 'email'    && <EmailTab />}
      </div>
    </div>
  );
}
