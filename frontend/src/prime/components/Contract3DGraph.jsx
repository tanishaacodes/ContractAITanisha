import { useRef, useState, useEffect, useCallback, useMemo } from "react";
import { Maximize2, Minimize2, RotateCcw, Info, X } from "lucide-react";

// â”€â”€ Constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const RISK_COLORS = {
  HIGH:   { node: "#7f1d1d", border: "#ef4444", glow: "#ef4444", text: "#fca5a5" },
  MEDIUM: { node: "#451a03", border: "#f59e0b", glow: "#f59e0b", text: "#fcd34d" },
  LOW:    { node: "#052e16", border: "#10b981", glow: "#10b981", text: "#6ee7b7" },
};

const NODE_COLORS = {
  HUB:     "#8b5cf6",
  CONTRACT:"#3b82f6",
  RISK:    "#ef4444",
  CLAUSE:  "#06b6d4",
  PARTY:   "#a78bfa",
  CLUSTER: "#64748b",
};

const CLAUSE_TYPES = [
  "Liability","Payment","Termination","IP Rights","Indemnity",
  "Penalties","Compliance","Arbitration","Confidentiality","SLA",
  "Force Majeure","Warranty","Governing Law","Dispute Resolution","Limitation"
];

function parseValue(raw) {
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
  if (!v) return "$0";
  if (v >= 1e9) return "$" + (v/1e9).toFixed(1) + "B";
  if (v >= 1e6) return "$" + (v/1e6).toFixed(1) + "M";
  if (v >= 1e3) return "$" + (v/1e3).toFixed(0) + "K";
  return "$" + v.toFixed(0);
}

function rrect(ctx, x, y, w, h, r) {
  if (ctx.roundRect) { ctx.roundRect(x, y, w, h, r); return; }
  ctx.beginPath();
  ctx.moveTo(x+r,y); ctx.lineTo(x+w-r,y);
  ctx.quadraticCurveTo(x+w,y,x+w,y+r); ctx.lineTo(x+w,y+h-r);
  ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h); ctx.lineTo(x+r,y+h);
  ctx.quadraticCurveTo(x,y+h,x,y+h-r); ctx.lineTo(x,y+r);
  ctx.quadraticCurveTo(x,y,x+r,y); ctx.closePath();
}

// â”€â”€ 3D projection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function project3D(x3, y3, z3, rotX, rotY, W, H, fov) {
  // rotate around Y
  const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
  const x1 = x3 * cosY - z3 * sinY;
  const z1 = x3 * sinY + z3 * cosY;
  // rotate around X
  const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
  const y1 = y3 * cosX - z1 * sinX;
  const z2 = y3 * sinX + z1 * cosX;
  // perspective
  const d = fov / (fov + z2 + 400);
  return {
    sx: W/2 + x1 * d,
    sy: H/2 + y1 * d,
    scale: d,
    z: z2,
  };
}

