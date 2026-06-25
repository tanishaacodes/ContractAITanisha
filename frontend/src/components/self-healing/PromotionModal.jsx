import { CheckCircle, XCircle, Info, X } from 'lucide-react';

/**
 * Promotion Result Modal Component
 * Displays promotion/analysis results in a clean modal
 */
const PromotionModal = ({ isOpen, onClose, result, isAnalysis }) => {
  if (!isOpen) return null;

  const isSuccess = isAnalysis ? result?.would_promote : result?.promoted;
  const Icon = isSuccess ? CheckCircle : result?.reason?.includes('Error') ? XCircle : Info;
  const iconColor = isSuccess ? 'text-green-500' : result?.reason?.includes('Error') ? 'text-red-500' : 'text-yellow-500';
  const bgColor = isSuccess ? 'bg-green-50' : result?.reason?.includes('Error') ? 'bg-red-50' : 'bg-yellow-50';

  const getTitle = () => {
    if (isAnalysis) {
      return result?.would_promote
        ? '📊 Analysis: This Clause is Eligible for Promotion'
        : '📊 Analysis: Cannot Promote Yet';
    }
    return result?.promoted
      ? '✅ Clause Promoted Successfully!'
      : 'ℹ️ Promotion Not Performed';
  };

  const formatReason = () => {
    if (!result?.reason) return 'No reason provided';

    // In analysis mode, replace "Auto-promoted" with more appropriate text
    if (isAnalysis && result?.would_promote) {
      return result.reason.replace('Auto-promoted:', '✅ This clause qualifies because:');
    }

    return result.reason;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-md w-full mx-4">
        {/* Header */}
        <div className={`${bgColor} px-6 py-4 rounded-t-lg flex items-center justify-between border-b`}>
          <div className="flex items-center gap-3">
            <Icon className={`w-6 h-6 ${iconColor}`} />
            <h2 className="text-lg font-bold text-gray-800">{getTitle()}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          {/* Reason */}
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-600 mb-2">
              {isAnalysis && result?.would_promote ? 'Why it qualifies:' : 'Reason:'}
            </p>
            <p className="text-gray-800 bg-gray-50 p-3 rounded border border-gray-200">
              {formatReason()}
            </p>
          </div>

          {/* Metrics */}
          {result?.best_version?.metrics && (
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-blue-50 p-3 rounded border border-blue-200">
                <p className="text-xs text-blue-600 font-medium mb-1">Health Score</p>
                <p className="text-xl font-bold text-blue-800">
                  {(result.best_version.metrics.health_score * 100).toFixed(0)}%
                </p>
              </div>
              <div className="bg-green-50 p-3 rounded border border-green-200">
                <p className="text-xs text-green-600 font-medium mb-1">Success Rate</p>
                <p className="text-xl font-bold text-green-800">
                  {(result.best_version.metrics.success_rate * 100).toFixed(0)}%
                </p>
              </div>
              <div className="bg-purple-50 p-3 rounded border border-purple-200">
                <p className="text-xs text-purple-600 font-medium mb-1">Usage Count</p>
                <p className="text-xl font-bold text-purple-800">
                  {result.best_version.event_count || 0}
                </p>
              </div>
              <div className="bg-orange-50 p-3 rounded border border-orange-200">
                <p className="text-xs text-orange-600 font-medium mb-1">Enforceability</p>
                <p className="text-xl font-bold text-orange-800">
                  {(result.best_version.metrics.enforceability_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          )}

          {/* Analysis Mode Notice */}
          {isAnalysis && result?.would_promote && (
            <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4 mb-4">
              <div className="flex items-start gap-2">
                <span className="text-2xl">💡</span>
                <div>
                  <p className="text-sm text-blue-900 font-semibold mb-1">Analysis Mode - No Changes Made</p>
                  <p className="text-xs text-blue-800">
                    This clause meets all promotion criteria. To officially mark it as "Auto-Promoted",
                    click the <span className="font-bold bg-blue-200 px-1 rounded">Promote</span> button instead.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Cannot Promote Info */}
          {!isSuccess && !result?.reason?.includes('Error') && (
            <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-r-lg p-4">
              <div className="flex items-start gap-2">
                <span className="text-2xl">ℹ️</span>
                <div>
                  <p className="text-sm text-yellow-900 font-semibold mb-1">
                    {isAnalysis ? 'Not Ready for Promotion' : 'Promotion Blocked'}
                  </p>
                  <p className="text-xs text-yellow-800">
                    This clause doesn't meet the promotion criteria yet. To improve:
                  </p>
                  <ul className="text-xs text-yellow-800 mt-2 space-y-1 list-disc list-inside">
                    <li>Ensure health score is above 75%</li>
                    <li>Record more successful contract executions</li>
                    <li>Maintain high success rate (80%+)</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-lg border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
};

export default PromotionModal;
