import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import { Clock, User, FileText, ChevronDown, ChevronUp } from 'lucide-react';

const VersionHistory = ({ contractId, refreshKey = 0 }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedVersions, setExpandedVersions] = useState(new Set());

  useEffect(() => {
    if (contractId) {
      loadVersionHistory();
    }
  }, [contractId, refreshKey]);

  const loadVersionHistory = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/contracts/${contractId}/versions`);
      setVersions(response.data.versions || []);
      setError(null);
    } catch (err) {
      console.error('Failed to load version history:', err);
      setError('Failed to load version history');
    } finally {
      setLoading(false);
    }
  };

  const toggleVersionExpand = (versionId) => {
    setExpandedVersions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(versionId)) {
        newSet.delete(versionId);
      } else {
        newSet.add(versionId);
      }
      return newSet;
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (versions.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
        <FileText className="mx-auto h-12 w-12 text-slate-500 mb-3" />
        <p className="text-slate-400">No version history available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Version History</h3>
        <span className="text-sm text-slate-400">
          {versions.length} {versions.length === 1 ? 'version' : 'versions'}
        </span>
      </div>

      <div className="space-y-3">
        {versions.map((version, index) => {
          const isExpanded = expandedVersions.has(version.id);
          const isLatest = index === 0;

          return (
            <div
              key={version.id}
              className={`border rounded-lg overflow-hidden transition-all ${
                isLatest
                  ? 'border-blue-500 bg-blue-900/30'
                  : 'border-slate-700 bg-slate-800 hover:border-slate-600'
              }`}
            >
              {/* Version Header */}
              <div
                className="p-4 cursor-pointer"
                onClick={() => toggleVersionExpand(version.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          isLatest
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-700 text-slate-200'
                        }`}
                      >
                        v{version.version_number}
                        {isLatest && ' (Current)'}
                      </span>

                      <span className="text-sm font-medium text-slate-200">
                        {version.change_description || 'No description'}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <div className="flex items-center gap-1">
                        <User size={14} />
                        <span>{version.created_by_name}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock size={14} />
                        <span>{formatDate(version.created_at)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <FileText size={14} />
                        <span>{version.file_type}</span>
                      </div>
                    </div>
                  </div>

                  <button
                    className="ml-4 p-1 hover:bg-slate-700 rounded"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleVersionExpand(version.id);
                    }}
                  >
                    {isExpanded ? (
                      <ChevronUp size={20} className="text-slate-400" />
                    ) : (
                      <ChevronDown size={20} className="text-slate-400" />
                    )}
                  </button>
                </div>
              </div>

              {/* Expanded Version Details */}
              {isExpanded && (
                <div className="border-t border-slate-700 bg-slate-900/50 p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <label className="font-medium text-slate-300">Filename:</label>
                      <p className="text-slate-400 mt-1">{version.original_filename}</p>
                    </div>
                    {version.contract_type && (
                      <div>
                        <label className="font-medium text-slate-300">Contract Type:</label>
                        <p className="text-slate-400 mt-1">{version.contract_type}</p>
                      </div>
                    )}
                    {version.party_name && (
                      <div>
                        <label className="font-medium text-slate-300">Party Name:</label>
                        <p className="text-slate-400 mt-1">{version.party_name}</p>
                      </div>
                    )}
                    {version.contract_value && (
                      <div>
                        <label className="font-medium text-slate-300">Contract Value:</label>
                        <p className="text-slate-400 mt-1">{version.contract_value}</p>
                      </div>
                    )}
                    {version.contract_duration && (
                      <div>
                        <label className="font-medium text-slate-300">Duration:</label>
                        <p className="text-slate-400 mt-1">{version.contract_duration}</p>
                      </div>
                    )}
                  </div>

                  {version.full_text && (
                    <div>
                      <label className="font-medium text-slate-300 block mb-2">
                        Text Preview:
                      </label>
                      <div className="bg-slate-950 border border-slate-700 rounded p-3 text-xs text-slate-400 font-mono max-h-40 overflow-y-auto">
                        {version.full_text.substring(0, 500)}
                        {version.full_text.length > 500 && '...'}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default VersionHistory;
