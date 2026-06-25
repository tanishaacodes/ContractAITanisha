/**
 * Stress Test Scenarios Table
 */

import React from 'react';
import { AlertTriangle, TrendingUp } from 'lucide-react';

export default function StressTestTable({ data }) {
  if (!data || !data.stress_test) return null;

  const stressData = data.stress_test;
  const scenarios = stressData.scenarios || {};

  const scenarioList = [
    { key: 'base_case', label: 'Base Case', severity: 'LOW', color: 'green' },
    { key: 'moderate_stress', label: 'Moderate Stress', severity: 'MEDIUM', color: 'yellow' },
    { key: 'severe_stress', label: 'Severe Stress', severity: 'HIGH', color: 'orange' },
    { key: 'extreme_stress', label: 'Extreme Stress', severity: 'CRITICAL', color: 'red' },
    { key: 'worst_case', label: 'Worst Case', severity: 'MAX', color: 'red' }
  ];

  const getColorClasses = (color) => {
    const colors = {
      green: 'bg-green-900/30 text-green-300 border-green-700',
      yellow: 'bg-yellow-900/30 text-yellow-300 border-yellow-700',
      orange: 'bg-orange-900/30 text-orange-300 border-orange-700',
      red: 'bg-red-900/30 text-red-300 border-red-700'
    };
    return colors[color] || colors.green;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center">
        <AlertTriangle className="text-orange-400 mr-3" size={28} />
        <div>
          <h2 className="text-2xl font-bold text-white">Stress Test Scenarios</h2>
          <p className="text-gray-400 text-sm">
            {stressData.iterations?.toLocaleString()} iterations per scenario
          </p>
        </div>
      </div>

      {/* Scenarios Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Scenario
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Severity
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                Exposure
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Description
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {scenarioList.map((scenario) => {
              const scenarioData = scenarios[scenario.key];
              if (!scenarioData) return null;

              return (
                <tr key={scenario.key} className="hover:bg-gray-700/50 transition">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-medium text-white">{scenario.label}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getColorClasses(scenario.color)}`}>
                      {scenario.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className="text-lg font-bold text-white">
                      {scenarioData.exposure_formatted}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-400">
                      {scenarioData.description}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Contract Value Reference */}
      {stressData.contract_value && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Contract Value</p>
              <p className="text-xl font-bold text-white mt-1">
                {stressData.contract_value_formatted}
              </p>
            </div>
            <TrendingUp className="text-purple-400" size={24} />
          </div>
        </div>
      )}
    </div>
  );
}
