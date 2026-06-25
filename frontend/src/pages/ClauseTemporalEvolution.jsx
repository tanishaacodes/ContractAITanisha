import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const ClauseTemporalEvolution = () => {
  const { clauseId } = useParams();
  const [temporalData, setTemporalData] = useState(null);
  const [trendData, setTrendData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('usage');

  useEffect(() => {
    fetchTemporalData();
  }, [clauseId]);

  useEffect(() => {
    fetchTrendData(selectedMetric);
  }, [clauseId, selectedMetric]);

  const fetchTemporalData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/clauses/${clauseId}/temporal/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setTemporalData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching temporal data:', err);
      setError(err.response?.data?.error || 'Failed to load temporal data');
    } finally {
      setLoading(false);
    }
  };

  const fetchTrendData = async (metric) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/clauses/${clauseId}/temporal/trend/?metric=${metric}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setTrendData(prev => ({ ...prev, [metric]: response.data.data }));
    } catch (err) {
      console.error(`Error fetching ${metric} trend:`, err);
    }
  };

  const prepareChartData = (metric) => {
    const data = trendData[metric] || [];
    if (!data.length) return null;

    return {
      labels: data.map(d => d.year),
      datasets: [
        {
          label: metric.charAt(0).toUpperCase() + metric.slice(1),
          data: data.map(d => d.value),
          borderColor: metric === 'usage' ? '#3b82f6' : metric === 'risk' ? '#ef4444' : '#10b981',
          backgroundColor: metric === 'usage' ? 'rgba(59, 130, 246, 0.1)' :
                          metric === 'risk' ? 'rgba(239, 68, 68, 0.1)' :
                          'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#e5e7eb'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleColor: '#fff',
        bodyColor: '#e5e7eb'
      }
    },
    scales: {
      x: {
        ticks: {
          color: '#9ca3af'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      y: {
        ticks: {
          color: '#9ca3af'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading temporal evolution...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
            <p className="text-red-400">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!temporalData) {
    return null;
  }

  const chartData = prepareChartData(selectedMetric);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-100">Temporal Clause Evolution</h1>
          <p className="text-gray-400 mt-1">Track clause performance over time</p>
        </div>

        {/* Aging Status Card */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
          <div className="text-center">
            <div className="text-5xl mb-4">
              {temporalData.aging?.aging_level === 'COMMERCIALLY_EXTINCT' && '💀'}
              {temporalData.aging?.aging_level === 'AGING' && '⏳'}
              {temporalData.aging?.aging_level === 'DECLINING' && '📉'}
              {temporalData.aging?.aging_level === 'ACTIVE' && '✅'}
            </div>
            <div className="text-4xl font-bold mb-2" style={{
              color: temporalData.aging?.aging_score > 0.75 ? '#dc2626' :
                     temporalData.aging?.aging_score > 0.5 ? '#f59e0b' :
                     temporalData.aging?.aging_score > 0.3 ? '#fbbf24' : '#10b981'
            }}>
              {(temporalData.aging?.aging_score * 100).toFixed(0)}%
            </div>
            <div className="text-xl text-gray-300 mb-4">{temporalData.aging?.aging_level}</div>
            <div className="text-sm text-gray-400">
              {temporalData.years_in_use} years in use
            </div>
          </div>
        </div>

        {/* Trends Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Usage Trend</div>
            <div className="text-2xl font-bold text-blue-400">
              {temporalData.usage_trend?.trend}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Slope: {temporalData.usage_trend?.slope?.toFixed(2) || 0}
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Risk Trend</div>
            <div className="text-2xl font-bold text-red-400">
              {temporalData.risk_trend?.trend}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {temporalData.risk_trend?.increasing ? '⬆️ Increasing' : '⬇️ Stable/Decreasing'}
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Trust Trend</div>
            <div className="text-2xl font-bold text-green-400">
              {temporalData.trust_trend?.trend || 'N/A'}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {temporalData.trust_trend ?
                `Slope: ${temporalData.trust_trend.slope?.toFixed(2)}` :
                'No data'}
            </div>
          </div>
        </div>

        {/* Timeline Chart */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-200">Historical Timeline</h3>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedMetric('usage')}
                className={`px-3 py-1 rounded text-sm ${
                  selectedMetric === 'usage'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Usage
              </button>
              <button
                onClick={() => setSelectedMetric('risk')}
                className={`px-3 py-1 rounded text-sm ${
                  selectedMetric === 'risk'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Risk
              </button>
              <button
                onClick={() => setSelectedMetric('trust')}
                className={`px-3 py-1 rounded text-sm ${
                  selectedMetric === 'trust'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Trust
              </button>
            </div>
          </div>

          <div className="h-64">
            {chartData ? (
              <Line data={chartData} options={chartOptions} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-400">No trend data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Regulatory Drift */}
        {temporalData.regulatory_drift && temporalData.regulatory_drift.has_drift && (
          <div className="bg-gray-800 rounded-lg p-6 border border-red-700 mb-6">
            <h3 className="text-lg font-semibold text-red-400 mb-4">⚠️ Regulatory Drift Detected</h3>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-xs text-gray-400">Total Events</div>
                <div className="text-lg font-bold text-gray-200">
                  {temporalData.regulatory_drift.total_events}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400">Critical</div>
                <div className="text-lg font-bold text-red-400">
                  {temporalData.regulatory_drift.critical_count}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400">High Impact</div>
                <div className="text-lg font-bold text-orange-400">
                  {temporalData.regulatory_drift.high_count}
                </div>
              </div>
            </div>
            {temporalData.regulatory_drift.affected_events && (
              <div className="space-y-2">
                {temporalData.regulatory_drift.affected_events.map((event, idx) => (
                  <div key={idx} className="bg-gray-900/50 rounded p-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-gray-200">{event.title}</span>
                      <span className="text-xs px-2 py-1 rounded bg-red-900 text-red-300">
                        {event.severity}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {event.year} | {event.type}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Top Industries */}
        {temporalData.top_industries && temporalData.top_industries.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Top Industries</h3>
            <div className="space-y-2">
              {temporalData.top_industries.map(([industry, count], idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">{industry}</span>
                  <span className="text-sm font-semibold text-gray-200">{count} uses</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {temporalData.recommendations && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">📋 Recommendations</h3>
            <div className="space-y-3">
              {temporalData.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border ${
                    rec.priority === 'CRITICAL' ? 'bg-red-900/20 border-red-700' :
                    rec.priority === 'HIGH' ? 'bg-orange-900/20 border-orange-700' :
                    rec.priority === 'MEDIUM' ? 'bg-yellow-900/20 border-yellow-700' :
                    'bg-blue-900/20 border-blue-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-gray-200">{rec.action}</div>
                    <div className="text-xs px-2 py-1 rounded" style={{
                      backgroundColor: rec.priority === 'CRITICAL' ? '#7f1d1d' :
                                     rec.priority === 'HIGH' ? '#78350f' :
                                     rec.priority === 'MEDIUM' ? '#713f12' : '#1e3a8a',
                      color: '#fff'
                    }}>
                      {rec.priority}
                    </div>
                  </div>
                  <div className="text-sm text-gray-300 mb-1">{rec.reason}</div>
                  <div className="text-xs text-gray-400">Category: {rec.category}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClauseTemporalEvolution;
