import React, { useState, useEffect } from 'react';
import { AlertTriangle, Loader2, Info } from 'lucide-react';
import HeatmapCell from './HeatmapCell';
import { silentRiskAPI } from '../../services/negotiationAPI';

/**
 * SilentRiskHeatmap Component
 * Main visualization for cross-clause silent risks
 * Shows a matrix of clause interactions with color-coded risk levels
 */
const SilentRiskHeatmap = ({ contractId, cachedData, onDataLoaded }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [risks, setRisks] = useState([]);

  useEffect(() => {
    if (contractId) {
      // Always load from backend - it will check database cache automatically
      console.log('Loading Silent Risk data for contract:', contractId);
      loadHeatmapData();
    }
  }, [contractId]);

  const loadHeatmapData = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      const heatmapResult = await silentRiskAPI.getHeatmap(contractId, forceRefresh);
      setHeatmapData(heatmapResult);

      // Also load risks and cache both together
      const risksResult = await silentRiskAPI.detectRisks(contractId);
      const risksData = risksResult.silent_risks || [];
      setRisks(risksData);

      // Notify parent to cache this data
      if (onDataLoaded) {
        onDataLoaded({
          heatmapData: heatmapResult,
          risks: risksData
        });
      }
    } catch (err) {
      console.error('Error loading heatmap:', err);
      setError('Failed to load silent risk heatmap');
    } finally {
      setLoading(false);
    }
  };

  const loadRisks = async () => {
    // This function is now integrated into loadHeatmapData
    // Keeping it for backward compatibility but it's no longer called separately
    try {
      const data = await silentRiskAPI.detectRisks(contractId);
      setRisks(data.silent_risks || []);
    } catch (err) {
      console.error('Error loading risks:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 bg-slate-800/60 backdrop-blur-xl rounded-xl border border-cyan-500/20">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <span className="ml-3 text-slate-300">Analyzing clause interactions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 backdrop-blur-xl">
        <div className="flex items-center gap-2 text-red-400">
          <AlertTriangle className="w-5 h-5" />
          <span className="font-semibold">{error}</span>
        </div>
      </div>
    );
  }

  if (!heatmapData || !heatmapData.clauses || heatmapData.clauses.length === 0) {
    return (
      <div className="bg-slate-800/60 border border-slate-600/30 rounded-xl p-6 backdrop-blur-xl">
        <div className="flex items-center gap-2 text-slate-400">
          <Info className="w-5 h-5" />
          <span>No clauses available for analysis</span>
        </div>
      </div>
    );
  }

  // Filter out null/undefined clauses and ensure matrix exists
  const { clauses: rawClauses = [], matrix = {} } = heatmapData;
  const clauses = rawClauses.filter(clause => clause != null && clause !== '');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between bg-slate-800/60 backdrop-blur-xl rounded-xl p-6 border border-red-500/20">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-red-400" style={{ filter: 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.5))' }} />
            Silent Risk Heatmap
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Clause Interaction Analysis - {risks.length} risk(s) detected
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4">
          <div className="text-xs text-slate-300 font-semibold">Risk Level:</div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-green-400 rounded border border-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.3)]" />
            <span className="text-xs text-slate-300">Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-yellow-500 rounded border border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.3)]" />
            <span className="text-xs text-slate-300">Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-red-600 rounded border border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.3)]" />
            <span className="text-xs text-slate-300">High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-red-900 rounded border border-red-900/50 shadow-[0_0_10px_rgba(127,29,29,0.3)]" />
            <span className="text-xs text-slate-300">Critical</span>
          </div>
        </div>
      </div>

      {/* Heatmap Container */}
      <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl shadow-[0_0_30px_rgba(6,182,212,0.1)] border border-slate-700/50 p-6">
        <div className="overflow-x-auto">
          <div className="inline-block min-w-full">
            {/* Column Headers with proper spacing */}
            <div className="flex mb-2" style={{ paddingLeft: '160px' }}>
              {clauses.map((clause, idx) => (
                <div
                  key={idx}
                  className="flex items-start justify-center"
                  style={{ width: '100px', height: '100px' }}
                >
                  <div
                    className="text-xs font-semibold text-cyan-300 whitespace-nowrap"
                    style={{
                      transform: 'rotate(-45deg)',
                      transformOrigin: 'center center',
                      marginTop: '50px'
                    }}
                  >
                    {clause && clause.length > 20 ? clause.substring(0, 20) + '...' : clause || 'N/A'}
                  </div>
                </div>
              ))}
            </div>

            {/* Rows */}
            {clauses.map((rowClause, rowIdx) => (
              <div key={rowIdx} className="flex items-center mb-1">
                {/* Row Header */}
                <div className="w-40 pr-4 text-right flex-shrink-0">
                  <span className="text-xs font-semibold text-cyan-300">
                    {rowClause || 'N/A'}
                  </span>
                </div>

                {/* Cells */}
                <div className="flex gap-1">
                  {clauses.map((colClause, colIdx) => {
                    const key = `${rowClause}|${colClause}`;
                    const risk = matrix[key];

                    return (
                      <HeatmapCell
                        key={colIdx}
                        risk={risk}
                        clauseA={rowClause}
                        clauseB={colClause}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Risk Summary */}
      {risks.length > 0 && (
        <div className="bg-red-500/10 border-2 border-red-500/30 rounded-xl p-6 backdrop-blur-xl">
          <h3 className="text-lg font-bold text-red-400 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" style={{ filter: 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.5))' }} />
            Top Silent Risks
          </h3>
          <div className="space-y-3">
            {risks.slice(0, 3).map((risk, idx) => (
              <div key={idx} className="bg-slate-900/60 rounded-lg p-4 border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-white text-sm mb-1">
                      {risk.risk_type.replace(/_/g, ' ')}
                    </h4>
                    <p className="text-xs text-slate-400 mb-2">
                      {risk.clause_pair ? `${risk.clause_pair[0]} + ${risk.clause_pair[1]} interaction creates latent risk` : risk.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs">
                      <span className="text-red-400 font-semibold">
                        Exposure: ₹{(risk.financial_exposure / 10000000).toFixed(1)} Cr
                      </span>
                      <span className="text-cyan-400 font-semibold">
                        Confidence: {Math.round(risk.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${risk.severity === 'CRITICAL' ? 'bg-red-900 text-white shadow-[0_0_10px_rgba(127,29,29,0.5)]' : risk.severity === 'HIGH' ? 'bg-red-600 text-white shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-yellow-500 text-slate-900 shadow-[0_0_10px_rgba(234,179,8,0.5)]'}`}>
                    {risk.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analyze Again Button */}
      {heatmapData && !loading && (
        <div className="bg-slate-800/60 backdrop-blur-xl border border-cyan-500/20 rounded-xl p-6 text-center">
          <button
            onClick={() => loadHeatmapData(true)}
            className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-bold text-sm shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all duration-300 transform hover:scale-105"
          >
            <AlertTriangle className="w-4 h-4 inline-block mr-2" />
            Analyze Again
          </button>
          <p className="text-xs text-slate-400 mt-2">
            Re-run analysis to detect new risks with updated patterns
          </p>
        </div>
      )}
    </div>
  );
};

export default SilentRiskHeatmap;
