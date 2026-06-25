import { FileText, AlertTriangle, CheckCircle, ChevronRight } from 'lucide-react';

const ClauseTable = ({ clauses, selectedClause, onClauseSelect, loading }) => {
  const getRiskBadge = (riskLevel) => {
    const config = {
      HIGH: { color: 'red', icon: AlertTriangle, label: 'HIGH' },
      MEDIUM: { color: 'orange', icon: AlertTriangle, label: 'MEDIUM' },
      LOW: { color: 'green', icon: CheckCircle, label: 'LOW' }
    };

    const risk = config[riskLevel] || config.MEDIUM;
    const Icon = risk.icon;

    return (
      <div className={`flex items-center gap-1 px-2 py-1 bg-${risk.color}-900/30 border border-${risk.color}-500/50 rounded-full`}>
        <Icon className={`w-3 h-3 text-${risk.color}-400`} />
        <span className={`text-xs font-semibold text-${risk.color}-400`}>{risk.label}</span>
      </div>
    );
  };

  const getRiskColor = (riskLevel) => {
    const colors = {
      HIGH: 'border-red-500/50 bg-red-900/10',
      MEDIUM: 'border-orange-500/50 bg-orange-900/10',
      LOW: 'border-green-500/50 bg-green-900/10'
    };
    return colors[riskLevel] || colors.MEDIUM;
  };

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
        <div className="flex items-center justify-center h-[600px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
            <p className="text-slate-400 text-sm">Loading clauses...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-semibold text-white">High-Risk Clauses</h3>
        </div>
        <div className="px-3 py-1 bg-purple-900/30 border border-purple-500/50 rounded-full">
          <span className="text-xs font-semibold text-purple-400">{clauses.length} Clauses</span>
        </div>
      </div>

      {/* Clause List */}
      <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
        {clauses.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No clauses found</p>
            <p className="text-slate-500 text-xs mt-1">Upload contracts to analyze clauses</p>
          </div>
        ) : (
          clauses.map((clause) => (
            <div
              key={clause.id}
              onClick={() => onClauseSelect(clause)}
              className={`group relative p-4 rounded-lg border-2 transition-all cursor-pointer
                ${selectedClause?.id === clause.id
                  ? 'border-purple-500 bg-purple-900/20'
                  : `border-slate-700 hover:${getRiskColor(clause.risk_level)}`
                }
              `}
            >
              {/* Risk Badge */}
              <div className="absolute -top-2 -left-2">
                {getRiskBadge(clause.risk_level)}
              </div>

              {/* Clause Info */}
              <div className="mb-3 mt-2">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold text-white group-hover:text-purple-400 transition line-clamp-2">
                    {clause.clause_name}
                  </h4>
                  <ChevronRight className={`w-4 h-4 flex-shrink-0 mt-1 transition ${
                    selectedClause?.id === clause.id ? 'text-purple-400' : 'text-slate-600 group-hover:text-purple-400'
                  }`} />
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Contract: {clause.contract_name}
                </p>
              </div>

              {/* Clause Text Preview */}
              <div className="p-3 bg-slate-800/50 rounded-lg mb-3">
                <p className="text-xs text-slate-300 line-clamp-3">
                  {clause.text}
                </p>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span>Type: {clause.clause_type}</span>
                {clause.jurisdiction && (
                  <>
                    <span>•</span>
                    <span>{clause.jurisdiction}</span>
                  </>
                )}
              </div>

              {/* Selection Indicator */}
              {selectedClause?.id === clause.id && (
                <div className="absolute right-2 top-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Filter Info */}
      {clauses.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <p className="text-xs text-slate-500">
            Showing clauses requiring legal review and action
          </p>
        </div>
      )}
    </div>
  );
};

export default ClauseTable;
