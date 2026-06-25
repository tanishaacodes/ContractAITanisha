/**
 * Contract Concept Risk Topology Engine
 * ======================================
 * Visualizes Pearson correlation between legal concepts across 5 contract archetypes.
 */

import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  MarkerType,
  getBezierPath,
  BaseEdge,
  EdgeLabelRenderer,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts';
import {
  getConceptGraphByType,
  getCorrelationMatrix,
  getConceptSummary,
  getContractConceptGraph,
  compareContracts,
  getConceptCentrality,
  getConceptCommunities,
} from '../services/conceptGraphService';
import api from '../utils/api';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CONTRACT_TYPES = [
  { id: 'MSA',        label: 'MSA',        color: '#4C8EDA', icon: '📋', short: 'Master Service Agreement',    density: 'high',      tag: 'Liability Dense'     },
  { id: 'SaaS',       label: 'SaaS',       color: '#68BC00', icon: '☁️',  short: 'Software as a Service',      density: 'medium',    tag: 'IP & Data Focus'     },
  { id: 'NDA',        label: 'NDA',        color: '#9063CD', icon: '🔒', short: 'Non-Disclosure Agreement',    density: 'low',       tag: 'Confidentiality Core' },
  { id: 'Employment', label: 'Employment', color: '#F79767', icon: '👔', short: 'Employment Agreement',        density: 'medium',    tag: 'Obligations Hub'     },
  { id: 'EPC',        label: 'EPC',        color: '#F16667', icon: '🏗️', short: 'Engineering Procurement Const.', density: 'very_high', tag: 'Risk Maximum'    },
  { id: 'ALL',        label: 'Global',     color: '#06B6D4', icon: '🌐', short: 'All 5 Archetypes Combined',   density: 'high',      tag: 'Cross-Archetype'     },
];

// Concept role descriptions for node detail panel
const CONCEPT_ROLES = {
  'Termination':     'Governs exit conditions and contract end triggers. High in employment and MSA.',
  'Liability':       'Caps financial exposure. Central in MSA and EPC — anchor concept.',
  'Indemnification': 'Shifts loss between parties. Tightly coupled with Liability across archetypes.',
  'IP Rights':       'Defines ownership of created works. Dominant in NDA and SaaS.',
  'Risk Allocation': 'Distributes contract risk. Core to EPC construction contracts.',
  'Arbitration':     'Dispute resolution mechanism. Concentrated in high-value contracts.',
  'Penalty':         'Financial consequences for breach. EPC-dominant with force multipliers.',
  'Obligations':     'Party duties and performance standards. Strong in Employment and MSA.',
  'Data Protection': 'GDPR/privacy compliance. Rising importance in SaaS/digital contracts.',
  'Force Majeure':   'Unforeseeable event carve-outs. Amplified by EPC and global contracts.',
};

const TABS = [
  { id: 'graph',       label: 'Correlation Graph',    icon: '🕸️' },
  { id: 'matrix',      label: 'Correlation Matrix',   icon: '📊' },
  { id: 'radar',       label: 'Concept Radar',        icon: '📡' },
  { id: 'summary',     label: 'Concept Summary',      icon: '📋' },
  { id: 'contracts',   label: 'Real Contracts',       icon: '📄', badge: 'NEW' },
  { id: 'comparison',  label: 'Compare Contracts',    icon: '⚖️', badge: 'NEW' },
  { id: 'analytics',   label: 'Graph Analytics',      icon: '🔬', badge: 'NEW' },
  { id: 'howto',       label: 'How It Works',         icon: '📖' },
];

const DENSITY_COLORS = {
  low: '#68BC00',
  medium: '#F79767',
  high: '#F16667',
  very_high: '#E8474C',
};

// ---------------------------------------------------------------------------
// Custom Node — circular with Handles on all 4 sides so edges attach
// ---------------------------------------------------------------------------

function ConceptNode({ data, selected }) {
  const size = data.size || 80;
  const strength = data.strength || 0;
  const ringColor = strength >= 0.75 ? '#4ade80' : strength >= 0.50 ? '#fbbf24' : '#f87171';
  const glowPx = Math.round(size * 0.42);

  // Label font: clamp between 11 and 16px, readable at all sizes
  const labelFontSize = Math.min(16, Math.max(11, Math.round(size * 0.148)));
  const valueFontSize = Math.min(12, Math.max(9,  Math.round(size * 0.11)));

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      {/* Invisible handles — required for React Flow edges */}
      <Handle type="source" position={Position.Top}    style={{ opacity: 0, top: '50%', left: '50%' }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, top: '50%', left: '50%' }} />
      <Handle type="source" position={Position.Left}   style={{ opacity: 0, top: '50%', left: '50%' }} />
      <Handle type="source" position={Position.Right}  style={{ opacity: 0, top: '50%', left: '50%' }} />
      <Handle type="target" position={Position.Top}    style={{ opacity: 0, top: '50%', left: '50%' }} />
      <Handle type="target" position={Position.Bottom} style={{ opacity: 0, top: '50%', left: '50%' }} />
      <Handle type="target" position={Position.Left}   style={{ opacity: 0, top: '50%', left: '50%' }} />
      <Handle type="target" position={Position.Right}  style={{ opacity: 0, top: '50%', left: '50%' }} />

      {/* Selection halo */}
      {selected && (
        <div style={{
          position: 'absolute', inset: -8, borderRadius: '50%',
          border: `2.5px solid ${data.color}`,
          boxShadow: `0 0 0 5px ${data.color}33, 0 0 0 10px ${data.color}11`,
          pointerEvents: 'none',
        }} />
      )}

      {/* Strength arc ring SVG */}
      <svg style={{ position: 'absolute', top: -6, left: -6, pointerEvents: 'none' }}
           width={size + 12} height={size + 12}>
        <circle cx={(size+12)/2} cy={(size+12)/2} r={(size+2)/2}
          fill="none" stroke={data.color + '20'} strokeWidth={5} />
        <circle cx={(size+12)/2} cy={(size+12)/2} r={(size+2)/2}
          fill="none" stroke={ringColor} strokeWidth={5}
          strokeDasharray={`${strength * Math.PI * (size+2)} ${Math.PI * (size+2)}`}
          strokeDashoffset={Math.PI * (size+2) * 0.25}
          strokeLinecap="round" opacity={0.9}
        />
      </svg>

      {/* Main circle body */}
      <div style={{
        width: size, height: size, borderRadius: '50%',
        background: `radial-gradient(circle at 32% 28%,
          ${data.color}ee 0%,
          ${data.color}bb 35%,
          ${data.color}66 65%,
          ${data.color}22 100%)`,
        border: `3px solid ${data.color}cc`,
        boxShadow: [
          `0 0 ${glowPx}px ${data.color}55`,
          `0 0 ${Math.round(glowPx * 0.45)}px ${data.color}33`,
          `inset 0 3px 8px rgba(255,255,255,0.28)`,
          `inset 0 -3px 8px rgba(0,0,0,0.40)`,
        ].join(', '),
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        cursor: 'pointer', padding: 8,
        overflow: 'hidden',
      }}>
        {/* Name label — strong shadow for legibility on any background */}
        <div style={{
          color: '#fff',
          fontWeight: 800,
          fontSize: labelFontSize,
          textAlign: 'center',
          lineHeight: 1.2,
          maxWidth: size - 16,
          wordBreak: 'break-word',
          textShadow: [
            '0 0 8px rgba(0,0,0,1)',
            '0 1px 0 rgba(0,0,0,0.9)',
            '0 2px 6px rgba(0,0,0,0.8)',
          ].join(', '),
          letterSpacing: -0.3,
        }}>
          {data.label}
        </div>

        {/* Strength badge */}
        <div style={{
          color: '#fff',
          fontSize: valueFontSize,
          fontWeight: 700,
          marginTop: 5,
          background: 'rgba(0,0,0,0.45)',
          borderRadius: 8,
          padding: '2px 8px',
          border: '1px solid rgba(255,255,255,0.18)',
          textShadow: '0 1px 4px rgba(0,0,0,0.9)',
          letterSpacing: 0.4,
          lineHeight: 1,
        }}>
          {strength.toFixed(2)}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom Edge — curved with weight label in the middle
// ---------------------------------------------------------------------------

function CorrelationEdge({ id, sourceX, sourceY, targetX, targetY, data, style, markerEnd }) {
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, targetX, targetY });
  const weight = data?.weight ?? 0;
  const show = weight > 0.52;
  const isStrong = weight > 0.80;
  const isMedium = weight > 0.65;

  const labelBg = isStrong ? 'rgba(96,165,250,0.18)' : isMedium ? 'rgba(148,163,184,0.14)' : 'rgba(30,41,59,0.75)';
  const labelColor = isStrong ? '#93c5fd' : isMedium ? '#cbd5e1' : '#64748b';
  const labelBorder = isStrong ? '#3b82f666' : isMedium ? '#47556966' : '#1e293b';

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={style} />
      {show && (
        <EdgeLabelRenderer>
          <div style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            background: labelBg,
            border: `1px solid ${labelBorder}`,
            borderRadius: 5,
            padding: '2px 6px',
            fontSize: isStrong ? 10 : 9,
            fontWeight: isStrong ? 800 : 600,
            color: labelColor,
            pointerEvents: 'none',
            zIndex: 10,
            backdropFilter: 'blur(4px)',
            letterSpacing: 0.3,
            boxShadow: isStrong ? '0 0 6px rgba(96,165,250,0.3)' : 'none',
          }}>
            {weight.toFixed(2)}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

const nodeTypes = { conceptNode: ConceptNode };
const edgeTypes = { correlationEdge: CorrelationEdge };

// ---------------------------------------------------------------------------
// Build React Flow nodes/edges from backend data
// ---------------------------------------------------------------------------

function buildFlowElements(graphData, archetypeColor) {
  if (!graphData) return { nodes: [], edges: [] };

  const acColor = archetypeColor || '#4C8EDA';

  // Nodes: keep backend positions, ensure type = conceptNode
  const nodes = (graphData.nodes || []).map(n => ({
    ...n,
    type: 'conceptNode',
    data: { ...n.data },
  }));

  // Edges: rich styling with archetype-colored strokes
  const edges = (graphData.edges || []).map(e => {
    const weight = e.data?.weight ?? 0;
    const animated = weight > 0.80;
    const strokeWidth = Math.max(1.2, weight * 9);

    // Color tiers: strong = archetype accent, medium = muted, weak = very dim
    let strokeColor;
    if (weight > 0.80) strokeColor = acColor;
    else if (weight > 0.65) strokeColor = acColor + 'bb';
    else if (weight > 0.52) strokeColor = '#4b6584';
    else strokeColor = '#2d3748';

    return {
      id: e.id,
      source: e.source,
      target: e.target,
      type: 'correlationEdge',
      animated,
      data: e.data || {},
      markerEnd: animated
        ? { type: MarkerType.ArrowClosed, color: acColor, width: 10, height: 10 }
        : undefined,
      style: {
        stroke: strokeColor,
        strokeWidth,
        opacity: Math.max(0.2, Math.min(1, weight * 1.1)),
        filter: animated ? `drop-shadow(0 0 4px ${acColor}88)` : 'none',
      },
    };
  });

  return { nodes, edges };
}

