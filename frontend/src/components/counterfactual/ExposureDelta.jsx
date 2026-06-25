import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';

const ExposureDelta = ({ data }) => {
  const isPositive = data.avg_loss_inr > 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-slate-400 uppercase tracking-wider">Exposure Δ</p>
        {isPositive ? (
          <TrendingUp className="w-4 h-4 text-red-400" />
        ) : (
          <TrendingDown className="w-4 h-4 text-green-400" />
        )}
      </div>

      {/* Primary Value */}
      <div className="mb-3">
        <div className="flex items-baseline gap-2">
          <span className="text-xs text-slate-500">₹</span>
          <p className={`text-2xl font-bold ${isPositive ? 'text-red-400' : 'text-green-400'}`}>
            {isPositive ? '+' : ''}{Math.abs(data.avg_loss_inr).toLocaleString()}
          </p>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          ${isPositive ? '+' : ''}{Math.abs(data.avg_loss_usd).toLocaleString()} USD
        </p>
      </div>

      {/* VaR Display */}
      <div className="pt-3 border-t border-slate-800">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-slate-400">95% VaR</span>
          <span className="text-amber-400 font-semibold">
            ₹{data.percentile_95_inr.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">99% VaR</span>
          <span className="text-red-400 font-semibold">
            ₹{data.percentile_99_inr.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Info */}
      <div className="mt-3 pt-3 border-t border-slate-800">
        <p className="text-xs text-slate-500">
          Expected loss change from modifications
        </p>
      </div>
    </div>
  );
};

export default ExposureDelta;
