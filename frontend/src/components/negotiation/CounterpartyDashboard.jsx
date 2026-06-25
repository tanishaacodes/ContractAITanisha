import React, { useState, useEffect } from 'react';
import { Users, AlertCircle, TrendingUp, Zap, Shield, Loader2 } from 'lucide-react';
import MetricCard from './MetricCard';
import ClauseHeatmap from './ClauseHeatmap';
import { counterpartyAPI } from '../../services/negotiationAPI';

/**
 * CounterpartyDashboard Component
 * Comprehensive behavior analysis dashboard for a counterparty
 */
const CounterpartyDashboard = ({ counterpartyId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    if (counterpartyId) {
      loadBehaviorData();
    }
  }, [counterpartyId]);

  const loadBehaviorData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await counterpartyAPI.getBehavior(counterpartyId);
      setData(response);
    } catch (err) {
      console.error('Error loading counterparty behavior:', err);
      setError('Failed to load counterparty behavior data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-gray-600">Loading behavior data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-2 text-red-800">
          <AlertCircle className="w-5 h-5" />
          <span className="font-semibold">{error}</span>
        </div>
      </div>
    );
  }

  if (!data || !data.behavior) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <p className="text-gray-600">No negotiation history available for this counterparty</p>
      </div>
    );
  }

  const { counterparty, behavior, negotiation_style, clause_acceptance_matrix, stall_clauses, trends } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <Users className="w-8 h-8" />
          <h1 className="text-3xl font-bold">{counterparty}</h1>
        </div>
        <p className="text-blue-100 text-sm">
          Based on {behavior.total_negotiations} negotiation(s)
        </p>
      </div>

      {/* Negotiation Style */}
      {negotiation_style && (
        <div className="bg-red-500/10 border-2 border-red-500/30 backdrop-blur-sm rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5 text-red-400" />
            Negotiation Style: {negotiation_style.style}
          </h2>
          <p className="text-slate-300 leading-relaxed">
            {negotiation_style.description}
          </p>
        </div>
      )}

      {/* Key Metrics */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Key Behavior Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            label="Aggressiveness"
            value={behavior.aggressiveness}
            icon={Zap}
            colorClass={behavior.aggressiveness > 0.7 ? 'bg-red-500' : behavior.aggressiveness > 0.4 ? 'bg-yellow-500' : 'bg-green-500'}
            trend={trends?.trend === 'GETTING_TOUGHER' ? 'up' : trends?.trend === 'GETTING_SOFTER' ? 'down' : 'stable'}
            trendValue={trends?.change ? `${(trends.change * 100).toFixed(0)}%` : null}
          />
          <MetricCard
            label="Elasticity"
            value={behavior.elasticity}
            icon={TrendingUp}
            colorClass="bg-blue-500"
          />
          <MetricCard
            label="Acceptance Rate"
            value={`${Math.round(behavior.acceptance_rate * 100)}%`}
            icon={Shield}
            colorClass="bg-purple-500"
          />
          <MetricCard
            label="Avg Redlines"
            value={behavior.avg_redlines}
            icon={AlertCircle}
            colorClass="bg-orange-500"
          />
        </div>
      </div>

      {/* Clause Acceptance Matrix */}
      {clause_acceptance_matrix && Object.keys(clause_acceptance_matrix).length > 0 && (
        <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl border border-cyan-500/20 p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            Clause Acceptance Rates
          </h2>
          <ClauseHeatmap data={clause_acceptance_matrix} />
        </div>
      )}

      {/* Stall Clauses */}
      {stall_clauses && stall_clauses.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 backdrop-blur-sm rounded-lg p-6">
          <h2 className="text-xl font-bold text-yellow-400 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            High-Risk Stall Clauses
          </h2>
          <div className="space-y-3">
            {stall_clauses.map((item, idx) => (
              <div key={idx} className="bg-slate-700/30 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-white">{item.clause_type}</h3>
                    <p className="text-sm text-slate-400">
                      Stalled in {item.occurrences} negotiation(s)
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-red-400">
                      {Math.round(item.stall_rate * 100)}%
                    </p>
                    <p className="text-xs text-slate-500">Stall Rate</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trends */}
      {trends && trends.trend !== 'STABLE' && (
        <div className={`${trends.trend === 'GETTING_TOUGHER' ? 'bg-red-500/10 border-red-500/30' : 'bg-emerald-500/10 border-emerald-500/30'} border backdrop-blur-sm rounded-lg p-6`}>
          <h2 className={`text-lg font-bold ${trends.trend === 'GETTING_TOUGHER' ? 'text-red-400' : 'text-emerald-400'} mb-2 flex items-center gap-2`}>
            {trends.trend === 'GETTING_TOUGHER' ? (
              <TrendingUp className="w-5 h-5" />
            ) : (
              <TrendingUp className="w-5 h-5 transform rotate-180" />
            )}
            Behavior Trend
          </h2>
          <p className={`${trends.trend === 'GETTING_TOUGHER' ? 'text-red-300' : 'text-emerald-300'}`}>
            {trends.description}
          </p>
        </div>
      )}
    </div>
  );
};

export default CounterpartyDashboard;
