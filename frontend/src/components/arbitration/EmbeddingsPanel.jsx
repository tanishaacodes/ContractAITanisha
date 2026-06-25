/**
 * EmbeddingsPanel.jsx
 * ====================
 * LegalBERT semantic embeddings visualization
 * Shows 768-dim embeddings and clause similarity matrix
 */

import { useState, useEffect } from 'react';
import { Brain, Search, TrendingUp } from 'lucide-react';
import { getArbitrationAnalysis, findSimilarClauses } from '../../services/arbitrationService';

export default function EmbeddingsPanel({ analysisId }) {
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedClause, setSelectedClause] = useState(null);
  const [similarClauses, setSimilarClauses] = useState([]);

  useEffect(() => {
    if (analysisId) {
      loadEmbeddings();
    }
  }, [analysisId]);

  const loadEmbeddings = async () => {
    try {
      setLoading(true);
      const data = await getArbitrationAnalysis(analysisId);
      setClauses(data.clauses || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFindSimilar = async (clauseId) => {
    try {
      const data = await findSimilarClauses(clauseId, 0.7);
      setSimilarClauses(data.similar_clauses || []);
      setSelectedClause(clauseId);

      // Log filtering info if available
      if (data.filtered_duplicates && data.total_found !== undefined) {
        console.log(`Found ${data.total_found} similar clauses (duplicates filtered)`);
      }
    } catch (err) {
      console.error('Failed to find similar clauses:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
        <p className="text-red-400">Failed to load embeddings: {error}</p>
      </div>
    );
  }

  const clausesWithEmbeddings = clauses.filter(c => c.embedding && c.embedding.length > 0);

  if (clausesWithEmbeddings.length === 0) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
        <Brain className="mx-auto mb-4" size={48} color="#4C8EDA" />
        <h3 className="text-lg font-semibold mb-2">No Embeddings Available</h3>
        <p className="text-slate-400 text-sm">
          Embeddings are generated automatically during analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={20} color="#4C8EDA" />
          <h3 className="text-lg font-semibold">LegalBERT Embeddings</h3>
        </div>
        <div className="text-sm text-slate-400">
          {clausesWithEmbeddings.length} clauses × 768 dimensions
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <TrendingUp size={20} className="text-cyan-400 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-cyan-400 mb-1">Semantic Embeddings Active</h4>
            <p className="text-xs text-slate-300">
              Each clause is encoded as a 768-dimensional vector using nlpaueb/legal-bert-base-uncased.
              Click on any clause to find semantically similar clauses across your contracts.
            </p>
          </div>
        </div>
      </div>

      {/* Clauses Grid */}
      <div className="grid gap-3">
        {clausesWithEmbeddings.map((clause) => {
          const embeddingSize = clause.embedding ? clause.embedding.length : 0;
          const isSelected = selectedClause === clause.id;

          return (
            <div
              key={clause.id}
              className={`bg-slate-800/50 border rounded-lg p-4 transition-all ${
                isSelected
                  ? 'border-cyan-500 ring-2 ring-cyan-500/20'
                  : 'border-slate-700 hover:border-slate-600'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-slate-500">Clause {clause.clause_index + 1}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      clause.risk_level === 'HIGH'
                        ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                        : clause.risk_level === 'MEDIUM'
                        ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                        : 'bg-green-500/10 text-green-400 border border-green-500/30'
                    }`}>
                      {clause.risk_level}
                    </span>
                    <span className="text-xs text-slate-500">
                      Risk: {(clause.composite_risk * 100).toFixed(0)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 mb-3">{clause.clause_text}</p>
                  <div className="flex items-center gap-4">
                    <div className="text-xs text-slate-500">
                      Embedding: {embeddingSize}D vector
                    </div>
                    {clause.pattern_hits > 0 && (
                      <div className="text-xs text-slate-500">
                        Patterns: {clause.pattern_hits}
                      </div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleFindSimilar(clause.id)}
                  className="px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded text-xs text-cyan-400 transition-colors flex items-center gap-1.5"
                >
                  <Search size={14} />
                  Find Similar
                </button>
              </div>

              {/* Similar Clauses */}
              {isSelected && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs text-slate-400">
                      Similar Clauses {similarClauses.length > 0 && `(${similarClauses.length} found)`}
                    </div>
                    <div className="text-xs text-slate-500">
                      From different contracts • Duplicates filtered
                    </div>
                  </div>
                  {similarClauses.length === 0 ? (
                    <div className="bg-slate-900/30 border border-slate-700/50 rounded p-4 text-center">
                      <p className="text-xs text-slate-500">
                        No similar clauses found in other contracts
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {similarClauses.map((similar, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-900/50 border border-slate-700 rounded p-3 hover:border-slate-600 transition-colors"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs text-cyan-400 font-medium">
                              {(similar.similarity * 100).toFixed(1)}% match
                            </span>
                            <span className="text-xs text-slate-500">•</span>
                            <span className="text-xs text-slate-400">
                              {similar.contract_name}
                            </span>
                            {similar.analysis_id && (
                              <>
                                <span className="text-xs text-slate-500">•</span>
                                <span className="text-xs text-slate-600">
                                  Analysis {similar.analysis_id.substring(0, 8)}
                                </span>
                              </>
                            )}
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed">
                            {similar.text.length > 200 ? `${similar.text.substring(0, 200)}...` : similar.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Embedding Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-1">Total Clauses</div>
          <div className="text-2xl font-bold text-cyan-400">{clausesWithEmbeddings.length}</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-1">Embedding Model</div>
          <div className="text-sm font-semibold text-slate-300">LegalBERT</div>
          <div className="text-xs text-slate-500">nlpaueb/legal-bert-base-uncased</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <div className="text-xs text-slate-400 mb-1">Vector Size</div>
          <div className="text-2xl font-bold text-cyan-400">768</div>
        </div>
      </div>
    </div>
  );
}
