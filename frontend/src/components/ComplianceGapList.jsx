import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Filter,
} from 'lucide-react';
import api from '../utils/api';

const ComplianceGapList = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [gaps, setGaps] = useState([]);
  const [expandedGap, setExpandedGap] = useState(null);

  // Filters
  const [frameworks, setFrameworks] = useState([]);
  const [selectedFramework, setSelectedFramework] = useState('');
  const [selectedCriticality, setSelectedCriticality] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');

  useEffect(() => {
    loadGaps();
  }, [selectedFramework, selectedCriticality, selectedStatus]);

  const loadGaps = async () => {
    try {
      setLoading(true);
      const params = {};
      if (selectedFramework) params.framework = selectedFramework;
      if (selectedCriticality) params.criticality = selectedCriticality;
      if (selectedStatus) params.status = selectedStatus;

      const response = await api.get('/compliance/gaps', { params });
      setGaps(response.data.gaps || []);

      // Extract unique frameworks from gaps
      const uniqueFrameworks = [...new Set(response.data.gaps?.map(g => g.frameworkCode) || [])];
      setFrameworks(uniqueFrameworks);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load compliance gaps');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const CRITICALITY_COLORS = {
    CRITICAL: { bg: 'bg-red-900/30', border: 'border-red-700/50', text: 'text-red-400' },
    HIGH: { bg: 'bg-orange-900/30', border: 'border-orange-700/50', text: 'text-orange-400' },
    MEDIUM: { bg: 'bg-yellow-900/30', border: 'border-yellow-700/50', text: 'text-yellow-400' },
    LOW: { bg: 'bg-green-900/30', border: 'border-green-700/50', text: 'text-green-400' },
  };

  const FRAMEWORK_COLORS = {
    GDPR: 'bg-blue-900/30 border-blue-700/50 text-blue-400',
    SOX: 'bg-purple-900/30 border-purple-700/50 text-purple-400',
    HIPAA: 'bg-pink-900/30 border-pink-700/50 text-pink-400',
    GST: 'bg-amber-900/30 border-amber-700/50 text-amber-400',
  };

  if (loading && gaps.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
          <p className="text-slate-400">Loading compliance gaps...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 text-red-300 rounded-lg p-4">
        <AlertTriangle size={20} className="inline mr-2" />
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Filter size={20} className="text-slate-400" />
          <p className="text-white font-semibold">Filters</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Framework Filter */}
          <div>
            <label className="block text-sm text-slate-400 mb-2">Framework</label>
            <select
              value={selectedFramework}
              onChange={(e) => setSelectedFramework(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Frameworks</option>
              {frameworks.map((framework) => (
                <option key={framework} value={framework}>
                  {framework}
                </option>
              ))}
            </select>
          </div>

          {/* Criticality Filter */}
          <div>
            <label className="block text-sm text-slate-400 mb-2">Criticality</label>
            <select
              value={selectedCriticality}
              onChange={(e) => setSelectedCriticality(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm text-slate-400 mb-2">Compliance Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="PARTIAL">Partial</option>
              <option value="NON_COMPLIANT">Non-Compliant</option>
            </select>
          </div>
        </div>
      </div>

      {/* Gaps Table */}
      {gaps && gaps.length > 0 ? (
        <div className="space-y-2">
          {gaps.map((gap) => {
            const criticality = gap.criticality || 'MEDIUM';
            const criticityColor = CRITICALITY_COLORS[criticality] || CRITICALITY_COLORS.MEDIUM;
            const frameworkColor = FRAMEWORK_COLORS[gap.frameworkCode] || 'bg-slate-900/30 border-slate-700/50 text-slate-400';
            const expanded = expandedGap === gap.id;

            return (
              <div
                key={gap.id}
                className={`border rounded-lg overflow-hidden transition-all ${
                  criticityColor.bg
                } ${criticityColor.border}`}
              >
                <button
                  onClick={() =>
                    setExpandedGap(expanded ? null : gap.id)
                  }
                  className="w-full p-4 flex items-center justify-between hover:bg-slate-700/20 transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1 text-left">
                    <AlertTriangle size={20} className={criticityColor.text} />
                    <div className="flex-1">
                      <p className="text-white font-semibold">{gap.requirementCode}</p>
                      <p className="text-slate-400 text-sm">{gap.requirementName}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${frameworkColor}`}>
                        {gap.frameworkCode}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${criticityColor.bg} ${criticityColor.border} ${criticityColor.text}`}>
                        {criticality}
                      </span>
                    </div>
                  </div>
                  {expanded ? (
                    <ChevronUp size={20} className="text-slate-400 ml-2" />
                  ) : (
                    <ChevronDown size={20} className="text-slate-400 ml-2" />
                  )}
                </button>

                {/* Expanded Content */}
                {expanded && (
                  <div className="border-t border-slate-700 p-4 bg-slate-900/30">
                    <div className="space-y-4">
                      {gap.description && (
                        <div>
                          <p className="text-slate-400 text-sm font-semibold mb-1">
                            Description
                          </p>
                          <p className="text-slate-300">{gap.description}</p>
                        </div>
                      )}

                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-2 border-t border-slate-700">
                        <div>
                          <p className="text-slate-400 text-xs mb-1">Affected Contracts</p>
                          <p className="text-white font-semibold text-lg">
                            {gap.affected_contracts_count || 0}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs mb-1">Avg Risk Score</p>
                          <p className="text-white font-semibold text-lg">
                            {parseFloat(((gap.avg_risk_score || 0) * 100).toFixed(1))}%
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs mb-1">Non-Compliance Rate</p>
                          <p className="text-white font-semibold text-lg">
                            {parseFloat(((gap.non_compliance_rate || 0) * 100).toFixed(1))}%
                          </p>
                        </div>
                      </div>

                      {gap.affected_contracts && gap.affected_contracts.length > 0 && (
                        <div>
                          <p className="text-slate-400 text-sm font-semibold mb-2">
                            Affected Contracts
                          </p>
                          <div className="space-y-1">
                            {gap.affected_contracts.map((contract, idx) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between bg-slate-900/30 p-2 rounded text-sm"
                              >
                                <span className="text-slate-300">{contract.name}</span>
                                <span className="text-slate-400 text-xs">
                                  Risk: {parseFloat(((contract.risk_score || 0) * 100).toFixed(1))}%
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
          <p className="text-slate-400">No compliance gaps found with the selected filters.</p>
        </div>
      )}
    </div>
  );
};

export default ComplianceGapList;
