import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowLeft, Brain, FileText, Eye, Network } from 'lucide-react';
import api from '../utils/api';
import useThemeStore from '../store/themeStore';

export default function LowConfidenceContracts() {
  const { theme } = useThemeStore();
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLowConfidenceContracts();
  }, []);

  const fetchLowConfidenceContracts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/dashboard/low-confidence-contracts');
      setContracts(response.data.contracts || []);
    } catch (err) {
      console.error('Failed to fetch low-confidence contracts:', err);
      setError(err.response?.data?.error || 'Failed to load contracts');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceBadge = (confidence) => {
    if (confidence < 50) {
      return (
        <span className="px-3 py-1 bg-red-900/30 text-red-400 text-xs font-medium rounded-full border border-red-800">
          Very Low ({confidence}%)
        </span>
      );
    } else if (confidence < 70) {
      return (
        <span className="px-3 py-1 bg-orange-900/30 text-orange-400 text-xs font-medium rounded-full border border-orange-800">
          Low ({confidence}%)
        </span>
      );
    }
    return (
      <span className="px-3 py-1 bg-yellow-900/30 text-yellow-400 text-xs font-medium rounded-full border border-yellow-800">
        Moderate ({confidence}%)
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
          <Brain className="w-16 h-16 animate-spin text-purple-400 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Loading low-confidence contracts...</p>
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
          <Brain className="w-8 h-8 text-purple-400" />
          <h1 className="text-3xl font-bold text-white">Low AI Confidence Contracts</h1>
        </div>
        <p className="text-gray-400">
          Contracts where AI analysis has confidence below 80% and may require manual review
        </p>
      </div>

      {/* Info Banner */}
      <div className="mb-6 bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-purple-400 mt-1 flex-shrink-0" />
          <div>
            <p className="text-purple-400 font-semibold mb-1">Why Low Confidence?</p>
            <p className="text-gray-300 text-sm">
              These contracts may have unclear language, missing clauses, or complex legal terms that
              reduce AI confidence. Consider manual legal review for these contracts.
            </p>
          </div>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <FileText className="w-8 h-8 text-blue-400" />
            <div>
              <p className="text-gray-400 text-sm">Total Low-Confidence</p>
              <p className="text-2xl font-bold text-white">{contracts.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-8 h-8 text-red-400" />
            <div>
              <p className="text-gray-400 text-sm">Very Low (&lt;50%)</p>
              <p className="text-2xl font-bold text-white">
                {contracts.filter(c => c.confidence_score < 50).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-400" />
            <div>
              <p className="text-gray-400 text-sm">Avg Confidence</p>
              <p className="text-2xl font-bold text-white">
                {contracts.length > 0
                  ? (contracts.reduce((sum, c) => sum + (c.confidence_score || 0), 0) / contracts.length).toFixed(1)
                  : 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Contracts List */}
      {contracts.length === 0 ? (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-12 text-center">
          <Brain className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Low-Confidence Contracts</h3>
          <p className="text-gray-400 mb-6">
            All your contracts have high AI confidence scores (≥80%). Great job!
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
          {contracts.map((contract) => (
            <div
              key={contract.id}
              className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="bg-purple-600/10 p-3 rounded-lg">
                    <FileText className="w-6 h-6 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">
                        {contract.name}
                      </h3>
                      {getConfidenceBadge(contract.confidence_score)}
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
                        <span className="font-medium">Counterparty:</span>
                        {contract.counterparty || 'N/A'}
                      </span>
                    </div>

                    {/* Reasons for Low Confidence */}
                    {contract.low_confidence_reasons && contract.low_confidence_reasons.length > 0 && (
                      <div className="mt-3 p-3 bg-orange-900/20 border border-orange-500/30 rounded-lg">
                        <p className="text-orange-400 font-semibold text-sm mb-2">⚠️ Confidence Issues:</p>
                        <ul className="text-gray-300 text-sm space-y-1">
                          {contract.low_confidence_reasons.map((reason, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-orange-400">•</span>
                              {reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
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
                  <button
                    onClick={() => navigate(`/contracts/${contract.id}/graph-dashboard`)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 rounded-lg transition"
                    title="Graph Intelligence"
                  >
                    <Network className="w-4 h-4" />
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
