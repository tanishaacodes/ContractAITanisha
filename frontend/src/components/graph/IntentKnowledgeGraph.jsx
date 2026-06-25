import { useEffect, useRef, useState } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import { circular } from 'graphology-layout';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import { Network, ZoomIn, ZoomOut, Maximize2, RefreshCw, Filter, Search } from 'lucide-react';

/**
 * Neo4j-style Intent Knowledge Graph using Sigma.js
 * Shows Intents → Clauses → Parties → Risk relationships
 * Inspired by Neo4j GraphRAG contract visualization
 */
const IntentKnowledgeGraph = ({ heatmapData }) => {
  const containerRef = useRef(null);
  const sigmaRef = useRef(null);
  const graphRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [stats, setStats] = useState({ nodes: 0, edges: 0, intents: 0 });
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState('all'); // all, high, medium, low

  useEffect(() => {
    if (!containerRef.current || !heatmapData || !heatmapData.rows) return;

    // Create a new graph
    const graph = new Graph();
    graphRef.current = graph;

    // Build the knowledge graph
    buildIntentGraph(graph, heatmapData);

    // Apply circular layout first
    circular.assign(graph);

    // Then apply force-directed layout for better clustering
    const settings = forceAtlas2.inferSettings(graph);
    forceAtlas2.assign(graph, {
      iterations: 150,
      settings: {
        ...settings,
        gravity: 1.5,
        scalingRatio: 15,
        strongGravityMode: true,
        barnesHutOptimize: true,
      }
    });

    // Initialize Sigma
    const sigma = new Sigma(graph, containerRef.current, {
      renderEdgeLabels: false,
      defaultNodeColor: '#8D99AE',
      defaultEdgeColor: '#475569',
      labelFont: 'Inter, sans-serif',
      labelSize: 11,
      labelWeight: 'bold',
      labelColor: { color: '#E2E8F0' },
      enableEdgeEvents: true,
    });

    sigmaRef.current = sigma;

    // Update stats
    const intentCount = graph.filterNodes((node, attrs) => attrs.nodeType === 'Intent').length;
    setStats({
      nodes: graph.order,
      edges: graph.size,
      intents: intentCount,
    });

    // Event handlers
    sigma.on('clickNode', ({ node }) => {
      const nodeData = graph.getNodeAttributes(node);
      setSelectedNode({ id: node, ...nodeData });

      // Highlight connected nodes
      highlightNeighbors(graph, sigma, node);
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
      resetHighlight(graph, sigma);
    });

    // Cleanup
    return () => {
      if (sigmaRef.current) {
        sigmaRef.current.kill();
        sigmaRef.current = null;
      }
    };
  }, [heatmapData]);

  const buildIntentGraph = (graph, data) => {
    const intentNodes = new Map();
    const partyNodes = new Set();
    let intentIndex = 0;

    // Intent field names in the API response
    const intentFields = ['risk_transfer', 'liability_shielding', 'payment_control', 'termination_leverage', 'compliance_burden'];

    // Process each row (clause/section)
    data.rows.forEach((row, rowIndex) => {
      const clauseId = `clause-${rowIndex}`;

      // Build intents object from individual fields
      const intents = {};
      intentFields.forEach(field => {
        if (row[field] !== undefined) {
          intents[field] = row[field];
        }
      });

      // Add clause node
      const intentValues = Object.values(intents).filter(v => v > 0);
      const avgRisk = intentValues.length > 0
        ? intentValues.reduce((sum, val) => sum + val, 0) / intentValues.length
        : 0;

      const sectionName = row.section || row.clause_section || `Clause ${rowIndex + 1}`;

      graph.addNode(clauseId, {
        label: sectionName.length > 20 ? sectionName.substring(0, 20) + '...' : sectionName,
        fullName: sectionName,
        nodeType: 'Clause',
        size: 12 + avgRisk * 8,
        color: getClauseColor(avgRisk),
        metadata: {
          avg_risk: avgRisk,
          clause_id: row.clause_id,
        }
      });

      // Process each intent in this clause
      Object.entries(intents).forEach(([intent, riskScore]) => {
        if (riskScore > 0) {
          const intentId = `intent-${intent}`;

          // Add intent node if not exists
          if (!intentNodes.has(intentId)) {
            graph.addNode(intentId, {
              label: formatIntentName(intent),
              fullName: formatIntentName(intent),
              nodeType: 'Intent',
              size: 25,
              color: getIntentColor(intent),
              metadata: {
                intent_category: intent,
                total_clauses: 0,
              }
            });
            intentNodes.set(intentId, 0);
            intentIndex++;
          }

          // Increment clause count for this intent
          const currentCount = intentNodes.get(intentId);
          intentNodes.set(intentId, currentCount + 1);

          // Update the metadata with the new count
          const currentMetadata = graph.getNodeAttribute(intentId, 'metadata') || {};
          graph.setNodeAttribute(intentId, 'metadata', {
            ...currentMetadata,
            total_clauses: currentCount + 1,
          });

          // Add edge from intent to clause
          const edgeId = `${intentId}-${clauseId}`;
          if (!graph.hasEdge(edgeId)) {
            graph.addEdge(intentId, clauseId, {
              size: 1 + riskScore * 3,
              color: getRiskEdgeColor(riskScore),
              weight: riskScore,
              metadata: {
                risk_score: riskScore,
              }
            });
          }
        }
      });
    });

    // Add party nodes (YOUR_COMPANY vs COUNTERPARTY)
    const parties = ['YOUR_COMPANY', 'COUNTERPARTY'];
    parties.forEach((party, idx) => {
      const partyId = `party-${party}`;
      graph.addNode(partyId, {
        label: party.replace('_', ' '),
        fullName: party.replace('_', ' '),
        nodeType: 'Party',
        size: 30,
        color: party === 'YOUR_COMPANY' ? '#10B981' : '#F59E0B',
        metadata: {
          party_type: party,
        }
      });
    });

    // Connect high-risk clauses to counterparty, low-risk to your company
    graph.forEachNode((node, attrs) => {
      if (attrs.nodeType === 'Clause') {
        const avgRisk = attrs.metadata.avg_risk;
        const partyId = avgRisk > 0.5 ? 'party-COUNTERPARTY' : 'party-YOUR_COMPANY';

        const edgeId = `${node}-${partyId}`;
        if (!graph.hasEdge(edgeId)) {
          graph.addEdge(node, partyId, {
            size: 0.5,
            color: '#334155',
            weight: 0.3,
          });
        }
      }
    });

    // Add aggregate intent nodes if available
    if (data.aggregate_intents) {
      Object.entries(data.aggregate_intents).forEach(([intent, score]) => {
        const intentId = `intent-${intent}`;
        if (graph.hasNode(intentId)) {
          // Update size based on aggregate score
          graph.setNodeAttribute(intentId, 'size', 25 + score * 15);
        }
      });
    }
  };

  const formatIntentName = (intent) => {
    return intent
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  const getIntentColor = (intent) => {
    const colors = {
      risk_transfer: '#EF4444',        // Red
      liability_shielding: '#F59E0B',  // Orange
      payment_control: '#FBBF24',      // Yellow
      termination: '#DC2626',          // Dark Red
      compliance: '#8B5CF6',           // Purple
    };
    return colors[intent.toLowerCase()] || '#4C8EDA'; // Blue default
  };

  const getClauseColor = (riskScore) => {
    if (riskScore > 0.7) return '#DC2626';  // High risk - Red
    if (riskScore > 0.4) return '#F59E0B';  // Medium risk - Orange
    return '#10B981';                       // Low risk - Green
  };

  const getRiskEdgeColor = (riskScore) => {
    if (riskScore > 0.7) return '#EF4444';
    if (riskScore > 0.4) return '#FBBF24';
    return '#6EE7B7';
  };

  const highlightNeighbors = (graph, sigma, nodeId) => {
    const neighbors = new Set([nodeId]);
    graph.forEachNeighbor(nodeId, (neighbor) => {
      neighbors.add(neighbor);
    });

    graph.forEachNode((node, attrs) => {
      if (!neighbors.has(node)) {
        graph.setNodeAttribute(node, 'hidden', true);
      }
    });

    sigma.refresh();
  };

  const resetHighlight = (graph, sigma) => {
    graph.forEachNode((node) => {
      graph.setNodeAttribute(node, 'hidden', false);
    });
    sigma.refresh();
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
    if (graphRef.current && sigmaRef.current) {
      resetHighlight(graphRef.current, sigmaRef.current);
      setSelectedNode(null);
    }
  };

  const handleReLayout = () => {
    if (graphRef.current) {
      const settings = forceAtlas2.inferSettings(graphRef.current);
      forceAtlas2.assign(graphRef.current, {
        iterations: 150,
        settings: {
          ...settings,
          gravity: 1.5,
          scalingRatio: 15,
          strongGravityMode: true,
          barnesHutOptimize: true,
        }
      });
      sigmaRef.current?.refresh();
    }
  };

  const handleSearch = (term) => {
    setSearchTerm(term);
    if (!graphRef.current || !sigmaRef.current) return;

    if (!term) {
      resetHighlight(graphRef.current, sigmaRef.current);
      return;
    }

    const matchingNodes = new Set();
    graphRef.current.forEachNode((node, attrs) => {
      if (attrs.label?.toLowerCase().includes(term.toLowerCase()) ||
          attrs.fullName?.toLowerCase().includes(term.toLowerCase())) {
        matchingNodes.add(node);
        // Also include neighbors
        graphRef.current.forEachNeighbor(node, (neighbor) => {
          matchingNodes.add(neighbor);
        });
      }
    });

    graphRef.current.forEachNode((node) => {
      graphRef.current.setNodeAttribute(node, 'hidden', !matchingNodes.has(node));
    });

    sigmaRef.current.refresh();
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-purple-500/30 rounded-xl p-6 mt-6 shadow-2xl">
      {/* Header with Title & Search */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <Network className="w-6 h-6 text-purple-400" />
            Intent Knowledge Graph
            <span className="text-xs bg-purple-600/30 text-purple-300 px-2 py-1 rounded-full ml-2">
              Neo4j-inspired
            </span>
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Interactive network showing intent-clause-party relationships • Inspired by Neo4j GraphRAG
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 w-64"
          />
        </div>
      </div>

      {/* Stats Bar */}
      <div className="flex items-center gap-6 mb-4 text-sm bg-slate-800/50 rounded-lg p-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span className="text-slate-400">
            <span className="text-purple-400 font-semibold">{stats.intents}</span> Intents
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-500" />
          <span className="text-slate-400">
            <span className="text-cyan-400 font-semibold">{stats.nodes}</span> Total Nodes
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-slate-400">
            <span className="text-green-400 font-semibold">{stats.edges}</span> Relationships
          </span>
        </div>
      </div>

      <div className="relative" style={{ height: '700px' }}>
        {/* Sigma.js container */}
        <div
          ref={containerRef}
          style={{
            width: '100%',
            height: '100%',
            background: 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',
            borderRadius: '0.75rem',
            border: '1px solid rgba(139, 92, 246, 0.1)',
          }}
        />

        {/* Control buttons */}
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
          <button
            onClick={handleZoomIn}
            className="bg-slate-800/90 hover:bg-slate-700 text-white p-2.5 rounded-lg transition-all shadow-lg backdrop-blur-sm border border-slate-600/50"
            title="Zoom In"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          <button
            onClick={handleZoomOut}
            className="bg-slate-800/90 hover:bg-slate-700 text-white p-2.5 rounded-lg transition-all shadow-lg backdrop-blur-sm border border-slate-600/50"
            title="Zoom Out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          <button
            onClick={handleReset}
            className="bg-slate-800/90 hover:bg-slate-700 text-white p-2.5 rounded-lg transition-all shadow-lg backdrop-blur-sm border border-slate-600/50"
            title="Reset View"
          >
            <Maximize2 className="w-5 h-5" />
          </button>
          <button
            onClick={handleReLayout}
            className="bg-purple-600/90 hover:bg-purple-500 text-white p-2.5 rounded-lg transition-all shadow-lg backdrop-blur-sm"
            title="Re-apply Layout"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>

        {/* Legend */}
        <div className="absolute top-4 left-4 bg-slate-900/95 backdrop-blur-xl border border-purple-500/40 rounded-xl p-4 z-10 max-w-xs shadow-2xl">
          <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Network className="w-4 h-4 text-purple-400" />
            Graph Legend
          </h4>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-full bg-blue-500 border-2 border-blue-300" />
              <span className="text-xs text-slate-300">Intent Category</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-green-500" />
              <span className="text-xs text-slate-300">Low Risk Clause</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-red-500" />
              <span className="text-xs text-slate-300">High Risk Clause</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-green-600 border-2 border-green-400" />
              <span className="text-xs text-slate-300">Your Company</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-orange-500 border-2 border-orange-300" />
              <span className="text-xs text-slate-300">Counterparty</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700">
            <p className="text-xs text-slate-400">💡 Click node to highlight</p>
            <p className="text-xs text-slate-400">🖱️ Drag to pan</p>
            <p className="text-xs text-slate-400">⚙️ Scroll to zoom</p>
          </div>
        </div>

        {/* Hovered Node Tooltip */}
        {hoveredNode && (
          <div className="absolute bottom-4 right-4 bg-slate-900/98 backdrop-blur-xl border border-cyan-500/60 rounded-xl p-3 max-w-xs z-10 shadow-2xl">
            <div className="flex items-center gap-2 mb-1">
              <div
                className="w-3 h-3 rounded-full ring-2 ring-white/20"
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
          <div className="absolute bottom-4 left-4 bg-slate-900/98 backdrop-blur-xl border border-purple-500/40 rounded-xl p-4 max-w-sm z-10 shadow-2xl">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full ring-2 ring-purple-400/30"
                  style={{ backgroundColor: selectedNode.color }}
                />
                <h4 className="text-sm font-semibold text-white">{selectedNode.nodeType}</h4>
              </div>
              <button
                onClick={() => {
                  setSelectedNode(null);
                  resetHighlight(graphRef.current, sigmaRef.current);
                }}
                className="text-slate-400 hover:text-white transition-colors text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-sm text-white font-medium mb-2">
              {selectedNode.fullName || selectedNode.label}
            </p>

            {selectedNode.metadata && (
              <div className="space-y-1 mt-3 pt-3 border-t border-slate-700">
                {Object.entries(selectedNode.metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className="text-slate-200 font-medium">
                      {typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Graph Info Footer */}
      <div className="mt-4 text-xs text-slate-400 text-center space-y-1">
        <p>
          Powered by <span className="text-purple-400 font-semibold">Sigma.js</span> + <span className="text-cyan-400 font-semibold">ForceAtlas2</span> layout
        </p>
        <p className="text-slate-500">
          Inspired by <a href="https://neo4j.com/blog/developer/graphrag-in-action/" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 underline">Neo4j GraphRAG Contract Analysis</a>
        </p>
      </div>
    </div>
  );
};

export default IntentKnowledgeGraph;
