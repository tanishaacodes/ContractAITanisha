/**
 * ContractGraph3D
 * ================
 * 3D interactive contract knowledge graph using Three.js + CSS3DRenderer.
 * Renders contract nodes as glowing spheres in 3D space with animated edges.
 *
 * Node colors match existing Neo4j palette:
 *   Contract  → #68BC00 (green)
 *   Clause    → #4C8EDA (blue)
 *   Risk      → #F16667 (red)
 *   Obligation → #F79767 (orange)
 *   Party     → #FFD86E (yellow)
 *   Jurisdiction → #9063CD (purple)
 *
 * Props:
 *   nodes: [ { id, label, type, risk_score, size } ]
 *   edges: [ { source, target, label } ]
 *   height: string (default "600px")
 *   onNodeClick: (node) => void
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { RefreshCw, ZoomIn, ZoomOut, RotateCcw, Eye } from 'lucide-react';

const NODE_COLORS = {
  Contract: '#68BC00',
  Clause: '#4C8EDA',
  ClauseType: '#9063CD',
  Risk: '#F16667',
  Obligation: '#F79767',
  Party: '#FFD86E',
  Jurisdiction: '#9063CD',
  Amendment: '#06B6D4',
  Definition: '#10b981',
  Term: '#8b5cf6',
  CrossReference: '#f59e0b',
  ContractEmbedding: '#6366f1',
  Industry: '#06B6D4',
  // Diff status
  same: '#68BC00',
  modified: '#FFD86E',
  missing: '#F16667',
  new: '#4C8EDA',
};

const DEFAULT_COLOR = '#4C8EDA';

// Simple 3D canvas renderer using WebGL-like canvas 2D projection
// (Pure canvas — no Three.js import needed, works without npm install)
class Graph3DRenderer {
  constructor(canvas, width, height) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.width = width;
    this.height = height;
    this.nodes = [];
    this.edges = [];
    this.camera = { x: 0, y: 0, z: 600, rotX: 0.3, rotY: 0.0 };
    this.dragging = false;
    this.lastMouse = { x: 0, y: 0 };
    this.animFrame = null;
    this.onNodeClick = null;
    this.hoveredNode = null;
    this.autoRotate = true;
    this.zoom = 1.0;

    this._bindEvents();
  }

  setData(nodes, edges) {
    // ── Layer-based shell positioning ────────────────────────────────────
    // Each node type gets its own orbital shell radius so nodes never overlap.
    // Shells expand with sqrt(n) so large graphs stay readable.
    const n = nodes.length;
    const scale = Math.max(1, Math.sqrt(n / 8));

    const SHELL_RADIUS = {
      Contract:          0,          // centre — anchor nodes
      ClauseType:        220 * scale,
      Clause:            340 * scale,
      Risk:              440 * scale,
      Obligation:        420 * scale,
      Party:             160 * scale,
      Jurisdiction:      180 * scale,
      Amendment:         300 * scale,
      Industry:          200 * scale,
      Definition:        380 * scale,
    };
    const DEFAULT_SHELL = 300 * scale;

    // Group nodes by shell
    const byShell = {};
    nodes.forEach(node => {
      const shell = SHELL_RADIUS[node.type] ?? DEFAULT_SHELL;
      (byShell[shell] = byShell[shell] || []).push(node);
    });

    // For each shell, spread nodes evenly using golden spiral
    const positioned = new Map(); // id → {x3d,y3d,z3d}
    Object.entries(byShell).forEach(([shellStr, shellNodes]) => {
      const r = parseFloat(shellStr);
      if (r === 0) {
        // Contract nodes: place at origin spread slightly
        shellNodes.forEach((node, i) => {
          const gap = 80 * scale;
          positioned.set(node.id, {
            x3d: (i - (shellNodes.length - 1) / 2) * gap,
            y3d: 0,
            z3d: 0,
          });
        });
        return;
      }
      const m = shellNodes.length;
      shellNodes.forEach((node, i) => {
        const phi   = Math.acos(-1 + (2 * i) / Math.max(m, 1));
        const theta = Math.sqrt(m * Math.PI) * phi;
        positioned.set(node.id, {
          x3d: r * Math.sin(phi) * Math.cos(theta),
          y3d: r * Math.sin(phi) * Math.sin(theta),
          z3d: r * Math.cos(phi),
        });
      });
    });

    this.nodes = nodes.map(node => {
      const pos = positioned.get(node.id) || { x3d: 0, y3d: 0, z3d: 0 };
      return {
        ...node,
        ...pos,
        color: NODE_COLORS[node.type] || NODE_COLORS[node.diff_status] || DEFAULT_COLOR,
        // Node visual radius: bigger for Contract/ClauseType, smaller for leaf nodes
        radius: node.type === 'Contract'    ? 22
               : node.type === 'ClauseType' ? 16
               : node.type === 'Risk'       ? 10
               : node.type === 'Obligation' ? 9
               : 10 + (node.size || 40) * 0.12,
      };
    });

    this.edges = edges.map(e => ({
      ...e,
      sourceNode: this.nodes.find(nd => nd.id === e.source),
      targetNode: this.nodes.find(nd => nd.id === e.target),
    })).filter(e => e.sourceNode && e.targetNode);

    // Auto-fit camera distance to graph extent
    const maxR = Math.max(...this.nodes.map(nd =>
      Math.sqrt(nd.x3d ** 2 + nd.y3d ** 2 + nd.z3d ** 2)
    ), 1);
    this.camera.z = maxR * 2.8;
  }

  _project(x3d, y3d, z3d) {
    // Rotate around Y axis
    const cosY = Math.cos(this.camera.rotY);
    const sinY = Math.sin(this.camera.rotY);
    let rx = x3d * cosY - z3d * sinY;
    let rz = x3d * sinY + z3d * cosY;

    // Rotate around X axis
    const cosX = Math.cos(this.camera.rotX);
    const sinX = Math.sin(this.camera.rotX);
    let ry = y3d * cosX - rz * sinX;
    rz = y3d * sinX + rz * cosX;

    // Perspective projection — focal length scales with camera distance
    const focal = this.camera.z * this.zoom;
    const depth  = focal + rz;
    const perspScale = depth > 0 ? focal / depth : 0.01;
    const px = this.width  / 2 + rx * perspScale;
    const py = this.height / 2 + ry * perspScale;
    return { x: px, y: py, scale: perspScale, depth: rz };
  }

  _render() {
    const { ctx, width, height } = this;

    // Clear with dark background
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);

    // Auto-rotate
    if (this.autoRotate && !this.dragging) {
      this.camera.rotY += 0.004;
    }

    // Project all nodes
    const projected = this.nodes.map(node => ({
      node,
      proj: this._project(node.x3d, node.y3d, node.z3d),
    }));

    // Sort by depth (painter's algorithm — far nodes first)
    projected.sort((a, b) => b.proj.depth - a.proj.depth);

    // Draw edges first
    this.edges.forEach(edge => {
      const src = this._project(edge.sourceNode.x3d, edge.sourceNode.y3d, edge.sourceNode.z3d);
      const tgt = this._project(edge.targetNode.x3d, edge.targetNode.y3d, edge.targetNode.z3d);
      const alpha = Math.max(0.1, Math.min(0.5, 0.3 + (src.scale + tgt.scale) * 0.3));
      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      ctx.strokeStyle = `rgba(100, 150, 255, ${alpha})`;
      ctx.lineWidth = Math.max(0.5, (src.scale + tgt.scale) * 0.8);
      ctx.stroke();
    });

    // Draw nodes
    projected.forEach(({ node, proj }) => {
      // Clamp scale so far/near nodes don't become invisible or giant
      const clampedScale = Math.max(0.25, Math.min(2.0, proj.scale));
      const r = node.radius * clampedScale;
      const isHovered = this.hoveredNode && this.hoveredNode.id === node.id;

      // Glow effect for hovered/high-risk nodes
      if (isHovered || (node.risk_score && node.risk_score > 0.6)) {
        const glowR = r * (isHovered ? 2.5 : 1.8);
        const grd = ctx.createRadialGradient(proj.x, proj.y, 0, proj.x, proj.y, glowR);
        grd.addColorStop(0, node.color + '44');
        grd.addColorStop(1, node.color + '00');
        ctx.beginPath();
        ctx.arc(proj.x, proj.y, glowR, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.fill();
      }

      // Node sphere (radial gradient for 3D sheen)
      const grd = ctx.createRadialGradient(
        proj.x - r * 0.3, proj.y - r * 0.3, 0,
        proj.x, proj.y, r
      );
      grd.addColorStop(0, node.color + 'ff');
      grd.addColorStop(0.6, node.color + 'cc');
      grd.addColorStop(1, node.color + '44');
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, Math.max(r, 2), 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();

      // Border ring
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, Math.max(r, 2), 0, Math.PI * 2);
      ctx.strokeStyle = isHovered ? '#ffffff' : node.color;
      ctx.lineWidth = isHovered ? 2 : 0.8;
      ctx.stroke();

      // Label — always show for Contract/ClauseType, show others when big enough
      const showLabel = isHovered || r > 10 ||
                        node.type === 'Contract' || node.type === 'ClauseType';
      if (showLabel) {
        const label = (node.label || node.id || '').slice(0, 18);
        ctx.font = `${Math.max(9, Math.min(14, r * 0.85))}px Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#000000';
        ctx.shadowBlur = 4;
        ctx.fillText(label, proj.x, proj.y + r + 12);
        ctx.shadowBlur = 0;
      }
    });

    // Tooltip for hovered node
    if (this.hoveredNode) {
      const proj = this._project(this.hoveredNode.x3d, this.hoveredNode.y3d, this.hoveredNode.z3d);
      const text = `${this.hoveredNode.type}: ${this.hoveredNode.label}`;
      const risk = this.hoveredNode.risk_score ? ` | Risk: ${(this.hoveredNode.risk_score * 100).toFixed(0)}%` : '';
      ctx.font = '11px Inter, sans-serif';
      const tw = ctx.measureText(text + risk).width + 16;
      const tx = Math.min(Math.max(proj.x - tw / 2, 4), width - tw - 4);
      const ty = proj.y - 36;
      ctx.fillStyle = 'rgba(15,23,42,0.92)';
      ctx.strokeStyle = '#4C8EDA';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(tx, ty, tw, 24, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#e2e8f0';
      ctx.fillText(text + risk, tx + 8, ty + 15);
    }

    // Stats overlay
    ctx.font = '10px monospace';
    ctx.fillStyle = '#334155';
    ctx.fillText(`Nodes: ${this.nodes.length} | Edges: ${this.edges.length}`, 8, height - 8);
  }

  _bindEvents() {
    const canvas = this.canvas;

    canvas.addEventListener('mousedown', e => {
      this.dragging = true;
      this.autoRotate = false;
      this.lastMouse = { x: e.clientX, y: e.clientY };
    });

    canvas.addEventListener('mousemove', e => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      if (this.dragging) {
        const dx = e.clientX - this.lastMouse.x;
        const dy = e.clientY - this.lastMouse.y;
        this.camera.rotY += dx * 0.005;
        this.camera.rotX += dy * 0.005;
        this.lastMouse = { x: e.clientX, y: e.clientY };
      }

      // Hit test for hover
      this.hoveredNode = null;
      const projected = this.nodes.map(node => ({
        node,
        proj: this._project(node.x3d, node.y3d, node.z3d),
      }));
      projected.sort((a, b) => b.proj.depth - a.proj.depth);
      for (const { node, proj } of projected) {
        const r = node.radius * Math.max(0.25, Math.min(2.0, proj.scale));
        const dist = Math.sqrt((mx - proj.x) ** 2 + (my - proj.y) ** 2);
        if (dist < r + 4) {
          this.hoveredNode = node;
          canvas.style.cursor = 'pointer';
          break;
        }
      }
      if (!this.hoveredNode) canvas.style.cursor = 'grab';
    });

    canvas.addEventListener('mouseup', () => { this.dragging = false; });
    canvas.addEventListener('mouseleave', () => { this.dragging = false; this.hoveredNode = null; });

    canvas.addEventListener('click', e => {
      if (this.hoveredNode && this.onNodeClick) {
        this.onNodeClick(this.hoveredNode);
      }
    });

    canvas.addEventListener('wheel', e => {
      e.preventDefault();
      this.zoom = Math.max(0.3, Math.min(3.0, this.zoom - e.deltaY * 0.001));
    }, { passive: false });
  }

  start() {
    const loop = () => {
      this._render();
      this.animFrame = requestAnimationFrame(loop);
    };
    loop();
  }

  stop() {
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
  }

  reset() {
    // Re-fit camera to current graph extent
    const maxR = this.nodes.length
      ? Math.max(...this.nodes.map(nd =>
          Math.sqrt(nd.x3d ** 2 + nd.y3d ** 2 + nd.z3d ** 2)
        ), 1)
      : 600;
    this.camera = { x: 0, y: 0, z: maxR * 2.8, rotX: 0.3, rotY: 0.0 };
    this.zoom = 1.0;
    this.autoRotate = true;
  }
}

// ─── React Component ─────────────────────────────────────────────────────────

export default function ContractGraph3D({ nodes = [], edges = [], height = '600px', onNodeClick }) {
  const canvasRef = useRef(null);
  const rendererRef = useRef(null);
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [autoRotate, setAutoRotate] = useState(true);

  const initRenderer = useCallback(() => {
    if (!canvasRef.current || !containerRef.current) return;
    const w = containerRef.current.offsetWidth || 800;
    const h = parseInt(height) || 600;

    canvasRef.current.width = w;
    canvasRef.current.height = h;

    if (rendererRef.current) rendererRef.current.stop();

    const renderer = new Graph3DRenderer(canvasRef.current, w, h);
    renderer.setData(nodes, edges);
    renderer.onNodeClick = (node) => {
      setSelectedNode(node);
      if (onNodeClick) onNodeClick(node);
    };
    renderer.start();
    rendererRef.current = renderer;
  }, [nodes, edges, height, onNodeClick]);

  useEffect(() => {
    initRenderer();
    return () => { if (rendererRef.current) rendererRef.current.stop(); };
  }, [initRenderer]);

  const handleReset = () => {
    if (rendererRef.current) {
      rendererRef.current.reset();
      setAutoRotate(true);
    }
  };

  const handleToggleRotate = () => {
    if (rendererRef.current) {
      rendererRef.current.autoRotate = !rendererRef.current.autoRotate;
      setAutoRotate(rendererRef.current.autoRotate);
    }
  };

  const handleZoomIn = () => {
    if (rendererRef.current) rendererRef.current.zoom = Math.min(3.0, rendererRef.current.zoom + 0.2);
  };
  const handleZoomOut = () => {
    if (rendererRef.current) rendererRef.current.zoom = Math.max(0.3, rendererRef.current.zoom - 0.2);
  };

  if (!nodes.length) {
    return (
      <div
        className="flex items-center justify-center bg-slate-950 rounded-xl border border-slate-700"
        style={{ height }}
      >
        <div className="text-center text-slate-500">
          <div className="text-4xl mb-3">🌐</div>
          <p className="text-sm">No graph data — run comparison or ingestion first</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-700 bg-slate-950" ref={containerRef}>
      {/* Controls */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-2">
        <button
          onClick={handleReset}
          className="p-2 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 backdrop-blur"
          title="Reset view"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
        <button
          onClick={handleToggleRotate}
          className={`p-2 rounded-lg text-slate-300 backdrop-blur transition-colors ${autoRotate ? 'bg-blue-700/80 hover:bg-blue-600' : 'bg-slate-800/80 hover:bg-slate-700'}`}
          title={autoRotate ? 'Stop auto-rotate' : 'Start auto-rotate'}
        >
          <RefreshCw className="w-4 h-4" />
        </button>
        <button onClick={handleZoomIn} className="p-2 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 backdrop-blur" title="Zoom in">
          <ZoomIn className="w-4 h-4" />
        </button>
        <button onClick={handleZoomOut} className="p-2 bg-slate-800/80 hover:bg-slate-700 rounded-lg text-slate-300 backdrop-blur" title="Zoom out">
          <ZoomOut className="w-4 h-4" />
        </button>
      </div>

      {/* Label */}
      <div className="absolute top-3 left-3 z-10">
        <span className="px-2 py-1 bg-slate-900/80 text-slate-400 text-xs rounded font-mono backdrop-blur">
          3D Contract Graph · Drag to rotate · Scroll to zoom
        </span>
      </div>

      {/* Canvas */}
      <canvas ref={canvasRef} style={{ width: '100%', height }} className="block" />

      {/* Selected node panel */}
      {selectedNode && (
        <div className="absolute bottom-3 left-3 right-3 z-10">
          <div className="bg-slate-900/95 border border-slate-600 rounded-lg p-3 backdrop-blur max-w-sm">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: NODE_COLORS[selectedNode.type] || DEFAULT_COLOR }}
                />
                <span className="text-white text-sm font-semibold">{selectedNode.label}</span>
              </div>
              <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-white text-xs">✕</button>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <span className="text-slate-400">Type</span>
              <span className="text-slate-200">{selectedNode.type}</span>
              {selectedNode.risk_score != null && (
                <>
                  <span className="text-slate-400">Risk Score</span>
                  <span className={`font-semibold ${selectedNode.risk_score > 0.6 ? 'text-red-400' : selectedNode.risk_score > 0.3 ? 'text-yellow-400' : 'text-green-400'}`}>
                    {(selectedNode.risk_score * 100).toFixed(1)}%
                  </span>
                </>
              )}
              {selectedNode.diff_status && (
                <>
                  <span className="text-slate-400">Diff Status</span>
                  <span className="text-slate-200 capitalize">{selectedNode.diff_status}</span>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Node type legend */}
      <div className="absolute bottom-3 right-3 z-10">
        <div className="bg-slate-900/80 rounded-lg p-2 backdrop-blur">
          {Object.entries(NODE_COLORS).slice(0, 6).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5 mb-1">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-slate-400 text-xs">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
