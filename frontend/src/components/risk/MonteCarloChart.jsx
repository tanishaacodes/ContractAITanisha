/**
 * Monte Carlo Exposure Chart
 * ===========================
 * Visualizes exposure distribution and percentiles
 */

import React from 'react';
import { Activity, TrendingUp, AlertTriangle } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from 'recharts';

export default function MonteCarloChart({ data }) {
  if (!data || !data.monte_carlo) return null;

  const mc = data.monte_carlo;
  const formatCurrency = (value) => {
    if (!value) return '₹0';
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)} Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(1)} L`;
    return `₹${value.toLocaleString()}`;
  };

  // Build distribution data for chart
  const distributionData = mc.distribution
    ? mc.distribution.map((value, index) => ({
        index,
        exposure: value
      }))
    : [];

  // Percentile data
  const percentileData = [
    { label: 'P50', value: mc.p50, color: '#10b981' },
    { label: 'P75', value: mc.p75, color: '#f59e0b' },
    { label: 'P90', value: mc.p90, color: '#ef4444' },
    { label: 'P95', value: mc.p95, color: '#dc2626' },
    { label: 'P99', value: mc.p99, color: '#991b1b' }
  ];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Mean Exposure</span>
            <Activity size={16} className="text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">{formatCurrency(mc.mean)}</p>
          <p className="text-xs text-gray-500 mt-1">{mc.iterations?.toLocaleString()} iterations</p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">P90 (90th %ile)</span>
            <TrendingUp size={16} className="text-orange-400" />
          </div>
          <p className="text-2xl font-bold text-white">{formatCurrency(mc.p90)}</p>
          <p className="text-xs text-gray-500 mt-1">High risk scenario</p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">P95 (95th %ile)</span>
            <AlertTriangle size={16} className="text-red-400" />
          </div>
          <p className="text-2xl font-bold text-white">{formatCurrency(mc.p95)}</p>
          <p className="text-xs text-gray-500 mt-1">Severe stress</p>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Max Exposure</span>
            <AlertTriangle size={16} className="text-red-600" />
          </div>
          <p className="text-2xl font-bold text-white">{formatCurrency(mc.max)}</p>
          <p className="text-xs text-gray-500 mt-1">Worst case simulated</p>
        </div>
      </div>

      {/* Distribution Chart */}
      {distributionData.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-white">
            Exposure Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={distributionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="index"
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af' }}
              />
              <YAxis
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af' }}
                tickFormatter={(value) => formatCurrency(value)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#9ca3af' }}
                itemStyle={{ color: '#fff' }}
                formatter={(value) => [formatCurrency(value), 'Exposure']}
              />
              <Line
                type="monotone"
                dataKey="exposure"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
              />
              <ReferenceLine
                y={mc.p90}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{ value: 'P90', fill: '#f59e0b' }}
              />
              <ReferenceLine
                y={mc.p95}
                stroke="#ef4444"
                strokeDasharray="3 3"
                label={{ value: 'P95', fill: '#ef4444' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Percentile Breakdown */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">
          Percentile Breakdown
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={percentileData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="label"
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
              tickFormatter={(value) => formatCurrency(value)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '8px'
              }}
              formatter={(value) => [formatCurrency(value), 'Exposure']}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {percentileData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Statistics Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">
          Statistical Summary
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <p className="text-gray-400 text-sm">Mean</p>
            <p className="text-lg font-semibold text-white">{formatCurrency(mc.mean)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Std Dev</p>
            <p className="text-lg font-semibold text-white">{formatCurrency(mc.std)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Min</p>
            <p className="text-lg font-semibold text-white">{formatCurrency(mc.min)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Median (P50)</p>
            <p className="text-lg font-semibold text-white">{formatCurrency(mc.p50)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">P75</p>
            <p className="text-lg font-semibold text-white">{formatCurrency(mc.p75)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Max</p>
            <p className="text-lg font-semibold text-white">{formatCurrency(mc.max)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
