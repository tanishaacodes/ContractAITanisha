import { Shield, TrendingUp, TrendingDown } from 'lucide-react';

export default function ExposureCard({ title, value, subtitle, trend, icon: Icon = Shield, color = "cyan" }) {
  const colorClasses = {
    cyan: {
      bg: 'from-cyan-500/20 to-blue-500/20',
      border: 'border-cyan-500/30',
      shadow: 'shadow-[0_0_30px_rgba(6,182,212,0.2)]',
      text: 'text-cyan-400',
      icon: 'text-cyan-400'
    },
    violet: {
      bg: 'from-violet-500/20 to-purple-500/20',
      border: 'border-violet-500/30',
      shadow: 'shadow-[0_0_30px_rgba(139,92,246,0.2)]',
      text: 'text-violet-400',
      icon: 'text-violet-400'
    },
    emerald: {
      bg: 'from-emerald-500/20 to-green-500/20',
      border: 'border-emerald-500/30',
      shadow: 'shadow-[0_0_30px_rgba(16,185,129,0.2)]',
      text: 'text-emerald-400',
      icon: 'text-emerald-400'
    },
    red: {
      bg: 'from-red-500/20 to-rose-500/20',
      border: 'border-red-500/30',
      shadow: 'shadow-[0_0_30px_rgba(239,68,68,0.2)]',
      text: 'text-red-400',
      icon: 'text-red-400'
    },
    amber: {
      bg: 'from-amber-500/20 to-orange-500/20',
      border: 'border-amber-500/30',
      shadow: 'shadow-[0_0_30px_rgba(245,158,11,0.2)]',
      text: 'text-amber-400',
      icon: 'text-amber-400'
    }
  };

  const colors = colorClasses[color] || colorClasses.cyan;

  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${colors.bg} border ${colors.border} ${colors.shadow} backdrop-blur-xl transition-all duration-500 hover:scale-[1.02]`}>
      {/* Animated background shimmer */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full hover:translate-x-full transition-transform duration-1000"></div>

      <div className="relative p-6">
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-xl bg-gradient-to-br ${colors.bg} border ${colors.border}`}>
            <Icon className={`w-6 h-6 ${colors.icon}`} />
          </div>

          {trend !== undefined && (
            <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${trend >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
              {trend >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span className="text-xs font-bold">{Math.abs(trend)}%</span>
            </div>
          )}
        </div>

        <h3 className="text-sm font-medium text-slate-400 mb-2">{title}</h3>
        <p className={`text-3xl font-black ${colors.text} mb-1`}>{value}</p>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}
