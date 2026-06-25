import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, ArrowLeft, TrendingDown, FileText, Eye, AlertCircle } from 'lucide-react';
import api from '../utils/api';
import useThemeStore from '../store/themeStore';

export default function ReviewTimeAnalytics() {
  const { theme } = useThemeStore();
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLongestReviewTimeContracts();
  }, []);

  const fetchLongestReviewTimeContracts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/dashboard/longest-review-contracts');
      setContracts(response.data.contracts || []);
    } catch (err) {
      console.error('Failed to fetch review time analytics:', err);
      setError(err.response?.data?.error || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const getReviewTimeBadge = (hours) => {
    if (hours > 24) {
      return (
        <span className="px-3 py-1 bg-red-900/30 text-red-400 text-xs font-medium rounded-full border border-red-800">
          Very Slow ({hours}h)
        </span>
      );
    } else if (hours > 12) {
      return (
        <span className="px-3 py-1 bg-orange-900/30 text-orange-400 text-xs font-medium rounded-full border border-orange-800">
          Slow ({hours}h)
        </span>
      );
    }
    return (
      <span className="px-3 py-1 bg-yellow-900/30 text-yellow-400 text-xs font-medium rounded-full border border-yellow-800">
        Moderate ({hours}h)
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <Clock className="w-16 h-16 animate-spin text-emerald-400 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Loading review time analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <p className="text-red-400 text-lg mb-4">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const avgReviewTime = contracts.length > 0
    ? (contracts.reduce((sum, c) => sum + (c.review_time || 0), 0) / contracts.length).toFixed(1)
    : 0;

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-gray-400 hover:text-gray-200 mb-6 transition"
      >
        <ArrowLeft size={20} />
        <span>Back to Dashboard</span>
      </button>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Clock className="w-8 h-8 text-emerald-400" />
          <h1 className="text-3xl font-bold text-white">Review Time Analytics</h1>
        </div>
        <p className="text-gray-400">
          Contracts with longest review times - focus on these for process optimization
        </p>
      </div>

      {/* AI Impact Banner */}
      <div className="mb-6 bg-emerald-900/20 border border-emerald-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <TrendingDown className="w-5 h-5 text-emerald-400 mt-1 flex-shrink-0" />
          <div>
            <p className="text-emerald-400 font-semibold mb-1">AI Impact: 64% Time Reduction</p>
            <p className="text-gray-300 text-sm">
              Before AI: <span className="font-bold">18.4 hours</span> average review time.
              After AI: <span className="font-bold">6.6 hours</span> average. You're saving{' '}
              <span className="font-bold">11.8 hours per contract</span>!
            </p>
          </div>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Clock className="w-8 h-8 text-emerald-400" />
            <div>
              <p className="text-gray-400 text-sm">Avg Review Time</p>
              <p className="text-2xl font-bold text-white">{avgReviewTime}h</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <FileText className="w-8 h-8 text-blue-400" />
            <div>
              <p className="text-gray-400 text-sm">Contracts Tracked</p>
              <p className="text-2xl font-bold text-white">{contracts.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <TrendingDown className="w-8 h-8 text-green-400" />
            <div>
              <p className="text-gray-400 text-sm">Time Saved</p>
              <p className="text-2xl font-bold text-white">64%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Contracts List */}
      {contracts.length === 0 ? (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-12 text-center">
          <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Review Time Data</h3>
          <p className="text-gray-400 mb-6">
            Review time tracking is not available yet for your contracts.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition"
          >
            Back to Dashboard
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white mb-4">
            Contracts Sorted by Review Time (Longest First)
          </h3>
          {contracts.map((contract) => (
            <div
              key={contract.id}
              className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="bg-emerald-600/10 p-3 rounded-lg">
                    <FileText className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">
                        {contract.name}
                      </h3>
                      {getReviewTimeBadge(contract.review_time)}
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
                      <span className="flex items-center gap-1">
                        <span className="font-medium">Type:</span>
                        {contract.contract_type || 'Unknown'}
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="font-medium">Uploaded:</span>
                        {formatDate(contract.uploaded_at)}
                      </span>
                      <span className="flex items-center gap-1">
                        <span className="font-medium">Reviewed:</span>
                        {contract.reviewed_at ? formatDate(contract.reviewed_at) : 'Pending'}
                      </span>
                    </div>

                    {/* Review Progress */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Review Progress</span>
                        <span className="text-sm font-medium text-emerald-400">
                          {contract.review_progress || 0}%
                        </span>
                      </div>
                      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 transition-all"
                          style={{ width: `${contract.review_progress || 0}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
                  <button
                    onClick={() => navigate(`/contract/${contract.id}/clauses`)}
                    className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition"
                    title="View Contract"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