// â”€â”€ Build 3D positions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function buildGraph(contracts, selectedId) {
  const nodes = [], edges = [];
  const display = selectedId && selectedId !== "all"
    ? contracts.filter(c => String(c.id) === String(selectedId))
    : contracts.slice(0, 14);
  if (!display.length) return { nodes, edges };

  const values = display.map(c => parseValue(c.contract_value));
  const maxVal = Math.max(...values, 1);
  const minVal = Math.min(...values.filter(v=>v>0), 0);

  // Hub at center
  nodes.push({ id:"hub", type:"HUB", x3:0, y3:0, z3:0,
    label:"Portfolio Hub", sub: display.length + " contracts",
    color:"#8b5cf6", border:"#a78bfa", glow:"#8b5cf6", size:38 });

  // Risk clusters on sphere surface
  const clusterPos = [
    { id:"rc-high", label:"HIGH RISK",  color:"#ef4444", x3:-200, y3:-120, z3:60  },
    { id:"rc-med",  label:"MED RISK",   color:"#f59e0b", x3:200,  y3:-120, z3:60  },
    { id:"rc-low",  label:"LOW RISK",   color:"#10b981", x3:0,    y3:-200, z3:-60 },
  ];
  clusterPos.forEach(cl => {
    nodes.push({ id:cl.id, type:"CLUSTER", x3:cl.x3, y3:cl.y3, z3:cl.z3,
      label:cl.label, color:cl.color, border:cl.color, glow:cl.color, size:24 });
    edges.push({ src:"hub", tgt:cl.id, color:cl.color+"55", dashed:true });
  });

  // Contracts on a sphere
  const R = 160;
  display.forEach((c, i) => {
    const phi   = Math.acos(1 - 2*(i+0.5)/display.length);
    const theta = Math.PI * (1 + Math.sqrt(5)) * i;
    const val   = parseValue(c.contract_value);
    const norm  = maxVal > minVal ? (val-minVal)/(maxVal-minVal) : 0.5;
    const risk  = c.liability_level || "LOW";
    const rc    = RISK_COLORS[risk] || RISK_COLORS.LOW;
    const cSize = 22 + norm * 14;
    const cId   = String(c.id || "c"+i);

    const cx3 = R * Math.sin(phi) * Math.cos(theta);
    const cy3 = R * Math.cos(phi);
    const cz3 = R * Math.sin(phi) * Math.sin(theta);

    nodes.push({ id:cId, type:"CONTRACT", x3:cx3, y3:cy3, z3:cz3,
      label:(c.original_filename||"Contract "+(i+1)).replace(/\.(pdf|docx?|txt)$/i,"").substring(0,20),
      sub: c.party_name && c.party_name!=="Unknown" ? c.party_name.substring(0,18) : (c.contract_type||""),
      value:val, risk, riskPct: risk==="HIGH"?85:risk==="MEDIUM"?60:28,
      status:c.status, end_date:c.end_date, contract_type:c.contract_type,
      color:rc.node, border:rc.border, glow:rc.glow, size:cSize });
    edges.push({ src:"hub", tgt:cId, color:rc.border+"88", label:risk });

    const clId = risk==="HIGH"?"rc-high":risk==="MEDIUM"?"rc-med":"rc-low";
    edges.push({ src:cId, tgt:clId, color:rc.border+"44", dashed:true });

    // Risk satellite
    const rId = "risk-"+cId;
    const rf = 1.42;
    nodes.push({ id:rId, type:"RISK", x3:cx3*rf, y3:cy3*rf, z3:cz3*rf,
      label:risk+" RISK", color:rc.node, border:rc.border, glow:rc.glow, size:16 });
    edges.push({ src:cId, tgt:rId, color:rc.border+"99", label:"risk" });

    // Clause satellite
    const oId = "clause-"+cId;
    const of2 = 0.62;
    nodes.push({ id:oId, type:"CLAUSE", x3:cx3*of2, y3:cy3*of2+40, z3:cz3*of2,
      label:CLAUSE_TYPES[i%CLAUSE_TYPES.length], color:"#0c2233", border:"#06b6d4", glow:"#06b6d4", size:14 });
    edges.push({ src:cId, tgt:oId, color:"#06b6d499", dashed:true, label:"clause" });

    // Party
    if (c.party_name && c.party_name!=="Unknown") {
      const pId = "party-"+i;
      nodes.push({ id:pId, type:"PARTY", x3:cx3*1.6, y3:cy3*1.6-30, z3:cz3*1.6,
        label:c.party_name.substring(0,16), color:"#12083a", border:"#a78bfa", glow:"#a78bfa", size:14 });
      edges.push({ src:cId, tgt:pId, color:"#a78bfa66", label:"party" });
    }
  });

  // Cross high-risk edges
  const highIds = display.filter(c=>c.liability_level==="HIGH").map(c=>String(c.id));
  for (let i=0;i<highIds.length-1;i++) {
    edges.push({ src:highIds[i], tgt:highIds[i+1], color:"#ef444466", dashed:true, label:"risk link" });
  }

  return { nodes, edges };
}

// â”€â”€ Drawing helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function drawHex(ctx,x,y,r) {
  ctx.beginPath();
  for(let i=0;i<6;i++){const a=Math.PI/3*i-Math.PI/6;i===0?ctx.moveTo(x+r*Math.cos(a),y+r*Math.sin(a)):ctx.lineTo(x+r*Math.cos(a),y+r*Math.sin(a));}
  ctx.closePath();
}
function drawDia(ctx,x,y,r) {
  ctx.beginPath();ctx.moveTo(x,y-r);ctx.lineTo(x+r*0.7,y);ctx.lineTo(x,y+r);ctx.lineTo(x-r*0.7,y);ctx.closePath();
}

