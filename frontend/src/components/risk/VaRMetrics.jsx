/**
 * Value at Risk (VaR) Metrics Component
 */

import React from 'react';
import { Target, AlertCircle } from 'lucide-react';

export default function VaRMetrics({ data }) {
  if (!data || !data.var) return null;

  const varData = data.var;

  const formatCurrency = (value) => {
    if (!value) return '₹0';
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)} Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(1)} L`;
    return `₹${value.toLocaleString()}`;
  };

  return (
    <div className="space-y-6">
      {/* Main VaR Card */}
      <div className="bg-gradient-to-br from-purple-900 to-gray-800 border border-purple-700 rounded-lg p-8">
        <div className="flex items-center mb-4">
          <Target className="text-purple-400 mr-3" size={32} />
          <div>
            <h2 className="text-2xl font-bold text-white">Value at Risk (VaR)</h2>
            <p className="text-purple-300 text-sm">
              {(varData.confidence_level * 100).toFixed(0)}% Confidence Level
            </p>
          </div>
        </div>

        <div className="text-5xl font-bold text-white mb-2">
          {formatCurrency(varData.var)}
        </div>

        <p className="text-purple-200">
          {varData.interpretation}
        </p>
      </div>

      {/* Comparison Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Mean Exposure</p>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(varData.mean_exposure)}
          </p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">VaR ({(varData.confidence_level * 100).toFixed(0)}%)</p>
          <p className="text-2xl font-bold text-orange-400">
            {formatCurrency(varData.var)}
          </p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Maximum Exposure</p>
          <p className="text-2xl font-bold text-red-400">
            {formatCurrency(varData.max_exposure)}
          </p>
        </div>
      </div>

      {/* Explanation */}
      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="text-blue-400 mr-3 mt-0.5" size={20} />
          <div>
            <p className="font-medium text-blue-300 mb-2">What is VaR?</p>
            <p className="text-blue-200 text-sm">
              Value at Risk (VaR) is the maximum expected loss at a given confidence level.
              This means there's only a {((1 - varData.confidence_level) * 100).toFixed(0)}% chance
              that losses will exceed {formatCurrency(varData.var)}.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
