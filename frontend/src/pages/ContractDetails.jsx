import { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft, FileText, Shield, History, GitCompare, Sparkles,
  Upload, X, AlertTriangle, CheckSquare, Zap, Edit3, Activity,
  FileEdit, MessageCircle, TrendingUp, Network, FlaskConical, Send, BookOpen, Target
} from "lucide-react";
import api from "../utils/api";
import useThemeStore from "../store/themeStore";
import VersionHistory from "../components/VersionHistory";
import ComplianceDetails from "../components/ComplianceDetails";
import IntentDriftTimeline from "../components/IntentDriftTimeline";
import IntentDriftComparison from "../components/IntentDriftComparison";
import NegotiationPanel from "../components/NegotiationPanel";
import ApprovalTimeline from "../components/ApprovalTimeline";
import AgentPanel from "../components/AgentPanel";
import PortfolioRiskIntelligence from "../components/PortfolioRiskIntelligence";

/* ─── SUB-COMPONENTS (defined outside to avoid re-creation) ─── */

const ActionButton = ({ label, icon: Icon, color, glow, isHovered, onMouseEnter, onMouseLeave, onClick }) => (
  <button
    onMouseEnter={onMouseEnter}
    onMouseLeave={onMouseLeave}
    onClick={onClick}
    className="ai-action-btn relative flex items-center gap-2.5 px-4 py-2.5 rounded-lg overflow-hidden"
    style={{
      background: isHovered ? `linear-gradient(135deg, ${color}28, ${color}18)` : `${color}10`,
      border: `1px solid ${isHovered ? color + '55' : color + '22'}`,
      boxShadow: isHovered ? `0 0 22px ${glow}, 0 4px 14px rgba(0,0,0,0.35)` : '0 2px 8px rgba(0,0,0,0.25)',
      transform: isHovered ? 'translateY(-1px)' : 'translateY(0)',
      transition: 'all 0.35s cubic-bezier(0.22, 1, 0.36, 1)',
      cursor: 'pointer',
    }}
  >
    {/* internal radial glow on hover */}
    <div style={{
      position: 'absolute', inset: 0, borderRadius: '8px',
      background: `radial-gradient(ellipse at center, ${color}18 0%, transparent 70%)`,
      opacity: isHovered ? 1 : 0,
      transition: 'opacity 0.4s',
      pointerEvents: 'none',
    }} />
    <Icon size={15} className="relative" style={{ color, filter: isHovered ? `drop-shadow(0 0 5px ${color}80)` : 'none', transition: 'filter 0.3s' }} />
    <span className="relative text-xs font-bold tracking-wide" style={{ color: isHovered ? '#fff' : 'rgba(255,255,255,0.78)' }}>
      {label}
    </span>
  </button>
);

const AIModule = ({ title, icon: Icon, iconColor, badges, staggerIndex, isHovered, onMouseEnter, onMouseLeave, mounted, children }) => (
  <div
    onMouseEnter={onMouseEnter}
    onMouseLeave={onMouseLeave}
    className="relative rounded-xl overflow-hidden"
    style={{
      opacity: mounted ? 1 : 0,
      transform: mounted ? 'translateY(0)' : 'translateY(18px)',
      transition: `opacity 0.6s cubic-bezier(0.22,1,0.36,1) ${staggerIndex * 100}ms, transform 0.6s cubic-bezier(0.22,1,0.36,1) ${staggerIndex * 100}ms, background 0.5s, border-color 0.5s, box-shadow 0.5s`,
      background: isHovered
        ? 'linear-gradient(135deg, rgba(15,23,42,0.97) 0%, rgba(30,41,59,0.95) 100%)'
        : 'linear-gradient(135deg, rgba(15,23,42,0.82) 0%, rgba(25,35,55,0.82) 100%)',
      border: `1px solid ${isHovered ? iconColor + '45' : 'rgba(51,65,85,0.35)'}`,
      boxShadow: isHovered
        ? `0 0 40px ${iconColor}12, 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06)`
        : '0 4px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.03)',
    }}
  >
    {/* animated energy border – top edge */}
    <div className="absolute top-0 left-0 right-0 h-px overflow-hidden" style={{ pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute', top: 0, left: '-100%', width: '100%', height: '100%',
        background: `linear-gradient(90deg, transparent 0%, ${iconColor} 50%, transparent 100%)`,
        animation: isHovered ? 'borderSlide 2s linear infinite' : 'none',
        opacity: isHovered ? 0.75 : 0,
        transition: 'opacity 0.5s',
      }} />
    </div>
    {/* subtle beneath-glow when hovered */}
    {isHovered && (
      <div className="absolute inset-0 pointer-events-none" style={{
        background: `radial-gradient(ellipse at 50% 0%, ${iconColor}09 0%, transparent 65%)`,
      }} />
    )}

    <div className="relative p-5">
      {/* module header row */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{
          background: `${iconColor}14`,
          border: `1px solid ${iconColor}28`,
          boxShadow: isHovered ? `0 0 18px ${iconColor}22` : 'none',
          transition: 'box-shadow 0.5s',
        }}>
          <Icon size={18} style={{ color: iconColor }} />
        </div>
        <h3 className="text-sm font-bold text-white tracking-wide flex-1">{title}</h3>
        {/* live status pip */}
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#10b981', boxShadow: '0 0 6px rgba(16,185,129,0.6)', animation: 'breathe 2.8s ease-in-out infinite' }} />
          <span className="text-[9px] font-black text-slate-600 tracking-widest uppercase">Active</span>
        </div>
      </div>
      {/* buttons slot */}
      {children}
      {/* capability badges */}
      {badges && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-4">
          {badges.map((b, i) => (
            <span key={i} className="text-[11px] font-semibold tracking-wide" style={{ color: 'rgba(148,163,184,0.6)' }}>
              <span style={{ color: iconColor, opacity: 0.55 }}>✓</span> {b}
            </span>
          ))}
        </div>
      )}
    </div>
  </div>
);

