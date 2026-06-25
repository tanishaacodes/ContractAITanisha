import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * MetricCard Component
 * Displays a single behavior metric with trend indicator
 */
const MetricCard = ({ label, value, trend, trendValue, icon: Icon, colorClass = 'bg-blue-500' }) => {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-emerald-400';
    if (trend === 'down') return 'text-red-400';
    return 'text-slate-400';
  };

  return (
    <div className="bg-slate-800/60 backdrop-blur-xl border border-cyan-500/20 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.1)] p-6 hover:shadow-[0_0_30px_rgba(6,182,212,0.2)] transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClass} shadow-[0_0_15px_rgba(6,182,212,0.5)]`}>
          {Icon && <Icon className="w-6 h-6 text-white" />}
        </div>
        {trend && (
          <div className="flex items-center gap-1">
            {getTrendIcon()}
            {trendValue && (
              <span className={`text-xs font-semibold ${getTrendColor()}`}>
                {trendValue}
              </span>
            )}
          </div>
        )}
      </div>

      <div>
        <p className="text-sm text-slate-400 font-medium mb-1">{label}</p>
        <p className="text-3xl font-bold text-white">{value}</p>
      </div>
    </div>
  );
};

export default MetricCard;
