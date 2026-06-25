/**
 * ArbitrationDashboard.jsx
 * =========================
 * Enterprise Arbitration Risk Management Dashboard
 * For $100M+ EPC construction contracts.
 *
 * Tabs:
 *  1. Overview        — summary KPIs, risk level badges, dispute probability
 *  2. Clause Analysis — extracted clauses with 8-dim risk vectors
 *  3. Monte Carlo     — correlated simulation histogram + percentiles
 *  4. Tribunal        — arbitrator panel simulation, outcome probabilities
 *  5. Scenarios       — seat × tribunal × cost_rule scenario explorer
 *  6. Knowledge Graph — 32-node Neo4j-style arbitration graph (React Flow)
 *  7. Strategy        — legal strategy comparator + settlement decision
 */

import { useState, useCallback, useRef } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import "reactflow/dist/style.css";
import dagre from "dagre";
import {
  Scale, Zap, AlertTriangle, TrendingUp, BarChart3, Network,
  Brain, Target, Shield, DollarSign, Activity, ChevronDown,
  ChevronUp, RefreshCw, FileText, Globe, Users, Upload, CheckCircle, X,
  Sparkles, Maximize, Minimize,
} from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend, LineChart, Line, CartesianGrid, Area, AreaChart,
} from "recharts";
import {
  arbitrationAnalyze,
  arbitrationMonteCarlo,
  arbitrationScenarios,
  arbitrationTribunal,
  arbitrationCanonicalGraph,
  arbitrationStrategies,
  arbitrationOptimize,
} from "../services/arbitrationService";
import ClauseRewritesPanel from "../components/arbitration/ClauseRewritesPanel";
import EmbeddingsPanel from "../components/arbitration/EmbeddingsPanel";
import GNNPredictionsPanel from "../components/arbitration/GNNPredictionsPanel";

// ─── helpers ───────────────────────────────────────────────────
const fmt = (n, decimals = 0) =>
  n == null ? "—" : n.toLocaleString("en-US", { maximumFractionDigits: decimals });
const fmtUSD = (n) =>
  n == null ? "—" : "$" + fmt(n);
const pct = (n) => (n == null ? "—" : (n * 100).toFixed(1) + "%");

// ─── Graph Layout Helper: Circular Layout ──────────────────────
const getLayoutedElements = (nodes, edges) => {
  if (nodes.length === 0) return { nodes: [], edges };

  const centerX = 1500;
  const centerY = 1000;
  const baseRadius = 600;

  // Group nodes by type for concentric circles
  const nodesByType = {};
  nodes.forEach(node => {
    const type = node.data?.type || 'Unknown';
    if (!nodesByType[type]) nodesByType[type] = [];
    nodesByType[type].push(node);
  });

  const types = Object.keys(nodesByType);
  const layoutedNodes = [];

  types.forEach((type, ringIndex) => {
    const nodesInRing = nodesByType[type];
    const radius = baseRadius + (ringIndex * 350); // Much larger spacing between rings
    const angleStep = (2 * Math.PI) / nodesInRing.length;

    nodesInRing.forEach((node, i) => {
      const angle = i * angleStep;
      // Add slight random offset to prevent exact overlaps
      const offsetX = (Math.random() - 0.5) * 40;
      const offsetY = (Math.random() - 0.5) * 40;
      layoutedNodes.push({
        ...node,
        position: {
          x: centerX + radius * Math.cos(angle) + offsetX,
          y: centerY + radius * Math.sin(angle) + offsetY,
        },
      });
    });
  });

  return { nodes: layoutedNodes, edges };
};

const RISK_COLORS = { HIGH: "#F16667", MEDIUM: "#F79767", LOW: "#68BC00" };
const TAB_LIST = [
  { id: "overview",   label: "Overview",        icon: Activity },
  { id: "clauses",    label: "Clause Analysis",  icon: FileText },
  { id: "embeddings", label: "LegalBERT",        icon: Brain },
  { id: "rewrites",   label: "AI Rewrites",      icon: Sparkles },
  { id: "gnn",        label: "GNN Predictions",  icon: Network },
  { id: "montecarlo", label: "Monte Carlo",       icon: BarChart3 },
  { id: "tribunal",   label: "Tribunal Sim",      icon: Users },
  { id: "scenarios",  label: "Scenarios",         icon: Globe },
  { id: "graph",      label: "Knowledge Graph",   icon: Target },
  { id: "strategy",   label: "Strategy",          icon: Shield },
];

const OUTCOME_COLORS = {
  buyer_win:    "#68BC00",
  supplier_win: "#F16667",
  partial_award:"#F79767",
  settlement:   "#4C8EDA",
};

// ─── KPI Card ──────────────────────────────────────────────────
const KPICard = ({ label, value, sub, color = "#06B6D4", icon: Icon }) => (
  <div
    className="rounded-xl p-4 flex flex-col gap-1"
    style={{
      background: `linear-gradient(135deg, ${color}12 0%, ${color}06 100%)`,
      border: `1px solid ${color}30`,
    }}
  >
    <div className="flex items-center gap-2 mb-1">
      {Icon && <Icon size={14} style={{ color }} />}
      <span className="text-xs text-slate-400">{label}</span>
    </div>
    <div className="text-2xl font-bold" style={{ color }}>
      {value}
    </div>
    {sub && <div className="text-xs text-slate-500">{sub}</div>}
  </div>
);

