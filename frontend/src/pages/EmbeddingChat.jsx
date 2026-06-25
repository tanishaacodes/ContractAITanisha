import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Send, MessageCircle, FileText, TrendingUp, Lightbulb } from 'lucide-react';
import useThemeStore from '../store/themeStore';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const EmbeddingChat = () => {
  const { contractId } = useParams();
  const { theme } = useThemeStore();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [expandedClauses, setExpandedClauses] = useState({}); // Track which clauses are expanded

  useEffect(() => {
    if (contractId) {
      loadSuggestedQuestions();
    }
  }, [contractId]);

  const loadSuggestedQuestions = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/embedding/contracts/${contractId}/suggest-questions`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setSuggestedQuestions(response.data.suggested_questions || []);
    } catch (err) {
      console.error('Failed to load suggested questions:', err);
    }
  };

  const handleSubmit = async (e, customQuery = null) => {
    e?.preventDefault();

    const questionText = customQuery || query;
    if (!questionText.trim()) return;

    // Add user message
    setMessages(prev => [...prev, {
      type: 'user',
      text: questionText,
      timestamp: new Date()
    }]);

    setQuery('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/embedding/contracts/${contractId}/query`,
        {
          query: questionText,
          top_k: 3,
          min_similarity: 0.3
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      // Add assistant response
      setMessages(prev => [...prev, {
        type: 'assistant',
        data: response.data,
        timestamp: new Date()
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'error',
        text: err.response?.data?.error || 'Failed to get answer',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedClick = (question) => {
    handleSubmit(null, question);
  };

  const toggleClauseExpansion = (messageIdx, clauseIdx) => {
    const key = `${messageIdx}-${clauseIdx}`;
    setExpandedClauses(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  return (
    <div className={`flex flex-col h-screen ${theme.colors.background}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-6 shadow-lg">
        <h1 className="text-2xl font-bold mb-2">Embedding-Based Contract Chat</h1>
        <p className="text-blue-100 text-sm">
          Pure semantic retrieval • No hallucinations • Explainable results
        </p>
      </div>

      {/* Chat Container */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <MessageCircle className={`w-16 h-16 ${theme.colors.textSecondary} mx-auto mb-4`} />
              <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} mb-2`}>
                Ask a question about your contract
              </h3>
              <p className={`${theme.colors.textSecondary} text-sm mb-6`}>
                Get relevant clauses without any AI-generated text
              </p>

              {/* Suggested Questions */}
              {suggestedQuestions.length > 0 && (
                <div className="max-w-2xl mx-auto">
                  <div className={`flex items-center gap-2 ${theme.colors.textPrimary} mb-3`}>
                    <Lightbulb className="w-5 h-5" />
                    <span className="font-medium text-sm">Try asking:</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {suggestedQuestions.slice(0, 6).map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestedClick(q)}
                        className={`text-left ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg p-3 hover:border-blue-500 transition-all text-sm ${theme.colors.textPrimary}`}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.type === 'user' ? (
                  <div className="bg-blue-600 text-white rounded-lg px-4 py-3 max-w-xl">
                    {msg.text}
                  </div>
                ) : msg.type === 'error' ? (
                  <div className="bg-red-900 bg-opacity-20 border border-red-500 text-red-400 rounded-lg px-4 py-3 max-w-xl">
                    {msg.text}
                  </div>
                ) : (
                  <div className={`${theme.colors.surface} rounded-lg border ${theme.colors.surfaceBorder} p-4 max-w-3xl`}>
                    {/* Answer */}
                    <div className="mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-5 h-5 text-blue-400" />
                        <span className={`font-semibold ${theme.colors.textPrimary}`}>Answer</span>
                      </div>
                      <p className={`${theme.colors.textSecondary} whitespace-pre-wrap`}>{msg.data.answer}</p>
                    </div>

                    {/* Supporting Clauses */}
                    {msg.data.supporting_clauses && msg.data.supporting_clauses.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <TrendingUp className="w-5 h-5 text-green-400" />
                          <span className={`font-semibold ${theme.colors.textPrimary}`}>
                            Supporting Clauses ({msg.data.num_results})
                          </span>
                        </div>

                        <div className="space-y-3">
                          {msg.data.supporting_clauses.map((clause, cidx) => {
                            const isExpanded = expandedClauses[`${idx}-${cidx}`];
                            return (
                              <div
                                key={cidx}
                                onClick={() => toggleClauseExpansion(idx, cidx)}
                                className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg p-3 cursor-pointer hover:border-blue-500 transition-all`}
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <h4 className={`font-medium ${theme.colors.textPrimary} flex items-center gap-2`}>
                                    {clause.clause_name}
                                    {!isExpanded && (
                                      <span className="text-xs text-blue-400">(click for details)</span>
                                    )}
                                  </h4>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs bg-blue-900 bg-opacity-30 text-blue-400 border border-blue-500 px-2 py-1 rounded-full font-medium">
                                      {(clause.similarity * 100).toFixed(0)}% relevant
                                    </span>
                                    {clause.risk_level && (
                                      <span className={`text-xs px-2 py-1 rounded-full font-medium border ${
                                        clause.risk_level === 'HIGH' ? 'bg-red-900 bg-opacity-20 text-red-400 border-red-500' :
                                        clause.risk_level === 'MEDIUM' ? 'bg-orange-900 bg-opacity-20 text-orange-400 border-orange-500' :
                                        'bg-green-900 bg-opacity-20 text-green-400 border-green-500'
                                      }`}>
                                        {clause.risk_level}
                                      </span>
                                    )}
                                  </div>
                                </div>

                                {/* Clause Text - Expandable */}
                                <div className={`text-sm ${theme.colors.textSecondary} ${isExpanded ? '' : 'line-clamp-3'} mb-2`}>
                                  {clause.clause_text}
                                </div>

                                {/* Expanded Details */}
                                {isExpanded && (
                                  <div className={`mt-3 pt-3 border-t ${theme.colors.surfaceBorder} space-y-2`}>
                                    <div className="grid grid-cols-2 gap-3 text-xs">
                                      <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded p-2`}>
                                        <p className="text-blue-400 font-semibold mb-1">Similarity Score</p>
                                        <p className={`${theme.colors.textPrimary} text-lg font-bold`}>
                                          {(clause.similarity * 100).toFixed(2)}%
                                        </p>
                                        <p className={`${theme.colors.textSecondary} text-xs mt-1`}>
                                          Semantic match to your question
                                        </p>
                                      </div>

                                      {clause.risk_level && (
                                        <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded p-2`}>
                                          <p className="text-purple-400 font-semibold mb-1">Risk Assessment</p>
                                          <p className={`text-lg font-bold ${
                                            clause.risk_level === 'HIGH' ? 'text-red-400' :
                                            clause.risk_level === 'MEDIUM' ? 'text-orange-400' :
                                            'text-green-400'
                                          }`}>
                                            {clause.risk_level}
                                          </p>
                                          <p className={`${theme.colors.textSecondary} text-xs mt-1`}>
                                            Based on clause analysis
                                          </p>
                                        </div>
                                      )}
                                    </div>

                                    <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded p-2`}>
                                      <p className="text-cyan-400 font-semibold text-xs mb-1">Analysis Method</p>
                                      <p className={`${theme.colors.textSecondary} text-xs`}>
                                        ✓ Pure semantic embedding retrieval<br />
                                        ✓ No AI generation or hallucinations<br />
                                        ✓ Direct extraction from contract text
                                      </p>
                                    </div>

                                    <p className="text-xs text-blue-400 text-center mt-2">
                                      Click again to collapse
                                    </p>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className={`mt-4 pt-3 border-t ${theme.colors.surfaceBorder} flex items-center justify-between text-xs ${theme.colors.textSecondary}`}>
                      <span>Confidence: {(msg.data.confidence * 100).toFixed(0)}%</span>
                      <span>{msg.data.analysis_method || 'Semantic retrieval'}</span>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div className="flex justify-start">
              <div className={`${theme.colors.surface} rounded-lg border ${theme.colors.surfaceBorder} px-4 py-3`}>
                <div className="flex items-center gap-2">
                  <div className="animate-pulse flex gap-1">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animation-delay-200"></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animation-delay-400"></div>
                  </div>
                  <span className={`${theme.colors.textSecondary} text-sm`}>Searching clauses...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className={`${theme.colors.surface} border-t ${theme.colors.surfaceBorder} p-4 shadow-lg`}>
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your contract..."
              className={`flex-1 px-4 py-3 border ${theme.colors.surfaceBorder} ${theme.colors.surface} ${theme.colors.textPrimary} rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
              Send
            </button>
          </form>

          <p className={`text-xs ${theme.colors.textSecondary} mt-2 text-center`}>
            Zero hallucinations • Pure semantic retrieval • All answers from actual contract clauses
          </p>
        </div>
      </div>
    </div>
  );
};

export default EmbeddingChat;
