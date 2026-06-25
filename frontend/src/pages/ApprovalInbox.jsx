import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle, XCircle, Clock, FileText, AlertCircle, User, Calendar } from "lucide-react";
import api from "../utils/api";

const ApprovalInbox = () => {
  const navigate = useNavigate();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [processing, setProcessing] = useState(null);

  // Modal states
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [comments, setComments] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // Load approval tasks and stats
  useEffect(() => {
    loadInbox();
    loadStats();
  }, []);

  const loadInbox = async () => {
    try {
      setLoading(true);
      const response = await api.get("/approvals/inbox");
      setTasks(response.data.tasks || []);
    } catch (error) {
      console.error("Error loading approval inbox:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.get("/approvals/stats");
      setStats(response.data.stats);
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  const handleApprove = async () => {
    if (!selectedTask) return;

    try {
      setActionLoading(true);
      await api.post(`/approvals/tasks/${selectedTask.id}/approve`, {
        comments: comments.trim() || "Approved"
      });

      // Success - reload inbox
      await loadInbox();
      await loadStats();

      setShowApproveModal(false);
      setSelectedTask(null);
      setComments("");
    } catch (error) {
      console.error("Error approving task:", error);
      alert(error.response?.data?.message || "Failed to approve task");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedTask) return;

    if (!comments.trim()) {
      alert("Rejection reason is required");
      return;
    }

    try {
      setActionLoading(true);
      await api.post(`/approvals/tasks/${selectedTask.id}/reject`, {
        comments: comments.trim()
      });

      // Success - reload inbox
      await loadInbox();
      await loadStats();

      setShowRejectModal(false);
      setSelectedTask(null);
      setComments("");
    } catch (error) {
      console.error("Error rejecting task:", error);
      alert(error.response?.data?.message || "Failed to reject task");
    } finally {
      setActionLoading(false);
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      LEGAL: "bg-blue-900 text-blue-300 border border-blue-700",
      BUSINESS: "bg-green-900 text-green-300 border border-green-700",
      COMPLIANCE: "bg-purple-900 text-purple-300 border border-purple-700",
      ADMIN: "bg-red-900 text-red-300 border border-red-700"
    };
    return colors[role] || "bg-gray-800 text-gray-300 border border-gray-600";
  };

  const getStatusColor = (status) => {
    const colors = {
      PENDING: "text-yellow-600",
      APPROVED: "text-green-600",
      REJECTED: "text-red-600"
    };
    return colors[status] || "text-gray-600";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0f172a] p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f172a] p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Approval Inbox</h1>
          <p className="text-gray-400">Review and approve pending contract tasks</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-[#1e293b] rounded-lg shadow-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Pending Tasks</p>
                  <p className="text-3xl font-bold text-yellow-500">{stats.pending}</p>
                </div>
                <Clock className="w-12 h-12 text-yellow-500 opacity-20" />
              </div>
            </div>

            <div className="bg-[#1e293b] rounded-lg shadow-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Approved</p>
                  <p className="text-3xl font-bold text-green-500">{stats.approved}</p>
                </div>
                <CheckCircle className="w-12 h-12 text-green-500 opacity-20" />
              </div>
            </div>

            <div className="bg-[#1e293b] rounded-lg shadow-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Rejected</p>
                  <p className="text-3xl font-bold text-red-500">{stats.rejected}</p>
                </div>
                <XCircle className="w-12 h-12 text-red-500 opacity-20" />
              </div>
            </div>

            <div className="bg-[#1e293b] rounded-lg shadow-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Total Actions</p>
                  <p className="text-3xl font-bold text-blue-500">{stats.total_actions}</p>
                </div>
                <FileText className="w-12 h-12 text-blue-500 opacity-20" />
              </div>
            </div>
          </div>
        )}

        {/* Tasks List */}
        {tasks.length === 0 ? (
          <div className="bg-[#1e293b] rounded-lg shadow-lg border border-gray-700 p-12 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">All Caught Up!</h3>
            <p className="text-gray-400">You have no pending approval tasks.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {tasks.map((task) => (
              <div key={task.id} className="bg-[#1e293b] rounded-lg shadow-lg border border-gray-700 hover:border-gray-600 transition-all">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <FileText className="w-5 h-5 text-blue-400" />
                        <h3
                          className="text-lg font-semibold text-white hover:text-blue-400 cursor-pointer"
                          onClick={() => navigate(`/contracts/${task.contract_id}`)}
                        >
                          {task.contract_name}
                        </h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleBadgeColor(task.role_required)}`}>
                          {task.role_required}
                        </span>
                      </div>

                      {task.contract_type && (
                        <p className="text-sm text-gray-400 mb-2">
                          Type: <span className="font-medium text-gray-300">{task.contract_type}</span>
                        </p>
                      )}

                      <div className="flex items-center gap-4 text-sm text-gray-400">
                        <div className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          <span>{task.contract_owner.name || task.contract_owner.email}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>{new Date(task.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <AlertCircle className="w-4 h-4" />
                          <span>Stage: {task.workflow_stage.replace(/_/g, ' ')}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setSelectedTask(task);
                          setShowApproveModal(true);
                        }}
                        disabled={processing === task.id}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>

                      <button
                        onClick={() => {
                          setSelectedTask(task);
                          setShowRejectModal(true);
                        }}
                        disabled={processing === task.id}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>

                      <button
                        onClick={() => navigate(`/contracts/${task.contract_id}`)}
                        className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Approve Modal */}
        {showApproveModal && selectedTask && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
            <div className="bg-[#1e293b] border border-gray-700 rounded-lg shadow-xl max-w-md w-full mx-4">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <CheckCircle className="w-8 h-8 text-green-500" />
                  <h3 className="text-xl font-semibold text-white">Approve Contract</h3>
                </div>

                <p className="text-gray-400 mb-4">
                  You are about to approve <span className="font-semibold text-white">{selectedTask.contract_name}</span>
                </p>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Approval Comments (Optional)
                  </label>
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="Add any comments about this approval..."
                    className="w-full px-3 py-2 bg-[#0f172a] border border-gray-600 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 placeholder-gray-500"
                    rows={3}
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleApprove}
                    disabled={actionLoading}
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition disabled:opacity-50"
                  >
                    {actionLoading ? "Approving..." : "Confirm Approval"}
                  </button>
                  <button
                    onClick={() => {
                      setShowApproveModal(false);
                      setSelectedTask(null);
                      setComments("");
                    }}
                    disabled={actionLoading}
                    className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reject Modal */}
        {showRejectModal && selectedTask && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
            <div className="bg-[#1e293b] border border-gray-700 rounded-lg shadow-xl max-w-md w-full mx-4">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <XCircle className="w-8 h-8 text-red-500" />
                  <h3 className="text-xl font-semibold text-white">Reject Contract</h3>
                </div>

                <p className="text-gray-400 mb-4">
                  You are about to reject <span className="font-semibold text-white">{selectedTask.contract_name}</span>
                </p>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Rejection Reason <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="Please provide a detailed reason for rejection..."
                    className="w-full px-3 py-2 bg-[#0f172a] border border-gray-600 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 placeholder-gray-500"
                    rows={4}
                  />
                  {!comments.trim() && (
                    <p className="text-sm text-red-400 mt-1">Rejection reason is required</p>
                  )}
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleReject}
                    disabled={actionLoading || !comments.trim()}
                    className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition disabled:opacity-50"
                  >
                    {actionLoading ? "Rejecting..." : "Confirm Rejection"}
                  </button>
                  <button
                    onClick={() => {
                      setShowRejectModal(false);
                      setSelectedTask(null);
                      setComments("");
                    }}
                    disabled={actionLoading}
                    className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApprovalInbox;
