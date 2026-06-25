/**
 * NeoVizPanel.jsx
 * ================
 * Neovis.js-based Neo4j graph visualization for the Dispute Predictor.
 * Shows risk nodes + causal edges pulled directly from Neo4j via Bolt.
 * Falls back gracefully if Neo4j is not running.
 */

import { useEffect, useRef, useState } from 'react';
import { Maximize, Minimize } from 'lucide-react';

const BOLT_URL      = 'bolt://localhost:7687';
const NEO4J_USER    = 'neo4j';
const NEO4J_PASS    = 'password123';  // matches neo4j-arbitration container

// Cypher query: fetch all RiskNode relationships (max 300)
const CYPHER_QUERY  = `
  MATCH (a:RiskNode)-[r:CAUSES]->(b:RiskNode)
  RETURN a, r, b LIMIT 300
`;

// Fallback static graph data (same 60 risk nodes, rendered by React Flow-style SVG)
const STATIC_NODES = [
  { id: 'WarRisk',           label: 'War Risk',              cluster: 'geo',          risk: 0.05 },
  { id: 'SanctionsRisk',     label: 'Sanctions Risk',        cluster: 'geo',          risk: 0.10 },
  { id: 'PoliticalInstab',   label: 'Political Instability', cluster: 'geo',          risk: 0.12 },
  { id: 'InflationRisk',     label: 'Inflation Risk',        cluster: 'macro',        risk: 0.35 },
  { id: 'CurrencyVolat',     label: 'Currency Volatility',   cluster: 'macro',        risk: 0.22 },
  { id: 'CommodityShock',    label: 'Commodity Shock',       cluster: 'macro',        risk: 0.40 },
  { id: 'EnergyPriceShock',  label: 'Energy Price Shock',    cluster: 'macro',        risk: 0.30 },
  { id: 'CompetitionInc',    label: 'Competition Increase',  cluster: 'market',       risk: 0.20 },
  { id: 'DemandDecline',     label: 'Demand Decline',        cluster: 'market',       risk: 0.18 },
  { id: 'RegulatoryChange',  label: 'Regulatory Change',     cluster: 'market',       risk: 0.15 },
  { id: 'SupplierDelay',     label: 'Supplier Delay',        cluster: 'supply_chain', risk: 0.28 },
  { id: 'SupplierBankrupt',  label: 'Supplier Bankruptcy',   cluster: 'supply_chain', risk: 0.10 },
  { id: 'TransportDisrupt',  label: 'Transport Disruption',  cluster: 'supply_chain', risk: 0.20 },
  { id: 'InventoryShortage', label: 'Inventory Shortage',    cluster: 'supply_chain', risk: 0.15 },
  { id: 'PaymentDefault',    label: 'Payment Default Risk',  cluster: 'financial',    risk: 0.25 },
  { id: 'CashFlowStress',    label: 'Cash Flow Stress',      cluster: 'financial',    risk: 0.30 },
  { id: 'CostOverrun',       label: 'Contract Cost Overrun', cluster: 'financial',    risk: 0.35 },
  { id: 'DeliveryFailure',   label: 'Delivery Failure',      cluster: 'operational',  risk: 0.45 },
  { id: 'SLAViolation',      label: 'SLA Violation',         cluster: 'operational',  risk: 0.30 },
  { id: 'ProjectDelay',      label: 'Project Delay',         cluster: 'operational',  risk: 0.38 },
  { id: 'ContractAmbiguity', label: 'Contract Ambiguity',    cluster: 'contract',     risk: 0.40 },
  { id: 'ClauseConflict',    label: 'Clause Conflict',       cluster: 'contract',     risk: 0.35 },
  { id: 'LiabilityExposure', label: 'Liability Exposure',    cluster: 'contract',     risk: 0.45 },
  { id: 'RenegotiationRisk', label: 'Renegotiation Risk',    cluster: 'contract',     risk: 0.42 },
  { id: 'ContractRisk',      label: 'Contract Risk',         cluster: 'contract',     risk: 0.58 },
  { id: 'DisputeTrigger',    label: 'Dispute Trigger',       cluster: 'legal',        risk: 0.55 },
  { id: 'DisputeEscalation', label: 'Dispute Escalation',    cluster: 'legal',        risk: 0.48 },
  { id: 'ArbitrationInit',   label: 'Arbitration Initiated', cluster: 'legal',        risk: 0.40 },
  { id: 'LegalCostExposure', label: 'Legal Cost Exposure',   cluster: 'legal',        risk: 0.50 },
  { id: 'DisputeProb',       label: 'Dispute Probability',   cluster: 'legal',        risk: 0.65 },
];

