import { useState } from 'react';
import { CheckCircle, ArrowRight, Loader } from 'lucide-react';
import api from '../utils/api';

export default function WorkflowActions({ contract, onStatusUpdate }) {
  const [loading, setLoading] = useState(false);

  const STATUS_CONFIG = {
    DRAFT: {
      label: 'Draft',
      color: 'gray',
      bgClass: 'bg-slate-600',
      textClass: 'text-slate-300',
      nextStates: ['REVIEW']
    },
    REVIEW: {
      label: 'Under Review',
      color: 'blue',
      bgClass: 'bg-blue-600',
      textClass: 'text-blue-300',
      nextStates: ['NEGOTIATION', 'FINAL']
    },
    NEGOTIATION: {
      label: 'In Negotiation',
      color: 'yellow',
      bgClass: 'bg-yellow-600',
      textClass: 'text-yellow-300',
      nextStates: ['FINAL']
    },
    FINAL: {
      label: 'Finalized',
      color: 'green',
      bgClass: 'bg-green-600',
      textClass: 'text-green-300',
      nextStates: []
    }
  };

  const currentStatus = contract.status || 'DRAFT';
  const config = STATUS_CONFIG[currentStatus];

  const handleStatusChange = async (newStatus) => {
    if (!confirm(`Change status from "${config.label}" to "${STATUS_CONFIG[newStatus].label}"?`)) {
      return;
    }

    setLoading(true);

    try {
      const response = await api.put(`/contracts/${contract.id}/status`, {
        status: newStatus
      });

      if (onStatusUpdate) {
        onStatusUpdate(response.data);
      }

      alert(response.data.message);
    } catch (error) {
      console.error('Status update error:', error);
      alert(error.response?.data?.error || 'Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-card">
      <h3 className="text-lg font-semibold text-white mb-4">Contract Workflow</h3>

      {/* Current Status */}
      <div className="flex items-center space-x-3 mb-6">
        <div className={`${config.bgClass} px-4 py-2 rounded-lg flex items-center space-x-2`}>
          <CheckCircle className="w-5 h-5 text-white" />
          <span className="text-white font-medium">{config.label}</span>
        </div>
      </div>

      {/* Status Timeline */}
      <div className="flex items-center space-x-2 mb-6">
        {Object.keys(STATUS_CONFIG).map((status, idx) => (
          <div key={status} className="flex items-center">
            <div
              className={`w-24 h-2 rounded ${
                Object.keys(STATUS_CONFIG).indexOf(currentStatus) >= idx
                  ? STATUS_CONFIG[status].bgClass
                  : 'bg-slate-700'
              }`}
            />
            {idx < Object.keys(STATUS_CONFIG).length - 1 && (
              <ArrowRight className="w-4 h-4 text-slate-600 mx-1" />
            )}
          </div>
        ))}
      </div>

      {/* Next Actions */}
      {config.nextStates.length > 0 ? (
        <div>
          <p className="text-sm text-slate-400 mb-3">Available transitions:</p>
          <div className="flex flex-wrap gap-2">
            {config.nextStates.map((nextStatus) => (
              <button
                key={nextStatus}
                onClick={() => handleStatusChange(nextStatus)}
                disabled={loading}
                className={`${STATUS_CONFIG[nextStatus].bgClass} hover:opacity-90 disabled:opacity-50 text-white px-4 py-2 rounded-lg font-medium transition flex items-center space-x-2`}
              >
                {loading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Updating...</span>
                  </>
                ) : (
                  <>
                    <ArrowRight className="w-4 h-4" />
                    <span>Move to {STATUS_CONFIG[nextStatus].label}</span>
                  </>
                )}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-green-900/20 border border-green-800 rounded-lg p-3">
          <p className="text-sm text-green-300">
            ✓ This contract has been finalized. No further status changes available.
          </p>
        </div>
      )}
    </div>
  );
}
