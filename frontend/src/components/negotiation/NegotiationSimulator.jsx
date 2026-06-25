import React, { useState, useEffect } from 'react';
import { Play, Loader2, AlertCircle } from 'lucide-react';
import SimulationTimeline from './SimulationTimeline';
import StrategyPanel from './StrategyPanel';
import { simulationAPI } from '../../services/negotiationAPI';

/**
 * NegotiationSimulator Component
 * Main interface for running multi-clause negotiation simulations
 */
const NegotiationSimulator = ({ contractId, clauses, counterpartyId }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Load cached simulation on mount
  useEffect(() => {
    if (contractId && counterpartyId) {
      loadSimulation();
    }
  }, [contractId, counterpartyId]);

  const loadSimulation = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to load cached simulation
      const cached = await simulationAPI.getSimulation(contractId, counterpartyId);
      if (cached && cached.simulation) {
        console.log('Loaded cached simulation for contract:', contractId);
        setResult(cached);
      }
    } catch (err) {
      // No cache found - user needs to click "Run Simulation"
      console.log('No cached simulation found');
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async (forceRefresh = false) => {
    if (!counterpartyId || !clauses || clauses.length === 0) {
      setError('Please provide counterparty and clauses for simulation');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const payload = {
        contract_id: contractId,
        counterparty: counterpartyId,
        clauses: clauses.map(c => ({
          clause_type: c.clause_type || c.clauseType,
          text: c.text
        })),
        force_refresh: forceRefresh
      };

      const response = await simulationAPI.simulate(payload);
      setResult(response);
    } catch (err) {
      console.error('Error running simulation:', err);
      setError('Failed to run negotiation simulation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-700 rounded-lg shadow-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">Negotiation Simulator</h1>
        <p className="text-purple-100">
          Predict multi-round negotiation outcomes and identify optimal strategies
        </p>
      </div>

      {/* Run Simulation Button */}
      {!result && (
        <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl border border-purple-500/20 p-6">
          <div className="text-center">
            <button
              onClick={() => runSimulation(false)}
              disabled={loading}
              className={`inline-flex items-center gap-3 px-8 py-4 rounded-lg text-lg font-semibold transition-all ${
                loading
                  ? 'bg-slate-700 cursor-not-allowed text-slate-400'
                  : 'bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 text-white shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)]'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  Running Simulation...
                </>
              ) : (
                <>
                  <Play className="w-6 h-6" />
                  Run Negotiation Simulation
                </>
              )}
            </button>
            {clauses && (
              <p className="mt-4 text-sm text-slate-400">
                Simulating {clauses.length} clause(s) across multiple rounds
              </p>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 backdrop-blur-sm rounded-lg p-6">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">{error}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Strategy Recommendations */}
          <StrategyPanel
            strategy={result.strategy}
            summary={result.simulation?.summary}
          />

          {/* Timeline Visualization */}
          <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl border border-purple-500/20 p-6">
            <h2 className="text-2xl font-bold text-white mb-6">
              Simulation Timeline
            </h2>
            <SimulationTimeline
              clauseStates={result.simulation?.clause_states}
              status={result.simulation?.status}
            />
          </div>

          {/* Simulation Metrics */}
          <div className="bg-slate-700/50 border border-slate-600/30 backdrop-blur-sm rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4">
              Simulation Metrics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">Total Rounds</p>
                <p className="text-2xl font-bold text-white">
                  {result.simulation?.rounds || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Final Status</p>
                <p className={`text-2xl font-bold ${
                  result.simulation?.status === 'SIGNED' ? 'text-emerald-400' :
                  result.simulation?.status === 'STALLED' ? 'text-red-400' :
                  'text-yellow-400'
                }`}>
                  {result.simulation?.status}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Stall Probability</p>
                <p className="text-2xl font-bold text-orange-400">
                  {Math.round((result.simulation?.global_stall_risk || 0) * 100)}%
                </p>
              </div>
            </div>
          </div>

          {/* Run Again Button */}
          <div className="bg-slate-800/60 backdrop-blur-xl border border-purple-500/20 rounded-xl p-6 text-center">
            <button
              onClick={() => runSimulation(true)}
              disabled={loading}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 text-white rounded-lg font-semibold shadow-[0_0_20px_rgba(168,85,247,0.3)] transition-all"
            >
              <Play className="w-5 h-5" />
              Run New Simulation
            </button>
            <p className="text-xs text-slate-400 mt-2">
              Re-run simulation with updated data and strategies
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default NegotiationSimulator;
