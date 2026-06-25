import { useState } from 'react';
import useThemeStore from '../store/themeStore';

const RiskMatrixHeatmap = ({ data = [] }) => {
  const { theme } = useThemeStore();
  const [selectedCell, setSelectedCell] = useState(null);

  // 5x5 Matrix configuration
  const likelihood = ['Improbable', 'Remote', 'Occasional', 'Probable', 'Frequent'];
  const impact = ['Negligible', 'Low', 'Moderate', 'Significant', 'Catastrophic'];

  // Calculate risk score for each cell (Impact × Likelihood)
  const getRiskScore = (impactLevel, likelihoodLevel) => {
    return (impactLevel + 1) * (likelihoodLevel + 1);
  };

  // Get color based on risk score
  const getCellColor = (score) => {
    if (score <= 5) return '#22c55e'; // Green - Desirable/No Action
    if (score <= 9) return '#84cc16'; // Light Green - Acceptable/Monitor
    if (score <= 12) return '#eab308'; // Yellow - Undesirable/Action
    if (score <= 16) return '#f97316'; // Orange - Unacceptable/Urgent
    return '#ef4444'; // Red - Catastrophic/Stop
  };

  // Get risk level text
  const getRiskLevel = (score) => {
    if (score <= 5) return 'LOW';
    if (score <= 9) return 'MEDIUM';
    if (score <= 12) return 'HIGH';
    if (score <= 16) return 'CRITICAL';
    return 'CATASTROPHIC';
  };

  // Get contracts in each cell
  const getContractsInCell = (impactLevel, likelihoodLevel) => {
    if (!data || data.length === 0) return [];
    return data.filter(item => {
      const itemImpact = Math.floor(item.impact_score * 5);
      const itemLikelihood = Math.floor(item.likelihood_score * 5);
      return itemImpact === impactLevel && itemLikelihood === likelihoodLevel;
    });
  };

  // Count contracts in each cell
  const getContractCount = (impactLevel, likelihoodLevel) => {
    return getContractsInCell(impactLevel, likelihoodLevel).length;
  };

  return (
    <div className={`${theme.colors.surface} rounded-lg p-6 border ${theme.colors.surfaceBorder}`}>
      <div className="mb-8">
        <h2 className={`text-2xl font-bold ${theme.colors.textPrimary} mb-2 flex items-center gap-2`}>
          <svg className="w-7 h-7 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          5×5 Risk Matrix (Likelihood × Impact)
        </h2>
        <p className={`${theme.colors.textSecondary} flex items-center gap-2`}>
          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
          Interactive Enterprise Risk Management Heatmap - <span className="font-semibold">Click any cell for detailed analysis</span>
        </p>
      </div>

      {/* Matrix Grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[800px]">
          {/* Header with Likelihood labels */}
          <div className="flex mb-2">
            <div className="w-32"></div>
            <div className="flex-1 grid grid-cols-5 gap-2">
              {likelihood.map((label, idx) => (
                <div
                  key={idx}
                  className={`text-center text-sm font-semibold ${theme.colors.textPrimary} p-2`}
                >
                  {idx + 1}. {label}
                </div>
              ))}
            </div>
          </div>

          {/* Likelihood Label (top right) */}
          <div className="flex mb-4">
            <div className="w-32"></div>
            <div className="flex-1 text-center">
              <span className={`text-lg font-bold ${theme.colors.textPrimary}`}>
                LIKELIHOOD →
              </span>
            </div>
          </div>

          {/* Matrix Rows */}
          {[...impact].reverse().map((impactLabel, rowIdx) => {
            const impactLevel = 4 - rowIdx;
            return (
              <div key={impactLevel} className="flex mb-2">
                {/* Impact Label */}
                <div className="w-32 flex items-center justify-end pr-4">
                  <div className="text-right">
                    <div className={`text-sm font-semibold ${theme.colors.textPrimary}`}>
                      {impactLevel + 1}. {impactLabel}
                    </div>
                  </div>
                </div>

                {/* Row Cells */}
                <div className="flex-1 grid grid-cols-5 gap-2">
                  {likelihood.map((_, likelihoodLevel) => {
                    const score = getRiskScore(impactLevel, likelihoodLevel);
                    const contractCount = getContractCount(impactLevel, likelihoodLevel);
                    const color = getCellColor(score);

                    const isSelected = selectedCell?.impactLevel === impactLevel && selectedCell?.likelihoodLevel === likelihoodLevel;

                    return (
                      <button
                        key={likelihoodLevel}
                        onClick={() => {
                          const contracts = getContractsInCell(impactLevel, likelihoodLevel);
                          setSelectedCell({ impactLevel, likelihoodLevel, score, contractCount, contracts });
                        }}
                        className={`relative h-20 rounded-lg transition-all cursor-pointer border-4 ${
                          isSelected ? 'border-white scale-105 shadow-2xl' : 'border-transparent hover:border-white/50 hover:scale-105 hover:shadow-xl'
                        }`}
                        style={{ backgroundColor: color }}
                      >
                        <div className="text-white flex flex-col items-center justify-center h-full">
                          <div className="text-3xl font-bold drop-shadow-lg">{score}</div>
                          {contractCount > 0 && (
                            <div className="text-xs mt-1 bg-black/30 backdrop-blur-sm rounded-full px-3 py-1">
                              {contractCount} {contractCount === 1 ? 'contract' : 'contracts'}
                            </div>
                          )}
                        </div>
                        {isSelected && (
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-white rounded-full animate-pulse"></div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Impact Label (vertical) */}
          <div className="flex mt-4">
            <div className="w-32"></div>
            <div className="flex-1 text-center">
              <span className={`text-lg font-bold ${theme.colors.textPrimary}`}>
                ↑ IMPACT
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: '#22c55e' }}></div>
          <div>
            <div className={`text-xs font-semibold ${theme.colors.textPrimary}`}>1-5: LOW</div>
            <div className={`text-xs ${theme.colors.textSecondary}`}>Desirable</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: '#84cc16' }}></div>
          <div>
            <div className={`text-xs font-semibold ${theme.colors.textPrimary}`}>6-9: MEDIUM</div>
            <div className={`text-xs ${theme.colors.textSecondary}`}>Acceptable</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: '#eab308' }}></div>
          <div>
            <div className={`text-xs font-semibold ${theme.colors.textPrimary}`}>10-12: HIGH</div>
            <div className={`text-xs ${theme.colors.textSecondary}`}>Action Needed</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: '#f97316' }}></div>
          <div>
            <div className={`text-xs font-semibold ${theme.colors.textPrimary}`}>13-16: CRITICAL</div>
            <div className={`text-xs ${theme.colors.textSecondary}`}>Urgent Action</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded" style={{ backgroundColor: '#ef4444' }}></div>
          <div>
            <div className={`text-xs font-semibold ${theme.colors.textPrimary}`}>17-25: CATASTROPHIC</div>
            <div className={`text-xs ${theme.colors.textSecondary}`}>Stop Activity</div>
          </div>
        </div>
      </div>

      {/* Selected Cell Details */}
      {selectedCell && (
        <div className="mt-8 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-2 border-blue-500/30 rounded-xl p-6 shadow-lg animate-fadeIn">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-xl font-bold text-blue-400">Selected Cell Analysis</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-black/20 rounded-lg p-4">
              <div className={`text-xs ${theme.colors.textSecondary} mb-1 uppercase tracking-wide`}>Risk Score</div>
              <div className={`text-3xl font-bold ${theme.colors.textPrimary}`}>
                {selectedCell.score}
              </div>
            </div>
            <div className="bg-black/20 rounded-lg p-4">
              <div className={`text-xs ${theme.colors.textSecondary} mb-1 uppercase tracking-wide`}>Risk Level</div>
              <div className={`text-lg font-bold ${theme.colors.textPrimary}`}>
                {getRiskLevel(selectedCell.score)}
              </div>
            </div>
            <div className="bg-black/20 rounded-lg p-4">
              <div className={`text-xs ${theme.colors.textSecondary} mb-1 uppercase tracking-wide`}>Contracts</div>
              <div className={`text-3xl font-bold ${theme.colors.textPrimary}`}>
                {selectedCell.contractCount}
              </div>
            </div>
            <div className="bg-black/20 rounded-lg p-4">
              <div className={`text-xs ${theme.colors.textSecondary} mb-1 uppercase tracking-wide`}>Action Required</div>
              <div className={`text-sm font-bold ${theme.colors.textPrimary}`}>
                {selectedCell.score <= 5 ? '✓ Monitor' : selectedCell.score <= 12 ? '⚠ Mitigate' : '🚨 Immediate Action'}
              </div>
            </div>
          </div>

          {/* Contracts List */}
          {selectedCell.contracts && selectedCell.contracts.length > 0 && (
            <div className="mt-4">
              <h4 className={`text-sm font-semibold ${theme.colors.textPrimary} mb-3 uppercase tracking-wide`}>
                Contracts in this Risk Cell:
              </h4>
              <div className="space-y-2">
                {selectedCell.contracts.map((contract, index) => (
                  <div
                    key={contract.contract_id || index}
                    className={`flex items-center justify-between p-3 rounded-lg bg-black/10 border border-white/10 hover:bg-black/20 transition-all`}
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getCellColor(selectedCell.score) }}></div>
                      <span className={`font-medium ${theme.colors.textPrimary} truncate`}>
                        {contract.contract_name || `Contract ${index + 1}`}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className={`text-xs ${theme.colors.textSecondary}`}>Impact</div>
                        <div className={`text-sm font-bold ${theme.colors.textPrimary}`}>
                          {(contract.impact_score * 5).toFixed(1)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-xs ${theme.colors.textSecondary}`}>Likelihood</div>
                        <div className={`text-sm font-bold ${theme.colors.textPrimary}`}>
                          {(contract.likelihood_score * 5).toFixed(1)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskMatrixHeatmap;
