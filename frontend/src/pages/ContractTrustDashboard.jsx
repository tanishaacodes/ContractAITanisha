import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import TrustBadge from '../components/trust/TrustBadge';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const ContractTrustDashboard = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchContractTrust();
  }, [contractId]);

  const fetchContractTrust = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/contracts/${contractId}/trust/dashboard/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setDashboardData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching contract trust dashboard:', err);
      setError(err.response?.data?.error || 'Failed to load contract trust dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading contract trust dashboard...</p>
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

  if (!dashboardData) {
    return null;
  }

  const { statistics, high_risk_clauses, excellent_clauses, all_clauses } = dashboardData;

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-100">Contract Trust Dashboard</h1>
          <p className="text-gray-400 mt-1">Portfolio-level trust analysis</p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Total Clauses</div>
            <div className="text-2xl font-bold text-gray-100">{statistics.total_clauses}</div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-green-700">
            <div className="text-sm text-gray-400 mb-1">Average Trust</div>
            <div className="text-2xl font-bold text-green-400">
              {(statistics.avg_trust * 100).toFixed(0)}%
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-blue-700">
            <div className="text-sm text-gray-400 mb-1">Excellent Clauses</div>
            <div className="text-2xl font-bold text-blue-400">{statistics.excellent_count}</div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-red-700">
            <div className="text-sm text-gray-400 mb-1">High Risk Clauses</div>
            <div className="text-2xl font-bold text-red-400">{statistics.poor_count}</div>
          </div>
        </div>

        {/* Badge Distribution */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Trust Badge Distribution</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(statistics.badge_distribution || {}).map(([badge, count]) => (
              <div key={badge} className="text-center">
                <div className="text-2xl font-bold text-gray-200">{count}</div>
                <div className="text-xs text-gray-400 mt-1">{badge.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>

        {/* High Risk Clauses */}
        {high_risk_clauses && high_risk_clauses.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 border border-red-700 mb-6">
            <h3 className="text-lg font-semibold text-red-400 mb-4">
              ⚠️ High Risk Clauses ({high_risk_clauses.length})
            </h3>
            <div className="space-y-3">
              {high_risk_clauses.map((clause) => (
                <div
                  key={clause.clause_id}
                  className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 hover:border-red-500 transition-colors cursor-pointer"
                  onClick={() => navigate(`/clauses/${clause.clause_id}/trust`)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{clause.badge_icon}</div>
                      <div>
                        <div className="font-medium text-gray-200">Clause {clause.clause_id}</div>
                        <div className="text-xs text-gray-400">{clause.badge_description}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-red-400">
                        {(clause.trust_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-400">{clause.trust_grade}</div>
                    </div>
                  </div>
                  <TrustBadge
                    badge={clause.badge}
                    label={clause.badge_label}
                    color={clause.badge_color}
                    icon={clause.badge_icon}
                    description={clause.badge_description}
                    size="small"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Excellent Clauses */}
        {excellent_clauses && excellent_clauses.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 border border-green-700 mb-6">
            <h3 className="text-lg font-semibold text-green-400 mb-4">
              ✅ Excellent Clauses ({excellent_clauses.length})
            </h3>
            <div className="space-y-3">
              {excellent_clauses.map((clause) => (
                <div
                  key={clause.clause_id}
                  className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 hover:border-green-500 transition-colors cursor-pointer"
                  onClick={() => navigate(`/clauses/${clause.clause_id}/trust`)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div className="text-3xl">{clause.badge_icon}</div>
                      <div>
                        <div className="font-medium text-gray-200">Clause {clause.clause_id}</div>
                        <div className="text-xs text-gray-400">{clause.badge_description}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-400">
                        {(clause.trust_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-400">{clause.trust_grade}</div>
                    </div>
                  </div>
                  <TrustBadge
                    badge={clause.badge}
                    label={clause.badge_label}
                    color={clause.badge_color}
                    icon={clause.badge_icon}
                    description={clause.badge_description}
                    size="small"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Clauses List */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">
            All Clauses ({all_clauses?.length || 0})
          </h3>
          <div className="space-y-2">
            {all_clauses?.map((clause) => (
              <div
                key={clause.clause_id}
                className="bg-gray-900/50 rounded-lg p-3 border border-gray-700 hover:border-blue-500 transition-colors cursor-pointer flex items-center justify-between"
                onClick={() => navigate(`/clauses/${clause.clause_id}/trust`)}
              >
                <div className="flex items-center gap-3">
                  <div className="text-xl">{clause.badge_icon}</div>
                  <div>
                    <div className="text-sm font-medium text-gray-200">
                      Clause {clause.clause_id}
                    </div>
                    <TrustBadge
                      badge={clause.badge}
                      label={clause.badge_label}
                      color={clause.badge_color}
                      icon=""
                      description={clause.badge_description}
                      size="small"
                    />
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold" style={{ color: clause.color }}>
                    {(clause.trust_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-400">{clause.trust_grade}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContractTrustDashboard;
