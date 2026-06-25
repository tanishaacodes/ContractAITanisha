import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, Network, Loader2, AlertTriangle, Download,
  RefreshCw, ChevronDown, Maximize2, X, Info,
  Package, Globe, Shield, TrendingUp, Zap, Link2
} from 'lucide-react';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import enterpriseRiskService from '../../services/enterpriseRiskService';

// Register cose-bilkent layout
cytoscape.use(coseBilkent);

// Node type config: color, icon label, glow
const NODE_TYPES = {
  Contract:        { color: '#a78bfa', border: '#7c3aed', glow: '#7c3aed', size: 90, emoji: '📄' },
  Supplier:        { color: '#22d3ee', border: '#0891b2', glow: '#06b6d4', size: 60, emoji: '🏭' },
  Country:         { color: '#34d399', border: '#059669', glow: '#10b981', size: 55, emoji: '🌍' },
  Commodity:       { color: '#fbbf24', border: '#d97706', glow: '#f59e0b', size: 55, emoji: '📦' },
  Liability:       { color: '#f87171', border: '#dc2626', glow: '#ef4444', size: 60, emoji: '⚠️' },
  GeoPoliticalRisk:{ color: '#fb923c', border: '#ea580c', glow: '#f97316', size: 50, emoji: '🌐' },
  Sanction:        { color: '#e879f9', border: '#a21caf', glow: '#d946ef', size: 50, emoji: '🚫' },
};

const EDGE_COLORS = {
  DEPENDS_ON:       '#22d3ee',
  LOCATED_IN:       '#34d399',
  HAS_GEO_RISK:     '#fb923c',
  HAS_SANCTION:     '#e879f9',
  USES_COMMODITY:   '#fbbf24',
  HAS_LIABILITY:    '#f87171',
};

