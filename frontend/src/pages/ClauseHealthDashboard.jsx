import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, XCircle, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import ClauseHealthCard from '../components/self-healing/ClauseHealthCard';
import HealthReportSummary from '../components/self-healing/HealthReportSummary';
import ClauseHealthChart from '../components/self-healing/ClauseHealthChart';
import PromotionModal from '../components/self-healing/PromotionModal';

/**
 * Self-Healing Clause Library - Health Dashboard
 * Displays real-time health metrics for all clauses
 */
const ClauseHealthDashboard = () => {
  const [healthData, setHealthData] = useState([]);
  const [healthReport, setHealthReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [sortBy, setSortBy] = useState('health_score');
  const [modalOpen, setModalOpen] = useState(false);
  const [modalResult, setModalResult] = useState(null);
  const [isAnalysisMode, setIsAnalysisMode] = useState(false);

  useEffect(() => {
    fetchHealthData();
    fetchHealthReport();
  }, []);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/clauses/health/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      setHealthData(response.data.clauses || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching health data:', err);
      setError('Failed to load clause health data');
    } finally {
      setLoading(false);
    }
  };

  const fetchHealthReport = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/clauses/health/report/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      setHealthReport(response.data);
    } catch (err) {
      console.error('Error fetching health report:', err);
    }
  };

  const handlePromoteClause = async (clauseId, dryRun = false) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/clauses/promote/${clauseId}/`,
        { dry_run: dryRun },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Show modal with result
      setModalResult(response.data);
      setIsAnalysisMode(dryRun);
      setModalOpen(true);

      // Refresh data if actually promoted
      if (!dryRun && response.data.promoted) {
        fetchHealthData();
      }
    } catch (err) {
      console.error('Error promoting clause:', err);
      setModalResult({
        reason: 'Error: Failed to promote clause. Please try again.',
        promoted: false
      });
      setIsAnalysisMode(dryRun);
      setModalOpen(true);
    }
  };

  const handleRetireWeak = async () => {
    if (!confirm('Are you sure you want to retire all weak clauses?')) {
      return;
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}/clauses/retire/`,
        { dry_run: false, min_health_score: 0.45 },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      alert(`✅ Retired ${response.data.retired} weak clauses`);
      fetchHealthData(); // Refresh data
    } catch (err) {
      console.error('Error retiring clauses:', err);
      alert('Failed to retire clauses');
    }
  };

  // Filter and sort clauses
  const filteredClauses = healthData
    .filter(clause => filterStatus === 'ALL' || clause.status === filterStatus)
    .sort((a, b) => {
      if (sortBy === 'health_score') return b.health_score - a.health_score;
      if (sortBy === 'success_rate') return b.success_rate - a.success_rate;
      if (sortBy === 'name') return a.clause_code.localeCompare(b.clause_code);
      return 0;
    });

  const getStatusColor = (status) => {
    switch (status) {
      case 'ALIVE':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'WEAK':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'RETIRED':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ALIVE':
        return <CheckCircle className="w-5 h-5" />;
      case 'WEAK':
        return <AlertCircle className="w-5 h-5" />;
      case 'RETIRED':
        return <XCircle className="w-5 h-5" />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070d1a]">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-11 h-11 rounded-2xl flex items-center justify-center" style={{background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 0 20px rgba(99,102,241,0.4)'}}>
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Clause Health Dashboard</h1>
            <p className="text-slate-500 text-sm">Self-Healing Clause Library · Real-time monitoring & auto-promotion</p>
          </div>
        </div>
        <div className="h-px mt-4" style={{background: 'linear-gradient(90deg, rgba(99,102,241,0.5), transparent)'}} />
      </div>

      {/* Health Report Summary */}
      {healthReport && <HealthReportSummary report={healthReport} />}

      {/* Actions bar */}
      <div className="rounded-2xl border border-white/5 p-4 mb-6 flex items-center justify-between flex-wrap gap-4" style={{background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(10px)'}}>
        <div className="flex gap-4 flex-wrap items-center">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Filter</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="text-sm rounded-xl px-3 py-2 text-slate-200 border border-white/10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              style={{background: 'rgba(255,255,255,0.06)'}}
            >
              <option value="ALL">All Clauses</option>
              <option value="ALIVE">Alive Only</option>
              <option value="WEAK">Weak Only</option>
              <option value="RETIRED">Retired Only</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sort</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="text-sm rounded-xl px-3 py-2 text-slate-200 border border-white/10 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              style={{background: 'rgba(255,255,255,0.06)'}}
            >
              <option value="health_score">Health Score</option>
              <option value="success_rate">Success Rate</option>
              <option value="name">Name</option>
            </select>
          </div>
          <span className="text-xs text-slate-600">{filteredClauses.length} clauses</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchHealthData}
            className="px-4 py-2 text-sm font-semibold rounded-xl border border-indigo-500/40 text-indigo-300 transition-all hover:bg-indigo-500/20"
            style={{background: 'rgba(99,102,241,0.1)'}}
          >
            Refresh
          </button>
          <button
            onClick={handleRetireWeak}
            className="px-4 py-2 text-sm font-semibold rounded-xl border border-red-500/40 text-red-300 transition-all hover:bg-red-500/20"
            style={{background: 'rgba(239,68,68,0.1)'}}
          >
            Retire Weak Clauses
          </button>
        </div>
      </div>

      {/* Health Chart */}
      {filteredClauses.length > 0 && (
        <ClauseHealthChart data={filteredClauses} />
      )}

      {/* Clause Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-2">
        {filteredClauses.length === 0 ? (
          <div className="col-span-full text-center py-16">
            <div className="rounded-2xl border border-white/5 p-10" style={{background: 'rgba(255,255,255,0.02)'}}>
              <BarChart3 className="w-12 h-12 text-slate-700 mx-auto mb-4" />
              <p className="text-slate-400 text-base font-semibold">No clauses found</p>
              <p className="text-slate-600 text-sm mt-2">Upload contracts to generate clause health data</p>
            </div>
          </div>
        ) : (
          filteredClauses.map((clause) => (
            <ClauseHealthCard
              key={clause.clause_id}
              clause={clause}
              onPromote={handlePromoteClause}
              getStatusColor={getStatusColor}
              getStatusIcon={getStatusIcon}
            />
          ))
        )}
      </div>

      {/* Promotion Modal */}
      <PromotionModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        result={modalResult}
        isAnalysis={isAnalysisMode}
      />
    </div>
  );
};

export default ClauseHealthDashboard;
