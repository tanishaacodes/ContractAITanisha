import { Activity, Target, AlertTriangle, AlertCircle, TrendingUp } from 'lucide-react';
import useThemeStore from '../../store/themeStore';

/**
 * Monte Carlo Simulation Results Visualization
 * Shows distribution, percentiles, and confidence ranges
 */
export default function MonteCarloVisualization({ monteCarlo }) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  if (!monteCarlo) return null;

  if (monteCarlo.warning) {
    return (
      <div className="flex items-start gap-2 bg-amber-900/30 border border-amber-700 rounded-lg p-4">
        <AlertCircle size={18} className="text-amber-400 mt-0.5 shrink-0" />
        <p className="text-amber-300 text-sm">{monteCarlo.warning}</p>
      </div>
    );
  }

  const before = monteCarlo.before || {};
  const after = monteCarlo.after || {};
  const delta = monteCarlo.delta || {};
  const confidence = monteCarlo.confidence_statement || '';

  const formatAmount = (amount, currency = 'INR') => {
    if (!amount) return '\u20B90';
    const symbol = currency === 'INR' ? '\u20B9' : '$';

    if (currency === 'INR') {
      if (amount >= 10000000) {
        return `${symbol}${(amount / 10000000).toFixed(1)} Cr`;
      } else if (amount >= 100000) {
        return `${symbol}${(amount / 100000).toFixed(1)} L`;
      }
    }
    return `${symbol}${amount.toLocaleString()}`;
  };

  const percentileData = [
    { label: 'P50 (Median)', before: before.p50, after: after.p50 },
    { label: 'P75', before: before.p75, after: after.p75 },
    { label: 'P90', before: before.p90, after: after.p90 },
    { label: 'P95', before: before.p95, after: after.p95 },
    { label: 'P99 (Tail)', before: before.p99, after: after.p99 }
  ];

  return (
    <div className={`rounded-lg shadow-lg p-6 mb-6 ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
    }`}>
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <div className={`p-2 rounded-lg ${
          theme === 'dark' ? 'bg-purple-900 bg-opacity-50' : 'bg-purple-100'
        }`}>
          <Activity className="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <h3 className={`text-lg font-bold ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            Monte Carlo Exposure Analysis
          </h3>
          <p className={`text-sm ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            {monteCarlo.iterations?.toLocaleString() || 5000} iterations
          </p>
        </div>
      </div>

      {/* Confidence Statement */}
      {confidence && (
        <div className={`p-4 rounded-lg mb-6 ${
          theme === 'dark'
            ? 'bg-green-900 bg-opacity-30 border border-green-800'
            : 'bg-green-50 border border-green-200'
        }`}>
          <div className="flex items-start space-x-3">
            <Target className="w-5 h-5 text-green-600 mt-0.5" />
            <p className={`text-sm ${
              theme === 'dark' ? 'text-green-300' : 'text-green-800'
            }`}>
              {confidence}
            </p>
          </div>
        </div>
      )}

      {/* KPI Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className={`p-4 rounded-lg ${
          theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          <p className={`text-xs font-medium mb-1 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            Expected Reduction
          </p>
          <p className="text-xl font-bold text-green-600">
            {formatAmount(delta.mean)}
          </p>
        </div>

        <div className={`p-4 rounded-lg ${
          theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          <p className={`text-xs font-medium mb-1 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            90% Confidence
          </p>
          <p className="text-xl font-bold text-blue-600">
            {formatAmount(delta.p90)}
          </p>
        </div>

        <div className={`p-4 rounded-lg ${
          theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          <p className={`text-xs font-medium mb-1 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            Reduction % (Mean)
          </p>
          <p className="text-xl font-bold text-purple-600">
            {delta.reduction_pct_mean?.toFixed(1) || 0}%
          </p>
        </div>

        <div className={`p-4 rounded-lg ${
          theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          <p className={`text-xs font-medium mb-1 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            Reduction % (P90)
          </p>
          <p className="text-xl font-bold text-indigo-600">
            {delta.reduction_pct_p90?.toFixed(1) || 0}%
          </p>
        </div>
      </div>

      {/* Percentile Comparison Table */}
      <div className="mb-6">
        <h4 className={`text-sm font-semibold mb-3 ${
          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
        }`}>
          Percentile Analysis
        </h4>
        <div className={`overflow-x-auto rounded-lg border ${
          theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <table className="w-full">
            <thead>
              <tr className={theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}>
                  Percentile
                </th>
                <th className={`px-4 py-3 text-right text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}>
                  Before
                </th>
                <th className={`px-4 py-3 text-right text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}>
                  After
                </th>
                <th className={`px-4 py-3 text-right text-sm font-medium ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}>
                  Delta
                </th>
              </tr>
            </thead>
            <tbody>
              {percentileData.map((row, idx) => (
                <tr
                  key={idx}
                  className={`border-t ${
                    theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
                  }`}
                >
                  <td className={`px-4 py-3 text-sm font-medium ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-900'
                  }`}>
                    {row.label}
                  </td>
                  <td className={`px-4 py-3 text-sm text-right ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    {formatAmount(row.before)}
                  </td>
                  <td className={`px-4 py-3 text-sm text-right ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    {formatAmount(row.after)}
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-medium text-green-600">
                    {formatAmount((row.before || 0) - (row.after || 0))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Statistical Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={`p-4 rounded-lg ${
          theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          <h5 className={`text-sm font-semibold mb-2 ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Before Removal
          </h5>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                Mean:
              </span>
              <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}>
                {before.mean_formatted || formatAmount(before.mean)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                Std Dev:
              </span>
              <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}>
                {formatAmount(before.std)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                Range:
              </span>
              <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}>
                {formatAmount(before.min)} - {formatAmount(before.max)}
              </span>
            </div>
          </div>
        </div>

        <div className={`p-4 rounded-lg ${
          theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          <h5 className={`text-sm font-semibold mb-2 ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            After Removal
          </h5>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                Mean:
              </span>
              <span className="text-green-600 font-medium">
                {after.mean_formatted || formatAmount(after.mean)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                Std Dev:
              </span>
              <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}>
                {formatAmount(after.std)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}>
                Range:
              </span>
              <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}>
                {formatAmount(after.min)} - {formatAmount(after.max)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
