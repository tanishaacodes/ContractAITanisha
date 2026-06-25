import React, { useState } from "react";
import { CheckCircle, XCircle, AlertTriangle, Lightbulb, Target, ChevronDown, ChevronUp } from "lucide-react";
import useThemeStore from "../store/themeStore";

const SuggestionCard = ({ suggestion, onAccept, onReject }) => {
  const { theme } = useThemeStore();
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAccept = async () => {
    setLoading(true);
    await onAccept(suggestion.id);
    setLoading(false);
  };

  const handleReject = async () => {
    setLoading(true);
    await onReject(suggestion.id);
    setLoading(false);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "HIGH":
        return "text-red-400 bg-red-900/30 border-red-700";
      case "MEDIUM":
        return "text-yellow-400 bg-yellow-900/30 border-yellow-700";
      case "LOW":
        return "text-blue-400 bg-blue-900/30 border-blue-700";
      default:
        return "text-gray-400 bg-gray-900/30 border-gray-700";
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case "RISK_REDUCTION":
        return <AlertTriangle className="w-4 h-4" />;
      case "FAVORABLE_TERMS":
        return <Target className="w-4 h-4" />;
      case "CLARITY_IMPROVEMENT":
        return <Lightbulb className="w-4 h-4" />;
      default:
        return <CheckCircle className="w-4 h-4" />;
    }
  };

  const getCategoryLabel = (category) => {
    return category.split("_").map(w => w.charAt(0) + w.slice(1).toLowerCase()).join(" ");
  };

  const isPending = suggestion.status === "PENDING";

  return (
    <div className={`${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg p-4 hover:opacity-95 transition-colors`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold border ${getPriorityColor(suggestion.priority)}`}>
            {getCategoryIcon(suggestion.category)}
            {getCategoryLabel(suggestion.category)}
          </span>
          <span className={`text-xs ${theme.colors.textSecondary}`}>
            {(suggestion.confidenceScore * 100).toFixed(0)}% confidence
          </span>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-semibold ${
          suggestion.status === "ACCEPTED" ? "bg-green-900/30 text-green-400 border border-green-700" :
          suggestion.status === "REJECTED" ? "bg-red-900/30 text-red-400 border border-red-700" :
          `${theme.colors.surfaceBorder} ${theme.colors.textSecondary} border ${theme.colors.surfaceBorder}`
        }`}>
          {suggestion.status}
        </span>
      </div>

      {/* Rationale */}
      <p className={`${theme.colors.textSecondary} text-sm mb-3 italic`}>
        "{suggestion.rationale}"
      </p>

      {/* Suggested Text */}
      <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded p-3 mb-3`}>
        <div className={`text-xs font-semibold ${theme.colors.textSecondary} mb-1`}>Suggested Rewrite:</div>
        <p className={`${theme.colors.textPrimary} text-sm leading-relaxed`}>{suggestion.suggestedText}</p>
      </div>

      {/* Expandable Details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-blue-400 hover:text-blue-300 text-xs font-semibold flex items-center gap-1 mb-2"
      >
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        {expanded ? "Hide Details" : "Show Details"}
      </button>

      {expanded && (
        <div className={`space-y-3 mb-3 pl-3 border-l-2 ${theme.colors.surfaceBorder}`}>
          {/* Original Text */}
          <div>
            <div className={`text-xs font-semibold ${theme.colors.textSecondary} mb-1`}>Original Text:</div>
            <p className={`${theme.colors.textSecondary} text-sm ${theme.colors.surface} p-2 rounded`}>{suggestion.originalText}</p>
          </div>

          {/* Impact Analysis */}
          {suggestion.impactAnalysis && (
            <div>
              <div className={`text-xs font-semibold ${theme.colors.textSecondary} mb-1`}>Impact Analysis:</div>
              <p className={`${theme.colors.textSecondary} text-sm`}>{suggestion.impactAnalysis}</p>
            </div>
          )}

          {/* Negotiation Tips */}
          {suggestion.negotiationTips && (
            <div>
              <div className="text-xs font-semibold text-blue-400 mb-1 flex items-center gap-1">
                <Lightbulb className="w-3 h-3" />
                Negotiation Tips:
              </div>
              <p className={`${theme.colors.textSecondary} text-sm italic`}>{suggestion.negotiationTips}</p>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {isPending && (
        <div className={`flex gap-2 pt-3 border-t ${theme.colors.surfaceBorder}`}>
          <button
            onClick={handleAccept}
            disabled={loading}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white px-4 py-2 rounded font-semibold text-sm flex items-center justify-center gap-2 transition-colors"
          >
            <CheckCircle className="w-4 h-4" />
            {loading ? "Processing..." : "Accept"}
          </button>
          <button
            onClick={handleReject}
            disabled={loading}
            className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 text-white px-4 py-2 rounded font-semibold text-sm flex items-center justify-center gap-2 transition-colors"
          >
            <XCircle className="w-4 h-4" />
            {loading ? "Processing..." : "Reject"}
          </button>
        </div>
      )}

      {/* Review Info */}
      {!isPending && suggestion.reviewedBy && (
        <div className={`text-xs ${theme.colors.textSecondary} pt-2 border-t ${theme.colors.surfaceBorder}`}>
          {suggestion.status} by {suggestion.reviewedBy}
        </div>
      )}
    </div>
  );
};

export default SuggestionCard;