/* ─── PARTICLE DATA (fixed positions for deterministic layout) ─── */
const PARTICLES = [
  { x: 6,  y: 12, s: 2,   c: 'rgba(6,182,212,0.35)',  d: 0 },
  { x: 22, y: 38, s: 1.5, c: 'rgba(139,92,246,0.28)', d: 1.4 },
  { x: 44, y: 6,  s: 2.5, c: 'rgba(6,182,212,0.22)',  d: 0.6 },
  { x: 63, y: 52, s: 1.5, c: 'rgba(59,130,246,0.3)',  d: 2.1 },
  { x: 80, y: 22, s: 2,   c: 'rgba(139,92,246,0.24)', d: 0.9 },
  { x: 14, y: 68, s: 1.5, c: 'rgba(6,182,212,0.28)',  d: 1.7 },
  { x: 53, y: 76, s: 2,   c: 'rgba(59,130,246,0.22)', d: 2.6 },
  { x: 88, y: 58, s: 1.5, c: 'rgba(6,182,212,0.32)',  d: 0.35 },
  { x: 34, y: 86, s: 2,   c: 'rgba(139,92,246,0.26)', d: 1.9 },
  { x: 71, y: 9,  s: 1.5, c: 'rgba(59,130,246,0.3)',  d: 3.1 },
  { x: 4,  y: 46, s: 2,   c: 'rgba(6,182,212,0.22)',  d: 0.75 },
  { x: 47, y: 63, s: 1.5, c: 'rgba(139,92,246,0.3)',  d: 2.3 },
];

