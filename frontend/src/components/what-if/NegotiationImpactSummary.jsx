import { Scale, ArrowRight, TrendingDown, TrendingUp } from 'lucide-react';
import useThemeStore from '../../store/themeStore';

/**
 * Negotiation Priority Impact Summary
 * Shows how negotiation priorities shift after clause removal
 */
export default function NegotiationImpactSummary({ negotiation, delta }) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  if (!negotiation) return null;

  const { before, after, priority_shifts } = negotiation;

  const getPriorityColor = (priority) => {
    if (priority === 'HIGH') return 'text-red-600 bg-red-100';
    if (priority === 'MEDIUM') return 'text-orange-600 bg-orange-100';
    return 'text-green-600 bg-green-100';
  };

  const getPriorityDarkColor = (priority) => {
    if (priority === 'HIGH') return 'text-red-400 bg-red-900 bg-opacity-50';
    if (priority === 'MEDIUM') return 'text-orange-400 bg-orange-900 bg-opacity-50';
    return 'text-green-400 bg-green-900 bg-opacity-50';
  };

  return (
    <div className={`rounded-lg shadow-lg p-6 mb-6 ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
    }`}>
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <div className={`p-2 rounded-lg ${
          theme === 'dark' ? 'bg-orange-900 bg-opacity-50' : 'bg-orange-100'
        }`}>
          <Scale className="w-6 h-6 text-orange-600" />
        </div>
        <div>
          <h3 className={`text-lg font-bold ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            Negotiation Impact Summary
          </h3>
          <p className={`text-sm ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            How negotiation priorities shift after removal
          </p>
        </div>
      </div>

      {/* Impact Statement */}
      {delta && (
        <div className={`p-4 rounded-lg mb-6 ${
          theme === 'dark'
            ? 'bg-blue-900 bg-opacity-30 border border-blue-800'
            : 'bg-blue-50 border border-blue-200'
        }`}>
          <p className={`text-sm ${
            theme === 'dark' ? 'text-blue-300' : 'text-blue-800'
          }`}>
            Removing this clause reduces cascading contractual risk by{' '}
            <span className="font-bold">
              {delta.risk_reduction_pct?.toFixed(1) || 0}%
            </span>.
            {delta.risk_reduction > 0.1 && (
              <span>
                {' '}This clause materially amplifies exposure through interactions with
                termination, payment, and liability provisions.
              </span>
            )}
          </p>
        </div>
      )}

      {/* Priority Shifts */}
      {priority_shifts && priority_shifts.length > 0 && (
        <div className="mb-6">
          <h4 className={`text-sm font-semibold mb-3 ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Priority Shifts ({priority_shifts.length})
          </h4>
          <div className="space-y-2">
            {priority_shifts.map((shift, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg flex items-center justify-between ${
                  theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                }`}
              >
                <span className={`text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Clause #{shift.clause_id?.substring(0, 8)}...
                </span>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-xs font-bold ${
                    theme === 'dark'
                      ? getPriorityDarkColor(shift.priority_before)
                      : getPriorityColor(shift.priority_before)
                  }`}>
                    {shift.priority_before}
                  </span>
                  <ArrowRight className={`w-4 h-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                  }`} />
                  <span className={`px-2 py-1 rounded text-xs font-bold ${
                    theme === 'dark'
                      ? getPriorityDarkColor(shift.priority_after)
                      : getPriorityColor(shift.priority_after)
                  }`}>
                    {shift.priority_after}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Before/After Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Before */}
        <div>
          <h4 className={`text-sm font-semibold mb-3 flex items-center space-x-2 ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            <span>High Priority - Before</span>
            <span className={`px-2 py-0.5 rounded text-xs ${
              theme === 'dark' ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600'
            }`}>
              {(before || []).filter(a => a.priority === 'HIGH').length}
            </span>
          </h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {(before || [])
              .filter(a => a.priority === 'HIGH')
              .slice(0, 5)
              .map((item, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded text-sm ${
                    theme === 'dark'
                      ? 'bg-red-900 bg-opacity-30 border border-red-800'
                      : 'bg-red-50 border border-red-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                      {item.clause_type || 'Unknown'}
                    </span>
                    <span className="text-red-600 font-medium text-xs">
                      {item.priority_score?.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            {(before || []).filter(a => a.priority === 'HIGH').length === 0 && (
              <p className={`text-sm italic ${
                theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
              }`}>
                No high priority clauses
              </p>
            )}
          </div>
        </div>

        {/* After */}
        <div>
          <h4 className={`text-sm font-semibold mb-3 flex items-center space-x-2 ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            <span>High Priority - After</span>
            <span className={`px-2 py-0.5 rounded text-xs ${
              theme === 'dark' ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600'
            }`}>
              {(after || []).filter(a => a.priority === 'HIGH').length}
            </span>
          </h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {(after || [])
              .filter(a => a.priority === 'HIGH')
              .slice(0, 5)
              .map((item, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded text-sm ${
                    theme === 'dark'
                      ? 'bg-red-900 bg-opacity-30 border border-red-800'
                      : 'bg-red-50 border border-red-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                      {item.clause_type || 'Unknown'}
                    </span>
                    <span className="text-red-600 font-medium text-xs">
                      {item.priority_score?.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            {(after || []).filter(a => a.priority === 'HIGH').length === 0 && (
              <p className={`text-sm italic ${
                theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
              }`}>
                No high priority clauses
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
