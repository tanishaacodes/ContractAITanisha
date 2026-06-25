import { Shield, ExternalLink, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const UnlimitedWatchlist = ({ contracts }) => {
  const navigate = useNavigate();

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-red-400" />
          <h3 className="text-sm font-semibold text-white">Unlimited Liability Watchlist</h3>
        </div>
        <div className="px-3 py-1 bg-red-900/30 border border-red-500/50 rounded-full">
          <span className="text-xs font-semibold text-red-400">{contracts.length} Contracts</span>
        </div>
      </div>

      {/* Watchlist Items */}
      <div className="space-y-3 mb-6 max-h-[400px] overflow-y-auto">
        {contracts.length === 0 ? (
          <div className="text-center py-12">
            <Shield className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No unlimited liability contracts</p>
            <p className="text-slate-500 text-xs mt-1">Your portfolio is protected</p>
          </div>
        ) : (
          contracts.map((contract, index) => (
            <div
              key={contract.id}
              className="group relative p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-red-500/50 rounded-lg transition-all cursor-pointer"
              onClick={() => navigate(`/contracts/${contract.id}`)}
            >
              {/* Rank Badge */}
              <div className="absolute -left-2 -top-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white">
                {index + 1}
              </div>

              {/* Contract Info */}
              <div className="mb-3">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold text-white group-hover:text-red-400 transition line-clamp-1">
                    {contract.name}
                  </h4>
                  <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-red-400 transition flex-shrink-0 mt-1" />
                </div>
              </div>

              {/* Value */}
              <div className="mb-3">
                <p className="text-lg font-bold text-red-400">₹{contract.value_inr.toLocaleString()}</p>
                <p className="text-xs text-slate-500">${contract.value_usd.toLocaleString()} USD</p>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-orange-400" />
                  Risk: {contract.risk_score}
                </span>
              </div>

              {/* Warning indicator */}
              <div className="absolute right-2 top-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Summary Stats */}
      {contracts.length > 0 && (
        <>
          <div className="pt-4 border-t border-slate-800 mb-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-slate-400 mb-1">Total Exposure</p>
                <p className="text-white font-semibold">
                  ₹{contracts.reduce((sum, c) => sum + c.value_inr, 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Avg Risk Score</p>
                <p className="text-red-400 font-semibold">
                  {(contracts.reduce((sum, c) => sum + c.risk_score, 0) / contracts.length).toFixed(0)}
                </p>
              </div>
            </div>
          </div>

          {/* Warning Banner */}
          <div className="p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-red-400 font-semibold mb-1">ACTION REQUIRED</p>
                <p className="text-xs text-slate-400">
                  These contracts have unlimited liability clauses. Review and negotiate caps immediately to limit exposure.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default UnlimitedWatchlist;