function drawNode(ctx, node, proj, selected, hovered, t) {
  const { sx, sy, scale } = proj;
  const r = node.size * scale * (1 + Math.sin(t*2)*(selected||hovered?0.08:0.03));
  const { color, border, glow, type } = node;

  // Glow halo
  if (glow) {
    const gl = ctx.createRadialGradient(sx,sy,0,sx,sy,r*3.2);
    gl.addColorStop(0, glow+(selected?"55":"22"));
    gl.addColorStop(1, glow+"00");
    ctx.beginPath();
    ctx.arc(sx,sy,r*3.2,0,Math.PI*2);
    ctx.fillStyle=gl; ctx.fill();
  }

  ctx.save();
  ctx.shadowBlur = selected?28:hovered?18:10;
  ctx.shadowColor = border||glow||"#fff";

  // Shape
  ctx.beginPath();
  if (type==="HUB") drawHex(ctx,sx,sy,r);
  else if (type==="RISK") drawDia(ctx,sx,sy,r);
  else if (type==="CLAUSE") rrect(ctx,sx-r*0.9,sy-r*0.65,r*1.8,r*1.3,4);
  else if (type==="CLUSTER") drawHex(ctx,sx,sy,r);
  else ctx.arc(sx,sy,r,0,Math.PI*2);

  // 3D sphere shading gradient
  const grad = ctx.createRadialGradient(sx-r*0.3,sy-r*0.3,r*0.05,sx,sy,r*1.2);
  grad.addColorStop(0, lighten(color,0.5));
  grad.addColorStop(0.4, color);
  grad.addColorStop(1, darken(color,0.6));
  ctx.fillStyle=grad; ctx.fill();
  ctx.lineWidth=selected?2.5:1.5;
  ctx.strokeStyle=selected?"#fff":border;
  ctx.stroke();
  ctx.restore();

  if (selected) {
    ctx.beginPath();ctx.arc(sx,sy,r+8*scale,0,Math.PI*2);
    ctx.strokeStyle="#ffffff44";ctx.lineWidth=1.5;
    ctx.setLineDash([4,4]);ctx.stroke();ctx.setLineDash([]);
  }

  // Icon
  const iconSize = Math.max(8,r*0.65);
  ctx.font = iconSize+"px sans-serif";
  ctx.textAlign="center";ctx.textBaseline="middle";
  ctx.fillStyle=(border||"#fff")+"cc";
  const icon = type==="HUB"?"â¬¡":type==="RISK"?"âš ":type==="CLAUSE"?"Â§":type==="PARTY"?"ðŸ‘¤":type==="CLUSTER"?"â—ˆ":"â—";
  ctx.fillText(icon,sx,sy+1);

  // Label
  const fontSize = Math.max(7, Math.min(11, 9*scale));
  ctx.font=(selected?"bold ":"")+fontSize+"px Inter,sans-serif";
  const labelY = sy + r + 16*scale;
  const text = node.label||"";
  const tw = ctx.measureText(text).width+10;
  ctx.fillStyle="rgba(2,6,23,0.88)";
  rrect(ctx,sx-tw/2,labelY-9,tw,18,5);ctx.fill();
  ctx.strokeStyle=(border||"#fff")+"55";ctx.lineWidth=0.8;rrect(ctx,sx-tw/2,labelY-9,tw,18,5);ctx.stroke();
  ctx.fillStyle=selected?"#fff":type==="HUB"?"#c4b5fd":type==="RISK"?"#fca5a5":type==="CLAUSE"?"#67e8f9":type==="PARTY"?"#c4b5fd":"#e2e8f0";
  ctx.fillText(text,sx,labelY);

  // Value badge
  if (type==="CONTRACT"&&node.value>0) {
    const vt = fmtVal(node.value);
    const vw = ctx.measureText(vt).width+8;
    ctx.fillStyle="#052e16cc";rrect(ctx,sx-vw/2,sy-r-22*scale,vw,14,3);ctx.fill();
    ctx.strokeStyle="#10b98166";ctx.lineWidth=0.8;rrect(ctx,sx-vw/2,sy-r-22*scale,vw,14,3);ctx.stroke();
    ctx.font="bold 8px monospace";ctx.fillStyle="#34d399";ctx.fillText(vt,sx,sy-r-15*scale);
  }
}

