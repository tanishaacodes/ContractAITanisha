import { useState, useEffect } from 'react';
import { Sparkles, TrendingUp } from 'lucide-react';
import axios from 'axios';
import useThemeStore from '../store/themeStore';
import SimulationControls from '../components/counterfactual/SimulationControls';
import RiskDeltaGauge from '../components/counterfactual/RiskDeltaGauge';
import ExposureDelta from '../components/counterfactual/ExposureDelta';
import NegotiationShift from '../components/counterfactual/NegotiationShift';
import LossDistribution from '../components/counterfactual/LossDistribution';

const CounterfactualSimulation = () => {
  const { theme } = useThemeStore();
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/counterfactual/contracts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContracts(response.data.contracts || []);
      if (response.data.contracts && response.data.contracts.length > 0) {
        setSelectedContract(response.data.contracts[0].id);
      }
    } catch (error) {
      console.error('Error fetching contracts:', error);
      setError('Failed to load contracts');
    }
  };

  const runSimulation = async (actions) => {
    if (!selectedContract) {
      setError('Please select a contract');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      const response = await axios.post(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/counterfactual/simulate`,
        {
          contract_id: selectedContract,
          actions: actions
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setResult(response.data);
    } catch (error) {
      console.error('Error running simulation:', error);
      setError(error.response?.data?.message || 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Sparkles className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h1 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
              Counterfactual & What-If Simulation Engine
            </h1>
            <p className="text-sm text-slate-400">
              Decision Cockpit — Simulate legal changes & predict impact before negotiation
            </p>
          </div>
        </div>
      </div>

      {/* Strategy Banner */}
      <div className="mb-6 bg-gradient-to-r from-indigo-900/20 to-purple-900/20 border border-indigo-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <TrendingUp className="w-5 h-5 text-indigo-400 mt-1 flex-shrink-0" />
          <div>
            <p className="text-indigo-400 font-semibold mb-1">Monte Carlo Risk Modeling</p>
            <p className="text-gray-300 text-sm">
              Simulate contract modifications (clauses, caps, jurisdiction) and see immediate impact on{' '}
              <span className="font-semibold text-white">risk exposure</span>,{' '}
              <span className="font-semibold text-white">financial loss distribution</span>, and{' '}
              <span className="font-semibold text-white">negotiation leverage</span>.
              Each simulation runs 1,000 Monte Carlo trials for statistical confidence.
            </p>
          </div>
        </div>
      </div>

      {/* Contract Selector */}
      <div className="mb-6 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <label className="block text-sm font-semibold text-white mb-3">
          Select Contract for Simulation
        </label>
        <select
          value={selectedContract || ''}
          onChange={(e) => setSelectedContract(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
        >
          <option value="">Choose a contract...</option>
          {contracts.map((contract) => (
            <option key={contract.id} value={contract.id}>
              {contract.name} {contract.business_unit && `- ${contract.business_unit}`}
            </option>
          ))}
        </select>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls - Left Column */}
        <div className="lg:col-span-1">
          <SimulationControls onRun={runSimulation} loading={loading} />
        </div>

        {/* Results - Right Columns */}
        <div className="lg:col-span-2">
          {error && (
            <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 mb-6">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {loading && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12">
              <div className="flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mb-4"></div>
                <p className="text-slate-400 text-sm">Running Monte Carlo simulation...</p>
                <p className="text-slate-500 text-xs mt-2">Analyzing 1,000 scenarios</p>
              </div>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-6">
              {/* Metrics Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <RiskDeltaGauge value={result.risk_delta_percentage} />
                <ExposureDelta data={result} />
                <NegotiationShift value={result.negotiation_shift} />
              </div>

              {/* Loss Distribution Chart */}
              <LossDistribution data={result} />

              {/* Summary Stats */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Simulation Summary</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-slate-400 mb-1">Base Exposure</p>
                    <p className="text-white font-semibold">₹{result.base_exposure_inr.toLocaleString()}</p>
                    <p className="text-slate-500 text-xs">${result.base_exposure_usd.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 mb-1">Avg Loss (Expected)</p>
                    <p className="text-white font-semibold">₹{result.avg_loss_inr.toLocaleString()}</p>
                    <p className="text-slate-500 text-xs">${result.avg_loss_usd.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 mb-1">95th Percentile (VaR)</p>
                    <p className="text-amber-400 font-semibold">₹{result.percentile_95_inr.toLocaleString()}</p>
                    <p className="text-slate-500 text-xs">${result.percentile_95_usd.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 mb-1">99th Percentile (Tail)</p>
                    <p className="text-red-400 font-semibold">₹{result.percentile_99_inr.toLocaleString()}</p>
                    <p className="text-slate-500 text-xs">${result.percentile_99_usd.toLocaleString()}</p>
                  </div>
                </div>
              </div>

              {/* Actions Applied */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-white mb-3">Modifications Applied</h3>
                <div className="flex flex-wrap gap-2">
                  {result.actions_applied.remove_clause && (
                    <span className="px-3 py-1 bg-red-900/30 border border-red-500/50 rounded-full text-red-400 text-xs">
                      Clause Removed
                    </span>
                  )}
                  {result.actions_applied.add_indemnity && (
                    <span className="px-3 py-1 bg-blue-900/30 border border-blue-500/50 rounded-full text-blue-400 text-xs">
                      Indemnity Added
                    </span>
                  )}
                  {result.actions_applied.add_arbitration && (
                    <span className="px-3 py-1 bg-green-900/30 border border-green-500/50 rounded-full text-green-400 text-xs">
                      Arbitration Clause Added
                    </span>
                  )}
                  {result.actions_applied.termination_rights && (
                    <span className="px-3 py-1 bg-purple-900/30 border border-purple-500/50 rounded-full text-purple-400 text-xs">
                      Termination Rights Added
                    </span>
                  )}
                  <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-slate-300 text-xs">
                    Liability Cap: {result.actions_applied.liability_cap}x
                  </span>
                  <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-slate-300 text-xs">
                    Law: {result.actions_applied.governing_law}
                  </span>
                </div>
              </div>
            </div>
          )}

          {!result && !loading && !error && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12">
              <div className="text-center">
                <Sparkles className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400 text-sm">Configure simulation parameters and click "Run Simulation"</p>
                <p className="text-slate-500 text-xs mt-2">Results will appear here</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CounterfactualSimulation;
