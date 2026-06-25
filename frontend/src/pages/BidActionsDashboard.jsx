/**
 * Bid Actions Dashboard
 * Complete action item management with filters, search, and status updates
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const BidActionsDashboard = ({ tenderId: propTenderId }) => {
  const { tenderId: paramTenderId } = useParams();
  const navigate = useNavigate();
  const tenderId = propTenderId || paramTenderId;
  const [actions, setActions] = useState([]);
  const [filters, setFilters] = useState({
    department: '',
    priority: '',
    status: '',
    search: ''
  });
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedAction, setSelectedAction] = useState(null);

  const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

  useEffect(() => {
    if (tenderId) {
      loadActions();
    }
  }, [tenderId, filters]);

  const loadActions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.department) params.append('department', filters.department);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.status) params.append('status', filters.status);
      if (filters.search) params.append('search', filters.search);

      const response = await axios.get(
        `${API_BASE}/api/tenders/${tenderId}/bid/actions/?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setActions(response.data.items || []);
      setSummary(response.data.summary || {});
    } catch (error) {
      console.error('Failed to load actions:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateAction = async (actionId, updates) => {
    try {
      await axios.patch(
        `${API_BASE}/api/tenders/${tenderId}/bid/actions/${actionId}/`,
        updates,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      loadActions(); // Reload
    } catch (error) {
      console.error('Failed to update action:', error);
      alert('Failed to update action');
    }
  };

  const generateActions = async () => {
    if (!window.confirm('Generate action items from tender data? This may take a moment.')) {
      return;
    }

    try {
      setLoading(true);
      await axios.post(
        `${API_BASE}/api/tenders/${tenderId}/bid/generate-actions/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      alert('Actions generated successfully!');
      loadActions();
    } catch (error) {
      console.error('Failed to generate actions:', error);
      alert('Failed to generate actions');
    } finally {
      setLoading(false);
    }
  };

  if (loading && actions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading actions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate(`/tenders/${tenderId}/dashboard`)}
              className="text-blue-400 hover:text-blue-300 mb-2 flex items-center text-sm"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Tender Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Bid Action Items</h1>
          </div>
          <button
            onClick={generateActions}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Generate Actions
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Filters */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <select
            value={filters.department}
            onChange={(e) => setFilters({ ...filters, department: e.target.value })}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700"
          >
            <option value="">All Departments</option>
            <option value="Civil">Civil</option>
            <option value="Mechanical">Mechanical</option>
            <option value="Electrical">Electrical</option>
            <option value="MEP">MEP</option>
            <option value="Signaling">Signaling</option>
            <option value="Planning">Planning</option>
            <option value="Procurement">Procurement</option>
            <option value="Finance">Finance</option>
            <option value="Legal">Legal</option>
            <option value="HSE">HSE</option>
            <option value="QA/QC">QA/QC</option>
          </select>

          <select
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700"
          >
            <option value="">All Priorities</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>

          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700"
          >
            <option value="">All Status</option>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Review">Review</option>
            <option value="Completed">Completed</option>
            <option value="Blocked">Blocked</option>
          </select>

          <input
            type="text"
            placeholder="Search actions..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700"
          />
        </div>

        {/* Summary Cards */}
        {Object.keys(summary).length > 0 && (
          <div className="grid grid-cols-5 gap-4 mb-6">
            {Object.entries(summary).map(([status, count]) => (
              <div key={status} className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                <div className="text-slate-400 text-sm">{status}</div>
                <div className="text-white text-2xl font-bold">{count}</div>
              </div>
            ))}
          </div>
        )}

        {/* Actions Table */}
        <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
          <table className="w-full">
            <thead className="bg-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-white">Title</th>
                <th className="px-4 py-3 text-left text-white">Department</th>
                <th className="px-4 py-3 text-left text-white">Priority</th>
                <th className="px-4 py-3 text-left text-white">Status</th>
                <th className="px-4 py-3 text-left text-white">Risk</th>
                <th className="px-4 py-3 text-left text-white">Complexity</th>
                <th className="px-4 py-3 text-left text-white">Source</th>
              </tr>
            </thead>
            <tbody>
              {actions.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-slate-400">
                    No action items found. Click "Generate Actions" to create them.
                  </td>
                </tr>
              ) : (
                actions.map((action) => (
                  <tr
                    key={action.id}
                    className="border-b border-slate-700 hover:bg-slate-750 cursor-pointer"
                    onClick={() => setSelectedAction(action)}
                  >
                    <td className="px-4 py-3 text-white">{action.title}</td>
                    <td className="px-4 py-3 text-slate-300">{action.department}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-3 py-1 rounded-full text-xs ${
                          action.priority === 'Critical'
                            ? 'bg-red-600 text-white'
                            : action.priority === 'High'
                            ? 'bg-orange-600 text-white'
                            : action.priority === 'Medium'
                            ? 'bg-yellow-600 text-white'
                            : 'bg-slate-600 text-white'
                        }`}
                      >
                        {action.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={action.status}
                        onChange={(e) => {
                          e.stopPropagation();
                          updateAction(action.id, { status: e.target.value });
                        }}
                        className="px-3 py-1 bg-slate-700 text-white rounded border border-slate-600"
                      >
                        <option value="Pending">Pending</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Review">Review</option>
                        <option value="Completed">Completed</option>
                        <option value="Blocked">Blocked</option>
                      </select>
                    </td>
                    <td className="px-4 py-3 text-white">
                      {(action.risk_score * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-white">
                      {(action.complexity_score * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-slate-300 text-sm">{action.source_type}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Detail Modal */}
      {selectedAction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-2xl w-full mx-4 border border-slate-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">{selectedAction.title}</h3>
              <button
                onClick={() => setSelectedAction(null)}
                className="text-slate-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <div className="text-slate-400 text-sm mb-1">Description</div>
                <div className="text-white">{selectedAction.description || 'No description'}</div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-slate-400 text-sm mb-1">Department</div>
                  <div className="text-white">{selectedAction.department}</div>
                </div>
                <div>
                  <div className="text-slate-400 text-sm mb-1">Source</div>
                  <div className="text-white">{selectedAction.source_type}</div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-slate-400 text-sm mb-1">Risk Score</div>
                  <div className="text-white text-2xl font-bold">
                    {(selectedAction.risk_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-sm mb-1">Complexity</div>
                  <div className="text-white text-2xl font-bold">
                    {(selectedAction.complexity_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-sm mb-1">Exposure</div>
                  <div className="text-white text-2xl font-bold">
                    ${(selectedAction.financial_exposure / 1000).toFixed(0)}K
                  </div>
                </div>
              </div>

              {selectedAction.source_ref && (
                <div>
                  <div className="text-slate-400 text-sm mb-1">Source Reference</div>
                  <div className="text-white">{selectedAction.source_ref}</div>
                </div>
              )}

              <div>
                <div className="text-slate-400 text-sm mb-1">Created</div>
                <div className="text-white">
                  {new Date(selectedAction.created_at).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BidActionsDashboard;
