import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const RiskDeltaGauge = ({ value }) => {
  // value is percentage (-100 to +100)
  const getRiskLevel = () => {
    if (value < -10) return { label: 'Risk Reduced', color: 'green', icon: TrendingDown };
    if (value > 10) return { label: 'Risk Increased', color: 'red', icon: TrendingUp };
    return { label: 'No Change', color: 'slate', icon: Minus };
  };

  const risk = getRiskLevel();
  const Icon = risk.icon;

  // Calculate gauge position (map -100 to 0, +100 to 180 degrees)
  const rotation = ((value + 100) / 200) * 180;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-slate-400 uppercase tracking-wider">Risk Δ</p>
        <Icon className={`w-4 h-4 text-${risk.color}-400`} />
      </div>

      {/* Gauge Visualization */}
      <div className="relative w-full h-32 flex items-end justify-center mb-4">
        {/* Background Arc */}
        <svg className="w-full h-full" viewBox="0 0 200 100">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="50%" stopColor="#fbbf24" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>
          {/* Background track */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="#334155"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Colored gauge */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Needle */}
          <line
            x1="100"
            y1="90"
            x2="100"
            y2="30"
            stroke={risk.color === 'green' ? '#10b981' : risk.color === 'red' ? '#ef4444' : '#94a3b8'}
            strokeWidth="3"
            strokeLinecap="round"
            transform={`rotate(${rotation - 90} 100 90)`}
            className="transition-transform duration-700 ease-out"
          />
          {/* Center dot */}
          <circle cx="100" cy="90" r="5" fill="#1e293b" stroke="#475569" strokeWidth="2" />
        </svg>
      </div>

      {/* Value Display */}
      <div className="text-center">
        <p className={`text-3xl font-bold text-${risk.color}-400`}>
          {value > 0 ? '+' : ''}{value.toFixed(1)}%
        </p>
        <p className="text-xs text-slate-500 mt-1">{risk.label}</p>
      </div>

      {/* Scale Labels */}
      <div className="flex justify-between text-xs text-slate-600 mt-2">
        <span>-100%</span>
        <span>0%</span>
        <span>+100%</span>
      </div>
    </div>
  );
};

export default RiskDeltaGauge;
