/**
 * Contract Concept Viewer
 * ========================
 * View concept graphs extracted from real uploaded contracts.
 * Shows which legal concepts are present in a specific contract.
 */

import React, { useState, useEffect, memo } from 'react';
import ReactFlow, { Background, Controls, MiniMap, Handle, Position } from 'reactflow';
import 'reactflow/dist/style.css';
import { getContractConceptGraph } from '../services/conceptGraphService';
import api from '../utils/api';
import { Search, FileText, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

// Custom Concept Node Component
const ConceptNode = memo(({ data }) => {
  const { label, strength, color, size } = data;

  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '50%',
        background: `linear-gradient(135deg, ${color}CC, ${color}FF)`,
        border: `3px solid ${color}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px',
        boxShadow: `0 4px 12px ${color}40`,
        cursor: 'pointer',
        transition: 'all 0.3s ease',
      }}
      className="concept-node"
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />

      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontSize: size > 90 ? '11px' : '9px',
          fontWeight: 'bold',
          color: '#fff',
          textShadow: '0 1px 2px rgba(0,0,0,0.3)',
          lineHeight: '1.2'
        }}>
          {label}
        </div>
        <div style={{
          fontSize: size > 90 ? '10px' : '8px',
          color: '#fff',
          opacity: 0.9,
          marginTop: '2px'
        }}>
          {Math.round(strength * 100)}%
        </div>
      </div>
    </div>
  );
});

ConceptNode.displayName = 'ConceptNode';

// Register custom node types
const nodeTypes = {
  conceptNode: ConceptNode,
};

const ContractConceptViewer = () => {
  const [contracts, setContracts] = useState([]);
  const [selectedContractId, setSelectedContractId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingContracts, setLoadingContracts] = useState(true);
  const [error, setError] = useState(null);
  const [graphData, setGraphData] = useState(null);

  // Fetch contracts on mount
  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      setLoadingContracts(true);
      const response = await api.get('/contracts/list');
      setContracts(response.data.contracts || []);
    } catch (err) {
      console.error('Failed to fetch contracts:', err);
      setError('Failed to load contracts');
    } finally {
      setLoadingContracts(false);
    }
  };

  const handleContractSelect = async (contractId) => {
    if (!contractId) return;

    setSelectedContractId(contractId);
    setLoading(true);
    setError(null);

    try {
      const data = await getContractConceptGraph(contractId);
      setGraphData(data);
    } catch (err) {
      console.error('Failed to fetch concept graph:', err);
      setError(err.response?.data?.error || 'Failed to load concept graph');
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  };

  // Get top 5 concepts by strength
  const getTopConcepts = () => {
    if (!graphData?.concept_strengths) return [];
    return Object.entries(graphData.concept_strengths)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-400" />
              Contract Concept Viewer
            </h1>
            <p className="text-gray-400 mt-2">
              Extract and visualize legal concepts from your uploaded contracts
            </p>
          </div>
        </div>
      </div>

      {/* Contract Selector */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
          <label className="block text-sm font-medium text-gray-300 mb-3">
            Select Contract
          </label>
          <div className="flex gap-4">
            <select
              value={selectedContractId || ''}
              onChange={(e) => handleContractSelect(e.target.value)}
              className="flex-1 bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              disabled={loadingContracts}
            >
              <option value="">
                {loadingContracts ? 'Loading contracts...' : 'Choose a contract'}
              </option>
              {contracts.map((contract) => (
                <option key={contract.id} value={contract.id}>
                  {contract.original_filename || contract.filename}
                  {contract.contract_type && ` (${contract.contract_type})`}
                </option>
              ))}
            </select>
            <button
              onClick={() => selectedContractId && handleContractSelect(selectedContractId)}
              disabled={!selectedContractId || loading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg font-medium transition flex items-center gap-2"
            >
              <Search className="w-4 h-4" />
              Analyze
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-12 text-center">
            <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-300">Extracting concepts from contract...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
            <div>
              <p className="text-red-300 font-medium">Error</p>
              <p className="text-red-400 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Graph Data Display */}
      {graphData && !loading && (
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-300 text-sm">Contract Type</p>
                  <p className="text-white text-2xl font-bold mt-1">
                    {graphData.contract_type || 'Unknown'}
                  </p>
                </div>
                <FileText className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-300 text-sm">Total Concepts</p>
                  <p className="text-white text-2xl font-bold mt-1">
                    {graphData.stats?.total_nodes || 0}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-300 text-sm">Correlations</p>
                  <p className="text-white text-2xl font-bold mt-1">
                    {graphData.stats?.total_edges || 0}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-400" />
              </div>
            </div>

            <div className="bg-gradient-to-br from-orange-900/50 to-orange-800/30 border border-orange-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-orange-300 text-sm">Strong Links</p>
                  <p className="text-white text-2xl font-bold mt-1">
                    {graphData.stats?.strong_correlations || 0}
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-orange-400" />
              </div>
            </div>
          </div>

          {/* Top Concepts */}
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Top 5 Concepts</h2>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {getTopConcepts().map(([concept, strength], idx) => (
                <div
                  key={concept}
                  className="bg-slate-700/50 border border-slate-600 rounded-lg p-4"
                >
                  <div className="text-xs text-gray-400 mb-1">#{idx + 1}</div>
                  <div className="text-white font-medium text-sm mb-2">{concept}</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-slate-600 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-full transition-all duration-500"
                        style={{ width: `${strength * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-300 font-mono">
                      {(strength * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Concept Graph Visualization */}
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Concept Correlation Graph</h2>
            <div className="bg-slate-900 rounded-lg overflow-hidden" style={{ height: '600px' }}>
              <ReactFlow
                nodes={graphData.nodes || []}
                edges={graphData.edges || []}
                nodeTypes={nodeTypes}
                fitView
                attributionPosition="bottom-left"
              >
                <Background color="#334155" gap={16} />
                <Controls />
                <MiniMap
                  nodeColor="#60a5fa"
                  maskColor="rgba(0, 0, 0, 0.6)"
                  style={{ background: '#1e293b' }}
                />
              </ReactFlow>
            </div>
            <p className="text-gray-400 text-sm mt-3">
              <strong>Note:</strong> Node size indicates concept strength. Edge thickness shows correlation strength.
              {graphData.using_neo4j && ' ✓ Stored in Neo4j'}
            </p>
          </div>

          {/* Concept Strengths Table */}
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">All Concept Strengths</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="text-left text-gray-300 font-medium py-3 px-4">Concept</th>
                    <th className="text-left text-gray-300 font-medium py-3 px-4">Strength</th>
                    <th className="text-left text-gray-300 font-medium py-3 px-4">Visual</th>
                    <th className="text-left text-gray-300 font-medium py-3 px-4">Classification</th>
                  </tr>
                </thead>
                <tbody>
                  {graphData.concept_strengths &&
                    Object.entries(graphData.concept_strengths)
                      .sort((a, b) => b[1] - a[1])
                      .map(([concept, strength]) => (
                        <tr key={concept} className="border-b border-slate-700 hover:bg-slate-700/30">
                          <td className="py-3 px-4 text-white font-medium">{concept}</td>
                          <td className="py-3 px-4">
                            <span className="font-mono text-blue-300">{strength.toFixed(3)}</span>
                          </td>
                          <td className="py-3 px-4">
                            <div className="w-32 bg-slate-600 rounded-full h-2">
                              <div
                                className={`h-full rounded-full ${
                                  strength > 0.7 ? 'bg-green-500' :
                                  strength > 0.4 ? 'bg-yellow-500' :
                                  'bg-red-500'
                                }`}
                                style={{ width: `${strength * 100}%` }}
                              />
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                strength > 0.7 ? 'bg-green-900/50 text-green-300 border border-green-700' :
                                strength > 0.4 ? 'bg-yellow-900/50 text-yellow-300 border border-yellow-700' :
                                'bg-gray-900/50 text-gray-300 border border-gray-700'
                              }`}
                            >
                              {strength > 0.7 ? 'High' : strength > 0.4 ? 'Medium' : 'Low'}
                            </span>
                          </td>
                        </tr>
                      ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!selectedContractId && !loading && !error && (
        <div className="max-w-7xl mx-auto">
          <div className="bg-slate-800/30 border-2 border-dashed border-slate-600 rounded-lg p-12 text-center">
            <FileText className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">
              Select a contract above to view its concept graph
            </p>
            <p className="text-gray-500 text-sm mt-2">
              Concepts are automatically extracted from contract clauses
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractConceptViewer;
