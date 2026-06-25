import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import useThemeStore from '../store/themeStore';
import RiskHeatmap from '../components/RiskHeatmap';
import ClauseRedliner from '../components/ClauseRedliner';
import ExplainabilityDrawer from '../components/ExplainabilityDrawer';

/**
 * RiskHeatmapPage
 *
 * Integrated page combining:
 * - Risk Heatmap (left panel)
 * - Clause Viewer + Redlining (main panel)
 * - Explainability Drawer (right slide-in)
 *
 * Feature 3: Complete Risk Heatmap & Redlining UI
 */

const RiskHeatmapPage = () => {
  const { contractId } = useParams();
  const { theme } = useThemeStore();

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [heatmapData, setHeatmapData] = useState([]);
  const [selectedRisk, setSelectedRisk] = useState(null);
  const [explainabilityOpen, setExplainabilityOpen] = useState(false);
  const [contractName, setContractName] = useState('');
  const [safeguardTable, setSafeguardTable] = useState([]);
  const [activeTab, setActiveTab] = useState('heatmap'); // heatmap | safeguards

  // Load heatmap data
  useEffect(() => {
    loadHeatmapData();
  }, [contractId]);

  // Update safeguard table when heatmap data changes
  useEffect(() => {
    if (heatmapData.length > 0) {
      loadSafeguardTable();
    }
  }, [heatmapData]);

  const loadHeatmapData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/embedding/contracts/${contractId}/risk-heatmap`
      );

      const heatmapItems = response.data.heatmap_items || [];

      // If no data exists, trigger analysis automatically
      if (heatmapItems.length === 0) {
        console.log('No risk data found. Triggering automatic analysis...');
        await triggerAnalysis();
        // Reload data after analysis
        const retryResponse = await axios.get(
          `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/embedding/contracts/${contractId}/risk-heatmap`
        );
        setHeatmapData(retryResponse.data.heatmap_items || []);
        setContractName(retryResponse.data.contract_name || 'Contract');
      } else {
        setHeatmapData(heatmapItems);
        setContractName(response.data.contract_name || 'Contract');
      }

      setLoading(false);
    } catch (err) {
      console.error('Error loading heatmap data:', err);
      setError(err.response?.data?.error || 'Failed to load risk heatmap');
      setLoading(false);
    }
  };

  const triggerAnalysis = async () => {
    try {
      console.log('Running deviation analysis...');
      await axios.post(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/embedding/contracts/${contractId}/analyze-deviations`
      );

      console.log('Running safeguard detection...');
      await axios.post(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/embedding/contracts/${contractId}/detect-safeguards`
      );

      console.log('Analysis complete!');
    } catch (err) {
      console.error('Error during analysis:', err);
      throw err;
    }
  };

  const loadSafeguardTable = async () => {
    try {
      // Use heatmap data filtered for missing safeguards instead of separate API call
      // This ensures consistency and reduces API calls
      const safeguards = heatmapData.filter(item => item.type === 'MISSING_SAFEGUARD');
      setSafeguardTable(safeguards);
    } catch (err) {
      console.error('Error loading safeguard table:', err);
    }
  };

  const handleSelectRisk = (risk) => {
    setSelectedRisk(risk);
  };

  const handleOpenExplainability = () => {
    if (selectedRisk && selectedRisk.details) {
      setExplainabilityOpen(true);
    }
  };

  // Build explainability insight from selected risk
  const buildExplainabilityInsight = () => {
    if (!selectedRisk) return null;

    const { details, riskScore, status, clauseType, category } = selectedRisk;

    if (selectedRisk.type === 'DEVIATION') {
      return {
        clauseType,
        reason: details.risk_type,
        similarity: riskScore,
        explanation: details.explanation,
        suggestion: details.suggested_replacement,
        courtPrecedent: details.court_precedent,
        riskType: details.risk_type,
        analysisMethod: 'embedding-based deviation detection (deterministic)'
      };
    } else {
      // MISSING_SAFEGUARD
      return {
        clauseType,
        reason: `Missing ${details.criticality} safeguard`,
        similarity: null,
        confidenceLevel: 1.0 - riskScore, // Invert for missing items
        explanation: details.ai_insight,
        suggestedAction: details.suggested_action,
        suggestion: details.suggested_clause,
        riskType: `Missing ${category.replace(/_/g, ' ')}`,
        analysisMethod: 'semantic absence detection (deterministic)'
      };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ backgroundColor: theme.colors.background }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg" style={{ color: theme.colors.textPrimary }}>
            Loading risk analysis...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ backgroundColor: theme.colors.background }}>
        <div className="max-w-md p-6 rounded-lg bg-red-50 border border-red-200">
          <h3 className="text-lg font-bold text-red-900 mb-2">Error Loading Data</h3>
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={loadHeatmapData}
            className="mt-4 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: theme.colors.background }}>
      {/* Header */}
      <div className="px-6 py-4 border-b" style={{ borderColor: theme.colors.border }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: theme.colors.textPrimary }}>
              Risk Heatmap & Deviation Analysis
            </h1>
            <p className="text-sm mt-1" style={{ color: theme.colors.textSecondary }}>
              {contractName}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              AI-Powered
            </span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              No Hallucinations
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mt-4">
          <button
            onClick={() => setActiveTab('heatmap')}
            className={`px-4 py-2 font-medium rounded-lg transition-colors ${
              activeTab === 'heatmap'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Risk Heatmap
          </button>
          <button
            onClick={() => setActiveTab('safeguards')}
            className={`px-4 py-2 font-medium rounded-lg transition-colors ${
              activeTab === 'safeguards'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Missing Safeguards
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Heatmap or Safeguards */}
        <div className="w-[350px] border-r overflow-y-auto p-4" style={{ borderColor: theme.colors.border }}>
          {activeTab === 'heatmap' ? (
            <RiskHeatmap
              risks={heatmapData.filter(item => item.type === 'DEVIATION')}
              onSelect={handleSelectRisk}
              selectedClauseType={selectedRisk?.clauseType}
            />
          ) : (
            <SafeguardTable safeguards={safeguardTable} onSelect={handleSelectRisk} />
          )}
        </div>

        {/* Main Panel - Clause Viewer + Redlining */}
        <div className="flex-1 overflow-y-auto p-6">
          {selectedRisk ? (
            <div className="space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold" style={{ color: theme.colors.textPrimary }}>
                    {selectedRisk.clauseType}
                  </h2>
                  <p className="text-sm mt-1" style={{ color: theme.colors.textSecondary }}>
                    Category: {selectedRisk.category?.replace(/_/g, ' ')}
                  </p>
                </div>

                <button
                  onClick={handleOpenExplainability}
                  className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <span>🔍</span>
                  <span>View Explainability</span>
                </button>
              </div>

              {/* Redliner */}
              {selectedRisk.type === 'DEVIATION' && selectedRisk.details && (
                <ClauseRedliner
                  originalText={selectedRisk.originalText || '[No text available]'}
                  suggestedText={selectedRisk.suggestedText || selectedRisk.details.suggested_replacement}
                  riskType={selectedRisk.details.risk_type}
                  explanation={selectedRisk.details.explanation}
                  showDiff={true}
                />
              )}

              {selectedRisk.type === 'MISSING_SAFEGUARD' && selectedRisk.details && (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-red-50 border border-red-200">
                    <div className="flex items-start gap-2">
                      <span className="text-red-600 text-2xl">❌</span>
                      <div>
                        <h3 className="font-semibold text-red-900 mb-2">Missing Safeguard</h3>
                        <p className="text-sm text-red-800">{selectedRisk.details.ai_insight}</p>
                      </div>
                    </div>
                  </div>

                  {selectedRisk.details.suggested_clause && (
                    <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                      <h4 className="font-semibold text-green-900 mb-2">Suggested Clause to Add:</h4>
                      <p className="text-sm text-green-800">{selectedRisk.details.suggested_clause}</p>
                    </div>
                  )}

                  <div className="p-4 rounded-lg bg-purple-50 border border-purple-200">
                    <h4 className="font-semibold text-purple-900 mb-2">Recommended Action:</h4>
                    <p className="text-sm text-purple-800">{selectedRisk.details.suggested_action}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <span className="text-6xl mb-4 block">👈</span>
                <p className="text-lg" style={{ color: theme.colors.textPrimary }}>
                  Select a risk item from the heatmap to view details
                </p>
                <p className="text-sm mt-2" style={{ color: theme.colors.textSecondary }}>
                  Click on any colored item in the left panel
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Explainability Drawer */}
      <ExplainabilityDrawer
        insight={buildExplainabilityInsight()}
        isOpen={explainabilityOpen}
        onClose={() => setExplainabilityOpen(false)}
      />
    </div>
  );
};

/**
 * SafeguardTable Component
 *
 * Displays missing/weak safeguards in table format
 */
const SafeguardTable = ({ safeguards, onSelect }) => {
  const { theme } = useThemeStore();

  if (!safeguards || safeguards.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No safeguard data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-bold mb-3" style={{ color: theme.colors.textPrimary }}>
        Safeguard Status
      </h3>

      {safeguards.map((safeguard, index) => {
        const criticality = safeguard.details?.criticality || 'RECOMMENDED';
        const confidence = safeguard.details?.confidenceLevel || safeguard.riskScore || 0;
        const statusSymbol = safeguard.status === 'MISSING' ? '❌' : '⚠️';

        return (
          <div
            key={index}
            onClick={() => onSelect(safeguard)}
            className="p-3 rounded-lg cursor-pointer hover:shadow-lg transition-all border"
            style={{
              backgroundColor: theme.colors.surface,
              borderColor: theme.colors.border
            }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">{statusSymbol}</span>
                <div>
                  <p className="font-medium text-sm" style={{ color: theme.colors.textPrimary }}>
                    {safeguard.clauseType}
                  </p>
                  <p className="text-xs" style={{ color: theme.colors.textSecondary }}>
                    {safeguard.category}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-xs font-medium px-2 py-1 rounded ${
                  criticality === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                  criticality === 'IMPORTANT' ? 'bg-orange-100 text-orange-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {criticality}
                </span>
                <p className="text-xs mt-1" style={{ color: theme.colors.textSecondary }}>
                  {(confidence * 100).toFixed(0)}% conf
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RiskHeatmapPage;
