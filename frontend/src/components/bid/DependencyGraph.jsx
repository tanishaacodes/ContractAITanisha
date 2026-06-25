/**
 * Dependency Graph Visualization
 * Interactive network graph showing task dependencies with risk coloring
 * Requires: npm install vis-network
 */
import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

// Dynamic import to handle SSR
let Network = null;
if (typeof window !== 'undefined') {
  try {
    const vis = require('vis-network');
    Network = vis.Network;
  } catch (error) {
    console.warn('vis-network not installed. Run: npm install vis-network');
  }
}

const DependencyGraph = ({ tenderId }) => {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

  useEffect(() => {
    if (tenderId) {
      loadGraph();
    }
  }, [tenderId]);

  useEffect(() => {
    if (graph && containerRef.current && Network) {
      renderGraph();
    }
  }, [graph]);

  const loadGraph = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(
        `${API_BASE}/api/tenders/${tenderId}/bid/dependency-graph/`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setGraph(response.data);
    } catch (err) {
      console.error('Failed to load graph:', err);
      setError('Failed to load dependency graph');
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (risk) => {
    if (risk > 0.7) return '#DC2626'; // Red
    if (risk > 0.5) return '#F59E0B'; // Orange
    if (risk > 0.3) return '#EAB308'; // Yellow
    return '#10B981'; // Green
  };

  const renderGraph = () => {
    if (!graph || !containerRef.current || !Network) return;

    // Clean up previous network
    if (networkRef.current) {
      networkRef.current.destroy();
    }

    // Transform nodes for vis-network
    const nodes = graph.nodes.map((node) => ({
      id: node.id,
      label: node.label,
      title: `<b>${node.label}</b><br/>Risk: ${(node.risk * 100).toFixed(0)}%<br/>Tasks: ${
        node.count
      }<br/>Est. Delay: ${node.delay} days`,
      color: {
        background: getNodeColor(node.risk),
        border: '#374151',
        highlight: {
          background: '#60A5FA',
          border: '#3B82F6'
        },
        hover: {
          background: getNodeColor(node.risk),
          border: '#60A5FA'
        }
      },
      font: {
        color: '#FFFFFF',
        size: 14,
        face: 'Inter, system-ui, sans-serif'
      },
      shape: 'box',
      margin: 10,
      borderWidth: 2,
      shadow: {
        enabled: true,
        color: 'rgba(0,0,0,0.3)',
        size: 5,
        x: 2,
        y: 2
      }
    }));

    // Transform edges
    const edges = graph.edges.map((edge) => ({
      from: edge.from,
      to: edge.to,
      arrows: {
        to: {
          enabled: true,
          scaleFactor: 1
        }
      },
      color: {
        color: '#6B7280',
        highlight: '#3B82F6',
        hover: '#60A5FA'
      },
      width: Math.max(1, edge.weight * 3),
      label: `${(edge.weight * 100).toFixed(0)}%`,
      font: {
        color: '#9CA3AF',
        size: 11,
        strokeWidth: 0,
        background: '#1E293B'
      },
      smooth: {
        enabled: true,
        type: 'cubicBezier',
        roundness: 0.5
      }
    }));

    const data = { nodes, edges };

    const options = {
      layout: {
        hierarchical: {
          direction: 'LR',
          sortMethod: 'directed',
          levelSeparation: 250,
          nodeSpacing: 150,
          treeSpacing: 200
        }
      },
      physics: {
        enabled: false
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
        navigationButtons: true,
        keyboard: true
      },
      nodes: {
        shapeProperties: {
          borderRadius: 6
        }
      }
    };

    networkRef.current = new Network(containerRef.current, data, options);

    // Event listeners
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = graph.nodes.find((n) => n.id === nodeId);
        setSelectedNode(node);
      } else {
        setSelectedNode(null);
      }
    });
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg p-12 border border-slate-700">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !graph) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="text-center text-red-400">
          {error || 'Failed to load graph'}
        </div>
      </div>
    );
  }

  if (!Network) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-4">
          <p className="text-yellow-400 mb-2">vis-network library not installed</p>
          <p className="text-slate-300 text-sm">
            Run: <code className="bg-slate-900 px-2 py-1 rounded">npm install vis-network</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white text-xl font-bold">Task Dependency Graph</h3>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-sm">
              {graph.nodes.length} Departments
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400 text-sm">
              {graph.edges.length} Dependencies
            </span>
          </div>
        </div>

        {/* Graph Container */}
        <div className="bg-slate-900 rounded-lg border border-slate-700 relative">
          <div
            ref={containerRef}
            style={{
              width: '100%',
              height: '600px'
            }}
          />

          {/* Selected Node Info */}
          {selectedNode && (
            <div className="absolute top-4 right-4 bg-slate-800 border border-slate-600 rounded-lg p-4 shadow-lg max-w-xs">
              <div className="text-white font-bold mb-2">{selectedNode.label}</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Risk:</span>
                  <span
                    className={`font-medium ${
                      selectedNode.risk > 0.7
                        ? 'text-red-400'
                        : selectedNode.risk > 0.5
                        ? 'text-orange-400'
                        : selectedNode.risk > 0.3
                        ? 'text-yellow-400'
                        : 'text-green-400'
                    }`}
                  >
                    {(selectedNode.risk * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Tasks:</span>
                  <span className="text-white">{selectedNode.count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Est. Delay:</span>
                  <span className="text-orange-400">{selectedNode.delay} days</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-600 rounded"></div>
            <span className="text-slate-300">High Risk (&gt;70%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-500 rounded"></div>
            <span className="text-slate-300">Medium Risk (50-70%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded"></div>
            <span className="text-slate-300">Low Risk (30-50%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-slate-300">Safe (&lt;30%)</span>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-4 bg-slate-700/50 rounded-lg p-3 text-sm text-slate-300">
          <p>
            <strong className="text-white">How to use:</strong> Click nodes to see details • Drag
            to pan • Scroll to zoom • Arrows show dependency direction
          </p>
        </div>
      </div>
    </div>
  );
};

export default DependencyGraph;
