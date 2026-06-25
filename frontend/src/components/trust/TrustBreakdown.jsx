import React from 'react';

/**
 * Trust Breakdown Component
 * Shows detailed breakdown of trust score components with weights
 */
const TrustBreakdown = ({ breakdown }) => {
  if (!breakdown || !breakdown.components) {
    return null;
  }

  const components = [
    {
      key: 'enforceability',
      label: 'Enforceability',
      description: 'Court enforceability based on litigation outcomes',
      icon: '⚖️'
    },
    {
      key: 'negotiability',
      label: 'Negotiability',
      description: 'Deal closure success rate',
      icon: '🤝'
    },
    {
      key: 'clarity',
      label: 'Clarity',
      description: 'Legal clarity (inverse of ambiguity)',
      icon: '✨'
    },
    {
      key: 'litigation_survival',
      label: 'Litigation Survival',
      description: 'Financial survival in litigation',
      icon: '🛡️'
    }
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">Trust Score Breakdown</h3>

      <div className="space-y-4">
        {components.map(({ key, label, description, icon }) => {
          const comp = breakdown.components[key];
          if (!comp) return null;

          const percentage = (comp.score * 100).toFixed(0);
          const contributionPct = (comp.contribution / breakdown.trust_score * 100).toFixed(0);

          return (
            <div key={key} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{icon}</span>
                  <div>
                    <div className="text-sm font-medium text-gray-200">{label}</div>
                    <div className="text-xs text-gray-400">{description}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-gray-200">{percentage}%</div>
                  <div className="text-xs text-gray-400">Weight: {(comp.weight * 100)}%</div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: percentage >= 70 ? '#10b981' : percentage >= 50 ? '#f59e0b' : '#ef4444'
                  }}
                />
              </div>

              {/* Contribution */}
              <div className="text-xs text-gray-400">
                Contributes {contributionPct}% to overall trust score
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall Trust Score */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-200">Overall Trust Score</span>
          <span className="text-lg font-bold" style={{ color: breakdown.color }}>
            {(breakdown.trust_score * 100).toFixed(0)}% ({breakdown.trust_grade})
          </span>
        </div>
      </div>
    </div>
  );
};

export default TrustBreakdown;
