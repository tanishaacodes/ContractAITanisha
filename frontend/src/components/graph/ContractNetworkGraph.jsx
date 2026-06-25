import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, Maximize2, RefreshCw, Layers } from 'lucide-react';
import Neo4jGraphCanvas from './Neo4jGraphCanvas';
import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const ContractNetworkGraph = ({ contractId, initialData = null }) => {
  const [graphData, setGraphData] = useState(initialData);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showStats, setShowStats] = useState(true);

  // Update graphData when initialData changes
  useEffect(() => {
    if (initialData) {
      console.log('[ContractNetworkGraph] Setting initialData:', initialData);
      // Extract subgraph if initialData has nested structure
      const extractedData = initialData.subgraph || initialData;
      console.log('[ContractNetworkGraph] Extracted data:', extractedData);
      setGraphData(extractedData);
      setLoading(false);
    }
  }, [initialData]);

  useEffect(() => {
    if (!initialData && contractId) {
      fetchGraphData();
    }
  }, [contractId, initialData]);

  const fetchGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/risk-intelligence/risk-subgraph/${contractId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      console.log('[ContractNetworkGraph] API Response:', response.data);

      // Handle both response formats:
      // MySQL fallback: {nodes, edges, ...}
      // Neo4j path: {subgraph: {nodes, edges}, ...}
      const raw = response.data;
      const graphData = (raw.subgraph?.nodes?.length > 0)
        ? raw.subgraph
        : (raw.nodes?.length > 0)
          ? raw
          : raw.subgraph || raw;

      console.log('[ContractNetworkGraph] Nodes count:', graphData?.nodes?.length || 0);
      console.log('[ContractNetworkGraph] Edges count:', graphData?.edges?.length || 0);
      setGraphData(graphData);
    } catch (err) {
      console.error('[ContractNetworkGraph] Error fetching graph data:', err);
      console.error('[ContractNetworkGraph] Error details:', err.response?.data);
      setError(err.response?.data?.error || 'Failed to load graph');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const handleExportGraph = () => {
    const dataStr = JSON.stringify(graphData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `contract_${contractId}_graph.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-300">Loading contract network graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-6">
        <h3 className="text-red-400 font-semibold mb-2">Error Loading Graph</h3>
        <p className="text-gray-300">{error}</p>
        <button
          onClick={fetchGraphData}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];

  console.log('[ContractNetworkGraph] graphData:', graphData);
  console.log('[ContractNetworkGraph] Rendering with nodes:', nodes.length, 'edges:', edges.length);
  if (nodes.length > 0) {
    console.log('[ContractNetworkGraph] First node:', nodes[0]);
  }
  if (edges.length > 0) {
    console.log('[ContractNetworkGraph] First edge:', edges[0]);
  }

  // Filter nodes based on search and type
  const filteredNodes = nodes.filter(node => {
    const matchesSearch = searchTerm === '' ||
      node.data.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter = filterType === 'all' || node.data.type === filterType;

    return matchesSearch && matchesFilter;
  });

  const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
  const filteredEdges = edges.filter(edge =>
    filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
  );

  console.log('[ContractNetworkGraph] After filtering - nodes:', filteredNodes.length, 'edges:', filteredEdges.length);

  // Calculate statistics
  const stats = {
    totalNodes: nodes.length,
    totalEdges: edges.length,
    nodeTypes: [...new Set(nodes.map(n => n.data?.type))].filter(Boolean),
    riskNodes: nodes.filter(n => n.data?.type === 'Risk').length,
    clauseNodes: nodes.filter(n => n.data?.type === 'Clause').length,
    obligationNodes: nodes.filter(n => n.data?.type === 'Obligation').length,
  };

  return (
    <div className="space-y-4">
      {/* Controls Panel */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search nodes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Filter by type */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              {stats.nodeTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={fetchGraphData}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              title="Refresh graph"
            >
              <RefreshCw className="w-4 h-4 text-gray-300" />
            </button>
            <button
              onClick={handleExportGraph}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              title="Export graph data"
            >
              <Download className="w-4 h-4 text-gray-300" />
            </button>
            <button
              onClick={() => setShowStats(!showStats)}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              title="Toggle statistics"
            >
              <Layers className="w-4 h-4 text-gray-300" />
            </button>
          </div>
        </div>

        {/* Statistics */}
        {showStats && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{stats.totalNodes}</div>
                <div className="text-xs text-gray-400">Total Nodes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{stats.totalEdges}</div>
                <div className="text-xs text-gray-400">Relationships</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">{stats.riskNodes}</div>
                <div className="text-xs text-gray-400">Risks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-400">{stats.obligationNodes}</div>
                <div className="text-xs text-gray-400">Obligations</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Graph Canvas */}
      <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
        <Neo4jGraphCanvas
          key={`graph-${contractId}-${filteredNodes.length}`}
          nodes={filteredNodes}
          edges={filteredEdges}
          onNodeClick={handleNodeClick}
          height="700px"
          showMiniMap={true}
          showControls={true}
          darkMode={true}
        />
      </div>

      {/* Node Details Panel */}
      {selectedNode && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-gray-100 mb-2">
                {selectedNode.data.label}
              </h3>
              <span className="px-3 py-1 bg-blue-900/50 text-blue-300 text-xs font-semibold rounded-full">
                {selectedNode.data.type}
              </span>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            {Object.entries(selectedNode.data).map(([key, value]) => {
              if (key === 'label' || key === 'type' || key === 'size') return null;
              return (
                <div key={key}>
                  <span className="text-gray-400 capitalize">{key}:</span>
                  <span className="text-gray-100 ml-2 font-semibold">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Connected nodes */}
          <div className="mt-4 pt-4 border-t border-gray-700">
            <h4 className="text-sm font-semibold text-gray-300 mb-2">Connected Nodes</h4>
            <div className="flex flex-wrap gap-2">
              {edges
                .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
                .map(edge => {
                  const connectedNodeId = edge.source === selectedNode.id ? edge.target : edge.source;
                  const connectedNode = nodes.find(n => n.id === connectedNodeId);
                  return connectedNode ? (
                    <span
                      key={edge.id}
                      className="px-2 py-1 bg-gray-700 text-gray-200 text-xs rounded cursor-pointer hover:bg-gray-600"
                      onClick={() => setSelectedNode(connectedNode)}
                    >
                      {connectedNode.data.label} ({edge.label || 'related'})
                    </span>
                  ) : null;
                })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractNetworkGraph;
