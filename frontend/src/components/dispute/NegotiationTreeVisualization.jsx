/**
 * NegotiationTreeVisualization.jsx
 * ==================================
 * ReactFlow-based MCTS Negotiation Tree Visualization
 * Shows top 2 levels of the decision tree clearly — root + 11 immediate children
 */

import { useState, useEffect, useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { Maximize, Minimize } from "lucide-react";

// Custom Node Component
const NegotiationNode = ({ data }) => {
  const risk = data.disputeRisk ?? 50;
  const isOptimal = data.isOptimal;
  const isRoot = data.nodeType === 'Root';

  const color = risk < 40 ? '#10b981' : risk < 60 ? '#f59e0b' : risk < 75 ? '#f97316' : '#ef4444';
  const bg = isRoot ? '#1e40af' : isOptimal ? '#14532d' : '#1e293b';
  const border = isOptimal ? '#10b981' : isRoot ? '#3b82f6' : '#334155';

  return (
    <div style={{
      background: bg,
      border: `2px solid ${border}`,
      borderRadius: 10,
      padding: '12px 16px',
      minWidth: 180,
      boxShadow: isOptimal ? `0 0 16px #10b98150` : isRoot ? `0 0 12px #3b82f640` : 'none',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ color: '#94a3b8', fontSize: 10, fontWeight: 600 }}>
          {isRoot ? '🌳 ROOT' : isOptimal ? '⭐ OPTIMAL' : `Level ${data.level}`}
        </span>
        <span style={{ color: '#64748b', fontSize: 10 }}>{data.visits} visits</span>
      </div>

      {/* Action */}
      {data.action && data.action !== 'Root' && (
        <div style={{ color: '#93c5fd', fontSize: 11, fontWeight: 600, marginBottom: 8,
          background: '#1e3a5f', borderRadius: 4, padding: '2px 8px', display: 'inline-block' }}>
          {data.action.replace(/_/g, ' ')}
        </div>
      )}

      {/* Dispute Risk — main metric */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ color: '#94a3b8', fontSize: 11 }}>Dispute Risk</span>
        <span style={{ color, fontSize: 18, fontWeight: 700 }}>{risk}%</span>
      </div>

      {/* Commercial Value */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#94a3b8', fontSize: 11 }}>Comm. Value</span>
        <span style={{ color: '#10b981', fontSize: 13, fontWeight: 600 }}>
          ${((data.commercialValue || 0) / 1e6).toFixed(1)}M
        </span>
      </div>

      {/* State quick-view */}
      {data.state && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #334155',
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {[
            ['Price', data.state.price],
            ['Days', data.state.delivery_days],
            ['Liab', `${((data.state.liability_cap || 0) * 100).toFixed(0)}%`],
            ['Pay', `${data.state.payment_terms}d`],
          ].map(([k, v]) => (
            <div key={k} style={{ color: '#64748b', fontSize: 10 }}>
              {k}: <span style={{ color: '#e2e8f0' }}>{v}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const nodeTypes = { negotiationNode: NegotiationNode };

const defaultEdgeOptions = {
  type: 'smoothstep',
  markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: '#475569' },
  style: { strokeWidth: 1.5, stroke: '#475569' },
  animated: false,
};

export default function NegotiationTreeVisualization({ treeData, onNodeClick }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);
  // How many levels to show: start at 2 (root + children)
  const [maxLevel, setMaxLevel] = useState(2);

  const buildFlowGraph = useCallback((data, levelLimit) => {
    if (!data?.nodes?.length) return { nodes: [], edges: [] };

    // Filter to maxLevel
    const visibleNodes = data.nodes.filter(n => (n.level ?? 0) < levelLimit);
    const visibleIds = new Set(visibleNodes.map(n => n.id));

    // Find optimal child (highest visits at level 1)
    const level1 = visibleNodes.filter(n => (n.level ?? 0) === 1);
    const optimalId = level1.length
      ? level1.reduce((best, n) => (n.visits > best.visits ? n : best), level1[0]).id
      : null;

    // Group by level for layout
    const byLevel = {};
    visibleNodes.forEach(n => {
      const lv = n.level ?? 0;
      if (!byLevel[lv]) byLevel[lv] = [];
      byLevel[lv].push(n);
    });

    const NODE_W = 220;
    const NODE_H = 280;
    const H_GAP = 40;
    const V_GAP = 80;

    const flowNodes = visibleNodes.map(node => {
      const lv = node.level ?? 0;
      const siblings = byLevel[lv];
      const idx = siblings.indexOf(node);
      const totalW = siblings.length * NODE_W + (siblings.length - 1) * H_GAP;
      const x = -totalW / 2 + idx * (NODE_W + H_GAP);
      const y = lv * (NODE_H + V_GAP);

      return {
        id: node.id.toString(),
        type: 'negotiationNode',
        data: {
          ...node,
          isOptimal: node.id === optimalId,
          nodeType: lv === 0 ? 'Root' : `Level ${lv}`,
        },
        position: { x, y },
      };
    });

    const flowEdges = (data.edges || [])
      .filter(e => visibleIds.has(e.source) && visibleIds.has(e.target))
      .map(e => {
        const isOptimalEdge = e.target === optimalId;
        return {
          id: `e${e.source}-${e.target}`,
          source: e.source.toString(),
          target: e.target.toString(),
          ...defaultEdgeOptions,
          style: {
            ...defaultEdgeOptions.style,
            stroke: isOptimalEdge ? '#10b981' : '#475569',
            strokeWidth: isOptimalEdge ? 2.5 : 1.5,
          },
          markerEnd: {
            ...defaultEdgeOptions.markerEnd,
            color: isOptimalEdge ? '#10b981' : '#475569',
          },
          animated: isOptimalEdge,
        };
      });

    return { nodes: flowNodes, edges: flowEdges };
  }, []);

  useEffect(() => {
    if (treeData) {
      const { nodes: fn, edges: fe } = buildFlowGraph(treeData, maxLevel);
      setNodes(fn);
      setEdges(fe);
    }
  }, [treeData, maxLevel, buildFlowGraph, setNodes, setEdges]);

  if (!treeData?.nodes?.length) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: 400, background: '#0f172a', borderRadius: 10, border: '1px solid #1e293b' }}>
        <div style={{ textAlign: 'center', color: '#64748b' }}>
          <div style={{ fontSize: 16, marginBottom: 8 }}>No MCTS tree data</div>
          <div style={{ fontSize: 13 }}>Run MCTS negotiation to generate the tree</div>
        </div>
      </div>
    );
  }

  const totalNodes = treeData.nodes.length;
  const maxDepth = Math.max(...treeData.nodes.map(n => n.level ?? 0));

  return (
    <div style={{ position: 'relative' }}>
      {/* Stats bar */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ color: '#94a3b8', fontSize: 12 }}>
          Total nodes: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{totalNodes}</span>
        </div>
        <div style={{ color: '#94a3b8', fontSize: 12 }}>
          Max depth: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{maxDepth}</span>
        </div>
        <div style={{ color: '#94a3b8', fontSize: 12 }}>
          Showing levels: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>0–{maxLevel - 1}</span>
        </div>
        {/* Level controls */}
        <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
          {[1, 2, 3, 4].map(lv => (
            <button key={lv} onClick={() => setMaxLevel(lv + 1)}
              style={{
                padding: '4px 12px', borderRadius: 6, border: 'none', cursor: 'pointer',
                fontSize: 11, fontWeight: 600,
                background: maxLevel === lv + 1 ? '#3b82f6' : '#1e293b',
                color: maxLevel === lv + 1 ? '#fff' : '#94a3b8',
              }}>
              L{lv}
            </button>
          ))}
        </div>
        <button onClick={() => setIsFullscreen(!isFullscreen)}
          style={{ padding: '4px 12px', borderRadius: 6, border: '1px solid #334155',
            background: '#1e293b', color: '#94a3b8', cursor: 'pointer', fontSize: 11,
            display: 'flex', alignItems: 'center', gap: 4 }}>
          {isFullscreen ? <><Minimize size={12} /> Exit</> : <><Maximize size={12} /> Fullscreen</>}
        </button>
      </div>

      <div style={{
        height: isFullscreen ? '80vh' : 600,
        background: '#0f172a', borderRadius: 10,
        border: '1px solid #1e293b', overflow: 'hidden',
        position: isFullscreen ? 'fixed' : 'relative',
        inset: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? 9999 : 'auto',
      }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => onNodeClick && onNodeClick(node.data)}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.1}
          maxZoom={2}
          attributionPosition="bottom-left"
        >
          <Background color="#1e293b" gap={24} />
          <Controls style={{ background: '#1e293b', border: '1px solid #334155' }} />
          <MiniMap
            nodeColor={n => {
              const risk = n.data?.disputeRisk ?? 50;
              return risk < 40 ? '#10b981' : risk < 60 ? '#f59e0b' : '#ef4444';
            }}
            style={{ background: '#0f172a', border: '1px solid #334155' }}
          />
        </ReactFlow>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
        {[['#10b981', 'Low Risk (<40%)'], ['#f59e0b', 'Medium Risk (40-60%)'],
          ['#f97316', 'High Risk (60-75%)'], ['#ef4444', 'Very High Risk (>75%)']].map(([c, l]) => (
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#64748b' }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
            {l}
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#64748b' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
          Optimal path
        </div>
      </div>
    </div>
  );
}
