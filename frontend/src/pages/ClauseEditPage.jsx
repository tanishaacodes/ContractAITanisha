import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Edit, History, Save, X, AlertTriangle,
  Download, Loader2, FileText, CheckCircle, TrendingDown, TrendingUp
} from 'lucide-react';
import api from '../utils/api';

const ClauseEditPage = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [contract, setContract] = useState(null);
  const [clauses, setClauses] = useState([]);
  const [error, setError] = useState('');

  const [editingClause, setEditingClause] = useState(null);
  const [showHistory, setShowHistory] = useState(null);

  const [regenerating, setRegenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);

  useEffect(() => {
    loadContract();
  }, [contractId]);

  const loadContract = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/contracts/${contractId}/clauses/edit`);

      if (response.data.success) {
        setContract(response.data.contract);
        setClauses(response.data.clauses);
      } else {
        setError(response.data.error || 'Failed to load contract');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load contract clauses');
      console.error('Error loading contract:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateContract = async () => {
    try {
      setRegenerating(true);
      const response = await api.post(`/contracts/${contractId}/regenerate`);

      if (response.data.success) {
        const versionId = response.data.contract_version.id;
        setDownloadUrl(`/contract-versions/${versionId}/download`);
        alert(`Contract regenerated successfully! Version ${response.data.contract_version.version_number} created with ${response.data.contract_version.modified_clause_count} modified clauses.`);
      } else {
        alert(response.data.error || 'Failed to regenerate contract');
      }
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to regenerate contract');
      console.error('Error regenerating:', err);
    } finally {
      setRegenerating(false);
    }
  };

  const handleDownloadModified = async () => {
    if (!downloadUrl) return;

    try {
      const response = await api.get(downloadUrl, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${contract.filename}_modified.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download modified contract');
      console.error('Download error:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading contract clauses...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-blue-400" />
            </button>
            <h1 className="text-3xl font-bold text-white">Edit Contract</h1>
          </div>
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-red-400 font-semibold mb-1">Error Loading Contract</h3>
                <p className="text-red-300">{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!contract?.can_edit) {
    return (
      <div className="min-h-screen bg-slate-950 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-blue-400" />
            </button>
            <h1 className="text-3xl font-bold text-white">Edit Contract</h1>
          </div>
          <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-yellow-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-yellow-400 font-semibold mb-1">Cannot Edit Contract</h3>
                <p className="text-yellow-300">
                  Only contracts in DRAFT status can be edited. This contract is currently in {contract.status} status.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const modifiedClausesCount = clauses.filter(c => c.has_been_edited).length;

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-blue-400" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-white">Edit Contract Clauses</h1>
              <p className="text-slate-400 mt-1">{contract.filename}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {modifiedClausesCount > 0 && (
              <button
                onClick={handleRegenerateContract}
                disabled={regenerating}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-medium transition"
              >
                {regenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5" />
                    Regenerate Contract
                  </>
                )}
              </button>
            )}

            {downloadUrl && (
              <button
                onClick={handleDownloadModified}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition"
              >
                <Download className="w-5 h-5" />
                Download Modified
              </button>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Total Clauses</p>
                <p className="text-2xl font-bold text-white mt-1">{clauses.length}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Modified Clauses</p>
                <p className="text-2xl font-bold text-white mt-1">{modifiedClausesCount}</p>
              </div>
              <Edit className="w-8 h-8 text-purple-400" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">High Risk Clauses</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {clauses.filter(c => c.risk_level === 'HIGH').length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
          </div>
        </div>

        {/* Clauses List */}
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">Contract Clauses</h2>

          <div className="space-y-3">
            {clauses.map((clause) => (
              <ClauseCard
                key={clause.id}
                clause={clause}
                onEdit={() => setEditingClause(clause)}
                onViewHistory={() => setShowHistory(clause)}
              />
            ))}
          </div>
        </div>

        {/* Edit Modal */}
        {editingClause && (
          <EditClauseModal
            clause={editingClause}
            onClose={() => setEditingClause(null)}
            onSave={() => {
              loadContract();
              setEditingClause(null);
            }}
          />
        )}

        {/* History Modal */}
        {showHistory && (
          <HistoryModal
            clause={showHistory}
            onClose={() => setShowHistory(null)}
          />
        )}
      </div>
    </div>
  );
};

// Clause Card Component
const ClauseCard = ({ clause, onEdit, onViewHistory }) => {
  const getRiskColor = (level) => {
    switch (level) {
      case 'HIGH': return 'text-red-400 bg-red-900/30 border-red-700';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-900/30 border-yellow-700';
      case 'LOW': return 'text-green-400 bg-green-900/30 border-green-700';
      default: return 'text-slate-400 bg-slate-800 border-slate-600';
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:bg-slate-750 transition">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-white font-semibold text-lg">{clause.clause_name}</h3>
          <p className="text-slate-400 text-sm">{clause.clause_type}</p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs font-semibold border ${getRiskColor(clause.risk_level)}`}>
            {clause.risk_level || 'UNKNOWN'}
          </span>

          {clause.has_been_edited && (
            <span className="px-2 py-1 rounded text-xs font-semibold bg-purple-900/30 text-purple-400 border border-purple-700">
              Modified (v{clause.version_count})
            </span>
          )}
        </div>
      </div>

      <div className="bg-slate-900 rounded p-3 mb-3">
        <p className="text-slate-300 text-sm line-clamp-3">{clause.current_text}</p>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span>Risk: {(clause.risk_score * 100).toFixed(0)}%</span>
          <span>Likelihood: {clause.likelihood_score?.toFixed(1) || 'N/A'}</span>
          <span>Impact: {clause.impact_score?.toFixed(1) || 'N/A'}</span>
        </div>

        <div className="flex items-center gap-2">
          {clause.has_been_edited && (
            <button
              onClick={onViewHistory}
              className="flex items-center gap-1 bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded text-sm transition"
            >
              <History size={14} />
              History
            </button>
          )}

          <button
            onClick={onEdit}
            className="flex items-center gap-1 bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded text-sm transition"
          >
            <Edit size={14} />
            Edit
          </button>
        </div>
      </div>
    </div>
  );
};

