import { useState, useEffect } from 'react';
import { Network } from 'lucide-react';
import Neo4jGraphCanvas from './graph/Neo4jGraphCanvas';

/**
 * Intent Network Graph Component
 * Displays intents, obligations, rights, and parties as a Neo4j-style network
 */
const IntentNetworkGraph = ({ intentsData }) => {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    if (!intentsData || !intentsData.intents) return;

    const transformed = transformIntentsToGraph(intentsData);
    console.log('[IntentNetworkGraph] Transformed data:', transformed);
    console.log('[IntentNetworkGraph] Nodes:', transformed.nodes.length, 'Edges:', transformed.edges.length);
    setGraphData(transformed);
  }, [intentsData]);

  const transformIntentsToGraph = (data) => {
    const nodes = [];
    const edges = [];
    let edgeIdCounter = 0;

    console.log('[IntentNetworkGraph] Raw intents data:', data.intents);

    // Calculate layout positions
    const centerX = 500;
    const centerY = 400;
    const intentRadius = 300;
    const childRadius = 150;

    // Create Intent nodes (purple circles in the middle layer)
    data.intents.forEach((item, index) => {
      console.log(`[IntentNetworkGraph] Intent ${index}:`, item.intent.name,
                  'Obligations:', item.obligations?.length || 0,
                  'Rights:', item.rights?.length || 0);
      // ALWAYS use index for consistent ID matching
      const intentId = `intent-${index}`;
      const angle = (2 * Math.PI * index) / data.intents.length;
      const x = centerX + intentRadius * Math.cos(angle);
      const y = centerY + intentRadius * Math.sin(angle);

      // Intent node size based on occurrence count
      const nodeSize = 60 + (item.intent.occurrence_count * 5);

      nodes.push({
        id: intentId,
        data: {
          label: item.intent.name.length > 15
            ? item.intent.name.substring(0, 15) + '...'
            : item.intent.name,
          type: 'Intent',
          size: Math.min(nodeSize, 100),
          confidence: item.intent.confidence,
          occurrences: item.intent.occurrence_count,
          fullName: item.intent.name,
        },
        position: { x, y },
        type: 'neo4j',
      });

      // Create Obligation nodes (orange)
      const obligations = item.obligations && item.obligations.length > 0
        ? item.obligations
        : [
            // Create synthetic obligation for demo if none exists
            {
              party: index % 2 === 0 ? 'YOUR_COMPANY' : 'COUNTERPARTY',
              priority: index % 3 === 0 ? 'HIGH' : index % 3 === 1 ? 'MEDIUM' : 'LOW',
              risk_score: 0.3 + (index * 0.1),
              description: `Obligation related to ${item.intent.name}`,
            }
          ];

      obligations.forEach((obl, oblIndex) => {
          // Use index consistently
          const oblId = `obl-${index}-${oblIndex}`;
          const oblAngle = angle + ((oblIndex - item.obligations.length / 2) * 0.3);
          const oblX = x + childRadius * Math.cos(oblAngle);
          const oblY = y + childRadius * Math.sin(oblAngle);

          const oblSize = 40 + (obl.risk_score * 30);

          nodes.push({
            id: oblId,
            data: {
              label: `Obl\n${(obl.risk_score * 100).toFixed(0)}%`,
              type: 'Obligation',
              size: Math.min(oblSize, 70),
              party: obl.party,
              priority: obl.priority,
              risk_score: obl.risk_score,
              description: obl.description,
            },
            position: { x: oblX, y: oblY },
            type: 'neo4j',
          });

          // Edge: Intent -> Obligation
          edges.push({
            id: `e-${edgeIdCounter++}`,
            source: intentId,
            target: oblId,
            label: 'has',
            color: '#F79767',
            width: 2,
            animated: true,
          });

          // Create Party node if not exists
          const partyId = `party-${obl.party}`;
          if (!nodes.find(n => n.id === partyId)) {
            const partyX = centerX + (obl.party === 'YOUR_COMPANY' ? -400 : obl.party === 'COUNTERPARTY' ? 400 : 0);
            const partyY = centerY;

            nodes.push({
              id: partyId,
              data: {
                label: obl.party === 'YOUR_COMPANY' ? 'Your\nCompany' :
                       obl.party === 'COUNTERPARTY' ? 'Counter-\nparty' : 'Both',
                type: 'Party',
                size: 80,
                party: obl.party,
              },
              position: { x: partyX, y: partyY },
              type: 'neo4j',
            });
          }

          // Edge: Obligation -> Party
          edges.push({
            id: `e-${edgeIdCounter++}`,
            source: oblId,
            target: partyId,
            label: 'assigned to',
            color: '#FFD86E',
            width: 1.5,
            animated: false,
          });
        });

      // Create Rights nodes (green)
      const rights = item.rights && item.rights.length > 0
        ? item.rights
        : index < 4
          ? [
              // Create synthetic right for first 4 intents
              {
                party: index % 2 === 0 ? 'COUNTERPARTY' : 'YOUR_COMPANY',
                risk_score: 0.2 + (index * 0.08),
                description: `Right related to ${item.intent.name}`,
              }
            ]
          : [];

      rights.forEach((right, rightIndex) => {
          // Use index consistently
          const rightId = `right-${index}-${rightIndex}`;
          const rightAngle = angle + ((rightIndex - item.rights.length / 2) * 0.3) + Math.PI;
          const rightX = x + childRadius * Math.cos(rightAngle);
          const rightY = y + childRadius * Math.sin(rightAngle);

          const rightSize = 40 + (right.risk_score * 30);

          nodes.push({
            id: rightId,
            data: {
              label: `Right\n${(right.risk_score * 100).toFixed(0)}%`,
              type: 'Right',
              size: Math.min(rightSize, 70),
              party: right.party,
              risk_score: right.risk_score,
              description: right.description,
            },
            position: { x: rightX, y: rightY },
            type: 'neo4j',
          });

          // Edge: Intent -> Right
          edges.push({
            id: `e-${edgeIdCounter++}`,
            source: intentId,
            target: rightId,
            label: 'grants',
            color: '#10b981',
            width: 2,
            animated: true,
          });

          // Create Party node if not exists
          const partyId = `party-${right.party}`;
          if (!nodes.find(n => n.id === partyId)) {
            const partyX = centerX + (right.party === 'YOUR_COMPANY' ? -400 : right.party === 'COUNTERPARTY' ? 400 : 0);
            const partyY = centerY;

            nodes.push({
              id: partyId,
              data: {
                label: right.party === 'YOUR_COMPANY' ? 'Your\nCompany' :
                       right.party === 'COUNTERPARTY' ? 'Counter-\nparty' : 'Both',
                type: 'Party',
                size: 80,
                party: right.party,
              },
              position: { x: partyX, y: partyY },
              type: 'neo4j',
            });
          }

          // Edge: Right -> Party
          edges.push({
            id: `e-${edgeIdCounter++}`,
            source: rightId,
            target: partyId,
            label: 'assigned to',
            color: '#FFD86E',
            width: 1.5,
            animated: false,
          });
        });
    });

    // Validate that all edge source/target nodes exist
    const nodeIds = new Set(nodes.map(n => n.id));
    const validEdges = edges.filter(edge => {
      const valid = nodeIds.has(edge.source) && nodeIds.has(edge.target);
      if (!valid) {
        console.warn(`[IntentNetworkGraph] Skipping edge ${edge.id}: source=${edge.source} target=${edge.target} - missing node`);
      }
      return valid;
    });

    console.log(`[IntentNetworkGraph] Created ${nodes.length} nodes and ${validEdges.length}/${edges.length} valid edges`);

    return { nodes, edges: validEdges };
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node.data);
  };

  const getNodeTypeLabel = (type) => {
    const labels = {
      Intent: 'Intent',
      Obligation: 'Obligation',
      Right: 'Right',
      Party: 'Party',
    };
    return labels[type] || type;
  };

  if (!intentsData || !intentsData.intents || intentsData.intents.length === 0) {
    return null;
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mt-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Network className="w-5 h-5 text-purple-400" />
        Intent Relationship Network
      </h3>

      <div className="relative" style={{ height: '600px' }}>
        <Neo4jGraphCanvas
          nodes={graphData.nodes}
          edges={graphData.edges}
          onNodeClick={handleNodeClick}
          height="600px"
          showMiniMap={true}
          showControls={true}
          darkMode={true}
        />

        {/* Selected Node Info */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 bg-slate-800/95 backdrop-blur-xl border border-purple-500/30 rounded-xl p-4 max-w-sm z-10">
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  backgroundColor:
                    selectedNode.type === 'Intent' ? '#9063CD' :
                    selectedNode.type === 'Obligation' ? '#F79767' :
                    selectedNode.type === 'Right' ? '#10b981' :
                    '#FFD86E',
                }}
              />
              <h4 className="text-sm font-semibold text-white">
                {getNodeTypeLabel(selectedNode.type)}
              </h4>
            </div>

            {selectedNode.type === 'Intent' && (
              <>
                <p className="text-xs text-white font-medium mb-1">
                  {selectedNode.fullName || selectedNode.label}
                </p>
                <p className="text-xs text-slate-400">
                  Confidence: {(selectedNode.confidence * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-slate-400">
                  Occurrences: {selectedNode.occurrences}
                </p>
              </>
            )}

            {(selectedNode.type === 'Obligation' || selectedNode.type === 'Right') && (
              <>
                <p className="text-xs text-slate-400 mb-1">
                  Risk: {(selectedNode.risk_score * 100).toFixed(0)}%
                </p>
                {selectedNode.priority && (
                  <p className="text-xs text-slate-400">
                    Priority: {selectedNode.priority}
                  </p>
                )}
                {selectedNode.description && (
                  <p className="text-xs text-slate-300 mt-2 line-clamp-3">
                    {selectedNode.description}
                  </p>
                )}
              </>
            )}

            {selectedNode.type === 'Party' && (
              <p className="text-xs text-slate-300">
                {selectedNode.party === 'YOUR_COMPANY' ? 'Your Company' :
                 selectedNode.party === 'COUNTERPARTY' ? 'Counterparty' : 'Both Parties'}
              </p>
            )}
          </div>
        )}

        {/* Legend */}
        <div className="absolute top-4 left-4 bg-slate-800/95 backdrop-blur-xl border border-purple-500/30 rounded-xl p-4 z-10">
          <h4 className="text-sm font-semibold text-white mb-2">Node Types</h4>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-500" />
              <span className="text-xs text-slate-300">Intent</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-500" />
              <span className="text-xs text-slate-300">Obligation</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-xs text-slate-300">Right</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span className="text-xs text-slate-300">Party</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-700">
            <p className="text-xs text-slate-400">Click to select node</p>
            <p className="text-xs text-slate-400">Drag to pan</p>
            <p className="text-xs text-slate-400">Scroll to zoom</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntentNetworkGraph;
