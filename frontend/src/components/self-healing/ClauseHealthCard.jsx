import { ArrowUpCircle, TrendingUp, Activity } from 'lucide-react';

/**
 * Individual Clause Health Card Component
 * Displays health metrics and action buttons for a single clause
 */
const ClauseHealthCard = ({ clause, onPromote, getStatusColor, getStatusIcon }) => {
  const healthPercentage = (clause.health_score * 100).toFixed(0);
  const successPercentage = (clause.success_rate * 100).toFixed(0);

  const getHealthBarColor = (score) => {
    if (score >= 0.75) return 'bg-green-500';
    if (score >= 0.45) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const barGradient = clause.health_score >= 0.75
    ? 'linear-gradient(90deg,#10b981,#34d399)'
    : clause.health_score >= 0.45
    ? 'linear-gradient(90deg,#f59e0b,#fbbf24)'
    : 'linear-gradient(90deg,#ef4444,#f87171)';

  const scoreColor = clause.health_score >= 0.75 ? '#34d399' : clause.health_score >= 0.45 ? '#fbbf24' : '#f87171';

  return (
    <div className="rounded-2xl border border-white/5 p-5 transition-all hover:-translate-y-1 hover:border-indigo-500/30 relative overflow-hidden"
      style={{background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(8px)'}}>
      {/* Top accent bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl" style={{background: barGradient}} />

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-bold text-white truncate">{clause.clause_code}</h3>
          <p className="text-xs text-slate-600 mt-0.5 font-mono">{clause.clause_id.substring(0, 8)}···</p>
        </div>
        <div className={`flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-bold ml-2 flex-shrink-0 ${getStatusColor(clause.status)}`}>
          {getStatusIcon(clause.status)}
          <span>{clause.status}</span>
        </div>
      </div>

      {/* Health Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Health Score</span>
          <span className="text-xl font-black" style={{color: scoreColor}}>{healthPercentage}%</span>
        </div>
        <div className="w-full rounded-full h-1.5" style={{background: 'rgba(255,255,255,0.06)'}}>
          <div className="h-1.5 rounded-full transition-all duration-500" style={{width: `${healthPercentage}%`, background: barGradient}} />
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="rounded-xl p-3 border border-indigo-500/15" style={{background: 'rgba(99,102,241,0.07)'}}>
          <div className="flex items-center gap-1 mb-1">
            <TrendingUp className="w-3 h-3 text-indigo-400" />
            <span className="text-xs font-semibold text-indigo-400">Success</span>
          </div>
          <div className="text-lg font-black text-indigo-300">{successPercentage}%</div>
        </div>
        <div className="rounded-xl p-3 border border-purple-500/15" style={{background: 'rgba(139,92,246,0.07)'}}>
          <div className="flex items-center gap-1 mb-1">
            <Activity className="w-3 h-3 text-purple-400" />
            <span className="text-xs font-semibold text-purple-400">Usage</span>
          </div>
          <div className="text-lg font-black text-purple-300">{clause.usage_count || 0}</div>
        </div>
      </div>

      {clause.is_promoted && (
        <div className="rounded-xl px-3 py-2 mb-3 border border-emerald-500/20 flex items-center gap-2" style={{background: 'rgba(16,185,129,0.08)'}}>
          <ArrowUpCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-xs font-semibold text-emerald-400">Auto-Promoted</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button onClick={() => onPromote(clause.clause_id, true)}
          className="flex-1 py-2 text-xs font-semibold rounded-xl border border-white/10 text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-all">
          Analyze
        </button>
        <button onClick={() => onPromote(clause.clause_id, false)} disabled={clause.status === 'RETIRED'}
          className={`flex-1 py-2 text-xs font-semibold rounded-xl transition-all ${
            clause.status === 'RETIRED'
              ? 'bg-white/3 text-slate-700 cursor-not-allowed border border-white/5'
              : 'text-white border-0'
          }`}
          style={clause.status !== 'RETIRED' ? {background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', boxShadow: '0 4px 14px rgba(99,102,241,0.3)'} : {}}>
          Promote
        </button>
      </div>
    </div>
  );
};

export default ClauseHealthCard;
