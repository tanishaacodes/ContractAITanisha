/**
 * Advanced What-If Dashboard
 * ============================
 * Unified decision-intelligence page with four tabs:
 *   1. Clause Rewrite   – auto-suggest safer language
 *   2. Counter-Proposal – negotiation counter-proposal generator
 *   3. Advanced Simulation – remove / add / counterfactual_add with full
 *      risk + obligation + Monte Carlo readout
 *   4. How It Works     – quick explainer for executives
 *
 * Tab 3 is contract-scoped (reads contractId from URL params).
 * Tabs 1 & 2 are standalone (paste any clause text).
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  PenLine,
  MessageSquarePlus,
  FlaskConical,
  BookOpen,
  ArrowLeft,
  Loader,
  AlertCircle,
  CheckCircle,
  TrendingDown,
  TrendingUp,
  Activity,
  DollarSign,
  FileText,
} from 'lucide-react';
import useThemeStore from '../store/themeStore';
import { advancedWhatIfAPI } from '../services/advancedAI';
import ClauseRewritePanel   from '../components/ClauseRewritePanel';
import CounterProposalPanel from '../components/CounterProposalPanel';

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------
const TABS = [
  { id: 'rewrite',    label: 'Clause Rewrite',       icon: PenLine,            color: 'violet' },
  { id: 'proposal',   label: 'Counter-Proposal',    icon: MessageSquarePlus,  color: 'emerald' },
  { id: 'simulation', label: 'Advanced Simulation', icon: FlaskConical,       color: 'cyan' },
  { id: 'howit',      label: 'How It Works',         icon: BookOpen,           color: 'amber' },
];

// ---------------------------------------------------------------------------
// Simulation action options
// ---------------------------------------------------------------------------
const ACTION_OPTIONS = [
  { value: 'remove',             label: 'Remove Clause',              desc: 'Remove paragraphs containing a keyword' },
  { value: 'add',                label: 'Add Clause',                 desc: 'Append a user-written clause' },
  { value: 'counterfactual_add', label: 'AI Counterfactual Add',      desc: 'LLM generates a protective clause for a stated objective' },
];

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function AdvancedWhatIfDashboard() {
  const { contractId } = useParams();
  const navigate       = useNavigate();
  const { currentTheme } = useThemeStore();
  const isDark = currentTheme === 'dark';

  const [activeTab, setActiveTab] = useState('rewrite');

  // --- simulation state ---
  const [action,                  setAction]                  = useState('remove');
  const [clauseKeyword,           setClauseKeyword]           = useState('');
  const [clauseText,              setClauseText]              = useState('');
  const [counterfactualObjective, setCounterfactualObjective] = useState('');
  const [simLoading,              setSimLoading]              = useState(false);
  const [simResult,               setSimResult]               = useState(null);
  const [simError,                setSimError]                = useState(null);

  // Navigate away if no contract and user picks simulation tab
  useEffect(() => {
    if (activeTab === 'simulation' && !contractId) {
      navigate('/contracts/list');
    }
  }, [activeTab, contractId, navigate]);

  // ---------------------------------------------------------------------------
  // Run simulation
  // ---------------------------------------------------------------------------
  const runSimulation = async (e) => {
    e.preventDefault();
    setSimLoading(true);
    setSimError(null);
    setSimResult(null);

    const payload = { action };
    if (action === 'remove')              payload.clause_keyword            = clauseKeyword;
    if (action === 'add')                 payload.clause_text               = clauseText;
    if (action === 'counterfactual_add')  payload.counterfactual_objective  = counterfactualObjective;

    try {
      const data = await advancedWhatIfAPI.simulate(contractId, payload);
      if (data.success === false) throw new Error(data.error || 'Simulation failed');
      setSimResult(data);
    } catch (err) {
      setSimError(err.message || err.response?.data?.error || 'Simulation failed');
    } finally {
      setSimLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Colours
  // ---------------------------------------------------------------------------
  const card    = isDark ? 'bg-gray-800 border-gray-700'  : 'bg-white border-gray-200';
  const text    = isDark ? 'text-gray-100'                : 'text-gray-800';
  const subtext = isDark ? 'text-gray-400'                : 'text-gray-500';
  const input   = isDark ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400'
                        : 'bg-gray-50  border-gray-300 text-gray-800 placeholder-gray-400';
  const select  = isDark ? 'bg-gray-700 border-gray-600 text-gray-100'
                        : 'bg-gray-50  border-gray-300 text-gray-800';

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className={`min-h-screen ${isDark ? 'bg-gray-950' : 'bg-gray-100'} py-6 px-4 sm:px-6 lg:px-8`}>
      {/* Header */}
      <div className="max-w-5xl mx-auto mb-6">
        <button
          onClick={() => navigate(contractId ? `/contracts/${contractId}` : '/contracts/list')}
          className={`inline-flex items-center gap-1.5 text-sm mb-3 ${subtext} hover:text-violet-400 transition`}
        >
          <ArrowLeft size={15} /> Back
        </button>

        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-violet-900/40 rounded-xl">
            <Activity size={24} className="text-violet-400" />
          </div>
          <div>
            <h1 className={`text-xl font-bold ${text}`}>Advanced Decision Intelligence</h1>
            <p className={`text-sm ${subtext}`}>
              Clause rewrite · Counter-proposal · What-if simulation · Monte Carlo exposure
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto">
        {/* Tab bar */}
        <div className={`flex gap-1 rounded-xl border p-1.5 mb-6 ${card}`}>
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 text-sm font-medium rounded-lg py-2 px-3 transition
                  ${active
                    ? 'bg-violet-700 text-white shadow'
                    : isDark ? 'text-gray-400 hover:text-gray-200 hover:bg-gray-700' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
              >
                <Icon size={15} />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* =====================================================================
            TAB: Clause Rewrite
        ===================================================================== */}
        {activeTab === 'rewrite' && <ClauseRewritePanel />}

        {/* =====================================================================
            TAB: Counter-Proposal
        ===================================================================== */}
        {activeTab === 'proposal' && <CounterProposalPanel />}

        {/* =====================================================================
            TAB: Advanced Simulation
        ===================================================================== */}
        {activeTab === 'simulation' && (
          <div className="space-y-5">
            {/* Action selector cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {ACTION_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setAction(opt.value)}
                  className={`text-left rounded-xl border p-4 transition
                    ${action === opt.value
                      ? 'border-cyan-500 bg-cyan-900/20'
                      : card
                    }`}
                >
                  <p className={`text-sm font-semibold ${action === opt.value ? 'text-cyan-300' : text}`}>{opt.label}</p>
                  <p className={`text-xs mt-0.5 ${subtext}`}>{opt.desc}</p>
                </button>
              ))}
            </div>

            {/* Dynamic input */}
            <form onSubmit={runSimulation} className={`rounded-xl border p-5 ${card}`}>
              {action === 'remove' && (
                <>
                  <label className={`block text-xs mb-1 ${subtext}`}>Keyword to Remove</label>
                  <input
                    type="text"
                    placeholder="e.g. termination"
                    value={clauseKeyword}
                    onChange={e => setClauseKeyword(e.target.value)}
                    className={`w-full rounded-lg border px-3 py-2 text-sm ${input}`}
                  />
                </>
              )}

              {action === 'add' && (
                <>
                  <label className={`block text-xs mb-1 ${subtext}`}>Clause to Add</label>
                  <textarea
                    rows={4}
                    placeholder="Write the new clause you want to append…"
                    value={clauseText}
                    onChange={e => setClauseText(e.target.value)}
                    className={`w-full rounded-lg border px-3 py-2 text-sm resize-none ${input}`}
                  />
                </>
              )}

              {action === 'counterfactual_add' && (
                <>
                  <label className={`block text-xs mb-1 ${subtext}`}>Protective Objective</label>
                  <input
                    type="text"
                    placeholder="e.g. cap financial liability"
                    value={counterfactualObjective}
                    onChange={e => setCounterfactualObjective(e.target.value)}
                    className={`w-full rounded-lg border px-3 py-2 text-sm ${input}`}
                  />
                  <p className={`text-xs mt-1 ${subtext}`}>
                    The AI will generate a protective clause aligned to this objective.
                  </p>
                </>
              )}

              <button
                type="submit"
                disabled={simLoading || (action === 'remove' && !clauseKeyword.trim()) || (action === 'add' && !clauseText.trim()) || (action === 'counterfactual_add' && !counterfactualObjective.trim())}
                className="mt-4 w-full flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-40 text-white text-sm font-medium rounded-lg py-2 transition"
              >
                {simLoading ? <Loader size={16} className="animate-spin" /> : <FlaskConical size={16} />}
                {simLoading ? 'Simulating…' : 'Run Simulation'}
              </button>
            </form>

            {/* Error */}
            {simError && (
              <div className="flex items-start gap-2 bg-red-900/30 border border-red-700 rounded-lg p-3">
                <AlertCircle size={18} className="text-red-400 mt-0.5 shrink-0" />
                <p className="text-red-300 text-sm">{simError}</p>
              </div>
            )}

            {/* Result dashboard */}
            {simResult && <SimulationResult result={simResult} isDark={isDark} />}
          </div>
        )}

        {/* =====================================================================
            TAB: How It Works
        ===================================================================== */}
        {activeTab === 'howit' && (
          <div className={`rounded-xl border p-6 space-y-6 ${card}`}>
            <h3 className={`text-lg font-bold ${text}`}>How Decision Intelligence Works</h3>

            {[
              {
                step: '1',
                title: 'Clause Rewrite',
                icon: PenLine,
                color: 'violet',
                body: 'Paste a clause the system flagged as risky. Select the risk category. The engine rewrites it using Qwen (AI) or proven rule-based templates, preserving commercial intent while capping liability, clarifying terms, or adding protective language.'
              },
              {
                step: '2',
                title: 'Counter-Proposal',
                icon: MessageSquarePlus,
                color: 'emerald',
                body: 'Enter what the counterparty wants. Set your risk appetite (low / medium / high). The engine generates a balanced counter-proposal that increases the probability of agreement — plus actionable negotiation tips.'
              },
              {
                step: '3',
                title: 'Advanced Simulation',
                icon: FlaskConical,
                color: 'cyan',
                body: 'Select a contract. Choose remove / add / counterfactual add. The engine mutates the contract text, re-extracts obligations, re-scores risk against the clause interaction graph, and runs a Monte Carlo exposure simulation (3,000 iterations) to produce confidence-interval exposure ranges.'
              },
              {
                step: '4',
                title: 'The Full Loop',
                icon: Activity,
                color: 'amber',
                body: 'Risky clause detected → Safe rewrite suggested → Counter-proposal generated → What-if simulated (add / replace) → Dispute risk recalculated → Monte Carlo ₹/$ exposure quantified. Every step is API-driven, composable, and auditable.'
              },
            ].map(s => {
              const Icon = s.icon;
              return (
                <div key={s.step} className="flex gap-4">
                  <div className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-${s.color}-900/40`}>
                    <Icon size={18} className={`text-${s.color}-400`} />
                  </div>
                  <div>
                    <h4 className={`font-semibold ${text}`}>{s.title}</h4>
                    <p className={`text-sm mt-0.5 ${subtext}`}>{s.body}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SimulationResult sub-component – renders the full result card grid
// ---------------------------------------------------------------------------
function SimulationResult({ result, isDark }) {
  const card    = isDark ? 'bg-gray-800 border-gray-700'  : 'bg-white border-gray-200';
  const text    = isDark ? 'text-gray-100'                : 'text-gray-800';
  const subtext = isDark ? 'text-gray-400'                : 'text-gray-500';

  const risk      = result.risk || {};
  const textDelta = result.text_delta || {};
  const oblig     = result.obligations || {};
  const mc        = result.monte_carlo;

  return (
    <div className="space-y-4">
      {/* Top badge */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="inline-flex items-center gap-1 bg-green-900/40 text-green-300 text-xs font-medium px-2.5 py-1 rounded-full">
          <CheckCircle size={13} /> Simulation Complete
        </span>
        <span className={`text-xs ${subtext}`}>Action: <span className="font-semibold capitalize">{result.action?.replace('_', ' ')}</span></span>
        {result.generation_method && (
          <span className={`text-xs ${subtext}`}>Generated by: <span className="font-semibold capitalize">{result.generation_method}</span></span>
        )}
      </div>

      {/* Generated clause (counterfactual) */}
      {result.generated_clause && (
        <div className={`rounded-xl border p-4 ${card}`}>
          <label className="block text-xs font-semibold mb-2 text-cyan-400">AI-Generated Protective Clause</label>
          <div className={`rounded-lg border p-3 text-sm whitespace-pre-wrap ${isDark ? 'bg-cyan-950 border-cyan-800 text-cyan-200' : 'bg-cyan-50 border-cyan-200 text-cyan-800'}`}>
            {result.generated_clause}
          </div>
        </div>
      )}

      {/* KPI grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Risk before vs after */}
        <KPICard
          icon={Activity}
          label="Risk Before"
          value={risk.before?.toFixed(3) ?? '—'}
          isDark={isDark}
          accent="gray"
        />
        <KPICard
          icon={risk.delta < 0 ? TrendingDown : TrendingUp}
          label="Risk After"
          value={risk.after?.toFixed(3) ?? '—'}
          isDark={isDark}
          accent={risk.delta < 0 ? 'green' : 'red'}
          sub={risk.reduction_pct != null ? `${risk.reduction_pct > 0 ? '↓' : '↑'} ${Math.abs(risk.reduction_pct)}%` : undefined}
        />
        {/* Text delta */}
        <KPICard
          icon={FileText}
          label="Chars Changed"
          value={textDelta.chars_added != null ? (textDelta.chars_added >= 0 ? `+${textDelta.chars_added}` : textDelta.chars_added.toString()) : '—'}
          isDark={isDark}
          accent="violet"
        />
        {/* Obligations */}
        <KPICard
          icon={CheckCircle}
          label="Obligations"
          value={`${oblig.before_count ?? 0} → ${oblig.after_count ?? 0}`}
          isDark={isDark}
          accent="amber"
        />
      </div>

      {/* Monte Carlo result */}
      {mc && (
        <div className={`rounded-xl border p-5 ${card}`}>
          <h4 className={`font-semibold text-sm mb-3 ${text}`}>Monte Carlo Exposure ({mc.iterations?.toLocaleString()} iterations)</h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MCMetric label="Mean Before"  value={mc.before?.mean}  isDark={isDark} />
            <MCMetric label="Mean After"   value={mc.after?.mean}   isDark={isDark} accent="green" />
            <MCMetric label="P90 Before"   value={mc.before?.p90}   isDark={isDark} />
            <MCMetric label="P90 After"    value={mc.after?.p90}    isDark={isDark} accent="green" />
          </div>
          {mc.confidence_statement && (
            <p className={`text-xs mt-3 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{mc.confidence_statement}</p>
          )}
        </div>
      )}

      {/* Obligation diff */}
      {oblig.after && oblig.after.length > 0 && (
        <div className={`rounded-xl border p-5 ${card}`}>
          <h4 className={`font-semibold text-sm mb-2 ${text}`}>Obligations After Mutation</h4>
          <div className="space-y-2">
            {oblig.after.map((o, i) => (
              <div key={i} className={`flex items-center gap-3 rounded-lg px-3 py-2 ${isDark ? 'bg-gray-900' : 'bg-gray-50'}`}>
                <span className="text-xs font-semibold text-cyan-400 capitalize w-24 shrink-0">{o.type}</span>
                <span className={`text-xs truncate ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{o.value}</span>
                <span className={`ml-auto text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{Math.round((o.confidence || 0) * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tiny KPI card
// ---------------------------------------------------------------------------
function KPICard({ icon: Icon, label, value, sub, isDark, accent = 'gray' }) {
  const card = isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200';
  return (
    <div className={`rounded-xl border p-3 ${card}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon size={15} className={`text-${accent}-400`} />
        <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{label}</span>
      </div>
      <p className={`text-lg font-bold ${isDark ? 'text-gray-100' : 'text-gray-800'}`}>{value}</p>
      {sub && <p className={`text-xs ${accent === 'green' ? 'text-green-400' : 'text-red-400'}`}>{sub}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Monte Carlo metric cell
// ---------------------------------------------------------------------------
function MCMetric({ label, value, isDark, accent }) {
  const fmt = (v) => v != null ? `₹${Number(v).toLocaleString('en-IN')}` : '—';
  return (
    <div className={`rounded-lg p-2.5 ${isDark ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{label}</p>
      <p className={`text-sm font-bold ${accent === 'green' ? 'text-green-400' : isDark ? 'text-gray-200' : 'text-gray-700'}`}>{fmt(value)}</p>
    </div>
  );
}