function lighten(hex,amt) {
  const n=parseInt(hex.slice(1),16);
  const r=Math.min(255,((n>>16)&255)+amt*255|0);
  const g=Math.min(255,((n>>8)&255)+amt*255|0);
  const b=Math.min(255,(n&255)+amt*255|0);
  return "#"+[r,g,b].map(x=>x.toString(16).padStart(2,"0")).join("");
}
function darken(hex,amt) {
  const n=parseInt(hex.slice(1),16);
  const r=Math.max(0,((n>>16)&255)-amt*255|0);
  const g=Math.max(0,((n>>8)&255)-amt*255|0);
  const b=Math.max(0,(n&255)-amt*255|0);
  return "#"+[r,g,b].map(x=>x.toString(16).padStart(2,"0")).join("");
}

function drawEdge(ctx, edge, nodeMap, rotX, rotY, W, H, fov, t) {
  const src = nodeMap[edge.src], tgt = nodeMap[edge.tgt];
  if (!src||!tgt) return;
  const ps = project3D(src.x3,src.y3,src.z3,rotX,rotY,W,H,fov);
  const pt = project3D(tgt.x3,tgt.y3,tgt.z3,rotX,rotY,W,H,fov);
  const avgZ = (ps.z+pt.z)/2;
  const alpha = Math.max(0.15, Math.min(0.85, 0.5 - avgZ/1200));
  const col = edge.color||"#ffffff44";

  ctx.save();
  ctx.strokeStyle = col;
  ctx.lineWidth = edge.dashed?0.8:1.4;
  ctx.globalAlpha = alpha;
  if (edge.dashed) {
    ctx.setLineDash([5,5]);
    ctx.lineDashOffset = -(t*12)%16;
  }
  const mx=(ps.sx+pt.sx)/2, my=(ps.sy+pt.sy)/2-18;
  ctx.beginPath();ctx.moveTo(ps.sx,ps.sy);ctx.quadraticCurveTo(mx,my,pt.sx,pt.sy);ctx.stroke();
  ctx.setLineDash([]);ctx.globalAlpha=1;

  if (edge.label) {
    ctx.font="7px Inter,sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";
    const lw=ctx.measureText(edge.label).width+6;
    ctx.fillStyle="rgba(2,6,23,0.75)";rrect(ctx,mx-lw/2,my-7,lw,13,3);ctx.fill();
    ctx.fillStyle="#94a3b8";ctx.fillText(edge.label,mx,my);
  }

  // Arrow
  const dx=pt.sx-ps.sx,dy=pt.sy-ps.sy,len=Math.sqrt(dx*dx+dy*dy);
  if (len>0) {
    const ux=dx/len,uy=dy/len;
    const ar=(tgt.size||16)*pt.scale+3;
    const ax=pt.sx-ux*ar,ay=pt.sy-uy*ar;
    ctx.beginPath();
    ctx.moveTo(ax-ux*7-uy*3.5,ay-uy*7+ux*3.5);ctx.lineTo(ax,ay);
    ctx.lineTo(ax-ux*7+uy*3.5,ay-uy*7-ux*3.5);
    ctx.strokeStyle=col;ctx.lineWidth=edge.dashed?0.8:1.4;ctx.globalAlpha=alpha;ctx.stroke();
    ctx.globalAlpha=1;
  }
  ctx.restore();
}

