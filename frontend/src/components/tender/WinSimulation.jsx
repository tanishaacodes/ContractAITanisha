/**
 * Win Simulation Component
 * Displays win probability analysis and scenario simulations
 */
import React, { useState, useEffect } from 'react';
import tenderService from '../../services/tenderService';

const WinSimulation = ({ tenderId }) => {
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    runSimulation();
  }, [tenderId]);

  const runSimulation = async () => {
    if (!tenderId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await tenderService.simulateWinProbability(tenderId);
      setSimulation(result);
    } catch (err) {
      console.error('Error running simulation:', err);
      setError(err.response?.data?.error || 'Failed to run win simulation. Please ensure your company profile is complete.');
    } finally {
      setLoading(false);
    }
  };

  const getWinProbabilityColor = (probability) => {
    if (probability >= 70) return 'text-green-600';
    if (probability >= 50) return 'text-yellow-600';
    if (probability >= 30) return 'text-orange-600';
    return 'text-red-600';
  };

  const getWinProbabilityBgColor = (probability) => {
    if (probability >= 70) return 'bg-green-600';
    if (probability >= 50) return 'bg-yellow-600';
    if (probability >= 30) return 'bg-orange-600';
    return 'bg-red-600';
  };

  const getWinProbabilityIcon = (probability) => {
    if (probability >= 70) return '🎯';
    if (probability >= 50) return '👍';
    if (probability >= 30) return '⚡';
    return '⚠️';
  };

  const getRecommendation = (probability) => {
    if (probability >= 70) return 'Strong candidate for bidding. High probability of success.';
    if (probability >= 50) return 'Moderate chance of winning. Consider competitive pricing.';
    if (probability >= 30) return 'Lower probability. Requires strategic positioning.';
    return 'Low win probability. Evaluate risks carefully before bidding.';
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-300">Running win probability simulation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-12">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-white mb-2">Simulation Error</h3>
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={runSimulation}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry Simulation
          </button>
        </div>
      </div>
    );
  }

  if (!simulation) {
    return (
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-12">
        <div className="text-center">
          <div className="text-6xl mb-4">🎲</div>
          <h3 className="text-lg font-medium text-white mb-2">No Simulation Data</h3>
          <p className="text-slate-300 mb-4">Run simulation to analyze your win probability</p>
          <button
            onClick={runSimulation}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Run Simulation
          </button>
        </div>
      </div>
    );
  }

  const winProbability = simulation.win_probability || 0;
  const factors = simulation.factors || {};

  return (
    <div className="space-y-6">
      {/* Main Win Probability Card */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg shadow-lg border border-slate-700 p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center">
            <svg className="w-7 h-7 mr-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Win Probability Analysis
          </h2>
          <button
            onClick={runSimulation}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center text-sm"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Win Probability Gauge */}
          <div className="text-center">
            <div className="text-8xl mb-4">{getWinProbabilityIcon(winProbability)}</div>
            <div className={`text-6xl font-bold mb-2 ${getWinProbabilityColor(winProbability)}`}>
              {winProbability.toFixed(1)}%
            </div>
            <div className="text-xl text-slate-300 mb-6">
              Estimated Win Probability
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-700 rounded-full h-4 mb-4">
              <div
                className={`h-4 rounded-full transition-all duration-500 ${getWinProbabilityBgColor(winProbability)}`}
                style={{ width: `${winProbability}%` }}
              ></div>
            </div>

            <p className="text-slate-300 text-sm leading-relaxed">
              {getRecommendation(winProbability)}
            </p>
          </div>

          {/* Contributing Factors */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white mb-4">Contributing Factors</h3>

            {/* Eligibility Score */}
            {factors.eligibility_score !== undefined && (
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-300">Eligibility Compliance</span>
                  <span className={`font-bold ${factors.eligibility_score >= 0.7 ? 'text-green-600' : factors.eligibility_score >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {(factors.eligibility_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${factors.eligibility_score >= 0.7 ? 'bg-green-600' : factors.eligibility_score >= 0.5 ? 'bg-yellow-600' : 'bg-red-600'}`}
                    style={{ width: `${factors.eligibility_score * 100}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Risk Score */}
            {factors.risk_score !== undefined && (
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-300">Risk Factor</span>
                  <span className={`font-bold ${factors.risk_score <= 0.3 ? 'text-green-600' : factors.risk_score <= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {(factors.risk_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${factors.risk_score <= 0.3 ? 'bg-green-600' : factors.risk_score <= 0.6 ? 'bg-yellow-600' : 'bg-red-600'}`}
                    style={{ width: `${factors.risk_score * 100}%` }}
                  ></div>
                </div>
                <p className="text-xs text-slate-400 mt-1">Lower is better</p>
              </div>
            )}

            {/* Competitiveness */}
            {factors.competitiveness !== undefined && (
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-300">Company Competitiveness</span>
                  <span className={`font-bold ${factors.competitiveness >= 0.7 ? 'text-green-600' : factors.competitiveness >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {(factors.competitiveness * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${factors.competitiveness >= 0.7 ? 'bg-green-600' : factors.competitiveness >= 0.5 ? 'bg-yellow-600' : 'bg-red-600'}`}
                    style={{ width: `${factors.competitiveness * 100}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Scenario Analysis */}
      {simulation.scenario_analysis && (
        <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
            Scenario Analysis
          </h3>
          <div className="space-y-3">
            {simulation.scenario_analysis.best_case && (
              <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-green-400">Best Case</div>
                    <div className="text-xs text-slate-400 mt-1">Optimal conditions</div>
                  </div>
                  <div className="text-2xl font-bold text-green-600">
                    {simulation.scenario_analysis.best_case}%
                  </div>
                </div>
              </div>
            )}

            {simulation.scenario_analysis.realistic && (
              <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-blue-400">Realistic</div>
                    <div className="text-xs text-slate-400 mt-1">Expected outcome</div>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">
                    {simulation.scenario_analysis.realistic}%
                  </div>
                </div>
              </div>
            )}

            {simulation.scenario_analysis.worst_case && (
              <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-red-400">Worst Case</div>
                    <div className="text-xs text-slate-400 mt-1">Conservative estimate</div>
                  </div>
                  <div className="text-2xl font-bold text-red-600">
                    {simulation.scenario_analysis.worst_case}%
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Key Insights */}
      {simulation.insights && simulation.insights.length > 0 && (
        <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Key Insights
          </h3>
          <ul className="space-y-2">
            {simulation.insights.map((insight, index) => (
              <li key={index} className="flex items-start text-slate-300">
                <svg className="w-5 h-5 mr-2 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                <span className="text-sm">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {simulation.recommendations && simulation.recommendations.length > 0 && (
        <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Recommendations
          </h3>
          <ul className="space-y-3">
            {simulation.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-600 text-white text-xs flex items-center justify-center mr-3 mt-0.5">
                  {index + 1}
                </span>
                <span className="text-sm text-slate-300">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default WinSimulation;
