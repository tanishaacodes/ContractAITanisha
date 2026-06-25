import React, { useState } from 'react';
import {
  AlertTriangle, AlertCircle, CheckCircle, XCircle, Info, Lightbulb,
  Scale, TrendingDown, TrendingUp, ShieldAlert, Globe, BookOpen,
  Target, Zap, AlertOctagon, MessageSquare, BarChart3, Brain,
  Gavel, FileWarning, DollarSign, Clock, MapPin, Sparkles, Eye,
  ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis,
  Cell, LineChart, Line, AreaChart, Area
} from 'recharts';

const RISK_COLORS = {
  HIGH: '#F16667',
  MEDIUM: '#FFD86E',
  LOW: '#68BC00',
};

// ════════════════════════════════════════════════════════════════
// ENHANCED RISK BADGE WITH ANIMATIONS
// ════════════════════════════════════════════════════════════════
const EnhancedRiskBadge = ({ level, priority }) => {
  const config = {
    HIGH: {
      bg: 'from-red-600/30 to-red-900/30',
      border: 'border-red-500/50',
      text: 'text-red-300',
      glow: 'shadow-red-500/40',
      icon: AlertOctagon,
      pulse: priority ? 'animate-pulse' : '',
    },
    MEDIUM: {
      bg: 'from-yellow-600/30 to-yellow-900/30',
      border: 'border-yellow-500/50',
      text: 'text-yellow-300',
      glow: 'shadow-yellow-500/40',
      icon: AlertTriangle,
      pulse: '',
    },
    LOW: {
      bg: 'from-green-600/30 to-green-900/30',
      border: 'border-green-500/50',
      text: 'text-green-300',
      glow: 'shadow-green-500/40',
      icon: CheckCircle,
      pulse: '',
    },
  };

  const c = config[level] || config.LOW;
  const Icon = c.icon;

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl border-2
      bg-gradient-to-r ${c.bg} ${c.border} ${c.glow} shadow-xl ${c.pulse}`}>
      <Icon size={18} className={c.text} />
      <span className={`${c.text} font-bold text-sm tracking-wide`}>{level} RISK</span>
      {priority && (
        <span className="ml-2 px-2 py-0.5 bg-red-500 text-white text-[10px] font-bold rounded-full animate-pulse">
          PRIORITY
        </span>
      )}
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// CLAUSE TYPE INDICATOR
// ════════════════════════════════════════════════════════════════
const ClauseTypeIndicator = ({ type, confidence }) => {
  const typeIcons = {
    preamble: FileWarning,
    compound_interest: DollarSign,
    non_compete: ShieldAlert,
    liquidated_damages: AlertOctagon,
    indemnification: Scale,
    payment: DollarSign,
    confidentiality: Eye,
    termination: XCircle,
    ip_ownership: Lightbulb,
    governing_law: Gavel,
    data_protection: Globe,
  };

  const Icon = typeIcons[type] || Info;

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30">
      <Icon size={14} className="text-indigo-400" />
      <span className="text-indigo-300 text-xs font-semibold">
        {type.replace(/_/g, ' ').toUpperCase()}
      </span>
      <span className="text-indigo-500 text-[10px]">
        ({(confidence * 100).toFixed(0)}% match)
      </span>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// RISK METRICS DASHBOARD
// ════════════════════════════════════════════════════════════════
const RiskMetricsDashboard = ({ probability, impact, score }) => {
  const radarData = [
    { metric: 'Probability', value: probability, fullMark: 100 },
    { metric: 'Impact', value: impact * 10, fullMark: 100 },
    { metric: 'Risk Score', value: score * 25, fullMark: 100 },
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Probability */}
      <div className="bg-gradient-to-br from-purple-900/30 to-purple-950/50 border border-purple-500/30 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <Target size={16} className="text-purple-400" />
          <p className="text-purple-300 text-xs font-semibold uppercase">Probability</p>
        </div>
        <p className="text-3xl font-black text-purple-400">{probability}%</p>
        <div className="mt-3 h-2 bg-slate-700/50 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-1000"
            style={{ width: `${probability}%` }}
          />
        </div>
      </div>

      {/* Impact */}
      <div className="bg-gradient-to-br from-orange-900/30 to-orange-950/50 border border-orange-500/30 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <Zap size={16} className="text-orange-400" />
          <p className="text-orange-300 text-xs font-semibold uppercase">Impact</p>
        </div>
        <p className="text-3xl font-black text-orange-400">{impact.toFixed(1)}</p>
        <p className="text-orange-500 text-[10px] mt-1">out of 10.0</p>
        <div className="mt-2 h-2 bg-slate-700/50 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-orange-500 to-red-500 transition-all duration-1000"
            style={{ width: `${impact * 10}%` }}
          />
        </div>
      </div>

      {/* Risk Score */}
      <div className="bg-gradient-to-br from-red-900/30 to-red-950/50 border border-red-500/30 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 size={16} className="text-red-400" />
          <p className="text-red-300 text-xs font-semibold uppercase">Risk Score</p>
        </div>
        <p className="text-3xl font-black text-red-400">{score.toFixed(2)}</p>
        <p className="text-red-500 text-[10px] mt-1">out of 4.00</p>
        <div className="mt-2 h-2 bg-slate-700/50 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-1000 ${
              score >= 3.0 ? 'bg-gradient-to-r from-red-500 to-red-700 animate-pulse' :
              score >= 1.2 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
              'bg-gradient-to-r from-green-500 to-emerald-500'
            }`}
            style={{ width: `${(score / 4) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// ACTIONABLE INSIGHTS PANEL
// ════════════════════════════════════════════════════════════════
const ActionableInsightsPanel = ({ insights }) => {
  const [expanded, setExpanded] = useState(true);

  if (!insights) return null;

  return (
    <div className="space-y-4">
      {/* Risk Explanation */}
      {insights.risk_explanation && (
        <div className="bg-gradient-to-r from-blue-900/20 to-indigo-900/20 border border-blue-500/30 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <Brain size={20} className="text-blue-400" />
            <h3 className="text-blue-300 font-bold text-sm uppercase tracking-wide">AI Analysis</h3>
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">{insights.risk_explanation}</p>
        </div>
      )}

      {/* Specific Issues */}
      {insights.specific_issues && insights.specific_issues.length > 0 && (
        <div className="bg-gradient-to-r from-red-900/20 to-orange-900/20 border border-red-500/30 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle size={20} className="text-red-400" />
            <h3 className="text-red-300 font-bold text-sm uppercase tracking-wide">Specific Issues Identified</h3>
          </div>
          <ul className="space-y-2">
            {insights.specific_issues.map((issue, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <XCircle size={14} className="text-red-400 mt-1 shrink-0" />
                <span className="text-slate-300 text-sm">{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {insights.recommendations && insights.recommendations.length > 0 && (
        <div className="bg-gradient-to-r from-green-900/20 to-emerald-900/20 border border-green-500/30 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <Lightbulb size={20} className="text-green-400" />
            <h3 className="text-green-300 font-bold text-sm uppercase tracking-wide">Recommendations</h3>
          </div>
          <ul className="space-y-2">
            {insights.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <CheckCircle size={14} className="text-green-400 mt-1 shrink-0" />
                <span className="text-slate-300 text-sm">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Negotiation Points */}
      {insights.negotiation_points && insights.negotiation_points.length > 0 && (
        <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 border border-purple-500/30 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <MessageSquare size={20} className="text-purple-400" />
            <h3 className="text-purple-300 font-bold text-sm uppercase tracking-wide">Negotiation Strategy</h3>
          </div>
          <ul className="space-y-2">
            {insights.negotiation_points.map((point, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <Sparkles size={14} className="text-purple-400 mt-1 shrink-0" />
                <span className="text-slate-300 text-sm">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Jurisdictional Concerns */}
      {insights.jurisdictional_concerns && insights.jurisdictional_concerns.length > 0 && (
        <div className="bg-gradient-to-r from-amber-900/20 to-yellow-900/20 border border-amber-500/30 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <Globe size={20} className="text-amber-400" />
            <h3 className="text-amber-300 font-bold text-sm uppercase tracking-wide">Jurisdictional Analysis</h3>
          </div>
          <ul className="space-y-2">
            {insights.jurisdictional_concerns.map((concern, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <MapPin size={14} className="text-amber-400 mt-1 shrink-0" />
                <span className="text-slate-300 text-sm">{concern}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Benchmark Comparison */}
      {insights.benchmark && Object.keys(insights.benchmark).length > 0 && (
        <div className="bg-gradient-to-r from-cyan-900/20 to-blue-900/20 border border-cyan-500/30 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 size={20} className="text-cyan-400" />
            <h3 className="text-cyan-300 font-bold text-sm uppercase tracking-wide">Market Benchmark</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(insights.benchmark).map(([key, value]) => (
              <div key={key} className="bg-slate-800/50 rounded-lg p-3">
                <p className="text-slate-500 text-[10px] uppercase tracking-wide mb-1">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="text-slate-200 text-sm font-semibold">{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// ENHANCED CASE LAW CARD
// ════════════════════════════════════════════════════════════════
const EnhancedCaseLawCard = ({ caseData }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-700/50 rounded-xl p-4
      hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/20 transition-all cursor-pointer"
      onClick={() => setExpanded(!expanded)}>

      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Gavel size={14} className="text-blue-400" />
            <h4 className="text-blue-300 font-bold text-sm">{caseData?.court || 'Unknown Court'} - {caseData?.year || 'N/A'}</h4>
            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 text-[10px] rounded-full">
              {caseData?.jurisdiction || 'N/A'}
            </span>
          </div>
          <p className="text-slate-300 text-xs font-mono">{caseData?.citation || 'No citation available'}</p>
        </div>
        {expanded ? <ChevronUp size={16} className="text-slate-500" /> : <ChevronDown size={16} className="text-slate-500" />}
      </div>

      {/* Topics */}
      <div className="flex flex-wrap gap-1.5 mt-3">
        {(caseData?.topics || []).map((topic, idx) => (
          <span key={idx} className="px-2 py-1 bg-purple-500/20 text-purple-300 text-[10px] rounded-md border border-purple-500/30">
            {topic}
          </span>
        ))}
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-3">
          <div>
            <p className="text-slate-500 text-[10px] uppercase tracking-wide mb-1">Relevance</p>
            <p className="text-slate-300 text-xs leading-relaxed">{caseData?.relevance || 'No relevance information available'}</p>
          </div>
          <div>
            <p className="text-slate-500 text-[10px] uppercase tracking-wide mb-1">Key Finding</p>
            <p className="text-green-300 text-xs leading-relaxed italic">"{caseData?.key_finding || 'No key finding available'}"</p>
          </div>
        </div>
      )}
    </div>
  );
};

// ════════════════════════════════════════════════════════════════
// MAIN ENHANCED CLAUSE REVIEW COMPONENT
// ════════════════════════════════════════════════════════════════
const EnhancedClauseReview = ({ clause, index }) => {
  const [showFullText, setShowFullText] = useState(false);

  // REAL enhanced data from backend (enhanced_clause_analyzer.py)
  const enhancedData = {
    clause_type: clause?.enhanced_clause_type || clause?.clause_type || 'general',
    clause_type_confidence: clause?.clause_type_confidence || 0.5,
    risk_score: clause?.risk?.risk_score || 0,
    risk_level: clause?.risk?.risk_level || 'LOW',
    probability: clause?.risk?.probability || 0,
    impact: clause?.risk?.impact || 0,
    high_priority: clause?.high_priority || false,
    case_law: clause?.cases || [],
    insights: clause?.insights || {
      risk_explanation: "",
      specific_issues: [],
      recommendations: [],
      negotiation_points: [],
      jurisdictional_concerns: [],
      benchmark: {},
    },
    enforceability_concerns: clause?.enforceability_concerns || false,
    penalty_risk: clause?.penalty_risk || false,
    regulatory_risk: clause?.regulatory_risk || false,
  };

  const clauseText = clause?.text || clause?.clause_text || "Clause text not available";
  const truncatedText = clauseText.length > 400 ? clauseText.slice(0, 400) + '...' : clauseText;

  return (
    <div className="bg-gradient-to-br from-slate-900/80 to-slate-950/80 border border-slate-700/50 rounded-2xl p-6 shadow-2xl">

      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-slate-500 text-sm font-mono">#{index + 1}</span>
            <EnhancedRiskBadge level={enhancedData.risk_level} priority={enhancedData.high_priority} />
            <ClauseTypeIndicator type={enhancedData.clause_type} confidence={enhancedData.clause_type_confidence} />
          </div>
          <h3 className="text-slate-200 text-lg font-bold">
            {clause?.type?.replace(/_/g, ' ') || `Clause ${index + 1}`}
          </h3>
        </div>
      </div>

      {/* Risk Metrics Dashboard */}
      <RiskMetricsDashboard
        probability={enhancedData.probability}
        impact={enhancedData.impact}
        score={enhancedData.risk_score}
      />

      {/* Clause Text */}
      <div className="mt-6 bg-slate-800/40 border border-slate-700/30 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileWarning size={14} className="text-slate-400" />
            <p className="text-slate-400 text-xs font-semibold uppercase">Clause Text</p>
          </div>
          <button
            onClick={() => setShowFullText(!showFullText)}
            className="text-blue-400 text-xs hover:text-blue-300 transition-colors flex items-center gap-1">
            {showFullText ? 'Show Less' : 'Show Full Text'}
            {showFullText ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </div>
        <p className="text-slate-300 text-sm leading-relaxed font-mono">
          {showFullText ? clauseText : truncatedText}
        </p>
      </div>

      {/* Actionable Insights */}
      <div className="mt-6">
        <ActionableInsightsPanel insights={enhancedData.insights} />
      </div>

      {/* Case Law */}
      {enhancedData.case_law && enhancedData.case_law.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-4">
            <Scale size={18} className="text-amber-400" />
            <h3 className="text-slate-200 font-bold text-sm uppercase tracking-wide">Supporting Case Law</h3>
            <span className="px-2 py-1 bg-amber-500/20 text-amber-300 text-[10px] rounded-full">
              {enhancedData.case_law.length} cases
            </span>
          </div>
          <div className="space-y-3">
            {enhancedData.case_law.map((caseData, idx) => (
              <EnhancedCaseLawCard key={idx} caseData={caseData} />
            ))}
          </div>
        </div>
      )}

      {/* Special Flags */}
      {(enhancedData.high_priority || enhancedData.enforceability_concerns || enhancedData.penalty_risk) && (
        <div className="mt-6 p-4 bg-red-900/20 border-2 border-red-500/50 rounded-xl">
          <div className="flex items-center gap-2 mb-3">
            <AlertOctagon size={18} className="text-red-400" />
            <h3 className="text-red-300 font-bold text-sm uppercase">Critical Warnings</h3>
          </div>
          <div className="space-y-2">
            {enhancedData.high_priority && (
              <p className="text-red-300 text-xs">⚠️ HIGH PRIORITY - Requires immediate legal review</p>
            )}
            {enhancedData.enforceability_concerns && (
              <p className="text-red-300 text-xs">⚠️ ENFORCEABILITY RISK - May be void in certain jurisdictions</p>
            )}
            {enhancedData.penalty_risk && (
              <p className="text-red-300 text-xs">⚠️ PENALTY CLAUSE RISK - May be struck down by courts</p>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default EnhancedClauseReview;
