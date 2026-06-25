/**
 * Margin Optimization Component
 * Displays bid scenarios and win probability analysis
 */
import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import tenderService from '../../services/tenderService';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const MarginOptimization = ({ tenderId, scenarios: initialScenarios = [] }) => {
  const [scenarios, setScenarios] = useState(initialScenarios);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [optimizationData, setOptimizationData] = useState(null);

  const runOptimization = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await tenderService.optimizeMargin(tenderId, [5, 25], 5);
      setScenarios(result.scenarios);
      setOptimizationData(result);
    } catch (err) {
      console.error('Optimization error:', err);
      setError(err.response?.data?.error || 'Failed to optimize margin');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialScenarios.length === 0) {
      runOptimization();
    }
  }, []);

  const formatCurrency = (value) => {
    return `₹${(value / 10000000).toFixed(2)} Cr`;
  };

  // Prepare chart data
  const chartData = {
    labels: scenarios.map((s) => `${s.margin_percentage}%`),
    datasets: [
      {
        label: 'Win Probability (%)',
        data: scenarios.map((s) => s.win_probability),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        yAxisID: 'y',
      },
      {
        label: 'Expected Profit (Cr)',
        data: scenarios.map((s) => s.expected_profit / 10000000),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        yAxisID: 'y1',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Margin vs Win Probability & Expected Profit',
      },
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Win Probability (%)',
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Expected Profit (Cr)',
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  const optimal = scenarios.find((s) => s.is_recommended) || scenarios[0];

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-slate-300">Optimizing margin scenarios...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-6">
        <p className="text-red-800">{error}</p>
        <button
          onClick={runOptimization}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Optimal Recommendation */}
      {optimal && (
        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg shadow-lg p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium mb-1 opacity-90">Recommended Bid Price</div>
              <div className="text-4xl font-bold mb-2">{formatCurrency(optimal.bid_price)}</div>
              <div className="text-lg opacity-90">
                Margin: {optimal.margin_percentage}% | Win Probability: {optimal.win_probability}%
              </div>
            </div>
            <div className="text-6xl">🎯</div>
          </div>
        </div>
      )}

      {/* Cost Breakdown */}
      {optimizationData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-4">
            <div className="text-sm text-slate-400 mb-1">Base Cost</div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(optimizationData.cost_breakdown.base_cost)}
            </div>
          </div>
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-4">
            <div className="text-sm text-slate-400 mb-1">Material</div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(optimizationData.cost_breakdown.material_cost)}
            </div>
          </div>
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-4">
            <div className="text-sm text-slate-400 mb-1">Labor</div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(optimizationData.cost_breakdown.labor_cost)}
            </div>
          </div>
          <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-4">
            <div className="text-sm text-slate-400 mb-1">Equipment</div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(optimizationData.cost_breakdown.equipment_cost)}
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* Scenarios Table */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 overflow-hidden">
        <div className="px-6 py-4 bg-slate-900 border-b border-slate-700">
          <h3 className="text-lg font-bold text-white">Bid Scenarios</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-slate-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">Margin</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase">Bid Price</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase">Gross Profit</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase">Win Probability</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase">Expected Profit</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-slate-400 uppercase">Recommended</th>
              </tr>
            </thead>
            <tbody className="bg-slate-800 divide-y divide-gray-200">
              {scenarios.map((scenario, index) => (
                <tr key={index} className={scenario.is_recommended ? 'bg-green-900/30' : 'hover:bg-slate-900'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                    {scenario.margin_percentage}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                    {formatCurrency(scenario.bid_price)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-white">
                    {formatCurrency(scenario.gross_profit)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      scenario.win_probability >= 70 ? 'bg-green-100 text-green-800' :
                      scenario.win_probability >= 50 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {scenario.win_probability}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-white">
                    {formatCurrency(scenario.expected_profit)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {scenario.is_recommended && (
                      <span className="text-green-600 font-bold">✓</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end space-x-4">
        <button
          onClick={runOptimization}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Recalculate
        </button>
      </div>
    </div>
  );
};

export default MarginOptimization;
