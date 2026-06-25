import { useRef, useState, useEffect, useCallback } from "react";
import { Network, Zap, RefreshCw, ZoomIn, ZoomOut, RotateCcw, X, Maximize2, Minimize2 } from "lucide-react";
import axios from "axios";
import { config } from "../../config/api.config";

const API_BASE_URL = config.API_BASE_URL;

// ── Node colours by type ──────────────────────────────────────────────────────
const TYPE_STYLE = {
  Contract:    { fill: "#1e3a5f", stroke: "#3b82f6", text: "#93c5fd", r: 28 },
  Clause:      { fill: "#1a0a3e", stroke: "#8b5cf6", text: "#c4b5fd", r: 20 },
  Risk:        { fill: "#3b0d0d", stroke: "#ef4444", text: "#fca5a5", r: 20 },
  Party:       { fill: "#0c2233", stroke: "#06b6d4", text: "#67e8f9", r: 18 },
  Obligation:  { fill: "#052e16", stroke: "#10b981", text: "#6ee7b7", r: 18 },
  Status:      { fill: "#1a1a3e", stroke: "#6366f1", text: "#a5b4fc", r: 14 },
  RISK_CLUSTER:{ fill: "#2d1a00", stroke: "#f97316", text: "#fdba74", r: 24 },
  default:     { fill: "#1e293b", stroke: "#64748b", text: "#94a3b8", r: 16 },
};

const CLAUSE_LABELS = ["Liability","Payment","Termination","IP Rights","Indemnity","Penalties","Compliance","Arbitration","Confidentiality","SLA","Force Majeure","Warranty","Governing Law","Dispute Resolution"];
const OBLIGATION_LABELS = ["Delivery Obligation","Payment Obligation","Reporting Duty","Confidentiality Duty","Performance Target","Audit Right","Non-Compete","Notice Requirement"];
const RISK_LABELS = ["Unlimited Liability","Auto-Renewal Trap","Unilateral Termination","IP Ownership Risk","Penalty Clause","Jurisdiction Risk","Force Majeure Gap","Data Privacy Risk"];

