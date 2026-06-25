import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Calendar } from 'lucide-react';

const IntentDriftTimeline = ({ contractId, onVersionSelect }) => {
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (contractId) {
      loadTimeline();
    }
  }, [contractId]);

  const loadTimeline = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/contracts/${contractId}/drift-timeline`);
      setTimeline(response.data.timeline || []);
      setError(null);
    } catch (err) {
      setError('Failed to load drift timeline');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const chartData = timeline.map(item => ({
    version: `v${item.from_version} → v${item.to_version}`,
    driftScore: (item.drift_score * 100).toFixed(1),
    riskDelta: (item.risk_delta * 100).toFixed(1),
    totalChanges: item.intent_changes + item.obligation_changes + item.right_changes,
    from: item.from_version,
    to: item.to_version
  }));

  const handleRowClick = (from, to) => {
    if (onVersionSelect) {
      onVersionSelect(from, to);
    }
  };

  if (loading) {
    return (
      <div className="text-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-400 p-4">{error}</div>;
  }

  if (timeline.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
        <Calendar className="mx-auto h-12 w-12 text-slate-500 mb-3" />
        <p className="text-slate-400">No drift history available</p>
        <p className="text-sm text-slate-500 mt-2">Need at least 2 versions to show drift timeline</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <TrendingUp size={20} />
          Drift Over Time
        </h3>
        <span className="text-sm text-slate-400">
          {timeline.length} comparison{timeline.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Chart */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis
              dataKey="version"
              stroke="#94a3b8"
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="driftScore"
              stroke="#f59e0b"
              strokeWidth={2}
              name="Drift Score (%)"
            />
            <Line
              type="monotone"
              dataKey="riskDelta"
              stroke="#ef4444"
              strokeWidth={2}
              name="Risk Change (%)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Timeline Table */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-900">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300">Version Change</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300">Drift Score</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300">Risk Delta</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300">Total Changes</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-slate-300">Date</th>
            </tr>
          </thead>
          <tbody>
            {timeline.map((item, idx) => (
              <tr
                key={idx}
                className="border-t border-slate-700 hover:bg-slate-700/50 cursor-pointer"
                onClick={() => handleRowClick(item.from_version, item.to_version)}
              >
                <td className="px-4 py-3 text-white">
                  v{item.from_version} → v{item.to_version}
                </td>
                <td className="px-4 py-3">
                  <span className={`font-medium ${
                    item.drift_score > 0.6 ? 'text-red-400' :
                    item.drift_score > 0.3 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {(item.drift_score * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={item.risk_delta > 0 ? 'text-red-400' : 'text-green-400'}>
                    {item.risk_delta > 0 ? '+' : ''}{(item.risk_delta * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {item.intent_changes + item.obligation_changes + item.right_changes}
                </td>
                <td className="px-4 py-3 text-slate-400 text-sm">
                  {new Date(item.comparison_date).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default IntentDriftTimeline;
