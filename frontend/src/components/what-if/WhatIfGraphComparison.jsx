import { ArrowRight, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';
import useThemeStore from '../../store/themeStore';

/**
 * Side-by-side comparison of Before vs After risk timelines
 */
export default function WhatIfGraphComparison({ timeline }) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  if (!timeline || !timeline.before || !timeline.after) return null;

  const before = timeline.before;
  const after = timeline.after;

  const getRiskColor = (score) => {
    if (score >= 0.7) return 'text-red-600';
    if (score >= 0.5) return 'text-orange-600';
    if (score >= 0.3) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRiskBg = (score) => {
    if (score >= 0.7) return theme === 'dark' ? 'bg-red-900 bg-opacity-40' : 'bg-red-50';
    if (score >= 0.5) return theme === 'dark' ? 'bg-orange-900 bg-opacity-40' : 'bg-orange-50';
    if (score >= 0.3) return theme === 'dark' ? 'bg-yellow-900 bg-opacity-40' : 'bg-yellow-50';
    return theme === 'dark' ? 'bg-green-900 bg-opacity-40' : 'bg-green-50';
  };

  const renderTimeline = (data, title, isAfter = false) => {
    const steps = data.timeline || [];
    const hotspots = data.hotspots || [];

    return (
      <div className={`rounded-lg shadow p-4 ${
        theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
      }`}>
        <div className="flex items-center space-x-2 mb-4">
          {isAfter ? (
            <CheckCircle className="w-5 h-5 text-green-500" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-orange-500" />
          )}
          <h4 className={`font-semibold ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            {title}
          </h4>
        </div>

        {/* Total Risk */}
        <div className={`p-3 rounded-lg mb-4 ${getRiskBg(data.total_risk || 0)}`}>
          <div className="flex items-center justify-between">
            <span className={`text-sm font-medium ${
              theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              Total Risk Score
            </span>
            <span className={`text-xl font-bold ${getRiskColor(data.total_risk || 0)}`}>
              {(data.total_risk || 0).toFixed(3)}
            </span>
          </div>
        </div>

        {/* Propagation Steps */}
        <div className="mb-4">
          <p className={`text-sm font-medium mb-2 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Propagation Steps: {data.propagation_steps || 0}
          </p>
        </div>

        {/* Hotspots */}
        <div>
          <p className={`text-sm font-medium mb-2 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Risk Hotspots ({hotspots.length})
          </p>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {hotspots.length > 0 ? (
              hotspots.map((hotspot, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded text-sm ${
                    theme === 'dark'
                      ? 'bg-gray-700 border border-gray-600'
                      : 'bg-gray-50 border border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
                      {hotspot.clause_type || 'Clause'}
                    </span>
                    <span className={`font-bold ${getRiskColor(hotspot.total_risk || 0)}`}>
                      {(hotspot.total_risk || 0).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className={`text-sm italic ${
                theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
              }`}>
                No hotspots detected
              </p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="mb-6">
      <h3 className={`text-lg font-semibold mb-4 ${
        theme === 'dark' ? 'text-white' : 'text-gray-900'
      }`}>
        Risk Propagation Comparison
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
        {/* Before */}
        <div>
          {renderTimeline(before, 'Before - Current Contract', false)}
        </div>

        {/* Arrow */}
        <div className="flex justify-center">
          <div className={`p-4 rounded-full ${
            theme === 'dark' ? 'bg-blue-900 bg-opacity-50' : 'bg-blue-100'
          }`}>
            <ArrowRight className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        {/* After */}
        <div>
          {renderTimeline(after, 'After - Clause Removed', true)}
        </div>
      </div>
    </div>
  );
}
