/**
 * AdvancedNegotiation.jsx
 * =======================
 * Advanced AI Negotiation Dashboard
 * - MCTS Negotiation Tree (ReactFlow visualization)
 * - Multi-Agent Negotiation (5 autonomous agents)
 * - RL Contract Optimizer
 * - Legal Precedent Matching
 */

import { useState } from 'react';
import {
  Brain, Users, Zap, Scale, Play, Loader, TrendingDown,
  CheckCircle, AlertTriangle, DollarSign, Calendar, FileText
} from 'lucide-react';
import NegotiationTreeVisualization from '../components/dispute/NegotiationTreeVisualization';
import MultiAgentDecisionPanel from '../components/dispute/MultiAgentDecisionPanel';
import {
  runMCTSNegotiation,
  runAdvancedMultiAgent,
  optimizeContractWithRL,
  matchLegalPrecedents,
} from '../services/disputeService';

export default function AdvancedNegotiation() {
  const [activeTab, setActiveTab] = useState('mcts'); // mcts, multiagent, rl, precedents
  const [loading, setLoading] = useState(false);

  // MCTS State
  const [mctsResult, setMctsResult] = useState(null);
  const [mctsIterations, setMctsIterations] = useState(500);
  const [mctsDepth, setMctsDepth] = useState(5);

  // Multi-Agent State
  const [multiAgentResult, setMultiAgentResult] = useState(null);
  const [multiAgentRounds, setMultiAgentRounds] = useState(5);

  // RL State
  const [rlResult, setRlResult] = useState(null);

  // Legal Precedent State
  const [precedentResult, setPrecedentResult] = useState(null);

  // Sample contract for testing
  const [contract, setContract] = useState({
    price: 110,
    delivery_days: 40,
    liability_cap: 0.2,
    payment_terms: 60,
    termination_penalty: 10,
    force_majeure: 1,
  });

  // ═══════════════════════════════════════════════════════════
  // HANDLERS
  // ═══════════════════════════════════════════════════════════

  const handleRunMCTS = async () => {
    setLoading(true);
    try {
      const result = await runMCTSNegotiation(contract, mctsIterations, mctsDepth);
      setMctsResult(result);
    } catch (error) {
      console.error('MCTS error:', error);
      alert('MCTS failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunMultiAgent = async () => {
    setLoading(true);
    try {
      const result = await runAdvancedMultiAgent(contract, multiAgentRounds);
      setMultiAgentResult(result);
    } catch (error) {
      console.error('Multi-agent error:', error);
      alert('Multi-agent negotiation failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunRL = async () => {
    setLoading(true);
    try {
      const result = await optimizeContractWithRL(contract);
      setRlResult(result);
    } catch (error) {
      console.error('RL error:', error);
      alert('RL optimization failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMatchPrecedents = async () => {
    setLoading(true);
    try {
      const result = await matchLegalPrecedents(
        'Sample construction contract with EPC terms',
        contract.price * 1000000,
        'construction',
        'US',
        5
      );
      setPrecedentResult(result);
    } catch (error) {
      console.error('Precedent matching error:', error);
      alert('Precedent matching failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-100 mb-2">
          Advanced AI Negotiation Intelligence
        </h1>
        <p className="text-slate-400">
          MCTS Tree Search • Multi-Agent Negotiation • RL Optimization • Legal Precedents
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        <TabButton
          active={activeTab === 'mcts'}
          onClick={() => setActiveTab('mcts')}
          icon={<Brain size={18} />}
          label="MCTS Tree"
        />
        <TabButton
          active={activeTab === 'multiagent'}
          onClick={() => setActiveTab('multiagent')}
          icon={<Users size={18} />}
          label="Multi-Agent"
        />
        <TabButton
          active={activeTab === 'rl'}
          onClick={() => setActiveTab('rl')}
          icon={<Zap size={18} />}
          label="RL Optimizer"
        />
        <TabButton
          active={activeTab === 'precedents'}
          onClick={() => setActiveTab('precedents')}
          icon={<Scale size={18} />}
          label="Legal Precedents"
        />
      </div>

      {/* Contract Input Panel */}
      <ContractInputPanel contract={contract} setContract={setContract} />

      {/* Main Content */}
      <div className="mt-6">
        {/* MCTS Tab */}
        {activeTab === 'mcts' && (
          <div className="space-y-4">
            {/* Controls */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Max Iterations</label>
                  <input
                    type="number"
                    value={mctsIterations}
                    onChange={(e) => setMctsIterations(Number(e.target.value))}
                    className="bg-slate-900 border border-slate-600 rounded px-3 py-2 text-slate-200 w-32"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Max Depth</label>
                  <input
                    type="number"
                    value={mctsDepth}
                    onChange={(e) => setMctsDepth(Number(e.target.value))}
                    className="bg-slate-900 border border-slate-600 rounded px-3 py-2 text-slate-200 w-32"
                  />
                </div>
                <button
                  onClick={handleRunMCTS}
                  disabled={loading}
                  className="ml-auto px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
                  Run MCTS
                </button>
              </div>
            </div>

            {/* MCTS Results */}
            {mctsResult && (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h2 className="text-xl font-bold text-slate-200 mb-4">
                  MCTS Negotiation Tree
                </h2>

                {/* Summary Stats */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <StatCard
                    label="Best Score"
                    value={mctsResult.best_score?.toFixed(1) || 'N/A'}
                    color="text-green-400"
                  />
                  <StatCard
                    label="Dispute Risk"
                    value={`${(mctsResult.dispute_risk * 100).toFixed(1)}%`}
                    color="text-red-400"
                  />
                  <StatCard
                    label="Commercial Value"
                    value={`$${(mctsResult.commercial_value / 1000000).toFixed(1)}M`}
                    color="text-blue-400"
                  />
                </div>

                {/* Tree Visualization */}
                <div className="bg-slate-900 rounded-lg border border-slate-700">
                  <NegotiationTreeVisualization treeData={mctsResult.tree} />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Multi-Agent Tab */}
        {activeTab === 'multiagent' && (
          <div className="space-y-4">
            {/* Controls */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Max Rounds</label>
                  <input
                    type="number"
                    value={multiAgentRounds}
                    onChange={(e) => setMultiAgentRounds(Number(e.target.value))}
                    className="bg-slate-900 border border-slate-600 rounded px-3 py-2 text-slate-200 w-32"
                  />
                </div>
                <button
                  onClick={handleRunMultiAgent}
                  disabled={loading}
                  className="ml-auto px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
                  Run Multi-Agent
                </button>
              </div>
            </div>

            {/* Multi-Agent Results */}
            {multiAgentResult && (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h2 className="text-xl font-bold text-slate-200 mb-4">
                  Multi-Agent Negotiation Results
                </h2>

                {/* Risk Reduction Banner */}
                {multiAgentResult.dispute_risk_reduction !== undefined && (
                  <div className="mb-6 bg-green-900/20 border border-green-700 rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="text-green-400" size={20} />
                      <div className="text-sm text-green-400 font-semibold">
                        Dispute Risk Reduction: {multiAgentResult.dispute_risk_reduction.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )}

                {/* Agent Decision Panel */}
                <MultiAgentDecisionPanel
                  agentDecisions={multiAgentResult.agent_decisions}
                  originalContract={multiAgentResult.initial_contract}
                  negotiatedContract={multiAgentResult.final_contract}
                />
              </div>
            )}
          </div>
        )}

        {/* RL Optimizer Tab */}
        {activeTab === 'rl' && (
          <div className="space-y-4">
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <button
                onClick={handleRunRL}
                disabled={loading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
                Optimize with RL
              </button>
            </div>

            {rlResult && (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h2 className="text-xl font-bold text-slate-200 mb-4">
                  RL Optimization Results
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-900 rounded p-4">
                    <div className="text-xs text-slate-400 mb-1">Dispute Risk</div>
                    <div className="text-2xl font-bold text-red-400">
                      {(rlResult.dispute_risk * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-slate-900 rounded p-4">
                    <div className="text-xs text-slate-400 mb-1">Actions Taken</div>
                    <div className="text-2xl font-bold text-blue-400">
                      {rlResult.actions_taken?.length || 0}
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">Optimized Contract</h3>
                  <pre className="bg-slate-900 rounded p-4 text-xs text-slate-300 overflow-x-auto">
                    {JSON.stringify(rlResult.optimized_contract, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Legal Precedents Tab */}
        {activeTab === 'precedents' && (
          <div className="space-y-4">
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <button
                onClick={handleMatchPrecedents}
                disabled={loading}
                className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
                Match Precedents
              </button>
            </div>

            {precedentResult && (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <h2 className="text-xl font-bold text-slate-200 mb-4">
                  Legal Precedent Analysis
                </h2>
                {/* Display precedent results */}
                <pre className="bg-slate-900 rounded p-4 text-xs text-slate-300 overflow-x-auto">
                  {JSON.stringify(precedentResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ═══════════════════════════════════════════════════════════

const TabButton = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 rounded-lg flex items-center gap-2 whitespace-nowrap transition-all ${
      active
        ? 'bg-blue-600 text-white'
        : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-700'
    }`}
  >
    {icon}
    <span className="font-semibold">{label}</span>
  </button>
);

const StatCard = ({ label, value, color }) => (
  <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
    <div className="text-xs text-slate-400 mb-1">{label}</div>
    <div className={`text-2xl font-bold ${color}`}>{value}</div>
  </div>
);

const ContractInputPanel = ({ contract, setContract }) => (
  <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
    <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
      <FileText size={16} />
      Contract Parameters
    </h3>
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      <InputField
        label="Price (M)"
        value={contract.price}
        onChange={(v) => setContract({ ...contract, price: v })}
      />
      <InputField
        label="Delivery Days"
        value={contract.delivery_days}
        onChange={(v) => setContract({ ...contract, delivery_days: v })}
      />
      <InputField
        label="Liability Cap"
        value={contract.liability_cap}
        onChange={(v) => setContract({ ...contract, liability_cap: v })}
        step="0.01"
      />
      <InputField
        label="Payment Terms"
        value={contract.payment_terms}
        onChange={(v) => setContract({ ...contract, payment_terms: v })}
      />
      <InputField
        label="Termination Penalty"
        value={contract.termination_penalty}
        onChange={(v) => setContract({ ...contract, termination_penalty: v })}
      />
      <InputField
        label="Force Majeure"
        value={contract.force_majeure}
        onChange={(v) => setContract({ ...contract, force_majeure: v })}
      />
    </div>
  </div>
);

const InputField = ({ label, value, onChange, step = "1" }) => (
  <div>
    <label className="text-xs text-slate-400 block mb-1">{label}</label>
    <input
      type="number"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      step={step}
      className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-slate-200 text-sm"
    />
  </div>
);
