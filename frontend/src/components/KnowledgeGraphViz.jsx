/**
 * Knowledge Graph Visualization - Interactive Network Graph
 * Uses Cytoscape.js to visualize FM knowledge graph relationships
 */

import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import cola from 'cytoscape-cola';

// Register layout
cytoscape.use(cola);

const KnowledgeGraphViz = ({
  graphData,
  height = '600px',
  onNodeClick,
  highlightPath = null
}) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Initialize Cytoscape
    cyRef.current = cytoscape({
      container: containerRef.current,

      elements: transformGraphData(graphData),

      style: [
        // Node styles
        {
          selector: 'node',
          style: {
            'background-color': (ele) => getNodeColor(ele.data('type')),
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'color': '#FFFFFF',
            'text-outline-width': 2,
            'text-outline-color': (ele) => getNodeColor(ele.data('type')),
            'width': (ele) => 30 + (ele.data('importance') || 0) * 20,
            'height': (ele) => 30 + (ele.data('importance') || 0) * 20
          }
        },
        // Event nodes
        {
          selector: 'node[type = "Event"]',
          style: {
            'shape': 'hexagon',
            'background-color': '#DC2626'
          }
        },
        // Disruption nodes
        {
          selector: 'node[type = "Disruption"]',
          style: {
            'shape': 'diamond',
            'background-color': '#EA580C'
          }
        },
        // Outcome nodes
        {
          selector: 'node[type = "ContractOutcome"]',
          style: {
            'shape': 'rectangle',
            'background-color': '#8B5CF6'
          }
        },
        // Edge styles
        {
          selector: 'edge',
          style: {
            'width': (ele) => 2 + (ele.data('probability') || 0) * 4,
            'line-color': '#9CA3AF',
            'target-arrow-color': '#9CA3AF',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(type)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10
          }
        },
        // CAUSES relationship
        {
          selector: 'edge[type = "CAUSES"]',
          style: {
            'line-color': '#DC2626',
            'target-arrow-color': '#DC2626',
            'line-style': 'solid'
          }
        },
        // MITIGATED_BY relationship
        {
          selector: 'edge[type = "MITIGATED_BY"]',
          style: {
            'line-color': '#10B981',
            'target-arrow-color': '#10B981',
            'line-style': 'dashed'
          }
        },
        // Highlighted path
        {
          selector: '.highlighted',
          style: {
            'background-color': '#FBBF24',
            'line-color': '#FBBF24',
            'target-arrow-color': '#FBBF24',
            'width': 6,
            'z-index': 999
          }
        },
        // Selected nodes
        {
          selector: ':selected',
          style: {
            'border-width': 3,
            'border-color': '#3B82F6'
          }
        }
      ],

      layout: {
        name: 'cola',
        animate: true,
        animationDuration: 500,
        nodeSpacing: 50,
        edgeLengthVal: 100,
        randomize: false,
        maxSimulationTime: 2000
      },

      minZoom: 0.5,
      maxZoom: 3
    });

    // Add click handler
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      if (onNodeClick) {
        onNodeClick(node.data());
      }
    });

    // Add hover effects
    cyRef.current.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      node.style('background-color', '#3B82F6');

      // Highlight connected edges
      node.connectedEdges().style({
        'line-color': '#3B82F6',
        'target-arrow-color': '#3B82F6',
        'width': 4
      });
    });

    cyRef.current.on('mouseout', 'node', (evt) => {
      const node = evt.target;
      node.style('background-color', getNodeColor(node.data('type')));

      // Reset connected edges
      node.connectedEdges().style({
        'line-color': '#9CA3AF',
        'target-arrow-color': '#9CA3AF',
        'width': 2
      });
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [graphData]);

  // Highlight path effect
  useEffect(() => {
    if (!cyRef.current || !highlightPath) return;

    // Remove previous highlighting
    cyRef.current.elements().removeClass('highlighted');

    // Highlight new path
    if (highlightPath.nodes && highlightPath.nodes.length > 0) {
      highlightPath.nodes.forEach(nodeId => {
        cyRef.current.getElementById(nodeId).addClass('highlighted');
      });
    }

    if (highlightPath.edges && highlightPath.edges.length > 0) {
      highlightPath.edges.forEach(edgeId => {
        cyRef.current.getElementById(edgeId).addClass('highlighted');
      });
    }

    // Fit to highlighted path
    if (highlightPath.nodes && highlightPath.nodes.length > 0) {
      const highlightedElements = cyRef.current.collection();
      highlightPath.nodes.forEach(nodeId => {
        highlightedElements.merge(cyRef.current.getElementById(nodeId));
      });
      cyRef.current.fit(highlightedElements, 50);
    }
  }, [highlightPath]);

  const handleResetZoom = () => {
    if (cyRef.current) {
      cyRef.current.fit();
    }
  };

  const handleExportPNG = () => {
    if (cyRef.current) {
      const png = cyRef.current.png({ full: true, scale: 2 });
      const link = document.createElement('a');
      link.download = 'knowledge-graph.png';
      link.href = png;
      link.click();
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {/* Controls */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        zIndex: 10
      }}>
        <button
          onClick={handleResetZoom}
          style={{
            padding: '8px 12px',
            backgroundColor: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: '500',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          🔍 Reset Zoom
        </button>
        <button
          onClick={handleExportPNG}
          style={{
            padding: '8px 12px',
            backgroundColor: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: '500',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          📸 Export PNG
        </button>
      </div>

      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: '10px',
        left: '10px',
        backgroundColor: 'white',
        padding: '15px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: 10,
        maxWidth: '200px'
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold' }}>
          Legend
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              backgroundColor: '#DC2626',
              clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)'
            }} />
            <span>Event</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              backgroundColor: '#EA580C',
              transform: 'rotate(45deg)'
            }} />
            <span>Disruption</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '20px',
              height: '20px',
              backgroundColor: '#8B5CF6'
            }} />
            <span>Outcome</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
            <div style={{ width: '30px', height: '2px', backgroundColor: '#DC2626' }} />
            <span>Causes</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '30px',
              height: '2px',
              backgroundColor: '#10B981',
              borderTop: '2px dashed #10B981'
            }} />
            <span>Mitigates</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      {graphData && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          backgroundColor: 'rgba(255,255,255,0.95)',
          padding: '10px 15px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          fontSize: '12px',
          fontWeight: '500'
        }}>
          <div>Nodes: {graphData.node_count || 0}</div>
          <div>Edges: {graphData.edge_count || 0}</div>
        </div>
      )}
    </div>
  );
};

// Helper functions
const transformGraphData = (graphData) => {
  if (!graphData || !graphData.nodes || !graphData.edges) {
    return [];
  }

  const elements = [];

  // Add nodes
  graphData.nodes.forEach(node => {
    elements.push({
      data: {
        id: node.id,
        label: node.label || node.id,
        type: node.type,
        ...node.properties
      }
    });
  });

  // Add edges
  graphData.edges.forEach((edge, index) => {
    elements.push({
      data: {
        id: `edge-${index}`,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        ...edge.properties
      }
    });
  });

  return elements;
};

const getNodeColor = (type) => {
  const colorMap = {
    'Event': '#DC2626',
    'Disruption': '#EA580C',
    'ContractOutcome': '#8B5CF6',
    'Risk': '#F59E0B',
    'Mitigation': '#10B981',
    'Supplier': '#3B82F6',
    'Port': '#06B6D4',
    'Country': '#6366F1'
  };

  return colorMap[type] || '#6B7280';
};

export default KnowledgeGraphViz;
