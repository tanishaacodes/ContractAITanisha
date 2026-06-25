import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, RefreshCw, Search } from 'lucide-react';
import axios from 'axios';
import useAuthStore from '../store/authStore';

const RiskNetwork = () => {
  const [networkData, setNetworkData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [limit, setLimit] = useState(100);
  const { token } = useAuthStore();

  useEffect(() => {
    fetchNetworkData();
  }, [limit]);

  const fetchNetworkData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/risk/network?limit=${limit}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setNetworkData(response.data.data);
      }
    } catch (err) {
      console.error('Error fetching network data:', err);
      setError(err.response?.data?.error || 'Failed to load risk network');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskScore) => {
    if (riskScore >= 0.8) return '#dc2626'; // red-600
    if (riskScore >= 0.6) return '#ea580c'; // orange-600
    if (riskScore >= 0.3) return '#ca8a04'; // yellow-600
    return '#16a34a'; // green-600
  };

  const getRiskLevel = (riskScore) => {
    if (riskScore >= 0.8) return 'CRITICAL';
    if (riskScore >= 0.6) return 'HIGH';
    if (riskScore >= 0.3) return 'MEDIUM';
    return 'LOW';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading risk network...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
          <AlertTriangle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Error</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchNetworkData}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-3 rounded-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Risk Network Graph</h1>
              <p className="text-gray-600">Visualize cross-contract risk correlations</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-700">Show top:</label>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="border border-gray-300 rounded px-3 py-1.5"
              >
                <option value={50}>50 contracts</option>
                <option value={100}>100 contracts</option>
                <option value={200}>200 contracts</option>
              </select>
            </div>

            <button
              onClick={fetchNetworkData}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Nodes</p>
              <p className="text-2xl font-bold text-gray-900">{networkData.nodes.length}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Correlations</p>
              <p className="text-2xl font-bold text-gray-900">{networkData.edges.length}</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <Search className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">High Risk Nodes</p>
              <p className="text-2xl font-bold text-red-600">
                {networkData.nodes.filter(n => n.risk_score >= 0.6).length}
              </p>
            </div>
            <div className="bg-red-100 p-3 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Risk Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {(
                  networkData.nodes.reduce((sum, n) => sum + (n.risk_score || 0), 0) /
                  (networkData.nodes.length || 1)
                ).toFixed(2)}
              </p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-lg">
              <Shield className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Network Visualization Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Graph Area */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Network Graph</h3>

          {/* SVG Network Graph */}
          <div className="border border-gray-200 rounded-lg overflow-hidden" style={{ height: '600px' }}>
            <NetworkGraphSVG
              data={networkData}
              onNodeClick={setSelectedNode}
              selectedNode={selectedNode}
            />
          </div>

          <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-600 rounded-full"></div>
              <span className="text-gray-700">Critical (0.8+)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-orange-600 rounded-full"></div>
              <span className="text-gray-700">High (0.6-0.8)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-yellow-600 rounded-full"></div>
              <span className="text-gray-700">Medium (0.3-0.6)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-green-600 rounded-full"></div>
              <span className="text-gray-700">Low (&lt;0.3)</span>
            </div>
          </div>
        </div>

        {/* Details Panel */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Node Details</h3>

          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-600">Contract ID</label>
                <p className="font-mono text-sm text-gray-900 truncate">{selectedNode.id}</p>
              </div>

              <div>
                <label className="text-sm text-gray-600">Type</label>
                <p className="text-gray-900 capitalize">{selectedNode.type}</p>
              </div>

              {selectedNode.risk_score !== undefined && (
                <>
                  <div>
                    <label className="text-sm text-gray-600">Risk Score</label>
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${selectedNode.risk_score * 100}%`,
                            backgroundColor: getRiskColor(selectedNode.risk_score)
                          }}
                        ></div>
                      </div>
                      <span className="text-sm font-semibold">{selectedNode.risk_score.toFixed(2)}</span>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm text-gray-600">Risk Level</label>
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                        getRiskLevel(selectedNode.risk_score) === 'CRITICAL'
                          ? 'bg-red-100 text-red-800'
                          : getRiskLevel(selectedNode.risk_score) === 'HIGH'
                          ? 'bg-orange-100 text-orange-800'
                          : getRiskLevel(selectedNode.risk_score) === 'MEDIUM'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {getRiskLevel(selectedNode.risk_score)}
                    </span>
                  </div>
                </>
              )}

              <div>
                <label className="text-sm text-gray-600">Connections</label>
                <p className="text-gray-900">
                  {networkData.edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id).length}
                </p>
              </div>

              <button
                onClick={() => window.location.href = `/risk-analysis/${selectedNode.id}`}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 mt-4"
              >
                View Full Analysis
              </button>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <Shield className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p>Click on a node to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Simple SVG-based network graph component
const NetworkGraphSVG = ({ data, onNodeClick, selectedNode }) => {
  const width = 800;
  const height = 600;
  const centerX = width / 2;
  const centerY = height / 2;

  // Simple circular layout
  const nodePositions = data.nodes.map((node, index) => {
    const angle = (2 * Math.PI * index) / data.nodes.length;
    const radius = Math.min(width, height) * 0.35;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  });

  const getRiskColor = (riskScore) => {
    if (riskScore >= 0.8) return '#dc2626';
    if (riskScore >= 0.6) return '#ea580c';
    if (riskScore >= 0.3) return '#ca8a04';
    return '#16a34a';
  };

  return (
    <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
      {/* Edges */}
      <g>
        {data.edges.map((edge, index) => {
          const source = nodePositions.find(n => n.id === edge.source);
          const target = nodePositions.find(n => n.id === edge.target);
          if (!source || !target) return null;

          const opacity = edge.weight || 0.3;
          const strokeWidth = 1 + (edge.weight || 0.5) * 2;

          return (
            <line
              key={index}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="#94a3b8"
              strokeWidth={strokeWidth}
              opacity={opacity}
            />
          );
        })}
      </g>

      {/* Nodes */}
      <g>
        {nodePositions.map((node, index) => {
          const isSelected = selectedNode?.id === node.id;
          const radius = isSelected ? 10 : 7;
          const color = getRiskColor(node.risk_score || 0);

          return (
            <g key={index}>
              <circle
                cx={node.x}
                cy={node.y}
                r={radius}
                fill={color}
                stroke={isSelected ? '#1e40af' : '#fff'}
                strokeWidth={isSelected ? 3 : 2}
                style={{ cursor: 'pointer' }}
                onClick={() => onNodeClick(node)}
              />
              {isSelected && (
                <text
                  x={node.x}
                  y={node.y - radius - 5}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#1f2937"
                  fontWeight="600"
                >
                  {node.id.substring(0, 8)}...
                </text>
              )}
            </g>
          );
        })}
      </g>
    </svg>
  );
};

export default RiskNetwork;
