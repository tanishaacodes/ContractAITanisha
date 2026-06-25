import React from 'react';
import { Lightbulb, AlertCircle, ArrowRight, TrendingUp } from 'lucide-react';

/**
 * StrategyPanel Component
 * Displays strategic recommendations based on simulation
 */
const StrategyPanel = ({ strategy, summary }) => {
  if (!strategy) {
    return null;
  }

  const { strategy: strategyText, recommendations, trade_off_opportunities } = strategy;

  const getStrategyColor = () => {
    if (strategyText.includes('Defensive') || strategyText.includes('High risk')) {
      return 'bg-red-500/10 border-red-500/30 text-red-400';
    }
    if (strategyText.includes('Cautious') || strategyText.includes('Balanced')) {
      return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
    }
    return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
  };

  return (
    <div className="space-y-6">
      {/* Strategy Description */}
      <div className={`rounded-lg border backdrop-blur-sm p-6 ${getStrategyColor()}`}>
        <div className="flex items-center gap-3 mb-3">
          <Lightbulb className="w-6 h-6" />
          <h2 className="text-xl font-bold text-white">Recommended Strategy</h2>
        </div>
        <p className="text-lg leading-relaxed text-slate-300">
          {strategyText}
        </p>
      </div>

      {/* Summary Statistics */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/60 backdrop-blur-xl border border-cyan-500/20 rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.1)] p-4">
            <p className="text-sm text-slate-400 mb-1">Total Clauses</p>
            <p className="text-2xl font-bold text-white">{summary.total_clauses}</p>
          </div>
          <div className="bg-slate-800/60 backdrop-blur-xl border border-emerald-500/20 rounded-lg shadow-[0_0_20px_rgba(16,185,129,0.1)] p-4">
            <p className="text-sm text-emerald-400 mb-1">Accepted</p>
            <p className="text-2xl font-bold text-white">{summary.accepted_clauses}</p>
          </div>
          <div className="bg-slate-800/60 backdrop-blur-xl border border-yellow-500/20 rounded-lg shadow-[0_0_20px_rgba(245,158,11,0.1)] p-4">
            <p className="text-sm text-yellow-400 mb-1">Pending</p>
            <p className="text-2xl font-bold text-white">{summary.pending_clauses}</p>
          </div>
          <div className="bg-slate-800/60 backdrop-blur-xl border border-cyan-500/20 rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.1)] p-4">
            <p className="text-sm text-cyan-400 mb-1">Acceptance Rate</p>
            <p className="text-2xl font-bold text-white">
              {Math.round(summary.acceptance_rate * 100)}%
            </p>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="bg-cyan-500/10 border border-cyan-500/30 backdrop-blur-sm rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertCircle className="w-5 h-5 text-cyan-400" />
            <h3 className="text-lg font-bold text-white">Tactical Recommendations</h3>
          </div>
          <ul className="space-y-3">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-3 bg-slate-700/30 border-l-2 border-cyan-500 rounded-lg p-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-600 text-white flex items-center justify-center text-xs font-bold shadow-[0_0_10px_rgba(6,182,212,0.5)]">
                  {idx + 1}
                </span>
                <span className="flex-1 pt-0.5 text-slate-300">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Trade-off Opportunities */}
      {trade_off_opportunities && trade_off_opportunities.length > 0 && (
        <div className="bg-purple-500/10 border border-purple-500/30 backdrop-blur-sm rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            <h3 className="text-lg font-bold text-white">Trade-off Opportunities</h3>
          </div>
          <div className="space-y-4">
            {trade_off_opportunities.map((tradeoff, idx) => (
              <div key={idx} className="bg-slate-700/50 border border-slate-600/30 backdrop-blur-sm rounded-lg p-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <p className="text-sm text-slate-400 mb-1">Consider conceding:</p>
                    <p className="font-bold text-red-400">{tradeoff.give_up}</p>
                  </div>
                  <ArrowRight className="w-6 h-6 text-cyan-400 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm text-slate-400 mb-1">To strengthen:</p>
                    <p className="font-bold text-emerald-400">
                      {tradeoff.strengthen.join(', ')}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Most Problematic Clauses */}
      {summary?.most_problematic && summary.most_problematic.length > 0 && (
        <div className="bg-red-500/10 border border-red-500/30 backdrop-blur-sm rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <h3 className="text-lg font-bold text-white">Most Problematic Clauses</h3>
          </div>
          <div className="space-y-3">
            {summary.most_problematic.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between bg-slate-700/30 border border-red-500/30 rounded-lg p-3">
                <span className="font-semibold text-white">{item.clause_type}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">Stall Risk:</span>
                  <span className="font-bold text-red-400">
                    {Math.round(item.stall_risk * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategyPanel;
