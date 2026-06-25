import { useEffect, useRef, useState } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import { circular } from 'graphology-layout';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import { Network, ZoomIn, ZoomOut, Maximize2, RefreshCw } from 'lucide-react';

/**
 * EdgeQuake-style Playbook Knowledge Graph using Sigma.js
 * Shows playbooks, clauses, drift patterns, and community clusters
 */
const PlaybookKnowledgeGraph = ({ playbooksData, driftData }) => {
  const containerRef = useRef(null);
  const sigmaRef = useRef(null);
  const graphRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [stats, setStats] = useState({ nodes: 0, edges: 0, communities: 0 });

  useEffect(() => {
    if (!containerRef.current || !playbooksData) return;

    // Create a new graph
    const graph = new Graph();
    graphRef.current = graph;

    // Build the knowledge graph
    buildKnowledgeGraph(graph, playbooksData, driftData || []);

    // Apply circular layout first
    circular.assign(graph);

    // Then apply force-directed layout for better clustering
    const settings = forceAtlas2.inferSettings(graph);
    forceAtlas2.assign(graph, {
      iterations: 100,
      settings: {
        ...settings,
        gravity: 1,
        scalingRatio: 10,
        strongGravityMode: true,
      }
    });

    // Initialize Sigma
    const sigma = new Sigma(graph, containerRef.current, {
      renderEdgeLabels: true,
      defaultNodeColor: '#8D99AE',
      defaultEdgeColor: '#475569',
      labelFont: 'Inter, sans-serif',
      labelSize: 12,
      labelWeight: 'bold',
      labelColor: { color: '#E2E8F0' },
      edgeLabelFont: 'Inter, sans-serif',
      edgeLabelSize: 10,
      edgeLabelColor: { color: '#94A3B8' },
    });

    sigmaRef.current = sigma;

    // Update stats
    setStats({
      nodes: graph.order,
      edges: graph.size,
      communities: getCommunityCount(graph),
    });

    // Event handlers
    sigma.on('clickNode', ({ node }) => {
      const nodeData = graph.getNodeAttributes(node);
      setSelectedNode({ id: node, ...nodeData });
    });

    sigma.on('enterNode', ({ node }) => {
      const nodeData = graph.getNodeAttributes(node);
      setHoveredNode({ id: node, ...nodeData });
      containerRef.current.style.cursor = 'pointer';
    });

    sigma.on('leaveNode', () => {
      setHoveredNode(null);
      containerRef.current.style.cursor = 'default';
    });

    sigma.on('clickStage', () => {
      setSelectedNode(null);
    });

    // Cleanup
    return () => {
      if (sigmaRef.current) {
        sigmaRef.current.kill();
        sigmaRef.current = null;
      }
    };
  }, [playbooksData, driftData]);

  const buildKnowledgeGraph = (graph, playbooks, drifts) => {
    const communities = new Map();
    let communityId = 0;

    // Add playbook nodes (central hubs)
    playbooks.forEach((playbook, index) => {
      const community = playbook.clause_type || 'GENERAL';
      if (!communities.has(community)) {
        communities.set(community, communityId++);
      }

      graph.addNode(`playbook-${playbook.id}`, {
        label: playbook.name.length > 20 ? playbook.name.substring(0, 20) + '...' : playbook.name,
        fullName: playbook.name,
        nodeType: 'Playbook', // Changed from 'type' to 'nodeType' to avoid conflict
        size: 20 + (playbook.clause_count || 5) * 2, // Size based on clauses
        color: getPlaybookColor(playbook.clause_type),
        x: Math.cos((2 * Math.PI * index) / playbooks.length) * 100,
        y: Math.sin((2 * Math.PI * index) / playbooks.length) * 100,
        community: communities.get(community),
        metadata: {
          clause_type: playbook.clause_type,
          jurisdiction: playbook.jurisdiction,
          risk_tolerance: playbook.risk_tolerance,
        }
      });
    });

    // Add drift snapshot nodes (showing deviation patterns)
    const driftMap = new Map();
    drifts.forEach((drift, index) => {
      const driftId = `drift-${drift.id}`;
      const severity = drift.avg_similarity < 0.5 ? 'HIGH' : drift.avg_similarity < 0.7 ? 'MEDIUM' : 'LOW';

      graph.addNode(driftId, {
        label: `Drift\n${(drift.avg_similarity * 100).toFixed(0)}%`,
        nodeType: 'Drift', // Changed from 'type'
        size: 10 + (1 - drift.avg_similarity) * 20, // Larger = more drift
        color: getDriftColor(severity),
        x: Math.random() * 200 - 100,
        y: Math.random() * 200 - 100,
        severity,
        metadata: {
          avg_similarity: drift.avg_similarity,
          flagged_count: drift.flagged_count,
          snapshot_date: drift.snapshot_date,
        }
      });

      driftMap.set(drift.playbook_id, driftId);

      // Connect drift to playbook
      const playbookId = `playbook-${drift.playbook_id}`;
      if (graph.hasNode(playbookId)) {
        graph.addEdge(playbookId, driftId, {
          label: 'drift',
          size: 2,
          color: getDriftColor(severity),
          type: 'arrow',
        });
      }
    });

    // Add clause nodes (connected to playbooks via results)
    // For demo purposes, create synthetic clause nodes around each playbook
    playbooks.forEach((playbook, pIndex) => {
      const clauseCount = playbook.clause_count || 5;
      const playbookId = `playbook-${playbook.id}`;

      for (let i = 0; i < Math.min(clauseCount, 8); i++) {
        const clauseId = `clause-${playbook.id}-${i}`;
        const riskScore = 0.3 + Math.random() * 0.5;

        graph.addNode(clauseId, {
          label: `Clause ${i + 1}`,
          nodeType: 'Clause', // Changed from 'type'
          size: 8 + riskScore * 10,
          color: getClauseColor(riskScore),
          x: Math.cos((2 * Math.PI * pIndex) / playbooks.length) * 100 + Math.random() * 40 - 20,
          y: Math.sin((2 * Math.PI * pIndex) / playbooks.length) * 100 + Math.random() * 40 - 20,
          metadata: {
            risk_score: riskScore,
            playbook_id: playbook.id,
          }
        });

        // Connect clause to playbook
        graph.addEdge(playbookId, clauseId, {
          label: 'contains',
          size: 1,
          color: '#475569',
          type: 'arrow',
        });

        // Some clauses connect to drift nodes
        if (driftMap.has(playbook.id) && Math.random() > 0.5) {
          graph.addEdge(clauseId, driftMap.get(playbook.id), {
            label: 'deviates',
            size: 1.5,
            color: '#F59E0B',
            type: 'arrow',
          });
        }
      }
    });

    // Add community hub nodes (like EdgeQuake's entity clusters)
    communities.forEach((communityId, communityName) => {
      const hubId = `community-${communityId}`;
      graph.addNode(hubId, {
        label: communityName,
        nodeType: 'Community', // Changed from 'type'
        size: 25,
        color: getCommunityColor(communityId),
        x: Math.cos((2 * Math.PI * communityId) / communities.size) * 150,
        y: Math.sin((2 * Math.PI * communityId) / communities.size) * 150,
        metadata: {
          community_id: communityId,
          member_count: 0,
        }
      });

      // Connect playbooks to their community hub
      graph.forEachNode((node, attrs) => {
        if (attrs.type === 'Playbook' && attrs.community === communityId) {
          graph.addEdge(node, hubId, {
            label: 'belongs to',
            size: 0.5,
            color: '#334155',
            type: 'line',
          });
        }
      });
    });
  };

  const getPlaybookColor = (clauseType) => {
    const colors = {
      TERMINATION: '#F16667',      // Red
      INDEMNIFICATION: '#F79767',   // Orange
      CONFIDENTIALITY: '#9063CD',   // Purple
      PAYMENT: '#68BC00',           // Green
      LIABILITY: '#F59E0B',         // Yellow
      FORCE_MAJEURE: '#06B6D4',     // Cyan
      ARBITRATION: '#8B5CF6',       // Violet
      default: '#4C8EDA',           // Blue
    };
    return colors[clauseType] || colors.default;
  };

  const getDriftColor = (severity) => {
    const colors = {
      HIGH: '#DC2626',    // Red
      MEDIUM: '#F59E0B',  // Orange
      LOW: '#10B981',     // Green
    };
    return colors[severity] || colors.LOW;
  };

  const getClauseColor = (riskScore) => {
    if (riskScore > 0.7) return '#DC2626';  // High risk - Red
    if (riskScore > 0.4) return '#F59E0B';  // Medium risk - Orange
    return '#10B981';                       // Low risk - Green
  };

  const getCommunityColor = (communityId) => {
    const colors = ['#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#06B6D4', '#84CC16'];
    return colors[communityId % colors.length];
  };

  const getCommunityCount = (graph) => {
    const communities = new Set();
    graph.forEachNode((node, attrs) => {
      if (attrs.community !== undefined) {
        communities.add(attrs.community);
      }
    });
    return communities.size;
  };

  const handleZoomIn = () => {
    if (sigmaRef.current) {
      const camera = sigmaRef.current.getCamera();
      camera.animatedZoom({ duration: 300 });
    }
  };

  const handleZoomOut = () => {
    if (sigmaRef.current) {
      const camera = sigmaRef.current.getCamera();
      camera.animatedUnzoom({ duration: 300 });
    }
  };

  const handleReset = () => {
    if (sigmaRef.current) {
      const camera = sigmaRef.current.getCamera();
      camera.animatedReset({ duration: 300 });
    }
  };

  const handleReLayout = () => {
    if (graphRef.current) {
      // Re-apply force-directed layout
      const settings = forceAtlas2.inferSettings(graphRef.current);
      forceAtlas2.assign(graphRef.current, {
        iterations: 100,
        settings: {
          ...settings,
          gravity: 1,
          scalingRatio: 10,
          strongGravityMode: true,
        }
      });
      sigmaRef.current?.refresh();
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Network className="w-5 h-5 text-purple-400" />
          Playbook Knowledge Graph
          <span className="text-xs text-slate-400 font-normal ml-2">(EdgeQuake-style Sigma.js)</span>
        </h3>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm">
          <div className="text-slate-400">
            <span className="text-purple-400 font-semibold">{stats.nodes}</span> nodes
          </div>
          <div className="text-slate-400">
            <span className="text-cyan-400 font-semibold">{stats.edges}</span> edges
          </div>
          <div className="text-slate-400">
            <span className="text-green-400 font-semibold">{stats.communities}</span> communities
          </div>
        </div>
      </div>

      <div className="relative" style={{ height: '600px' }}>
        {/* Sigma.js container */}
        <div
          ref={containerRef}
          style={{ width: '100%', height: '100%', background: '#0F172A', borderRadius: '0.5rem' }}
        />

        {/* Control buttons */}
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
          <button
            onClick={handleZoomIn}
            className="bg-slate-700/90 hover:bg-slate-600 text-white p-2 rounded-lg transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="bg-slate-700/90 hover:bg-slate-600 text-white p-2 rounded-lg transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="bg-slate-700/90 hover:bg-slate-600 text-white p-2 rounded-lg transition-colors"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            onClick={handleReLayout}
            className="bg-purple-600/90 hover:bg-purple-500 text-white p-2 rounded-lg transition-colors"
            title="Re-apply Layout"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Legend */}
        <div className="absolute top-4 left-4 bg-slate-800/95 backdrop-blur-xl border border-purple-500/30 rounded-xl p-4 z-10 max-w-xs">
          <h4 className="text-sm font-semibold text-white mb-2">Node Types</h4>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500" />
              <span className="text-xs text-slate-300">Playbook Template</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-xs text-slate-300">Clause (Low Risk)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span className="text-xs text-slate-300">Drift Pattern</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-purple-500" />
              <span className="text-xs text-slate-300">Community Hub</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-700">
            <p className="text-xs text-slate-400">🖱️ Click: Select node</p>
            <p className="text-xs text-slate-400">🖱️ Drag: Pan view</p>
            <p className="text-xs text-slate-400">⚙️ Scroll: Zoom</p>
          </div>
        </div>

        {/* Hovered Node Tooltip */}
        {hoveredNode && (
          <div className="absolute bottom-4 right-4 bg-slate-900/95 backdrop-blur-xl border border-cyan-500/50 rounded-xl p-3 max-w-xs z-10 shadow-2xl">
            <div className="flex items-center gap-2 mb-1">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: hoveredNode.color }}
              />
              <h4 className="text-sm font-semibold text-white">{hoveredNode.nodeType}</h4>
            </div>
            <p className="text-xs text-white font-medium">
              {hoveredNode.fullName || hoveredNode.label}
            </p>
          </div>
        )}

        {/* Selected Node Info Panel */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 bg-slate-800/95 backdrop-blur-xl border border-purple-500/30 rounded-xl p-4 max-w-sm z-10 shadow-2xl">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: selectedNode.color }}
                />
                <h4 className="text-sm font-semibold text-white">{selectedNode.nodeType}</h4>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-white transition-colors text-xs"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-white font-medium mb-2">
              {selectedNode.fullName || selectedNode.label}
            </p>

            {selectedNode.metadata && (
              <div className="space-y-1 mt-3 pt-3 border-t border-slate-700">
                {Object.entries(selectedNode.metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-slate-400">{key.replace(/_/g, ' ')}:</span>
                    <span className="text-slate-200 font-medium">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {selectedNode.severity && (
              <div className="mt-2">
                <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                  selectedNode.severity === 'HIGH' ? 'bg-red-900/50 text-red-400' :
                  selectedNode.severity === 'MEDIUM' ? 'bg-yellow-900/50 text-yellow-400' :
                  'bg-green-900/50 text-green-400'
                }`}>
                  {selectedNode.severity} Severity
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Graph Info */}
      <div className="mt-4 text-xs text-slate-400 text-center">
        <p>Powered by <span className="text-purple-400 font-semibold">Sigma.js</span> + <span className="text-cyan-400 font-semibold">ForceAtlas2</span> layout algorithm</p>
        <p className="mt-1">Inspired by EdgeQuake's knowledge graph visualization</p>
      </div>
    </div>
  );
};

export default PlaybookKnowledgeGraph;
