import React from 'react';
import useThemeStore from '../store/themeStore';

/**
 * ExplainabilityDrawer Component
 *
 * Provides AI transparency and explainability for contract analysis.
 * Feature 3.3: Explainability for court-defensible AI decisions
 *
 * Shows:
 * - Why a clause was flagged
 * - Similarity scores (MiniLM-based)
 * - Industry benchmark comparisons
 * - Court precedent reasoning
 * - Suggested negotiation text
 */

const ExplainabilityDrawer = ({ insight, isOpen, onClose }) => {
  const { theme } = useThemeStore();

  if (!isOpen) {
    return null;
  }

  // Extract insight data
  const {
    clauseType,
    reason,
    similarity,
    goldStandardSimilarity,
    industryBenchmarkSimilarity,
    standardClause,
    industryStandard,
    benchmarkSource,
    suggestion,
    courtPrecedent,
    riskType,
    explanation,
    legalNotes,
    jurisdiction,
    analysisMethod = 'embedding-based (deterministic)',
    confidenceLevel,
    suggestedAction
  } = insight || {};

  // Determine similarity color
  const getSimilarityColor = (score) => {
    if (score >= 0.90) return 'text-green-600';
    if (score >= 0.75) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Format percentage
  const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className="fixed right-0 top-0 h-full w-full md:w-[650px] lg:w-[750px] z-50 shadow-2xl transform transition-transform overflow-y-auto bg-white"
      >
        {/* Header */}
        <div className="sticky top-0 z-10 px-8 py-6 border-b-2 border-gray-300 flex items-center justify-between bg-gradient-to-r from-blue-600 to-blue-700"
        >
          <div>
            <h3 className="text-3xl font-bold text-white">
              AI Explainability
            </h3>
            {clauseType && (
              <p className="text-base mt-2 text-blue-100">
                {clauseType}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-blue-800 transition-colors"
          >
            <span className="text-3xl text-white">×</span>
          </button>
        </div>

        {/* Content */}
        <div className="px-8 py-8 space-y-8">
          {/* Analysis Method Badge */}
          <div className="flex items-center gap-3 p-5 rounded-lg bg-blue-50 border-2 border-blue-200">
            <span className="text-blue-600 text-3xl">🔍</span>
            <div>
              <p className="font-semibold text-blue-900 text-base">Analysis Method</p>
              <p className="text-blue-700 text-base mt-1">{analysisMethod}</p>
              <p className="text-blue-600 text-sm mt-2">
                Deterministic • No hallucinations • Court-defensible
              </p>
            </div>
          </div>

          {/* Why Flagged */}
          {reason && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Why Flagged?
              </h4>
              <div className="p-5 rounded-lg border-2 border-gray-300 bg-gray-50">
                <p className="text-base leading-relaxed text-gray-900">
                  {reason}
                </p>
              </div>
            </div>
          )}

          {/* Explanation */}
          {explanation && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Detailed Explanation
              </h4>
              <div className="p-5 rounded-lg border-2 border-gray-300 bg-gray-50">
                <p className="text-base leading-relaxed text-gray-900">
                  {explanation}
                </p>
              </div>
            </div>
          )}

          {/* Risk Type */}
          {riskType && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Risk Type
              </h4>
              <div className="flex items-center gap-3 p-5 rounded-lg bg-orange-100 border-2 border-orange-400">
                <span className="text-orange-600 text-3xl">⚠️</span>
                <p className="text-orange-900 font-semibold text-lg">{riskType}</p>
              </div>
            </div>
          )}

          {/* Similarity Scores */}
          <div className="space-y-4">
            <h4 className="font-bold text-xl text-gray-900">
              Similarity Scores (MiniLM)
            </h4>

            {/* Overall Similarity */}
            {similarity !== undefined && (
              <div className="p-5 rounded-lg border-2 border-gray-300 bg-white shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-base font-semibold text-gray-900">
                    Overall Similarity
                  </span>
                  <span className={`text-2xl font-bold ${getSimilarityColor(similarity)}`}>
                    {formatPercentage(similarity)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      similarity >= 0.90 ? 'bg-green-500' :
                      similarity >= 0.75 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${similarity * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Gold Standard Similarity */}
            {goldStandardSimilarity !== undefined && (
              <div className="p-5 rounded-lg border-2 border-gray-300 bg-white shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-base font-semibold text-gray-900">
                    vs. Gold Standard
                  </span>
                  <span className={`text-2xl font-bold ${getSimilarityColor(goldStandardSimilarity)}`}>
                    {formatPercentage(goldStandardSimilarity)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      goldStandardSimilarity >= 0.90 ? 'bg-green-500' :
                      goldStandardSimilarity >= 0.75 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${goldStandardSimilarity * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Industry Benchmark Similarity */}
            {industryBenchmarkSimilarity !== undefined && (
              <div className="p-5 rounded-lg border-2 border-gray-300 bg-white shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-base font-semibold text-gray-900">
                    vs. Industry Benchmark
                  </span>
                  <span className={`text-2xl font-bold ${getSimilarityColor(industryBenchmarkSimilarity)}`}>
                    {formatPercentage(industryBenchmarkSimilarity)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      industryBenchmarkSimilarity >= 0.90 ? 'bg-green-500' :
                      industryBenchmarkSimilarity >= 0.75 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${industryBenchmarkSimilarity * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Confidence Level */}
            {confidenceLevel !== undefined && (
              <div className="p-5 rounded-lg border-2 border-gray-300 bg-white shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="text-base font-semibold text-gray-900">
                    Confidence Level
                  </span>
                  <span className={`text-2xl font-bold ${getSimilarityColor(confidenceLevel)}`}>
                    {formatPercentage(confidenceLevel)}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Gold Standard Clause */}
          {standardClause && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Gold Standard Clause
              </h4>
              <div className="p-5 rounded-lg border-l-4 border-green-600 bg-green-100">
                <blockquote className="text-base italic leading-relaxed text-green-900 font-medium">
                  "{standardClause}"
                </blockquote>
              </div>
            </div>
          )}

          {/* Industry Standard */}
          {industryStandard && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Industry Standard
              </h4>
              <div className="p-5 rounded-lg border-l-4 border-blue-600 bg-blue-100">
                <blockquote className="text-base italic leading-relaxed text-blue-900 font-medium">
                  "{industryStandard}"
                </blockquote>
                {benchmarkSource && (
                  <p className="text-sm mt-3 text-blue-900 font-semibold">
                    Source: {benchmarkSource}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Suggested Fix */}
          {suggestion && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Suggested Fix
              </h4>
              <div className="p-5 rounded-lg bg-green-100 border-2 border-green-500">
                <p className="text-base leading-relaxed text-green-900 font-semibold">{suggestion}</p>
              </div>
            </div>
          )}

          {/* Suggested Action */}
          {suggestedAction && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Recommended Action
              </h4>
              <div className="p-5 rounded-lg bg-purple-100 border-2 border-purple-500">
                <p className="text-base leading-relaxed text-purple-900 font-semibold">{suggestedAction}</p>
              </div>
            </div>
          )}

          {/* Court Precedent */}
          {courtPrecedent && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Court Precedent / Legal Notes
              </h4>
              <div className="p-5 rounded-lg border-l-4 border-purple-600 bg-purple-100">
                <p className="text-base leading-relaxed text-purple-900 font-medium">
                  {courtPrecedent}
                </p>
              </div>
            </div>
          )}

          {/* Legal Notes */}
          {legalNotes && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Legal Notes
              </h4>
              <div className="p-5 rounded-lg border-2 border-gray-300 bg-gray-50">
                <p className="text-base leading-relaxed text-gray-900 font-medium">
                  {legalNotes}
                </p>
              </div>
            </div>
          )}

          {/* Jurisdiction */}
          {jurisdiction && (
            <div className="space-y-3">
              <h4 className="font-bold text-xl text-gray-900">
                Jurisdiction
              </h4>
              <div className="p-5 rounded-lg border-2 border-indigo-400 bg-indigo-50">
                <p className="text-lg font-bold text-indigo-900">
                  📍 {jurisdiction}
                </p>
              </div>
            </div>
          )}

          {/* Footer - Why This Matters */}
          <div className="mt-8 p-6 rounded-lg bg-blue-50 border-2 border-blue-400">
            <h5 className="font-bold text-blue-900 mb-3 text-lg">
              🏛️ Court-Defensible AI
            </h5>
            <ul className="text-base text-blue-900 space-y-2 leading-relaxed font-medium">
              <li>• All scores based on cosine similarity (0-1 scale)</li>
              <li>• No generative AI hallucinations</li>
              <li>• Deterministic and reproducible results</li>
              <li>• Traceable to source templates and benchmarks</li>
              <li>• Suitable for legal audit and compliance review</li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
};

export default ExplainabilityDrawer;
