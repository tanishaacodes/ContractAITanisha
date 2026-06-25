/**
 * Contract Comparison Dashboard
 * ==============================
 * Compare concept profiles between two contracts side-by-side.
 */

import React, { useState, useEffect } from 'react';
import { compareContracts } from '../services/conceptGraphService';
import api from '../utils/api';
import { GitCompare, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const ContractComparisonDashboard = () => {
  const [contracts, setContracts] = useState([]);
  const [contract1, setContract1] = useState(null);
  const [contract2, setContract2] = useState(null);
  const [loading, setLoading] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      const response = await api.get('/contracts/list');
      setContracts(response.data.contracts || []);
    } catch (err) {
      console.error('Failed to fetch contracts:', err);
    }
  };

  const handleCompare = async () => {
    if (!contract1 || !contract2) {
      setError('Please select both contracts');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await compareContracts(contract1, contract2);
      setComparisonData(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to compare contracts');
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    if (!comparisonData?.concept_differences) return [];
    return Object.entries(comparisonData.concept_differences).map(([concept, data]) => ({
      concept,
      contract_1: data.contract_1_strength,
      contract_2: data.contract_2_strength,
      difference: data.difference
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <GitCompare className="w-8 h-8 text-purple-400" />
            Contract Comparison Dashboard
          </h1>
          <p className="text-gray-400 mt-2">Compare concept profiles between two contracts</p>
        </div>

        {/* Contract Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">Contract 1</label>
            <select
              value={contract1 || ''}
              onChange={(e) => setContract1(e.target.value)}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            >
              <option value="">Select first contract</option>
              {contracts.map(c => (
                <option key={c.id} value={c.id}>{c.original_filename}</option>
              ))}
            </select>
          </div>

          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">Contract 2</label>
            <select
              value={contract2 || ''}
              onChange={(e) => setContract2(e.target.value)}
              className="w-full bg-slate-700 text-white rounded px-3 py-2 border border-slate-600"
            >
              <option value="">Select second contract</option>
              {contracts.map(c => (
                <option key={c.id} value={c.id}>{c.original_filename}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={!contract1 || !contract2 || loading}
          className="w-full md:w-auto px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg font-medium mb-6"
        >
          {loading ? 'Comparing...' : 'Compare Contracts'}
        </button>

        {error && (
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 mb-6 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {comparisonData && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                  <h3 className="text-green-300 font-medium">Major Increases</h3>
                </div>
                <p className="text-white text-2xl font-bold">{comparisonData.major_increases?.length || 0}</p>
                <p className="text-green-400 text-sm mt-1">
                  {comparisonData.major_increases?.join(', ') || 'None'}
                </p>
              </div>

              <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingDown className="w-5 h-5 text-red-400" />
                  <h3 className="text-red-300 font-medium">Major Decreases</h3>
                </div>
                <p className="text-white text-2xl font-bold">{comparisonData.major_decreases?.length || 0}</p>
                <p className="text-red-400 text-sm mt-1">
                  {comparisonData.major_decreases?.join(', ') || 'None'}
                </p>
              </div>
            </div>

            {/* Bar Chart Comparison */}
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Concept Strength Comparison</h2>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={getChartData()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="concept" angle={-45} textAnchor="end" height={120} tick={{ fill: '#94a3b8' }} />
                  <YAxis tick={{ fill: '#94a3b8' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <Bar dataKey="contract_1" fill="#3b82f6" name="Contract 1" />
                  <Bar dataKey="contract_2" fill="#8b5cf6" name="Contract 2" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Detailed Comparison Table */}
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-xl font-bold text-white mb-4">Detailed Differences</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-600">
                      <th className="text-left text-gray-300 py-3 px-4">Concept</th>
                      <th className="text-right text-gray-300 py-3 px-4">Contract 1</th>
                      <th className="text-right text-gray-300 py-3 px-4">Contract 2</th>
                      <th className="text-right text-gray-300 py-3 px-4">Difference</th>
                      <th className="text-right text-gray-300 py-3 px-4">% Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonData.concept_differences &&
                      Object.entries(comparisonData.concept_differences)
                        .sort((a, b) => Math.abs(b[1].difference) - Math.abs(a[1].difference))
                        .map(([concept, data]) => (
                          <tr key={concept} className="border-b border-slate-700 hover:bg-slate-700/30">
                            <td className="py-3 px-4 text-white font-medium">{concept}</td>
                            <td className="py-3 px-4 text-right text-blue-300 font-mono">
                              {data.contract_1_strength.toFixed(3)}
                            </td>
                            <td className="py-3 px-4 text-right text-purple-300 font-mono">
                              {data.contract_2_strength.toFixed(3)}
                            </td>
                            <td className={`py-3 px-4 text-right font-mono ${
                              data.difference > 0 ? 'text-green-400' :
                              data.difference < 0 ? 'text-red-400' : 'text-gray-400'
                            }`}>
                              {data.difference > 0 && '+'}{data.difference.toFixed(3)}
                            </td>
                            <td className={`py-3 px-4 text-right font-mono ${
                              data.percent_change > 0 ? 'text-green-400' :
                              data.percent_change < 0 ? 'text-red-400' : 'text-gray-400'
                            }`}>
                              {data.percent_change > 0 && '+'}{data.percent_change.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContractComparisonDashboard;
