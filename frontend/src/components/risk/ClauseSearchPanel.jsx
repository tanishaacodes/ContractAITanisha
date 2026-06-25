/**
 * Clause Search Panel (BM25 + BERT)
 * ==================================
 * Hybrid semantic + lexical search interface
 */

import React, { useState } from 'react';
import { Search, Sparkles, FileText } from 'lucide-react';
import { searchSimilarClauses } from '../../services/riskIntelligence';

export default function ClauseSearchPanel({ contractId }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const data = await searchSimilarClauses({
        query_text: query,
        contract_id: contractId,
        top_k: 10
      });

      setResults(data.results || []);
    } catch (err) {
      console.error('Search failed:', err);
      setError(err.response?.data?.error || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getMethodBadge = (method) => {
    const badges = {
      hybrid: { label: 'Hybrid', color: 'bg-purple-900/30 text-purple-300 border-purple-700' },
      lexical: { label: 'BM25', color: 'bg-blue-900/30 text-blue-300 border-blue-700' },
      semantic: { label: 'BERT', color: 'bg-green-900/30 text-green-300 border-green-700' }
    };
    return badges[method] || badges.hybrid;
  };

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Sparkles className="text-purple-400 mr-3" size={24} />
          <div>
            <h3 className="text-lg font-semibold text-white">Hybrid Clause Search</h3>
            <p className="text-sm text-gray-400">BM25 (lexical) + BERT (semantic) fusion</p>
          </div>
        </div>

        <div className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search for clauses (e.g., 'indemnification obligations')"
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 transition"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition flex items-center"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Searching...
              </>
            ) : (
              <>
                <Search size={18} className="mr-2" />
                Search
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-300">{error}</p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-white">
            Results ({results.length})
          </h3>

          <div className="space-y-4">
            {results.map((result, idx) => {
              const doc = result.document || {};
              const badge = getMethodBadge(result.retrieval_method);

              return (
                <div
                  key={idx}
                  className="bg-gray-700 border border-gray-600 rounded-lg p-4 hover:border-purple-500 transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center">
                      <FileText className="text-purple-400 mr-2" size={18} />
                      <span className="font-medium text-white">
                        {doc.clause_name || 'Unnamed Clause'}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs border ${badge.color}`}>
                        {badge.label}
                      </span>
                      <span className="text-sm text-gray-400">
                        Score: {(result.fusion_score * 100).toFixed(0)}
                      </span>
                    </div>
                  </div>

                  <p className="text-sm text-gray-300 mb-3 line-clamp-2">
                    {doc.text || 'No text available'}
                  </p>

                  <div className="flex items-center space-x-4 text-xs text-gray-400">
                    <span>Type: {doc.clause_type || 'N/A'}</span>
                    {doc.risk_score !== undefined && (
                      <span>Risk: {(doc.risk_score * 100).toFixed(0)}%</span>
                    )}
                    {result.bm25_score > 0 && (
                      <span>BM25: {result.bm25_score.toFixed(2)}</span>
                    )}
                    {result.bert_score > 0 && (
                      <span>BERT: {result.bert_score.toFixed(2)}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && results.length === 0 && query && (
        <div className="text-center py-12">
          <Search className="mx-auto text-gray-600 mb-4" size={48} />
          <p className="text-gray-400">No results found</p>
        </div>
      )}
    </div>
  );
}
