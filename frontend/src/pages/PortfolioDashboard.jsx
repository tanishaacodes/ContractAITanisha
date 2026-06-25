/**
 * Portfolio Dashboard
 * Multi-tender overview with aggregated KPIs and drill-down capabilities
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const PortfolioDashboard = () => {
  const navigate = useNavigate();
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('readiness'); // readiness, value, risk

  const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

  useEffect(() => {
    loadPortfolio();
  }, []);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${API_BASE}/api/tenders/bid/portfolio/`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      setPortfolio(response.data);
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSortedTenders = () => {
    if (!portfolio || !portfolio.tenders) return [];

    const tenders = [...portfolio.tenders];

    switch (sortBy) {
      case 'readiness':
        return tenders.sort((a, b) => a.readiness_index - b.readiness_index);
      case 'value':
        return tenders.sort((a, b) => b.estimated_value - a.estimated_value);
      case 'risk':
        return tenders.sort((a, b) => b.avg_risk - a.avg_risk);
      default:
        return tenders;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-6">
          <p className="text-red-400">Failed to load portfolio data</p>
        </div>
      </div>
    );
  }

  const sortedTenders = getSortedTenders();

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Bid Portfolio Dashboard</h1>
            <p className="text-slate-400 mt-1">Overview of all active tender opportunities</p>
          </div>
          <button
            onClick={() => navigate('/tenders')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View All Tenders
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-6 mb-6">
          <div className="bg-gradient-to-br from-blue-600 to-blue-800 p-6 rounded-lg shadow-lg">
            <div className="text-blue-100 text-sm mb-2">Total Tenders</div>
            <div className="text-white text-4xl font-bold">{portfolio.total_tenders}</div>
            <div className="text-blue-200 text-xs mt-2">Active opportunities</div>
          </div>

          <div className="bg-gradient-to-br from-green-600 to-green-800 p-6 rounded-lg shadow-lg">
            <div className="text-green-100 text-sm mb-2">Pipeline Value</div>
            <div className="text-white text-4xl font-bold">
              ${(portfolio.total_value / 1000000).toFixed(1)}M
            </div>
            <div className="text-green-200 text-xs mt-2">Total estimated value</div>
          </div>

          <div className="bg-gradient-to-br from-purple-600 to-purple-800 p-6 rounded-lg shadow-lg">
            <div className="text-purple-100 text-sm mb-2">Avg Readiness</div>
            <div className="text-white text-4xl font-bold">
              {portfolio.avg_readiness.toFixed(1)}%
            </div>
            <div className="text-purple-200 text-xs mt-2">Portfolio maturity</div>
          </div>

          <div className="bg-gradient-to-br from-orange-600 to-orange-800 p-6 rounded-lg shadow-lg">
            <div className="text-orange-100 text-sm mb-2">Total Exposure</div>
            <div className="text-white text-4xl font-bold">
              ${(portfolio.total_exposure / 1000000).toFixed(1)}M
            </div>
            <div className="text-orange-200 text-xs mt-2">Risk-weighted value</div>
          </div>
        </div>

        {/* Filters/Sort */}
        <div className="bg-slate-800 rounded-lg p-4 mb-6 flex items-center justify-between border border-slate-700">
          <div className="text-white">
            Showing {sortedTenders.length} tenders
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-sm">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600"
            >
              <option value="readiness">Readiness (Low to High)</option>
              <option value="value">Value (High to Low)</option>
              <option value="risk">Risk (High to Low)</option>
            </select>
          </div>
        </div>

        {/* Tenders Grid */}
        <div className="space-y-4">
          {sortedTenders.map((tender) => (
            <div
              key={tender.tender_id}
              className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 cursor-pointer transition-all hover:shadow-lg"
              onClick={() => navigate(`/tenders/${tender.tender_id}/dashboard`)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-white text-xl font-bold mb-1">{tender.tender_title}</h3>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-slate-400">{tender.reference_number}</span>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        tender.status === 'ANALYZED'
                          ? 'bg-green-600 text-white'
                          : tender.status === 'ANALYZING'
                          ? 'bg-yellow-600 text-white'
                          : tender.status === 'BIDDING'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-600 text-white'
                      }`}
                    >
                      {tender.status}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white text-2xl font-bold">
                    ${(tender.estimated_value / 1000000).toFixed(1)}M
                  </div>
                  <div className="text-slate-400 text-xs mt-1">Estimated Value</div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-5 gap-4 mb-4">
                <div>
                  <div className="text-slate-400 text-xs mb-1">Readiness</div>
                  <div
                    className={`text-2xl font-bold ${
                      tender.readiness_index >= 80
                        ? 'text-green-400'
                        : tender.readiness_index >= 50
                        ? 'text-yellow-400'
                        : 'text-red-400'
                    }`}
                  >
                    {tender.readiness_index.toFixed(0)}%
                  </div>
                </div>

                <div>
                  <div className="text-slate-400 text-xs mb-1">Actions</div>
                  <div className="text-white text-lg font-semibold">
                    {tender.completed_actions}/{tender.total_actions}
                  </div>
                  <div className="text-xs text-slate-500">
                    {tender.total_actions > 0
                      ? ((tender.completed_actions / tender.total_actions) * 100).toFixed(0)
                      : 0}
                    % done
                  </div>
                </div>

                <div>
                  <div className="text-slate-400 text-xs mb-1">Critical</div>
                  <div
                    className={`text-lg font-semibold ${
                      tender.critical_pending > 0 ? 'text-orange-400' : 'text-green-400'
                    }`}
                  >
                    {tender.critical_pending}
                  </div>
                  <div className="text-xs text-slate-500">Pending</div>
                </div>

                <div>
                  <div className="text-slate-400 text-xs mb-1">Avg Risk</div>
                  <div
                    className={`text-lg font-semibold ${
                      tender.avg_risk > 0.7
                        ? 'text-red-400'
                        : tender.avg_risk > 0.5
                        ? 'text-orange-400'
                        : tender.avg_risk > 0.3
                        ? 'text-yellow-400'
                        : 'text-green-400'
                    }`}
                  >
                    {(tender.avg_risk * 100).toFixed(0)}%
                  </div>
                </div>

                <div>
                  <div className="text-slate-400 text-xs mb-1">Exposure</div>
                  <div className="text-white text-lg font-semibold">
                    ${(tender.total_exposure / 1000000).toFixed(1)}M
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="relative">
                <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      tender.readiness_index >= 80
                        ? 'bg-green-500'
                        : tender.readiness_index >= 50
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${tender.readiness_index}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}

          {sortedTenders.length === 0 && (
            <div className="bg-slate-800 rounded-lg p-12 text-center border border-slate-700">
              <p className="text-slate-400 text-lg mb-4">No tenders found</p>
              <button
                onClick={() => navigate('/tenders/upload')}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upload New Tender
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PortfolioDashboard;