const STATIC_EDGES = [
  ['WarRisk','CommodityShock'], ['WarRisk','EnergyPriceShock'], ['WarRisk','SanctionsRisk'],
  ['SanctionsRisk','SupplierDelay'], ['PoliticalInstab','CurrencyVolat'],
  ['InflationRisk','CostOverrun'], ['CurrencyVolat','CashFlowStress'],
  ['CommodityShock','CostOverrun'], ['EnergyPriceShock','DeliveryFailure'],
  ['CompetitionInc','DemandDecline'], ['DemandDecline','SupplierBankrupt'],
  ['RegulatoryChange','ContractAmbiguity'],
  ['SupplierDelay','DeliveryFailure'], ['SupplierBankrupt','SupplierDelay'],
  ['TransportDisrupt','DeliveryFailure'], ['InventoryShortage','DeliveryFailure'],
  ['PaymentDefault','CashFlowStress'], ['CashFlowStress','ProjectDelay'],
  ['CostOverrun','ContractRisk'], ['DeliveryFailure','ContractRisk'],
  ['SLAViolation','ContractRisk'], ['ProjectDelay','RenegotiationRisk'],
  ['ContractAmbiguity','ClauseConflict'], ['ClauseConflict','DisputeTrigger'],
  ['LiabilityExposure','DisputeTrigger'], ['RenegotiationRisk','DisputeEscalation'],
  ['ContractRisk','DisputeTrigger'], ['DisputeTrigger','DisputeEscalation'],
  ['DisputeEscalation','ArbitrationInit'], ['ArbitrationInit','LegalCostExposure'],
  ['DisputeEscalation','DisputeProb'], ['ContractRisk','DisputeProb'],
];

const CLUSTER_COLOR = {
  geo:          { node: '#dc2626', edge: '#ef4444', text: '#fca5a5' },
  macro:        { node: '#d97706', edge: '#f59e0b', text: '#fcd34d' },
  market:       { node: '#7c3aed', edge: '#8b5cf6', text: '#c4b5fd' },
  supply_chain: { node: '#0369a1', edge: '#0ea5e9', text: '#7dd3fc' },
  financial:    { node: '#047857', edge: '#10b981', text: '#6ee7b7' },
  operational:  { node: '#b45309', edge: '#f59e0b', text: '#fde68a' },
  contract:     { node: '#1d4ed8', edge: '#3b82f6', text: '#93c5fd' },
  legal:        { node: '#6d28d9', edge: '#a78bfa', text: '#ddd6fe' },
};