// ---------------------------------------------------------------------------
// Correlation Matrix Heatmap — improved
// ---------------------------------------------------------------------------

const CONCEPT_COLORS_MAP = {
  'Termination':    '#F16667',
  'Liability':      '#F79767',
  'Indemnification':'#FFD86E',
  'IP Rights':      '#9063CD',
  'Risk Allocation':'#F16667',
  'Arbitration':    '#4C8EDA',
  'Penalty':        '#E8474C',
  'Obligations':    '#F79767',
  'Data Protection':'#68BC00',
  'Force Majeure':  '#06B6D4',
};

function CorrelationHeatmap({ matrix, concepts }) {
  const [tooltip, setTooltip] = useState(null); // {row, col, val, x, y}

  if (!matrix || !concepts) return null;

  // Color: 0=deep blue, 0.5=neutral dark, 1=deep red
  const getColor = (val, isDiag) => {
    if (isDiag) return '#1e3a5f'; // diagonal = muted blue
    if (val >= 0.85) return `rgba(220,38,38,${0.6 + val * 0.4})`;   // strong red
    if (val >= 0.70) return `rgba(249,115,22,${0.5 + val * 0.4})`;  // orange
    if (val >= 0.55) return `rgba(234,179,8,${0.4 + val * 0.3})`;   // yellow
    if (val >= 0.40) return `rgba(100,116,139,0.5)`;                 // neutral
    return `rgba(37,99,235,${0.3 + (0.5 - val) * 0.8})`;            // blue
  };

  const getTextColor = (val, isDiag) => {
    if (isDiag) return '#93c5fd';
    if (val >= 0.70) return '#fff';
    if (val >= 0.40) return '#e2e8f0';
    return '#bfdbfe';
  };

  const CELL = 58; // cell size px
  const ROW_LABEL_W = 120;
  const HEADER_H = 90;

  return (
    <div>
      {/* Color scale legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <span style={{ color: '#64748b', fontSize: 12, fontWeight: 600 }}>Correlation scale:</span>
        <div style={{ display: 'flex', gap: 0, borderRadius: 6, overflow: 'hidden', border: '1px solid #334155' }}>
          {[
            { label: '< 0.40', bg: 'rgba(37,99,235,0.7)',   text: '#bfdbfe' },
            { label: '0.40–0.55', bg: 'rgba(100,116,139,0.5)', text: '#e2e8f0' },
            { label: '0.55–0.70', bg: 'rgba(234,179,8,0.6)',   text: '#fff' },
            { label: '0.70–0.85', bg: 'rgba(249,115,22,0.8)',  text: '#fff' },
            { label: '> 0.85', bg: 'rgba(220,38,38,0.9)',    text: '#fff' },
          ].map(s => (
            <div key={s.label} style={{
              background: s.bg, padding: '5px 12px',
              fontSize: 11, fontWeight: 600, color: s.text, whiteSpace: 'nowrap',
            }}>{s.label}</div>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 16, height: 16, background: '#1e3a5f', borderRadius: 3, border: '1px solid #334155' }} />
          <span style={{ color: '#64748b', fontSize: 11 }}>Diagonal (self)</span>
        </div>
      </div>

      {/* Matrix */}
      <div style={{ overflowX: 'auto', position: 'relative' }}>
        <table style={{ borderCollapse: 'separate', borderSpacing: 2 }}>
          <thead>
            <tr>
              {/* empty corner */}
              <th style={{ width: ROW_LABEL_W, minWidth: ROW_LABEL_W }} />
              {concepts.map(c => (
                <th key={c} style={{
                  width: CELL, minWidth: CELL,
                  height: HEADER_H, verticalAlign: 'bottom',
                  padding: '0 0 6px 0',
                }}>
                  {/* Diagonal rotated label */}
                  <div style={{
                    display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
                    height: HEADER_H,
                  }}>
                    <div style={{
                      transformOrigin: 'bottom center',
                      transform: 'rotate(-45deg) translateX(-4px)',
                      whiteSpace: 'nowrap',
                      fontSize: 11, fontWeight: 700,
                      color: CONCEPT_COLORS_MAP[c] || '#94a3b8',
                      letterSpacing: 0.3,
                      display: 'flex', alignItems: 'center', gap: 4,
                    }}>
                      <span style={{
                        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                        background: CONCEPT_COLORS_MAP[c] || '#94a3b8',
                        display: 'inline-block',
                      }} />
                      {c}
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {concepts.map((row, ri) => (
              <tr key={row}>
                {/* Row label */}
                <td style={{
                  paddingRight: 10, paddingLeft: 4,
                  fontWeight: 700, fontSize: 12,
                  color: CONCEPT_COLORS_MAP[row] || '#94a3b8',
                  whiteSpace: 'nowrap', verticalAlign: 'middle',
                  width: ROW_LABEL_W,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <span style={{
                      width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
                      background: CONCEPT_COLORS_MAP[row] || '#94a3b8',
                      display: 'inline-block',
                    }} />
                    {row}
                  </div>
                </td>

                {/* Cells */}
                {concepts.map((col, ci) => {
                  const val = matrix?.[row]?.[col] ?? 0;
                  const isDiag = row === col;
                  const bg = getColor(val, isDiag);
                  const tc = getTextColor(val, isDiag);
                  const isHovered = tooltip?.row === row && tooltip?.col === col;

                  return (
                    <td
                      key={col}
                      onMouseEnter={(e) => setTooltip({ row, col, val, isDiag })}
                      onMouseLeave={() => setTooltip(null)}
                      style={{
                        width: CELL, height: CELL,
                        background: bg,
                        textAlign: 'center', verticalAlign: 'middle',
                        fontSize: isDiag ? 12 : 11,
                        fontWeight: isDiag ? 800 : val >= 0.80 ? 700 : 400,
                        color: tc,
                        borderRadius: 5,
                        cursor: 'default',
                        transition: 'transform 0.1s, box-shadow 0.1s',
                        transform: isHovered ? 'scale(1.12)' : 'scale(1)',
                        boxShadow: isHovered
                          ? `0 0 0 2px #fff4, 0 4px 16px ${bg}`
                          : 'none',
                        position: 'relative',
                        zIndex: isHovered ? 10 : 1,
                      }}
                    >
                      {isDiag ? '—' : val.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>

        {/* Hover tooltip */}
        {tooltip && !tooltip.isDiag && (
          <div style={{
            position: 'fixed',
            bottom: 24, right: 24,
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 10,
            padding: '12px 18px',
            fontSize: 13,
            color: '#e2e8f0',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            zIndex: 1000,
            pointerEvents: 'none',
            minWidth: 220,
          }}>
            <div style={{ fontWeight: 700, marginBottom: 8, color: '#f1f5f9', fontSize: 14 }}>
              Correlation Detail
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                <span style={{ color: '#64748b' }}>Concept A</span>
                <span style={{ color: CONCEPT_COLORS_MAP[tooltip.row] || '#94a3b8', fontWeight: 700 }}>{tooltip.row}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                <span style={{ color: '#64748b' }}>Concept B</span>
                <span style={{ color: CONCEPT_COLORS_MAP[tooltip.col] || '#94a3b8', fontWeight: 700 }}>{tooltip.col}</span>
              </div>
              <div style={{ borderTop: '1px solid #334155', paddingTop: 8, marginTop: 2, display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Pearson (normalised)</span>
                <span style={{
                  fontWeight: 800, fontSize: 16,
                  color: tooltip.val >= 0.85 ? '#f87171'
                       : tooltip.val >= 0.70 ? '#fb923c'
                       : tooltip.val >= 0.55 ? '#fbbf24'
                       : tooltip.val >= 0.40 ? '#94a3b8'
                       : '#60a5fa',
                }}>{tooltip.val.toFixed(3)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Strength</span>
                <span style={{ color: '#e2e8f0', fontWeight: 600 }}>
                  {tooltip.val >= 0.85 ? 'Very Strong' : tooltip.val >= 0.70 ? 'Strong' : tooltip.val >= 0.55 ? 'Moderate' : tooltip.val >= 0.40 ? 'Weak' : 'Negative / None'}
                </span>
              </div>
              {/* Mini bar */}
              <div style={{ marginTop: 4 }}>
                <div style={{ background: '#0f172a', borderRadius: 3, height: 6, overflow: 'hidden' }}>
                  <div style={{
                    width: `${tooltip.val * 100}%`,
                    height: '100%',
                    background: tooltip.val >= 0.85 ? '#ef4444'
                               : tooltip.val >= 0.70 ? '#f97316'
                               : tooltip.val >= 0.55 ? '#eab308'
                               : tooltip.val >= 0.40 ? '#64748b'
                               : '#3b82f6',
                    borderRadius: 3,
                    transition: 'width 0.3s',
                  }} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ConceptCorrelationGraph() {
  const [activeTab, setActiveTab]       = useState('graph');
  const [selectedType, setSelectedType] = useState('MSA');
  const [graphData, setGraphData]       = useState(null);
  const [matrixData, setMatrixData]     = useState(null);
  const [summaryData, setSummaryData]   = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // NEW: Real contract analysis state
  const [contracts, setContracts] = useState([]);
  const [selectedContractId, setSelectedContractId] = useState(null);
  const [contractGraphData, setContractGraphData] = useState(null);
  const [contractNodes, setContractNodes, onContractNodesChange] = useNodesState([]);
  const [contractEdges, setContractEdges, onContractEdgesChange] = useEdgesState([]);

  // NEW: Contract comparison state
  const [contract1, setContract1] = useState(null);
  const [contract2, setContract2] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);

  // NEW: Analytics state
  const [analyticsMode, setAnalyticsMode] = useState('archetype'); // 'archetype' or 'contract'
  const [centralityData, setCentralityData] = useState(null);
  const [communitiesData, setCommunitiesData] = useState(null);

  // ------------------------------------------------------------------
  // Load graph for selected archetype
  // ------------------------------------------------------------------
  const loadGraph = useCallback(async (contractType) => {
    setLoading(true);
    setError(null);
    setSelectedNode(null);  // reset node detail on archetype switch
    try {
      const data = await getConceptGraphByType(contractType);
      setGraphData(data);
      const acMeta = CONTRACT_TYPES.find(ct => ct.id === contractType);
      const { nodes: n, edges: e } = buildFlowElements(data, acMeta?.color);
      setNodes(n);
      setEdges(e);
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Failed to load graph');
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  const loadMatrix = useCallback(async () => {
    if (matrixData) return;
    try {
      const data = await getCorrelationMatrix();
      setMatrixData(data);
    } catch (err) {
      setError(err?.response?.data?.error || err.message);
    }
  }, [matrixData]);

  const loadSummary = useCallback(async () => {
    if (summaryData) return;
    try {
      const data = await getConceptSummary();
      setSummaryData(data);
    } catch (err) {
      setError(err?.response?.data?.error || err.message);
    }
  }, [summaryData]);

  useEffect(() => { loadGraph(selectedType); }, [selectedType, loadGraph]);

  useEffect(() => {
    if (activeTab === 'matrix') loadMatrix();
    if (activeTab === 'summary' || activeTab === 'radar') loadSummary();
  }, [activeTab, loadMatrix, loadSummary]);

  // NEW: Load contracts when contracts tab is opened
  useEffect(() => {
    if (activeTab === 'contracts' || activeTab === 'comparison') {
      loadContracts();
    }
  }, [activeTab]);

  // NEW: Fetch contracts list
  const loadContracts = useCallback(async () => {
    if (contracts.length > 0) return;
    try {
      const response = await api.get('/contracts/list');
      setContracts(response.data.contracts || []);
    } catch (err) {
      console.error('Failed to fetch contracts:', err);
    }
  }, [contracts.length]);

  // NEW: Load real contract concept graph
  const loadContractGraph = useCallback(async (contractId) => {
    if (!contractId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getContractConceptGraph(contractId);
      setContractGraphData(data);
      const { nodes: n, edges: e } = buildFlowElements(data, '#4C8EDA');
      setContractNodes(n);
      setContractEdges(e);
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Failed to load contract graph');
    } finally {
      setLoading(false);
    }
  }, [setContractNodes, setContractEdges]);

  // NEW: Compare two contracts
  const handleCompare = useCallback(async () => {
    if (!contract1 || !contract2) {
      setError('Please select both contracts');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await compareContracts(contract1, contract2);
      setComparisonData(data);
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Failed to compare contracts');
    } finally {
      setLoading(false);
    }
  }, [contract1, contract2]);

  // NEW: Load centrality analytics
  const loadCentrality = useCallback(async (contractType) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getConceptCentrality(contractType);
      setCentralityData(data);
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Failed to load centrality');
    } finally {
      setLoading(false);
    }
  }, []);

  // NEW: Load community detection
  const loadCommunities = useCallback(async (contractType) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getConceptCommunities(contractType);
      setCommunitiesData(data);
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Failed to load communities');
    } finally {
      setLoading(false);
    }
  }, []);

  // NEW: Load contract-specific centrality
  const loadContractCentrality = useCallback(async (contractId) => {
    if (!contractId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/concept-graph/analytics/centrality/', {
        params: { contract_id: contractId }
      });
      setCentralityData(response.data);
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Failed to load contract centrality');
    } finally {
      setLoading(false);
    }
  }, []);

  // ------------------------------------------------------------------
  // Derived chart data
  // ------------------------------------------------------------------
  const radarData = summaryData?.concepts?.map(c => ({
    concept: c.concept.replace(' ', '\n'),
    MSA: c.by_archetype?.MSA || 0,
    SaaS: c.by_archetype?.SaaS || 0,
    NDA: c.by_archetype?.NDA || 0,
    Employment: c.by_archetype?.Employment || 0,
    EPC: c.by_archetype?.EPC || 0,
  })) || [];

  const barData = summaryData?.concepts?.map(c => ({
    name: c.concept,
    avg: c.average_strength,
    fill: c.color,
  })) || [];

  const activeContractMeta = CONTRACT_TYPES.find(ct => ct.id === selectedType);

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#e2e8f0', fontFamily: 'Inter, sans-serif' }}>

      {/* ── Header ──────────────────────────────────────── */}
      <div style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        borderBottom: '1px solid #1e40af44',
        padding: '24px 32px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 8 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 24, boxShadow: '0 0 20px #3b82f644',
          }}>🧠</div>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>
              Contract Concept Risk Topology Engine
            </h1>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: 13 }}>
              Pearson correlation between legal concepts · 5 contract archetypes · animated edges = strong coupling
            </p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 12 }}>
            {[
              { label: 'Concepts', value: '10' },
              { label: 'Archetypes', value: '5' },
              { label: 'Method', value: 'Pearson' },
            ].map(kpi => (
              <div key={kpi.label} style={{
                background: '#1e293b', border: '1px solid #334155',
                borderRadius: 8, padding: '8px 16px', textAlign: 'center',
              }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#60a5fa' }}>{kpi.value}</div>
                <div style={{ fontSize: 10, color: '#64748b' }}>{kpi.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Tab Bar ─────────────────────────────────────── */}
      <div style={{
        display: 'flex', background: '#111827',
        borderBottom: '1px solid #1e293b', padding: '0 32px',
      }}>
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            padding: '14px 20px', fontSize: 13, fontWeight: 600,
            color: activeTab === tab.id ? '#60a5fa' : '#64748b',
            borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
            transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span>{tab.icon}</span>{tab.label}
            {tab.badge && (
              <span style={{
                background: '#8b5cf6',
                color: '#fff',
                fontSize: 9,
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: 4,
                marginLeft: 4
              }}>
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      <div style={{ padding: '24px 32px' }}>

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — Correlation Graph                           */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'graph' && (
          <div>

            {/* ── Rich Archetype Selector Cards ─────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 10, marginBottom: 20 }}>
              {CONTRACT_TYPES.map(ct => {
                const isActive = selectedType === ct.id;
                return (
                  <button key={ct.id} onClick={() => setSelectedType(ct.id)} style={{
                    background: isActive
                      ? `linear-gradient(135deg, ${ct.color}33 0%, ${ct.color}18 100%)`
                      : 'linear-gradient(135deg, #1e293b 0%, #111827 100%)',
                    border: isActive ? `2px solid ${ct.color}` : '2px solid #1e293b',
                    borderRadius: 12, cursor: 'pointer', padding: '12px 10px',
                    textAlign: 'center', transition: 'all 0.2s',
                    boxShadow: isActive ? `0 0 20px ${ct.color}44, 0 4px 12px rgba(0,0,0,0.3)` : '0 2px 8px rgba(0,0,0,0.2)',
                    transform: isActive ? 'translateY(-2px)' : 'none',
                    position: 'relative', overflow: 'hidden',
                  }}>
                    {/* Active glow bar at top */}
                    {isActive && (
                      <div style={{
                        position: 'absolute', top: 0, left: 0, right: 0, height: 3,
                        background: `linear-gradient(90deg, transparent, ${ct.color}, transparent)`,
                        borderRadius: '12px 12px 0 0',
                      }} />
                    )}
                    <div style={{ fontSize: 22, marginBottom: 4 }}>{ct.icon}</div>
                    <div style={{
                      color: isActive ? ct.color : '#94a3b8',
                      fontWeight: 800, fontSize: 13, marginBottom: 2,
                    }}>
                      {ct.label}
                    </div>
                    <div style={{
                      color: isActive ? ct.color + 'cc' : '#475569',
                      fontSize: 9, lineHeight: 1.3, fontWeight: 500,
                    }}>
                      {ct.short}
                    </div>
                    {/* Density / tag badge */}
                    <div style={{
                      marginTop: 6,
                      display: 'inline-block',
                      background: isActive ? ct.color + '33' : '#0f172a',
                      border: `1px solid ${isActive ? ct.color + '66' : '#334155'}`,
                      borderRadius: 20, padding: '2px 8px',
                      fontSize: 9, fontWeight: 700,
                      color: isActive ? ct.color : '#475569',
                    }}>
                      {ct.tag}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* ── Rich Info Strip ───────────────────────────── */}
            {graphData && !loading && (
              <div style={{
                background: `linear-gradient(135deg, ${activeContractMeta?.color}18 0%, #0f172a 60%)`,
                border: `1px solid ${activeContractMeta?.color}44`,
                borderLeft: `4px solid ${activeContractMeta?.color}`,
                borderRadius: 12, padding: '14px 20px',
                marginBottom: 14,
                display: 'flex', gap: 0, alignItems: 'stretch', flexWrap: 'wrap',
              }}>
                {/* Left: title + description */}
                <div style={{ flex: 1, minWidth: 200, paddingRight: 24, borderRight: `1px solid ${activeContractMeta?.color}22` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 20 }}>{activeContractMeta?.icon}</span>
                    <span style={{ color: activeContractMeta?.color, fontWeight: 800, fontSize: 16 }}>
                      {graphData.contract_type === 'ALL' ? 'Global' : graphData.contract_type}
                    </span>
                    <span style={{
                      background: activeContractMeta?.color + '22',
                      border: `1px solid ${activeContractMeta?.color}55`,
                      borderRadius: 20, padding: '2px 10px',
                      fontSize: 10, fontWeight: 700, color: activeContractMeta?.color,
                    }}>
                      {activeContractMeta?.tag}
                    </span>
                  </div>
                  {graphData.description && (
                    <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.5 }}>{graphData.description}</div>
                  )}
                </div>

                {/* Right: KPI grid */}
                {graphData.stats && (
                  <div style={{ display: 'flex', gap: 0, flexWrap: 'wrap' }}>
                    {[
                      { label: 'Nodes',          value: graphData.stats.total_nodes,                 color: activeContractMeta?.color, icon: '⬤' },
                      { label: 'Edges',           value: graphData.stats.total_edges,                 color: '#94a3b8',                  icon: '—' },
                      { label: 'Avg Weight',      value: graphData.stats.avg_edge_weight?.toFixed(3), color: '#10b981',                  icon: '⚖' },
                      { label: 'Strong Links',    value: graphData.stats.strong_correlations,         color: '#f59e0b',                  icon: '⚡' },
                      { label: 'Density',
                        value: (graphData.edge_density || 'medium').replace('_', ' '),
                        color: DENSITY_COLORS[graphData.edge_density] || '#94a3b8',
                        icon: '📶', caps: true },
                    ].map(kpi => (
                      <div key={kpi.label} style={{
                        padding: '8px 18px', textAlign: 'center',
                        borderRight: '1px solid #1e293b', minWidth: 80,
                      }}>
                        <div style={{ fontSize: 11, marginBottom: 2 }}>{kpi.icon}</div>
                        <div style={{
                          fontSize: 18, fontWeight: 800, color: kpi.color,
                          textTransform: kpi.caps ? 'capitalize' : 'none',
                        }}>
                          {kpi.value}
                        </div>
                        <div style={{ fontSize: 10, color: '#475569', fontWeight: 600 }}>{kpi.label}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── Dominant Concepts Chips ───────────────────── */}
            {graphData?.dominant_concepts?.length > 0 && !loading && (
              <div style={{
                display: 'flex', gap: 8, marginBottom: 14,
                alignItems: 'center', flexWrap: 'wrap',
              }}>
                <span style={{
                  color: '#64748b', fontSize: 11, fontWeight: 700, letterSpacing: 0.5,
                  background: '#1e293b', borderRadius: 6, padding: '3px 10px',
                }}>
                  ★ DOMINANT
                </span>
                {graphData.dominant_concepts.map(dc => (
                  <span key={dc} style={{
                    background: activeContractMeta?.color + '18',
                    border: `1px solid ${activeContractMeta?.color}55`,
                    borderRadius: 20, padding: '3px 14px',
                    fontSize: 12, fontWeight: 700,
                    color: activeContractMeta?.color,
                    boxShadow: `0 0 8px ${activeContractMeta?.color}22`,
                  }}>
                    {dc}
                  </span>
                ))}
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div style={{
                height: 580, display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: '#111827', borderRadius: 12, border: '1px solid #1e293b',
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 52, marginBottom: 12 }}>{activeContractMeta?.icon || '🧠'}</div>
                  <div style={{ color: activeContractMeta?.color || '#60a5fa', fontSize: 14, fontWeight: 600 }}>
                    Computing {selectedType === 'ALL' ? 'Global' : selectedType} correlation graph…
                  </div>
                  <div style={{ color: '#475569', fontSize: 12, marginTop: 6 }}>
                    Applying Pearson correlation across 10 legal concepts
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && !loading && (
              <div style={{
                background: '#450a0a', border: '1px solid #dc2626', borderRadius: 10,
                padding: 16, color: '#fca5a5', marginBottom: 16,
              }}>{error}</div>
            )}

            {/* ── Graph Canvas + Panels ─────────────────────── */}
            {!loading && !error && nodes.length > 0 && (
              <div style={{ display: 'flex', gap: 14 }}>

                {/* React Flow canvas */}
                <div style={{
                  flex: 1, height: 680,
                  background: `radial-gradient(ellipse at 50% 50%, ${activeContractMeta?.color}0a 0%, #080f1a 72%)`,
                  borderRadius: 14,
                  border: `1px solid ${activeContractMeta?.color}44`,
                  overflow: 'hidden',
                  boxShadow: `0 0 50px ${activeContractMeta?.color}14, inset 0 0 60px rgba(0,0,0,0.4)`,
                  position: 'relative',
                }}>
                  {/* Archetype watermark */}
                  <div style={{
                    position: 'absolute', top: 14, left: 18, zIndex: 5,
                    display: 'flex', alignItems: 'center', gap: 8,
                    background: 'rgba(0,0,0,0.45)', borderRadius: 8, padding: '5px 12px',
                    backdropFilter: 'blur(8px)',
                    border: `1px solid ${activeContractMeta?.color}33`,
                  }}>
                    <span style={{ fontSize: 16 }}>{activeContractMeta?.icon}</span>
                    <span style={{ color: activeContractMeta?.color, fontWeight: 700, fontSize: 12 }}>
                      {selectedType === 'ALL' ? 'Global' : selectedType}
                    </span>
                    <span style={{ color: '#475569', fontSize: 11 }}>Correlation Graph</span>
                  </div>

                  <ReactFlow
                    key={selectedType}
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    onNodeClick={(_, node) => setSelectedNode(node)}
                    fitView
                    fitViewOptions={{ padding: 0.15, includeHiddenNodes: false }}
                    minZoom={0.12}
                    maxZoom={2.5}
                    proOptions={{ hideAttribution: true }}
                  >
                    <Background
                      color={activeContractMeta?.color + '18'}
                      gap={32} size={1.2}
                      variant="dots"
                    />
                    <Controls style={{
                      background: '#1e293b99', border: `1px solid ${activeContractMeta?.color}33`,
                      borderRadius: 8, backdropFilter: 'blur(8px)',
                    }} />
                    <MiniMap
                      nodeColor={n => n.data?.color || '#4C8EDA'}
                      maskColor="#0f172a99"
                      style={{
                        background: '#0a0f1a',
                        border: `1px solid ${activeContractMeta?.color}44`,
                        borderRadius: 8,
                      }}
                    />
                  </ReactFlow>
                </div>

                {/* ── Right Panel: Node Detail + Edge Legend ── */}
                <div style={{
                  width: 240, flexShrink: 0,
                  display: 'flex', flexDirection: 'column', gap: 12,
                }}>

                  {/* Node detail card */}
                  <div style={{
                    background: 'linear-gradient(145deg, #1e293b, #111827)',
                    borderRadius: 12, border: '1px solid #334155',
                    padding: 16, flex: selectedNode ? 'none' : 1,
                  }}>
                    <div style={{
                      fontWeight: 700, color: '#64748b', fontSize: 10,
                      letterSpacing: 1.5, marginBottom: 14, display: 'flex',
                      alignItems: 'center', gap: 6,
                    }}>
                      <span style={{
                        width: 6, height: 6, borderRadius: '50%',
                        background: selectedNode ? selectedNode.data?.color : '#334155',
                        display: 'inline-block',
                      }} />
                      NODE DETAIL
                    </div>

                    {selectedNode ? (
                      <>
                        {/* Large circle preview */}
                        <div style={{
                          width: 80, height: 80, borderRadius: '50%',
                          background: `radial-gradient(circle at 30% 30%, ${selectedNode.data?.color}ff, ${selectedNode.data?.color}55)`,
                          border: `3px solid ${selectedNode.data?.color}`,
                          boxShadow: `0 0 28px ${selectedNode.data?.color}66, 0 0 12px ${selectedNode.data?.color}33`,
                          margin: '0 auto 12px',
                          display: 'flex', flexDirection: 'column',
                          alignItems: 'center', justifyContent: 'center',
                          color: '#fff', fontWeight: 700, fontSize: 9,
                          textAlign: 'center', padding: 6,
                          lineHeight: 1.2,
                        }}>
                          {selectedNode.data?.label}
                        </div>

                        <div style={{ fontSize: 14, fontWeight: 800, color: '#f1f5f9', textAlign: 'center', marginBottom: 4 }}>
                          {selectedNode.data?.label}
                        </div>
                        <div style={{
                          textAlign: 'center', marginBottom: 14,
                          fontSize: 10, color: selectedNode.data?.color,
                          background: selectedNode.data?.color + '18',
                          borderRadius: 20, padding: '2px 12px',
                          display: 'inline-block', width: '100%',
                        }}>
                          strength {selectedNode.data?.strength?.toFixed(3)}
                        </div>

                        {/* Stats rows */}
                        {[
                          { label: 'Contract Type', value: selectedNode.data?.contract_type, color: activeContractMeta?.color },
                          { label: 'Node Size',     value: `${selectedNode.data?.size}px`,   color: '#94a3b8' },
                        ].map(item => (
                          <div key={item.label} style={{
                            background: '#0f172a', borderRadius: 6, padding: '7px 10px',
                            marginBottom: 6,
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          }}>
                            <span style={{ color: '#64748b', fontSize: 11 }}>{item.label}</span>
                            <span style={{ color: item.color, fontWeight: 700, fontSize: 11 }}>{item.value}</span>
                          </div>
                        ))}

                        {/* Importance bar */}
                        <div style={{ marginTop: 8, marginBottom: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ color: '#64748b', fontSize: 10 }}>Importance</span>
                            <span style={{
                              fontSize: 10, fontWeight: 700,
                              color: (selectedNode.data?.strength || 0) >= 0.70 ? '#4ade80'
                                   : (selectedNode.data?.strength || 0) >= 0.45 ? '#fbbf24'
                                   : '#f87171',
                            }}>
                              {(selectedNode.data?.strength || 0) >= 0.70 ? 'High'
                               : (selectedNode.data?.strength || 0) >= 0.45 ? 'Medium' : 'Low'}
                            </span>
                          </div>
                          <div style={{ background: '#0f172a', borderRadius: 4, height: 8, overflow: 'hidden' }}>
                            <div style={{
                              width: `${(selectedNode.data?.strength || 0) * 100}%`, height: '100%',
                              background: `linear-gradient(90deg, ${selectedNode.data?.color}88, ${selectedNode.data?.color})`,
                              borderRadius: 4, transition: 'width 0.4s',
                            }} />
                          </div>
                        </div>

                        {/* Role description */}
                        {CONCEPT_ROLES[selectedNode.data?.label] && (
                          <div style={{
                            background: '#0f172a', borderRadius: 8, padding: '10px 12px',
                            border: `1px solid ${selectedNode.data?.color}22`,
                          }}>
                            <div style={{ color: '#64748b', fontSize: 9, fontWeight: 700, letterSpacing: 1, marginBottom: 5 }}>
                              ROLE
                            </div>
                            <div style={{ color: '#94a3b8', fontSize: 11, lineHeight: 1.55 }}>
                              {CONCEPT_ROLES[selectedNode.data?.label]}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '20px 0' }}>
                        <div style={{ fontSize: 36, marginBottom: 10, opacity: 0.4 }}>⬤</div>
                        <div style={{ color: '#475569', fontSize: 12, lineHeight: 1.7 }}>
                          Click any concept node<br />to inspect details
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Edge Legend card */}
                  <div style={{
                    background: 'linear-gradient(145deg, #1e293b, #111827)',
                    borderRadius: 12, border: '1px solid #334155', padding: '14px 16px',
                  }}>
                    <div style={{ fontWeight: 700, color: '#64748b', fontSize: 10, letterSpacing: 1.5, marginBottom: 12 }}>
                      EDGE LEGEND
                    </div>
                    {[
                      { label: '> 0.80  animated glow', color: activeContractMeta?.color || '#60a5fa', thick: 4, animated: true },
                      { label: '0.65 – 0.80  medium',   color: '#4b6584',                              thick: 2.5 },
                      { label: '< 0.65  weak link',     color: '#2d3748',                              thick: 1.5 },
                    ].map(l => (
                      <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <div style={{
                          width: 32, height: Math.round(l.thick) + 1,
                          background: l.animated
                            ? `linear-gradient(90deg, transparent, ${l.color}, transparent)`
                            : l.color,
                          borderRadius: 2, flexShrink: 0,
                          boxShadow: l.animated ? `0 0 6px ${l.color}` : 'none',
                        }} />
                        <span style={{ color: '#64748b', fontSize: 10 }}>{l.label}</span>
                      </div>
                    ))}

                    {/* Archetype color note */}
                    <div style={{
                      marginTop: 10, padding: '8px 10px',
                      background: '#0f172a', borderRadius: 6,
                      border: `1px solid ${activeContractMeta?.color}22`,
                    }}>
                      <div style={{ color: '#475569', fontSize: 10, lineHeight: 1.5 }}>
                        Strong edges glow in{' '}
                        <span style={{ color: activeContractMeta?.color, fontWeight: 700 }}>
                          {activeContractMeta?.label}
                        </span>{' '}
                        archetype color
                      </div>
                    </div>
                  </div>

                  {/* Quick-switch mini buttons */}
                  <div style={{
                    background: 'linear-gradient(145deg, #1e293b, #111827)',
                    borderRadius: 12, border: '1px solid #334155', padding: '12px 14px',
                  }}>
                    <div style={{ fontWeight: 700, color: '#64748b', fontSize: 10, letterSpacing: 1.5, marginBottom: 10 }}>
                      QUICK SWITCH
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {CONTRACT_TYPES.map(ct => (
                        <button key={ct.id} onClick={() => setSelectedType(ct.id)} style={{
                          background: selectedType === ct.id ? ct.color + '33' : '#0f172a',
                          border: `1px solid ${selectedType === ct.id ? ct.color : '#334155'}`,
                          borderRadius: 6, padding: '4px 10px', cursor: 'pointer',
                          color: selectedType === ct.id ? ct.color : '#64748b',
                          fontSize: 10, fontWeight: 700,
                          transition: 'all 0.15s',
                        }}>
                          {ct.icon} {ct.label}
                        </button>
                      ))}
                    </div>
                  </div>

                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — Correlation Matrix                          */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'matrix' && (
          <div>
            {/* Rich header */}
            <div style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
              border: '1px solid #1e40af44', borderRadius: 14,
              padding: '22px 28px', marginBottom: 20,
              display: 'flex', alignItems: 'flex-start', gap: 32, flexWrap: 'wrap',
            }}>
              <div style={{ flex: 1, minWidth: 260 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <span style={{ fontSize: 22 }}>📊</span>
                  <span style={{ fontSize: 18, fontWeight: 800, color: '#f1f5f9' }}>Pearson Correlation Matrix</span>
                </div>
                <div style={{ color: '#64748b', fontSize: 13, lineHeight: 1.7 }}>
                  Each cell = normalised Pearson correlation [0,1] between two legal concepts across 5 contract archetypes.<br />
                  <span style={{ color: '#f87171' }}>Red</span> = strongly co-occur · <span style={{ color: '#60a5fa' }}>Blue</span> = inversely related · <span style={{ color: '#94a3b8' }}>Gray</span> = neutral
                </div>
              </div>
              {/* KPI cards */}
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {matrixData && (() => {
                  const concepts = matrixData.concepts || [];
                  const allVals = [];
                  concepts.forEach(r => concepts.forEach(c => {
                    if (r !== c) allVals.push(matrixData.matrix?.[r]?.[c] ?? 0);
                  }));
                  const strongPairs = allVals.filter(v => v >= 0.85).length / 2;
                  const avg = allVals.reduce((a, b) => a + b, 0) / allVals.length;
                  const max = Math.max(...allVals);
                  return [
                    { label: 'Concepts', value: concepts.length, color: '#60a5fa', icon: '🔵' },
                    { label: 'Pairs', value: concepts.length * (concepts.length - 1) / 2, color: '#94a3b8', icon: '🔗' },
                    { label: 'Strong pairs (≥0.85)', value: strongPairs, color: '#f87171', icon: '🔴' },
                    { label: 'Avg correlation', value: avg.toFixed(3), color: '#10b981', icon: '📈' },
                    { label: 'Max correlation', value: max.toFixed(3), color: '#f59e0b', icon: '⚡' },
                  ].map(kpi => (
                    <div key={kpi.label} style={{
                      background: '#0f172a', border: '1px solid #1e293b',
                      borderRadius: 10, padding: '10px 16px', textAlign: 'center', minWidth: 90,
                    }}>
                      <div style={{ fontSize: 16, marginBottom: 2 }}>{kpi.icon}</div>
                      <div style={{ fontSize: 17, fontWeight: 800, color: kpi.color }}>{kpi.value}</div>
                      <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>{kpi.label}</div>
                    </div>
                  ));
                })()}
              </div>
            </div>

            {!matrixData ? (
              <div style={{ color: '#60a5fa' }}>Loading matrix…</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {/* Heatmap */}
                <div style={{ background: '#111827', borderRadius: 14, padding: '28px 24px', border: '1px solid #1e293b' }}>
                  <CorrelationHeatmap matrix={matrixData.matrix} concepts={matrixData.concepts} />
                </div>

                {/* Insight cards below heatmap */}
                {(() => {
                  const concepts = matrixData.concepts || [];
                  const pairs = [];
                  concepts.forEach(r => concepts.forEach(c => {
                    if (r < c) pairs.push({ r, c, val: matrixData.matrix?.[r]?.[c] ?? 0 });
                  }));
                  const top5 = [...pairs].sort((a, b) => b.val - a.val).slice(0, 5);
                  const bot5 = [...pairs].sort((a, b) => a.val - b.val).slice(0, 5);
                  return (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                      {/* Strongest pairs */}
                      <div style={{
                        background: 'linear-gradient(145deg, #111827, #0d1829)',
                        border: '1px solid #dc262622', borderLeft: '4px solid #ef4444',
                        borderRadius: 14, padding: '20px 22px',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                          <span style={{ fontSize: 18 }}>🔴</span>
                          <div>
                            <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14 }}>Strongest Correlations</div>
                            <div style={{ color: '#64748b', fontSize: 11 }}>Concept pairs that always co-appear</div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {top5.map((p, i) => (
                            <div key={i}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                  <span style={{
                                    width: 18, height: 18, borderRadius: '50%',
                                    background: i === 0 ? '#f59e0b' : i === 1 ? '#94a3b8' : i === 2 ? '#b45309' : '#1e293b',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: 9, fontWeight: 800, color: '#0f172a', flexShrink: 0,
                                  }}>{i + 1}</span>
                                  <span style={{
                                    color: CONCEPT_COLORS_MAP[p.r] || '#94a3b8',
                                    fontWeight: 700, fontSize: 12,
                                  }}>{p.r}</span>
                                  <span style={{ color: '#475569', fontSize: 11 }}>↔</span>
                                  <span style={{
                                    color: CONCEPT_COLORS_MAP[p.c] || '#94a3b8',
                                    fontWeight: 700, fontSize: 12,
                                  }}>{p.c}</span>
                                </div>
                                <span style={{ color: '#f87171', fontWeight: 800, fontSize: 14 }}>{p.val.toFixed(3)}</span>
                              </div>
                              <div style={{ background: '#0f172a', borderRadius: 3, height: 6, overflow: 'hidden' }}>
                                <div style={{
                                  width: `${p.val * 100}%`, height: '100%',
                                  background: `linear-gradient(90deg, #dc262688, #ef4444)`,
                                  borderRadius: 3,
                                }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Weakest pairs */}
                      <div style={{
                        background: 'linear-gradient(145deg, #111827, #0d1829)',
                        border: '1px solid #1d4ed822', borderLeft: '4px solid #3b82f6',
                        borderRadius: 14, padding: '20px 22px',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                          <span style={{ fontSize: 18 }}>🔵</span>
                          <div>
                            <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14 }}>Weakest Correlations</div>
                            <div style={{ color: '#64748b', fontSize: 11 }}>Concept pairs that rarely co-appear</div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {bot5.map((p, i) => (
                            <div key={i}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                  <span style={{
                                    width: 18, height: 18, borderRadius: '50%',
                                    background: '#1e293b', border: '1px solid #334155',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: 9, fontWeight: 800, color: '#64748b', flexShrink: 0,
                                  }}>{i + 1}</span>
                                  <span style={{
                                    color: CONCEPT_COLORS_MAP[p.r] || '#94a3b8',
                                    fontWeight: 700, fontSize: 12,
                                  }}>{p.r}</span>
                                  <span style={{ color: '#475569', fontSize: 11 }}>↔</span>
                                  <span style={{
                                    color: CONCEPT_COLORS_MAP[p.c] || '#94a3b8',
                                    fontWeight: 700, fontSize: 12,
                                  }}>{p.c}</span>
                                </div>
                                <span style={{ color: '#60a5fa', fontWeight: 800, fontSize: 14 }}>{p.val.toFixed(3)}</span>
                              </div>
                              <div style={{ background: '#0f172a', borderRadius: 3, height: 6, overflow: 'hidden' }}>
                                <div style={{
                                  width: `${p.val * 100}%`, height: '100%',
                                  background: `linear-gradient(90deg, #1d4ed888, #3b82f6)`,
                                  borderRadius: 3,
                                }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Per-concept row avg */}
                      <div style={{
                        background: 'linear-gradient(145deg, #111827, #0d1829)',
                        border: '1px solid #059669 22', borderLeft: '4px solid #10b981',
                        borderRadius: 14, padding: '20px 22px', gridColumn: '1 / -1',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                          <span style={{ fontSize: 18 }}>📐</span>
                          <div>
                            <div style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14 }}>Concept Centrality (Row Average)</div>
                            <div style={{ color: '#64748b', fontSize: 11 }}>How correlated each concept is with ALL others — higher = more structurally central</div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {(() => {
                            const concepts = matrixData.concepts || [];
                            const rowAvgs = concepts.map(r => {
                              const vals = concepts.filter(c => c !== r).map(c => matrixData.matrix?.[r]?.[c] ?? 0);
                              const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
                              return { concept: r, avg };
                            }).sort((a, b) => b.avg - a.avg);
                            const maxAvg = rowAvgs[0]?.avg || 1;
                            return rowAvgs.map((item, i) => (
                              <div key={item.concept} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                <div style={{ width: 22, textAlign: 'right', color: '#475569', fontSize: 11, flexShrink: 0 }}>#{i + 1}</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: 140, flexShrink: 0 }}>
                                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: CONCEPT_COLORS_MAP[item.concept] || '#94a3b8', flexShrink: 0 }} />
                                  <span style={{ color: CONCEPT_COLORS_MAP[item.concept] || '#94a3b8', fontWeight: 700, fontSize: 12 }}>{item.concept}</span>
                                </div>
                                <div style={{ flex: 1, background: '#0f172a', borderRadius: 4, height: 18, overflow: 'hidden', position: 'relative' }}>
                                  <div style={{
                                    width: `${(item.avg / maxAvg) * 100}%`, height: '100%',
                                    background: `linear-gradient(90deg, ${CONCEPT_COLORS_MAP[item.concept] || '#94a3b8'}66, ${CONCEPT_COLORS_MAP[item.concept] || '#94a3b8'})`,
                                    borderRadius: 4, display: 'flex', alignItems: 'center', paddingLeft: 8,
                                  }}>
                                    {item.avg > 0.3 && (
                                      <span style={{ color: '#fff', fontSize: 10, fontWeight: 700 }}>{item.avg.toFixed(3)}</span>
                                    )}
                                  </div>
                                  {item.avg <= 0.3 && (
                                    <span style={{ position: 'absolute', left: `${(item.avg / maxAvg) * 100 + 1}%`, top: '50%', transform: 'translateY(-50%)', color: '#64748b', fontSize: 10, fontWeight: 700 }}>
                                      {item.avg.toFixed(3)}
                                    </span>
                                  )}
                                </div>
                                <div style={{
                                  width: 70, textAlign: 'right', flexShrink: 0, fontSize: 11, fontWeight: 600,
                                  color: item.avg >= 0.80 ? '#f87171' : item.avg >= 0.65 ? '#fb923c' : item.avg >= 0.50 ? '#fbbf24' : '#60a5fa',
                                }}>
                                  {item.avg >= 0.80 ? 'Core' : item.avg >= 0.65 ? 'High' : item.avg >= 0.50 ? 'Medium' : 'Isolated'}
                                </div>
                              </div>
                            ));
                          })()}
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — Concept Radar                               */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'radar' && (
          <div>
            {/* Rich header with KPI strip */}
            <div style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
              border: '1px solid #1e40af44',
              borderRadius: 14, padding: '20px 28px', marginBottom: 24,
              display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
            }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', marginBottom: 4 }}>
                  Concept Strength Radar
                </div>
                <div style={{ color: '#64748b', fontSize: 13 }}>
                  How prominently each legal concept appears across all 5 contract archetypes
                </div>
              </div>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {CONTRACT_TYPES.filter(ct => ct.id !== 'ALL').map(ct => {
                  const topConcept = summaryData
                    ? [...(summaryData.concepts || [])].sort(
                        (a, b) => (b.by_archetype?.[ct.id] || 0) - (a.by_archetype?.[ct.id] || 0)
                      )[0]
                    : null;
                  return (
                    <div key={ct.id} style={{
                      background: ct.color + '18',
                      border: `1px solid ${ct.color}55`,
                      borderRadius: 10, padding: '8px 14px', textAlign: 'center',
                    }}>
                      <div style={{ fontSize: 11, color: ct.color, fontWeight: 700, marginBottom: 2 }}>
                        {ct.icon} {ct.label}
                      </div>
                      {topConcept && (
                        <div style={{ fontSize: 10, color: '#64748b' }}>
                          Top: <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{topConcept.concept.split(' ')[0]}</span>
                          {' '}<span style={{ color: ct.color, fontWeight: 700 }}>
                            {(topConcept.by_archetype?.[ct.id] || 0).toFixed(2)}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {!summaryData ? (
              <div style={{ color: '#60a5fa' }}>Loading concept data…</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

                {/* Row 1 — radar + bar side by side */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

                  {/* Radar */}
                  <div style={{
                    background: 'linear-gradient(145deg, #111827 0%, #0d1829 100%)',
                    borderRadius: 14, padding: '24px 20px',
                    border: '1px solid #1e293b',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                      <span style={{ fontSize: 16 }}>📡</span>
                      <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 700 }}>Multi-Archetype Radar</span>
                    </div>
                    <div style={{ color: '#475569', fontSize: 12, marginBottom: 16 }}>
                      Each polygon = one contract archetype. Larger area = broader concept coverage.
                    </div>
                    <ResponsiveContainer width="100%" height={380}>
                      <RadarChart data={radarData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
                        <PolarGrid stroke="#1e3a5f" strokeDasharray="3 3" />
                        <PolarAngleAxis
                          dataKey="concept"
                          tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 600 }}
                        />
                        <PolarRadiusAxis
                          domain={[0, 1]}
                          tickCount={5}
                          tick={{ fill: '#374151', fontSize: 9 }}
                          axisLine={false}
                        />
                        {CONTRACT_TYPES.filter(ct => ct.id !== 'ALL').map(ct => (
                          <Radar
                            key={ct.id}
                            name={ct.label}
                            dataKey={ct.id}
                            stroke={ct.color}
                            strokeWidth={2}
                            fill={ct.color}
                            fillOpacity={0.15}
                            dot={{ fill: ct.color, r: 3 }}
                          />
                        ))}
                        <Legend
                          wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
                          formatter={(value, entry) => (
                            <span style={{ color: entry.color, fontWeight: 700 }}>{value}</span>
                          )}
                        />
                        <Tooltip
                          contentStyle={{
                            background: '#1e293b', border: '1px solid #334155',
                            borderRadius: 10, color: '#e5e7eb', fontSize: 12,
                          }}
                          formatter={(value, name) => [
                            <span style={{ fontWeight: 700 }}>{Number(value).toFixed(2)}</span>,
                            name,
                          ]}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Bar chart */}
                  <div style={{
                    background: 'linear-gradient(145deg, #111827 0%, #0d1829 100%)',
                    borderRadius: 14, padding: '24px 20px', border: '1px solid #1e293b',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                      <span style={{ fontSize: 16 }}>📊</span>
                      <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 700 }}>Average Concept Strength</span>
                    </div>
                    <div style={{ color: '#475569', fontSize: 12, marginBottom: 16 }}>
                      Average score across all 5 archetypes. Higher = universally important concept.
                    </div>
                    <ResponsiveContainer width="100%" height={380}>
                      <BarChart data={barData} layout="vertical" margin={{ left: 0, right: 20, top: 4, bottom: 4 }}>
                        <defs>
                          {barData.map((entry, i) => (
                            <linearGradient key={i} id={`barGrad${i}`} x1="0" y1="0" x2="1" y2="0">
                              <stop offset="0%" stopColor={entry.fill} stopOpacity={0.6} />
                              <stop offset="100%" stopColor={entry.fill} stopOpacity={1} />
                            </linearGradient>
                          ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                        <XAxis
                          type="number" domain={[0, 1]}
                          tick={{ fill: '#64748b', fontSize: 10 }}
                          tickLine={false} axisLine={{ stroke: '#1e293b' }}
                          tickFormatter={v => v.toFixed(1)}
                        />
                        <YAxis
                          type="category" dataKey="name"
                          tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
                          width={110} tickLine={false} axisLine={false}
                        />
                        <Tooltip
                          contentStyle={{
                            background: '#1e293b', border: '1px solid #334155',
                            borderRadius: 10, color: '#e5e7eb', fontSize: 12,
                          }}
                          formatter={(value) => [
                            <span style={{ fontWeight: 700 }}>{Number(value).toFixed(3)}</span>,
                            'Avg Strength',
                          ]}
                          cursor={{ fill: '#ffffff08' }}
                        />
                        <Bar dataKey="avg" radius={[0, 6, 6, 0]} barSize={22}>
                          {barData.map((entry, i) => (
                            <Cell key={i} fill={`url(#barGrad${i})`} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Row 2 — per-archetype spotlight cards */}
                <div>
                  <div style={{ color: '#64748b', fontSize: 12, fontWeight: 600, marginBottom: 12, letterSpacing: 1 }}>
                    ARCHETYPE SPOTLIGHT — Top 3 Concepts Per Contract Type
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
                    {CONTRACT_TYPES.filter(ct => ct.id !== 'ALL').map(ct => {
                      const top3 = summaryData
                        ? [...summaryData.concepts]
                            .sort((a, b) => (b.by_archetype?.[ct.id] || 0) - (a.by_archetype?.[ct.id] || 0))
                            .slice(0, 3)
                        : [];
                      return (
                        <div key={ct.id} style={{
                          background: '#111827',
                          border: `1px solid ${ct.color}44`,
                          borderTop: `3px solid ${ct.color}`,
                          borderRadius: 12, padding: '16px 14px',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                            <span style={{ fontSize: 18 }}>{ct.icon}</span>
                            <span style={{ color: ct.color, fontWeight: 800, fontSize: 14 }}>{ct.label}</span>
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {top3.map((concept, rank) => {
                              const val = concept.by_archetype?.[ct.id] || 0;
                              return (
                                <div key={concept.concept}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                                      <span style={{
                                        width: 16, height: 16, borderRadius: '50%',
                                        background: rank === 0 ? '#f59e0b' : rank === 1 ? '#94a3b8' : '#b45309',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: 9, fontWeight: 800, color: '#0f172a', flexShrink: 0,
                                      }}>
                                        {rank + 1}
                                      </span>
                                      <span style={{ color: '#cbd5e1', fontSize: 11, fontWeight: 600 }}>
                                        {concept.concept}
                                      </span>
                                    </div>
                                    <span style={{ color: ct.color, fontWeight: 800, fontSize: 12 }}>
                                      {val.toFixed(2)}
                                    </span>
                                  </div>
                                  <div style={{ background: '#0f172a', borderRadius: 3, height: 5, overflow: 'hidden' }}>
                                    <div style={{
                                      width: `${val * 100}%`, height: '100%',
                                      background: `linear-gradient(90deg, ${ct.color}88, ${ct.color})`,
                                      borderRadius: 3,
                                    }} />
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — Concept Summary Table                       */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'summary' && (
          <div>
            <SectionHeader
              title="Concept Strength Summary"
              sub="Per-concept strength across all 5 contract archetypes. Bar width = strength (0–1). Green ≥ 0.70 · Amber 0.40–0.70 · Gray < 0.40."
            />
            {!summaryData ? (
              <div style={{ color: '#60a5fa' }}>Loading summary…</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {/* Archetype color key */}
                <div style={{
                  display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center',
                  background: '#1e293b', borderRadius: 10, padding: '10px 18px',
                  border: '1px solid #334155', marginBottom: 4,
                }}>
                  <span style={{ color: '#64748b', fontSize: 12, fontWeight: 600 }}>Archetype key:</span>
                  {CONTRACT_TYPES.filter(ct => ct.id !== 'ALL').map(ct => (
                    <div key={ct.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ width: 12, height: 12, borderRadius: 3, background: ct.color }} />
                      <span style={{ color: ct.color, fontSize: 12, fontWeight: 700 }}>{ct.label}</span>
                    </div>
                  ))}
                </div>

                {/* One card per concept */}
                {summaryData.concepts.map((c, i) => {
                  const archetypes = ['MSA', 'SaaS', 'NDA', 'Employment', 'EPC'];
                  const vals = archetypes.map(ct => ({ ct, val: c.by_archetype?.[ct] || 0 }));
                  const strongest = [...vals].sort((a, b) => b.val - a.val)[0];
                  const weakest  = [...vals].sort((a, b) => a.val - b.val)[0];

                  return (
                    <div key={c.concept} style={{
                      background: '#111827',
                      border: `1px solid ${c.color}33`,
                      borderLeft: `4px solid ${c.color}`,
                      borderRadius: 12,
                      padding: '16px 20px',
                    }}>
                      {/* Top row — concept name + avg badge + strongest/weakest */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
                        {/* Rank */}
                        <div style={{
                          width: 28, height: 28, borderRadius: '50%',
                          background: c.color + '33', border: `2px solid ${c.color}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: c.color, fontWeight: 800, fontSize: 12, flexShrink: 0,
                        }}>
                          {i + 1}
                        </div>

                        {/* Name + dot */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 14, height: 14, borderRadius: '50%', background: c.color, boxShadow: `0 0 8px ${c.color}88` }} />
                          <span style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 15 }}>{c.concept}</span>
                        </div>

                        {/* Avg badge */}
                        <div style={{
                          background: c.color + '22', border: `1px solid ${c.color}66`,
                          borderRadius: 20, padding: '3px 12px',
                          color: c.color, fontWeight: 800, fontSize: 13,
                        }}>
                          avg {c.average_strength.toFixed(3)}
                        </div>

                        <div style={{ marginLeft: 'auto', display: 'flex', gap: 10 }}>
                          {/* Strongest archetype */}
                          <div style={{
                            background: '#14532d33', border: '1px solid #16a34a66',
                            borderRadius: 8, padding: '3px 10px', fontSize: 11,
                            display: 'flex', alignItems: 'center', gap: 5,
                          }}>
                            <span style={{ color: '#4ade80' }}>▲ Strongest</span>
                            <span style={{
                              color: CONTRACT_TYPES.find(ct => ct.id === strongest.ct)?.color,
                              fontWeight: 700,
                            }}>{strongest.ct}</span>
                            <span style={{ color: '#4ade80', fontWeight: 700 }}>{strongest.val.toFixed(2)}</span>
                          </div>
                          {/* Weakest archetype */}
                          <div style={{
                            background: '#450a0a33', border: '1px solid #dc262666',
                            borderRadius: 8, padding: '3px 10px', fontSize: 11,
                            display: 'flex', alignItems: 'center', gap: 5,
                          }}>
                            <span style={{ color: '#f87171' }}>▼ Weakest</span>
                            <span style={{
                              color: CONTRACT_TYPES.find(ct => ct.id === weakest.ct)?.color,
                              fontWeight: 700,
                            }}>{weakest.ct}</span>
                            <span style={{ color: '#f87171', fontWeight: 700 }}>{weakest.val.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Per-archetype bars */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                        {vals.map(({ ct, val }) => {
                          const ctMeta = CONTRACT_TYPES.find(x => x.id === ct);
                          const barColor = val >= 0.70 ? '#10b981' : val >= 0.40 ? '#f59e0b' : '#475569';
                          return (
                            <div key={ct} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              {/* Archetype label */}
                              <div style={{
                                width: 80, flexShrink: 0,
                                display: 'flex', alignItems: 'center', gap: 5,
                              }}>
                                <div style={{ width: 8, height: 8, borderRadius: '50%', background: ctMeta?.color, flexShrink: 0 }} />
                                <span style={{ color: ctMeta?.color, fontWeight: 700, fontSize: 12 }}>{ct}</span>
                              </div>

                              {/* Bar track */}
                              <div style={{
                                flex: 1, height: 20, background: '#0f172a',
                                borderRadius: 4, overflow: 'hidden', position: 'relative',
                              }}>
                                <div style={{
                                  width: `${val * 100}%`,
                                  height: '100%',
                                  background: `linear-gradient(90deg, ${barColor}99, ${barColor})`,
                                  borderRadius: 4,
                                  transition: 'width 0.5s ease',
                                  display: 'flex', alignItems: 'center',
                                  paddingLeft: 8,
                                  minWidth: val > 0.05 ? 30 : 0,
                                }}>
                                  {val >= 0.15 && (
                                    <span style={{ color: '#fff', fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap' }}>
                                      {val.toFixed(2)}
                                    </span>
                                  )}
                                </div>
                                {val < 0.15 && (
                                  <span style={{
                                    position: 'absolute', left: `${val * 100 + 1}%`,
                                    top: '50%', transform: 'translateY(-50%)',
                                    color: '#64748b', fontSize: 11, fontWeight: 600,
                                  }}>
                                    {val.toFixed(2)}
                                  </span>
                                )}
                              </div>

                              {/* Strength label */}
                              <div style={{
                                width: 80, flexShrink: 0, textAlign: 'right',
                                fontSize: 11,
                                color: val >= 0.70 ? '#4ade80' : val >= 0.40 ? '#fbbf24' : '#64748b',
                                fontWeight: 600,
                              }}>
                                {val >= 0.70 ? 'High' : val >= 0.40 ? 'Medium' : 'Low'}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — Real Contracts (NEW)                        */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'contracts' && (
          <div>
            <SectionHeader
              title="Real Contract Concept Analysis"
              sub="Extract and visualize concepts from your uploaded contracts"
            />

            {/* Contract Selector */}
            <div style={{
              background: 'rgba(30,41,59,0.6)',
              padding: 24,
              borderRadius: 12,
              border: '1px solid rgba(71,85,105,0.5)',
              marginBottom: 24
            }}>
              <label style={{ color: '#cbd5e1', fontSize: 14, fontWeight: 600, display: 'block', marginBottom: 12 }}>
                Select Contract
              </label>
              <div style={{ display: 'flex', gap: 12 }}>
                <select
                  value={selectedContractId || ''}
                  onChange={(e) => setSelectedContractId(e.target.value)}
                  style={{
                    flex: 1,
                    background: '#1e293b',
                    color: '#fff',
                    border: '1px solid #475569',
                    borderRadius: 8,
                    padding: '12px 16px',
                    fontSize: 14,
                    cursor: 'pointer'
                  }}
                >
                  <option value="">Choose a contract...</option>
                  {contracts.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.original_filename} ({c.contract_type || 'Unknown'})
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => loadContractGraph(selectedContractId)}
                  disabled={!selectedContractId || loading}
                  style={{
                    background: selectedContractId && !loading ? '#3b82f6' : '#475569',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    padding: '12px 24px',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: selectedContractId && !loading ? 'pointer' : 'not-allowed',
                    opacity: selectedContractId && !loading ? 1 : 0.6
                  }}
                >
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
            </div>

            {/* Contract Graph Display */}
            {contractGraphData && (
              <div>
                {/* Stats Cards */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 16,
                  marginBottom: 24
                }}>
                  <div style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: 12, padding: 16 }}>
                    <div style={{ color: '#93c5fd', fontSize: 12, marginBottom: 4 }}>Contract Type</div>
                    <div style={{ color: '#fff', fontSize: 20, fontWeight: 700 }}>
                      {contractGraphData.contract_type || 'Unknown'}
                    </div>
                  </div>
                  <div style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 12, padding: 16 }}>
                    <div style={{ color: '#86efac', fontSize: 12, marginBottom: 4 }}>Total Concepts</div>
                    <div style={{ color: '#fff', fontSize: 20, fontWeight: 700 }}>
                      {contractGraphData.stats?.total_nodes || 0}
                    </div>
                  </div>
                  <div style={{ background: 'rgba(168,85,247,0.1)', border: '1px solid rgba(168,85,247,0.3)', borderRadius: 12, padding: 16 }}>
                    <div style={{ color: '#c084fc', fontSize: 12, marginBottom: 4 }}>Correlations</div>
                    <div style={{ color: '#fff', fontSize: 20, fontWeight: 700 }}>
                      {contractGraphData.stats?.total_edges || 0}
                    </div>
                  </div>
                  <div style={{ background: 'rgba(249,115,22,0.1)', border: '1px solid rgba(249,115,22,0.3)', borderRadius: 12, padding: 16 }}>
                    <div style={{ color: '#fb923c', fontSize: 12, marginBottom: 4 }}>Strong Links</div>
                    <div style={{ color: '#fff', fontSize: 20, fontWeight: 700 }}>
                      {contractGraphData.stats?.strong_correlations || 0}
                    </div>
                  </div>
                </div>

                {/* Concept Graph */}
                <div style={{
                  background: 'rgba(15,23,42,0.8)',
                  borderRadius: 16,
                  border: '1px solid rgba(71,85,105,0.5)',
                  overflow: 'hidden',
                  height: 600
                }}>
                  <ReactFlow
                    nodes={contractNodes}
                    edges={contractEdges}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    onNodesChange={onContractNodesChange}
                    onEdgesChange={onContractEdgesChange}
                    fitView
                    minZoom={0.3}
                    maxZoom={1.8}
                    attributionPosition="bottom-left"
                  >
                    <Background color="#334155" gap={16} />
                    <Controls />
                    <MiniMap nodeColor="#60a5fa" maskColor="rgba(0,0,0,0.6)" style={{ background: '#1e293b' }} />
                  </ReactFlow>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — Compare Contracts (NEW)                     */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'comparison' && (
          <div>
            <SectionHeader
              title="Contract Comparison"
              sub="Compare concept profiles between two contracts side-by-side"
            />

            {/* Contract Selectors */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
              <div style={{ background: 'rgba(30,41,59,0.6)', padding: 20, borderRadius: 12, border: '1px solid rgba(71,85,105,0.5)' }}>
                <label style={{ color: '#cbd5e1', fontSize: 14, fontWeight: 600, display: 'block', marginBottom: 12 }}>
                  Contract 1
                </label>
                <select
                  value={contract1 || ''}
                  onChange={(e) => setContract1(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#1e293b',
                    color: '#fff',
                    border: '1px solid #475569',
                    borderRadius: 8,
                    padding: '12px 16px',
                    fontSize: 14
                  }}
                >
                  <option value="">Select first contract...</option>
                  {contracts.map(c => (
                    <option key={c.id} value={c.id}>{c.original_filename}</option>
                  ))}
                </select>
              </div>

              <div style={{ background: 'rgba(30,41,59,0.6)', padding: 20, borderRadius: 12, border: '1px solid rgba(71,85,105,0.5)' }}>
                <label style={{ color: '#cbd5e1', fontSize: 14, fontWeight: 600, display: 'block', marginBottom: 12 }}>
                  Contract 2
                </label>
                <select
                  value={contract2 || ''}
                  onChange={(e) => setContract2(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#1e293b',
                    color: '#fff',
                    border: '1px solid #475569',
                    borderRadius: 8,
                    padding: '12px 16px',
                    fontSize: 14
                  }}
                >
                  <option value="">Select second contract...</option>
                  {contracts.map(c => (
                    <option key={c.id} value={c.id}>{c.original_filename}</option>
                  ))}
                </select>
              </div>
            </div>

            <button
              onClick={handleCompare}
              disabled={!contract1 || !contract2 || loading}
              style={{
                background: contract1 && contract2 && !loading ? '#3b82f6' : '#475569',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                padding: '12px 32px',
                fontSize: 14,
                fontWeight: 600,
                cursor: contract1 && contract2 && !loading ? 'pointer' : 'not-allowed',
                opacity: contract1 && contract2 && !loading ? 1 : 0.6,
                marginBottom: 24
              }}
            >
              {loading ? 'Comparing...' : 'Compare Contracts'}
            </button>

            {/* Comparison Results */}
            {comparisonData && (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
                  <div style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: 12, padding: 20 }}>
                    <div style={{ color: '#86efac', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                      📈 Major Increases
                    </div>
                    <div style={{ color: '#fff', fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
                      {comparisonData.major_increases?.length || 0}
                    </div>
                    <div style={{ color: '#86efac', fontSize: 12 }}>
                      {comparisonData.major_increases?.join(', ') || 'None'}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 12, padding: 20 }}>
                    <div style={{ color: '#fca5a5', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
                      📉 Major Decreases
                    </div>
                    <div style={{ color: '#fff', fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
                      {comparisonData.major_decreases?.length || 0}
                    </div>
                    <div style={{ color: '#fca5a5', fontSize: 12 }}>
                      {comparisonData.major_decreases?.join(', ') || 'None'}
                    </div>
                  </div>
                </div>

                {/* Detailed Comparison Table */}
                <div style={{ background: 'rgba(30,41,59,0.6)', borderRadius: 12, border: '1px solid rgba(71,85,105,0.5)', padding: 24 }}>
                  <h3 style={{ color: '#f1f5f9', fontSize: 16, fontWeight: 700, marginBottom: 16 }}>Detailed Differences</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid rgba(71,85,105,0.5)' }}>
                        <th style={{ textAlign: 'left', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Concept</th>
                        <th style={{ textAlign: 'right', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Contract 1</th>
                        <th style={{ textAlign: 'right', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Contract 2</th>
                        <th style={{ textAlign: 'right', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Difference</th>
                        <th style={{ textAlign: 'right', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>% Change</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonData.concept_differences &&
                        Object.entries(comparisonData.concept_differences)
                          .sort((a, b) => Math.abs(b[1].difference) - Math.abs(a[1].difference))
                          .map(([concept, data]) => (
                            <tr key={concept} style={{ borderBottom: '1px solid rgba(71,85,105,0.3)' }}>
                              <td style={{ padding: '12px 16px', color: '#f1f5f9', fontWeight: 600 }}>{concept}</td>
                              <td style={{ padding: '12px 16px', textAlign: 'right', color: '#60a5fa', fontFamily: 'monospace' }}>
                                {data.contract_1_strength.toFixed(3)}
                              </td>
                              <td style={{ padding: '12px 16px', textAlign: 'right', color: '#a78bfa', fontFamily: 'monospace' }}>
                                {data.contract_2_strength.toFixed(3)}
                              </td>
                              <td style={{
                                padding: '12px 16px',
                                textAlign: 'right',
                                color: data.difference > 0 ? '#86efac' : data.difference < 0 ? '#fca5a5' : '#94a3b8',
                                fontFamily: 'monospace',
                                fontWeight: 600
                              }}>
                                {data.difference > 0 && '+'}{data.difference.toFixed(3)}
                              </td>
                              <td style={{
                                padding: '12px 16px',
                                textAlign: 'right',
                                color: data.percent_change > 0 ? '#86efac' : data.percent_change < 0 ? '#fca5a5' : '#94a3b8',
                                fontFamily: 'monospace',
                                fontWeight: 600
                              }}>
                                {data.percent_change > 0 && '+'}{data.percent_change.toFixed(1)}%
                              </td>
                            </tr>
                          ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — Graph Analytics (NEW)                       */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'analytics' && (
          <div>
            <SectionHeader
              title="Graph Analytics"
              sub="Centrality metrics and community detection for concept networks"
            />

            {/* Analysis Mode Selector */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <button
                  onClick={() => setAnalyticsMode('archetype')}
                  style={{
                    background: analyticsMode === 'archetype' ? '#3b82f6' : 'transparent',
                    color: '#fff',
                    border: analyticsMode === 'archetype' ? 'none' : '1px solid #475569',
                    borderRadius: 8,
                    padding: '10px 20px',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                    marginRight: 12
                  }}
                >
                  📊 Archetype Analysis
                </button>
                <button
                  onClick={() => setAnalyticsMode('contract')}
                  style={{
                    background: analyticsMode === 'contract' ? '#3b82f6' : 'transparent',
                    color: '#fff',
                    border: analyticsMode === 'contract' ? 'none' : '1px solid #475569',
                    borderRadius: 8,
                    padding: '10px 20px',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  📄 Contract Analysis
                </button>
              </div>

              {analyticsMode === 'archetype' ? (
                <div>
                  <label style={{ color: '#cbd5e1', fontSize: 14, fontWeight: 600, display: 'block', marginBottom: 12 }}>
                    Select Contract Type for Analysis
                  </label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    style={{
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid #475569',
                      borderRadius: 8,
                      padding: '12px 16px',
                      fontSize: 14,
                      marginRight: 12
                    }}
                  >
                    {CONTRACT_TYPES.map(type => (
                      <option key={type.id} value={type.id}>{type.label} - {type.short}</option>
                    ))}
                  </select>
                </div>
              ) : (
                <div>
                  <label style={{ color: '#cbd5e1', fontSize: 14, fontWeight: 600, display: 'block', marginBottom: 12 }}>
                    Select Uploaded Contract for Analysis
                  </label>
                  <select
                    value={selectedContractId || ''}
                    onChange={(e) => setSelectedContractId(e.target.value)}
                    style={{
                      background: '#1e293b',
                      color: '#fff',
                      border: '1px solid #475569',
                      borderRadius: 8,
                      padding: '12px 16px',
                      fontSize: 14,
                      marginRight: 12,
                      minWidth: 300
                    }}
                  >
                    <option value="">-- Select Contract --</option>
                    {contracts.map(contract => (
                      <option key={contract.id} value={contract.id}>
                        {contract.original_filename} ({contract.contract_type || 'Unknown'})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div style={{ marginTop: 12 }}>
                <button
                  onClick={() => analyticsMode === 'archetype' ? loadCentrality(selectedType) : loadContractCentrality(selectedContractId)}
                  disabled={analyticsMode === 'contract' && !selectedContractId}
                  style={{
                    background: (analyticsMode === 'contract' && !selectedContractId) ? '#475569' : '#3b82f6',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    padding: '12px 24px',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: (analyticsMode === 'contract' && !selectedContractId) ? 'not-allowed' : 'pointer',
                    marginRight: 12
                  }}
                >
                  Load Centrality
                </button>
                <button
                  onClick={() => loadCommunities(selectedType)}
                  style={{
                    background: '#8b5cf6',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    padding: '12px 24px',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Detect Communities
                </button>
              </div>
            </div>

            {/* Centrality Results */}
            {centralityData && (
              <div style={{ background: 'rgba(30,41,59,0.6)', borderRadius: 12, border: '1px solid rgba(71,85,105,0.5)', padding: 24, marginBottom: 24 }}>
                <h3 style={{ color: '#f1f5f9', fontSize: 16, fontWeight: 700, marginBottom: 16 }}>
                  Centrality Metrics - {centralityData.contract_filename || centralityData.contract_type}
                </h3>
                <div style={{ marginBottom: 16 }}>
                  <strong style={{ color: '#60a5fa' }}>Most Influential Concept:</strong> {centralityData.most_influential}
                </div>
                {centralityData.contract_filename && (
                  <div style={{ marginBottom: 16, fontSize: 13, color: '#94a3b8' }}>
                    Contract-specific analysis based on actual clause data
                  </div>
                )}
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(71,85,105,0.5)' }}>
                      <th style={{ textAlign: 'left', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Concept</th>
                      <th style={{ textAlign: 'right', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Degree</th>
                      <th style={{ textAlign: 'right', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Betweenness</th>
                      <th style={{ textAlign: 'right', color: '#94a3b8', padding: '12px 16px', fontSize: 13 }}>Eigenvector</th>
                    </tr>
                  </thead>
                  <tbody>
                    {centralityData.ranked_by_influence?.map(concept => {
                      const metrics = centralityData.centrality_metrics[concept];
                      return (
                        <tr key={concept} style={{ borderBottom: '1px solid rgba(71,85,105,0.3)' }}>
                          <td style={{ padding: '12px 16px', color: '#f1f5f9', fontWeight: 600 }}>{concept}</td>
                          <td style={{ padding: '12px 16px', textAlign: 'right', color: '#60a5fa', fontFamily: 'monospace' }}>
                            {metrics.degree_centrality.toFixed(3)}
                          </td>
                          <td style={{ padding: '12px 16px', textAlign: 'right', color: '#a78bfa', fontFamily: 'monospace' }}>
                            {metrics.betweenness_centrality.toFixed(3)}
                          </td>
                          <td style={{ padding: '12px 16px', textAlign: 'right', color: '#86efac', fontFamily: 'monospace' }}>
                            {metrics.eigenvector_centrality.toFixed(3)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Community Detection Results */}
            {communitiesData && (
              <div style={{ background: 'rgba(30,41,59,0.6)', borderRadius: 12, border: '1px solid rgba(71,85,105,0.5)', padding: 24 }}>
                <h3 style={{ color: '#f1f5f9', fontSize: 16, fontWeight: 700, marginBottom: 16 }}>
                  Community Detection - {communitiesData.contract_type}
                </h3>
                <div style={{ marginBottom: 16 }}>
                  <strong style={{ color: '#60a5fa' }}>Total Communities:</strong> {communitiesData.total_communities}
                  <span style={{ marginLeft: 24 }}><strong style={{ color: '#8b5cf6' }}>Modularity Score:</strong> {communitiesData.modularity_score?.toFixed(3)}</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
                  {communitiesData.communities && Object.entries(communitiesData.communities).map(([name, community]) => (
                    <div key={community.id} style={{
                      background: 'rgba(59,130,246,0.1)',
                      border: '1px solid rgba(59,130,246,0.3)',
                      borderRadius: 8,
                      padding: 16
                    }}>
                      <div style={{ color: '#60a5fa', fontWeight: 700, marginBottom: 8 }}>{name}</div>
                      <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 12 }}>{community.description}</div>
                      <div style={{ color: '#fff', fontSize: 13 }}>
                        {community.concepts.join(', ')}
                      </div>
                      <div style={{ color: '#64748b', fontSize: 11, marginTop: 8 }}>
                        Size: {community.size} concepts
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════════════════════════════════════ */}
        {/* TAB — How It Works                                */}
        {/* ══════════════════════════════════════════════════ */}
        {activeTab === 'howto' && (
          <div style={{ maxWidth: 820 }}>
            <SectionHeader title="How the Concept Correlation Engine Works" />
            {[
              { step: '1', title: 'Contract Archetype Data', color: '#4C8EDA',
                body: `Five contract archetypes (MSA, SaaS, NDA, Employment, EPC) each carry concept strength scores extracted via Legal-BERT from real CUAD-annotated contracts.\nEach score ∈ [0,1] represents how prominently that concept appears in that contract type.` },
              { step: '2', title: 'Pearson Correlation Calculation', color: '#68BC00',
                body: `For each pair of concepts (e.g. Liability & Indemnification), Pearson correlation is computed across the 5 archetype data points:\n\n  corr(X,Y) = cov(X,Y) / (σ_X × σ_Y)\n\nNormalised from [-1,1] → [0,1]. Strong positive correlation = contracts with high Liability always have high Indemnification.` },
              { step: '3', title: 'Graph Construction', color: '#9063CD',
                body: `Nodes = concepts, sized by average strength.\nEdges = correlation weight above threshold.\n\nFor archetype-specific graphs:\n  combined_weight = pearson × mean(strength_c1, strength_c2)\n\nThis makes edges heavier where both concepts are truly dominant in that archetype.` },
              { step: '4', title: 'What the Visualization Shows', color: '#F79767',
                body: `• Node size → importance of this concept in this contract type\n• Edge thickness → how strongly the two concepts co-move\n• Animated edges → very high correlation (>0.80) — essentially coupled concepts\n• Edge label → exact correlation weight\n\nEPC = dense + thick edges (Risk/Penalty/Liability tightly coupled)\nNDA = sparse (only IP Rights dominates)` },
              { step: '5', title: 'Business Value', color: '#F16667',
                body: `• Identify which legal concepts are structurally coupled in each contract type\n• Reveal hidden risk clusters (e.g. Risk Allocation + Penalty + Force Majeure in EPC)\n• Compare archetype topologies to understand contract DNA\n• Inform negotiation strategy: modifying a high-centrality concept ripples through the entire structure` },
            ].map(s => (
              <div key={s.step} style={{
                background: '#111827', borderRadius: 12, padding: 22,
                border: `1px solid ${s.color}33`, marginBottom: 14,
                borderLeft: `4px solid ${s.color}`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: '50%', background: s.color,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontWeight: 700, fontSize: 14, flexShrink: 0,
                  }}>{s.step}</div>
                  <h3 style={{ margin: 0, color: s.color, fontSize: 14, fontWeight: 700 }}>{s.title}</h3>
                </div>
                <p style={{ margin: 0, color: '#94a3b8', fontSize: 13, lineHeight: 1.75, whiteSpace: 'pre-line' }}>
                  {s.body}
                </p>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function Stat({ label, value, color, caps }) {
  return (
    <div>
      <span style={{ color: '#64748b', fontSize: 12 }}>{label}: </span>
      <span style={{ color, fontWeight: 700, textTransform: caps ? 'capitalize' : 'none' }}>{value}</span>
    </div>
  );
}

function SectionHeader({ title, sub }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h2 style={{ color: '#f1f5f9', fontSize: 18, fontWeight: 700, margin: '0 0 4px' }}>{title}</h2>
      {sub && <p style={{ margin: 0, color: '#64748b', fontSize: 13 }}>{sub}</p>}
    </div>
  );
}
