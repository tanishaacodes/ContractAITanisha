import { useState } from 'react';
import { FlaskConical, Loader, AlertTriangle, CheckCircle } from 'lucide-react';
import useThemeStore from '../../store/themeStore';

/**
 * What-If Simulation Control Panel
 * Allows selecting a clause and running simulation
 */
export default function WhatIfPanel({
  clauses,
  onRunSimulation,
  loading,
  selectedClauseId,
  onSelectClause,
  includeExposure,
  onToggleExposure,
  includeMonteCarlo,
  onToggleMonteCarlo
}) {
  const { currentTheme } = useThemeStore();
  const theme = currentTheme;

  // Filter to clauses with risk > 0, sorted by risk score
  const sortedClauses = [...(clauses || [])]
    .filter(clause => (clause.risk_score || 0) > 0) // Only show clauses with risk
    .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0));

  const getRiskBadge = (score) => {
    if (score >= 0.7) return {
      text: 'HIGH',
      color: theme === 'dark' ? 'bg-red-900 bg-opacity-50 text-red-300 border border-red-700' : 'bg-red-100 text-red-700'
    };
    if (score >= 0.5) return {
      text: 'MED',
      color: theme === 'dark' ? 'bg-orange-900 bg-opacity-50 text-orange-300 border border-orange-700' : 'bg-orange-100 text-orange-700'
    };
    return {
      text: 'LOW',
      color: theme === 'dark' ? 'bg-green-900 bg-opacity-50 text-green-300 border border-green-700' : 'bg-green-100 text-green-700'
    };
  };

  return (
    <div className={`rounded-lg shadow-lg p-6 mb-6 ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
    }`}>
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <div className={`p-2 rounded-lg ${
          theme === 'dark' ? 'bg-blue-900 bg-opacity-50' : 'bg-blue-100'
        }`}>
          <FlaskConical className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h3 className={`text-lg font-bold ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            What-If Simulation
          </h3>
          <p className={`text-sm ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Simulate impact of removing a clause
          </p>
        </div>
      </div>

      {/* Clause Selection */}
      <div className="mb-4">
        <label className={`block text-sm font-medium mb-2 ${
          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
        }`}>
          Select Clause to Remove
        </label>
        <select
          value={selectedClauseId || ''}
          onChange={(e) => onSelectClause(e.target.value)}
          className={`w-full p-3 rounded-lg border ${
            theme === 'dark'
              ? 'bg-gray-700 border-gray-600 text-white'
              : 'bg-white border-gray-300 text-gray-900'
          } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
        >
          <option value="">-- Select a clause --</option>
          {sortedClauses.map((clause) => {
            const risk = getRiskBadge(clause.risk_score || 0);
            return (
              <option key={clause.id} value={clause.id}>
                [{risk.text}] {clause.clause_type || 'Unknown'} - Risk: {(clause.risk_score || 0).toFixed(2)}
              </option>
            );
          })}
        </select>
      </div>

      {/* Selected Clause Preview */}
      {selectedClauseId && (
        <div className={`p-4 rounded-lg mb-4 ${
          theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
        }`}>
          {(() => {
            const clause = clauses.find(c => c.id === selectedClauseId);
            if (!clause) return null;
            const risk = getRiskBadge(clause.risk_score || 0);

            return (
              <>
                <div className="flex items-center justify-between mb-2">
                  <span className={`font-medium ${
                    theme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>
                    {clause.clause_type || 'Unknown Type'}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${risk.color}`}>
                    {risk.text} RISK
                  </span>
                </div>
                <p className={`text-sm ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  {clause.extracted_text?.substring(0, 150) ||
                   clause.text_spans?.substring(0, 150) ||
                   'No text available'}...
                </p>
              </>
            );
          })()}
        </div>
      )}

      {/* Options */}
      <div className="space-y-3 mb-6">
        <label className={`flex items-center space-x-3 cursor-pointer ${
          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
        }`}>
          <input
            type="checkbox"
            checked={includeExposure}
            onChange={(e) => onToggleExposure(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
          />
          <span className="text-sm">Include Financial Exposure Analysis</span>
        </label>

        <label className={`flex items-center space-x-3 cursor-pointer ${
          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
        }`}>
          <input
            type="checkbox"
            checked={includeMonteCarlo}
            onChange={(e) => onToggleMonteCarlo(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
          />
          <span className="text-sm">Include Monte Carlo Simulation (90% Confidence)</span>
        </label>
      </div>

      {/* Run Button */}
      <button
        onClick={() => onRunSimulation(selectedClauseId)}
        disabled={!selectedClauseId || loading}
        className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
          !selectedClauseId || loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-red-600 hover:bg-red-700'
        }`}
      >
        {loading ? (
          <span className="flex items-center justify-center space-x-2">
            <Loader className="w-5 h-5 animate-spin" />
            <span>Running Simulation...</span>
          </span>
        ) : (
          <span className="flex items-center justify-center space-x-2">
            <FlaskConical className="w-5 h-5" />
            <span>Simulate Removal</span>
          </span>
        )}
      </button>

      {/* Info */}
      <p className={`mt-4 text-xs text-center ${
        theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
      }`}>
        This simulation is non-destructive. No changes are made to the contract.
      </p>
    </div>
  );
}