// ── Canvas-based fallback graph renderer ──────────────────────────────────
function StaticNeoGraph({ signals = {}, isFullscreen = false }) {
  const canvasRef = useRef(null);
  const animRef   = useRef(null);
  const posRef    = useRef({});
  const velRef    = useRef({});
  const [selected, setSelected] = useState(null);
  const canvasHeight = isFullscreen ? window.innerHeight - 250 : 680;

  // Assign initial positions in cluster rings
  useEffect(() => {
    const clusterOrder = ['geo','macro','market','supply_chain','financial','operational','contract','legal'];
    const cx = 540, cy = 340, ringR = [80, 150, 220, 290, 360, 430, 500, 570];
    const byCluster = {};
    STATIC_NODES.forEach(n => {
      byCluster[n.cluster] = byCluster[n.cluster] || [];
      byCluster[n.cluster].push(n.id);
    });
    const pos = {};
    const vel = {};
    clusterOrder.forEach((cl, ci) => {
      const ids = byCluster[cl] || [];
      ids.forEach((id, ii) => {
        const angle = (ii / ids.length) * 2 * Math.PI + ci * 0.3;
        pos[id] = { x: cx + ringR[ci] * Math.cos(angle), y: cy + ringR[ci] * Math.sin(angle) };
        vel[id] = { x: 0, y: 0 };
      });
    });
    posRef.current = pos;
    velRef.current = vel;
  }, []);

  // Force-directed layout + animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;

    const draw = () => {
      const pos = posRef.current;
      const vel = velRef.current;

      // Force-directed step
      const K = 80, REPEL = 8000, DAMP = 0.85;
      STATIC_NODES.forEach(a => {
        STATIC_NODES.forEach(b => {
          if (a.id === b.id) return;
          const dx = pos[a.id].x - pos[b.id].x;
          const dy = pos[a.id].y - pos[b.id].y;
          const d  = Math.sqrt(dx*dx + dy*dy) || 1;
          const f  = REPEL / (d * d);
          vel[a.id].x += (dx / d) * f;
          vel[a.id].y += (dy / d) * f;
        });
      });
      STATIC_EDGES.forEach(([s, t]) => {
        if (!pos[s] || !pos[t]) return;
        const dx = pos[t].x - pos[s].x;
        const dy = pos[t].y - pos[s].y;
        const d  = Math.sqrt(dx*dx + dy*dy) || 1;
        const f  = (d - K) * 0.02;
        vel[s].x += (dx / d) * f;
        vel[s].y += (dy / d) * f;
        vel[t].x -= (dx / d) * f;
        vel[t].y -= (dy / d) * f;
      });
      // Center pull
      const cx = W/2, cy = H/2;
      STATIC_NODES.forEach(n => {
        vel[n.id].x += (cx - pos[n.id].x) * 0.001;
        vel[n.id].y += (cy - pos[n.id].y) * 0.001;
        vel[n.id].x *= DAMP;
        vel[n.id].y *= DAMP;
        pos[n.id].x += vel[n.id].x;
        pos[n.id].y += vel[n.id].y;
        // clamp
        pos[n.id].x = Math.max(60, Math.min(W-60, pos[n.id].x));
        pos[n.id].y = Math.max(30, Math.min(H-30, pos[n.id].y));
      });

      // Draw with enhanced visuals
      ctx.clearRect(0, 0, W, H);

      // Background with subtle grid
      ctx.fillStyle = '#020617';
      ctx.fillRect(0, 0, W, H);

      // Draw grid pattern
      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 0.5;
      for (let i = 0; i < W; i += 50) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, H);
        ctx.stroke();
      }
      for (let i = 0; i < H; i += 50) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(W, i);
        ctx.stroke();
      }

      // Draw edges with gradients and glow
      STATIC_EDGES.forEach(([s, t]) => {
        if (!pos[s] || !pos[t]) return;
        const sNode = STATIC_NODES.find(n => n.id === s);
        const tNode = STATIC_NODES.find(n => n.id === t);
        const prob  = signals[s] ?? sNode?.risk ?? 0.2;

        // Edge gradient
        const gradient = ctx.createLinearGradient(pos[s].x, pos[s].y, pos[t].x, pos[t].y);
        const sColor = CLUSTER_COLOR[sNode?.cluster]?.edge || '#475569';
        const tColor = CLUSTER_COLOR[tNode?.cluster]?.edge || '#475569';

        if (prob > 0.6) {
          gradient.addColorStop(0, '#ef4444aa');
          gradient.addColorStop(1, '#dc2626aa');
        } else if (prob > 0.4) {
          gradient.addColorStop(0, sColor + 'aa');
          gradient.addColorStop(0.5, '#f59e0baa');
          gradient.addColorStop(1, tColor + 'aa');
        } else {
          gradient.addColorStop(0, sColor + '66');
          gradient.addColorStop(1, tColor + '66');
        }

        // Edge shadow/glow
        if (prob > 0.5) {
          ctx.shadowBlur = 12;
          ctx.shadowColor = prob > 0.6 ? '#ef4444' : '#f59e0b';
        }

        ctx.beginPath();
        ctx.moveTo(pos[s].x, pos[s].y);
        ctx.lineTo(pos[t].x, pos[t].y);
        ctx.strokeStyle = gradient;
        ctx.lineWidth   = 1 + prob * 3;
        ctx.stroke();

        ctx.shadowBlur = 0;

        // Enhanced arrow
        const angle = Math.atan2(pos[t].y - pos[s].y, pos[t].x - pos[s].x);
        const ax = pos[t].x - 18 * Math.cos(angle);
        const ay = pos[t].y - 18 * Math.sin(angle);
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax - 10*Math.cos(angle-0.4), ay - 10*Math.sin(angle-0.4));
        ctx.lineTo(ax - 10*Math.cos(angle+0.4), ay - 10*Math.sin(angle+0.4));
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();
      });

      // Draw nodes with gradients and effects
      STATIC_NODES.forEach(n => {
        const p  = pos[n.id];
        if (!p) return;
        const prob   = signals[n.id] ?? n.risk;
        const colors = CLUSTER_COLOR[n.cluster] || CLUSTER_COLOR['contract'];
        const r      = 12 + prob * 18;
        const isSelected = selected === n.id;

        // Outer glow (larger for high risk or selected)
        if (prob > 0.4 || isSelected) {
          const glowRadius = r + (isSelected ? 16 : 8 + prob * 8);
          const glowGradient = ctx.createRadialGradient(p.x, p.y, r, p.x, p.y, glowRadius);

          if (isSelected) {
            glowGradient.addColorStop(0, colors.node + 'dd');
            glowGradient.addColorStop(0.5, colors.edge + '88');
            glowGradient.addColorStop(1, colors.edge + '00');
          } else if (prob > 0.6) {
            glowGradient.addColorStop(0, '#ef4444aa');
            glowGradient.addColorStop(0.6, '#ef444444');
            glowGradient.addColorStop(1, '#ef444400');
          } else if (prob > 0.4) {
            glowGradient.addColorStop(0, '#f59e0baa');
            glowGradient.addColorStop(0.6, '#f59e0b44');
            glowGradient.addColorStop(1, '#f59e0b00');
          }

          ctx.beginPath();
          ctx.arc(p.x, p.y, glowRadius, 0, Math.PI*2);
          ctx.fillStyle = glowGradient;
          ctx.fill();
        }

        // Node gradient
        const nodeGradient = ctx.createRadialGradient(p.x - r*0.3, p.y - r*0.3, r * 0.1, p.x, p.y, r);
        nodeGradient.addColorStop(0, colors.text);
        nodeGradient.addColorStop(0.5, colors.node);
        nodeGradient.addColorStop(1, colors.edge);

        // Node circle
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI*2);
        ctx.fillStyle = nodeGradient;
        ctx.fill();

        // Border with shadow
        ctx.strokeStyle = isSelected ? '#fbbf24' : colors.edge;
        ctx.lineWidth = isSelected ? 4 : 2.5;
        ctx.shadowBlur = isSelected ? 8 : 4;
        ctx.shadowColor = isSelected ? '#fbbf24' : colors.node;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Inner highlight
        ctx.beginPath();
        ctx.arc(p.x - r*0.25, p.y - r*0.25, r*0.3, 0, Math.PI*2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.fill();

        // Label with background
        const label = n.label.length > 14 ? n.label.slice(0,13)+'…' : n.label;
        ctx.font = `600 ${Math.min(12, 8 + prob*6)}px Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const labelY = p.y + r + 16;
        const labelWidth = ctx.measureText(label).width;

        // Label background
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.fillRect(p.x - labelWidth/2 - 4, labelY - 8, labelWidth + 8, 16);

        // Label border
        ctx.strokeStyle = colors.edge + '44';
        ctx.lineWidth = 1;
        ctx.strokeRect(p.x - labelWidth/2 - 4, labelY - 8, labelWidth + 8, 16);

        // Label text
        ctx.fillStyle = '#f1f5f9';
        ctx.fillText(label, p.x, labelY);

        // Risk percentage badge with background
        ctx.font = 'bold 11px Inter, sans-serif';
        const pctText = `${(prob*100).toFixed(0)}%`;
        const pctWidth = ctx.measureText(pctText).width;

        // Badge background circle
        ctx.beginPath();
        ctx.arc(p.x, p.y, r*0.5, 0, Math.PI*2);
        ctx.fillStyle = prob > 0.6 ? '#dc2626' : prob > 0.35 ? '#d97706' : '#059669';
        ctx.fill();

        // Badge text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(pctText, p.x, p.y);
      });

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animRef.current);
  }, [selected, signals]);

  // Click detection
  const handleClick = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const pos = posRef.current;
    let hit = null;
    STATIC_NODES.forEach(n => {
      const p = pos[n.id];
      if (!p) return;
      const prob = signals[n.id] ?? n.risk;
      const r = 10 + prob * 14;
      const dx = mx - p.x, dy = my - p.y;
      if (dx*dx + dy*dy < r*r) hit = n;
    });
    setSelected(hit ? hit.id : null);
  };

  const selNode = STATIC_NODES.find(n => n.id === selected);

  return (
    <div style={{ position: 'relative' }}>
      <canvas
        ref={canvasRef}
        width={1080}
        height={canvasHeight}
        onClick={handleClick}
        style={{ width: '100%', height: canvasHeight, borderRadius: 12, cursor: 'crosshair', display: 'block', border: '1px solid #1e293b' }}
      />
      {selNode && (
        <div style={{
          position: 'absolute', top: 12, right: 12,
          background: '#0f172a', border: `1px solid ${CLUSTER_COLOR[selNode.cluster]?.edge || '#334155'}`,
          borderRadius: 10, padding: '14px 18px', minWidth: 200,
        }}>
          <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: 14, marginBottom: 6 }}>{selNode.label}</div>
          <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>Cluster: <b style={{ color: '#94a3b8' }}>{selNode.cluster.replace('_',' ')}</b></div>
          <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>Base Risk: <b style={{ color: signals[selNode.id] != null ? '#a78bfa' : '#10b981' }}>{((signals[selNode.id] ?? selNode.risk)*100).toFixed(0)}%</b></div>
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 10, color: '#475569', marginBottom: 4 }}>CAUSES →</div>
            {STATIC_EDGES.filter(([s]) => s === selNode.id).map(([,t]) => (
              <div key={t} style={{ fontSize: 11, color: '#3b82f6' }}>→ {STATIC_NODES.find(n=>n.id===t)?.label || t}</div>
            ))}
          </div>
          <button onClick={() => setSelected(null)} style={{ marginTop: 10, background: 'none', border: '1px solid #334155', borderRadius: 6, padding: '3px 10px', color: '#94a3b8', fontSize: 11, cursor: 'pointer' }}>Close</button>
        </div>
      )}
    </div>
  );
}

// ── Neovis.js live graph ───────────────────────────────────────────────────
function NeoVisLive({ onError, isFullscreen = false }) {
  const containerRef = useRef(null);

  useEffect(() => {
    let viz;
    import('neovis.js').then(({ default: NeoVis }) => {
      const config = {
        containerId: 'neovis-container',
        neo4j: {
          serverUrl:      BOLT_URL,
          serverUser:     NEO4J_USER,
          serverPassword: NEO4J_PASS,
        },
        visConfig: {
          nodes: {
            shape: 'dot',
            font: {
              color: '#f1f5f9',
              size: 13,
              face: 'Inter, system-ui, -apple-system, sans-serif',
              background: 'rgba(2, 6, 23, 0.95)',
              strokeWidth: 3,
              strokeColor: '#0f172a',
              bold: { color: '#ffffff', size: 15, face: 'Inter' }
            },
            borderWidth: 3,
            borderWidthSelected: 5,
            size: 25,
            shadow: {
              enabled: true,
              color: 'rgba(99, 102, 241, 0.5)',
              size: 15,
              x: 0,
              y: 0
            },
            color: {
              border: '#6366f1',
              background: '#3b82f6',
              highlight: {
                border: '#fbbf24',
                background: '#f59e0b'
              },
              hover: {
                border: '#a78bfa',
                background: '#8b5cf6'
              }
            },
            shapeProperties: {
              borderDashes: false,
              borderRadius: 6
            }
          },
          edges: {
            arrows: {
              to: {
                enabled: true,
                scaleFactor: 0.8,
                type: 'arrow'
              }
            },
            smooth: {
              enabled: true,
              type: 'dynamic',
              roundness: 0.5
            },
            color: {
              color: 'rgba(71, 85, 105, 0.6)',
              highlight: '#ef4444',
              hover: '#a78bfa',
              inherit: false,
              opacity: 0.8
            },
            width: 2,
            selectionWidth: 4,
            hoverWidth: 3,
            shadow: {
              enabled: true,
              color: 'rgba(139, 92, 246, 0.3)',
              size: 8,
              x: 0,
              y: 0
            }
          },
          physics: {
            enabled: true,
            barnesHut: {
              gravitationalConstant: -5000,
              centralGravity: 0.15,
              springLength: 200,
              springConstant: 0.02,
              damping: 0.92,
              avoidOverlap: 0.5
            },
            stabilization: {
              enabled: true,
              iterations: 200,
              updateInterval: 25,
              fit: true
            },
            timestep: 0.35,
            adaptiveTimestep: true,
            maxVelocity: 30,
            minVelocity: 0.75
          },
          interaction: {
            hover: true,
            hoverConnectedEdges: true,
            selectConnectedEdges: true,
            tooltipDelay: 50,
            hideEdgesOnDrag: false,
            hideEdgesOnZoom: false,
            navigationButtons: true,
            keyboard: {
              enabled: true,
              speed: { x: 10, y: 10, zoom: 0.02 },
              bindToWindow: false
            },
            zoomView: true,
            zoomSpeed: 1
          },
          layout: {
            improvedLayout: true,
            clusterThreshold: 150,
            hierarchical: false
          },
          background: '#020617',
        },
        labels: {
          RiskNode: {
            label: 'label',
            value: 'risk',
            group: 'cluster',
            [NeoVis.NEOVIS_DEFAULT_CONFIG]: {
              caption: 'label',
              size: {
                property: 'risk',
                type: 'number',
                min: 10,
                max: 30
              },
              community: 'cluster',
              title_properties: ['label', 'name', 'risk', 'cluster'],
            },
          },
        },
        relationships: {
          CAUSES: {
            value: 'prob',
            [NeoVis.NEOVIS_DEFAULT_CONFIG]: {
              caption: false,
              thickness: {
                property: 'prob',
                type: 'number',
                min: 1,
                max: 3
              },
            },
          },
        },
        initialCypher: CYPHER_QUERY,
      };

      try {
        viz = new NeoVis(config);

        // Apply custom cluster colors with gradients after completion
        viz.registerOnEvent('completed', () => {
          const network = viz._network;
          if (!network) return;

          const nodes = network.body.data.nodes;
          const updates = [];

          nodes.forEach((node) => {
            const cluster = node.cluster || 'contract';
            const colors = CLUSTER_COLOR[cluster] || CLUSTER_COLOR['contract'];
            const risk = node.risk || 0.3;

            // Size based on risk (higher risk = larger node)
            const nodeSize = 20 + (risk * 30);

            // Shadow color based on risk level
            const shadowColor = risk > 0.5
              ? 'rgba(239, 68, 68, 0.6)'   // High risk: red glow
              : risk > 0.3
                ? 'rgba(251, 191, 36, 0.6)' // Medium risk: amber glow
                : 'rgba(16, 185, 129, 0.4)'; // Low risk: green glow

            updates.push({
              id: node.id,
              size: nodeSize,
              color: {
                background: colors.node,
                border: colors.edge,
                highlight: {
                  background: colors.text,
                  border: '#fbbf24'
                },
                hover: {
                  background: colors.edge,
                  border: colors.text
                }
              },
              shadow: {
                enabled: true,
                color: shadowColor,
                size: 10 + (risk * 15),
                x: 0,
                y: 0
              },
              borderWidth: 3 + (risk * 2),
              font: {
                size: 11 + (risk * 4),
                color: '#f1f5f9',
                bold: risk > 0.5 ? { mod: 'bold' } : undefined
              }
            });
          });

          if (updates.length > 0) {
            nodes.update(updates);
          }

          // Update edges with risk-based styling
          const edges = network.body.data.edges;
          const edgeUpdates = [];

          edges.forEach((edge) => {
            const prob = edge.prob || 0.5;
            const edgeColor = prob > 0.7
              ? 'rgba(239, 68, 68, 0.8)'   // High probability: red
              : prob > 0.5
                ? 'rgba(251, 191, 36, 0.7)' // Medium probability: amber
                : 'rgba(71, 85, 105, 0.6)';  // Low probability: gray

            edgeUpdates.push({
              id: edge.id,
              width: 1 + (prob * 3),
              color: {
                color: edgeColor,
                highlight: '#ef4444',
                hover: '#f59e0b'
              },
              shadow: {
                enabled: prob > 0.6,
                color: prob > 0.7 ? 'rgba(239, 68, 68, 0.4)' : 'rgba(251, 191, 36, 0.3)',
                size: 6 + (prob * 8)
              },
              dashes: prob < 0.3 ? [5, 5] : false
            });
          });

          if (edgeUpdates.length > 0) {
            edges.update(edgeUpdates);
          }
        });

        viz.registerOnEvent('error', (e) => onError(e));
        viz.render();
      } catch (e) {
        onError(e);
      }
    }).catch(onError);

    return () => { try { viz?.clearNetwork(); } catch (_) {} };
  }, [onError]);

  return (
    <div
      id="neovis-container"
      ref={containerRef}
      style={{
        width: '100%',
        height: isFullscreen ? 'calc(100vh - 200px)' : 600,
        borderRadius: 12,
        border: '1px solid #1e293b',
        background: '#020617'
      }}
    />
  );
}

// ── Main exported panel ───────────────────────────────────────────────────
export default function NeoVizPanel() {
  const [mode, setMode]   = useState('static'); // 'static' | 'live'
  const [neo4jOk, setNeo4jOk] = useState(null); // null=untested, true, false
  const [connecting, setConnecting] = useState(false);
  const [liveError, setLiveError]   = useState(null);
  const [liveSignals, setLiveSignals] = useState({});
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  const tryConnect = () => {
    setConnecting(true);
    setLiveError(null);
    // Try a WebSocket test to Neo4j Bolt port
    try {
      const ws = new WebSocket('ws://localhost:7687');
      ws.onopen = () => { ws.close(); setNeo4jOk(true); setMode('live'); setConnecting(false); };
      ws.onerror = () => { setNeo4jOk(false); setConnecting(false); setLiveError('Neo4j not reachable at bolt://localhost:7687'); };
      setTimeout(() => { if (connecting) { ws.close(); setNeo4jOk(false); setConnecting(false); setLiveError('Connection timeout'); } }, 3000);
    } catch (e) {
      setNeo4jOk(false);
      setConnecting(false);
      setLiveError(String(e));
    }
  };

  const handleLiveError = (e) => {
    setLiveError(String(e?.message || e));
    setMode('static');
    setNeo4jOk(false);
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.error('Error attempting to enable fullscreen:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        background: isFullscreen ? '#020617' : 'transparent',
        padding: isFullscreen ? '20px' : '0',
        height: isFullscreen ? '100vh' : 'auto',
        overflow: isFullscreen ? 'auto' : 'visible',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <h3 style={{ color: '#e2e8f0', margin: 0, fontSize: 18, fontWeight: 700 }}>Neo4j Risk Intelligence Graph</h3>
          <p style={{ color: '#64748b', fontSize: 12, margin: 0 }}>
            {mode === 'live'
              ? 'Live Neo4j Bolt connection · Neovis.js rendering · Click nodes to explore causal paths'
              : 'Force-directed canvas graph · 30 risk nodes · 8 cluster layers · Click nodes for details'}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Status badge */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 5,
            background: neo4jOk ? '#05300020' : '#1e293b',
            border: `1px solid ${neo4jOk ? '#10b981' : '#334155'}`,
            borderRadius: 6, padding: '4px 10px',
          }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: neo4jOk ? '#10b981' : '#475569' }} />
            <span style={{ color: neo4jOk ? '#10b981' : '#64748b', fontSize: 11 }}>
              {neo4jOk ? 'Neo4j Connected' : 'Neo4j Offline'}
            </span>
          </div>

          {/* Mode toggle */}
          <div style={{ display: 'flex', background: '#1e293b', borderRadius: 8, padding: 2 }}>
            {[['static','Static Canvas'],['live','Live Neo4j']].map(([m,lbl]) => (
              <button key={m} onClick={() => m === 'live' ? tryConnect() : setMode('static')} style={{
                padding: '5px 14px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 12,
                background: mode === m ? 'linear-gradient(135deg,#6d28d9,#1d4ed8)' : 'transparent',
                color: mode === m ? '#fff' : '#64748b',
              }}>
                {m === 'live' && connecting ? 'Connecting…' : lbl}
              </button>
            ))}
          </div>

          {/* Fullscreen toggle */}
          <button
            onClick={toggleFullscreen}
            style={{
              padding: '6px 12px',
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8,
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#334155';
              e.currentTarget.style.color = '#e2e8f0';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#1e293b';
              e.currentTarget.style.color = '#94a3b8';
            }}
            title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
          >
            {isFullscreen ? <Minimize size={16} /> : <Maximize size={16} />}
            {isFullscreen ? 'Exit' : 'Fullscreen'}
          </button>
        </div>
      </div>

      {/* Error banner */}
      {liveError && (
        <div style={{ background: '#450a0a', border: '1px solid #ef4444', borderRadius: 8, padding: '8px 14px', marginBottom: 12, fontSize: 12, color: '#fca5a5' }}>
          ⚠ Neo4j error: {liveError} — showing static graph fallback.
          <span style={{ color: '#94a3b8', marginLeft: 8 }}>
            To use live mode, start Neo4j Desktop and seed nodes with <code style={{ color: '#a78bfa' }}>CREATE (r:RiskNode {'{'} name:"WarRisk", risk:0.05, cluster:"geo" {'}'})</code>
          </span>
        </div>
      )}

      {/* Graph */}
      {mode === 'live' && neo4jOk ? (
        <NeoVisLive onError={handleLiveError} isFullscreen={isFullscreen} />
      ) : (
        <StaticNeoGraph signals={liveSignals} isFullscreen={isFullscreen} />
      )}

      {/* Enhanced Legend */}
      <div style={{
        marginTop: 16,
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        border: '1px solid #334155',
        borderRadius: 12,
        padding: '16px 20px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1), 0 0 20px rgba(99, 102, 241, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <span style={{ color: '#94a3b8', fontSize: 13, fontWeight: 600 }}>Risk Clusters</span>
          <span style={{ color: '#64748b', fontSize: 11 }}>
            {mode === 'live' ? '50 nodes · 67 edges' : '30 nodes · 32 edges'}
          </span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          {Object.entries(CLUSTER_COLOR).map(([cl, c]) => (
            <div
              key={cl}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: `linear-gradient(135deg, ${c.node}22 0%, ${c.edge}11 100%)`,
                border: `1px solid ${c.edge}66`,
                borderRadius: 8,
                padding: '6px 14px',
                boxShadow: `0 2px 4px ${c.node}22, inset 0 1px 0 ${c.text}11`,
                transition: 'all 0.3s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = `linear-gradient(135deg, ${c.node}44 0%, ${c.edge}22 100%)`;
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = `0 4px 8px ${c.node}44, inset 0 1px 0 ${c.text}22`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = `linear-gradient(135deg, ${c.node}22 0%, ${c.edge}11 100%)`;
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = `0 2px 4px ${c.node}22, inset 0 1px 0 ${c.text}11`;
              }}
            >
              <div style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: `radial-gradient(circle at 30% 30%, ${c.text}, ${c.node})`,
                boxShadow: `0 0 8px ${c.node}, inset 0 1px 2px ${c.text}44`,
                border: `2px solid ${c.edge}`
              }} />
              <span style={{ color: c.text, fontSize: 12, fontWeight: 500, textTransform: 'capitalize' }}>
                {cl.replace('_',' ')}
              </span>
            </div>
          ))}
        </div>
        <div style={{
          marginTop: 14,
          paddingTop: 12,
          borderTop: '1px solid #334155',
          display: 'flex',
          gap: 24,
          flexWrap: 'wrap'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 16, height: 16, borderRadius: '50%', background: 'radial-gradient(circle at 30% 30%, #fca5a5, #ef4444)', boxShadow: '0 0 8px #ef4444' }} />
            <span style={{ color: '#94a3b8', fontSize: 11 }}>High Risk (&gt;60%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 16, height: 16, borderRadius: '50%', background: 'radial-gradient(circle at 30% 30%, #fde68a, #f59e0b)', boxShadow: '0 0 8px #f59e0b' }} />
            <span style={{ color: '#94a3b8', fontSize: 11 }}>Medium Risk (30-60%)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 16, height: 16, borderRadius: '50%', background: 'radial-gradient(circle at 30% 30%, #6ee7b7, #10b981)', boxShadow: '0 0 8px #10b981' }} />
            <span style={{ color: '#94a3b8', fontSize: 11 }}>Low Risk (&lt;30%)</span>
          </div>
          <div style={{ marginLeft: 'auto', color: '#64748b', fontSize: 11, fontStyle: 'italic' }}>
            Node size ∝ risk probability · Edge thickness ∝ causal strength
          </div>
        </div>
      </div>

      {/* How to connect Neo4j */}
      <div style={{ marginTop: 16, background: '#0f172a', border: '1px solid #1e293b', borderRadius: 10, padding: '14px 18px' }}>
        <div style={{ color: '#94a3b8', fontWeight: 700, fontSize: 13, marginBottom: 8 }}>Connect Live Neo4j (optional)</div>
        <div style={{ color: '#64748b', fontSize: 12, lineHeight: 1.6 }}>
          1. Install <b style={{ color: '#a78bfa' }}>Neo4j Desktop</b> → create a project → start a local database<br />
          2. Open Neo4j Browser → run the seed script to create <code style={{ color: '#3b82f6' }}>:RiskNode</code> nodes and <code style={{ color: '#3b82f6' }}>:CAUSES</code> relationships<br />
          3. Set password to <code style={{ color: '#3b82f6' }}>password</code> (or update <code style={{ color: '#3b82f6' }}>NEO4J_PASS</code> in <code style={{ color: '#3b82f6' }}>NeoVizPanel.jsx</code>)<br />
          4. Click <b style={{ color: '#e2e8f0' }}>Live Neo4j</b> button above — Neovis.js will render the graph via Bolt WebSocket
        </div>
        <div style={{ marginTop: 10, background: '#020617', borderRadius: 8, padding: '10px 14px', fontFamily: 'monospace', fontSize: 11, color: '#7dd3fc', lineHeight: 1.8 }}>
          {`// Seed script — paste in Neo4j Browser\nCREATE (a:RiskNode {name:"WarRisk", risk:0.05, cluster:"geo"})\nCREATE (b:RiskNode {name:"CommodityShock", risk:0.40, cluster:"macro"})\nCREATE (c:RiskNode {name:"ContractRisk", risk:0.58, cluster:"contract"})\nCREATE (d:RiskNode {name:"DisputeProbability", risk:0.65, cluster:"legal"})\nCREATE (a)-[:CAUSES {prob:0.7}]->(b)\nCREATE (b)-[:CAUSES {prob:0.6}]->(c)\nCREATE (c)-[:CAUSES {prob:0.8}]->(d)`}
        </div>
      </div>
    </div>
  );
}
