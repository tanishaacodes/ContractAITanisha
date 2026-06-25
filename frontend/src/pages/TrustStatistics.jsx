import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const TrustStatistics = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatistics();
    fetchBadges();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/trust/statistics/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setStats(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching trust statistics:', err);
      setError(err.response?.data?.error || 'Failed to load trust statistics');
    } finally {
      setLoading(false);
    }
  };

  const fetchBadges = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/trust/badges/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setBadges(response.data.badges || []);
    } catch (err) {
      console.error('Error fetching trust badges:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading trust statistics...</p>
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

  if (!stats) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-100">Trust Score Statistics</h1>
          <p className="text-gray-400 mt-1">Portfolio-wide trust intelligence</p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Total Clauses</div>
            <div className="text-3xl font-bold text-gray-100">{stats.total_clauses}</div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-green-700">
            <div className="text-sm text-gray-400 mb-1">Average Trust</div>
            <div className="text-3xl font-bold text-green-400">
              {(stats.avg_trust * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Median: {(stats.median_trust * 100).toFixed(0)}%
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-blue-700">
            <div className="text-sm text-gray-400 mb-1">Excellent Clauses</div>
            <div className="text-3xl font-bold text-blue-400">{stats.excellent_count}</div>
            <div className="text-xs text-gray-400 mt-1">Trust ≥ 85%</div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-red-700">
            <div className="text-sm text-gray-400 mb-1">High Risk</div>
            <div className="text-3xl font-bold text-red-400">{stats.poor_count}</div>
            <div className="text-xs text-gray-400 mt-1">{'Trust < 50%'}</div>
          </div>
        </div>

        {/* Trust Range Distribution */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Trust Score Distribution</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-300">Minimum</span>
              <span className="text-sm font-semibold text-gray-200">
                {(stats.min_trust * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-300">Maximum</span>
              <span className="text-sm font-semibold text-gray-200">
                {(stats.max_trust * 100).toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-300">Standard Deviation</span>
              <span className="text-sm font-semibold text-gray-200">
                {(stats.std_trust * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Badge Distribution */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Trust Badge Distribution</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.badge_distribution || {}).map(([badge, count]) => (
              <div
                key={badge}
                className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 text-center"
              >
                <div className="text-2xl font-bold text-gray-200">{count}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {badge.replace(/_/g, ' ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* All Badge Types */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Trust Badge Guide</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {badges.map((badge) => (
              <div
                key={badge.badge}
                className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 flex items-center gap-4"
              >
                <div
                  className="text-4xl w-16 h-16 flex items-center justify-center rounded-full"
                  style={{
                    backgroundColor: `${badge.color}20`,
                    borderWidth: '2px',
                    borderColor: badge.color
                  }}
                >
                  {badge.icon}
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-200">{badge.label}</div>
                  <div className="text-sm text-gray-400">{badge.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrustStatistics;