// ─── Main Component ────────────────────────────────────────────
export default function ArbitrationDashboard() {
  const [activeTab, setActiveTab]             = useState("overview");
  const [loading, setLoading]                 = useState(false);
  const [error, setError]                     = useState(null);
  const [analysisResult, setAnalysisResult]   = useState(null);
  const [canonicalGraph, setCanonicalGraph]   = useState(null);

  // Form state
  const [contractText, setContractText]       = useState("");
  const [contractValue, setContractValue]     = useState(150_000_000);
  const [settlementOffer, setSettlementOffer] = useState("");
  const [mcRuns, setMcRuns]                   = useState(50000);

  // Upload state
  const [uploadedFile, setUploadedFile]       = useState(null);
  const [uploading, setUploading]             = useState(false);
  const [uploadError, setUploadError]         = useState(null);

  // ── Run Analysis ────────────────────────────────────────────
  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await arbitrationAnalyze({
        contractText:  contractText || undefined,
        contractValue: Number(contractValue),
        settlementOffer: settlementOffer ? Number(settlementOffer) : undefined,
        monteCarloRuns: Number(mcRuns),
        tribunalRuns:   5000,
      });
      setAnalysisResult(result);
      setActiveTab("overview");
    } catch (e) {
      setError(e?.response?.data?.error || e.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, [contractText, contractValue, settlementOffer, mcRuns]);

  // ── Load canonical graph ─────────────────────────────────────
  const loadCanonicalGraph = useCallback(async () => {
    if (canonicalGraph) return;
    setLoading(true);
    try {
      const data = await arbitrationCanonicalGraph();
      setCanonicalGraph(data.graph);
    } catch (e) {
      setError("Failed to load knowledge graph");
    } finally {
      setLoading(false);
    }
  }, [canonicalGraph]);

  // ── File Upload & Text Extraction ───────────────────────────
  const handleFileUpload = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    const allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"];
    if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|docx|txt)$/i)) {
      setUploadError("Only PDF, DOCX, or TXT files are supported");
      return;
    }

    setUploadedFile(file);
    setUploadError(null);
    setUploading(true);

    try {
      // For TXT files — read directly in browser
      if (file.type === "text/plain" || file.name.endsWith(".txt")) {
        const text = await file.text();
        setContractText(text);
        setUploading(false);
        return;
      }

      // For PDF/DOCX — use dedicated extract-text endpoint (no DB save)
      const formData = new FormData();
      formData.append("file", file);

      const API_BASE = `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api`;
      const token = localStorage.getItem("token");

      const res = await fetch(`${API_BASE}/arbitration/extract-text`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Text extraction failed");
      }

      if (data.text && data.text.trim()) {
        setContractText(data.text);
      } else {
        setUploadError("File uploaded but text extraction returned empty. The file may be scanned/image-only. Try pasting manually.");
      }
    } catch (err) {
      setUploadError("Could not extract text from file. Try pasting the contract text manually.");
    } finally {
      setUploading(false);
      // Reset input so same file can be re-uploaded
      e.target.value = "";
    }
  }, []);

  const clearUpload = useCallback(() => {
    setUploadedFile(null);
    setUploadError(null);
    setContractText("");
  }, []);

  const graphData = analysisResult?.knowledge_graph || canonicalGraph;

  // ─── TAB: Overview ──────────────────────────────────────────
  const renderOverview = () => {
    const s  = analysisResult?.summary  || {};
    const ex = analysisResult?.exposure || {};
    const mc = analysisResult?.monte_carlo || {};
    const tr = analysisResult?.tribunal?.probabilities || {};

    // Use max score per dimension across all clauses — shows worst-case risk per axis
    const clauses = analysisResult?.clauses || [];
    const maxDim = (key, fallback) => clauses.length > 0
      ? Math.max(...clauses.map(cl => cl.risk_vector?.[key] || 0)) * 100
      : fallback * 100;

    const radarData = [
      { dim: "Jurisdiction",    score: Math.round(maxDim("jurisdiction_risk",           0.40)) },
      { dim: "Cost Exposure",   score: Math.round(maxDim("cost_exposure",               0.35)) },
      { dim: "Enforcement",     score: Math.round(maxDim("enforcement_risk",            0.38)) },
      { dim: "Delay Dispute",   score: Math.round(maxDim("delay_dispute_risk",          0.45)) },
      { dim: "Procedural",      score: Math.round(maxDim("procedural_risk",             0.32)) },
      { dim: "Subcontractor",   score: Math.round(maxDim("subcontractor_pass_through",  0.28)) },
    ];

    const pieData = Object.entries(tr).map(([k, v]) => ({
      name: k.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase()),
      value: Math.round(v * 100),
      color: OUTCOME_COLORS[k] || "#ccc",
    }));

    return (
      <div className="space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard label="Contract Value"     value={fmtUSD(s.contract_value || contractValue)} color="#06B6D4" icon={DollarSign} />
          <KPICard label="Arbitration Exposure" value={fmtUSD(ex.total_exposure)} color="#F16667" icon={AlertTriangle}
            sub={`${pct(s.dispute_probability)} dispute prob`} />
          <KPICard label="Expected Loss (MC)"  value={fmtUSD(mc.expected_loss)} color="#F79767" icon={TrendingUp}
            sub={`P95 worst: ${fmtUSD(mc.worst_case_p95)}`} />
          <KPICard label="Clauses Detected"    value={fmt(s.total_clauses)} color="#68BC00" icon={FileText}
            sub={`${s.high_risk_clauses || 0} HIGH · ${s.medium_risk_clauses || 0} MED`} />
        </div>

        {/* Radar + Pie */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/60">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Risk Dimension Radar</h3>
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="dim" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} />
                <Radar name="Risk" dataKey="score" stroke="#F16667" fill="#F16667" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/60">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Tribunal Outcome Probability</h3>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, value }) => `${name}: ${value}%`} labelLine>
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-40 text-slate-500 text-sm">
                Run analysis to see tribunal outcomes
              </div>
            )}
          </div>
        </div>

        {/* Settlement recommendation */}
        {analysisResult?.settlement && (
          <div
            className="rounded-xl p-5 border"
            style={{
              background: analysisResult.settlement.decision === "SETTLE"
                ? "rgba(104,188,0,0.08)" : "rgba(241,102,103,0.08)",
              borderColor: analysisResult.settlement.decision === "SETTLE"
                ? "#68BC0050" : "#F1666750",
            }}
          >
            <div className="flex items-center gap-3 mb-2">
              <Scale size={18} style={{ color: analysisResult.settlement.decision === "SETTLE" ? "#68BC00" : "#F16667" }} />
              <span className="font-bold text-white text-sm">
                Settlement Recommendation: {" "}
                <span style={{ color: analysisResult.settlement.decision === "SETTLE" ? "#68BC00" : "#F16667" }}>
                  {analysisResult.settlement.decision.replace(/_/g, " ")}
                </span>
              </span>
            </div>
            <p className="text-slate-300 text-xs">{analysisResult.settlement.recommendation}</p>
            <div className="mt-2 grid grid-cols-3 gap-3 text-xs text-slate-400">
              <span>Total Arb Cost: <strong className="text-white">{fmtUSD(analysisResult.settlement.total_arbitration_cost)}</strong></span>
              <span>Settlement Offer: <strong className="text-white">{fmtUSD(analysisResult.settlement.settlement_offer)}</strong></span>
              <span>Potential Saving: <strong style={{ color: "#68BC00" }}>{fmtUSD(analysisResult.settlement.potential_saving)}</strong></span>
            </div>
          </div>
        )}

        {/* Negotiation optimization */}
        {analysisResult?.negotiation && (
          <div className="rounded-xl p-4 border border-cyan-500/20 bg-cyan-500/05">
            <h3 className="text-sm font-semibold text-cyan-400 mb-3 flex items-center gap-2">
              <Target size={14} /> Optimal Arbitration Clause Configuration
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              {Object.entries(analysisResult.negotiation.optimal_configuration || {}).map(([k, v]) => (
                <div key={k} className="bg-slate-800/60 rounded-lg p-2">
                  <div className="text-slate-400 capitalize">{k.replace(/_/g, " ")}</div>
                  <div className="text-white font-semibold capitalize">{String(v).replace(/_/g, " ")}</div>
                </div>
              ))}
            </div>
            <div className="mt-2 text-xs text-slate-400">
              Potential saving vs worst config:{" "}
              <strong style={{ color: "#68BC00" }}>
                {fmtUSD(analysisResult.negotiation.potential_saving)} ({analysisResult.negotiation.saving_pct}%)
              </strong>
            </div>
          </div>
        )}
      </div>
    );
  };

  // ─── TAB: Clauses ───────────────────────────────────────────
  const renderClauses = () => {
    const clauses = analysisResult?.clauses || [];
    if (!clauses.length) return <EmptyState msg="Run analysis to see clause extraction results" />;

    const dims = [
      "jurisdiction_risk", "cost_exposure", "institutional_risk",
      "tribunal_structure", "procedural_risk", "enforcement_risk",
      "delay_dispute_risk", "subcontractor_pass_through",
    ];

    return (
      <div className="space-y-4">
        <div className="text-xs text-slate-400 mb-2">
          {clauses.length} arbitration-relevant clauses extracted · Scored across 8 risk dimensions
        </div>
        {clauses.map((cl, i) => {
          const rv = cl.risk_vector || {};
          const color = RISK_COLORS[cl.risk_level] || "#94a3b8";
          const radarData = dims.map(d => ({
            dim: d.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()).slice(0, 14),
            score: Math.round((rv[d] || 0) * 100),
          }));
          return (
            <div key={i} className="rounded-xl border border-slate-700/40 bg-slate-900/60 overflow-hidden">
              <div className="flex items-center justify-between p-3 border-b border-slate-700/30">
                <span className="text-xs text-slate-400">Clause #{i + 1} · Confidence {pct(cl.confidence)}</span>
                <span
                  className="text-xs font-bold px-2 py-0.5 rounded-full"
                  style={{ background: color + "22", color, border: `1px solid ${color}44` }}
                >
                  {cl.risk_level} RISK · composite {((rv.composite || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
                <div className="p-4 border-r border-slate-700/30">
                  <p className="text-xs text-slate-300 leading-relaxed line-clamp-6">{cl.text}</p>
                </div>
                <div className="p-2">
                  <ResponsiveContainer width="100%" height={160}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="dim" tick={{ fill: "#64748b", fontSize: 9 }} />
                      <PolarRadiusAxis domain={[0, 100]} tick={false} />
                      <Radar dataKey="score" stroke={color} fill={color} fillOpacity={0.2} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // ─── TAB: Monte Carlo ───────────────────────────────────────
  const renderMonteCarlo = () => {
    const mc = analysisResult?.monte_carlo;
    if (!mc) return <EmptyState msg="Run analysis to see Monte Carlo simulation results" />;

    const dist = (mc.loss_distribution || []).map(d => ({
      range: fmtUSD(d.range_start),
      count: d.count,
    }));

    const percentiles = [
      { label: "Expected (Mean)",  value: mc.expected_loss,   color: "#68BC00" },
      { label: "Median (P50)",     value: mc.median_loss,     color: "#4C8EDA" },
      { label: "P75",              value: mc.p75_loss,        color: "#F79767" },
      { label: "P90",              value: mc.p90_loss,        color: "#FF6B35" },
      { label: "P95 (Worst Case)", value: mc.worst_case_p95,  color: "#F16667" },
      { label: "VaR 99%",          value: mc.var_99,          color: "#E91E63" },
    ];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {percentiles.map(p => (
            <KPICard key={p.label} label={p.label} value={fmtUSD(p.value)} color={p.color} />
          ))}
        </div>
        <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/60">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">
            Loss Distribution ({fmt(mc.runs)} simulations, correlated risk factors)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dist} margin={{ top: 10, right: 20, bottom: 40, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="range" tick={{ fill: "#64748b", fontSize: 9 }} angle={-40} textAnchor="end" interval={1} />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#fff" }}
                formatter={(v) => [fmt(v), "Simulations"]}
              />
              <Bar dataKey="count" fill="#4C8EDA" radius={[3, 3, 0, 0]}>
                {dist.map((_, i) => (
                  <Cell key={i} fill={i > dist.length * 0.85 ? "#F16667" : i > dist.length * 0.70 ? "#F79767" : "#4C8EDA"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-2 text-xs text-slate-500 text-center">
            Red bars = tail risk zone (P85+) · Correlated delay × jurisdiction × enforcement × cost factors
          </div>
        </div>
        <div className="text-xs text-slate-400 bg-slate-800/40 rounded-lg p-3">
          <strong className="text-slate-300">Methodology:</strong> 50,000-run correlated Monte Carlo with Cholesky-decomposed
          covariance matrix across delay dispute (0.55 corr), jurisdiction, enforcement, and cost risk factors.
          Std deviation: {fmtUSD(mc.std_deviation)}.
        </div>
      </div>
    );
  };

  // ─── TAB: Tribunal ──────────────────────────────────────────
  const renderTribunal = () => {
    const tr = analysisResult?.tribunal;
    if (!tr) return <EmptyState msg="Run analysis to see tribunal simulation results" />;

    const probs = tr.probabilities || {};
    const barData = Object.entries(probs).map(([k, v]) => ({
      outcome: k.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase()),
      probability: Math.round(v * 100),
      color: OUTCOME_COLORS[k] || "#ccc",
    }));

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {barData.map(d => (
            <KPICard key={d.outcome} label={d.outcome} value={d.probability + "%"} color={d.color} icon={Scale} />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/60">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Outcome Probability Distribution</h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={barData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 10 }} unit="%" />
                <YAxis dataKey="outcome" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} width={110} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#fff" }}
                  formatter={(v) => [v + "%", "Probability"]}
                />
                <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                  {barData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/60 flex flex-col justify-between">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Tribunal Metrics</h3>
            <div className="space-y-3">
              <MetricRow label="Expected Award"          value={fmtUSD(tr.expected_award)} />
              <MetricRow label="Avg Tribunal Score"      value={(tr.avg_tribunal_score * 100).toFixed(1) + "%"} />
              <MetricRow label="Score Std Dev"           value={(tr.score_std * 100).toFixed(1) + "%"} />
              <MetricRow label="Simulated Panels"        value={fmt(tr.runs)} />
            </div>
            <div className="mt-4 p-3 bg-slate-800/50 rounded-lg text-xs text-slate-400">
              <strong className="text-slate-300">Arbitrator Profiles:</strong> Strict Legalist ·
              Commercial Pragmatist · Delay Specialist · Cost Sensitive · Enforcement Expert.
              Random panel composition across {fmt(tr.runs)} simulated tribunals.
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ─── TAB: Scenarios ─────────────────────────────────────────
  const renderScenarios = () => {
    const sc = analysisResult?.scenarios;
    if (!sc) return <EmptyState msg="Run analysis to see scenario engine results" />;

    const optimal = sc.optimal || [];
    const worst   = sc.worst   || [];

    return (
      <div className="space-y-6">
        <div className="text-xs text-slate-400">
          {fmt(sc.total_combinations)} total configurations evaluated · Ranked by expected arbitration cost
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Optimal */}
          <div className="rounded-xl border border-green-500/20 bg-green-500/05 overflow-hidden">
            <div className="p-3 border-b border-green-500/20">
              <h3 className="text-sm font-semibold text-green-400">Top {optimal.length} Optimal Configurations</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-700/40">
                    {["Seat", "Tribunal", "Cost Rule", "Institution", "Expected Cost"].map(h => (
                      <th key={h} className="px-3 py-2 text-left text-slate-400 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {optimal.map((s, i) => (
                    <tr key={i} className="border-b border-slate-700/20 hover:bg-slate-800/30">
                      <td className="px-3 py-2 text-slate-300 capitalize">{s.seat}</td>
                      <td className="px-3 py-2 text-slate-300 capitalize">{s.tribunal.replace(/_/g, " ")}</td>
                      <td className="px-3 py-2 text-slate-300 capitalize">{s.cost_rule.replace(/_/g, " ")}</td>
                      <td className="px-3 py-2 text-slate-300">{s.institution}</td>
                      <td className="px-3 py-2 font-semibold" style={{ color: "#68BC00" }}>{fmtUSD(s.expected_cost)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {/* Worst */}
          <div className="rounded-xl border border-red-500/20 bg-red-500/05 overflow-hidden">
            <div className="p-3 border-b border-red-500/20">
              <h3 className="text-sm font-semibold text-red-400">Top {worst.length} Worst Configurations (Avoid)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-700/40">
                    {["Seat", "Tribunal", "Cost Rule", "Institution", "Expected Cost"].map(h => (
                      <th key={h} className="px-3 py-2 text-left text-slate-400 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {worst.map((s, i) => (
                    <tr key={i} className="border-b border-slate-700/20 hover:bg-slate-800/30">
                      <td className="px-3 py-2 text-slate-300 capitalize">{s.seat}</td>
                      <td className="px-3 py-2 text-slate-300 capitalize">{s.tribunal.replace(/_/g, " ")}</td>
                      <td className="px-3 py-2 text-slate-300 capitalize">{s.cost_rule.replace(/_/g, " ")}</td>
                      <td className="px-3 py-2 text-slate-300">{s.institution}</td>
                      <td className="px-3 py-2 font-semibold" style={{ color: "#F16667" }}>{fmtUSD(s.expected_cost)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ─── TAB: Knowledge Graph ────────────────────────────────────
  const graphContainerRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    if (!graphContainerRef.current) return;

    if (!document.fullscreenElement) {
      graphContainerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const renderGraph = () => {
    if (!graphData) {
      return (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <Network size={40} className="text-slate-600" />
          <p className="text-slate-400 text-sm">32-node arbitration knowledge graph</p>
          <button
            onClick={loadCanonicalGraph}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
            style={{ background: "#4C8EDA22", border: "1px solid #4C8EDA55", color: "#4C8EDA" }}
          >
            <Network size={14} />
            {loading ? "Loading…" : "Load Canonical Graph"}
          </button>
        </div>
      );
    }

    // Apply circular layout for proper spacing
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      graphData.nodes || [],
      graphData.edges || []
    );

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs text-slate-400">
            {layoutedNodes.length} nodes · {layoutedEdges.length} edges · Click and drag to explore
          </div>
          <div className="flex items-center gap-3">
            <div className="flex gap-2 text-xs">
              {[
                { label: "Foundation",   color: "#68BC00" },
                { label: "Jurisdiction", color: "#9063CD" },
                { label: "Delay",        color: "#FF6B35" },
                { label: "Cost",         color: "#F16667" },
                { label: "Enforcement",  color: "#E91E63" },
              ].map(l => (
                <span key={l.label} className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full" style={{ background: l.color }} />
                  <span className="text-slate-400">{l.label}</span>
                </span>
              ))}
            </div>
            <button
              onClick={toggleFullscreen}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-500 transition-colors"
              style={{ color: "#4C8EDA" }}
            >
              {isFullscreen ? <Minimize size={14} /> : <Maximize size={14} />}
              {isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            </button>
          </div>
        </div>
        <div
          ref={graphContainerRef}
          className="rounded-xl overflow-hidden border border-slate-700/40"
          style={{ height: isFullscreen ? "100vh" : "580px", background: "#0f172a" }}
        >
          <ReactFlow
            nodes={layoutedNodes}
            edges={layoutedEdges}
            fitView
            attributionPosition="bottom-right"
            nodesDraggable
            nodesConnectable={false}
            elementsSelectable
          >
            <Background color="#334155" gap={24} />
            <Controls />
            <MiniMap
              nodeColor={(n) => n.style?.border?.replace(/2px solid /, "") || "#4C8EDA"}
              maskColor="#0f172a88"
              style={{ background: "#1e293b" }}
            />
          </ReactFlow>
        </div>
        {analysisResult?.influence_scores && (
          <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/60">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">PageRank Influence Scores (Top 8)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {Object.entries(analysisResult.influence_scores)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 8)
                .map(([id, score]) => {
                  const node = layoutedNodes.find(n => n.id === id);
                  return (
                    <div key={id} className="bg-slate-800/50 rounded-lg p-2 text-xs">
                      <div className="text-slate-400">{node?.data?.label || id}</div>
                      <div className="font-bold" style={{ color: score > 0.7 ? "#F16667" : score > 0.4 ? "#F79767" : "#68BC00" }}>
                        {(score * 100).toFixed(1)}%
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </div>
    );
  };

  // ─── TAB: Strategy ───────────────────────────────────────────
  const renderStrategy = () => {
    const strategies = analysisResult?.strategies || [];
    const exposure   = analysisResult?.exposure;
    const settlement = analysisResult?.settlement;
    const negotiation = analysisResult?.negotiation;

    if (!strategies.length) return <EmptyState msg="Run analysis to see legal strategy comparisons" />;

    const barData = strategies.map(s => ({
      strategy: s.strategy.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
      buyer_win:    Math.round((s.probabilities?.buyer_win || 0) * 100),
      supplier_win: Math.round((s.probabilities?.supplier_win || 0) * 100),
      settlement:   Math.round((s.probabilities?.settlement || 0) * 100),
      partial:      Math.round((s.probabilities?.partial_award || 0) * 100),
    }));

    // Rank badge color
    const rankColor = (i) => i === 0 ? "#68BC00" : i === 1 ? "#F79767" : "#64748b";

    // Exposure formula data
    const expFormulaRows = exposure ? [
      { label: "Dispute Probability",    value: ((exposure.dispute_probability || 0) * 100).toFixed(1) + "%" },
      { label: "Expected Award",         value: fmtUSD(exposure.expected_award) },
      { label: "Arbitration Exposure",   value: fmtUSD(exposure.arbitration_exposure) },
      { label: "Legal Cost Estimate",    value: fmtUSD(exposure.legal_cost_estimate) },
      { label: "Total Exposure",         value: fmtUSD(exposure.total_exposure), bold: true },
    ] : [];

    const isSettle = settlement?.decision === "SETTLE";

    return (
      <div className="space-y-6">

        {/* ── Exposure Formula Breakdown ── */}
        {exposure && (
          <div className="rounded-xl border border-purple-500/20 bg-purple-500/05 p-5">
            <h3 className="text-sm font-semibold text-purple-400 mb-1 flex items-center gap-2">
              <DollarSign size={14} /> Arbitration Exposure Formula
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Exposure = P(dispute) × [P(buyer win) × Buyer Award + P(supplier win) × Supplier Award + P(partial) × Partial Award] + Legal Costs
            </p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {expFormulaRows.map((row, i) => (
                <div
                  key={i}
                  className="bg-slate-800/60 rounded-lg p-3 text-center"
                  style={row.bold ? { border: "1px solid #9063CD50" } : {}}
                >
                  <div className="text-xs text-slate-400 mb-1">{row.label}</div>
                  <div
                    className="text-sm font-bold"
                    style={{ color: row.bold ? "#9063CD" : "#e2e8f0" }}
                  >
                    {row.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Settlement Decision Engine ── */}
        {settlement ? (
          <div
            className="rounded-xl p-5 border"
            style={{
              background: isSettle ? "rgba(104,188,0,0.07)" : "rgba(241,102,103,0.07)",
              borderColor: isSettle ? "#68BC0050" : "#F1666750",
            }}
          >
            <div className="flex items-center gap-3 mb-3">
              <Scale size={20} style={{ color: isSettle ? "#68BC00" : "#F16667" }} />
              <div>
                <div className="text-sm font-bold text-white">
                  Settlement Decision Engine
                </div>
                <div
                  className="text-xs font-semibold mt-0.5"
                  style={{ color: isSettle ? "#68BC00" : "#F16667" }}
                >
                  Recommendation: {settlement.decision.replace(/_/g, " ")}
                </div>
              </div>
              <div
                className="ml-auto px-3 py-1 rounded-full text-xs font-bold"
                style={{
                  background: isSettle ? "#68BC0022" : "#F1666722",
                  color: isSettle ? "#68BC00" : "#F16667",
                  border: `1px solid ${isSettle ? "#68BC0055" : "#F1666755"}`,
                }}
              >
                {isSettle ? "SETTLE" : "PROCEED"}
              </div>
            </div>
            <p className="text-xs text-slate-300 mb-4">{settlement.recommendation}</p>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-xs text-slate-400 mb-1">Total Arbitration Cost</div>
                <div className="text-base font-bold text-white">{fmtUSD(settlement.total_arbitration_cost)}</div>
                <div className="text-xs text-slate-500 mt-1">Exposure + legal fees</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-xs text-slate-400 mb-1">Settlement Offer</div>
                <div className="text-base font-bold" style={{ color: "#4C8EDA" }}>{fmtUSD(settlement.settlement_offer)}</div>
                <div className="text-xs text-slate-500 mt-1">Negotiated amount</div>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-xs text-slate-400 mb-1">Potential Saving</div>
                <div className="text-base font-bold" style={{ color: "#68BC00" }}>{fmtUSD(settlement.potential_saving)}</div>
                <div className="text-xs text-slate-500 mt-1">vs going to arbitration</div>
              </div>
            </div>
          </div>
        ) : (
          <div
            className="rounded-xl p-4 border border-slate-700/30 bg-slate-900/50"
          >
            <div className="flex items-center gap-2 mb-2">
              <Scale size={14} style={{ color: "#4C8EDA" }} />
              <span className="text-sm font-semibold text-slate-300">Settlement Decision Engine</span>
            </div>
            <p className="text-xs text-slate-400">
              Enter a settlement offer amount in the Contract Configuration panel above and re-run analysis to get a
              settle vs. proceed recommendation with potential savings calculation.
            </p>
          </div>
        )}

        {/* ── Negotiation Optimizer ── */}
        {negotiation && (
          <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/04 p-5">
            <h3 className="text-sm font-semibold text-cyan-400 mb-3 flex items-center gap-2">
              <Target size={14} /> Clause Negotiation Optimizer
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Exhaustive search across seat × tribunal × cost rule × institution — find the configuration that minimizes buyer exposure.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-800/50 rounded-xl p-4">
                <div className="text-xs text-emerald-400 font-semibold mb-2 flex items-center gap-1">
                  <Shield size={12} /> Optimal Configuration
                </div>
                <div className="space-y-2">
                  {Object.entries(negotiation.optimal_configuration || {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, " ")}</span>
                      <span className="text-white font-medium capitalize">
                        {k === "expected_cost" ? fmtUSD(v) : String(v).replace(/_/g, " ")}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-slate-800/50 rounded-xl p-4">
                <div className="text-xs text-red-400 font-semibold mb-2 flex items-center gap-1">
                  <AlertTriangle size={12} /> Worst Configuration (Avoid)
                </div>
                <div className="space-y-2">
                  {Object.entries(negotiation.worst_configuration || {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-slate-400 capitalize">{k.replace(/_/g, " ")}</span>
                      <span className="text-red-300 font-medium capitalize">
                        {k === "expected_cost" ? fmtUSD(v) : String(v).replace(/_/g, " ")}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div
              className="mt-4 rounded-lg p-3 text-center"
              style={{ background: "rgba(104,188,0,0.08)", border: "1px solid #68BC0030" }}
            >
              <span className="text-xs text-slate-400">Potential saving by choosing optimal vs worst config: </span>
              <span className="text-base font-bold text-emerald-400">{fmtUSD(negotiation.potential_saving)}</span>
              <span className="text-xs text-slate-400 ml-2">({negotiation.saving_pct}% reduction)</span>
            </div>
          </div>
        )}

        {/* ── Strategy Comparison Chart ── */}
        <div className="rounded-xl p-4 border border-slate-700/40 bg-slate-900/60">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Legal Strategy Comparison</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData} margin={{ top: 10, right: 20, bottom: 60, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="strategy" tick={{ fill: "#94a3b8", fontSize: 10 }} angle={-20} textAnchor="end" />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} unit="%" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", color: "#fff" }}
                formatter={(v) => [v + "%"]}
              />
              <Legend wrapperStyle={{ paddingTop: 8 }} />
              <Bar dataKey="buyer_win"    fill="#68BC00" name="Buyer Win"    radius={[3, 3, 0, 0]} />
              <Bar dataKey="supplier_win" fill="#F16667" name="Supplier Win" radius={[3, 3, 0, 0]} />
              <Bar dataKey="settlement"   fill="#4C8EDA" name="Settlement"   radius={[3, 3, 0, 0]} />
              <Bar dataKey="partial"      fill="#F79767" name="Partial Award" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* ── Strategy Cards ── */}
        <div className="space-y-3">
          {strategies.map((s, i) => (
            <div key={i} className="rounded-xl border border-slate-700/30 bg-slate-900/50 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span
                    className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold"
                    style={{ background: rankColor(i) + "22", color: rankColor(i), border: `1px solid ${rankColor(i)}44` }}
                  >
                    {i + 1}
                  </span>
                  <span className="text-sm font-semibold text-white capitalize">
                    {s.strategy.replace(/_/g, " ")}
                  </span>
                </div>
                <span
                  className="text-xs font-bold px-2 py-0.5 rounded-full"
                  style={{
                    background: rankColor(i) + "22",
                    color: rankColor(i),
                    border: `1px solid ${rankColor(i)}44`,
                  }}
                >
                  {Math.round((s.probabilities?.buyer_win || 0) * 100)}% Buyer Win
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-3">{s.description}</p>
              <div className="grid grid-cols-4 gap-2 text-xs mb-2">
                {Object.entries(s.probabilities || {}).map(([k, v]) => (
                  <div key={k} className="text-center bg-slate-800/40 rounded-lg p-1.5">
                    <div className="font-bold" style={{ color: OUTCOME_COLORS[k] || "#ccc" }}>
                      {Math.round(v * 100)}%
                    </div>
                    <div className="text-slate-500 capitalize text-xs">{k.replace("_", " ")}</div>
                  </div>
                ))}
              </div>
              {s.expected_award > 0 && (
                <div className="text-xs text-slate-400 mt-1">
                  Expected Award: <strong className="text-white">{fmtUSD(s.expected_award)}</strong>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ─── Helpers ────────────────────────────────────────────────
  const MetricRow = ({ label, value }) => (
    <div className="flex items-center justify-between py-1.5 border-b border-slate-700/20 last:border-0">
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-xs font-semibold text-white">{value}</span>
    </div>
  );

  const EmptyState = ({ msg }) => (
    <div className="flex flex-col items-center justify-center h-40 gap-3 text-slate-500">
      <AlertTriangle size={28} />
      <p className="text-sm">{msg}</p>
    </div>
  );

  // ─── Render ─────────────────────────────────────────────────
  // ─── NEW TAB RENDERERS ──────────────────────────────────────
  const renderEmbeddings = () => {
    if (!analysisResult?.analysis_id) {
      return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
          <Brain className="mx-auto mb-4" size={48} color="#4C8EDA" />
          <h3 className="text-lg font-semibold mb-2">Run Analysis First</h3>
          <p className="text-slate-400 text-sm">
            LegalBERT embeddings will be generated during the full analysis.
          </p>
        </div>
      );
    }
    return <EmbeddingsPanel analysisId={analysisResult.analysis_id} />;
  };

  const renderRewrites = () => {
    if (!analysisResult?.analysis_id) {
      return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
          <Sparkles className="mx-auto mb-4" size={48} color="#4C8EDA" />
          <h3 className="text-lg font-semibold mb-2">Run Analysis First</h3>
          <p className="text-slate-400 text-sm">
            AI clause rewrites will be generated for high-risk clauses during analysis.
          </p>
        </div>
      );
    }
    return <ClauseRewritesPanel analysisId={analysisResult.analysis_id} />;
  };

  const renderGNN = () => {
    if (!analysisResult?.analysis_id) {
      return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
          <Network className="mx-auto mb-4" size={48} color="#4C8EDA" />
          <h3 className="text-lg font-semibold mb-2">Run Analysis First</h3>
          <p className="text-slate-400 text-sm">
            GNN predictions will be generated from the contract knowledge graph.
          </p>
        </div>
      );
    }
    return <GNNPredictionsPanel analysisId={analysisResult.analysis_id} />;
  };

  const tabRenderers = {
    overview:   renderOverview,
    clauses:    renderClauses,
    embeddings: renderEmbeddings,
    rewrites:   renderRewrites,
    gnn:        renderGNN,
    montecarlo: renderMonteCarlo,
    tribunal:   renderTribunal,
    scenarios:  renderScenarios,
    graph:      renderGraph,
    strategy:   renderStrategy,
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">

        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl" style={{ background: "#F1666718", border: "1px solid #F1666740" }}>
            <Scale size={24} style={{ color: "#F16667" }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Arbitration Risk Management</h1>
            <p className="text-sm text-slate-400">
              Enterprise arbitration analysis for $100M+ EPC construction contracts
            </p>
          </div>
        </div>

        {/* Input Panel */}
        <div className="rounded-xl border border-slate-700/40 bg-slate-900/60 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-300">Contract Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Contract Value (USD)</label>
              <input
                type="number"
                value={contractValue}
                onChange={e => setContractValue(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                placeholder="150000000"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Settlement Offer (optional)</label>
              <input
                type="number"
                value={settlementOffer}
                onChange={e => setSettlementOffer(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                placeholder="8000000"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Monte Carlo Runs</label>
              <select
                value={mcRuns}
                onChange={e => setMcRuns(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                <option value={10000}>10,000 (fast)</option>
                <option value={50000}>50,000 (standard)</option>
                <option value={100000}>100,000 (high precision)</option>
              </select>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-slate-400">
                Contract Text (paste or upload — leave blank for demo)
              </label>
              {/* Upload button */}
              <label
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-all"
                style={{
                  background: uploading ? "#1e293b" : "#4C8EDA18",
                  border: "1px solid #4C8EDA44",
                  color: uploading ? "#64748b" : "#4C8EDA",
                  pointerEvents: uploading ? "none" : "auto",
                }}
              >
                {uploading
                  ? <><RefreshCw size={12} className="animate-spin" /> Extracting…</>
                  : <><Upload size={12} /> Upload PDF / DOCX / TXT</>
                }
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* Uploaded file pill */}
            {uploadedFile && !uploading && (
              <div
                className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-lg text-xs"
                style={{ background: "#68BC0012", border: "1px solid #68BC0030" }}
              >
                <CheckCircle size={12} style={{ color: "#68BC00" }} />
                <span className="text-green-400 font-medium">{uploadedFile.name}</span>
                <span className="text-slate-500">— text extracted</span>
                <button
                  onClick={clearUpload}
                  className="ml-auto text-slate-500 hover:text-red-400 transition-colors"
                >
                  <X size={12} />
                </button>
              </div>
            )}

            {/* Upload error */}
            {uploadError && (
              <div className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-lg text-xs"
                style={{ background: "#F1666712", border: "1px solid #F1666730" }}>
                <AlertTriangle size={12} style={{ color: "#F16667" }} />
                <span className="text-red-400">{uploadError}</span>
              </div>
            )}

            <textarea
              value={contractText}
              onChange={e => setContractText(e.target.value)}
              rows={4}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-cyan-500 resize-none"
              placeholder="Paste contract text containing arbitration, dispute resolution, governing law, seat of arbitration, liquidated damages, delay clauses…"
            />
            {contractText && (
              <div className="mt-1 text-xs text-slate-500">
                {contractText.length.toLocaleString()} characters · ready for analysis
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={runAnalysis}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold transition-all"
              style={{
                background: loading ? "#1e293b" : "linear-gradient(135deg, #F16667, #F79767)",
                color: loading ? "#64748b" : "#fff",
                border: loading ? "1px solid #334155" : "none",
              }}
            >
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
              {loading ? "Analysing…" : "Run Full Analysis"}
            </button>
            {analysisResult && (
              <span className="text-xs text-green-400 flex items-center gap-1">
                <Shield size={12} /> Analysis complete · {analysisResult.summary?.total_clauses} clauses
              </span>
            )}
            {error && <span className="text-xs text-red-400">{error}</span>}
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 overflow-x-auto pb-1">
          {TAB_LIST.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all"
                style={{
                  background: active ? "#F1666718" : "transparent",
                  border: active ? "1px solid #F1666740" : "1px solid transparent",
                  color: active ? "#F16667" : "#94a3b8",
                }}
              >
                <Icon size={13} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="min-h-96">
          {tabRenderers[activeTab]?.()}
        </div>

        {/* How It Works */}
        <div className="rounded-xl border border-slate-700/30 bg-slate-900/40 p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Brain size={14} className="text-cyan-400" /> How This Engine Works
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-400">
            <div>
              <div className="font-semibold text-slate-300 mb-1">Clause Extraction</div>
              30 regex patterns + confidence scoring across arbitration-specific legal language.
              Maps to 32 canonical FIDIC/EPC arbitration clause nodes.
            </div>
            <div>
              <div className="font-semibold text-slate-300 mb-1">Risk Scoring</div>
              8-dimensional configurable taxonomy (jurisdiction, cost, institutional, tribunal,
              procedural, enforcement, delay, subcontractor) with weighted composite scoring.
            </div>
            <div>
              <div className="font-semibold text-slate-300 mb-1">Monte Carlo + GNN</div>
              50,000-run correlated simulation (Cholesky covariance matrix) + PageRank-based
              influence propagation across the 32-node arbitration knowledge graph.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
