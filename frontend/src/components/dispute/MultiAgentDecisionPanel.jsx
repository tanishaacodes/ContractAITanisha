/**
 * MultiAgentDecisionPanel.jsx
 * ============================
 * Displays decisions from 5 autonomous negotiation agents:
 * - Buyer Agent
 * - Supplier Agent
 * - Regulator Agent
 * - Risk Agent
 * - Finance Agent
 */

import { useState } from "react";
import {
  User, Building2, Shield, AlertTriangle, DollarSign,
  TrendingDown, TrendingUp, ArrowRight, CheckCircle, XCircle,
  ChevronDown, ChevronUp
} from "lucide-react";

const AGENT_CONFIGS = {
  buyer: {
    name: "Buyer Agent",
    icon: User,
    color: "#4C8EDA",
    objective: "Minimize cost, maximize protection",
    strategy: "Aggressive cost reduction"
  },
  supplier: {
    name: "Supplier Agent",
    icon: Building2,
    color: "#F79767",
    objective: "Maximize revenue, minimize liability",
    strategy: "Defensive profit maximization"
  },
  regulator: {
    name: "Regulator Agent",
    icon: Shield,
    color: "#9333EA",
    objective: "Ensure compliance, fair terms",
    strategy: "Balanced regulatory oversight"
  },
  risk: {
    name: "Risk Agent",
    icon: AlertTriangle,
    color: "#F16667",
    objective: "Minimize dispute probability",
    strategy: "Conservative risk mitigation"
  },
  finance: {
    name: "Finance Agent",
    icon: DollarSign,
    color: "#68BC00",
    objective: "Optimize cash flow, reduce exposure",
    strategy: "Financial optimization"
  }
};

