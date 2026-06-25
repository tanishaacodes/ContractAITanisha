import { Scale, AlertTriangle, FileEdit, Lightbulb, Shield, MapPin } from 'lucide-react';

const PlaybookAnalysis = ({ clause, playbook }) => {
  if (!clause || !playbook) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
        <div className="flex items-center justify-center h-[600px]">
          <div className="text-center">
            <Scale className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">Select a clause to view legal playbook</p>
            <p className="text-slate-500 text-xs mt-1">Click on a clause from the list to analyze</p>
          </div>
        </div>
      </div>
    );
  }

  const getRiskColor = (riskLevel) => {
    const colors = {
      HIGH: 'text-red-400',
      MEDIUM: 'text-orange-400',
      LOW: 'text-green-400'
    };
    return colors[riskLevel] || colors.MEDIUM;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-semibold text-white">Legal Playbook Analysis</h3>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-semibold ${getRiskColor(playbook.risk_level)}`}>
          {playbook.risk_level} RISK
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="space-y-6 max-h-[550px] overflow-y-auto pr-2">
        {/* Clause Title */}
        <div>
          <h4 className="text-lg font-bold text-white mb-2">{playbook.clause_name}</h4>
          <div className="p-3 bg-slate-800/50 rounded-lg">
            <p className="text-xs text-slate-300">{clause.text}</p>
          </div>
        </div>

        {/* Risk Explanation */}
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h5 className="text-sm font-semibold text-red-400">Risk Explanation</h5>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            {playbook.risk_explanation}
          </p>
        </div>

        {/* Recommended Rewrite */}
        <div className="p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-3">
            <FileEdit className="w-5 h-5 text-green-400" />
            <h5 className="text-sm font-semibold text-green-400">Recommended Rewrite</h5>
          </div>
          <div className="p-3 bg-slate-800/50 rounded-lg">
            <p className="text-sm text-slate-200 leading-relaxed font-mono">
              {playbook.recommended_rewrite}
            </p>
          </div>
        </div>

        {/* Fallback Positions */}
        <div className="p-4 bg-orange-900/20 border border-orange-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-orange-400" />
            <h5 className="text-sm font-semibold text-orange-400">Fallback Positions</h5>
          </div>
          <div className="space-y-2">
            {playbook.fallbacks && playbook.fallbacks.length > 0 ? (
              playbook.fallbacks.map((fallback, index) => (
                <div key={index} className="flex items-start gap-2">
                  <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0 mt-0.5">
                    {index + 1}
                  </div>
                  <p className="text-sm text-slate-300">{fallback}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-400">No fallback positions available</p>
            )}
          </div>
        </div>

        {/* Negotiation Strategy */}
        <div className="p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-blue-400" />
            <h5 className="text-sm font-semibold text-blue-400">Negotiation Strategy</h5>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            {playbook.negotiation_strategy}
          </p>
        </div>

        {/* Jurisdiction Guidance */}
        {playbook.jurisdiction_guidance && (
          <div className="p-4 bg-purple-900/20 border border-purple-500/30 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="w-5 h-5 text-purple-400" />
              <h5 className="text-sm font-semibold text-purple-400">Jurisdiction-Specific Guidance</h5>
            </div>
            {Object.entries(playbook.jurisdiction_guidance).map(([jurisdiction, guidance]) => (
              <div key={jurisdiction}>
                <p className="text-xs text-purple-400 font-semibold mb-2">{jurisdiction}</p>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {guidance}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500 text-center">
          AI-generated legal strategy • Review with qualified counsel
        </p>
      </div>
    </div>
  );
};

export default PlaybookAnalysis;
