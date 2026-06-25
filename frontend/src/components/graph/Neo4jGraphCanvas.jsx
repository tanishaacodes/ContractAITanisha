import React, { useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Neo4j-style node colors by type
const NODE_COLORS = {
  Contract: '#68BC00',      // Neo4j green
  Clause: '#4C8EDA',        // Blue
  Risk: '#F16667',          // Red
  Obligation: '#F79767',    // Orange
  Jurisdiction: '#9063CD',  // Purple
  Party: '#FFD86E',         // Yellow
  Version: '#06B6D4',       // Cyan (for clause evolution)
  // Risk-level based colors for clause evolution
  LowRisk: '#10b981',       // Green (0-40%)
  MediumRisk: '#f59e0b',    // Orange/Yellow (40-70%)
  HighRisk: '#dc2626',      // Red (70-100%)
  // Intent analysis nodes
  Intent: '#9063CD',        // Purple (intents)
  Right: '#10b981',         // Green (rights)
  default: '#8D99AE',       // Gray
};

// Neo4j-style custom node component
const Neo4jNode = ({ data }) => {
  // Use node-specific color (risk-based for clauses) or fall back to type color
  const color = data.color || NODE_COLORS[data.type] || NODE_COLORS.default;

  return (
    <>
      {/* Add invisible handles for React Flow edge connections */}
      <Handle
        type="target"
        position={Position.Top}
        style={{ opacity: 0 }}
      />
      <Handle
        type="target"
        position={Position.Left}
        style={{ opacity: 0 }}
      />
      <Handle
        type="target"
        position={Position.Right}
        style={{ opacity: 0 }}
      />
      <Handle
        type="target"
        position={Position.Bottom}
        style={{ opacity: 0 }}
      />

      <div
        className="neo4j-node"
        style={{
          background: `radial-gradient(circle, ${color} 0%, ${color}dd 70%, ${color}aa 100%)`,
          border: `3px solid ${color}`,
          borderRadius: '50%',
          width: data.size || 60,
          height: data.size || 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 'bold',
          fontSize: data.size ? `${data.size / 6}px` : '10px',
          textAlign: 'center',
          padding: '4px',
          cursor: 'pointer',
          boxShadow: `0 0 20px ${color}66, 0 0 40px ${color}33`,
          transition: 'all 0.3s ease',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.2)';
          e.currentTarget.style.boxShadow = `0 0 30px ${color}aa, 0 0 60px ${color}66`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = `0 0 20px ${color}66, 0 0 40px ${color}33`;
        }}
      >
        <div style={{
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          lineHeight: '1.2',
          maxWidth: '100%',
        }}>
          {data.label}
        </div>
      </div>

      {/* Add invisible source handles for React Flow edge connections */}
      <Handle
        type="source"
        position={Position.Top}
        style={{ opacity: 0 }}
      />
      <Handle
        type="source"
        position={Position.Left}
        style={{ opacity: 0 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ opacity: 0 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ opacity: 0 }}
      />
    </>
  );
};

const nodeTypes = {
  neo4j: Neo4jNode,
};

const Neo4jGraphCanvas = ({
  nodes: initialNodes = [],
  edges: initialEdges = [],
  onNodeClick,
  onEdgeClick,
  height = '600px',
  showMiniMap = true,
  showControls = true,
  darkMode = true,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(
    initialNodes.map(node => ({
      ...node,
      type: 'neo4j',
      position: node.position || { x: Math.random() * 500, y: Math.random() * 500 },
    }))
  );

  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialEdges.map(edge => ({
      ...edge,
      type: 'default', // Changed from 'smoothstep' to 'default' for straighter, more visible lines
      animated: edge.animated !== false,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.color || '#8D99AE',
        width: 20,
        height: 20,
      },
      style: {
        stroke: edge.color || '#8D99AE',
        strokeWidth: edge.width || 2,
        strokeOpacity: 0.8, // Make edges more visible
      },
      label: edge.label,
      labelStyle: {
        fill: darkMode ? '#E2E8F0' : '#1E293B',
        fontWeight: 700,
        fontSize: 12,
        textShadow: darkMode ? '0 0 3px #000' : '0 0 3px #fff',
      },
      labelBgStyle: {
        fill: darkMode ? '#1E293B' : '#F8FAFC',
        fillOpacity: 0.95,
        rx: 4,
        ry: 4,
      },
      labelBgPadding: [8, 4],
      labelBgBorderRadius: 4,
    }))
  );

  // Update nodes and edges when props change
  useEffect(() => {
    console.log('[Neo4jGraphCanvas] Updating with', initialNodes.length, 'nodes and', initialEdges.length, 'edges');

    const formattedNodes = initialNodes.map(node => ({
      ...node,
      type: 'neo4j',
      position: node.position || { x: Math.random() * 500, y: Math.random() * 500 },
    }));

    const formattedEdges = initialEdges.map(edge => ({
      ...edge,
      type: 'default',
      animated: edge.animated !== false,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edge.color || '#8D99AE',
        width: 20,
        height: 20,
      },
      style: {
        stroke: edge.color || '#8D99AE',
        strokeWidth: edge.width || 2,
        strokeOpacity: 0.8,
      },
      label: edge.label,
      labelStyle: {
        fill: darkMode ? '#E2E8F0' : '#1E293B',
        fontWeight: 700,
        fontSize: 12,
        textShadow: darkMode ? '0 0 3px #000' : '0 0 3px #fff',
      },
      labelBgStyle: {
        fill: darkMode ? '#1E293B' : '#F8FAFC',
        fillOpacity: 0.95,
        rx: 4,
        ry: 4,
      },
      labelBgPadding: [8, 4],
      labelBgBorderRadius: 4,
    }));

    setNodes(formattedNodes);
    setEdges(formattedEdges);
  }, [initialNodes, initialEdges, darkMode]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleNodeClick = useCallback(
    (event, node) => {
      if (onNodeClick) {
        onNodeClick(node);
      }
    },
    [onNodeClick]
  );

  const handleEdgeClick = useCallback(
    (event, edge) => {
      if (onEdgeClick) {
        onEdgeClick(edge);
      }
    },
    [onEdgeClick]
  );

  return (
    <div style={{ width: '100%', height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
        style={{
          background: darkMode ? '#0F172A' : '#F8FAFC',
        }}
      >
        {showControls && (
          <Controls
            style={{
              button: {
                backgroundColor: darkMode ? '#1E293B' : '#FFFFFF',
                color: darkMode ? '#E2E8F0' : '#1E293B',
                borderColor: darkMode ? '#334155' : '#CBD5E1',
              }
            }}
          />
        )}
        <Background
          color={darkMode ? '#334155' : '#CBD5E1'}
          gap={16}
          size={1}
          variant="dots"
        />
        {showMiniMap && (
          <MiniMap
            nodeColor={(node) => {
              const color = NODE_COLORS[node.data?.type] || NODE_COLORS.default;
              return color;
            }}
            style={{
              backgroundColor: darkMode ? '#1E293B' : '#FFFFFF',
            }}
            maskColor={darkMode ? '#0F172A99' : '#F8FAFC99'}
          />
        )}
      </ReactFlow>
    </div>
  );
};

export default Neo4jGraphCanvas;
