/**
 * Cascading Risks Visualization
 * ==============================
 * Shows multi-hop risk propagation analysis with depth visualization
 */

import React, { useState } from 'react';
import { TrendingDown, AlertCircle, Layers, ArrowRight } from 'lucide-react';

export default function CascadingRisksView({ data }) {
  const [expandedRisks, setExpandedRisks] = useState(new Set());

  if (!data || !data.analysis) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
        <TrendingDown className="mx-auto text-gray-600 mb-4" size={48} />
        <p className="text-gray-400">No cascading risk data available</p>
      </div>
    );
  }

  const { analysis } = data;
  const cascadingRisks = analysis.cascading_risks || [];
  const paths = analysis.paths || [];

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': 'text-red-500 bg-red-900/30 border-red-700',
      'HIGH': 'text-orange-500 bg-orange-900/30 border-orange-700',
      'MEDIUM': 'text-yellow-500 bg-yellow-900/30 border-yellow-700',
      'LOW': 'text-green-500 bg-green-900/30 border-green-700'
    };
    return colors[severity] || colors['MEDIUM'];
  };

  const getDepthColor = (depth) => {
    const colors = ['text-purple-400', 'text-blue-400', 'text-cyan-400', 'text-teal-400', 'text-emerald-400'];
    return colors[Math.min(depth - 1, colors.length - 1)];
  };

  const toggleExpand = (riskId) => {
    setExpandedRisks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(riskId)) {
        newSet.delete(riskId);
      } else {
        newSet.add(riskId);
      }
      return newSet;
    });
  };

  // Group risks by depth
  const risksByDepth = cascadingRisks.reduce((acc, risk) => {
    if (!acc[risk.depth]) acc[risk.depth] = [];
    acc[risk.depth].push(risk);
    return acc;
  }, {});

  const maxDepth = Math.max(...Object.keys(risksByDepth).map(Number), 0);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Source Risk</p>
          <p className="text-2xl font-bold text-white">{analysis.source_risk}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Cascading Risks</p>
          <p className="text-3xl font-bold text-orange-400">{analysis.total_cascading_risks}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Max Depth</p>
          <p className="text-3xl font-bold text-purple-400">{analysis.max_depth_reached}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Total Impact</p>
          <p className="text-3xl font-bold text-red-400">{analysis.total_impact.toFixed(2)}</p>
        </div>
      </div>

      {/* Propagation Flow Visualization */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white flex items-center">
          <Layers className="mr-2 text-purple-400" size={20} />
          Risk Propagation Flow (by depth)
        </h3>

        <div className="space-y-6">
          {[...Array(maxDepth)].map((_, idx) => {
            const depth = idx + 1;
            const risksAtDepth = risksByDepth[depth] || [];

            return (
              <div key={depth} className="flex items-start gap-4">
                {/* Depth indicator */}
                <div className="flex flex-col items-center">
                  <div className={`w-16 h-16 rounded-full bg-gray-700 border-2 border-purple-500 flex items-center justify-center ${getDepthColor(depth)}`}>
                    <span className="font-bold">{depth}</span>
                  </div>
                  {depth < maxDepth && (
                    <ArrowRight className="text-gray-600 rotate-90 my-2" size={20} />
                  )}
                </div>

                {/* Risks at this depth */}
                <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {risksAtDepth.map((risk) => (
                    <div
                      key={risk.risk_id}
                      className={`border rounded-lg p-3 ${getSeverityColor(risk.severity)}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-sm mb-1">{risk.category}</p>
                          <p className="text-xs opacity-75">Severity: {risk.severity}</p>
                          <div className="mt-2 flex items-center gap-2">
                            <span className="text-xs opacity-75">Impact:</span>
                            <span className="text-sm font-bold">{risk.cumulative_impact.toFixed(3)}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => toggleExpand(risk.risk_id)}
                          className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
                        >
                          {expandedRisks.has(risk.risk_id) ? 'Hide' : 'Paths'}
                        </button>
                      </div>

                      {/* Expanded paths */}
                      {expandedRisks.has(risk.risk_id) && (
                        <div className="mt-3 pt-3 border-t border-gray-600">
                          <p className="text-xs font-medium mb-2">Propagation Paths:</p>
                          <div className="space-y-1">
                            {paths
                              .filter(p => p.target === risk.risk_id)
                              .slice(0, 3)
                              .map((path, idx) => (
                                <div key={idx} className="text-xs opacity-75 font-mono">
                                  {path.path.join(' → ')}
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* All Cascading Risks Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white flex items-center">
          <AlertCircle className="mr-2 text-orange-400" size={20} />
          All Cascading Risks ({cascadingRisks.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-2 px-3 text-gray-400 font-medium">Risk Category</th>
                <th className="text-left py-2 px-3 text-gray-400 font-medium">Severity</th>
                <th className="text-center py-2 px-3 text-gray-400 font-medium">Depth</th>
                <th className="text-right py-2 px-3 text-gray-400 font-medium">Impact</th>
                <th className="text-right py-2 px-3 text-gray-400 font-medium">Multiplier</th>
              </tr>
            </thead>
            <tbody>
              {cascadingRisks.map((risk, idx) => (
                <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                  <td className="py-2 px-3 text-white font-medium">{risk.category}</td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(risk.severity)}`}>
                      {risk.severity}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className={`font-bold ${getDepthColor(risk.depth)}`}>
                      {risk.depth}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right text-orange-400 font-bold">
                    {risk.cumulative_impact.toFixed(3)}
                  </td>
                  <td className="py-2 px-3 text-right text-gray-300">
                    {risk.base_multiplier.toFixed(2)}x
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
