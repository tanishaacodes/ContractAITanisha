/**
 * Blast Radius Visualization
 * ===========================
 * Shows impact scope of each risk in the contract
 */

import React, { useState } from 'react';
import { Zap, AlertTriangle, Target, ChevronDown, ChevronUp } from 'lucide-react';

export default function BlastRadiusView({ data }) {
  const [expandedRisks, setExpandedRisks] = useState(new Set());
  const [sortBy, setSortBy] = useState('blast_radius'); // blast_radius, severity, max_depth

  if (!data || !data.analysis) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
        <Zap className="mx-auto text-gray-600 mb-4" size={48} />
        <p className="text-gray-400">No blast radius data available</p>
      </div>
    );
  }

  const { analysis } = data;
  const risks = analysis.risks || [];
  const highImpactRisks = analysis.high_impact_risks || [];

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': 'text-red-500 bg-red-900/30 border-red-700',
      'HIGH': 'text-orange-500 bg-orange-900/30 border-orange-700',
      'MEDIUM': 'text-yellow-500 bg-yellow-900/30 border-yellow-700',
      'LOW': 'text-green-500 bg-green-900/30 border-green-700'
    };
    return colors[severity] || colors['MEDIUM'];
  };

  const getBlastRadiusColor = (radius) => {
    if (radius >= 5) return 'text-red-500';
    if (radius >= 3) return 'text-orange-500';
    if (radius >= 1) return 'text-yellow-500';
    return 'text-gray-500';
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

  // Sort risks
  const sortedRisks = [...risks].sort((a, b) => {
    if (sortBy === 'blast_radius') return b.blast_radius - a.blast_radius;
    if (sortBy === 'max_depth') return b.max_depth - a.max_depth;
    const severityOrder = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
    return severityOrder[b.severity] - severityOrder[a.severity];
  });

  const maxRadius = Math.max(...risks.map(r => r.blast_radius), 1);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Total Risks</p>
          <p className="text-3xl font-bold text-white">{risks.length}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Total Blast Radius</p>
          <p className="text-3xl font-bold text-orange-400">{analysis.total_blast_radius}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">High Impact Risks</p>
          <p className="text-3xl font-bold text-red-400">{highImpactRisks.length}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Analysis Depth</p>
          <p className="text-3xl font-bold text-purple-400">{analysis.analysis_depth}</p>
        </div>
      </div>

      {/* High Impact Risks */}
      {highImpactRisks.length > 0 && (
        <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-700/50 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-white flex items-center">
            <AlertTriangle className="mr-2 text-red-400" size={20} />
            High Impact Risks (≥3 affected risks)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {highImpactRisks.map((risk) => (
              <div
                key={risk.risk_id}
                className="bg-gray-800/50 border border-red-700/50 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-medium text-white">{risk.category}</p>
                    <p className="text-sm text-gray-400">{risk.severity}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-red-400">{risk.blast_radius}</p>
                    <p className="text-xs text-gray-400">affected</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <Target size={14} />
                  <span>Max depth: {risk.max_depth} hops</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sort Controls */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-400">Sort by:</span>
        <button
          onClick={() => setSortBy('blast_radius')}
          className={`px-3 py-1 rounded text-sm ${
            sortBy === 'blast_radius'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Blast Radius
        </button>
        <button
          onClick={() => setSortBy('severity')}
          className={`px-3 py-1 rounded text-sm ${
            sortBy === 'severity'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Severity
        </button>
        <button
          onClick={() => setSortBy('max_depth')}
          className={`px-3 py-1 rounded text-sm ${
            sortBy === 'max_depth'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          Max Depth
        </button>
      </div>

      {/* Blast Radius Visualization */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white flex items-center">
          <Zap className="mr-2 text-orange-400" size={20} />
          Risk Impact Analysis
        </h3>

        <div className="space-y-3">
          {sortedRisks.map((risk) => {
            const radiusPercent = (risk.blast_radius / maxRadius) * 100;
            const isExpanded = expandedRisks.has(risk.risk_id);

            return (
              <div
                key={risk.risk_id}
                className="bg-gray-700/50 border border-gray-600 rounded-lg overflow-hidden"
              >
                {/* Main Risk Row */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3 flex-1">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(risk.severity)}`}>
                        {risk.severity}
                      </span>
                      <span className="font-medium text-white">{risk.category}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className={`text-2xl font-bold ${getBlastRadiusColor(risk.blast_radius)}`}>
                          {risk.blast_radius}
                        </p>
                        <p className="text-xs text-gray-400">blast radius</p>
                      </div>
                      {risk.affected_risks.length > 0 && (
                        <button
                          onClick={() => toggleExpand(risk.risk_id)}
                          className="p-2 hover:bg-gray-600 rounded"
                        >
                          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Blast Radius Bar */}
                  <div className="relative w-full h-2 bg-gray-600 rounded-full overflow-hidden">
                    <div
                      className={`absolute left-0 top-0 h-full transition-all duration-300 ${
                        risk.blast_radius >= 5 ? 'bg-red-500' :
                        risk.blast_radius >= 3 ? 'bg-orange-500' :
                        risk.blast_radius >= 1 ? 'bg-yellow-500' :
                        'bg-gray-500'
                      }`}
                      style={{ width: `${radiusPercent}%` }}
                    />
                  </div>

                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>Max depth: {risk.max_depth} hops</span>
                    <span>•</span>
                    <span>{risk.affected_risks.length} affected risks</span>
                  </div>
                </div>

                {/* Expanded - Affected Risks */}
                {isExpanded && risk.affected_risks.length > 0 && (
                  <div className="border-t border-gray-600 p-4 bg-gray-800/50">
                    <p className="text-sm font-medium text-gray-300 mb-3">Affected Risks:</p>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                      {risk.affected_risks.map((affected, idx) => (
                        <div
                          key={idx}
                          className={`text-xs p-2 rounded border ${getSeverityColor(affected.severity)}`}
                        >
                          <p className="font-medium">{affected.category}</p>
                          <p className="opacity-75">{affected.severity}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
