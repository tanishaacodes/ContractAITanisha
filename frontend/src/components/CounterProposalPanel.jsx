import { useState } from 'react';
import { MessageSquarePlus, Loader, CheckCircle, AlertCircle, RefreshCw, Lightbulb } from 'lucide-react';
import { counterProposalAPI } from '../services/advancedAI';
import useThemeStore from '../store/themeStore';

const TOLERANCE_OPTIONS = [
  { value: 'low',    label: 'Low  – Protect our position' },
  { value: 'medium', label: 'Medium – Balanced approach' },
  { value: 'high',   label: 'High – Close deal quickly' },
];

export default function CounterProposalPanel() {
  const { currentTheme } = useThemeStore();
  const isDark = currentTheme === 'dark';

  const [originalClause,        setOriginalClause]        = useState('');
  const [counterpartyPosition,  setCounterpartyPosition]  = useState('');
  const [riskTolerance,         setRiskTolerance]         = useState('medium');
  const [loading,               setLoading]               = useState(false);
  const [result,                setResult]                = useState(null);
  const [error,                 setError]                 = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await counterProposalAPI.generate(originalClause, counterpartyPosition, riskTolerance);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate counter-proposal');
    } finally {
      setLoading(false);
    }
  };

  // colours
  const card    = isDark ? 'bg-gray-800 border-gray-700'  : 'bg-white border-gray-200';
  const text    = isDark ? 'text-gray-100'                : 'text-gray-800';
  const subtext = isDark ? 'text-gray-400'                : 'text-gray-500';
  const input   = isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400'
                        : 'bg-gray-50  border-gray-300 text-gray-800 placeholder-gray-400';
  const select  = isDark ? 'bg-gray-700 border-gray-600 text-gray-100'
                        : 'bg-gray-50  border-gray-300 text-gray-800';

  return (
    <div className="space-y-5">
      {/* Form */}
      <form onSubmit={handleSubmit} className={`rounded-xl border p-5 ${card}`}>
        <div className="flex items-center gap-2 mb-4">
          <MessageSquarePlus size={20} className="text-emerald-400" />
          <h3 className={`font-semibold text-base ${text}`}>Counter-Proposal Generator</h3>
        </div>

        {/* Risk tolerance */}
        <label className={`block text-xs mb-1 ${subtext}`}>Our Risk Tolerance</label>
        <select
          value={riskTolerance}
          onChange={e => setRiskTolerance(e.target.value)}
          className={`w-full rounded-lg border px-3 py-2 text-sm mb-3 ${select}`}
        >
          {TOLERANCE_OPTIONS.map(t => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>

        {/* Original clause */}
        <label className={`block text-xs mb-1 ${subtext}`}>Original Clause</label>
        <textarea
          rows={4}
          placeholder="Paste the clause currently under negotiation…"
          value={originalClause}
          onChange={e => setOriginalClause(e.target.value)}
          className={`w-full rounded-lg border px-3 py-2 text-sm resize-none mb-3 ${input}`}
        />

        {/* Counterparty position */}
        <label className={`block text-xs mb-1 ${subtext}`}>Counterparty Position</label>
        <textarea
          rows={3}
          placeholder={'What does the other side want? e.g. "We need 90-day payment terms…"'}
          value={counterpartyPosition}
          onChange={e => setCounterpartyPosition(e.target.value)}
          className={`w-full rounded-lg border px-3 py-2 text-sm resize-none ${input}`}
        />

        <button
          type="submit"
          disabled={loading || !originalClause.trim() || !counterpartyPosition.trim()}
          className="mt-3 w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white text-sm font-medium rounded-lg py-2 transition"
        >
          {loading ? <Loader size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {loading ? 'Generating…' : 'Generate Counter-Proposal'}
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
          {/* Badges */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="inline-flex items-center gap-1 bg-emerald-900/40 text-emerald-300 text-xs font-medium px-2.5 py-1 rounded-full">
              <CheckCircle size={13} /> Proposal Ready
            </span>
            <span className={`text-xs ${subtext}`}>
              Method: <span className="font-semibold">{result.method === 'llm' ? 'AI (Qwen)' : 'Rule-based'}</span>
            </span>
            <span className={`text-xs ${subtext}`}>
              Confidence: <span className="font-semibold">{Math.round((result.confidence || 0) * 100)}%</span>
            </span>
          </div>

          {/* Counter-proposal */}
          <div>
            <label className="block text-xs font-semibold mb-1 text-emerald-400">Counter-Proposal</label>
            <div className={`rounded-lg border p-3 text-sm whitespace-pre-wrap ${isDark ? 'bg-emerald-950 border-emerald-800 text-emerald-200' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}`}>
              {result.counter_proposal}
            </div>
          </div>

          {/* Negotiation tips */}
          {result.negotiation_tips && result.negotiation_tips.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Lightbulb size={14} className="text-amber-400" />
                <label className={`text-xs font-semibold ${subtext}`}>Negotiation Tips</label>
              </div>
              <ul className="space-y-1.5">
                {result.negotiation_tips.map((tip, i) => (
                  <li key={i} className={`text-sm flex gap-2 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                    <span className="text-amber-400 mt-0.5">•</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
