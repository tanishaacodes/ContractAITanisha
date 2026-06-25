/**
 * Neo4j Graph Visualization Component - REDESIGNED with React Flow
 * Modern, clean, professional graph visualization
 */

import React, { useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

const Neo4jGraphViz = ({ graphData, height = '500px', onNodeClick }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedNodeData, setSelectedNodeData] = useState(null);

  // Node colors by type
  const getNodeColor = (type) => {
    const colors = {
      'Contract': '#3b82f6',
      'Clause': '#8b5cf6',
      'Risk': '#ef4444',
      'Obligation': '#f59e0b',
      'Unknown': '#64748b'
    };
    return colors[type] || colors.Unknown;
  };

  // Convert Neo4j data to React Flow format
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!graphData?.nodes || !graphData?.links) {
      return { nodes: [], edges: [] };
    }

    // Calculate positions in a circle layout for clarity
    const nodeCount = graphData.nodes.length;
    const radius = Math.max(300, nodeCount * 30);
    const centerX = 0;
    const centerY = 0;

    const nodes = graphData.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / nodeCount;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      return {
        id: String(n.id),
        type: 'default',
        position: { x, y },
        data: {
          label: (
            <div style={{
              padding: '8px 12px',
              borderRadius: '8px',
              background: getNodeColor(n.type),
              color: '#ffffff',
              fontWeight: '600',
              fontSize: '12px',
              textAlign: 'center',
              minWidth: '80px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
            }}>
              <div style={{ fontSize: '10px', opacity: 0.9, marginBottom: '2px' }}>
                {n.type}
              </div>
              <div>{(n.name || n.id).slice(0, 30)}</div>
            </div>
          ),
          ...n
        },
        style: {
          background: 'transparent',
          border: 'none',
          padding: 0,
        },
      };
    });

    const edges = graphData.links.map((e, i) => ({
      id: `edge-${i}`,
      source: String(e.source),
      target: String(e.target),
      label: e.label || e.type || '',
      type: 'smoothstep',
      animated: false,
      style: {
        stroke: '#64748b',
        strokeWidth: 2,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#64748b',
        width: 20,
        height: 20,
      },
      labelStyle: {
        fill: '#94a3b8',
        fontSize: 10,
        fontWeight: 600,
      },
      labelBgStyle: {
        fill: '#0f172a',
        fillOpacity: 0.8,
      },
    }));

    return { nodes, edges };
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onNodeClickHandler = useCallback((event, node) => {
    setSelectedNodeData(node.data);
    if (onNodeClick) {
      onNodeClick(node.data);
    }
  }, [onNodeClick]);

  // Calculate stats
  const stats = useMemo(() => {
    const typeCount = {};
    nodes.forEach(n => {
      const type = n.data.type || 'Unknown';
      typeCount[type] = (typeCount[type] || 0) + 1;
    });
    return {
      nodes: nodes.length,
      edges: edges.length,
      types: typeCount
    };
  }, [nodes, edges]);

  const nodeTypes = [
    { type: 'Contract', color: '#3b82f6', shape: '▬' },
    { type: 'Clause', color: '#8b5cf6', shape: '●' },
    { type: 'Risk', color: '#ef4444', shape: '◆' },
    { type: 'Obligation', color: '#f59e0b', shape: '⬡' }
  ];

  return (
    <div style={{
      position: isFullscreen ? 'fixed' : 'relative',
      inset: isFullscreen ? 0 : 'auto',
      zIndex: isFullscreen ? 9999 : 'auto',
      backgroundColor: isFullscreen ? '#0f172a' : 'transparent',
      padding: isFullscreen ? '16px' : 0
    }}>
      {/* Stats Bar */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '8px',
        fontSize: '11px',
        color: '#94a3b8',
        padding: '10px 16px',
        backgroundColor: '#1e293b',
        borderRadius: '8px',
        border: '1px solid #334155',
        alignItems: 'center'
      }}>
        <span><strong style={{ color: '#06b6d4' }}>{stats.nodes}</strong> nodes</span>
        <span><strong style={{ color: '#06b6d4' }}>{stats.edges}</strong> edges</span>
        {Object.entries(stats.types).map(([type, count]) => (
          <span key={type}><strong style={{ color: '#06b6d4' }}>{count}</strong> {type}s</span>
        ))}

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ color: '#64748b', fontSize: '10px' }}>💡 Drag nodes • Scroll to zoom</span>

          {!isFullscreen && (
            <button
              onClick={() => setIsFullscreen(true)}
              style={{
                padding: '6px 12px',
                backgroundColor: '#334155',
                color: '#06b6d4',
                border: '1px solid #475569',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: '600'
              }}
            >
              ⛶ Fullscreen
            </button>
          )}
        </div>
      </div>

      {/* React Flow Graph */}
      <div style={{
        height: isFullscreen ? 'calc(100vh - 100px)' : height,
        background: 'radial-gradient(ellipse at center, #0f172a 0%, #020617 100%)',
        borderRadius: '12px',
        border: '1px solid #334155',
        position: 'relative'
      }}>
        {/* Exit Fullscreen Button */}
        {isFullscreen && (
          <button
            onClick={() => setIsFullscreen(false)}
            style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              zIndex: 10,
              padding: '10px 16px',
              backgroundColor: '#1e293b',
              color: '#fff',
              border: '1px solid #334155',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            ✕ Exit Fullscreen
          </button>
        )}

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClickHandler}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          nodesDraggable={true}
          nodesConnectable={false}
          elementsSelectable={true}
          minZoom={0.1}
          maxZoom={2}
        >
          <Background variant="dots" color="#1e293b" gap={24} size={1.2} />
          <Controls
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8
            }}
          />
          <MiniMap
            style={{
              background: '#020617',
              border: '1px solid #334155',
              borderRadius: 8
            }}
            nodeColor={(n) => getNodeColor(n.data.type)}
            maskColor="#02061788"
          />
        </ReactFlow>

        {/* Legend */}
        <div style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          backgroundColor: '#1e293bdd',
          borderRadius: '8px',
          border: '1px solid #334155',
          padding: '12px',
          fontSize: '11px',
          zIndex: 5
        }}>
          <div style={{ color: '#94a3b8', fontWeight: '600', marginBottom: '8px', fontSize: '10px', textTransform: 'uppercase' }}>
            Node Types
          </div>
          {nodeTypes.map(({ type, color, shape }) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ color, fontSize: '16px' }}>{shape}</span>
              <span style={{ color: '#e2e8f0', fontWeight: '500' }}>{type}</span>
            </div>
          ))}
        </div>

        {/* Selected Node Info */}
        {selectedNodeData && (
          <div style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            backgroundColor: '#1e293bdd',
            borderRadius: '8px',
            border: '1px solid #334155',
            padding: '12px',
            fontSize: '11px',
            maxWidth: '300px',
            zIndex: 5
          }}>
            <div style={{ color: '#06b6d4', fontWeight: '600', marginBottom: '6px', fontSize: '12px' }}>
              {selectedNodeData.type}
            </div>
            <div style={{ color: '#e2e8f0', marginBottom: '4px' }}>
              <strong>Name:</strong> {selectedNodeData.name || selectedNodeData.id}
            </div>
            {selectedNodeData.risk > 0 && (
              <div style={{ color: '#ef4444', marginBottom: '4px' }}>
                <strong>Risk:</strong> {(selectedNodeData.risk * 100).toFixed(0)}%
              </div>
            )}
            <button
              onClick={() => setSelectedNodeData(null)}
              style={{
                marginTop: '8px',
                padding: '4px 8px',
                backgroundColor: '#334155',
                color: '#e2e8f0',
                border: 'none',
                borderRadius: '4px',
                fontSize: '10px',
                cursor: 'pointer'
              }}
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Neo4jGraphViz;
