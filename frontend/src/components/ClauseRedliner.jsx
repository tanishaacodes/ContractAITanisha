import React from 'react';
import useThemeStore from '../store/themeStore';

/**
 * ClauseRedliner Component
 *
 * Displays clause text with color-coded redline markings.
 * Feature 3.2: Clause Viewer + Redlining
 *
 * Redline Color Logic:
 * - ❌ Red Strike: Risky text (REMOVE)
 * - ➕ Green Insert: AI Suggested Text (ADD)
 * - 🟦 Blue: Original retained text (ORIGINAL)
 */

const ClauseRedliner = ({
  originalText,
  suggestedText,
  riskType,
  explanation,
  showDiff = true
}) => {
  const { theme } = useThemeStore();

  // Generate redline segments
  const generateRedlineSegments = () => {
    if (!showDiff || !suggestedText) {
      return [{
        text: originalText,
        type: 'ORIGINAL'
      }];
    }

    // Simple diff: show original as REMOVE and suggested as ADD
    // In production, you'd use a proper diff algorithm
    return [
      {
        text: originalText,
        type: 'REMOVE'
      },
      {
        text: suggestedText,
        type: 'ADD'
      }
    ];
  };

  const segments = generateRedlineSegments();

  // Render a segment based on its type
  const renderSegment = (segment, index) => {
    const { text, type } = segment;

    switch (type) {
      case 'REMOVE':
        return (
          <span
            key={index}
            className="line-through text-red-600 bg-red-50 px-1 py-0.5 rounded"
            title="Risky text - suggested for removal"
          >
            {text}
          </span>
        );

      case 'ADD':
        return (
          <span
            key={index}
            className="bg-green-200 text-green-800 mx-1 px-2 py-0.5 rounded font-medium"
            title="AI-suggested safer clause text"
          >
            {text}
          </span>
        );

      case 'ORIGINAL':
      default:
        return (
          <span key={index} style={{ color: theme.colors.textPrimary }}>
            {text}
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Risk Type Badge */}
      {riskType && (
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
            ⚠️ {riskType}
          </span>
        </div>
      )}

      {/* Clause Text with Redlines */}
      <div
        className="prose max-w-none p-4 rounded-lg border-2"
        style={{
          backgroundColor: theme.colors.surface,
          borderColor: showDiff && suggestedText ? '#fbbf24' : theme.colors.border
        }}
      >
        <div className="leading-relaxed text-base">
          {segments.map((segment, index) => renderSegment(segment, index))}
        </div>
      </div>

      {/* Explanation */}
      {explanation && (
        <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
          <div className="flex items-start gap-2">
            <span className="text-blue-600 text-xl mt-0.5">💡</span>
            <div className="flex-1">
              <h4 className="font-semibold text-blue-900 mb-1">Why This Change?</h4>
              <p className="text-sm text-blue-800">{explanation}</p>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      {showDiff && suggestedText && (
        <div className="flex flex-wrap gap-4 p-3 rounded-lg bg-gray-50 border border-gray-200">
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 bg-red-50 border-2 border-red-600 rounded"></span>
            <span className="text-sm text-gray-700">
              <span className="line-through">Strikethrough</span> = Remove (risky)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-4 bg-green-200 border-2 border-green-600 rounded"></span>
            <span className="text-sm text-gray-700">
              <span className="bg-green-200 px-1 rounded">Highlighted</span> = Add (safer)
            </span>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors"
          onClick={() => {
            // In production, this would trigger accept logic
            console.log('Accept suggested changes');
          }}
        >
          ✓ Accept Suggestion
        </button>
        <button
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
          onClick={() => {
            // In production, this would trigger manual edit
            console.log('Edit manually');
          }}
        >
          ✏️ Edit Manually
        </button>
        <button
          className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg font-medium transition-colors"
          onClick={() => {
            // In production, this would trigger reject logic
            console.log('Reject suggestion');
          }}
        >
          ✗ Keep Original
        </button>
      </div>
    </div>
  );
};

/**
 * Advanced Redliner with Word-Level Diff
 *
 * For more sophisticated redlining, use this component.
 * It breaks down text word-by-word for precise highlighting.
 */
export const AdvancedClauseRedliner = ({ redlineSegments }) => {
  const { theme } = useThemeStore();

  if (!redlineSegments || redlineSegments.length === 0) {
    return <p className="text-gray-500">No redline data available</p>;
  }

  return (
    <div className="prose max-w-none p-4 rounded-lg" style={{ backgroundColor: theme.colors.surface }}>
      <div className="leading-relaxed text-base">
        {redlineSegments.map((segment, index) => {
          const { text, type } = segment;

          if (type === 'REMOVE') {
            return (
              <span
                key={index}
                className="line-through text-red-600 bg-red-50 px-0.5"
                title="Suggested for removal"
              >
                {text}
              </span>
            );
          }

          if (type === 'ADD') {
            return (
              <span
                key={index}
                className="bg-green-200 text-green-800 mx-0.5 px-1 rounded"
                title="Suggested addition"
              >
                {text}
              </span>
            );
          }

          // ORIGINAL
          return (
            <span key={index} style={{ color: theme.colors.textPrimary }}>
              {text}
            </span>
          );
        })}
      </div>
    </div>
  );
};

export default ClauseRedliner;
