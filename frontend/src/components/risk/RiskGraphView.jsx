/**
 * Risk Graph Visualization
 * =========================
 * Neo4j risk subgraph visualization with SVG network diagram
 */

import React, { useState, useMemo } from 'react';
import { Network, AlertCircle, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

export default function RiskGraphView({ data }) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  console.log('[RiskGraphView] Received data:', data);

  if (!data || !data.subgraph) {
    console.log('[RiskGraphView] No subgraph - data:', data);
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
        <Network className="mx-auto text-gray-600 mb-4" size={48} />
        <p className="text-gray-400">No graph data available</p>
        <pre className="text-xs text-gray-500 mt-4 text-left max-w-2xl mx-auto overflow-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  const subgraph = data.subgraph;
  console.log('[RiskGraphView] subgraph:', subgraph);
  console.log('[RiskGraphView] subgraph.nodes:', subgraph.nodes);
  console.log('[RiskGraphView] subgraph.edges:', subgraph.edges);

  const nodes = subgraph.nodes || [];
  const edges = subgraph.edges || [];

  console.log('[RiskGraphView] Rendering:', nodes.length, 'nodes,', edges.length, 'edges');
  console.log('[RiskGraphView] nodes array:', nodes);
  console.log('[RiskGraphView] edges array:', edges);

  // Group nodes by type
  const clauseNodes = nodes.filter(n => n.type === 'Clause');
  const riskNodes = nodes.filter(n => n.type === 'Risk');

  // Calculate node positions (improved spread-out layout)
  const nodePositions = useMemo(() => {
    const width = 1200;  // Increased canvas size
    const height = 900;
    const positions = {};

    // Separate high-risk and low-risk nodes for better organization
    const highRiskNodes = riskNodes.filter(n =>
      n.severity === 'CRITICAL' || n.severity === 'HIGH'
    );
    const lowRiskNodes = riskNodes.filter(n =>
      n.severity === 'MEDIUM' || n.severity === 'LOW'
    );

    // Place clause nodes in outer ring with more spacing
    const clauseRadius = 350;
    clauseNodes.forEach((node, idx) => {
      const angle = (idx / clauseNodes.length) * 2 * Math.PI - Math.PI / 2; // Start from top
      positions[node.id] = {
        x: width / 2 + clauseRadius * Math.cos(angle),
        y: height / 2 + clauseRadius * Math.sin(angle),
        node
      };
    });

    // Place high-risk nodes in middle ring
    const highRiskRadius = 220;
    highRiskNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(highRiskNodes.length, 1)) * 2 * Math.PI - Math.PI / 2;
      positions[node.id] = {
        x: width / 2 + highRiskRadius * Math.cos(angle),
        y: height / 2 + highRiskRadius * Math.sin(angle),
        node
      };
    });

    // Place low-risk nodes in inner ring
    const lowRiskRadius = 120;
    lowRiskNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(lowRiskNodes.length, 1)) * 2 * Math.PI - Math.PI / 2;
      positions[node.id] = {
        x: width / 2 + lowRiskRadius * Math.cos(angle),
        y: height / 2 + lowRiskRadius * Math.sin(angle),
        node
      };
    });

    return positions;
  }, [nodes]);

  const getRiskColor = (score) => {
    if (score >= 0.7) return '#ef4444';
    if (score >= 0.5) return '#f97316';
    if (score >= 0.3) return '#eab308';
    return '#22c55e';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'CRITICAL': '#ef4444',
      'HIGH': '#f97316',
      'MEDIUM': '#eab308',
      'LOW': '#22c55e'
    };
    return colors[severity] || colors['MEDIUM'];
  };

  const getNodeColor = (node) => {
    if (node.type === 'Clause') {
      return getRiskColor(node.risk_score || 0.5);
    } else {
      return getSeverityColor(node.severity || 'MEDIUM');
    }
  };

  // Count multi-hop edges
  const multiHopEdges = edges.filter(e => e.multi_hop || (e.hops && e.hops > 1));
  const isMultiHopEnabled = data.subgraph?.multi_hop_enabled || multiHopEdges.length > 0;

  return (
    <div className="space-y-6">
      {/* Graph Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Total Nodes</p>
          <p className="text-3xl font-bold text-white">{nodes.length}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Clauses</p>
          <p className="text-3xl font-bold text-purple-400">{clauseNodes.length}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Risk Factors</p>
          <p className="text-3xl font-bold text-orange-400">{riskNodes.length}</p>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Total Edges</p>
          <p className="text-3xl font-bold text-blue-400">{edges.length}</p>
        </div>
        {isMultiHopEnabled && (
          <div className="bg-gradient-to-br from-orange-900/30 to-amber-900/30 border border-orange-700 rounded-lg p-4">
            <p className="text-orange-400 text-sm mb-2">Multi-hop Edges</p>
            <p className="text-3xl font-bold text-orange-300">{multiHopEdges.length}</p>
          </div>
        )}
      </div>

      {/* Interactive Graph Visualization */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Network className="mr-2 text-purple-400" size={20} />
            Network Graph Visualization
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setZoom(z => Math.min(z + 0.2, 3))}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded transition"
              title="Zoom In"
            >
              <ZoomIn size={16} />
            </button>
            <button
              onClick={() => setZoom(z => Math.max(z - 0.2, 0.3))}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded transition"
              title="Zoom Out"
            >
              <ZoomOut size={16} />
            </button>
            <button
              onClick={() => setZoom(1)}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded transition"
              title="Reset Zoom"
            >
              <Maximize2 size={16} />
            </button>
            <span className="px-3 py-2 bg-gray-700 rounded text-sm text-gray-300">
              {Math.round(zoom * 100)}%
            </span>
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg overflow-auto" style={{ height: '800px' }}>
          <svg
            width="1200"
            height="900"
            viewBox={`0 0 1200 900`}
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
          >
            {/* Draw edges */}
            <g>
              {edges.map((edge, idx) => {
                const source = nodePositions[edge.source];
                const target = nodePositions[edge.target];
                if (!source || !target) return null;

                // Highlight multi-hop edges
                const isMultiHop = edge.multi_hop || (edge.hops && edge.hops > 1);
                const strokeColor = isMultiHop ? '#f59e0b' : '#6b7280'; // Orange for multi-hop
                const strokeWidth = isMultiHop ? 2.5 : 1.5;
                const opacity = isMultiHop ? 0.7 : 0.4;
                const strokeDasharray = isMultiHop ? '8,4' : '0';

                return (
                  <g key={idx}>
                    <line
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      opacity={opacity}
                      strokeDasharray={strokeDasharray}
                    />
                    {/* Only show labels for multi-hop edges */}
                    {isMultiHop && edge.hops && (
                      <text
                        x={(source.x + target.x) / 2}
                        y={(source.y + target.y) / 2}
                        fill="#f59e0b"
                        fontSize="10"
                        textAnchor="middle"
                        fontWeight="bold"
                        style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}
                      >
                        {edge.hops}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>

            {/* Draw nodes */}
            <g>
              {Object.values(nodePositions).map(({ x, y, node }) => {
                const color = getNodeColor(node);
                const radius = node.type === 'Clause' ? 35 : 28;
                const isHighRisk = node.severity === 'CRITICAL' || node.severity === 'HIGH';

                return (
                  <g key={node.id}>
                    {/* Node shadow */}
                    <circle
                      cx={x}
                      cy={y}
                      r={radius}
                      fill={color}
                      opacity="0.15"
                      stroke={color}
                      strokeWidth="2"
                    />
                    {/* Main node */}
                    <circle
                      cx={x}
                      cy={y}
                      r={radius - 3}
                      fill={color}
                      opacity="0.3"
                      stroke={color}
                      strokeWidth={isHighRisk ? 3 : 2}
                    />
                    {/* Node label above */}
                    <text
                      x={x}
                      y={y - radius - 8}
                      fill="#ffffff"
                      fontSize="12"
                      textAnchor="middle"
                      fontWeight="bold"
                      style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}
                    >
                      {node.label.length > 15 ? node.label.substring(0, 12) + '...' : node.label}
                    </text>
                    {/* Node type label below */}
                    <text
                      x={x}
                      y={y + radius + 15}
                      fill="#9ca3af"
                      fontSize="9"
                      textAnchor="middle"
                      opacity="0.8"
                    >
                      {node.type}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-purple-500"></div>
            <span className="text-gray-300">Clause Nodes</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500"></div>
            <span className="text-gray-300">Risk Nodes</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-gray-500"></div>
            <span className="text-gray-300">Direct Edge</span>
          </div>
          <div className="flex items-center gap-2">
            <svg width="32" height="8">
              <line x1="0" y1="4" x2="32" y2="4" stroke="#f59e0b" strokeWidth="2" strokeDasharray="5,5" />
            </svg>
            <span className="text-gray-300">Multi-hop Edge</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">{edges.length} Total Edges</span>
          </div>
        </div>
      </div>

      {/* Clause Nodes */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white flex items-center">
          <Network className="mr-2 text-purple-400" size={20} />
          Clause Nodes
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clauseNodes.map((node) => (
            <div
              key={node.id}
              className={`border rounded-lg p-4 ${getRiskColor(node.risk_score)}`}
            >
              <p className="font-medium mb-2">{node.label}</p>
              <div className="text-xs space-y-1">
                <p>Risk Score: {(node.risk_score * 100).toFixed(0)}%</p>
                <p>Breach Probability: {(node.breach_probability * 100).toFixed(1)}%</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Nodes */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white flex items-center">
          <AlertCircle className="mr-2 text-orange-400" size={20} />
          Risk Factors
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {riskNodes.map((node) => (
            <div
              key={node.id}
              className={`border rounded-lg p-4 ${getSeverityColor(node.severity)}`}
            >
              <p className="font-medium mb-2">{node.label}</p>
              <div className="text-xs space-y-1">
                <p>Severity: {node.severity}</p>
                <p>Base Multiplier: {(node.base_multiplier || 0).toFixed(2)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Relationships */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">
          Relationships ({edges.length})
        </h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {edges.map((edge, idx) => (
            <div key={idx} className="flex items-center text-sm text-gray-300 border-b border-gray-700 pb-2">
              <span className="font-mono text-purple-400">{edge.source}</span>
              <span className="mx-2 text-gray-500">→</span>
              <span className="px-2 py-1 bg-gray-700 rounded text-xs mr-2">{edge.type}</span>
              <span className="font-mono text-orange-400">{edge.target}</span>
              <span className="ml-auto text-gray-500">Weight: {edge.weight?.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
