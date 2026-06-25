import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Network, Loader2, AlertTriangle, Maximize2, Download, RefreshCw } from 'lucide-react';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import enterpriseRiskService from '../../services/enterpriseRiskService';

// Register the cose-bilkent layout for better node spacing
cytoscape.use(coseBilkent);

export default function ContractKnowledgeGraph() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || 'CONTRACT_X';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [graphElements, setGraphElements] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    loadGraphData();
  }, [contractId]);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      setError('');

      // Mock data for now - will connect to backend
      const mockGraphData = {
        nodes: [
          { data: { id: 'contract-1', label: 'Contract', type: 'Contract', value: '₹100M' } },
          { data: { id: 'supplier-1', label: 'Supplier A', type: 'Supplier', risk: 'HIGH' } },
          { data: { id: 'supplier-2', label: 'Supplier B', type: 'Supplier', risk: 'MEDIUM' } },
          { data: { id: 'country-1', label: 'India', type: 'Country', stability: 0.85 } },
          { data: { id: 'country-2', label: 'China', type: 'Country', stability: 0.65 } },
          { data: { id: 'commodity-1', label: 'Steel', type: 'Commodity', volatility: 0.3 } },
          { data: { id: 'liability-1', label: 'Unlimited Liability', type: 'Liability', amount: '₹50M' } },
          { data: { id: 'geo-risk-1', label: 'Political Instability', type: 'GeoPoliticalRisk', severity: 'HIGH' } },
          { data: { id: 'sanction-1', label: 'Trade Sanctions', type: 'Sanction', active: true } }
        ],
        edges: [
          { data: { source: 'contract-1', target: 'supplier-1', label: 'DEPENDS_ON' } },
          { data: { source: 'contract-1', target: 'supplier-2', label: 'DEPENDS_ON' } },
          { data: { source: 'supplier-1', target: 'country-1', label: 'LOCATED_IN' } },
          { data: { source: 'supplier-2', target: 'country-2', label: 'LOCATED_IN' } },
          { data: { source: 'contract-1', target: 'commodity-1', label: 'USES_COMMODITY' } },
          { data: { source: 'contract-1', target: 'liability-1', label: 'HAS_LIABILITY' } },
          { data: { source: 'country-2', target: 'geo-risk-1', label: 'HAS_GEO_RISK' } },
          { data: { source: 'country-2', target: 'sanction-1', label: 'HAS_SANCTION' } }
        ]
      };

      setGraphElements([...mockGraphData.nodes, ...mockGraphData.edges]);
    } catch (err) {
      setError(err.message || 'Failed to load graph data');
      console.error('Graph error:', err);
    } finally {
      setLoading(false);
    }
  };

  const cytoscapeStylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': '#06b6d4',
        'label': 'data(label)',
        'color': '#fff',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '12px',
        'width': '60px',
        'height': '60px',
        'border-width': '3px',
        'border-color': '#0891b2',
        'text-wrap': 'wrap',
        'text-max-width': '80px'
      }
    },
    {
      selector: 'node[type="Contract"]',
      style: {
        'background-color': '#8b5cf6',
        'border-color': '#7c3aed',
        'width': '80px',
        'height': '80px',
        'font-size': '14px',
        'font-weight': 'bold'
      }
    },
    {
      selector: 'node[type="Supplier"]',
      style: {
        'background-color': '#06b6d4',
        'border-color': '#0891b2'
      }
    },
    {
      selector: 'node[type="Country"]',
      style: {
        'background-color': '#10b981',
        'border-color': '#059669'
      }
    },
    {
      selector: 'node[type="Commodity"]',
      style: {
        'background-color': '#f59e0b',
        'border-color': '#d97706'
      }
    },
    {
      selector: 'node[type="Liability"]',
      style: {
        'background-color': '#ef4444',
        'border-color': '#dc2626'
      }
    },
    {
      selector: 'node[type="GeoPoliticalRisk"]',
      style: {
        'background-color': '#f97316',
        'border-color': '#ea580c'
      }
    },
    {
      selector: 'node[type="Sanction"]',
      style: {
        'background-color': '#dc2626',
        'border-color': '#b91c1c'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#475569',
        'target-arrow-color': '#475569',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': '10px',
        'color': '#94a3b8',
        'text-rotation': 'autorotate',
        'text-margin-y': -10
      }
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': '5px',
        'border-color': '#fbbf24',
        'background-color': '#f59e0b'
      }
    }
  ];

  const layout = {
    name: 'cose-bilkent',
    animate: true,
    animationDuration: 1000,
    // Quality of the layout
    quality: 'proof',
    // Node repulsion (default: 4500) - higher = more spacing
    nodeRepulsion: 45000,
    // Ideal edge length (default: 50) - higher = more spread out
    idealEdgeLength: 250,
    // Edge elasticity (default: 0.45)
    edgeElasticity: 0.45,
    // Nesting factor (default: 0.1)
    nestingFactor: 0.1,
    // Gravity force (default: 0.25) - lower = nodes spread more
    gravity: 0.15,
    // Number of iterations (default: 2500)
    numIter: 3500,
    // Whether to tile disconnected components
    tile: true,
    // Tile padding
    tilingPaddingVertical: 100,
    tilingPaddingHorizontal: 100,
    // Gravity range (default: 3.8)
    gravityRange: 3.8,
    // Gravity compound (default: 1.0)
    gravityCompound: 1.0,
    // Gravity range compound (default: 1.5)
    gravityRangeCompound: 1.5,
    // Initial cooling factor (default: 0.99)
    initialEnergyOnIncremental: 0.3,
    fit: true,
    padding: 100
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Loading Contract Knowledge Graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Error Loading Graph</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={loadGraphData}
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-semibold transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
              <Network className="w-8 h-8 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-blue-300">
                Contract Knowledge Graph
              </h1>
              <p className="text-slate-400 text-sm">Interactive Risk Relationship Visualization</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadGraphData}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all flex items-center gap-2 text-slate-300"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-semibold transition-all flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Graph Visualization */}
        <div className="lg:col-span-3">
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
            <div className="bg-slate-950 rounded-xl border border-slate-700 overflow-hidden" style={{ height: '700px' }}>
              <CytoscapeComponent
                elements={graphElements}
                stylesheet={cytoscapeStylesheet}
                layout={layout}
                style={{ width: '100%', height: '100%' }}
                cy={(cy) => {
                  cy.on('tap', 'node', (evt) => {
                    const node = evt.target;
                    setSelectedNode(node.data());
                  });
                }}
              />
            </div>
          </div>
        </div>

        {/* Node Details Panel */}
        <div className="lg:col-span-1">
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)] sticky top-6">
            <h3 className="text-xl font-bold text-white mb-4">Node Details</h3>

            {selectedNode ? (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Type</p>
                  <p className="text-lg font-bold text-cyan-400">{selectedNode.type}</p>
                </div>

                <div>
                  <p className="text-sm text-slate-400 mb-1">Label</p>
                  <p className="text-lg font-semibold text-white">{selectedNode.label}</p>
                </div>

                {Object.entries(selectedNode).map(([key, value]) => {
                  if (key !== 'id' && key !== 'label' && key !== 'type') {
                    return (
                      <div key={key}>
                        <p className="text-sm text-slate-400 mb-1 capitalize">{key}</p>
                        <p className="text-base font-medium text-white">{String(value)}</p>
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">Click on a node to view details</p>
            )}
          </div>

          {/* Legend */}
          <div className="mt-6 bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
            <h3 className="text-lg font-bold text-white mb-4">Legend</h3>
            <div className="space-y-3">
              {[
                { label: 'Contract', color: '#8b5cf6' },
                { label: 'Supplier', color: '#06b6d4' },
                { label: 'Country', color: '#10b981' },
                { label: 'Commodity', color: '#f59e0b' },
                { label: 'Liability', color: '#ef4444' },
                { label: 'Geo Risk', color: '#f97316' },
                { label: 'Sanction', color: '#dc2626' }
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full border-2"
                    style={{ backgroundColor: item.color, borderColor: item.color }}
                  />
                  <span className="text-sm text-slate-300">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
