import React, { useState, useEffect } from "react";
import { Sparkles, Loader2, Filter, RefreshCw } from "lucide-react";
import api from "../utils/api";
import SuggestionCard from "./SuggestionCard";
import useThemeStore from "../store/themeStore";

const NegotiationPanel = ({ contractId }) => {
  const { theme } = useThemeStore();
  const [clauses, setClauses] = useState([]);
  const [selectedClause, setSelectedClause] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [perspective, setPerspective] = useState("BUYER");
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [error, setError] = useState("");

  useEffect(() => {
    loadClauses();
    loadSuggestions();
  }, [contractId, statusFilter]);

  const loadClauses = async () => {
    try {
      const response = await api.get(`/contracts/${contractId}/clauses`);
      const foundClauses = response.data.clauses.filter(c => c.found);
      setClauses(foundClauses);
      if (foundClauses.length > 0 && !selectedClause) {
        setSelectedClause(foundClauses[0].id);
      }
    } catch (err) {
      console.error("Error loading clauses:", err);
      setError("Failed to load clauses");
    }
  };

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      const params = statusFilter ? `?status=${statusFilter}` : "";
      const response = await api.get(`/contracts/${contractId}/negotiation-suggestions${params}`);
      setSuggestions(response.data.suggestions || []);
    } catch (err) {
      console.error("Error loading suggestions:", err);
      setError("Failed to load suggestions");
    } finally {
      setLoading(false);
    }
  };

  const analyzeClause = async () => {
    if (!selectedClause) {
      setError("Please select a clause to analyze");
      return;
    }

    try {
      setAnalyzing(true);
      setError("");
      const response = await api.post(
        `/contracts/${contractId}/clauses/${selectedClause}/analyze-negotiation`,
        { perspective }
      );

      console.log("[NEGOTIATION] Analysis complete:", response.data);

      // Reload suggestions to show new ones
      await loadSuggestions();

      alert(`Generated ${response.data.suggestions_count} suggestions!`);
    } catch (err) {
      console.error("[NEGOTIATION] Analysis error:", err);
      setError(err.response?.data?.error || "Failed to analyze clause");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAccept = async (suggestionId) => {
    try {
      await api.post(`/negotiation-suggestions/${suggestionId}/update-status`, {
        action: "ACCEPT"
      });
      await loadSuggestions();
    } catch (err) {
      console.error("Error accepting suggestion:", err);
      setError("Failed to accept suggestion");
    }
  };

  const handleReject = async (suggestionId) => {
    try {
      await api.post(`/negotiation-suggestions/${suggestionId}/update-status`, {
        action: "REJECT"
      });
      await loadSuggestions();
    } catch (err) {
      console.error("Error rejecting suggestion:", err);
      setError("Failed to reject suggestion");
    }
  };

  const selectedClauseData = clauses.find(c => c.id === selectedClause);
  const clauseSuggestions = selectedClause
    ? suggestions.filter(s => s.clauseId === selectedClause)
    : suggestions;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-700 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="w-6 h-6 text-purple-400" />
          <h2 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>Negotiation Agent</h2>
        </div>
        <p className={theme.colors.textSecondary}>
          AI-powered clause rewrite suggestions to help you negotiate better terms
        </p>
      </div>

      {/* Analysis Controls */}
      <div className={`${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg p-6`}>
        <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} mb-4`}>Generate New Suggestions</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Clause Selector */}
          <div>
            <label className={`block text-sm font-semibold ${theme.colors.textSecondary} mb-2`}>
              Select Clause
            </label>
            <select
              value={selectedClause || ""}
              onChange={(e) => setSelectedClause(e.target.value)}
              className={`w-full ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded px-3 py-2 ${theme.colors.textPrimary} focus:border-purple-500 focus:outline-none`}
            >
              <option value="">-- Select a clause --</option>
              {clauses.map(clause => {
                // Handle confidence values that might be 0-1 or 0-100 format
                const confidencePercent = clause.confidence > 1
                  ? clause.confidence.toFixed(0)
                  : (clause.confidence * 100).toFixed(0);

                return (
                  <option key={clause.id} value={clause.id}>
                    {clause.clauseName} ({confidencePercent}%)
                  </option>
                );
              })}
            </select>
          </div>

          {/* Perspective Selector */}
          <div>
            <label className={`block text-sm font-semibold ${theme.colors.textSecondary} mb-2`}>
              Your Perspective
            </label>
            <select
              value={perspective}
              onChange={(e) => setPerspective(e.target.value)}
              className={`w-full ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded px-3 py-2 ${theme.colors.textPrimary} focus:border-purple-500 focus:outline-none`}
            >
              <option value="BUYER">Buyer / Client</option>
              <option value="SELLER">Seller / Vendor</option>
            </select>
          </div>

          {/* Analyze Button */}
          <div className="flex items-end">
            <button
              onClick={analyzeClause}
              disabled={analyzing || !selectedClause}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white px-6 py-2 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              {analyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze Clause
                </>
              )}
            </button>
          </div>
        </div>

        {/* Selected Clause Preview */}
        {selectedClauseData && (
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded p-3`}>
            <div className={`text-xs font-semibold ${theme.colors.textSecondary} mb-1`}>
              {selectedClauseData.clauseName}
            </div>
            <p className={`${theme.colors.textSecondary} text-sm line-clamp-2`}>
              {(() => {
                if (selectedClauseData.extractedText) return selectedClauseData.extractedText;
                if (selectedClauseData.contextSentences) {
                  // Handle if contextSentences is an array of objects
                  if (Array.isArray(selectedClauseData.contextSentences)) {
                    return selectedClauseData.contextSentences.map(s => s.text || s).join(" ");
                  }
                  // Handle if it's a string
                  if (typeof selectedClauseData.contextSentences === 'string') {
                    return selectedClauseData.contextSentences;
                  }
                }
                return "No text available";
              })()}
            </p>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Suggestions List */}
      <div className={`${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold ${theme.colors.textPrimary}`}>
            Suggestions ({clauseSuggestions.length})
          </h3>

          <div className="flex items-center gap-2">
            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded px-3 py-1.5 text-sm ${theme.colors.textPrimary} focus:border-purple-500 focus:outline-none`}
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="REJECTED">Rejected</option>
            </select>

            {/* Refresh Button */}
            <button
              onClick={loadSuggestions}
              disabled={loading}
              className={`p-2 ${theme.colors.surfaceBorder} hover:opacity-80 rounded ${theme.colors.textSecondary} hover:${theme.colors.textPrimary} transition-colors`}
              title="Refresh suggestions"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
          </div>
        ) : clauseSuggestions.length === 0 ? (
          <div className={`text-center py-12 ${theme.colors.textSecondary}`}>
            <Sparkles className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="font-semibold mb-1">No suggestions yet</p>
            <p className="text-sm">Select a clause and click "Analyze Clause" to generate AI-powered suggestions</p>
          </div>
        ) : (
          <div className="space-y-4">
            {clauseSuggestions.map(suggestion => (
              <SuggestionCard
                key={suggestion.id}
                suggestion={suggestion}
                onAccept={handleAccept}
                onReject={handleReject}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NegotiationPanel;