// Edit Clause Modal Component
const EditClauseModal = ({ clause, onClose, onSave }) => {
  const [modifiedText, setModifiedText] = useState(clause.current_text);
  const [changeDescription, setChangeDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [newRiskScore, setNewRiskScore] = useState(null);

  const handleSave = async () => {
    if (!modifiedText.trim()) {
      alert('Clause text cannot be empty');
      return;
    }

    if (!changeDescription.trim()) {
      alert('Please describe what you changed');
      return;
    }

    try {
      setSaving(true);
      const response = await api.put(`/clauses/${clause.id}/edit`, {
        modified_text: modifiedText,
        change_description: changeDescription
      });

      if (response.data.success) {
        setNewRiskScore(response.data.clause_version);
        setTimeout(() => {
          onSave();
        }, 2000); // Show risk improvement for 2 seconds
      } else {
        alert(response.data.error || 'Failed to update clause');
        setSaving(false);
      }
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to update clause');
      setSaving(false);
      console.error('Error updating clause:', err);
    }
  };

  if (newRiskScore) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full">
          <div className="text-center">
            <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-white mb-2">Clause Updated!</h3>
            <p className="text-slate-400 mb-4">Risk analysis complete</p>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-slate-800 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">Original Risk</p>
                <p className="text-2xl font-bold text-white">{(newRiskScore.original_risk_score * 100).toFixed(0)}%</p>
                <span className={`text-xs px-2 py-1 rounded mt-2 inline-block ${
                  newRiskScore.original_risk_level === 'HIGH' ? 'bg-red-900/30 text-red-400' :
                  newRiskScore.original_risk_level === 'MEDIUM' ? 'bg-yellow-900/30 text-yellow-400' :
                  'bg-green-900/30 text-green-400'
                }`}>
                  {newRiskScore.original_risk_level}
                </span>
              </div>

              <div className="bg-slate-800 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">New Risk</p>
                <p className="text-2xl font-bold text-white">{(newRiskScore.new_risk_score * 100).toFixed(0)}%</p>
                <span className={`text-xs px-2 py-1 rounded mt-2 inline-block ${
                  newRiskScore.new_risk_level === 'HIGH' ? 'bg-red-900/30 text-red-400' :
                  newRiskScore.new_risk_level === 'MEDIUM' ? 'bg-yellow-900/30 text-yellow-400' :
                  'bg-green-900/30 text-green-400'
                }`}>
                  {newRiskScore.new_risk_level}
                </span>
              </div>
            </div>

            {newRiskScore.risk_improved ? (
              <div className="flex items-center justify-center gap-2 text-green-400 mb-4">
                <TrendingDown className="w-5 h-5" />
                <span className="font-semibold">Risk Improved!</span>
              </div>
            ) : (
              <div className="flex items-center justify-center gap-2 text-red-400 mb-4">
                <TrendingUp className="w-5 h-5" />
                <span className="font-semibold">Risk Increased</span>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-5xl w-full my-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-white">Edit Clause</h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-slate-400" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Original */}
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Original Text
            </label>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 h-64 overflow-y-auto">
              <p className="text-slate-300 text-sm whitespace-pre-wrap">{clause.original_text}</p>
            </div>
          </div>

          {/* Modified */}
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Modified Text *
            </label>
            <textarea
              value={modifiedText}
              onChange={(e) => setModifiedText(e.target.value)}
              className="w-full h-64 bg-slate-800 border border-slate-700 rounded-lg p-4 text-slate-300 text-sm focus:outline-none focus:border-blue-500 resize-none"
              placeholder="Enter modified clause text..."
            />
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Change Description *
          </label>
          <textarea
            value={changeDescription}
            onChange={(e) => setChangeDescription(e.target.value)}
            className="w-full h-24 bg-slate-800 border border-slate-700 rounded-lg p-4 text-slate-300 text-sm focus:outline-none focus:border-blue-500 resize-none"
            placeholder="Describe what you changed and why..."
          />
        </div>

        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition"
          >
            Cancel
          </button>

          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Saving & Analyzing...
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// History Modal Component
const HistoryModal = ({ clause, onClose }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, [clause.id]);

  const loadHistory = async () => {
    try {
      const response = await api.get(`/clauses/${clause.id}/versions`);
      if (response.data.success) {
        setVersions(response.data.versions);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-4xl w-full my-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-white">Version History - {clause.clause_name}</h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-slate-400" />
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-4" />
            <p className="text-slate-400">Loading version history...</p>
          </div>
        ) : (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {versions.map((version) => (
              <div key={version.id} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="text-white font-semibold">Version {version.version_number}</span>
                    <p className="text-slate-400 text-sm">
                      {new Date(version.modified_at).toLocaleString()} by {version.modified_by}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    version.risk_level === 'HIGH' ? 'bg-red-900/30 text-red-400 border border-red-700' :
                    version.risk_level === 'MEDIUM' ? 'bg-yellow-900/30 text-yellow-400 border border-yellow-700' :
                    'bg-green-900/30 text-green-400 border border-green-700'
                  }`}>
                    {version.risk_level} ({(version.risk_score * 100).toFixed(0)}%)
                  </span>
                </div>

                <p className="text-slate-300 text-sm mb-2">
                  <strong>Change:</strong> {version.change_description}
                </p>

                <details className="text-sm">
                  <summary className="text-blue-400 cursor-pointer hover:text-blue-300 mb-2">
                    View modified text
                  </summary>
                  <div className="bg-slate-900 rounded p-3 mt-2">
                    <p className="text-slate-300 whitespace-pre-wrap">{version.modified_text}</p>
                  </div>
                </details>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClauseEditPage;