/* ─── MAIN COMPONENT ─── */
const ContractDetails = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  useThemeStore(); // keep store subscribed for sub-components

  const initialTab = searchParams.get("tab") || "overview";

  /* state */
  const [contract, setContract]             = useState(null);
  const [loadingContract, setLoadingContract] = useState(true);
  const [activeTab, setActiveTab]           = useState(initialTab);
  const [mounted, setMounted]               = useState(false);
  const [scorePulsed, setScorePulsed]       = useState(false);
  const [hoveredModule, setHoveredModule]   = useState(null);
  const [hoveredBtn, setHoveredBtn]         = useState(null);

  const [question, setQuestion]             = useState("");
  const [answer, setAnswer]                 = useState("");
  const [loadingAnswer, setLoadingAnswer]   = useState(false);

  const [versions, setVersions]             = useState([]);
  const [selectedVersion1, setSelectedVersion1] = useState(null);
  const [selectedVersion2, setSelectedVersion2] = useState(null);

  const [showUploadModal, setShowUploadModal]   = useState(false);
  const [uploadFile, setUploadFile]             = useState(null);
  const [uploadDescription, setUploadDescription] = useState("");
  const [uploading, setUploading]               = useState(false);
  const [uploadError, setUploadError]           = useState("");
  const [uploadSuccess, setUploadSuccess]       = useState("");
  const [versionRefreshKey, setVersionRefreshKey] = useState(0);

  /* mount + score pulse */
  useEffect(() => {
    setMounted(true);
    const t1 = setTimeout(() => setScorePulsed(true), 650);
    const t2 = setTimeout(() => setScorePulsed(false), 2300);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  /* load contract */
  useEffect(() => {
    if (!contractId || contractId === 'list') { navigate('/contracts/list', { replace: true }); return; }
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(contractId)) { navigate('/contracts/list', { replace: true }); return; }

    let cancelled = false;
    const load = async () => {
      try {
        const res = await api.get(`/contracts/${contractId}`);
        if (!cancelled && res.data?.contract) setContract(res.data.contract);
      } catch (err) {
        if (!cancelled && err.response?.status === 404) setTimeout(() => navigate('/contracts/list'), 2000);
      }
      if (!cancelled) setLoadingContract(false);
    };
    load();
    return () => { cancelled = true; };
  }, [contractId, navigate]);

  /* load versions for drift tab */
  useEffect(() => {
    if (activeTab !== "drift") return;
    let cancelled = false;
    const load = async () => {
      try {
        const res  = await api.get(`/contracts/${contractId}/versions`);
        const list = res.data.versions || [];
        if (cancelled) return;
        setVersions(list);
        if (list.length >= 2) {
          setSelectedVersion1(list[list.length - 2].id);
          setSelectedVersion2(list[list.length - 1].id);
        }
      } catch {}
    };
    load();
    return () => { cancelled = true; };
  }, [contractId, activeTab]);

  /* ask a question */
  const askQuestion = async () => {
    if (!question.trim()) return;
    setLoadingAnswer(true);
    setAnswer("");
    try {
      const res = await api.post("/rag/qa", { query: question, contractId });
      setAnswer(res.data.answer || "No answer returned.");
    } catch { setAnswer("Error: Unable to process your question."); }
    setLoadingAnswer(false);
  };

  /* upload new version */
  const handleUploadVersion = async () => {
    if (!uploadFile) { setUploadError("Please select a file"); return; }
    setUploading(true); setUploadError(""); setUploadSuccess("");
    try {
      const fd = new FormData();
      fd.append("file", uploadFile);
      fd.append("changeDescription", uploadDescription || "Version update");
      const res = await api.post(`/contracts/${contractId}/versions/upload`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadSuccess(`Version ${res.data.version.versionNumber} uploaded. Drift analysis initiated.`);
      setVersionRefreshKey(k => k + 1);
      setUploadFile(null); setUploadDescription("");
      setTimeout(() => { setShowUploadModal(false); setUploadSuccess(""); }, 2000);
    } catch (e) { setUploadError(e.response?.data?.message || "Failed to upload version"); }
    setUploading(false);
  };

  /* version selection from timeline */
  const handleVersionSelect = (from, to) => {
    const v1 = versions.find(v => v.version_number === from);
    const v2 = versions.find(v => v.version_number === to);
    if (v1 && v2) {
      setSelectedVersion1(v1.id);
      setSelectedVersion2(v2.id);
      setTimeout(() => document.getElementById("drift-comparison")?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  /* ─── risk derivation ─── */
  const getRisk = () => {
    const fn = (contract?.original_filename || "").toLowerCase();
    if (fn.includes('high_risk') || fn.includes('high-risk'))
      return { level: 'HIGH',     color: '#ef4444', glow: 'rgba(239,68,68,0.55)',   bg: 'rgba(239,68,68,0.1)' };
    if (fn.includes('medium') || fn.includes('moderate'))
      return { level: 'MODERATE', color: '#f59e0b', glow: 'rgba(245,158,11,0.5)',   bg: 'rgba(245,158,11,0.1)' };
    return   { level: 'ANALYZING', color: '#06b6d4', glow: 'rgba(6,182,212,0.5)',   bg: 'rgba(6,182,212,0.1)' };
  };

  /* ─── LOADING ─── */
  if (loadingContract) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#020a1a' }}>
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-5 rounded-xl border border-cyan-500/35 flex items-center justify-center"
            style={{ boxShadow: '0 0 30px rgba(6,182,212,0.25)', background: 'rgba(15,23,42,0.9)' }}>
            <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full" style={{ animation: 'spin 0.8s linear infinite' }} />
          </div>
          <p className="text-cyan-400 text-xs font-black tracking-widest uppercase">Initializing Contract Context</p>
          <p className="text-slate-600 text-xs mt-1 font-semibold">Loading AI modules…</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  /* ─── NOT FOUND ─── */
  if (!contract) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#020a1a' }}>
        <div className="text-center p-8 rounded-2xl border border-red-500/25 max-w-md w-full mx-4"
          style={{ background: 'rgba(15,23,42,0.96)', boxShadow: '0 0 50px rgba(239,68,68,0.12)' }}>
          <AlertTriangle className="w-14 h-14 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Contract Context Lost</h2>
          <p className="text-slate-400 text-sm mb-4">The requested contract could not be located in the system.</p>
          <p className="text-xs text-slate-600 mb-6">ID: <code className="text-slate-500">{contractId}</code></p>
          <button onClick={() => navigate('/contracts/list')}
            className="px-6 py-2.5 rounded-xl text-white text-sm font-bold tracking-wide"
            style={{ background: 'linear-gradient(135deg,#2563eb,#1d4ed8)', boxShadow: '0 0 22px rgba(37,99,235,0.4)', cursor: 'pointer' }}>
            Return to Contract List
          </button>
        </div>
      </div>
    );
  }

  /* ─── DERIVED DATA ─── */
  const risk = getRisk();

  const TABS = [
    { id: "overview",         label: "Overview",        icon: FileText },
    { id: "portfolio-risk",   label: "Portfolio Risk",  icon: TrendingUp },
    { id: "agent",            label: "Agentic AI",      icon: Zap },
    { id: "compliance",       label: "Compliance",      icon: Shield },
    { id: "versions",         label: "Version History", icon: History },
    { id: "drift",            label: "Intent Drift",    icon: GitCompare },
    { id: "negotiation",      label: "Negotiation",     icon: Sparkles },
    { id: "approvals",        label: "Approvals",       icon: CheckSquare },
  ];

  const CORE_ACTIONS = [
    { id: 'extract',   label: 'Extract / View Clauses',      icon: FileText,      route: `/contract/${contractId}/clauses`,            color: '#3b82f6', glow: 'rgba(59,130,246,0.45)' },
    { id: 'obligations', label: 'Extract Obligations',       icon: CheckSquare,   route: `/contracts/${contractId}/obligations`,       color: '#10b981', glow: 'rgba(16,185,129,0.45)' },
    { id: 'risk',      label: 'Risk Analysis',               icon: AlertTriangle, route: `/risk-analysis?contract=${contractId}`,     color: '#f59e0b', glow: 'rgba(245,158,11,0.45)' },
    { id: 'redline',   label: 'Redline Risky Clauses',       icon: AlertTriangle, route: `/contracts/${contractId}/redlining`,       color: '#ef4444', glow: 'rgba(239,68,68,0.45)' },
    { id: 'ai-redline',label: 'AI Redline Editor',           icon: Edit3,         route: `/contracts/${contractId}/redline-editor`,  color: '#8b5cf6', glow: 'rgba(139,92,246,0.45)' },
  ];

  const GRAPH_ACTIONS = [
    { id: 'graph',  label: 'Graph Intelligence Dashboard',         icon: Network,     route: `/contracts/${contractId}/graph-dashboard`,    color: '#10b981', glow: 'rgba(16,185,129,0.45)' },
    { id: 'whatif', label: 'What-If Analysis & Risk Simulation',   icon: FlaskConical,route: `/contracts/${contractId}/what-if`,           color: '#6366f1', glow: 'rgba(99,102,241,0.45)' },
    { id: 'advwhatif', label: 'Decision Intelligence',             icon: Sparkles,    route: `/contracts/${contractId}/advanced-what-if`, color: '#a855f7', glow: 'rgba(168,85,247,0.45)' },
    { id: 'intent', label: 'Intent Mapping & Heatmap',             icon: Target,      route: `/contracts/${contractId}/intent-heatmap`,   color: '#ec4899', glow: 'rgba(236,72,153,0.45)' },
  ];

  const EMBED_ACTIONS = [
    { id: 'emb-risk',    label: 'Embedding Risk Analysis',      icon: Shield,         route: `/contracts/${contractId}/embedding-risk`,   color: '#3b82f6', glow: 'rgba(59,130,246,0.45)' },
    { id: 'emb-redline', label: 'Smart Redline',                icon: FileEdit,       route: `/contracts/${contractId}/embedding-redline`,color: '#8b5cf6', glow: 'rgba(139,92,246,0.45)' },
    { id: 'emb-chat',    label: 'Ask Questions (Semantic)',     icon: MessageCircle,  route: `/contracts/${contractId}/embedding-chat`,  color: '#06b6d4', glow: 'rgba(6,182,212,0.45)' },
    { id: 'emb-heatmap', label: 'Risk Heatmap & Deviation',    icon: TrendingUp,     route: `/contracts/${contractId}/risk-heatmap`,    color: '#f97316', glow: 'rgba(249,115,22,0.45)' },
    { id: 'playbook',    label: 'Playbook Automation',         icon: BookOpen,       route: `/contracts/${contractId}/playbook`,        color: '#10b981', glow: 'rgba(16,185,129,0.45)' },
  ];

  /* helper – render a row of ActionButtons */
  const renderActions = (actions) => (
    <div className="flex flex-wrap gap-2">
      {actions.map(a => (
        <ActionButton
          key={a.id}
          {...a}
          isHovered={hoveredBtn === a.id}
          onMouseEnter={() => setHoveredBtn(a.id)}
          onMouseLeave={() => setHoveredBtn(null)}
          onClick={() => navigate(a.route)}
        />
      ))}
    </div>
  );

  /* ─── RENDER ─── */
  return (
    <div className="relative min-h-full" style={{ background: '#020a1a' }}>

      {/* ════════════════════════════════════════════════
          AMBIENT / BACKGROUND LAYER
          ════════════════════════════════════════════════ */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* neural grid */}
        <div className="absolute inset-0" style={{
          opacity: 0.055,
          backgroundImage: 'linear-gradient(to right, #06b6d4 1px, transparent 1px), linear-gradient(to bottom, #06b6d4 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }} />
        {/* deep radial colour fields */}
        <div className="absolute top-0 right-0" style={{ width: '440px', height: '440px', opacity: 0.07, background: 'radial-gradient(circle, #8b5cf6 0%, transparent 70%)', filter: 'blur(70px)' }} />
        <div className="absolute bottom-0 left-0" style={{ width: '360px', height: '360px', opacity: 0.055, background: 'radial-gradient(circle, #3b82f6 0%, transparent 70%)', filter: 'blur(65px)' }} />
        <div className="absolute top-1/2 left-1/2" style={{ width: '500px', height: '300px', transform: 'translate(-50%,-50%)', opacity: 0.035, background: 'radial-gradient(ellipse, #06b6d4 0%, transparent 70%)', filter: 'blur(80px)', animation: 'breathe 7s ease-in-out infinite' }} />
        {/* vertical scan line */}
        <div className="absolute left-0 right-0 h-px" style={{
          background: 'linear-gradient(90deg, transparent 0%, rgba(6,182,212,0.25) 50%, transparent 100%)',
          animation: 'scanLine 12s linear infinite',
        }} />
        {/* particle dots */}
        {PARTICLES.map((p, i) => (
          <div key={i} className="absolute rounded-full" style={{
            width: p.s, height: p.s,
            background: p.c,
            left: `${p.x}%`, top: `${p.y}%`,
            animation: `particleDrift ${9 + i * 1.1}s ease-in-out infinite`,
            animationDelay: `${p.d}s`,
          }} />
        ))}
      </div>

      {/* ════════════════════════════════════════════════
          SCROLLABLE CONTENT
          ════════════════════════════════════════════════ */}
      <div className="relative p-6 pb-10">

        {/* ── exit context button ── */}
        <button
          onClick={() => navigate(-1)}
          className="ai-action-btn group flex items-center gap-2 mb-5"
          style={{ opacity: mounted ? 1 : 0, transition: 'opacity 0.5s ease-out', cursor: 'pointer' }}
        >
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{
            background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.18)',
            transition: 'all 0.35s cubic-bezier(0.22,1,0.36,1)',
          }}>
            <ArrowLeft size={15} style={{ color: '#64748b' }} />
            <span className="text-[10px] font-black tracking-widest uppercase" style={{ color: '#64748b' }}>
              Exit Contract Context
            </span>
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#ef4444', boxShadow: '0 0 6px rgba(239,68,68,0.55)', animation: 'breathe 2.2s ease-in-out infinite' }} />
          </div>
        </button>

        {/* ── system context banner ── */}
        <div className="relative rounded-xl mb-5 overflow-hidden" style={{
          opacity: mounted ? 1 : 0,
          transform: mounted ? 'translateY(0)' : 'translateY(-10px)',
          transition: 'opacity 0.7s cubic-bezier(0.22,1,0.36,1), transform 0.7s cubic-bezier(0.22,1,0.36,1)',
          background: 'linear-gradient(135deg, rgba(15,23,42,0.96) 0%, rgba(28,38,60,0.94) 55%, rgba(15,23,42,0.96) 100%)',
          border: '1px solid rgba(6,182,212,0.2)',
          boxShadow: '0 0 55px rgba(6,182,212,0.07), 0 8px 36px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.05)',
        }}>
          {/* top-edge scan */}
          <div className="absolute top-0 left-0 right-0 h-px overflow-hidden" style={{ pointerEvents: 'none' }}>
            <div style={{
              position: 'absolute', top: 0, left: '-100%', width: '100%', height: '100%',
              background: 'linear-gradient(90deg, transparent 0%, rgba(6,182,212,0.55) 50%, transparent 100%)',
              animation: 'borderSlide 3s linear infinite',
            }} />
          </div>

          <div className="relative p-5">
            {/* identity + risk posture */}
            <div className="flex items-start justify-between flex-wrap gap-3">
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0" style={{
                  background: 'linear-gradient(135deg, rgba(6,182,212,0.18), rgba(59,130,246,0.12))',
                  border: '1px solid rgba(6,182,212,0.32)',
                  boxShadow: '0 0 18px rgba(6,182,212,0.14)',
                }}>
                  <FileText size={21} style={{ color: '#06b6d4' }} />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white" style={{ letterSpacing: '0.015em' }}>
                    {contract.original_filename}
                  </h2>
                  <p className="text-[9px] text-slate-600 font-black tracking-widest uppercase mt-0.5">Contract Identity</p>
                </div>
              </div>

              {/* risk posture badge – pulses once on load */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{
                background: risk.bg,
                border: `1px solid ${risk.color}38`,
                boxShadow: scorePulsed ? `0 0 26px ${risk.glow}` : `0 0 8px ${risk.color}30`,
                transition: 'box-shadow 0.9s cubic-bezier(0.22,1,0.36,1)',
              }}>
                <div className="w-2 h-2 rounded-full" style={{ background: risk.color, boxShadow: `0 0 8px ${risk.glow}`, animation: 'breathe 2.4s ease-in-out infinite' }} />
                <span className="text-[10px] font-black tracking-widest" style={{ color: risk.color }}>
                  RISK: {risk.level}
                </span>
              </div>
            </div>

            {/* metadata – sequential fade */}
            <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 pt-4" style={{ borderTop: '1px solid rgba(51,65,85,0.28)' }}>
              {[
                { label: 'TYPE',      value: contract.contract_type     || '—' },
                { label: 'VALUE',     value: contract.contract_value    || '—' },
                { label: 'PARTY',     value: contract.party_name        || '—' },
                { label: 'DURATION',  value: contract.contract_duration || '—' },
                { label: 'UPLOADED',  value: new Date(contract.uploaded_at).toLocaleDateString() },
              ].map((m, i) => (
                <div key={i} style={{ opacity: mounted ? 1 : 0, transition: `opacity 0.5s ease-out ${320 + i * 110}ms` }}>
                  <p className="text-[9px] text-slate-600 font-black tracking-widest uppercase">{m.label}</p>
                  <p className="text-sm text-slate-300 font-semibold mt-0.5">{m.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* AI-readiness status strip */}
          <div className="flex items-center gap-5 px-5 py-2" style={{ background: 'rgba(0,0,0,0.22)', borderTop: '1px solid rgba(51,65,85,0.18)' }}>
            {[
              { text: 'AI Models Loaded',   color: '#10b981', delay: 500 },
              { text: 'Risk Engine Active', color: '#3b82f6', delay: 650 },
              { text: 'Simulation Ready',   color: '#8b5cf6', delay: 800 },
            ].map((s, i) => (
              <div key={i} className="flex items-center gap-1.5" style={{ opacity: mounted ? 1 : 0, transition: `opacity 0.45s ease-out ${s.delay}ms` }}>
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: s.color, boxShadow: `0 0 6px ${s.color}70`, animation: `breathe 3.2s ease-in-out infinite`, animationDelay: `${i * 0.8}s` }} />
                <span className="text-[10px] font-semibold tracking-wide" style={{ color: 'rgba(148,163,184,0.55)' }}>{s.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── AI mode tab bar ── */}
        <div className="flex gap-1 mb-5 flex-wrap" style={{ opacity: mounted ? 1 : 0, transition: 'opacity 0.5s ease-out 220ms' }}>
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className="relative flex items-center gap-2 px-4 py-2.5 rounded-lg overflow-hidden"
                style={{
                  background: active ? 'linear-gradient(135deg, rgba(6,182,212,0.14), rgba(59,130,246,0.09))' : 'rgba(15,23,42,0.55)',
                  border: `1px solid ${active ? 'rgba(6,182,212,0.38)' : 'rgba(51,65,85,0.22)'}`,
                  boxShadow: active ? '0 0 18px rgba(6,182,212,0.14), inset 0 1px 0 rgba(255,255,255,0.07)' : 'none',
                  transition: 'all 0.4s cubic-bezier(0.22,1,0.36,1)',
                  cursor: 'pointer',
                }}
              >
                {/* active bottom energy line */}
                {active && (
                  <div className="absolute bottom-0 left-0 right-0 h-px overflow-hidden">
                    <div style={{
                      position: 'absolute', bottom: 0, left: '-100%', width: '100%', height: '100%',
                      background: 'linear-gradient(90deg, transparent 0%, #06b6d4 50%, transparent 100%)',
                      animation: 'borderSlide 2.2s linear infinite',
                    }} />
                  </div>
                )}
                <Icon size={15} style={{ color: active ? '#06b6d4' : '#475569', filter: active ? 'drop-shadow(0 0 5px rgba(6,182,212,0.5))' : 'none' }} />
                <span className="text-[11px] font-bold tracking-wide" style={{ color: active ? '#e0f2fe' : '#64748b' }}>
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* ════════════════════════════════════════════════
            TAB CONTENT
            ════════════════════════════════════════════════ */}

        {/* ── OVERVIEW ── */}
        {activeTab === "overview" && (
          <div className="space-y-4">
            {/* core action strip */}
            <div style={{ opacity: mounted ? 1 : 0, transition: 'opacity 0.5s ease-out 320ms' }}>
              {renderActions(CORE_ACTIONS)}
            </div>

            {/* graph intelligence module */}
            <AIModule
              id="graph"
              title="Graph Intelligence & Decision Simulation"
              icon={Network}
              iconColor="#10b981"
              staggerIndex={2}
              badges={['NetworkX + Neo4j', 'Risk Propagation', 'Monte Carlo Simulation', 'Financial Exposure (₹/$)', 'CFO-Ready']}
              isHovered={hoveredModule === 'graph'}
              onMouseEnter={() => setHoveredModule('graph')}
              onMouseLeave={() => setHoveredModule(null)}
              mounted={mounted}
            >
              {renderActions(GRAPH_ACTIONS)}
            </AIModule>

            {/* embedding-based AI module */}
            <AIModule
              id="embedding"
              title="Embedding-Based AI — Deterministic · Zero Hallucinations"
              icon={Activity}
              iconColor="#3b82f6"
              staggerIndex={3}
              badges={['Court-safe', 'Explainable', '10× faster', '$0 cost', 'Detects missing safeguards']}
              isHovered={hoveredModule === 'embedding'}
              onMouseEnter={() => setHoveredModule('embedding')}
              onMouseLeave={() => setHoveredModule(null)}
              mounted={mounted}
            >
              {renderActions(EMBED_ACTIONS)}
            </AIModule>

            {/* AI query terminal */}
            <div className="relative rounded-xl overflow-hidden" style={{
              opacity: mounted ? 1 : 0,
              transform: mounted ? 'translateY(0)' : 'translateY(18px)',
              transition: 'opacity 0.6s cubic-bezier(0.22,1,0.36,1) 420ms, transform 0.6s cubic-bezier(0.22,1,0.36,1) 420ms',
              background: 'linear-gradient(135deg, rgba(15,23,42,0.95) 0%, rgba(20,30,50,0.95) 100%)',
              border: '1px solid rgba(51,65,85,0.35)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.32)',
            }}>
              <div className="p-5">
                {/* terminal chrome bar */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full" style={{ background: '#ef4444' }} />
                    <div className="w-3 h-3 rounded-full" style={{ background: '#f59e0b' }} />
                    <div className="w-3 h-3 rounded-full" style={{ background: '#10b981' }} />
                  </div>
                  <span className="text-[9px] font-black text-slate-600 tracking-widest uppercase ml-2">AI Query Terminal</span>
                  <div className="ml-auto flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#10b981', boxShadow: '0 0 6px rgba(16,185,129,0.6)', animation: 'breathe 2.8s ease-in-out infinite' }} />
                    <span className="text-[9px] text-slate-600 font-black tracking-widest uppercase">Standing By</span>
                  </div>
                </div>

                {/* input */}
                <div className="relative">
                  <textarea
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); askQuestion(); } }}
                    placeholder="Query the contract intelligence… e.g. What are the payment terms?"
                    rows={3}
                    className="w-full resize-none focus:outline-none"
                    style={{
                      background: 'rgba(6,182,212,0.035)',
                      border: '1px solid rgba(6,182,212,0.2)',
                      borderRadius: '10px',
                      padding: '14px 50px 14px 16px',
                      color: '#e2e8f0',
                      fontSize: '13px',
                      lineHeight: '1.6',
                      fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
                    }}
                  />
                  {/* send trigger */}
                  <button
                    onClick={askQuestion}
                    disabled={!question.trim() || loadingAnswer}
                    className="absolute right-3 bottom-3 w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{
                      background: question.trim() && !loadingAnswer ? 'linear-gradient(135deg,#10b981,#059669)' : 'rgba(51,65,85,0.35)',
                      boxShadow: question.trim() && !loadingAnswer ? '0 0 18px rgba(16,185,129,0.4)' : 'none',
                      cursor: question.trim() && !loadingAnswer ? 'pointer' : 'not-allowed',
                      transition: 'all 0.3s',
                    }}
                  >
                    <Send size={14} style={{ color: question.trim() && !loadingAnswer ? '#fff' : '#475569' }} />
                  </button>
                </div>
                <p className="text-[10px] text-slate-600 mt-2 font-mono tracking-wide">Press Enter to query · Shift+Enter for new line</p>

                {/* processing state */}
                {loadingAnswer && (
                  <div className="flex items-center gap-2.5 mt-4 px-4 py-3 rounded-lg" style={{ background: 'rgba(6,182,212,0.055)', border: '1px solid rgba(6,182,212,0.18)' }}>
                    <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full" style={{ animation: 'spin 0.65s linear infinite' }} />
                    <span className="text-[11px] text-cyan-400 font-semibold tracking-wide">AI processing query…</span>
                  </div>
                )}

                {/* response panel */}
                {answer && (
                  <div className="mt-4 rounded-lg overflow-hidden" style={{ border: '1px solid rgba(6,182,212,0.2)', background: 'rgba(6,182,212,0.04)' }}>
                    <div className="px-4 py-2 flex items-center gap-2" style={{ background: 'rgba(6,182,212,0.07)', borderBottom: '1px solid rgba(6,182,212,0.15)' }}>
                      <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#06b6d4', boxShadow: '0 0 6px rgba(6,182,212,0.6)' }} />
                      <span className="text-[9px] font-black text-cyan-400 tracking-widest uppercase">AI Response</span>
                    </div>
                    <div className="p-4">
                      <p className="text-slate-300 whitespace-pre-wrap" style={{ fontFamily: "'SF Mono','Fira Code','Consolas',monospace", fontSize: '12px', lineHeight: '1.85' }}>
                        {answer}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── PORTFOLIO RISK ── */}
        {activeTab === "portfolio-risk" && (
          <PortfolioRiskIntelligence contractId={contractId} />
        )}

        {/* ── AGENTIC AI ── */}
        {activeTab === "agent" && (
          <AgentPanel contractId={contractId} />
        )}

        {/* ── COMPLIANCE ── */}
        {activeTab === "compliance" && (
          <ComplianceDetails contractId={contractId} />
        )}

        {/* ── VERSION HISTORY ── */}
        {activeTab === "versions" && (
          <div className="rounded-xl p-5" style={{ border: '1px solid rgba(51,65,85,0.28)', background: 'rgba(15,23,42,0.88)' }}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-white tracking-wide">Version History</h3>
              <button onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg"
                style={{
                  background: 'linear-gradient(135deg, rgba(59,130,246,0.18), rgba(37,99,235,0.12))',
                  border: '1px solid rgba(59,130,246,0.35)',
                  boxShadow: '0 0 14px rgba(59,130,246,0.18)',
                  cursor: 'pointer',
                }}>
                <Upload size={15} style={{ color: '#60a5fa' }} />
                <span className="text-[11px] font-bold text-blue-300 tracking-wide">Upload Version</span>
              </button>
            </div>
            <VersionHistory contractId={contractId} refreshKey={versionRefreshKey} />
          </div>
        )}

        {/* ── INTENT DRIFT ── */}
        {activeTab === "drift" && (
          <div className="space-y-4">
            <div className="rounded-xl p-5" style={{ border: '1px solid rgba(51,65,85,0.28)', background: 'rgba(15,23,42,0.88)' }}>
              <h3 className="text-sm font-bold text-white tracking-wide mb-4">Compare Versions</h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: 'Baseline Version',    val: selectedVersion1, set: setSelectedVersion1 },
                  { label: 'Comparison Version',  val: selectedVersion2, set: setSelectedVersion2 },
                ].map((s, i) => (
                  <div key={i}>
                    <label className="block text-[9px] text-slate-500 font-black tracking-widest uppercase mb-2">{s.label}</label>
                    <select value={s.val || ""} onChange={e => s.set(e.target.value)}
                      className="w-full focus:outline-none"
                      style={{
                        background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.38)',
                        borderRadius: '8px', padding: '8px 12px', color: '#e2e8f0', fontSize: '13px',
                        appearance: 'auto',
                      }}>
                      <option value="" style={{ background: '#0f172a' }}>Select version…</option>
                      {versions.map(v => (
                        <option key={v.id} value={v.id} style={{ background: '#0f172a' }}>
                          v{v.version_number} — {new Date(v.created_at).toLocaleDateString()}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>
            <IntentDriftTimeline contractId={contractId} onVersionSelect={handleVersionSelect} />
            {selectedVersion1 && selectedVersion2 && (
              <div id="drift-comparison">
                <IntentDriftComparison contractId={contractId} version1Id={selectedVersion1} version2Id={selectedVersion2} />
              </div>
            )}
          </div>
        )}

        {/* ── NEGOTIATION ── */}
        {activeTab === "negotiation" && (
          <NegotiationPanel contractId={contractId} />
        )}

        {/* ── APPROVALS ── */}
        {activeTab === "approvals" && (
          <ApprovalTimeline contractId={contractId} onWorkflowInitiated={() => {
            api.get(`/contracts/${contractId}`).then(r => setContract(r.data.contract)).catch(() => {});
          }} />
        )}
      </div>

      {/* ════════════════════════════════════════════════
          AI STATUS WHISPER BAR  (fixed bottom)
          ════════════════════════════════════════════════ */}
      <div className="fixed bottom-0 left-0 right-0 pointer-events-none" style={{ height: '26px', zIndex: 10 }}>
        <div className="h-full flex items-center justify-center gap-6" style={{ background: 'linear-gradient(to top, rgba(2,10,26,0.75), transparent)' }}>
          {[
            { text: 'AI Standing By',   color: '#10b981', delay: 0 },
            { text: 'Risk Model Loaded',color: '#3b82f6', delay: 1 },
            { text: 'Simulation Ready', color: '#8b5cf6', delay: 2 },
          ].map((s, i) => (
            <div key={i} className="flex items-center gap-4">
              {i > 0 && <div className="w-px h-3" style={{ background: 'rgba(100,116,139,0.18)' }} />}
              <div className="flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full" style={{ background: s.color, animation: `breathe 3s ease-in-out infinite`, animationDelay: `${s.delay}s` }} />
                <span className="text-[9px] font-semibold tracking-widest uppercase" style={{ color: 'rgba(100,116,139,0.42)' }}>{s.text}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ════════════════════════════════════════════════
          UPLOAD VERSION MODAL
          ════════════════════════════════════════════════ */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(2,10,26,0.88)', backdropFilter: 'blur(6px)' }}>
          <div className="relative w-full max-w-lg mx-4 rounded-2xl overflow-hidden" style={{
            background: 'linear-gradient(135deg, rgba(15,23,42,0.98), rgba(28,38,60,0.98))',
            border: '1px solid rgba(6,182,212,0.28)',
            boxShadow: '0 0 55px rgba(6,182,212,0.12), 0 24px 64px rgba(0,0,0,0.55)',
          }}>
            {/* modal top-scan */}
            <div className="absolute top-0 left-0 right-0 h-px overflow-hidden" style={{ pointerEvents: 'none' }}>
              <div style={{
                position: 'absolute', top: 0, left: '-100%', width: '100%', height: '100%',
                background: 'linear-gradient(90deg, transparent 0%, rgba(6,182,212,0.5) 50%, transparent 100%)',
                animation: 'borderSlide 2.2s linear infinite',
              }} />
            </div>

            <div className="relative p-6">
              {/* header */}
              <div className="flex justify-between items-center mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(59,130,246,0.14)', border: '1px solid rgba(59,130,246,0.3)' }}>
                    <Upload size={16} style={{ color: '#60a5fa' }} />
                  </div>
                  <h3 className="text-sm font-bold text-white tracking-wide">Upload New Version</h3>
                </div>
                <button onClick={() => { setShowUploadModal(false); setUploadError(""); setUploadSuccess(""); setUploadFile(null); setUploadDescription(""); }}
                  className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-slate-800 transition-colors" style={{ cursor: 'pointer' }}>
                  <X size={18} style={{ color: '#64748b' }} />
                </button>
              </div>

              <div className="space-y-4">
                {/* file input */}
                <div>
                  <label className="block text-[9px] text-slate-500 font-black tracking-widest uppercase mb-2">Select File</label>
                  <input type="file" accept=".pdf,.docx,.png,.jpg,.jpeg"
                    onChange={e => setUploadFile(e.target.files[0])}
                    className="w-full text-sm text-slate-300"
                    style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.38)', borderRadius: '8px', padding: '10px 12px' }}
                  />
                  {uploadFile && <p className="text-[11px] text-slate-500 mt-2">{uploadFile.name} — {(uploadFile.size / 1024 / 1024).toFixed(2)} MB</p>}
                </div>

                {/* description */}
                <div>
                  <label className="block text-[9px] text-slate-500 font-black tracking-widest uppercase mb-2">Change Description</label>
                  <textarea value={uploadDescription} onChange={e => setUploadDescription(e.target.value)}
                    placeholder="Describe what changed…" rows={3}
                    className="w-full resize-none focus:outline-none"
                    style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.38)', borderRadius: '8px', padding: '10px 12px', color: '#e2e8f0', fontSize: '13px' }}
                  />
                </div>

                {/* feedback */}
                {uploadError   && <div className="px-4 py-3 rounded-lg text-sm text-red-300"   style={{ background: 'rgba(239,68,68,0.1)',    border: '1px solid rgba(239,68,68,0.3)'   }}>{uploadError}</div>}
                {uploadSuccess && <div className="px-4 py-3 rounded-lg text-sm text-green-300" style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }}>{uploadSuccess}</div>}

                {/* actions */}
                <div className="flex gap-3 pt-1">
                  <button onClick={handleUploadVersion} disabled={uploading || !uploadFile}
                    className="flex-1 px-4 py-2.5 rounded-lg text-sm font-bold text-white tracking-wide"
                    style={{
                      background: uploading || !uploadFile ? 'rgba(51,65,85,0.4)' : 'linear-gradient(135deg,#2563eb,#1d4ed8)',
                      boxShadow: uploading || !uploadFile ? 'none' : '0 0 20px rgba(37,99,235,0.4)',
                      opacity: uploading || !uploadFile ? 0.5 : 1,
                      cursor: uploading || !uploadFile ? 'not-allowed' : 'pointer',
                    }}>
                    {uploading ? "Uploading…" : "Upload Version"}
                  </button>
                  <button onClick={() => { setShowUploadModal(false); setUploadError(""); setUploadSuccess(""); setUploadFile(null); setUploadDescription(""); }}
                    disabled={uploading}
                    className="px-4 py-2.5 rounded-lg text-sm font-bold text-slate-400"
                    style={{ background: 'rgba(51,65,85,0.3)', border: '1px solid rgba(51,65,85,0.38)', cursor: 'pointer' }}>
                    Cancel
                  </button>
                </div>

                {/* what-happens-next info */}
                <div className="px-4 py-3 rounded-lg" style={{ background: 'rgba(6,182,212,0.055)', border: '1px solid rgba(6,182,212,0.18)' }}>
                  <p className="text-[11px] text-cyan-400 font-bold mb-1.5">What happens next:</p>
                  <ul className="text-[11px] text-slate-500 space-y-1">
                    <li>• New version created (v2, v3…)</li>
                    <li>• Intent drift analysis triggered automatically</li>
                    <li>• Clause extraction & comparison initiated</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          SCOPED KEYFRAMES
          ════════════════════════════════════════════════ */}
      <style>{`
        /* vertical scan across the page */
        @keyframes scanLine {
          0%   { top: -4px; opacity: 0; }
          8%   { opacity: 0.7; }
          92%  { opacity: 0.7; }
          100% { top: 100%; opacity: 0; }
        }
        /* horizontal energy sweep (borders, header) */
        @keyframes borderSlide {
          0%   { left: -100%; }
          100% { left: 100%; }
        }
        /* ambient particle drift */
        @keyframes particleDrift {
          0%,100% { transform: translate(0, 0);         opacity: 0.25; }
          25%     { transform: translate(14px, -10px);   opacity: 0.55; }
          50%     { transform: translate(-8px, 16px);    opacity: 0.35; }
          75%     { transform: translate(11px,  7px);    opacity: 0.5;  }
        }
        /* slow breathing for status pips & glows */
        @keyframes breathe {
          0%,100% { opacity: 0.45; }
          50%     { opacity: 0.95; }
        }
        /* button press compression */
        .ai-action-btn:active {
          transform: scale(0.95) !important;
          transition: transform 0.1s ease !important;
        }
        /* standard spin */
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default ContractDetails;
