import { useState } from 'react';
import { PenLine, Loader, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { clauseRewriteAPI } from '../services/advancedAI';
import useThemeStore from '../store/themeStore';

const RISK_REASONS = [
  { value: 'unlimited_liability',      label: 'Unlimited Liability' },
  { value: 'ambiguous_termination',    label: 'Ambiguous Termination' },
  { value: 'unclear_payment',          label: 'Unclear Payment Terms' },
  { value: 'no_cap_on_damages',        label: 'No Cap on Damages' },
  { value: 'missing_force_majeure',    label: 'Missing Force Majeure' },
  { value: 'one_sided_indemnity',      label: 'One-Sided Indemnity' },
  { value: 'vague_warranty',           label: 'Vague Warranty' },
];

export default function ClauseRewritePanel() {
  const { currentTheme } = useThemeStore();
  const isDark = currentTheme === 'dark';

  const [clauseText, setClauseText]   = useState('');
  const [riskReason, setRiskReason]   = useState('unlimited_liability');
  const [loading, setLoading]         = useState(false);
  const [result, setResult]           = useState(null);
  const [error, setError]             = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await clauseRewriteAPI.rewrite(clauseText, riskReason);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate rewrite');
    } finally {
      setLoading(false);
    }
  };

  // colour palette
  const card     = isDark ? 'bg-gray-800 border-gray-700'  : 'bg-white border-gray-200';
  const text     = isDark ? 'text-gray-100'                : 'text-gray-800';
  const subtext  = isDark ? 'text-gray-400'                : 'text-gray-500';
  const input    = isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400'
                         : 'bg-gray-50  border-gray-300 text-gray-800 placeholder-gray-400';
  const select   = isDark ? 'bg-gray-700 border-gray-600 text-gray-100'
                         : 'bg-gray-50  border-gray-300 text-gray-800';

  return (
    <div className="space-y-5">
      {/* Input form */}
      <form onSubmit={handleSubmit} className={`rounded-xl border p-5 ${card}`}>
        <div className="flex items-center gap-2 mb-4">
          <PenLine size={20} className="text-violet-400" />
          <h3 className={`font-semibold text-base ${text}`}>Safe Clause Rewrite</h3>
        </div>

        {/* Risk reason selector */}
        <label className={`block text-xs mb-1 ${subtext}`}>Identified Risk</label>
        <select
          value={riskReason}
          onChange={e => setRiskReason(e.target.value)}
          className={`w-full rounded-lg border px-3 py-2 text-sm mb-3 ${select}`}
        >
          {RISK_REASONS.map(r => (
            <option key={r.value} value={r.value}>{r.label}</option>
          ))}
        </select>

        {/* Clause text */}
        <label className={`block text-xs mb-1 ${subtext}`}>Original Clause</label>
        <textarea
          rows={5}
          placeholder="Paste the risky clause here…"
          value={clauseText}
          onChange={e => setClauseText(e.target.value)}
          className={`w-full rounded-lg border px-3 py-2 text-sm resize-none ${input}`}
        />

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !clauseText.trim()}
          className="mt-3 w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white text-sm font-medium rounded-lg py-2 transition"
        >
          {loading ? <Loader size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {loading ? 'Rewriting…' : 'Generate Safe Rewrite'}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 bg-red-900/30 border border-red-700 rounded-lg p-3">
          <AlertCircle size={18} className="text-red-400 mt-0.5 shrink-0" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className={`rounded-xl border p-5 space-y-4 ${card}`}>
          {/* Badge row */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="inline-flex items-center gap-1 bg-green-900/40 text-green-300 text-xs font-medium px-2.5 py-1 rounded-full">
              <CheckCircle size={13} /> Rewrite Ready
            </span>
            <span className={`text-xs ${subtext}`}>
              Method: <span className="font-semibold">{result.method === 'llm' ? 'AI (Qwen)' : 'Rule-based'}</span>
            </span>
            <span className={`text-xs ${subtext}`}>
              Confidence: <span className="font-semibold">{Math.round((result.confidence || 0) * 100)}%</span>
            </span>
          </div>

          {/* Original */}
          <div>
            <label className={`block text-xs font-semibold mb-1 ${subtext}`}>Original Clause</label>
            <div className={`rounded-lg border p-3 text-sm whitespace-pre-wrap ${isDark ? 'bg-gray-900 border-gray-700 text-gray-300' : 'bg-gray-100 border-gray-200 text-gray-600'}`}>
              {result.original_clause}
            </div>
          </div>

          {/* Rewritten */}
          <div>
            <label className={`block text-xs font-semibold mb-1 text-violet-400`}>Rewritten Clause</label>
            <div className={`rounded-lg border p-3 text-sm whitespace-pre-wrap ${isDark ? 'bg-violet-950 border-violet-800 text-violet-200' : 'bg-violet-50 border-violet-200 text-violet-800'}`}>
              {result.rewritten_clause}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
