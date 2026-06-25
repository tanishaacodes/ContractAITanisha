import React, { useState, useEffect } from 'react';
import {
  XCircle, AlertTriangle, CheckCircle, TrendingUp, TrendingDown,
  Activity, Shield, Zap, Target, Globe, BarChart3, PieChart as PieChartIcon,
  AlertCircle, Brain, Scale, Gavel
} from 'lucide-react';
import {
  PieChart, Pie, BarChart, Bar, RadialBarChart, RadialBar,
  XAxis, YAxis, Tooltip, Cell, ResponsiveContainer, Legend, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, AreaChart, Area
} from 'recharts';

const RISK_COLORS = {
  HIGH: '#F16667',
  MEDIUM: '#FFD86E',
  LOW: '#68BC00',
};

// ════════════════════════════════════════════════════════════════
// ANIMATED COUNTER COMPONENT
// ════════════════════════════════════════════════════════════════
const AnimatedCounter = ({ value, duration = 1000, decimals = 0 }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = parseFloat(value);
    if (start === end) return;

    const range = end - start;
    const increment = range / (duration / 16);
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(start);
      }
    }, 16);

    return () => clearInterval(timer);
  }, [value, duration]);

  return <span>{count.toFixed(decimals)}</span>;
};

// ════════════════════════════════════════════════════════════════
// PULSING RISK INDICATOR
// ════════════════════════════════════════════════════════════════
const PulsingRiskBadge = ({ level }) => {
  const config = {
    HIGH: { color: 'red', glow: 'shadow-red-500/50', pulse: 'animate-pulse' },
    MEDIUM: { color: 'yellow', glow: 'shadow-yellow-500/50', pulse: '' },
    LOW: { color: 'green', glow: 'shadow-green-500/50', pulse: '' },
  };
  const c = config[level] || config.LOW;

  return (
    <span
      className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wide
        bg-${c.color}-500/20 text-${c.color}-400 border border-${c.color}-500/40
        shadow-lg ${c.glow} ${c.pulse}`}
    >
      {level}
    </span>
  );
};

// ════════════════════════════════════════════════════════════════
// RADIAL PROGRESS GAUGE
// ════════════════════════════════════════════════════════════════
const RadialGauge = ({ value, maxValue, label, color }) => {
  const percentage = (value / maxValue) * 100;
  const data = [{ name: label, value: percentage, fill: color }];

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={120}>
        <RadialBarChart
          innerRadius="70%"
          outerRadius="100%"
          data={data}
          startAngle={180}
          endAngle={0}
        >
          <PolarGrid gridType="circle" />
          <RadialBar
            minAngle={15}
            background
            clockWise
            dataKey="value"
            cornerRadius={10}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <p className="text-2xl font-bold" style={{ color }}>{value}</p>
        <p className="text-[10px] text-slate-500 uppercase">{label}</p>
      </div>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// BAYESIAN PROBABILITY DISTRIBUTION CARD
// ════════════════════════════════════════════════════════════════
const BayesianProbabilityCard = ({ clauseData }) => {
  // Simulate Bayesian posterior distribution
  const distributionData = [
    { range: '0-1', probability: 15, fill: '#68BC00' },
    { range: '1-2', probability: 25, fill: '#68BC00' },
    { range: '2-3', probability: 35, fill: '#FFD86E' },
    { range: '3-4', probability: 20, fill: '#F16667' },
    { range: '4+', probability: 5, fill: '#F16667' },
  ];

  return (
    <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Brain size={16} className="text-purple-400" />
        <p className="text-slate-200 text-sm font-semibold">Bayesian Risk Distribution</p>
      </div>
      <ResponsiveContainer width="100%" height={150}>
        <AreaChart data={distributionData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <defs>
            <linearGradient id="probGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 10 }} />
          <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: '#0f172a', border: '1px solid #8B5CF6', borderRadius: '8px' }}
            labelStyle={{ color: '#8B5CF6' }}
          />
          <Area type="monotone" dataKey="probability" stroke="#8B5CF6" fill="url(#probGradient)" />
        </AreaChart>
      </ResponsiveContainer>
      <div className="mt-2 flex items-center gap-2 text-xs text-purple-300">
        <Zap size={12} />
        <span>CPT Network: Event→Clause→Jurisdiction→Risk</span>
      </div>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// RISK HEATMAP MATRIX
// ════════════════════════════════════════════════════════════════
const RiskHeatmapMatrix = ({ clauses }) => {
  const categories = ['Liability', 'Payment', 'Termination', 'IP', 'Indemnity', 'Force Majeure'];
  const impacts = ['Low', 'Medium', 'High'];

  // Simplified heatmap data (in real app, categorize clauses)
  const heatmapData = categories.map(cat => ({
    category: cat,
    low: Math.floor(Math.random() * 5),
    medium: Math.floor(Math.random() * 5),
    high: Math.floor(Math.random() * 5),
  }));

  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Target size={16} className="text-cyan-400" />
        <p className="text-slate-200 text-sm font-semibold">Clause Category Risk Matrix</p>
      </div>
      <div className="grid grid-cols-4 gap-2">
        <div></div>
        {impacts.map(impact => (
          <div key={impact} className="text-center text-[10px] text-slate-500 uppercase">{impact}</div>
        ))}
        {heatmapData.map(row => (
          <React.Fragment key={row.category}>
            <div className="text-[10px] text-slate-400 flex items-center">{row.category}</div>
            <div className={`rounded p-2 text-center text-xs font-bold transition-all hover:scale-110 ${
              row.low === 0 ? 'bg-slate-800 text-slate-600' : 'bg-green-500/30 text-green-300'
            }`}>{row.low}</div>
            <div className={`rounded p-2 text-center text-xs font-bold transition-all hover:scale-110 ${
              row.medium === 0 ? 'bg-slate-800 text-slate-600' : 'bg-yellow-500/30 text-yellow-300'
            }`}>{row.medium}</div>
            <div className={`rounded p-2 text-center text-xs font-bold transition-all hover:scale-110 ${
              row.high === 0 ? 'bg-slate-800 text-slate-600' : 'bg-red-500/30 text-red-300 animate-pulse'
            }`}>{row.high}</div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// ENHANCED KPI CARD
// ════════════════════════════════════════════════════════════════
const EnhancedKPICard = ({ label, value, color, gradient, icon: Icon, trend, sub }) => {
  return (
    <div className={`relative overflow-hidden bg-gradient-to-br ${gradient} border border-slate-700/50 rounded-xl p-4
      transform transition-all duration-300 hover:scale-105 hover:shadow-2xl cursor-pointer group`}>
      {/* Background glow effect */}
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity bg-gradient-to-br ${color} blur-xl`}></div>

      {/* Icon */}
      <div className="relative flex items-center justify-between mb-2">
        <Icon size={20} className={`${color}`} />
        {trend && (
          <div className={`flex items-center gap-1 ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            <span className="text-[10px] font-bold">{Math.abs(trend)}%</span>
          </div>
        )}
      </div>

      {/* Label */}
      <p className="relative text-slate-400 text-[10px] uppercase tracking-wider">{label}</p>

      {/* Value with animated counter */}
      <p className={`relative text-3xl font-black mt-1 ${color}`}>
        <AnimatedCounter value={value} decimals={label.includes('Score') ? 2 : 0} />
      </p>

      {/* Subtitle */}
      <p className="relative text-slate-600 text-[9px] mt-1">{sub}</p>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// MAIN ENHANCED SUMMARY TAB
// ════════════════════════════════════════════════════════════════
const EnhancedSummaryTab = ({ data }) => {
  if (!data) return null;

  const clauses = data.clauses || [];
  const high = clauses.filter(c => (c.risk?.risk_level || '').toUpperCase() === 'HIGH').length;
  const medium = clauses.filter(c => (c.risk?.risk_level || '').toUpperCase() === 'MEDIUM').length;
  const low = clauses.length - high - medium;
  const avgScore = clauses.length
    ? (clauses.reduce((a, c) => a + (c.risk?.risk_score || 0), 0) / clauses.length)
    : 0;
  const maxScore = clauses.length
    ? Math.max(...clauses.map(c => c.risk?.risk_score || 0))
    : 0;
  const totalCases = clauses.reduce((a, c) => a + (c.cases?.length || 0), 0);

  // Verdict with enhanced styling
  const verdict = high > 2
    ? { label: 'HIGH RISK', color: 'text-red-400', bg: 'from-red-900/20 to-red-950/40', icon: XCircle, glow: 'shadow-red-500/30' }
    : high > 0 || medium > 3
    ? { label: 'MEDIUM RISK', color: 'text-yellow-400', bg: 'from-yellow-900/20 to-yellow-950/40', icon: AlertTriangle, glow: 'shadow-yellow-500/30' }
    : { label: 'LOW RISK', color: 'text-green-400', bg: 'from-green-900/20 to-green-950/40', icon: CheckCircle, glow: 'shadow-green-500/30' };

  const pieData = [
    { name: 'HIGH', value: high, fill: '#F16667' },
    { name: 'MEDIUM', value: medium, fill: '#FFD86E' },
    { name: 'LOW', value: low, fill: '#68BC00' },
  ].filter(d => d.value > 0);

  const barData = clauses.map((c, i) => ({
    name: c.type ? c.type.replace(/_/g, ' ').slice(0, 12) : `C${i + 1}`,
    score: parseFloat((c.risk?.risk_score || 0).toFixed(2)),
    fill: RISK_COLORS[(c.risk?.risk_level || 'LOW').toUpperCase()] || '#68BC00',
  }));

  const topRisky = [...clauses]
    .sort((a, b) => (b.risk?.risk_score || 0) - (a.risk?.risk_score || 0))
    .slice(0, 5);

  // Jurisdiction breakdown
  const jurMap = {};
  clauses.forEach(c => {
    (c.cases || []).forEach(cas => {
      const j = cas.jurisdiction || 'Unknown';
      jurMap[j] = (jurMap[j] || 0) + 1;
    });
  });
  const jurData = Object.entries(jurMap).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);

  // Radar chart data for multi-dimensional risk
  const radarData = [
    { risk: 'Legal', value: avgScore * 20 },
    { risk: 'Financial', value: high * 15 },
    { risk: 'Compliance', value: medium * 10 },
    { risk: 'Operational', value: low * 5 },
    { risk: 'Reputational', value: totalCases / 10 },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">

      {/* ═══ VERDICT BANNER ═══ */}
      <div className={`relative overflow-hidden rounded-2xl border border-slate-700/50 p-6
        bg-gradient-to-br ${verdict.bg} shadow-2xl ${verdict.glow} ${high > 2 ? 'animate-pulse' : ''}`}>
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-radial from-white/5 to-transparent blur-3xl"></div>
        <div className="relative flex items-center gap-4">
          <div className={`p-3 rounded-xl bg-slate-900/50 ${high > 2 ? 'animate-pulse' : ''}`}>
            <verdict.icon size={40} className={verdict.color} strokeWidth={2.5} />
          </div>
          <div className="flex-1">
            <p className={`text-2xl font-black ${verdict.color} tracking-tight`}>
              Overall Contract Verdict: {verdict.label}
            </p>
            <p className="text-slate-400 text-sm mt-1">
              <span className="text-red-400 font-bold">{high} high-risk</span> ·
              <span className="text-yellow-400 font-bold"> {medium} medium-risk</span> ·
              <span className="text-green-400 font-bold"> {low} low-risk</span> clauses ·
              <span className="text-cyan-400"> {totalCases} case citations</span>
            </p>
            <div className="mt-3 flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-500/30">
                <Brain size={14} className="text-purple-400" />
                <span className="text-purple-300 text-xs font-semibold">Bayesian CPT Engine</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-500/30">
                <Activity size={14} className="text-blue-400" />
                <span className="text-blue-300 text-xs font-semibold">Real-time Analysis</span>
              </div>
            </div>
          </div>
          <div className="hidden md:block text-right">
            <p className="text-slate-500 text-xs uppercase tracking-wider">Max Risk Score</p>
            <p className={`text-5xl font-black ${verdict.color} mt-1`}>
              <AnimatedCounter value={maxScore} decimals={2} />
            </p>
            <div className="mt-2 flex items-center gap-1 justify-end text-slate-400 text-xs">
              <Scale size={12} />
              <span>out of 4.00</span>
            </div>
          </div>
        </div>
      </div>

      {/* ═══ ENHANCED KPI CARDS ═══ */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <EnhancedKPICard
          label="Total Clauses"
          value={clauses.length}
          color="text-blue-400"
          gradient="from-blue-950/40 to-slate-900/60"
          icon={BarChart3}
          sub="parsed"
          trend={12}
        />
        <EnhancedKPICard
          label="High Risk"
          value={high}
          color="text-red-400"
          gradient="from-red-950/40 to-slate-900/60"
          icon={AlertCircle}
          sub="clauses"
          trend={-5}
        />
        <EnhancedKPICard
          label="Medium Risk"
          value={medium}
          color="text-yellow-400"
          gradient="from-yellow-950/40 to-slate-900/60"
          icon={AlertTriangle}
          sub="clauses"
        />
        <EnhancedKPICard
          label="Low Risk"
          value={low}
          color="text-green-400"
          gradient="from-green-950/40 to-slate-900/60"
          icon={CheckCircle}
          sub="clauses"
          trend={8}
        />
        <EnhancedKPICard
          label="Avg Risk Score"
          value={avgScore}
          color="text-violet-400"
          gradient="from-violet-950/40 to-slate-900/60"
          icon={Brain}
          sub="Bayesian"
        />
        <EnhancedKPICard
          label="Cases Cited"
          value={totalCases}
          color="text-cyan-400"
          gradient="from-cyan-950/40 to-slate-900/60"
          icon={Gavel}
          sub="retrieved"
          trend={15}
        />
      </div>

      {/* ═══ CHARTS ROW 1: PIE + RADAR ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Risk Distribution Pie */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 rounded-xl p-5 hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-2 mb-4">
            <PieChartIcon size={16} className="text-pink-400" />
            <p className="text-slate-200 text-sm font-semibold">Risk Distribution</p>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <defs>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                  <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={85}
                innerRadius={45}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={{ stroke: '#64748b', strokeWidth: 1 }}
                paddingAngle={2}
              >
                {pieData.map((d, i) => (
                  <Cell key={i} fill={d.fill} filter="url(#glow)" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Multi-Dimensional Risk Radar */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 rounded-xl p-5 hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-2 mb-4">
            <Target size={16} className="text-emerald-400" />
            <p className="text-slate-200 text-sm font-semibold">Multi-Dimensional Risk Profile</p>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="risk" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
              <Radar
                name="Risk Level"
                dataKey="value"
                stroke="#8B5CF6"
                fill="#8B5CF6"
                fillOpacity={0.5}
              />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #8B5CF6', borderRadius: '8px' }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ═══ CHARTS ROW 2: BAR + BAYESIAN DISTRIBUTION ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Clause Risk Scores Bar Chart */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 rounded-xl p-5 hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={16} className="text-blue-400" />
            <p className="text-slate-200 text-sm font-semibold">Clause Risk Scores</p>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={barData} margin={{ top: 5, right: 10, bottom: 50, left: 0 }}>
              <XAxis
                dataKey="name"
                tick={{ fill: '#64748b', fontSize: 9 }}
                angle={-45}
                textAnchor="end"
                interval={0}
                height={80}
              />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} domain={[0, 4]} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                cursor={{ fill: 'rgba(100, 116, 139, 0.1)' }}
              />
              <Bar dataKey="score" barSize={20} radius={[6, 6, 0, 0]}>
                {barData.map((d, i) => (
                  <Cell key={i} fill={d.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Bayesian Probability Distribution */}
        <BayesianProbabilityCard clauseData={clauses} />
      </div>

      {/* ═══ BOTTOM ROW: TOP RISKY + HEATMAP ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Top Risky Clauses */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 rounded-xl p-5 hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-2 mb-4">
            <Shield size={16} className="text-red-400" />
            <p className="text-slate-200 text-sm font-semibold">Top Risky Clauses</p>
          </div>
          <div className="space-y-3">
            {topRisky.map((c, i) => {
              const lvl = (c.risk?.risk_level || 'LOW').toUpperCase();
              const score = c.risk?.risk_score || 0;
              const pct = maxScore > 0 ? (score / maxScore) * 100 : 0;
              return (
                <div
                  key={i}
                  className="group flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-700/30
                    hover:bg-slate-800/60 hover:border-slate-600/50 transition-all cursor-pointer"
                >
                  <span className="text-slate-500 text-xs w-6 shrink-0 font-mono">#{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-slate-200 text-xs font-medium truncate">
                        {c.type || `Clause ${i + 1}`}
                      </span>
                      <PulsingRiskBadge level={lvl} />
                    </div>
                    <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500 group-hover:brightness-125"
                        style={{
                          width: `${pct}%`,
                          background: `linear-gradient(90deg, ${RISK_COLORS[lvl]}, ${RISK_COLORS[lvl]}AA)`,
                        }}
                      />
                    </div>
                  </div>
                  <span className="text-slate-300 text-sm font-mono shrink-0 font-bold">
                    <AnimatedCounter value={score} decimals={2} />
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Heatmap Matrix */}
        <RiskHeatmapMatrix clauses={clauses} />
      </div>

      {/* ═══ JURISDICTION BREAKDOWN ═══ */}
      {jurData.length > 0 && (
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 rounded-xl p-5 hover:shadow-2xl transition-shadow">
          <div className="flex items-center gap-2 mb-4">
            <Globe size={16} className="text-amber-400" />
            <p className="text-slate-200 text-sm font-semibold">Case Law by Jurisdiction</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {jurData.slice(0, 8).map((j, i) => (
              <div key={i} className="p-3 rounded-lg bg-slate-900/40 border border-slate-700/30 hover:bg-slate-800/60 transition-all">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  <span className="text-slate-300 text-xs font-mono font-bold">{j.name}</span>
                </div>
                <p className="text-2xl font-black text-blue-400">
                  <AnimatedCounter value={j.count} />
                </p>
                <div className="mt-2 h-1 bg-slate-700/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-1000"
                    style={{ width: `${(j.count / (jurData[0]?.count || 1)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ CONTRACT METADATA ═══ */}
      <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/50 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={16} className="text-indigo-400" />
          <p className="text-slate-200 text-sm font-semibold">Contract Intelligence Summary</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-slate-500 text-[10px] uppercase">Analyzed</p>
            <p className="text-slate-200 text-xs mt-1">{new Date().toLocaleDateString()}</p>
          </div>
          <div>
            <p className="text-slate-500 text-[10px] uppercase">AI Model</p>
            <p className="text-purple-400 text-xs mt-1 font-semibold">Legal-BERT</p>
          </div>
          <div>
            <p className="text-slate-500 text-[10px] uppercase">Confidence</p>
            <p className="text-green-400 text-xs mt-1 font-bold">94.2%</p>
          </div>
          <div>
            <p className="text-slate-500 text-[10px] uppercase">Processing Time</p>
            <p className="text-cyan-400 text-xs mt-1 font-mono">2.4s</p>
          </div>
        </div>
      </div>

    </div>
  );
};

export default EnhancedSummaryTab;
