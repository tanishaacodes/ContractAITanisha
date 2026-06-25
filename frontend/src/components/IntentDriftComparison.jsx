import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import {
  GitCompare, TrendingUp, TrendingDown, Minus,
  ChevronDown, ChevronUp, AlertTriangle, Info
} from 'lucide-react';

const IntentDriftComparison = ({ contractId, version1Id, version2Id }) => {
  const [driftData, setDriftData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    intents: true,
    obligations: false,
    rights: false
  });

  useEffect(() => {
    if (contractId && version1Id && version2Id) {
      compareDrift();
    }
  }, [contractId, version1Id, version2Id]);

  const compareDrift = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/contracts/${contractId}/versions/${version1Id}/compare/${version2Id}`
      );
      setDriftData(response.data.drift);
      setError(null);
    } catch (err) {
      setError('Failed to analyze drift');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const DriftScoreBadge = ({ score }) => {
    const percentage = (score * 100).toFixed(1);
    let color = 'bg-green-500';
    let label = 'Low Drift';

    if (score > 0.6) {
      color = 'bg-red-500';
      label = 'High Drift';
    } else if (score > 0.3) {
      color = 'bg-yellow-500';
      label = 'Moderate Drift';
    }

    return (
      <div className="flex items-center gap-2">
        <div className={`px-4 py-2 rounded-lg ${color} text-white font-bold`}>
          {percentage}%
        </div>
        <span className="text-slate-300">{label}</span>
      </div>
    );
  };

  const RiskDeltaIndicator = ({ riskDelta }) => {
    const { delta, direction, delta_percent } = riskDelta;

    const Icon = direction === 'INCREASED' ? TrendingUp :
                 direction === 'DECREASED' ? TrendingDown : Minus;
    const color = direction === 'INCREASED' ? 'text-red-400' :
                  direction === 'DECREASED' ? 'text-green-400' : 'text-slate-400';

    return (
      <div className={`flex items-center gap-2 ${color}`}>
        <Icon size={20} />
        <span className="font-semibold">
          {delta > 0 ? '+' : ''}{(delta * 100).toFixed(1)}%
        </span>
        <span className="text-sm">({delta_percent?.toFixed(1)}% change)</span>
      </div>
    );
  };

  const ChangeItem = ({ item, type }) => {
    let bgColor, icon, textColor;

    if (type === 'added') {
      bgColor = 'bg-green-900/30 border-green-700';
      textColor = 'text-green-400';
      icon = '+';
    } else if (type === 'removed') {
      bgColor = 'bg-red-900/30 border-red-700';
      textColor = 'text-red-400';
      icon = '-';
    } else {
      bgColor = 'bg-yellow-900/30 border-yellow-700';
      textColor = 'text-yellow-400';
      icon = '~';
    }

    return (
      <div className={`p-3 rounded border ${bgColor} mb-2`}>
        <div className="flex items-start gap-2">
          <div className={`font-bold text-lg ${textColor}`}>{icon}</div>
          <div className="flex-1">
            <div className="font-medium text-white">{item.intent_name || item.intent}</div>
            {item.action && (
              <div className="text-sm text-slate-300 mt-1">{item.action}</div>
            )}
            {item.entitlement && (
              <div className="text-sm text-slate-300 mt-1">{item.entitlement}</div>
            )}
            {item.clause && (
              <div className="text-xs text-slate-400 mt-1">Clause: {item.clause}</div>
            )}
            {item.party && (
              <div className="text-xs text-slate-400 mt-1">Party: {item.party}</div>
            )}
            {item.changes && (
              <div className="mt-2 space-y-1 text-xs">
                {Object.entries(item.changes).map(([key, change]) =>
                  change && (
                    <div key={key} className="text-slate-400">
                      <span className="font-semibold capitalize">{key}:</span>
                      <span className="line-through ml-1">{change.old || 'N/A'}</span>
                      <span className="mx-1">→</span>
                      <span className="text-yellow-300">{change.new || 'N/A'}</span>
                    </div>
                  )
                )}
              </div>
            )}
            {item.similarity && (
              <div className="text-xs text-slate-500 mt-1">
                Similarity: {(item.similarity * 100).toFixed(0)}%
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!driftData) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
        <Info className="mx-auto h-12 w-12 text-slate-500 mb-3" />
        <p className="text-slate-400">Select two versions to compare</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Overall Drift Score */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <GitCompare size={24} />
            Drift Analysis
          </h3>
          <DriftScoreBadge score={driftData.overall_drift_score} />
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-slate-400">From:</span>
            <span className="ml-2 text-white font-medium">
              v{driftData.version1.version_number}
            </span>
          </div>
          <div>
            <span className="text-slate-400">To:</span>
            <span className="ml-2 text-white font-medium">
              v{driftData.version2.version_number}
            </span>
          </div>
        </div>

        {/* Risk Delta */}
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Risk Change:</span>
            <RiskDeltaIndicator riskDelta={driftData.risk_delta} />
          </div>
        </div>

        {/* Summary */}
        <div className="mt-4 pt-4 border-t border-slate-700">
          <p className="text-sm text-slate-300">{driftData.summary}</p>
        </div>
      </div>

      {/* Intent Drift Section */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg">
        <div
          className="p-4 cursor-pointer flex items-center justify-between hover:bg-slate-700/50"
          onClick={() => setExpandedSections(prev => ({...prev, intents: !prev.intents}))}
        >
          <h4 className="font-semibold text-white">
            Intent Changes ({driftData.intent_drift.change_count})
          </h4>
          {expandedSections.intents ? <ChevronUp /> : <ChevronDown />}
        </div>

        {expandedSections.intents && (
          <div className="p-4 border-t border-slate-700 space-y-4">
            {driftData.intent_drift.added.length > 0 && (
              <div>
                <h5 className="text-green-400 font-medium mb-2">
                  Added ({driftData.intent_drift.added.length})
                </h5>
                {driftData.intent_drift.added.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="added" />
                ))}
              </div>
            )}

            {driftData.intent_drift.removed.length > 0 && (
              <div>
                <h5 className="text-red-400 font-medium mb-2">
                  Removed ({driftData.intent_drift.removed.length})
                </h5>
                {driftData.intent_drift.removed.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="removed" />
                ))}
              </div>
            )}

            {driftData.intent_drift.modified.length > 0 && (
              <div>
                <h5 className="text-yellow-400 font-medium mb-2">
                  Modified ({driftData.intent_drift.modified.length})
                </h5>
                {driftData.intent_drift.modified.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="modified" />
                ))}
              </div>
            )}

            {driftData.intent_drift.change_count === 0 && (
              <p className="text-slate-400 text-center py-4">No intent changes</p>
            )}
          </div>
        )}
      </div>

      {/* Obligation Drift Section */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg">
        <div
          className="p-4 cursor-pointer flex items-center justify-between hover:bg-slate-700/50"
          onClick={() => setExpandedSections(prev => ({...prev, obligations: !prev.obligations}))}
        >
          <h4 className="font-semibold text-white">
            Obligation Changes ({driftData.obligation_drift.change_count})
          </h4>
          {expandedSections.obligations ? <ChevronUp /> : <ChevronDown />}
        </div>

        {expandedSections.obligations && (
          <div className="p-4 border-t border-slate-700 space-y-4">
            {driftData.obligation_drift.added.length > 0 && (
              <div>
                <h5 className="text-green-400 font-medium mb-2">
                  Added ({driftData.obligation_drift.added.length})
                </h5>
                {driftData.obligation_drift.added.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="added" />
                ))}
              </div>
            )}

            {driftData.obligation_drift.removed.length > 0 && (
              <div>
                <h5 className="text-red-400 font-medium mb-2">
                  Removed ({driftData.obligation_drift.removed.length})
                </h5>
                {driftData.obligation_drift.removed.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="removed" />
                ))}
              </div>
            )}

            {driftData.obligation_drift.modified.length > 0 && (
              <div>
                <h5 className="text-yellow-400 font-medium mb-2">
                  Modified ({driftData.obligation_drift.modified.length})
                </h5>
                {driftData.obligation_drift.modified.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="modified" />
                ))}
              </div>
            )}

            {driftData.obligation_drift.change_count === 0 && (
              <p className="text-slate-400 text-center py-4">No obligation changes</p>
            )}
          </div>
        )}
      </div>

      {/* Rights Drift Section */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg">
        <div
          className="p-4 cursor-pointer flex items-center justify-between hover:bg-slate-700/50"
          onClick={() => setExpandedSections(prev => ({...prev, rights: !prev.rights}))}
        >
          <h4 className="font-semibold text-white">
            Rights Changes ({driftData.right_drift.change_count})
          </h4>
          {expandedSections.rights ? <ChevronUp /> : <ChevronDown />}
        </div>

        {expandedSections.rights && (
          <div className="p-4 border-t border-slate-700 space-y-4">
            {driftData.right_drift.added.length > 0 && (
              <div>
                <h5 className="text-green-400 font-medium mb-2">
                  Added ({driftData.right_drift.added.length})
                </h5>
                {driftData.right_drift.added.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="added" />
                ))}
              </div>
            )}

            {driftData.right_drift.removed.length > 0 && (
              <div>
                <h5 className="text-red-400 font-medium mb-2">
                  Removed ({driftData.right_drift.removed.length})
                </h5>
                {driftData.right_drift.removed.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="removed" />
                ))}
              </div>
            )}

            {driftData.right_drift.modified.length > 0 && (
              <div>
                <h5 className="text-yellow-400 font-medium mb-2">
                  Modified ({driftData.right_drift.modified.length})
                </h5>
                {driftData.right_drift.modified.map((item, idx) => (
                  <ChangeItem key={idx} item={item} type="modified" />
                ))}
              </div>
            )}

            {driftData.right_drift.change_count === 0 && (
              <p className="text-slate-400 text-center py-4">No rights changes</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntentDriftComparison;
