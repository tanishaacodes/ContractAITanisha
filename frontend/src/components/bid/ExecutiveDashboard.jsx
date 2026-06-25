/**
 * Executive Dashboard Component
 * High-level overview with KPIs, department breakdown, and risk cascade
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ExecutiveDashboard = ({ tenderId }) => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

  useEffect(() => {
    if (tenderId) {
      loadDashboard();
    }
  }, [tenderId]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${API_BASE}/api/tenders/${tenderId}/bid/dashboard/`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      setDashboard(response.data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const runRiskPropagation = async () => {
    try {
      await axios.post(
        `${API_BASE}/api/tenders/${tenderId}/bid/propagate-risk/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      alert('Risk propagation completed!');
      loadDashboard();
    } catch (error) {
      console.error('Failed to run propagation:', error);
      alert('Failed to run risk propagation');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="p-6 text-center text-slate-400">
        Failed to load dashboard data
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Executive Dashboard</h2>
        <button
          onClick={runRiskPropagation}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          Run Risk Propagation
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 p-6 rounded-lg shadow-lg">
          <div className="text-blue-100 text-sm mb-2">Bid Readiness</div>
          <div className="text-white text-4xl font-bold">
            {dashboard.readiness.readiness_index.toFixed(1)}%
          </div>
          <div className="text-blue-200 text-sm mt-2">
            {dashboard.readiness.completed_actions} / {dashboard.readiness.total_actions} completed
          </div>
          <div className="mt-3 w-full h-2 bg-blue-900 rounded-full">
            <div
              className="h-2 bg-white rounded-full"
              style={{ width: `${dashboard.readiness.readiness_index}%` }}
            ></div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-600 to-green-800 p-6 rounded-lg shadow-lg">
          <div className="text-green-100 text-sm mb-2">Total Actions</div>
          <div className="text-white text-4xl font-bold">
            {dashboard.readiness.total_actions}
          </div>
          <div className="text-green-200 text-sm mt-2">
            {dashboard.readiness.critical_pending} critical pending
          </div>
          <div className="mt-3 text-green-100 text-xs">
            Data Completeness: {dashboard.readiness.data_readiness.toFixed(1)}%
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-600 to-purple-800 p-6 rounded-lg shadow-lg">
          <div className="text-purple-100 text-sm mb-2">Financial Exposure</div>
          <div className="text-white text-4xl font-bold">
            ${(dashboard.readiness.total_exposure / 1000000).toFixed(1)}M
          </div>
          <div className="text-purple-200 text-sm mt-2">Estimated risk value</div>
        </div>
      </div>

      {/* Department Breakdown */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-white text-xl font-bold mb-4">Department Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-slate-700">
              <tr>
                <th className="px-4 py-2 text-left text-slate-300 font-medium">Department</th>
                <th className="px-4 py-2 text-right text-slate-300 font-medium">Total</th>
                <th className="px-4 py-2 text-right text-slate-300 font-medium">Done</th>
                <th className="px-4 py-2 text-right text-slate-300 font-medium">Progress</th>
                <th className="px-4 py-2 text-right text-slate-300 font-medium">Avg Risk</th>
                <th className="px-4 py-2 text-right text-slate-300 font-medium">Exposure</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.department_summary.map((dept, index) => (
                <tr
                  key={index}
                  className="border-b border-slate-700 hover:bg-slate-750"
                >
                  <td className="px-4 py-3 text-white font-medium">
                    {dept.department__name || 'Unknown'}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-300">{dept.total}</td>
                  <td className="px-4 py-3 text-right text-slate-300">{dept.completed}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-24 h-2 bg-slate-700 rounded-full">
                        <div
                          className={`h-2 rounded-full ${
                            dept.completion_pct >= 80
                              ? 'bg-green-500'
                              : dept.completion_pct >= 50
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${dept.completion_pct}%` }}
                        ></div>
                      </div>
                      <span className="text-white text-sm w-12 text-right">
                        {dept.completion_pct}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        dept.avg_risk > 0.7
                          ? 'bg-red-600 text-white'
                          : dept.avg_risk > 0.5
                          ? 'bg-orange-600 text-white'
                          : dept.avg_risk > 0.3
                          ? 'bg-yellow-600 text-white'
                          : 'bg-green-600 text-white'
                      }`}
                    >
                      {(dept.avg_risk * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-300">
                    ${(dept.exposure / 1000).toFixed(0)}K
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Risk Cascade Analysis */}
      {dashboard.risk_cascade && dashboard.risk_cascade.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white text-xl font-bold mb-4">Risk Cascade Analysis</h3>
          <div className="grid grid-cols-3 gap-4">
            {dashboard.risk_cascade.slice(0, 9).map((cascade, index) => (
              <div
                key={index}
                className="bg-slate-700 p-4 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors"
              >
                <div className="text-slate-300 text-sm font-medium mb-2">
                  {cascade.department}
                </div>
                <div
                  className={`text-3xl font-bold mb-1 ${
                    cascade.propagated_risk > 0.7
                      ? 'text-red-400'
                      : cascade.propagated_risk > 0.5
                      ? 'text-orange-400'
                      : cascade.propagated_risk > 0.3
                      ? 'text-yellow-400'
                      : 'text-green-400'
                  }`}
                >
                  {(cascade.propagated_risk * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-slate-400 mb-3">
                  Base: {(cascade.base_risk * 100).toFixed(0)}%
                  <span className="text-orange-400 ml-1">
                    (+{(cascade.amplification * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">{cascade.task_count} tasks</span>
                  <span className="text-orange-400 font-medium">
                    {cascade.predicted_delay_days}d delay
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Distribution */}
      {dashboard.status_counts && Object.keys(dashboard.status_counts).length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-white text-xl font-bold mb-4">Status Distribution</h3>
          <div className="grid grid-cols-5 gap-4">
            {Object.entries(dashboard.status_counts).map(([status, count]) => (
              <div key={status} className="text-center">
                <div className="text-3xl font-bold text-white mb-1">{count}</div>
                <div className="text-sm text-slate-400">{status}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutiveDashboard;
