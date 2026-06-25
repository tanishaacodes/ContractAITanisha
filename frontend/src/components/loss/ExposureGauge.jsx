import { Gauge, AlertTriangle } from 'lucide-react';

const ExposureGauge = ({ value, totalContracts, highRiskContracts }) => {
  // Determine risk level and color
  const getRiskLevel = () => {
    if (value >= 70) return { label: 'Critical', color: 'red', severity: 'CRITICAL' };
    if (value >= 50) return { label: 'High', color: 'orange', severity: 'HIGH' };
    if (value >= 30) return { label: 'Medium', color: 'yellow', severity: 'MEDIUM' };
    return { label: 'Low', color: 'green', severity: 'LOW' };
  };

  const risk = getRiskLevel();

  // Calculate rotation for needle (0-180 degrees)
  const rotation = (value / 100) * 180;

  // Get color classes
  const getColorClass = (color) => {
    switch (color) {
      case 'red': return 'from-red-500 to-rose-600';
      case 'orange': return 'from-orange-500 to-amber-600';
      case 'yellow': return 'from-yellow-500 to-amber-500';
      case 'green': return 'from-green-500 to-emerald-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Gauge className="w-5 h-5 text-red-400" />
          <h3 className="text-sm font-semibold text-white">Exposure Speedometer</h3>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
          risk.color === 'red' ? 'bg-red-900/30 text-red-400 border border-red-500/50' :
          risk.color === 'orange' ? 'bg-orange-900/30 text-orange-400 border border-orange-500/50' :
          risk.color === 'yellow' ? 'bg-yellow-900/30 text-yellow-400 border border-yellow-500/50' :
          'bg-green-900/30 text-green-400 border border-green-500/50'
        }`}>
          {risk.severity}
        </div>
      </div>

      {/* Gauge Visualization */}
      <div className="relative w-full h-48 flex items-end justify-center mb-6">
        <svg className="w-full h-full" viewBox="0 0 200 120">
          <defs>
            {/* Gradient for gauge */}
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="33%" stopColor="#fbbf24" />
              <stop offset="66%" stopColor="#f97316" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>

          {/* Background arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#1e293b"
            strokeWidth="20"
            strokeLinecap="round"
          />

          {/* Colored gauge arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="20"
            strokeLinecap="round"
          />

          {/* Needle */}
          <line
            x1="100"
            y1="100"
            x2="100"
            y2="35"
            stroke={risk.color === 'red' ? '#ef4444' : risk.color === 'orange' ? '#f97316' : risk.color === 'yellow' ? '#fbbf24' : '#10b981'}
            strokeWidth="4"
            strokeLinecap="round"
            transform={`rotate(${rotation - 90} 100 100)`}
            className="transition-transform duration-1000 ease-out"
          />

          {/* Center circle */}
          <circle cx="100" cy="100" r="8" fill="#0f172a" stroke="#475569" strokeWidth="2" />
        </svg>

        {/* Value display in center */}
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-center">
          <p className={`text-4xl font-bold ${
            risk.color === 'red' ? 'text-red-400' :
            risk.color === 'orange' ? 'text-orange-400' :
            risk.color === 'yellow' ? 'text-yellow-400' :
            'text-green-400'
          }`}>
            {value}%
          </p>
          <p className="text-xs text-slate-500 mt-1">{risk.label} Exposure</p>
        </div>
      </div>

      {/* Scale markers */}
      <div className="flex justify-between text-xs text-slate-600 mb-6 px-2">
        <span>0%</span>
        <span>25%</span>
        <span>50%</span>
        <span>75%</span>
        <span>100%</span>
      </div>

      {/* Portfolio Stats */}
      <div className="space-y-3 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Total Contracts</span>
          <span className="text-white font-semibold">{totalContracts}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">High Risk</span>
          <span className="text-red-400 font-semibold">{highRiskContracts}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Risk Ratio</span>
          <span className="text-orange-400 font-semibold">
            {totalContracts > 0 ? ((highRiskContracts / totalContracts) * 100).toFixed(1) : 0}%
          </span>
        </div>
      </div>

      {/* Warning if critical */}
      {risk.severity === 'CRITICAL' && (
        <div className="mt-4 p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-red-400">
              Critical exposure detected. Immediate portfolio review recommended.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExposureGauge;