function parseVal(raw) {
  if (!raw) return 0;
  try {
    let s = String(raw).trim(), m = 1;
    if (s.toUpperCase().endsWith("B")) { m = 1e9; s = s.slice(0,-1); }
    else if (s.toUpperCase().endsWith("M")) { m = 1e6; s = s.slice(0,-1); }
    else if (s.toUpperCase().endsWith("K")) { m = 1e3; s = s.slice(0,-1); }
    return parseFloat(s.replace(/[$,]/g,"")) * m || 0;
  } catch { return 0; }
}
function fmtVal(v) {
  if (!v) return "";
  if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v/1e3).toFixed(0)}K`;
  return `$${v}`;
}

// ── Build nodes + links from real contracts ───────────────────────────────────
function buildGraph(contracts, selectedId, W, H) {
  const nodes = [], links = [];
  const partyMap = {};
  const cx = W / 2, cy = H / 2;

  const display = selectedId && selectedId !== "all"
    ? contracts.filter(c => String(c.id) === String(selectedId))
    : contracts.slice(0, 10);
  if (!display.length) return { nodes, links };

  const n = display.length;
  const contractR = Math.min(cx, cy) * 0.48;

  display.forEach((c, i) => {
    const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
    const cId = `contract-${c.id || i}`;
    const risk = c.liability_level === "HIGH" ? 88 : c.liability_level === "MEDIUM" ? 62 : 30;
    const val  = parseVal(c.contract_value);
    const name = (c.original_filename || `Contract ${i+1}`).replace(/\.(pdf|docx?|txt)$/i,"").substring(0,22);

    // Contract node on ring
    const cx2 = cx + Math.cos(angle) * contractR;
    const cy2 = cy + Math.sin(angle) * contractR;
    nodes.push({ id: cId, label: name, type: "Contract", x: cx2, y: cy2,
      risk, val, status: c.status, party: c.party_name, end_date: c.end_date,
      contract_type: c.contract_type, vx: 0, vy: 0 });

    // 2 Clause satellites — tangent left/right
    [0, 1].forEach(j => {
      const oAng = angle + (j === 0 ? -0.65 : 0.65);
      const oR   = contractR - 85;
      const oId  = `clause-${cId}-${j}`;
      nodes.push({ id: oId, label: CLAUSE_LABELS[(i*2+j) % CLAUSE_LABELS.length],
        type: "Clause", x: cx + Math.cos(oAng) * Math.max(oR, 60),
        y: cy + Math.sin(oAng) * Math.max(oR, 60), vx: 0, vy: 0 });
      links.push({ source: cId, target: oId, label: "HAS_CLAUSE" });
    });

    // 1 Risk node — outward
    const rAng = angle;
    const rR   = contractR + 90;
    const rId  = `risk-${cId}`;
    const riskColor = risk >= 75 ? "Risk" : "Risk";
    nodes.push({ id: rId, label: RISK_LABELS[i % RISK_LABELS.length],
      type: "Risk", x: cx + Math.cos(rAng) * rR, y: cy + Math.sin(rAng) * rR,
      risk, vx: 0, vy: 0 });
    links.push({ source: cId, target: rId, label: "HAS_RISK" });

    // 1 Obligation — between contract and center
    const oblAng = angle + Math.PI * 0.12;
    const oblR   = contractR * 0.55;
    const oblId  = `obl-${cId}`;
    nodes.push({ id: oblId, label: OBLIGATION_LABELS[i % OBLIGATION_LABELS.length],
      type: "Obligation", x: cx + Math.cos(oblAng) * oblR,
      y: cy + Math.sin(oblAng) * oblR, vx: 0, vy: 0 });
    links.push({ source: cId, target: oblId, label: "HAS_OBLIGATION" });

    // Party — further outward at offset angle
    if (c.party_name && c.party_name !== "Unknown") {
      const pKey = c.party_name.substring(0, 20);
      if (!partyMap[pKey]) {
        const pAng = angle + Math.PI * 0.3;
        const pR   = contractR + 110;
        const pId  = `party-${Object.keys(partyMap).length}`;
        partyMap[pKey] = pId;
        nodes.push({ id: pId, label: pKey, type: "Party",
          x: cx + Math.cos(pAng) * pR, y: cy + Math.sin(pAng) * pR, vx: 0, vy: 0 });
      }
      links.push({ source: cId, target: partyMap[c.party_name.substring(0,20)], label: "WITH_PARTY" });
    }

    // Status badge — tiny node near contract
    if (c.status) {
      const sId = `status-${cId}`;
      nodes.push({ id: sId, label: c.status, type: "Status",
        x: cx2 + 35, y: cy2 - 35, vx: 0, vy: 0 });
      links.push({ source: cId, target: sId, label: "STATUS" });
    }
  });

  return { nodes, links };
}

// ── Force simulation (Verlet) ─────────────────────────────────────────────────
function runForces(nodes, links, W, H, iterations = 180) {
  const idMap = {};
  nodes.forEach(n => { idMap[n.id] = n; });

  for (let iter = 0; iter < iterations; iter++) {
    const alpha = 1 - iter / iterations;

    // Repulsion between all pairs
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx*dx + dy*dy) || 0.01;
        const minDist = (getR(a) + getR(b)) * 2.8 + 50;
        if (dist < minDist) {
          const force = (minDist - dist) / dist * 0.5 * alpha;
          const fx = dx * force, fy = dy * force;
          a.x -= fx; a.y -= fy;
          b.x += fx; b.y += fy;
        }
      }
    }

    // Link attraction
    links.forEach(l => {
      const a = idMap[l.source], b = idMap[l.target];
      if (!a || !b) return;
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.sqrt(dx*dx + dy*dy) || 0.01;
      const target = 160;
      if (dist > target) {
        const force = (dist - target) / dist * 0.12 * alpha;
        const fx = dx * force, fy = dy * force;
        a.x += fx; a.y += fy;
        b.x -= fx; b.y -= fy;
      }
    });

    // Keep inside bounds
    nodes.forEach(n => {
      const r = getR(n) + 30;
      n.x = Math.max(r, Math.min(W - r, n.x));
      n.y = Math.max(r, Math.min(H - r, n.y));
    });
  }
}

function getR(node) {
  const s = TYPE_STYLE[node.type] || TYPE_STYLE.default;
  return s.r;
}

// ── Canvas draw helpers ───────────────────────────────────────────────────────
function drawNode(ctx, node, sel, hov, t) {
  const s = TYPE_STYLE[node.type] || TYPE_STYLE.default;
  const pulse = 1 + Math.sin(t * 2.2) * (sel || hov ? 0.14 : 0.04);
  const r = s.r * pulse;
  const { x, y } = node;

  // Glow
  if (sel || hov || node.type === "Risk" && node.risk >= 75) {
    const gl = ctx.createRadialGradient(x, y, 0, x, y, r * 3);
    gl.addColorStop(0, s.stroke + (sel ? "55" : "22"));
    gl.addColorStop(1, s.stroke + "00");
    ctx.beginPath(); ctx.arc(x, y, r * 3, 0, Math.PI*2);
    ctx.fillStyle = gl; ctx.fill();
  }

  ctx.save();
  ctx.shadowBlur = sel ? 24 : hov ? 14 : 7;
  ctx.shadowColor = s.stroke;

  // Node shape
  ctx.beginPath();
  if (node.type === "Clause") {
    // rounded rect
    const rr = r * 0.8;
    ctx.roundRect(x - rr, y - rr * 0.65, rr * 2, rr * 1.3, 5);
  } else if (node.type === "Risk") {
    // diamond
    ctx.moveTo(x, y - r); ctx.lineTo(x + r*0.75, y);
    ctx.lineTo(x, y + r); ctx.lineTo(x - r*0.75, y); ctx.closePath();
  } else if (node.type === "Status") {
    // pill
    const rx = r * 1.4, ry = r * 0.6;
    ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI*2);
  } else {
    ctx.arc(x, y, r, 0, Math.PI*2);
  }
  ctx.fillStyle = s.fill; ctx.fill();
  ctx.lineWidth = sel ? 2.5 : 1.8;
  ctx.strokeStyle = sel ? "#ffffff" : s.stroke; ctx.stroke();
  ctx.restore();

  // Selection ring
  if (sel) {
    ctx.beginPath(); ctx.arc(x, y, r + 8, 0, Math.PI*2);
    ctx.strokeStyle = "#ffffff33"; ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]); ctx.stroke(); ctx.setLineDash([]);
  }

  // Label
  const fs = node.type === "Contract" ? 10 : node.type === "Status" ? 8 : 9;
  ctx.font = `${sel ? "bold " : ""}${fs}px Inter, sans-serif`;
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  const labelY = y + r + 14;
  const txt = node.label.length > 20 ? node.label.substring(0,18) + "…" : node.label;
  const tw = ctx.measureText(txt).width + 10;
  ctx.fillStyle = "rgba(2,6,23,0.9)";
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x - tw/2, labelY - 9, tw, 18, 5);
  else ctx.rect(x - tw/2, labelY - 9, tw, 18);
  ctx.fill();
  ctx.strokeStyle = s.stroke + "55"; ctx.lineWidth = 0.8; ctx.stroke();
  ctx.fillStyle = sel ? "#ffffff" : s.text;
  ctx.fillText(txt, x, labelY);

  // Value badge for contracts
  if (node.type === "Contract" && node.val > 0) {
    const vt = fmtVal(node.val);
    const vw = ctx.measureText(vt).width + 8;
    ctx.fillStyle = "#052e16cc";
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x - vw/2, y - r - 20, vw, 14, 3);
    else ctx.rect(x - vw/2, y - r - 20, vw, 14);
    ctx.fill();
    ctx.strokeStyle = "#10b98155"; ctx.lineWidth = 0.8; ctx.stroke();
    ctx.font = "bold 8px monospace";
    ctx.fillStyle = "#34d399";
    ctx.fillText(vt, x, y - r - 13);
  }

  // Type icon inside
  const icon = { Contract:"◆", Clause:"§", Risk:"⚠", Party:"●", Obligation:"✓", Status:"•", RISK_CLUSTER:"★" }[node.type] || "●";
  ctx.font = `${Math.max(8, r * 0.5)}px sans-serif`;
  ctx.fillStyle = s.stroke + "cc";
  ctx.fillText(icon, x, y + 1);
}

function drawLink(ctx, link, nodes, t) {
  const src = nodes.find(n => n.id === link.source);
  const tgt = nodes.find(n => n.id === link.target);
  if (!src || !tgt) return;

  const ss = TYPE_STYLE[src.type] || TYPE_STYLE.default;
  const ts = TYPE_STYLE[tgt.type] || TYPE_STYLE.default;

  // Gradient line
  const grad = ctx.createLinearGradient(src.x, src.y, tgt.x, tgt.y);
  grad.addColorStop(0, ss.stroke + "88");
  grad.addColorStop(1, ts.stroke + "55");

  const mx = (src.x + tgt.x) / 2;
  const my = (src.y + tgt.y) / 2 - 15;

  ctx.save();
  ctx.strokeStyle = grad;
  ctx.lineWidth = 1.2;

  // Animate dashes for risk links
  if (tgt.type === "Risk" || link.label === "HAS_RISK") {
    const off = (t * 10) % 14;
    ctx.setLineDash([5, 4]); ctx.lineDashOffset = -off;
  }

  ctx.beginPath();
  ctx.moveTo(src.x, src.y);
  ctx.quadraticCurveTo(mx, my, tgt.x, tgt.y);
  ctx.stroke();
  ctx.setLineDash([]);

  // Arrowhead at target
  const dx = tgt.x - src.x, dy = tgt.y - src.y;
  const len = Math.sqrt(dx*dx + dy*dy) || 1;
  const ux = dx/len, uy = dy/len;
  const ar = getR(tgt) + 2;
  const ax = tgt.x - ux * ar, ay = tgt.y - uy * ar;
  ctx.beginPath();
  ctx.moveTo(ax - ux*7 - uy*4, ay - uy*7 + ux*4);
  ctx.lineTo(ax, ay);
  ctx.lineTo(ax - ux*7 + uy*4, ay - uy*7 - ux*4);
  ctx.strokeStyle = ts.stroke + "99"; ctx.lineWidth = 1.2; ctx.stroke();

  // Edge label
  if (link.label) {
    ctx.font = "7px Inter, sans-serif";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    const lx = mx, ly = my - 7;
    const tw = ctx.measureText(link.label).width + 6;
    ctx.fillStyle = "rgba(2,6,23,0.75)"; ctx.fillRect(lx - tw/2, ly - 6, tw, 12);
    ctx.fillStyle = "#94a3b8"; ctx.fillText(link.label, lx, ly);
  }

  ctx.restore();
}

// ── Main component ────────────────────────────────────────────────────────────
export default function Neo4jExplorer({ selectedContract, contractData }) {
  const canvasRef = useRef(null);
  const animRef   = useRef(null);
  const stateRef  = useRef({ nodes: [], links: [], zoom: 1, panX: 0, panY: 0, drag: null, t: 0 });

  const [selNode, setSelNode]     = useState(null);
  const [hovNode, setHovNode]     = useState(null);
  const [loading, setLoading]     = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [zoom, setZoom]           = useState(1);
  const [stats, setStats]         = useState({ nodes: 0, links: 0, contracts: 0 });

  // Build and lay out graph
  const rebuild = useCallback(() => {
    const canvas = canvasRef.current;
    const W = canvas ? canvas.offsetWidth : 900;
    const H = canvas ? canvas.offsetHeight : 500;

    const contracts = Array.isArray(contractData) ? contractData : (contractData ? [contractData] : []);
    const { nodes, links } = buildGraph(contracts, selectedContract, W, H);

    if (nodes.length > 0) {
      runForces(nodes, links, W, H, 200);
    }

    stateRef.current.nodes = nodes;
    stateRef.current.links = links;
    stateRef.current.zoom  = 1;
    stateRef.current.panX  = 0;
    stateRef.current.panY  = 0;
    setStats({ nodes: nodes.length, links: links.length,
      contracts: nodes.filter(n => n.type === "Contract").length });
    setLoading(false);
  }, [contractData, selectedContract]);

  useEffect(() => { setLoading(true); setSelNode(null); rebuild(); }, [rebuild]);

  // Resize
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ro = new ResizeObserver(() => {
      canvas.width  = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
      rebuild();
    });
    ro.observe(canvas);
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    return () => ro.disconnect();
  }, [rebuild]);

  // Render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const draw = () => {
      const ctx = canvas.getContext("2d");
      const { nodes, links, zoom: z, panX, panY, t } = stateRef.current;
      const W = canvas.width, H = canvas.height;
      ctx.clearRect(0, 0, W, H);

      // Grid
      ctx.save();
      ctx.strokeStyle = "#1e293b44"; ctx.lineWidth = 0.5;
      const gs = 44 * z;
      const ox = ((panX % gs) + gs) % gs, oy = ((panY % gs) + gs) % gs;
      for (let x = ox; x < W; x += gs) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
      for (let y = oy; y < H; y += gs) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
      ctx.restore();

      ctx.save();
      ctx.translate(panX, panY);
      ctx.scale(z, z);

      links.forEach(l => drawLink(ctx, l, nodes, t));
      nodes.forEach(n => drawNode(ctx, n, selNode?.id === n.id, hovNode?.id === n.id, t));

      ctx.restore();
      stateRef.current.t += 0.016;
      animRef.current = requestAnimationFrame(draw);
    };
    animRef.current = requestAnimationFrame(draw);
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, [selNode, hovNode]);

  // Hit test
  const hitTest = useCallback((ex, ey) => {
    const { nodes, zoom: z, panX, panY } = stateRef.current;
    const wx = (ex - panX) / z, wy = (ey - panY) / z;
    let best = null, bestD = 99999;
    nodes.forEach(n => {
      const d = Math.hypot(n.x - wx, n.y - wy);
      if (d < getR(n) + 12 && d < bestD) { bestD = d; best = n; }
    });
    return best;
  }, []);

  const onMouseMove = useCallback(e => {
    const rect = canvasRef.current.getBoundingClientRect();
    const ex = e.clientX - rect.left, ey = e.clientY - rect.top;
    const { drag } = stateRef.current;
    if (drag) {
      if (drag.type === "pan") {
        stateRef.current.panX += e.movementX;
        stateRef.current.panY += e.movementY;
      } else if (drag.node) {
        const { zoom: z, panX, panY } = stateRef.current;
        drag.node.x = (ex - panX) / z;
        drag.node.y = (ey - panY) / z;
      }
      return;
    }
    const hit = hitTest(ex, ey);
    setHovNode(hit);
    canvasRef.current.style.cursor = hit ? "pointer" : "grab";
  }, [hitTest]);

  const onMouseDown = useCallback(e => {
    const rect = canvasRef.current.getBoundingClientRect();
    const hit = hitTest(e.clientX - rect.left, e.clientY - rect.top);
    stateRef.current.drag = hit ? { type: "node", node: hit } : { type: "pan" };
  }, [hitTest]);

  const onMouseUp = useCallback(e => {
    const { drag } = stateRef.current;
    if (drag?.type === "node") {
      const rect = canvasRef.current.getBoundingClientRect();
      const hit = hitTest(e.clientX - rect.left, e.clientY - rect.top);
      if (hit) setSelNode(n => n?.id === hit.id ? null : hit);
    }
    stateRef.current.drag = null;
  }, [hitTest]);

  const onWheel = useCallback(e => {
    e.preventDefault();
    stateRef.current.zoom = Math.min(3, Math.max(0.2, stateRef.current.zoom * (e.deltaY < 0 ? 1.12 : 0.9)));
    setZoom(stateRef.current.zoom);
  }, []);

  useEffect(() => {
    const c = canvasRef.current; if (!c) return;
    c.addEventListener("wheel", onWheel, { passive: false });
    return () => c.removeEventListener("wheel", onWheel);
  }, [onWheel]);

  const adjZoom = d => { stateRef.current.zoom = Math.min(3, Math.max(0.2, stateRef.current.zoom * d)); setZoom(stateRef.current.zoom); };
  const reset   = () => { stateRef.current.zoom = 1; stateRef.current.panX = 0; stateRef.current.panY = 0; setZoom(1); setSelNode(null); rebuild(); };

  const selStyle = selNode ? (TYPE_STYLE[selNode.type] || TYPE_STYLE.default) : null;

  return (
    <div className={`rounded-2xl bg-slate-950 border border-white/10 shadow-2xl flex flex-col ${fullscreen ? "fixed inset-2 z-50" : "h-[620px]"}`}>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-1 h-6 bg-gradient-to-b from-violet-500 to-purple-700 rounded-full" />
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Neo4j Knowledge Graph Explorer
              <span className="text-xs text-slate-500 font-normal">
                {selectedContract === "all" ? "(Portfolio)" : "(Contract)"}
              </span>
            </h3>
            <p className="text-xs text-slate-500">{stats.nodes} nodes · {stats.links} edges · drag · scroll zoom · click for details</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {loading && <RefreshCw className="w-4 h-4 text-violet-400 animate-spin" />}
          {!loading && <Zap className="w-4 h-4 text-violet-400 animate-pulse" />}
          <button onClick={() => adjZoom(1.2)} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"><ZoomIn className="w-3.5 h-3.5 text-white" /></button>
          <button onClick={() => adjZoom(0.85)} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"><ZoomOut className="w-3.5 h-3.5 text-white" /></button>
          <button onClick={reset} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"><RotateCcw className="w-3.5 h-3.5 text-white" /></button>
          <button onClick={() => setFullscreen(v => !v)} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            {fullscreen ? <Minimize2 className="w-3.5 h-3.5 text-white" /> : <Maximize2 className="w-3.5 h-3.5 text-white" />}
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative min-h-0">
        <canvas ref={canvasRef} className="w-full h-full block" style={{ cursor: "grab" }}
          onMouseMove={onMouseMove} onMouseDown={onMouseDown} onMouseUp={onMouseUp}
          onMouseLeave={() => { stateRef.current.drag = null; setHovNode(null); }} />

        <div className="absolute bottom-3 right-3 text-[10px] text-slate-500 bg-slate-900/80 px-2 py-1 rounded border border-white/10">{Math.round(zoom * 100)}%</div>

        {/* Selected node panel */}
        {selNode && (
          <div className="absolute top-3 left-3 bg-slate-900/96 backdrop-blur border rounded-xl p-3 text-xs z-10 min-w-[210px]"
            style={{ borderColor: (selStyle?.stroke || "#64748b") + "55" }}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: selStyle?.stroke }} />
                <span className="font-bold text-white text-sm">{selNode.label}</span>
              </div>
              <button onClick={() => setSelNode(null)} className="text-slate-500 hover:text-white"><X className="w-3.5 h-3.5" /></button>
            </div>
            <div className="space-y-1">
              {[
                ["Type",     selNode.type,          "text-violet-400"],
                ["Risk",     selNode.risk != null ? `${selNode.risk}/100` : null,
                  selNode.risk >= 75 ? "text-red-400" : selNode.risk >= 50 ? "text-yellow-400" : "text-green-400"],
                ["Value",    selNode.val > 0 ? fmtVal(selNode.val) : null, "text-green-400 font-mono font-bold"],
                ["Party",    selNode.party,          "text-cyan-400"],
                ["Status",   selNode.status,         "text-purple-400"],
                ["Expires",  selNode.end_date,       "text-slate-300"],
                ["Contract", selNode.contract_type,  "text-blue-400"],
              ].filter(r => r[1]).map(([k, v, cls]) => (
                <div key={k} className="flex justify-between gap-3">
                  <span className="text-slate-400">{k}</span>
                  <span className={cls}>{v}</span>
                </div>
              ))}
            </div>
            {selNode.risk != null && (
              <div className="mt-2 pt-2 border-t border-white/10">
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full rounded-full" style={{
                    width: `${selNode.risk}%`,
                    background: selNode.risk >= 75 ? "#ef4444" : selNode.risk >= 50 ? "#f59e0b" : "#10b981"
                  }} />
                </div>
                <p className="text-slate-500 text-[10px] mt-1">Risk exposure</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend bar */}
      <div className="border-t border-white/10 px-4 py-2.5 flex-shrink-0">
        <div className="flex items-center gap-4 flex-wrap text-xs">
          {[
            { color: "#3b82f6", label: "Contract" },
            { color: "#8b5cf6", label: "Clause" },
            { color: "#ef4444", label: "Risk" },
            { color: "#06b6d4", label: "Party" },
            { color: "#10b981", label: "Obligation" },
            { color: "#6366f1", label: "Status" },
          ].map(s => (
            <div key={s.label} className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full" style={{ background: s.color }} />
              <span className="text-slate-400">{s.label}</span>
            </div>
          ))}
          <div className="ml-auto text-slate-500 text-[10px]">{stats.contracts} contracts · {stats.nodes} nodes · {stats.links} edges</div>
        </div>
      </div>
    </div>
  );
}