export default function ContractKnowledgeGraph() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [graphElements, setGraphElements] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [availableContracts, setAvailableContracts] = useState([]);
  const [selectedContracts, setSelectedContracts] = useState([]);
  const [showContractDropdown, setShowContractDropdown] = useState(false);
  const [stats, setStats] = useState({ nodes: 0, edges: 0, suppliers: 0, countries: 0, risks: 0 });
  const cyRef = useRef(null);
  const timeoutRef = useRef(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    loadAvailableContracts();
  }, []);

  useEffect(() => {
    if (selectedContracts.length > 0) {
      loadGraphData();
    }
  }, [selectedContracts]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowContractDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (cyRef.current && !cyRef.current.destroyed()) {
        try { cyRef.current.destroy(); } catch {}
      }
    };
  }, []);

  const getContractDisplayName = (contract) => {
    if (!contract) return 'Unknown';
    return contract.title || contract.name || contract.filename
      || (contract.counterparty ? `${contract.counterparty}` : null)
      || `Contract ${contract.id?.substring(0, 8)}`;
  };

  const loadAvailableContracts = async () => {
    try {
      const portfolio = await enterpriseRiskService.getPortfolioContracts();
      if (portfolio.contracts && portfolio.contracts.length > 0) {
        setAvailableContracts(portfolio.contracts);
        if (contractId) {
          const match = portfolio.contracts.find(c => c.id === contractId);
          setSelectedContracts(match ? [contractId] : [portfolio.contracts[0].id]);
        } else {
          setSelectedContracts([portfolio.contracts[0].id]);
        }
      } else {
        setError('No contracts found. Please upload a contract first to view the Knowledge Graph.');
        setLoading(false);
      }
    } catch (err) {
      setError(err.message || 'Failed to load contracts');
      setLoading(false);
    }
  };

  const loadGraphData = async () => {
    try {
      setLoading(true);
      setError('');
      setSelectedNode(null);

      const allNodes = [];
      const allEdges = [];
      const nodeIds = new Set();

      for (const cId of selectedContracts) {
        const graphData = await enterpriseRiskService.getContractGraph(cId);

        graphData.nodes.forEach(n => {
          const node = n.data ? n : { data: n };
          if (!nodeIds.has(node.data.id)) {
            nodeIds.add(node.data.id);
            // Enrich: add type-based size and color info into data
            const typeConf = NODE_TYPES[node.data.type] || NODE_TYPES.Contract;
            allNodes.push({
              data: { ...node.data, _color: typeConf.color, _size: typeConf.size }
            });
          }
        });

        graphData.edges.forEach(e => {
          const edge = e.data ? e : { data: e };
          const edgeColor = EDGE_COLORS[edge.data.label] || '#64748b';
          allEdges.push({ data: { ...edge.data, _color: edgeColor } });
        });
      }

      // Compute stats
      const nodeTypes = allNodes.map(n => n.data.type);
      setStats({
        nodes: allNodes.length,
        edges: allEdges.length,
        suppliers: nodeTypes.filter(t => t === 'Supplier').length,
        countries: nodeTypes.filter(t => t === 'Country').length,
        risks: nodeTypes.filter(t => t === 'GeoPoliticalRisk' || t === 'Sanction' || t === 'Liability').length,
      });

      setGraphElements([...allNodes, ...allEdges]);
    } catch (err) {
      setError(err.message || 'Failed to load graph data');
    } finally {
      setLoading(false);
    }
  };

  const toggleContractSelection = (id) => {
    setSelectedContracts(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const fitGraphToScreen = () => {
    if (cyRef.current && !cyRef.current.destroyed()) {
      cyRef.current.fit(undefined, 60);
      cyRef.current.center();
    }
  };

  // ── Stunning Cytoscape stylesheet ──────────────────────────────────────────
  const cytoscapeStylesheet = [
    // Default node
    {
      selector: 'node',
      style: {
        'background-color': 'data(_color)',
        'label': 'data(label)',
        'color': '#ffffff',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '11px',
        'font-weight': '600',
        'font-family': 'Inter, system-ui, sans-serif',
        'width': 'data(_size)',
        'height': 'data(_size)',
        'border-width': '3px',
        'border-color': '#ffffff22',
        'text-wrap': 'wrap',
        'text-max-width': '75px',
        'overlay-padding': '6px',
        'shadow-blur': '20px',
        'shadow-color': 'data(_color)',
        'shadow-opacity': 0.7,
        'shadow-offset-x': 0,
        'shadow-offset-y': 0,
      }
    },
    // Contract node — largest, violet glow
    {
      selector: 'node[type="Contract"]',
      style: {
        'background-color': '#a78bfa',
        'border-color': '#7c3aed',
        'border-width': '4px',
        'width': 90,
        'height': 90,
        'font-size': '12px',
        'font-weight': '700',
        'color': '#fff',
        'shadow-color': '#7c3aed',
        'shadow-blur': 30,
        'shadow-opacity': 0.9,
      }
    },
    {
      selector: 'node[type="Supplier"]',
      style: {
        'background-color': '#22d3ee',
        'border-color': '#0891b2',
        'shadow-color': '#06b6d4',
        'shadow-blur': 18,
        'shadow-opacity': 0.7,
      }
    },
    {
      selector: 'node[type="Country"]',
      style: {
        'background-color': '#34d399',
        'border-color': '#059669',
        'shadow-color': '#10b981',
        'shadow-blur': 18,
        'shadow-opacity': 0.7,
      }
    },
    {
      selector: 'node[type="Commodity"]',
      style: {
        'background-color': '#fbbf24',
        'border-color': '#d97706',
        'color': '#1a1a2e',
        'shadow-color': '#f59e0b',
        'shadow-blur': 18,
        'shadow-opacity': 0.7,
      }
    },
    {
      selector: 'node[type="Liability"]',
      style: {
        'background-color': '#f87171',
        'border-color': '#dc2626',
        'shadow-color': '#ef4444',
        'shadow-blur': 22,
        'shadow-opacity': 0.8,
      }
    },
    {
      selector: 'node[type="GeoPoliticalRisk"]',
      style: {
        'background-color': '#fb923c',
        'border-color': '#ea580c',
        'shadow-color': '#f97316',
        'shadow-blur': 20,
        'shadow-opacity': 0.75,
      }
    },
    {
      selector: 'node[type="Sanction"]',
      style: {
        'background-color': '#e879f9',
        'border-color': '#a21caf',
        'shadow-color': '#d946ef',
        'shadow-blur': 20,
        'shadow-opacity': 0.8,
      }
    },
    // Selected node
    {
      selector: 'node:selected',
      style: {
        'border-width': '5px',
        'border-color': '#fbbf24',
        'shadow-color': '#fbbf24',
        'shadow-blur': 40,
        'shadow-opacity': 1,
        'overlay-opacity': 0.1,
        'overlay-color': '#fbbf24',
      }
    },
    // Default edge
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': 'data(_color)',
        'target-arrow-color': 'data(_color)',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 1.2,
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': '9px',
        'font-weight': '600',
        'color': '#94a3b8',
        'font-family': 'Inter, system-ui, sans-serif',
        'text-rotation': 'autorotate',
        'text-margin-y': -8,
        'text-background-color': '#0f172a',
        'text-background-opacity': 0.85,
        'text-background-padding': '2px',
        'text-background-shape': 'roundrectangle',
        'line-opacity': 0.85,
        'overlay-padding': '4px',
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'width': 3.5,
        'line-opacity': 1,
        'overlay-opacity': 0.05,
        'overlay-color': '#fbbf24',
      }
    },
  ];

  const layout = {
    name: 'cose-bilkent',
    quality: 'proof',
    nodeRepulsion: 50000,
    idealEdgeLength: 300,
    edgeElasticity: 0.45,
    nestingFactor: 0.1,
    gravity: 0.1,
    numIter: 5000,
    tile: true,
    tilingPaddingVertical: 150,
    tilingPaddingHorizontal: 150,
    gravityRange: 3.8,
    gravityCompound: 1.0,
    gravityRangeCompound: 1.5,
    initialEnergyOnIncremental: 0.3,
    animate: 'end',
    animationDuration: 1000,
    fit: true,
    padding: 120,
    randomize: false,
  };

  // ── Loading state ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <div className="relative mx-auto mb-6 w-20 h-20">
            <div className="absolute inset-0 rounded-full border-4 border-violet-500/20 animate-ping" />
            <div className="absolute inset-2 rounded-full border-4 border-cyan-400/30 animate-pulse" />
            <Network className="w-8 h-8 text-cyan-400 absolute inset-0 m-auto" />
          </div>
          <p className="text-white font-bold text-xl mb-1">Building Knowledge Graph</p>
          <p className="text-slate-400 text-sm">Mapping contracts · suppliers · countries · risks</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Graph Error</h2>
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

  const selectedContractObj = availableContracts.find(c => c.id === selectedContracts[0]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-[#0d1425] to-slate-900 p-6">

      {/* ── Header ── */}
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-violet-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-violet-500/30 shadow-[0_0_20px_rgba(139,92,246,0.3)]">
              <Network className="w-8 h-8 text-violet-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-violet-200 to-cyan-300">
                Contract Knowledge Graph
              </h1>
              <p className="text-slate-400 text-sm">
                {selectedContracts.length === 1 && selectedContractObj
                  ? getContractDisplayName(selectedContractObj)
                  : `${selectedContracts.length} contract${selectedContracts.length !== 1 ? 's' : ''} visualized`
                } · Interactive Risk Relationship Map
              </p>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={loadGraphData}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-violet-500/50 transition-all flex items-center gap-2 text-slate-300 text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={fitGraphToScreen}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all flex items-center gap-2 text-slate-300 text-sm"
          >
            <Maximize2 className="w-4 h-4" />
            Fit View
          </button>
        </div>
      </div>

      {/* ── Stats Bar + Contract Selector row ── */}
      <div className="mb-5 flex items-center gap-4 flex-wrap">

        {/* Contract Selector — positioned ABOVE graph, no z-index battle */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowContractDropdown(prev => !prev)}
            className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-800/90 border border-violet-500/40 hover:border-violet-400/70 backdrop-blur-xl transition-all shadow-[0_0_15px_rgba(139,92,246,0.2)] min-w-[240px]"
          >
            <Network className="w-4 h-4 text-violet-400 flex-shrink-0" />
            <span className="text-sm font-semibold text-white truncate flex-1 text-left">
              {selectedContracts.length === 0
                ? 'Select contracts…'
                : selectedContracts.length === 1
                ? getContractDisplayName(availableContracts.find(c => c.id === selectedContracts[0]))
                : `${selectedContracts.length} contracts selected`}
            </span>
            <ChevronDown className={`w-4 h-4 text-violet-400 flex-shrink-0 transition-transform ${showContractDropdown ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown rendered inline, uses z-[200] which is above the Cytoscape canvas */}
          {showContractDropdown && (
            <div
              className="absolute top-full left-0 mt-2 bg-slate-900 border-2 border-violet-500/50 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.8)] overflow-hidden"
              style={{ zIndex: 9999, minWidth: '280px', maxWidth: '360px' }}
            >
              <div className="p-3 border-b border-slate-700/60">
                <div className="flex gap-2 mb-2">
                  <button
                    onClick={() => { setSelectedContracts(availableContracts.map(c => c.id)); setShowContractDropdown(false); }}
                    className="flex-1 px-3 py-1.5 text-xs bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 rounded-lg transition-all font-semibold"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => setSelectedContracts([])}
                    className="flex-1 px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-all font-semibold"
                  >
                    Clear All
                  </button>
                </div>
                <p className="text-xs text-slate-500 text-center">
                  {availableContracts.length} contract{availableContracts.length !== 1 ? 's' : ''} available
                </p>
              </div>
              <div className="max-h-72 overflow-y-auto">
                {availableContracts.map((contract) => {
                  const isSelected = selectedContracts.includes(contract.id);
                  const name = getContractDisplayName(contract);
                  return (
                    <button
                      key={contract.id}
                      onClick={() => toggleContractSelection(contract.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-all border-b border-slate-700/40 last:border-0 ${
                        isSelected
                          ? 'bg-violet-500/20 hover:bg-violet-500/25'
                          : 'hover:bg-slate-800'
                      }`}
                    >
                      <div className={`w-4 h-4 rounded border-2 flex-shrink-0 flex items-center justify-center transition-all ${
                        isSelected
                          ? 'bg-violet-500 border-violet-400'
                          : 'border-slate-600'
                      }`}>
                        {isSelected && <div className="w-2 h-2 bg-white rounded-sm" />}
                      </div>
                      <span className={`text-sm truncate ${isSelected ? 'text-white font-semibold' : 'text-slate-300'}`}>
                        {name}
                      </span>
                      {isSelected && (
                        <span className="ml-auto text-xs text-violet-400 font-bold flex-shrink-0">✓</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Stats pills */}
        {[
          { icon: Link2,    label: 'Nodes',     val: stats.nodes,     color: 'text-cyan-400',    bg: 'bg-cyan-500/10 border-cyan-500/20' },
          { icon: Network,  label: 'Edges',     val: stats.edges,     color: 'text-violet-400',  bg: 'bg-violet-500/10 border-violet-500/20' },
          { icon: Package,  label: 'Suppliers', val: stats.suppliers, color: 'text-amber-400',   bg: 'bg-amber-500/10 border-amber-500/20' },
          { icon: Globe,    label: 'Countries', val: stats.countries, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
          { icon: Zap,      label: 'Risks',     val: stats.risks,     color: 'text-red-400',     bg: 'bg-red-500/10 border-red-500/20' },
        ].map(({ icon: Icon, label, val, color, bg }) => (
          <div key={label} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border ${bg} backdrop-blur-xl`}>
            <Icon className={`w-4 h-4 ${color}`} />
            <span className={`text-lg font-black ${color}`}>{val}</span>
            <span className="text-xs text-slate-400 font-medium">{label}</span>
          </div>
        ))}
      </div>

      {/* ── Main grid: Graph + Side Panel ── */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">

        {/* Graph Canvas */}
        <div className="lg:col-span-3">
          <div className="relative bg-gradient-to-br from-slate-900/80 to-[#0d1425]/80 backdrop-blur-xl border border-violet-500/20 rounded-2xl shadow-[0_0_50px_rgba(139,92,246,0.15)] overflow-hidden">
            {/* Top bar */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/50">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="ml-3 text-xs text-slate-500 font-mono">contract-knowledge-graph · live</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs text-emerald-400 font-semibold">LIVE</span>
              </div>
            </div>

            {/* The graph */}
            <div className="bg-[#060d1a]" style={{ height: '660px' }}>
              {graphElements.length > 0 ? (
                <CytoscapeComponent
                  key={`graph-${selectedContracts.join('-')}`}
                  elements={graphElements}
                  stylesheet={cytoscapeStylesheet}
                  layout={layout}
                  style={{ width: '100%', height: '100%', background: 'transparent' }}
                  cy={(cy) => {
                    if (!cy) return;
                    if (timeoutRef.current) clearTimeout(timeoutRef.current);
                    cyRef.current = cy;

                    cy.on('tap', 'node', (evt) => {
                      setSelectedNode(evt.target.data());
                    });
                    cy.on('tap', (evt) => {
                      if (evt.target === cy) setSelectedNode(null);
                    });

                    try { cy.fit(undefined, 60); cy.center(); } catch {}
                  }}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Network className="w-16 h-16 text-slate-700 mx-auto mb-4" />
                    <p className="text-slate-500">No graph data — select a contract above</p>
                  </div>
                </div>
              )}
            </div>

            {/* Bottom hint */}
            <div className="px-5 py-2 border-t border-slate-700/50 flex items-center gap-6">
              <p className="text-xs text-slate-600">Click node to inspect · Scroll to zoom · Drag to pan</p>
              <button
                onClick={fitGraphToScreen}
                className="ml-auto text-xs text-violet-400 hover:text-violet-300 transition-colors flex items-center gap-1"
              >
                <Maximize2 className="w-3 h-3" /> Fit to screen
              </button>
            </div>
          </div>
        </div>

        {/* Side Panel */}
        <div className="lg:col-span-1 space-y-4">

          {/* Node Inspector */}
          <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-5 shadow-[0_0_30px_rgba(139,92,246,0.12)]">
            <div className="flex items-center gap-2 mb-4">
              <Info className="w-4 h-4 text-violet-400" />
              <h3 className="text-base font-bold text-white">Node Inspector</h3>
            </div>

            {selectedNode ? (
              <div className="space-y-3">
                {/* Type badge */}
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: NODE_TYPES[selectedNode.type]?.color || '#64748b' }}
                  />
                  <span
                    className="text-xs font-black uppercase tracking-widest px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: (NODE_TYPES[selectedNode.type]?.color || '#64748b') + '22',
                      color: NODE_TYPES[selectedNode.type]?.color || '#64748b',
                    }}
                  >
                    {selectedNode.type}
                  </span>
                </div>

                {/* Label */}
                <div>
                  <p className="text-xs text-slate-500 mb-0.5">Label</p>
                  <p className="text-sm font-bold text-white break-words">{selectedNode.label}</p>
                </div>

                {/* Extra fields */}
                {Object.entries(selectedNode).map(([key, value]) => {
                  if (['id', 'label', 'type', '_color', '_size'].includes(key) || !value) return null;
                  return (
                    <div key={key} className="border-t border-slate-700/50 pt-2">
                      <p className="text-xs text-slate-500 mb-0.5 capitalize">{key.replace(/_/g, ' ')}</p>
                      <p className="text-sm font-semibold text-slate-200 break-words">{String(value)}</p>
                    </div>
                  );
                })}

                <button
                  onClick={() => setSelectedNode(null)}
                  className="mt-2 w-full text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center justify-center gap-1"
                >
                  <X className="w-3 h-3" /> Clear selection
                </button>
              </div>
            ) : (
              <div className="text-center py-8">
                <Network className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">Click any node in the graph to inspect its details</p>
              </div>
            )}
          </div>

          {/* Legend */}
          <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-5 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
            <h3 className="text-base font-bold text-white mb-4">Node Types</h3>
            <div className="space-y-2.5">
              {Object.entries(NODE_TYPES).map(([type, conf]) => (
                <div key={type} className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full flex-shrink-0 shadow-lg"
                    style={{ backgroundColor: conf.color, boxShadow: `0 0 8px ${conf.glow}88` }}
                  />
                  <span className="text-sm text-slate-300">{type}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Relationship legend */}
          <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-5 shadow-[0_0_20px_rgba(6,182,212,0.1)]">
            <h3 className="text-base font-bold text-white mb-4">Relationships</h3>
            <div className="space-y-2">
              {Object.entries(EDGE_COLORS).map(([rel, color]) => (
                <div key={rel} className="flex items-center gap-3">
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <div className="w-6 h-0.5 rounded" style={{ backgroundColor: color }} />
                    <div
                      className="w-0 h-0"
                      style={{
                        borderTop: '4px solid transparent',
                        borderBottom: '4px solid transparent',
                        borderLeft: `6px solid ${color}`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-slate-400 font-mono">{rel.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
