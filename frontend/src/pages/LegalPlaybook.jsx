import { useState, useEffect } from 'react';
import { Scale, FileText, CheckCircle, Download, Send, AlertTriangle } from 'lucide-react';
import ClauseTable from '../components/playbook/ClauseTable';
import PlaybookAnalysis from '../components/playbook/PlaybookAnalysis';
import ActionPanel from '../components/playbook/ActionPanel';

const LegalPlaybook = () => {
  const [clauses, setClauses] = useState([]);
  const [selectedClause, setSelectedClause] = useState(null);
  const [playbook, setPlaybook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    high_risk: 0,
    medium_risk: 0,
    low_risk: 0
  });

  useEffect(() => {
    fetchClauses();
  }, []);

  const fetchClauses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/legal-playbook/clauses`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setClauses(data.clauses || []);
        setStats(data.stats || { total: 0, high_risk: 0, medium_risk: 0, low_risk: 0 });
      }
    } catch (error) {
      console.error('Error fetching clauses:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlaybook = async (clauseId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/legal-playbook/clause/${clauseId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPlaybook(data);
      }
    } catch (error) {
      console.error('Error fetching playbook:', error);
    }
  };

  const handleClauseSelect = (clause) => {
    setSelectedClause(clause);
    fetchPlaybook(clause.id);
  };

  const handleGenerateCounterProposal = async () => {
    if (!selectedClause) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/legal-playbook/clause/${selectedClause.id}/counter-proposal`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Download the counter-proposal document
        const blob = new Blob([data.proposal], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `counter-proposal-${selectedClause.clause_name}.txt`;
        a.click();
        alert('Counter-proposal generated and downloaded successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.error || 'Failed to generate counter-proposal'}`);
      }
    } catch (error) {
      console.error('Error generating counter-proposal:', error);
    }
  };

  const handleExportRedlines = async () => {
    if (!selectedClause) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/legal-playbook/clause/${selectedClause.id}/export-redlines`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `redlines-${selectedClause.clause_name}.docx`;
        a.click();
      }
    } catch (error) {
      console.error('Error exporting redlines:', error);
    }
  };

  const handleTriggerApproval = async () => {
    if (!selectedClause) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/legal-playbook/clause/${selectedClause.id}/approve`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        alert(data.message || 'Approval workflow triggered successfully');
      }
    } catch (error) {
      console.error('Error triggering approval:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl">
            <Scale className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Legal Playbook & Action Engine</h1>
            <p className="text-slate-400 text-sm mt-1">
              Convert clause risk into actionable legal strategies
            </p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs mb-1">Total Clauses</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <FileText className="w-8 h-8 text-slate-600" />
            </div>
          </div>

          <div className="bg-slate-900 border border-red-900/50 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs mb-1">High Risk</p>
                <p className="text-2xl font-bold text-red-400">{stats.high_risk}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500/50" />
            </div>
          </div>

          <div className="bg-slate-900 border border-orange-900/50 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs mb-1">Medium Risk</p>
                <p className="text-2xl font-bold text-orange-400">{stats.medium_risk}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500/50" />
            </div>
          </div>

          <div className="bg-slate-900 border border-green-900/50 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-xs mb-1">Low Risk</p>
                <p className="text-2xl font-bold text-green-400">{stats.low_risk}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500/50" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Clause Table */}
        <ClauseTable
          clauses={clauses}
          selectedClause={selectedClause}
          onClauseSelect={handleClauseSelect}
          loading={loading}
        />

        {/* Right: Playbook Analysis & Actions */}
        <div className="space-y-6">
          <PlaybookAnalysis
            clause={selectedClause}
            playbook={playbook}
          />

          {selectedClause && playbook && (
            <ActionPanel
              onGenerateCounterProposal={handleGenerateCounterProposal}
              onExportRedlines={handleExportRedlines}
              onTriggerApproval={handleTriggerApproval}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default LegalPlaybook;
