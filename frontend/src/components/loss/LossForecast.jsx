import { TrendingUp, Calendar } from 'lucide-react';

const LossForecast = ({ forecast, varCvar, totalExposure }) => {
  const periods = [
    { key: '12m', label: '12 Months', icon: '📅' },
    { key: '24m', label: '24 Months', icon: '📆' },
    { key: '36m', label: '36 Months', icon: '🗓️' }
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-orange-400" />
          <h3 className="text-sm font-semibold text-white">Expected Loss Forecast</h3>
        </div>
        <Calendar className="w-4 h-4 text-slate-600" />
      </div>

      {/* Timeline Forecast Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {periods.map((period, index) => {
          const loss = forecast[period.key];
          const percentage = ((loss / totalExposure) * 100).toFixed(1);
          const isHighest = index === periods.length - 1;

          return (
            <div
              key={period.key}
              className={`relative p-4 rounded-lg border transition-all ${
                isHighest
                  ? 'bg-red-900/20 border-red-500/50'
                  : 'bg-slate-800/50 border-slate-700'
              }`}
            >
              {/* Period Indicator */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{period.icon}</span>
                <span className={`text-xs font-semibold px-2 py-1 rounded ${
                  isHighest ? 'bg-red-900/30 text-red-400' : 'bg-slate-700/50 text-slate-400'
                }`}>
                  {period.label}
                </span>
              </div>

              {/* Loss Amount */}
              <div className="mb-2">
                <p className={`text-xl font-bold ${
                  isHighest ? 'text-red-400' : 'text-orange-400'
                }`}>
                  ₹{(loss / 1_000_000).toFixed(0)}M
                </p>
                <p className="text-xs text-slate-500">
                  ${(loss / 83 / 1_000_000).toFixed(1)}M USD
                </p>
              </div>

              {/* Percentage Bar */}
              <div className="relative w-full h-2 bg-slate-700 rounded-full overflow-hidden mb-2">
                <div
                  className={`absolute top-0 left-0 h-full rounded-full transition-all duration-700 ${
                    isHighest
                      ? 'bg-gradient-to-r from-red-500 to-rose-600'
                      : 'bg-gradient-to-r from-orange-500 to-amber-500'
                  }`}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                />
              </div>

              <p className="text-xs text-slate-400">{percentage}% of exposure</p>

              {/* Arrow indicator for progression */}
              {index < periods.length - 1 && (
                <div className="absolute -right-2 top-1/2 transform -translate-y-1/2 z-10">
                  <div className="w-4 h-4 bg-slate-800 border-2 border-orange-500 rounded-full flex items-center justify-center">
                    <span className="text-orange-400 text-xs">→</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* VaR / CVaR Metrics */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800">
        <div className="p-3 bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-400 mb-1">95% VaR (Value at Risk)</p>
          <p className="text-lg font-bold text-amber-400">₹{(varCvar.var_95 / 1_000_000).toFixed(0)}M</p>
          <p className="text-xs text-slate-500 mt-1">Worst case (95% confidence)</p>
        </div>

        <div className="p-3 bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-400 mb-1">95% CVaR (Conditional VaR)</p>
          <p className="text-lg font-bold text-red-400">₹{(varCvar.cvar_95 / 1_000_000).toFixed(0)}M</p>
          <p className="text-xs text-slate-500 mt-1">Expected loss if VaR exceeded</p>
        </div>

        <div className="p-3 bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-400 mb-1">99% VaR (Tail Risk)</p>
          <p className="text-lg font-bold text-red-500">₹{(varCvar.var_99 / 1_000_000).toFixed(0)}M</p>
          <p className="text-xs text-slate-500 mt-1">Extreme scenario (99%)</p>
        </div>

        <div className="p-3 bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-400 mb-1">Expected Shortfall</p>
          <p className="text-lg font-bold text-orange-400">₹{(varCvar.expected_shortfall / 1_000_000).toFixed(0)}M</p>
          <p className="text-xs text-slate-500 mt-1">CVaR - VaR difference</p>
        </div>
      </div>

      {/* Info */}
      <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
        <p className="text-xs text-blue-400">
          <span className="font-semibold">Loss Forecast Model:</span> Projections based on historical risk patterns,
          portfolio composition, and Monte Carlo simulation (2,000 runs). VaR = maximum loss at confidence level; CVaR = expected loss beyond VaR.
        </p>
      </div>
    </div>
  );
};

export default LossForecast;
