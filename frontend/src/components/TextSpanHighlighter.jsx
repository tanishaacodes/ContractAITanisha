import { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Copy, Check } from 'lucide-react';

/**
 * TextSpanHighlighter - Highlights extracted text spans in the full contract text
 * Shows where in the contract each clause's key terms were found
 */
export default function TextSpanHighlighter({ fullText, clause, allClauses }) {
  const [currentSpanIndex, setCurrentSpanIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!clause?.textSpans || clause.textSpans.length === 0) {
    return (
      <div className="bg-slate-800/50 rounded-lg p-4 text-slate-400 text-sm">
        No specific text spans found for this clause
      </div>
    );
  }

  const spans = clause.textSpans;
  const currentSpan = spans[currentSpanIndex];

  // Find the span in the full text and extract context
  const getSpanContext = (text, spanText, contextLength = 150) => {
    const lowerText = text.toLowerCase();
    const lowerSpan = spanText.toLowerCase();

    // Find the position of this span
    const positions = [];
    let searchPos = 0;

    while (true) {
      const pos = lowerText.indexOf(lowerSpan, searchPos);
      if (pos === -1) break;
      positions.push(pos);
      searchPos = pos + 1;
    }

    if (positions.length === 0) {
      return {
        before: '',
        matched: spanText,
        after: '',
        startIdx: -1,
        endIdx: -1,
        notFound: true
      };
    }

    // Use the current index to cycle through occurrences
    const actualIndex = currentSpanIndex % positions.length;
    const matchPos = positions[actualIndex];
    const endPos = matchPos + spanText.length;

    return {
      before: text.substring(Math.max(0, matchPos - contextLength), matchPos),
      matched: text.substring(matchPos, endPos),
      after: text.substring(endPos, Math.min(text.length, endPos + contextLength)),
      startIdx: matchPos,
      endIdx: endPos,
      notFound: false,
      occurrences: positions.length,
      currentOccurrence: actualIndex + 1
    };
  };

  const context = useMemo(() => {
    if (!fullText || !currentSpan?.text) {
      return {
        before: '',
        matched: 'Text not found',
        after: '',
        notFound: true
      };
    }
    return getSpanContext(fullText, currentSpan.text);
  }, [fullText, currentSpan, currentSpanIndex]);

  const handleCopySpan = () => {
    navigator.clipboard.writeText(currentSpan.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrevSpan = () => {
    setCurrentSpanIndex((prev) => (prev - 1 + spans.length) % spans.length);
  };

  const handleNextSpan = () => {
    setCurrentSpanIndex((prev) => (prev + 1) % spans.length);
  };

  // Get color for the clause's confidence
  const getConfidenceColor = (confidence) => {
    if (confidence >= 75) return 'bg-green-500/20 border-green-700 text-green-200';
    if (confidence >= 50) return 'bg-yellow-500/20 border-yellow-700 text-yellow-200';
    return 'bg-red-500/20 border-red-700 text-red-200';
  };

  return (
    <div className="space-y-4">
      {/* Span Counter */}
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-300">
          Keyword Match {currentSpanIndex + 1} of {spans.length}
        </p>
        {context.occurrences && context.occurrences > 1 && (
          <p className="text-xs text-slate-400">
            Found {context.occurrences} occurrences in document
          </p>
        )}
      </div>

      {/* Current Span Display */}
      <div className={`border rounded-lg p-4 ${getConfidenceColor(clause.confidence)}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wide">
              Matched Term
            </p>
            <p className="text-base font-mono font-bold break-words">
              "{currentSpan.text}"
            </p>
          </div>
          <button
            onClick={handleCopySpan}
            className="flex items-center gap-2 px-3 py-2 rounded bg-black/30 hover:bg-black/50 transition text-sm font-medium flex-shrink-0"
            title="Copy matched text"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                Copied
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Context Display */}
      {!context.notFound ? (
        <div className="bg-slate-800/50 rounded-lg p-4 space-y-3">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
            Context in Document
          </p>
          <div className="bg-slate-900 rounded p-3 border border-slate-700">
            <p className="text-sm leading-relaxed text-slate-100">
              {/* Before text */}
              <span className="text-slate-500">
                {context.before}
              </span>
              {/* Highlighted match */}
              <span className="bg-yellow-500/40 text-yellow-50 font-bold px-1 rounded border border-yellow-600/50">
                {context.matched}
              </span>
              {/* After text */}
              <span className="text-slate-500">
                {context.after}
              </span>
            </p>
          </div>
          {context.occurrences && context.occurrences > 1 && (
            <p className="text-xs text-slate-400">
              Occurrence {context.currentOccurrence} of {context.occurrences}
            </p>
          )}
        </div>
      ) : (
        <div className="bg-slate-800/50 rounded-lg p-4 text-slate-400 text-sm">
          <p>⚠️ Text span could not be located in the full contract text</p>
          <p className="text-xs mt-2">This may occur if the text was modified after extraction.</p>
        </div>
      )}

      {/* Navigation */}
      {spans.length > 1 && (
        <div className="flex items-center gap-2 justify-center pt-2">
          <button
            onClick={handlePrevSpan}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition text-slate-300 hover:text-white disabled:opacity-50"
            title="Previous match"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-1">
            {spans.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSpanIndex(idx)}
                className={`w-2 h-2 rounded-full transition ${
                  idx === currentSpanIndex
                    ? 'bg-yellow-500'
                    : 'bg-slate-600 hover:bg-slate-500'
                }`}
                title={`Go to match ${idx + 1}`}
              />
            ))}
          </div>

          <button
            onClick={handleNextSpan}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition text-slate-300 hover:text-white disabled:opacity-50"
            title="Next match"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* All Spans List */}
      <div className="pt-2 border-t border-slate-700">
        <p className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wide">
          All Matched Terms ({spans.length})
        </p>
        <div className="flex flex-wrap gap-2">
          {spans.map((span, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentSpanIndex(idx)}
              className={`px-3 py-1 rounded text-xs font-medium transition ${
                idx === currentSpanIndex
                  ? 'bg-yellow-500 text-slate-900'
                  : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
              }`}
              title={`Show "${span.text}"`}
            >
              {span.text.length > 20 ? span.text.substring(0, 20) + '...' : span.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
