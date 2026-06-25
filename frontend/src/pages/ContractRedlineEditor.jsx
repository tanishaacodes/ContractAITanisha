import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  Loader,
  CheckCircle,
  XCircle,
  Download,
  FileText,
  Scale,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Edit3,
  Eye,
  Filter,
  BarChart3
} from 'lucide-react';
import api from '../utils/api';
import ClauseRedlineCard from '../components/ClauseRedlineCard';

const ContractRedlineEditor = () => {
  const { contractId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Session state
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [session, setSession] = useState(null);
  const [clauses, setClauses] = useState([]);

  // UI state
  const [expandedClauseId, setExpandedClauseId] = useState(null);
  const [filterRisk, setFilterRisk] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showSummary, setShowSummary] = useState(true);
  const [exporting, setExporting] = useState(null);

  // Contract info
  const [contractName, setContractName] = useState('');
  const [jurisdiction, setJurisdiction] = useState('Common Law');

  // Check for existing session or start new one
  useEffect(() => {
    const sessionId = searchParams.get('session');
    if (sessionId) {
      fetchSession(sessionId);
    } else {
      checkExistingSessions();
    }
  }, [contractId, searchParams]);

  const checkExistingSessions = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/redline/contracts/${contractId}/sessions`);
      setContractName(response.data.contract_name);

      // If there's an in-progress session, load it
      const inProgressSession = response.data.sessions.find(s => s.status === 'IN_PROGRESS');
      if (inProgressSession) {
        fetchSession(inProgressSession.id);
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error('Error checking sessions:', error);
      setLoading(false);
    }
  };

  const fetchSession = async (sessionId) => {
    try {
      setLoading(true);
      const response = await api.get(`/redline/sessions/${sessionId}`);
      setSession(response.data);
      setClauses(response.data.clauses || []);
      setContractName(response.data.contract_name);
      setJurisdiction(response.data.jurisdiction);
    } catch (error) {
      console.error('Error fetching session:', error);
      alert(error.response?.data?.message || 'Failed to load redline session');
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = async () => {
    try {
      setStarting(true);
      const response = await api.post(`/redline/contracts/${contractId}/start`, {
        jurisdiction
      });

      setSession(response.data);
      setClauses(response.data.clauses || []);
      setContractName(response.data.contract_name);

      // Update URL with session ID
      navigate(`/contracts/${contractId}/redline-editor?session=${response.data.session_id}`, { replace: true });
    } catch (error) {
      console.error('Error starting session:', error);
      alert(error.response?.data?.message || 'Failed to start redline session');
    } finally {
      setStarting(false);
    }
  };

  const handleClauseUpdate = async (changeId, action, acceptedText = null) => {
    try {
      const response = await api.post(`/redline/changes/${changeId}/update`, {
        action,
        accepted_text: acceptedText
      });

      // Update local state
      setClauses(prev => prev.map(clause => {
        if (clause.id === changeId) {
          return {
            ...clause,
            status: response.data.status,
            accepted_text: response.data.accepted_text
          };
        }
        return clause;
      }));

      // Update session stats
      setSession(prev => ({
        ...prev,
        changes_accepted: response.data.session_accepted,
        changes_rejected: response.data.session_rejected
      }));

    } catch (error) {
      console.error('Error updating clause:', error);
      alert(error.response?.data?.message || 'Failed to update clause');
    }
  };

  const handleRegenerateSuggestion = async (changeId, perspective = 'balanced') => {
    try {
      const response = await api.post(`/redline/changes/${changeId}/regenerate`, {
        perspective
      });

      // Update local state
      setClauses(prev => prev.map(clause => {
        if (clause.id === changeId) {
          return {
            ...clause,
            suggested_text: response.data.suggested_text,
            redline_diff: response.data.redline_diff
          };
        }
        return clause;
      }));

    } catch (error) {
      console.error('Error regenerating suggestion:', error);
      alert(error.response?.data?.message || 'Failed to regenerate suggestion');
    }
  };

  const handleExport = async (format) => {
    if (!session) return;

    try {
      setExporting(format);
      const endpoint = format === 'docx'
        ? `/redline/sessions/${session.session_id}/export/docx`
        : `/redline/sessions/${session.session_id}/export/pdf`;

      const response = await api.get(endpoint, { responseType: 'blob' });

      // Create download link
      const blob = new Blob([response.data], {
        type: format === 'docx'
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${contractName}_Redlined.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Error exporting:', error);
      alert(`Failed to export ${format.toUpperCase()}`);
    } finally {
      setExporting(null);
    }
  };

  const handleCompleteSession = async () => {
    if (!session) return;

    try {
      const pendingCount = clauses.filter(c => c.status === 'PENDING').length;
      if (pendingCount > 0) {
        if (!window.confirm(`You have ${pendingCount} pending changes. Are you sure you want to complete the session?`)) {
          return;
        }
      }

      await api.post(`/redline/sessions/${session.session_id}/complete`);
      setSession(prev => ({ ...prev, status: 'COMPLETED' }));
      alert('Redline session completed successfully!');

    } catch (error) {
      console.error('Error completing session:', error);
      alert(error.response?.data?.message || 'Failed to complete session');
    }
  };

  // Filter clauses
  const filteredClauses = clauses.filter(clause => {
    if (filterRisk !== 'all') {
      if (filterRisk === 'high' && clause.risk_score < 70) return false;
      if (filterRisk === 'medium' && (clause.risk_score < 40 || clause.risk_score >= 70)) return false;
      if (filterRisk === 'low' && clause.risk_score >= 40) return false;
    }
    if (filterStatus !== 'all' && clause.status !== filterStatus) return false;
    return true;
  });

  const getRiskColor = (score) => {
    if (score >= 70) return 'text-red-400 bg-red-900/30 border-red-700';
    if (score >= 40) return 'text-yellow-400 bg-yellow-900/30 border-yellow-700';
    return 'text-green-400 bg-green-900/30 border-green-700';
  };

  const getRiskBadge = (score) => {
    if (score >= 70) return { label: 'HIGH', color: 'bg-red-600' };
    if (score >= 40) return { label: 'MEDIUM', color: 'bg-yellow-600' };
    return { label: 'LOW', color: 'bg-green-600' };
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <Loader size={48} className="animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Loading redline session...</p>
        </div>
      </div>
    );
  }

  // No session - show start screen
  if (!session) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => navigate(`/contracts/${contractId}`)}
            className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition"
          >
            <ArrowLeft size={20} />
            <span>Back to Contract</span>
          </button>

          <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center">
            <Scale size={64} className="text-blue-500 mx-auto mb-6" />
            <h1 className="text-3xl font-bold text-white mb-4">Contract Redlining</h1>
            <p className="text-slate-400 mb-8 max-w-xl mx-auto">
              AI-powered contract review that identifies risky clauses, explains legal implications,
              and suggests safer alternatives with track changes support.
            </p>

            {/* Jurisdiction selector */}
            <div className="mb-8">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Legal Jurisdiction
              </label>
              <select
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2 w-64"
              >
                <option value="Common Law">Common Law</option>
                <option value="US">United States</option>
                <option value="UK">United Kingdom</option>
                <option value="EU">European Union</option>
                <option value="UAE">UAE / Middle East</option>
              </select>
            </div>

            <button
              onClick={startNewSession}
              disabled={starting}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition flex items-center gap-2 mx-auto disabled:opacity-50"
            >
              {starting ? (
                <>
                  <Loader size={20} className="animate-spin" />
                  Analyzing Contract...
                </>
              ) : (
                <>
                  <FileText size={20} />
                  Start Redline Analysis
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main editor view
  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(`/contracts/${contractId}`)}
            className="flex items-center gap-2 text-slate-400 hover:text-white mb-4 transition"
          >
            <ArrowLeft size={20} />
            <span>Back to Contract</span>
          </button>

          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <h1 className="text-2xl font-bold text-white mb-1">Contract Redlining</h1>
                <p className="text-slate-400">{contractName}</p>
                <p className="text-sm text-slate-500">Jurisdiction: {jurisdiction}</p>
              </div>

              <div className="flex items-center gap-3">
                {/* Export buttons */}
                <button
                  onClick={() => handleExport('docx')}
                  disabled={exporting === 'docx'}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
                >
                  {exporting === 'docx' ? <Loader size={18} className="animate-spin" /> : <FileText size={18} />}
                  Export DOCX
                </button>
                <button
                  onClick={() => handleExport('pdf')}
                  disabled={exporting === 'pdf'}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition disabled:opacity-50"
                >
                  {exporting === 'pdf' ? <Loader size={18} className="animate-spin" /> : <Download size={18} />}
                  Export PDF
                </button>
                {session.status === 'IN_PROGRESS' && (
                  <button
                    onClick={handleCompleteSession}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
                  >
                    <CheckCircle size={18} />
                    Complete
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Summary Panel */}
        <div className="mb-6">
          <button
            onClick={() => setShowSummary(!showSummary)}
            className="flex items-center gap-2 text-slate-300 hover:text-white mb-3 transition"
          >
            <BarChart3 size={18} />
            <span className="font-medium">Analysis Summary</span>
            {showSummary ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>

          {showSummary && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4 text-center">
                <div className="text-3xl font-bold text-white">{session.total_clauses}</div>
                <div className="text-sm text-slate-400">Total Clauses</div>
              </div>
              <div className="bg-slate-800 rounded-lg border border-red-700/50 p-4 text-center">
                <div className="text-3xl font-bold text-red-400">{session.high_risk_count}</div>
                <div className="text-sm text-slate-400">High Risk</div>
              </div>
              <div className="bg-slate-800 rounded-lg border border-yellow-700/50 p-4 text-center">
                <div className="text-3xl font-bold text-yellow-400">{session.medium_risk_count}</div>
                <div className="text-sm text-slate-400">Medium Risk</div>
              </div>
              <div className="bg-slate-800 rounded-lg border border-green-700/50 p-4 text-center">
                <div className="text-3xl font-bold text-green-400">{session.changes_accepted}</div>
                <div className="text-sm text-slate-400">Accepted</div>
              </div>
              <div className="bg-slate-800 rounded-lg border border-slate-600 p-4 text-center">
                <div className="text-3xl font-bold text-slate-300">{session.changes_rejected}</div>
                <div className="text-sm text-slate-400">Rejected</div>
              </div>
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-slate-400" />
            <span className="text-slate-400 text-sm">Filter:</span>
          </div>

          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm"
          >
            <option value="all">All Risk Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="ACCEPTED">Accepted</option>
            <option value="REJECTED">Rejected</option>
            <option value="MODIFIED">Modified</option>
          </select>

          <span className="text-slate-500 text-sm">
            Showing {filteredClauses.length} of {clauses.length} clauses
          </span>
        </div>

        {/* Clauses List */}
        <div className="space-y-4">
          {filteredClauses.map((clause, index) => (
            <ClauseRedlineCard
              key={clause.id}
              clause={clause}
              index={index + 1}
              isExpanded={expandedClauseId === clause.id}
              onToggle={() => setExpandedClauseId(expandedClauseId === clause.id ? null : clause.id)}
              onAccept={(text) => handleClauseUpdate(clause.id, 'accept', text)}
              onReject={() => handleClauseUpdate(clause.id, 'reject')}
              onModify={(text) => handleClauseUpdate(clause.id, 'modify', text)}
              onRegenerate={(perspective) => handleRegenerateSuggestion(clause.id, perspective)}
            />
          ))}
        </div>

        {/* Empty state */}
        {filteredClauses.length === 0 && (
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-12 text-center">
            <AlertTriangle size={48} className="text-slate-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-300 mb-2">No Clauses Found</h3>
            <p className="text-slate-500">
              {clauses.length === 0
                ? 'No clauses were extracted from this contract.'
                : 'No clauses match your current filters.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContractRedlineEditor;
