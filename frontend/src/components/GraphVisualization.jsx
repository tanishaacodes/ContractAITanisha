import { useState, useEffect } from 'react';
import Neo4jGraphCanvas from './graph/Neo4jGraphCanvas';

/**
 * Interactive Graph Visualization Component
 * Displays Neo4j clause evolution data as an interactive network graph
 * Now using Neo4j-style React Flow visualization
 */
export default function GraphVisualization({ data, onNodeClick }) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  useEffect(() => {
    if (!data) return;

    // Transform data into React Flow format
    const transformed = transformData(data);
    setGraphData(transformed);
  }, [data]);

  const transformData = (rawData) => {
    const nodes = [];
    const edges = [];

    if (!rawData || !rawData.nodes) return { nodes, edges };

    // Transform nodes to React Flow format
    rawData.nodes.forEach((node, index) => {
      const riskScore = node.risk_score || 0.5;
      const nodeSize = 50 + (riskScore * 50); // Size based on risk (50-100px)

      // Horizontal layout for version evolution
      const x = index * 300 + 200;
      const y = 300;

      // Determine node type based on risk level for color coding
      let nodeType;
      if (riskScore > 0.7) {
        nodeType = 'HighRisk'; // Red
      } else if (riskScore > 0.4) {
        nodeType = 'MediumRisk'; // Orange/Yellow
      } else {
        nodeType = 'LowRisk'; // Green
      }

      nodes.push({
        id: String(node.id),
        data: {
          label: `v${node.version}\n${(riskScore * 100).toFixed(0)}%`,
          type: nodeType, // Risk-based type for color
          size: nodeSize,
          version: node.version,
          risk_score: riskScore,
          text_preview: node.text_preview,
        },
        position: { x, y },
        type: 'neo4j',
      });
    });

    // Transform edges (evolution relationships)
    if (rawData.links) {
      rawData.links.forEach((link, index) => {
        edges.push({
          id: `e-${link.source}-${link.target}`,
          source: String(link.source),
          target: String(link.target),
          label: 'evolved',
          color: '#06B6D4', // Cyan for evolution
          width: 3,
          animated: true,
        });
      });
    }

    return { nodes, edges };
  };

  const getRiskColor = (score) => {
    if (score > 0.7) return '#dc2626'; // Red
    if (score > 0.4) return '#f59e0b'; // Yellow
    return '#10b981'; // Green
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node.data);
    if (onNodeClick) onNodeClick(node.data);
  };

  return (
    <div className="relative w-full h-full">
      {/* Neo4j-Style Graph */}
      <Neo4jGraphCanvas
        nodes={graphData.nodes}
        edges={graphData.edges}
        onNodeClick={handleNodeClick}
        height="100%"
        showMiniMap={true}
        showControls={true}
        darkMode={true}
      />

      {/* Selected Node Info */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 bg-slate-800/95 backdrop-blur-xl border border-cyan-500/30 rounded-xl p-4 max-w-sm z-10">
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getRiskColor(selectedNode.risk_score) }}
            />
            <h4 className="text-sm font-semibold text-white">Version {selectedNode.version}</h4>
          </div>
          <p className="text-xs text-slate-400 mb-2">
            Risk: {(selectedNode.risk_score * 100).toFixed(0)}%
          </p>
          {selectedNode.text_preview && (
            <p className="text-xs text-slate-300 line-clamp-3">{selectedNode.text_preview}</p>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-slate-800/95 backdrop-blur-xl border border-cyan-500/30 rounded-xl p-4 z-10">
        <h4 className="text-sm font-semibold text-white mb-2">Risk Levels</h4>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-xs text-slate-300">Low (0-40%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span className="text-xs text-slate-300">Medium (40-70%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-xs text-slate-300">High (70-100%)</span>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-slate-700">
          <p className="text-xs text-slate-400">Click to select node</p>
          <p className="text-xs text-slate-400">Drag to pan</p>
          <p className="text-xs text-slate-400">Scroll to zoom</p>
        </div>
      </div>
    </div>
  );
}
