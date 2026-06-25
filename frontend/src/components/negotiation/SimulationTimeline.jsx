import React from 'react';
import { CheckCircle, XCircle, Circle, AlertTriangle } from 'lucide-react';

/**
 * SimulationTimeline Component
 * Displays round-by-round negotiation progression
 */
const SimulationTimeline = ({ clauseStates, status }) => {
  if (!clauseStates || clauseStates.length === 0) {
    return (
      <div className="text-center text-slate-400 py-8">
        No simulation data available
      </div>
    );
  }

  // Group by round
  const rounds = {};
  clauseStates.forEach((state) => {
    const round = state.round;
    if (!rounds[round]) {
      rounds[round] = [];
    }
    rounds[round].push(state);
  });

  const getStatusIcon = (accepted, stallRisk) => {
    if (accepted) {
      return <CheckCircle className="w-5 h-5 text-emerald-400" />;
    }
    if (stallRisk > 0.7) {
      return <AlertTriangle className="w-5 h-5 text-red-400" />;
    }
    return <XCircle className="w-5 h-5 text-slate-400" />;
  };

  const getStatusBadge = (status) => {
    const badges = {
      'SIGNED': 'bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.4)]',
      'STALLED': 'bg-red-600 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]',
      'PARTIAL': 'bg-yellow-500 text-white shadow-[0_0_20px_rgba(245,158,11,0.4)]',
    };
    return badges[status] || 'bg-slate-500 text-white';
  };

  return (
    <div className="space-y-6">
      {/* Final Status Badge */}
      <div className="flex items-center justify-center">
        <span className={`px-6 py-3 rounded-full text-lg font-bold ${getStatusBadge(status)}`}>
          {status === 'SIGNED' && '✓ Deal Signed'}
          {status === 'STALLED' && '⚠ Negotiation Stalled'}
          {status === 'PARTIAL' && '⏸ Partial Agreement'}
        </span>
      </div>

      {/* Timeline */}
      <div className="relative">
        {Object.entries(rounds).map(([round, states], roundIdx) => (
          <div key={roundIdx} className="relative">
            {/* Round Header */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-cyan-600 to-blue-600 text-white font-bold text-lg shadow-[0_0_15px_rgba(6,182,212,0.5)]">
                {round}
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Round {round}</h3>
                <p className="text-sm text-slate-400">
                  {states.filter(s => s.accepted).length}/{states.length} clauses accepted
                </p>
              </div>
            </div>

            {/* Clauses in this round */}
            <div className="ml-14 space-y-3 mb-8">
              {states.map((state, stateIdx) => (
                <div
                  key={stateIdx}
                  className={`p-4 rounded-lg border backdrop-blur-sm ${
                    state.accepted
                      ? 'bg-emerald-500/10 border-emerald-500/30'
                      : state.stall_risk > 0.7
                      ? 'bg-red-500/10 border-red-500/30'
                      : 'bg-slate-700/30 border-slate-600/30'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {getStatusIcon(state.accepted, state.stall_risk)}
                        <h4 className="font-semibold text-white">
                          {state.clause_type}
                        </h4>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">Acceptance Probability</p>
                          <p className="font-bold text-cyan-400">
                            {Math.round(state.acceptance_probability * 100)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">Stall Risk</p>
                          <p className={`font-bold ${state.stall_risk > 0.7 ? 'text-red-400' : 'text-white'}`}>
                            {Math.round(state.stall_risk * 100)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">Expected Redlines</p>
                          <p className="font-bold text-orange-400">
                            {state.expected_redlines}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Connector Line */}
            {roundIdx < Object.keys(rounds).length - 1 && (
              <div className="absolute left-6 top-14 bottom-0 w-0.5 bg-cyan-500/30" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SimulationTimeline;
