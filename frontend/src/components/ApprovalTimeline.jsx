import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Clock, User, Calendar, MapPin, Monitor, Play } from "lucide-react";
import api from "../utils/api";
import useThemeStore from "../store/themeStore";

const ApprovalTimeline = ({ contractId, onWorkflowInitiated }) => {
  const { theme } = useThemeStore();
  const [approvalData, setApprovalData] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [initiating, setInitiating] = useState(false);

  useEffect(() => {
    loadApprovalStatus();
    loadTimeline();
  }, [contractId]);

  const loadApprovalStatus = async () => {
    try {
      const response = await api.get(`/approvals/contracts/${contractId}`);
      setApprovalData(response.data);
    } catch (error) {
      console.error("Error loading approval status:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadTimeline = async () => {
    try {
      const response = await api.get(`/approvals/contracts/${contractId}/timeline`);
      setTimeline(response.data.timeline || []);
    } catch (error) {
      console.error("Error loading timeline:", error);
    }
  };

  const initiateWorkflow = async () => {
    try {
      setInitiating(true);
      await api.post(`/approvals/contracts/${contractId}/initiate`);

      // Reload status
      await loadApprovalStatus();
      await loadTimeline();

      // Notify parent component
      if (onWorkflowInitiated) {
        onWorkflowInitiated();
      }
    } catch (error) {
      console.error("Error initiating workflow:", error);
      alert(error.response?.data?.message || "Failed to initiate workflow");
    } finally {
      setInitiating(false);
    }
  };

  const getStageIcon = (status) => {
    if (status === "APPROVED") return <CheckCircle className="w-6 h-6 text-green-500" />;
    if (status === "REJECTED") return <XCircle className="w-6 h-6 text-red-500" />;
    if (status === "PENDING") return <Clock className="w-6 h-6 text-yellow-500" />;
    return <Clock className="w-6 h-6 text-gray-500" />;
  };

  const getStageColor = (status) => {
    if (status === "APPROVED") return "border-green-600 bg-green-900/20";
    if (status === "REJECTED") return "border-red-600 bg-red-900/20";
    if (status === "PENDING") return "border-yellow-600 bg-yellow-900/20";
    return "border-gray-600 bg-gray-800/20";
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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // If workflow not initiated yet
  if (!approvalData || approvalData.approval_status.total_tasks === 0) {
    return (
      <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg shadow-lg p-8 text-center`}>
        <Play className="w-16 h-16 text-blue-500 mx-auto mb-4" />
        <h3 className={`text-xl font-semibold ${theme.colors.textPrimary} mb-2`}>Approval Workflow Not Started</h3>
        <p className={`${theme.colors.textSecondary} mb-6`}>
          Initiate the approval workflow to start the review process.
        </p>
        <button
          onClick={initiateWorkflow}
          disabled={initiating}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 font-medium"
        >
          {initiating ? "Initiating..." : "Start Approval Workflow"}
        </button>
      </div>
    );
  }

  const { contract, approval_status, tasks } = approvalData;

  return (
    <div className="space-y-6">
      {/* Status Overview */}
      <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg shadow-lg p-6`}>
        <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} mb-4`}>Approval Status</h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-500">{approval_status.approved}</p>
            <p className={`text-sm ${theme.colors.textSecondary}`}>Approved</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-500">{approval_status.pending}</p>
            <p className={`text-sm ${theme.colors.textSecondary}`}>Pending</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-500">{approval_status.rejected}</p>
            <p className={`text-sm ${theme.colors.textSecondary}`}>Rejected</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-500">{approval_status.total_tasks}</p>
            <p className={`text-sm ${theme.colors.textSecondary}`}>Total Tasks</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${theme.colors.textSecondary}`}>Contract Status:</span>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            contract.status === 'APPROVED' ? 'bg-green-900 text-green-300 border border-green-700' :
            contract.status === 'REJECTED' ? 'bg-red-900 text-red-300 border border-red-700' :
            'bg-yellow-900 text-yellow-300 border border-yellow-700'
          }`}>
            {contract.status.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      {/* Approval Tasks */}
      <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg shadow-lg p-6`}>
        <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} mb-4`}>Approval Stages</h3>

        <div className="space-y-4">
          {tasks.map((task, index) => (
            <div key={task.id} className={`border-l-4 p-4 rounded ${getStageColor(task.status)}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  {getStageIcon(task.status)}

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className={`font-semibold ${theme.colors.textPrimary}`}>
                        {task.workflow_stage.replace(/_/g, ' ')}
                      </h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getRoleBadgeColor(task.role_required)}`}>
                        {task.role_required}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        task.status === 'APPROVED' ? 'bg-green-900 text-green-300 border border-green-700' :
                        task.status === 'REJECTED' ? 'bg-red-900 text-red-300 border border-red-700' :
                        'bg-yellow-900 text-yellow-300 border border-yellow-700'
                      }`}>
                        {task.status}
                      </span>
                    </div>

                    <div className={`text-sm ${theme.colors.textSecondary} space-y-1`}>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>Created: {new Date(task.created_at).toLocaleString()}</span>
                      </div>

                      {task.approved_at && (
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span>
                            {task.status === 'APPROVED' ? 'Approved' : 'Rejected'}: {new Date(task.approved_at).toLocaleString()}
                          </span>
                        </div>
                      )}

                      {task.assigned_to && (
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4" />
                          <span>By: {task.assigned_to.name} ({task.assigned_to.email})</span>
                        </div>
                      )}

                      {task.comments && (
                        <div className={`mt-2 p-3 ${theme.colors.background} rounded border ${theme.colors.surfaceBorder}`}>
                          <p className={`text-sm ${theme.colors.textSecondary} italic`}>"{task.comments}"</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Audit Trail */}
      {timeline.length > 0 && (
        <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg shadow-lg p-6`}>
          <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} mb-4`}>Audit Trail</h3>

          <div className="space-y-3">
            {timeline.map((audit, index) => (
              <div key={audit.id} className={`flex items-start gap-4 pb-3 border-b ${theme.colors.surfaceBorder} last:border-0`}>
                <div className={`p-2 rounded-full ${
                  audit.action === 'APPROVED' ? 'bg-green-900/30' :
                  audit.action === 'REJECTED' ? 'bg-red-900/30' :
                  'bg-blue-900/30'
                }`}>
                  {audit.action === 'APPROVED' ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : audit.action === 'REJECTED' ? (
                    <XCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <User className="w-5 h-5 text-blue-500" />
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`font-semibold ${theme.colors.textPrimary}`}>{audit.user.name || audit.user.email}</span>
                    <span className={`text-sm ${theme.colors.textTertiary}`}>•</span>
                    <span className={`text-sm ${theme.colors.textSecondary}`}>{audit.user.role}</span>
                  </div>

                  <p className={`text-sm ${theme.colors.textSecondary} mb-2`}>
                    <span className={`font-medium ${
                      audit.action === 'APPROVED' ? 'text-green-400' :
                      audit.action === 'REJECTED' ? 'text-red-400' :
                      'text-blue-400'
                    }`}>
                      {audit.action}
                    </span>
                    {' '}approval for <span className={`font-medium ${theme.colors.textPrimary}`}>{audit.task.workflow_stage.replace(/_/g, ' ')}</span>
                  </p>

                  {audit.comments && (
                    <p className={`text-sm ${theme.colors.textSecondary} italic mb-2`}>"{audit.comments}"</p>
                  )}

                  <div className={`flex items-center gap-4 text-xs ${theme.colors.textTertiary}`}>
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{new Date(audit.timestamp).toLocaleString()}</span>
                    </div>
                    {audit.metadata.ip_address && (
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        <span>{audit.metadata.ip_address}</span>
                      </div>
                    )}
                    {audit.metadata.user_agent && (
                      <div className="flex items-center gap-1">
                        <Monitor className="w-3 h-3" />
                        <span className="truncate max-w-xs">{audit.metadata.user_agent.substring(0, 50)}...</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalTimeline;
