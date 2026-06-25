/**
 * GNNPredictionsPanel.jsx
 * ========================
 * Graph Neural Network predictions and insights
 * Shows ML-powered dispute probability and influential clauses
 */

import { useState, useEffect } from 'react';
import { Network, TrendingUp, AlertCircle, Target } from 'lucide-react';
import { getGNNPrediction } from '../../services/arbitrationService';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const OUTCOME_COLORS = {
  buyer_win: '#68BC00',
  supplier_win: '#F16667',
  partial_award: '#F79767',
  settlement: '#4C8EDA',
};

export default function GNNPredictionsPanel({ analysisId }) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (analysisId) {
      loadPrediction();
    }
  }, [analysisId]);

  const loadPrediction = async () => {
    try {
      setLoading(true);
      const data = await getGNNPrediction(analysisId);
      setPrediction(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (error || !prediction || prediction.fallback || prediction.model_available === false) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
        <Network className="mx-auto mb-4" size={48} color="#4C8EDA" />
        <h3 className="text-lg font-semibold mb-2">GNN Model Not Available</h3>
        <p className="text-slate-400 text-sm mb-4">
          Graph Neural Network predictions require a trained model on historical arbitration data.
        </p>
        <div className="text-xs text-slate-500">
          Status: Using heuristic fallback for predictions
        </div>
      </div>
    );
  }

  // Prepare outcome distribution data for pie chart
  const outcomeData = [
    { name: 'Buyer Win', value: prediction.buyer_win_probability * 100, color: OUTCOME_COLORS.buyer_win },
    { name: 'Supplier Win', value: prediction.supplier_win_probability * 100, color: OUTCOME_COLORS.supplier_win },
    { name: 'Partial Award', value: prediction.partial_award_probability * 100, color: OUTCOME_COLORS.partial_award },
    { name: 'Settlement', value: prediction.settlement_probability * 100, color: OUTCOME_COLORS.settlement },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Network size={20} color="#4C8EDA" />
          <h3 className="text-lg font-semibold">GNN Predictions</h3>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-xs text-slate-400">Model: {prediction.model_version}</div>
        </div>
      </div>

      {/* Main Predictions Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Dispute Probability */}
        <div className="bg-gradient-to-br from-red-500/10 to-red-500/5 border border-red-500/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle size={18} className="text-red-400" />
            <div className="text-sm text-red-400 font-medium">Dispute Probability</div>
          </div>
          <div className="text-4xl font-bold text-red-400 mb-2">
            {(prediction.dispute_probability * 100).toFixed(1)}%
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-red-500 to-red-400"
                style={{ width: `${prediction.dispute_probability * 100}%` }}
              />
            </div>
          </div>
          <div className="mt-3 text-xs text-slate-400">
            Confidence: {(prediction.prediction_confidence * 100).toFixed(0)}%
          </div>
        </div>

        {/* Model Certainty */}
        <div className="bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/30 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-3">
            <Target size={18} className="text-cyan-400" />
            <div className="text-sm text-cyan-400 font-medium">Model Certainty</div>
          </div>
          <div className="text-4xl font-bold text-cyan-400 mb-2">
            {(prediction.model_certainty * 100).toFixed(0)}%
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400"
                style={{ width: `${prediction.model_certainty * 100}%` }}
              />
            </div>
          </div>
          <div className="mt-3 text-xs text-slate-400">
            Inference: {prediction.inference_time_ms.toFixed(1)}ms
          </div>
        </div>
      </div>

      {/* Outcome Distribution */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <h4 className="text-sm font-semibold mb-4">Predicted Outcome Distribution</h4>
        <div className="grid grid-cols-2 gap-6">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={outcomeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {outcomeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => `${value.toFixed(1)}%`}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-3">
            {outcomeData.map((outcome) => (
              <div key={outcome.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: outcome.color }}
                  />
                  <span className="text-sm text-slate-300">{outcome.name}</span>
                </div>
                <span className="text-sm font-semibold" style={{ color: outcome.color }}>
                  {outcome.value.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Graph Statistics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-1">Nodes</div>
          <div className="text-xl font-bold text-cyan-400">{prediction.node_count}</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-1">Edges</div>
          <div className="text-xl font-bold text-cyan-400">{prediction.edge_count}</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-1">Avg Degree</div>
          <div className="text-xl font-bold text-cyan-400">
            {prediction.avg_node_degree.toFixed(1)}
          </div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-1">Density</div>
          <div className="text-xl font-bold text-cyan-400">
            {(prediction.graph_density * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Top Influential Clauses */}
      {prediction.top_influential_clauses && prediction.top_influential_clauses.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} className="text-cyan-400" />
            <h4 className="text-sm font-semibold">Most Influential Clauses</h4>
          </div>
          <div className="space-y-3">
            {prediction.top_influential_clauses.map((clause, idx) => (
              <div
                key={idx}
                className="bg-slate-900/50 border border-slate-700 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-slate-500">#{idx + 1}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      clause.risk_level === 'HIGH'
                        ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                        : clause.risk_level === 'MEDIUM'
                        ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                        : 'bg-green-500/10 text-green-400 border border-green-500/30'
                    }`}>
                      {clause.risk_level}
                    </span>
                  </div>
                  <span className="text-xs text-cyan-400 font-medium">
                    Influence: {(clause.influence_score * 100).toFixed(0)}
                  </span>
                </div>
                <p className="text-sm text-slate-300">{clause.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Model Info */}
      <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Network size={20} className="text-cyan-400 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-cyan-400 mb-1">GNN Architecture</h4>
            <p className="text-xs text-slate-300 mb-2">
              2× GCN (Graph Convolutional) + 1× GAT (Multi-Head Attention) layers with global mean pooling.
              Trained on historical arbitration outcomes for dispute prediction.
            </p>
            <div className="flex gap-4 text-xs text-slate-400">
              <div>Model: {prediction.model_version}</div>
              <div>Checkpoint: {prediction.model_checkpoint}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