// Agent Decision Card
const AgentCard = ({ agentType, decision, expanded, onToggle }) => {
  const config = AGENT_CONFIGS[agentType] || AGENT_CONFIGS.buyer;
  const Icon = config.icon;

  return (
    <div
      className="rounded-lg border p-4 transition-all hover:shadow-lg"
      style={{
        background: `linear-gradient(135deg, ${config.color}15 0%, ${config.color}05 100%)`,
        borderColor: `${config.color}40`,
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center"
            style={{ background: `${config.color}20` }}
          >
            <Icon size={20} style={{ color: config.color }} />
          </div>
          <div>
            <div className="font-bold text-slate-200">{config.name}</div>
            <div className="text-xs text-slate-400">{config.strategy}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {decision?.approved ? (
            <CheckCircle size={16} className="text-green-400" />
          ) : (
            <XCircle size={16} className="text-red-400" />
          )}
          {expanded ? (
            <ChevronUp size={16} className="text-slate-400" />
          ) : (
            <ChevronDown size={16} className="text-slate-400" />
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && decision && (
        <div className="mt-4 space-y-3">
          {/* Objective */}
          <div className="text-xs text-slate-400">
            <div className="font-semibold mb-1">Objective:</div>
            <div>{config.objective}</div>
          </div>

          {/* Actions Taken */}
          {decision.actions && decision.actions.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-300 mb-2">
                Actions Taken:
              </div>
              <div className="space-y-2">
                {decision.actions.map((action, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 text-xs bg-slate-800 rounded p-2"
                  >
                    {action.type === "increase" ? (
                      <TrendingUp size={12} className="text-green-400" />
                    ) : (
                      <TrendingDown size={12} className="text-red-400" />
                    )}
                    <span className="text-slate-300">{action.clause}:</span>
                    <span className="font-semibold" style={{ color: config.color }}>
                      {action.description}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rationale */}
          {decision.rationale && (
            <div className="text-xs">
              <div className="font-semibold text-slate-300 mb-1">Rationale:</div>
              <div className="text-slate-400 italic">{decision.rationale}</div>
            </div>
          )}

          {/* Impact */}
          {decision.impact && (
            <div className="grid grid-cols-2 gap-2 text-xs">
              {decision.impact.disputeChange !== undefined && (
                <div className="bg-slate-800 rounded p-2">
                  <div className="text-slate-400">Dispute Risk Change:</div>
                  <div
                    className={`font-bold ${
                      decision.impact.disputeChange > 0
                        ? "text-red-400"
                        : "text-green-400"
                    }`}
                  >
                    {decision.impact.disputeChange > 0 ? "+" : ""}
                    {decision.impact.disputeChange}%
                  </div>
                </div>
              )}
              {decision.impact.costChange !== undefined && (
                <div className="bg-slate-800 rounded p-2">
                  <div className="text-slate-400">Cost Impact:</div>
                  <div
                    className={`font-bold ${
                      decision.impact.costChange > 0
                        ? "text-red-400"
                        : "text-green-400"
                    }`}
                  >
                    {decision.impact.costChange > 0 ? "+" : ""}$
                    {decision.impact.costChange.toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Clause Comparison Table
const ClauseComparisonTable = ({ original, negotiated }) => {
  if (!original || !negotiated) return null;

  const clauses = Object.keys(original);

  return (
    <div className="mt-6">
      <div className="text-lg font-bold mb-4 text-slate-200">
        Contract Comparison
      </div>
      <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
        <table className="w-full text-sm">
          <thead className="bg-slate-900">
            <tr>
              <th className="text-left p-3 text-slate-400 font-semibold">
                Clause
              </th>
              <th className="text-left p-3 text-slate-400 font-semibold">
                Original
              </th>
              <th className="text-center p-3 text-slate-400 font-semibold">
                <ArrowRight size={16} className="inline" />
              </th>
              <th className="text-left p-3 text-slate-400 font-semibold">
                Negotiated
              </th>
              <th className="text-left p-3 text-slate-400 font-semibold">
                Change
              </th>
            </tr>
          </thead>
          <tbody>
            {clauses.map((clause, idx) => {
              const origValue = original[clause];
              const negValue = negotiated[clause];
              const changed = origValue !== negValue;

              return (
                <tr
                  key={idx}
                  className={`border-t border-slate-700 ${
                    changed ? "bg-blue-900/20" : ""
                  }`}
                >
                  <td className="p-3 text-slate-300 font-semibold capitalize">
                    {clause.replace(/_/g, " ")}
                  </td>
                  <td className="p-3 text-slate-400">{origValue}</td>
                  <td className="text-center p-3">
                    {changed && <ArrowRight size={14} className="text-blue-400 mx-auto" />}
                  </td>
                  <td className="p-3 text-slate-200 font-semibold">
                    {negValue}
                  </td>
                  <td className="p-3">
                    {changed ? (
                      <span className="text-xs px-2 py-1 bg-blue-600 text-white rounded">
                        Modified
                      </span>
                    ) : (
                      <span className="text-xs text-slate-500">No change</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Main Component
export default function MultiAgentDecisionPanel({ agentDecisions, originalContract, negotiatedContract }) {
  const [expandedAgents, setExpandedAgents] = useState(new Set(["buyer", "supplier"]));

  const toggleAgent = (agentType) => {
    setExpandedAgents((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(agentType)) {
        newSet.delete(agentType);
      } else {
        newSet.add(agentType);
      }
      return newSet;
    });
  };

  if (!agentDecisions) {
    return (
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-8 text-center">
        <div className="text-slate-400 mb-2">No agent decisions available</div>
        <div className="text-sm text-slate-500">
          Run multi-agent negotiation to see agent decisions
        </div>
      </div>
    );
  }

  const agents = Object.keys(AGENT_CONFIGS);
  const approvedCount = agents.filter(
    (a) => agentDecisions[a]?.approved
  ).length;

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-xs text-slate-400 mb-1">Total Agents</div>
          <div className="text-2xl font-bold text-slate-200">5</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-xs text-slate-400 mb-1">Approved</div>
          <div className="text-2xl font-bold text-green-400">{approvedCount}</div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-xs text-slate-400 mb-1">Rejected</div>
          <div className="text-2xl font-bold text-red-400">
            {5 - approvedCount}
          </div>
        </div>
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="text-xs text-slate-400 mb-1">Consensus</div>
          <div className="text-2xl font-bold text-blue-400">
            {Math.round((approvedCount / 5) * 100)}%
          </div>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="space-y-3">
        <div className="text-lg font-bold text-slate-200 mb-4">
          Agent Decisions
        </div>
        {agents.map((agentType) => (
          <AgentCard
            key={agentType}
            agentType={agentType}
            decision={agentDecisions[agentType]}
            expanded={expandedAgents.has(agentType)}
            onToggle={() => toggleAgent(agentType)}
          />
        ))}
      </div>

      {/* Clause Comparison */}
      {originalContract && negotiatedContract && (
        <ClauseComparisonTable
          original={originalContract}
          negotiated={negotiatedContract}
        />
      )}
    </div>
  );
}