// â”€â”€ Main Component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function Contract3DGraph({ selectedContract, contracts=[] }) {
  const canvasRef = useRef(null);
  const animRef   = useRef(null);
  const stateRef  = useRef({ rotX:0.25, rotY:0.3, autoRot:true, drag:null, t:0, zoom:1, panX:0, panY:0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode,  setHoveredNode]  = useState(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [showLegend, setShowLegend] = useState(false);
  const [zoom, setZoom] = useState(1);

  const { nodes, edges, nodeMap, stats } = useMemo(() => {
    const { nodes, edges } = buildGraph(contracts, selectedContract);
    const nodeMap = {};
    nodes.forEach(n => nodeMap[n.id]=n);
    const st = {
      contracts: nodes.filter(n=>n.type==="CONTRACT").length,
      risks:     nodes.filter(n=>n.type==="RISK").length,
      clauses:   nodes.filter(n=>n.type==="CLAUSE").length,
      parties:   nodes.filter(n=>n.type==="PARTY").length,
      highRisk:  nodes.filter(n=>n.type==="CONTRACT"&&n.risk==="HIGH").length,
      edges:     edges.length,
    };
    return { nodes, edges, nodeMap, stats:st };
  }, [contracts, selectedContract]);

  // Hit test in 3D projected space
  const hitTest = useCallback((ex, ey) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const W=canvas.width, H=canvas.height;
    const { rotX, rotY, zoom:z, panX, panY } = stateRef.current;
    const fov = 900*z;
    let best=null, bestD=99999;
    nodes.forEach(n => {
      const p = project3D(n.x3,n.y3,n.z3,rotX,rotY,W,H,fov);
      const r = n.size * p.scale + 12;
      const d = Math.hypot((ex-panX)-p.sx,(ey-panY)-p.sy);
      if (d<r&&d<bestD) { bestD=d; best=n; }
    });
    return best;
  }, [nodes]);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const draw = () => {
      const ctx = canvas.getContext("2d");
      const W=canvas.width, H=canvas.height;
      const { rotX, rotY, autoRot, t, zoom:z, panX, panY } = stateRef.current;
      if (autoRot) stateRef.current.rotY += 0.003;
      stateRef.current.t += 0.016;
      const fov = 900*z;

      ctx.clearRect(0,0,W,H);

      // Starfield background
      ctx.save();
      if (!stateRef.current._stars) {
        stateRef.current._stars = Array.from({length:80},()=>({
          x:Math.random()*2000-1000,y:Math.random()*1200-600,b:Math.random()
        }));
      }
      stateRef.current._stars.forEach(s => {
        const alpha = 0.2+s.b*0.5+Math.sin(t+s.b*10)*0.1;
        ctx.fillStyle="rgba(148,163,184,"+alpha+")";
        ctx.beginPath();ctx.arc(W/2+s.x*0.3+panX,H/2+s.y*0.3+panY,s.b*1.2,0,Math.PI*2);ctx.fill();
      });
      ctx.restore();

      // Grid plane
      ctx.save();ctx.translate(panX,panY);
      const gNodes = nodes.map(n=>({...n,...project3D(n.x3,n.y3,n.z3,rotX,rotY,W,H,fov)}));
      const gNodeMap = {};
      gNodes.forEach(n=>gNodeMap[n.id]=n);

      // Depth-sort: edges behind nodes
      const sortedNodes = [...gNodes].sort((a,b)=>a.z-b.z);

      // Draw edges (depth-sorted midpoint)
      const sortedEdges = [...edges].sort((a,b)=>{
        const za = (nodeMap[a.src]?.z3||0)+(nodeMap[a.tgt]?.z3||0);
        const zb = (nodeMap[b.src]?.z3||0)+(nodeMap[b.tgt]?.z3||0);
        return za-zb;
      });
      sortedEdges.forEach(e => drawEdge(ctx,e,nodeMap,rotX,rotY,W,H,fov,t));

      // Draw nodes back to front
      sortedNodes.forEach(n => {
        const proj = project3D(n.x3,n.y3,n.z3,rotX,rotY,W,H,fov);
        drawNode(ctx,n,proj,selectedNode?.id===n.id,hoveredNode?.id===n.id,t);
      });

      ctx.restore();
      animRef.current = requestAnimationFrame(draw);
    };
    animRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animRef.current);
  }, [nodes, edges, nodeMap, selectedNode, hoveredNode]);

  // Resize
  useEffect(()=>{
    const canvas=canvasRef.current; if(!canvas) return;
    const ro=new ResizeObserver(()=>{ canvas.width=canvas.offsetWidth; canvas.height=canvas.offsetHeight; });
    ro.observe(canvas);
    canvas.width=canvas.offsetWidth; canvas.height=canvas.offsetHeight;
    return ()=>ro.disconnect();
  },[fullscreen]);

  // Pointer events
  const onMouseMove = useCallback((e)=>{
    const rect=canvasRef.current.getBoundingClientRect();
    const ex=e.clientX-rect.left, ey=e.clientY-rect.top;
    const { drag } = stateRef.current;
    if (drag) {
      if (drag.type==="rotate") {
        stateRef.current.rotY += e.movementX*0.008;
        stateRef.current.rotX += e.movementY*0.008;
        stateRef.current.autoRot = false;
      } else if (drag.type==="pan") {
        stateRef.current.panX += e.movementX;
        stateRef.current.panY += e.movementY;
      }
      return;
    }
    const hit=hitTest(ex,ey);
    setHoveredNode(hit);
    canvasRef.current.style.cursor=hit?"pointer":"grab";
  },[hitTest]);

  const onMouseDown = useCallback((e)=>{
    const rect=canvasRef.current.getBoundingClientRect();
    const hit=hitTest(e.clientX-rect.left,e.clientY-rect.top);
    if (e.button===2||e.shiftKey) stateRef.current.drag={type:"pan"};
    else stateRef.current.drag={type:"rotate"};
    stateRef.current._clickHit=hit;
  },[hitTest]);

  const onMouseUp = useCallback((e)=>{
    const { drag, _clickHit } = stateRef.current;
    if (drag?.type==="rotate" && Math.abs(e.movementX)<2 && Math.abs(e.movementY)<2 && _clickHit) {
      setSelectedNode(n=>n?.id===_clickHit.id?null:_clickHit);
    }
    stateRef.current.drag=null;
    stateRef.current._clickHit=null;
  },[]);

  const onWheel = useCallback((e)=>{
    e.preventDefault();
    stateRef.current.zoom=Math.min(3,Math.max(0.4,stateRef.current.zoom*(e.deltaY<0?1.1:0.91)));
    setZoom(stateRef.current.zoom);
  },[]);

  useEffect(()=>{
    const c=canvasRef.current; if(!c) return;
    c.addEventListener("wheel",onWheel,{passive:false});
    return ()=>c.removeEventListener("wheel",onWheel);
  },[onWheel]);

  const resetView=()=>{
    stateRef.current.rotX=0.25; stateRef.current.rotY=0.3;
    stateRef.current.zoom=1; stateRef.current.panX=0; stateRef.current.panY=0;
    stateRef.current.autoRot=true;
    setZoom(1); setSelectedNode(null); setHoveredNode(null);
  };

  return (
    <div className={`rounded-2xl bg-slate-950 shadow-2xl border border-white/10 flex flex-col ${fullscreen?"fixed inset-2 z-50":"h-[650px]"}`}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-1 h-6 bg-gradient-to-b from-cyan-400 to-purple-600 rounded-full" />
          <div>
            <h3 className="text-sm font-bold text-white">Contract Knowledge Graph</h3>
            <p className="text-xs text-slate-500">{stats.contracts} contracts Â· {stats.edges} edges Â· drag to rotate Â· scroll to zoom</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <button onClick={()=>setShowLegend(v=>!v)} className={`p-1.5 rounded-lg transition-colors ${showLegend?"bg-purple-500/30 border border-purple-500/50":"bg-white/10 hover:bg-white/20"}`}>
            <Info className="w-3.5 h-3.5 text-white" />
          </button>
          <button onClick={resetView} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            <RotateCcw className="w-3.5 h-3.5 text-white" />
          </button>
          <button onClick={()=>setFullscreen(v=>!v)} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
            {fullscreen?<Minimize2 className="w-3.5 h-3.5 text-white"/>:<Maximize2 className="w-3.5 h-3.5 text-white"/>}
          </button>
        </div>
      </div>

      <div className="flex-1 relative min-h-0">
        <canvas ref={canvasRef} className="w-full h-full block" style={{cursor:"grab"}}
          onMouseMove={onMouseMove} onMouseDown={onMouseDown} onMouseUp={onMouseUp}
          onMouseLeave={()=>{stateRef.current.drag=null;setHoveredNode(null);}}
          onContextMenu={e=>e.preventDefault()} />

        <div className="absolute bottom-3 right-3 text-[10px] text-slate-500 bg-slate-900/80 px-2 py-1 rounded border border-white/10">
          {Math.round(zoom*100)}%
        </div>
        <div className="absolute bottom-3 left-3 text-[10px] text-slate-500 bg-slate-900/80 px-2 py-1 rounded border border-white/10">
          drag to rotate Â· scroll zoom Â· click node
        </div>

        {showLegend && (
          <div className="absolute top-3 left-3 bg-slate-900/96 backdrop-blur border border-white/10 rounded-xl p-3 text-xs space-y-1.5 z-10 min-w-[210px]">
            <div className="flex items-center justify-between mb-1">
              <p className="text-white font-semibold">Node Types</p>
              <button onClick={()=>setShowLegend(false)} className="text-slate-500 hover:text-white"><X className="w-3 h-3"/></button>
            </div>
            {[
              {color:"#8b5cf6",icon:"â¬¡",label:"Portfolio Hub"},
              {color:"#3b82f6",icon:"â—",label:"Contract (size = value)"},
              {color:"#ef4444",icon:"â—†",label:"Risk Factor (HIGH)"},
              {color:"#f59e0b",icon:"â—†",label:"Risk Factor (MED)"},
              {color:"#10b981",icon:"â—†",label:"Risk Factor (LOW)"},
              {color:"#06b6d4",icon:"â– ",label:"Clause Type"},
              {color:"#a78bfa",icon:"â—",label:"Counterparty"},
              {color:"#64748b",icon:"â¬¡",label:"Risk Cluster"},
            ].map(item=>(
              <div key={item.label} className="flex items-center gap-2">
                <span style={{color:item.color}} className="text-sm leading-none w-4">{item.icon}</span>
                <span className="text-slate-300">{item.label}</span>
              </div>
            ))}
          </div>
        )}

        {selectedNode && (
          <div className="absolute top-3 right-3 bg-slate-900/96 backdrop-blur border border-white/10 rounded-xl p-3 text-xs z-10 min-w-[220px] max-w-[260px]">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-white text-sm">{selectedNode.label}</span>
              <button onClick={()=>setSelectedNode(null)} className="text-slate-500 hover:text-white"><X className="w-3.5 h-3.5"/></button>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between"><span className="text-slate-400">Type</span><span className="text-slate-200 font-medium">{selectedNode.type}</span></div>
              {selectedNode.sub&&<div className="flex justify-between"><span className="text-slate-400">Info</span><span className="text-slate-200">{selectedNode.sub}</span></div>}
              {selectedNode.value>0&&<div className="flex justify-between"><span className="text-slate-400">Value</span><span className="text-green-400 font-mono font-bold">{fmtVal(selectedNode.value)}</span></div>}
              {selectedNode.risk&&<div className="flex justify-between"><span className="text-slate-400">Risk</span><span className={selectedNode.risk==="HIGH"?"font-semibold text-red-400":selectedNode.risk==="MEDIUM"?"font-semibold text-yellow-400":"font-semibold text-green-400"}>{selectedNode.risk}</span></div>}
              {selectedNode.riskPct&&<div className="flex justify-between"><span className="text-slate-400">Exposure</span><span className="text-orange-400 font-mono">{selectedNode.riskPct}%</span></div>}
              {selectedNode.status&&<div className="flex justify-between"><span className="text-slate-400">Status</span><span className="text-purple-400">{selectedNode.status}</span></div>}
              {selectedNode.end_date&&<div className="flex justify-between"><span className="text-slate-400">Expires</span><span className="text-slate-300">{selectedNode.end_date}</span></div>}
              {selectedNode.contract_type&&<div className="flex justify-between"><span className="text-slate-400">Type</span><span className="text-cyan-400">{selectedNode.contract_type}</span></div>}
            </div>
            {selectedNode.riskPct&&(
              <div className="mt-2 pt-2 border-t border-white/10">
                <div className="w-full h-1 rounded-full bg-slate-800 overflow-hidden">
                  <div className="h-full rounded-full" style={{width:selectedNode.riskPct+"%",background:selectedNode.risk==="HIGH"?"#ef4444":selectedNode.risk==="MEDIUM"?"#f59e0b":"#10b981"}}/>
                </div>
                <p className="text-slate-500 text-[10px] mt-1">Risk exposure bar</p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="border-t border-white/10 px-4 py-2.5 flex-shrink-0">
        <div className="flex items-center gap-4 text-xs flex-wrap">
          {[
            {color:"#3b82f6",label:"Contracts",val:stats.contracts},
            {color:"#ef4444",label:"High Risk",val:stats.highRisk},
            {color:"#ef4444",label:"Risk Nodes",val:stats.risks},
            {color:"#06b6d4",label:"Clauses",val:stats.clauses},
            {color:"#a78bfa",label:"Parties",val:stats.parties},
            {color:"#64748b",label:"Edges",val:stats.edges},
          ].map(s=>(
            <div key={s.label} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full flex-shrink-0" style={{background:s.color}}/>
              <span className="text-slate-400">{s.label}:</span>
              <span className="text-white font-semibold">{s.val}</span>
            </div>
          ))}
          <div className="ml-auto text-slate-500 text-[10px]">{Math.round(zoom*100)}% zoom Â· 3D rotatable Â· click node for details</div>
        </div>
      </div>
    </div>
  );
}