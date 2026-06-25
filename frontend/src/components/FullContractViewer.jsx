import { useState } from 'react';
import { X, Download, Copy } from 'lucide-react';

/**
 * FullContractViewer - Display complete contract text with all clause spans highlighted
 * Shows which parts of the contract belong to which extracted clauses
 */
export default function FullContractViewer({ fullText, clauses, onClose }) {
  const [selectedClauseIds, setSelectedClauseIds] = useState(
    clauses.filter(c => c.found).map(c => c.id)
  );
  const [highlightColors] = useState({
    default: 'bg-yellow-200/40 text-yellow-900',
    high: 'bg-green-200/40 text-green-900',
    medium: 'bg-blue-200/40 text-blue-900',
    low: 'bg-red-200/40 text-red-900'
  });

  if (!fullText) {
    return null;
  }

  // Build a map of all text spans with their clause information
  const buildSpanMap = () => {
    const spanMap = new Map(); // position -> {text, clauseName, confidence, clauseId}

    clauses.forEach(clause => {
      if (!clause.found || !clause.textSpans) return;

      clause.textSpans.forEach(span => {
        const lowerText = fullText.toLowerCase();
        const lowerSpan = span.text.toLowerCase();

        // Find all occurrences
        let searchPos = 0;
        while (true) {
          const pos = lowerText.indexOf(lowerSpan, searchPos);
          if (pos === -1) break;

          const key = `${pos}-${pos + span.text.length}`;
          if (!spanMap.has(key)) {
            spanMap.set(key, {
              text: fullText.substring(pos, pos + span.text.length),
              clauseName: clause.clauseName,
              confidence: clause.confidence,
              clauseId: clause.id,
              startPos: pos,
              endPos: pos + span.text.length
            });
          }

          searchPos = pos + 1;
        }
      });
    });

    return spanMap;
  };

  const spanMap = buildSpanMap();

  // Get color based on confidence
  const getHighlightClass = (confidence) => {
    if (confidence >= 75) return 'bg-green-300/50 text-green-900 font-semibold';
    if (confidence >= 50) return 'bg-yellow-300/40 text-yellow-900 font-medium';
    return 'bg-orange-300/30 text-orange-900';
  };

  // Render text with highlights
  const renderHighlightedText = () => {
    if (spanMap.size === 0) {
      return <p className="text-slate-400 text-sm">No spans found to highlight</p>;
    }

    const sortedSpans = Array.from(spanMap.values()).sort((a, b) => a.startPos - b.startPos);

    const elements = [];
    let lastPos = 0;

    sortedSpans.forEach((span, idx) => {
      // Only show if clause is selected
      if (!selectedClauseIds.includes(span.clauseId)) {
        return;
      }

      // Add text before this span
      if (span.startPos > lastPos) {
        elements.push(
          <span key={`text-${lastPos}`} className="text-slate-700">
            {fullText.substring(lastPos, span.startPos)}
          </span>
        );
      }

      // Add the highlighted span
      elements.push(
        <span
          key={`span-${idx}`}
          className={`${getHighlightClass(span.confidence)} px-1 rounded cursor-help transition hover:ring-2 hover:ring-offset-1 ring-slate-400`}
          title={`${span.clauseName} (${span.confidence.toFixed(1)}% confidence)`}
        >
          {span.text}
        </span>
      );

      lastPos = span.endPos;
    });

    // Add remaining text
    if (lastPos < fullText.length) {
      elements.push(
        <span key={`text-end`} className="text-slate-700">
          {fullText.substring(lastPos)}
        </span>
      );
    }

    return elements;
  };

  const handleCopyText = () => {
    navigator.clipboard.writeText(fullText);
  };

  const toggleClauseVisibility = (clauseId) => {
    setSelectedClauseIds(prev =>
      prev.includes(clauseId)
        ? prev.filter(id => id !== clauseId)
        : [...prev, clauseId]
    );
  };

  const foundClauses = clauses.filter(c => c.found);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center overflow-auto p-4">
      <div className="bg-slate-900 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col border border-slate-800">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 flex-shrink-0">
          <h2 className="text-2xl font-bold text-white">Full Contract Text</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition text-slate-400 hover:text-white"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Controls */}
        <div className="border-b border-slate-800 p-4 space-y-4 flex-shrink-0">
          {/* Legend */}
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase mb-3 tracking-wide">
              Highlight Legend:
            </p>
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-green-300/50 rounded border border-slate-600"></div>
                <span className="text-xs text-slate-300">High Confidence (≥75%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-yellow-300/40 rounded border border-slate-600"></div>
                <span className="text-xs text-slate-300">Medium Confidence (50-75%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-orange-300/30 rounded border border-slate-600"></div>
                <span className="text-xs text-slate-300">Low Confidence (&lt;50%)</span>
              </div>
            </div>
          </div>

          {/* Clause Filter */}
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase mb-2 tracking-wide">
              Show Clauses ({selectedClauseIds.length}/{foundClauses.length}):
            </p>
            <div className="flex flex-wrap gap-2">
              {foundClauses.map(clause => (
                <button
                  key={clause.id}
                  onClick={() => toggleClauseVisibility(clause.id)}
                  className={`px-3 py-1 rounded text-xs font-medium transition ${
                    selectedClauseIds.includes(clause.id)
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-400 opacity-50'
                  }`}
                >
                  {clause.clauseName}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleCopyText}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition text-sm font-medium"
            >
              <Copy className="w-4 h-4" />
              Copy All Text
            </button>
          </div>
        </div>

        {/* Full Text Display */}
        <div className="flex-1 overflow-auto p-6 bg-slate-950">
          <div className="bg-white rounded-lg p-6 shadow-lg">
            <div className="text-sm leading-relaxed whitespace-pre-wrap break-words font-sans text-slate-900">
              {renderHighlightedText()}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 p-4 flex items-center justify-between flex-shrink-0 bg-slate-800/50">
          <p className="text-xs text-slate-400">
            {fullText.length} characters | {Math.round(fullText.length / 4.7)} words
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-medium text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
