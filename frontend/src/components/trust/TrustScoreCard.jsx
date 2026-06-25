import React from 'react';
import TrustBadge from './TrustBadge';

/**
 * Trust Score Card Component
 * Displays overall trust score with grade and visual indicator
 */
const TrustScoreCard = ({ trustData }) => {
  const {
    trust_score,
    trust_level,
    trust_grade,
    color,
    badge,
    badge_label,
    badge_color,
    badge_icon,
    badge_description
  } = trustData;

  // Calculate rotation for arc (0-180 degrees)
  const rotation = (trust_score || 0.5) * 180;

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">Clause Trust Score</h3>

        {/* Circular Trust Score */}
        <div className="relative w-40 h-40 mx-auto mb-4">
          <svg className="w-full h-full transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="80"
              cy="80"
              r="70"
              fill="none"
              stroke="#374151"
              strokeWidth="12"
            />
            {/* Colored arc */}
            <circle
              cx="80"
              cy="80"
              r="70"
              fill="none"
              stroke={color || '#6b7280'}
              strokeWidth="12"
              strokeDasharray={`${(trust_score || 0) * 439.8} 439.8`}
              strokeLinecap="round"
              style={{ transition: 'stroke-dasharray 1s ease-in-out' }}
            />
          </svg>

          {/* Score text in center */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-4xl font-bold" style={{ color: color || '#6b7280' }}>
              {((trust_score || 0) * 100).toFixed(0)}
            </div>
            <div className="text-xs text-gray-400 mt-1">Trust Score</div>
          </div>
        </div>

        {/* Grade and Level */}
        <div className="flex justify-center gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold" style={{ color: color }}>
              {trust_grade || 'N/A'}
            </div>
            <div className="text-xs text-gray-400">Grade</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-semibold text-gray-300">
              {trust_level || 'UNTESTED'}
            </div>
            <div className="text-xs text-gray-400">Level</div>
          </div>
        </div>

        {/* Badge */}
        {badge && (
          <div className="flex justify-center">
            <TrustBadge
              badge={badge}
              label={badge_label}
              color={badge_color}
              icon={badge_icon}
              description={badge_description}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default TrustScoreCard;
