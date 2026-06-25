import { Activity, TrendingUp, Shield, Award } from 'lucide-react';

/**
 * Health Report Summary Component
 * Displays overall system health statistics
 */
const HealthReportSummary = ({ report }) => {
  const statusCounts = report.status_distribution || {};
  const avgMetrics = report.average_metrics || {};

  const stats = [
    {
      label: 'Total Clauses',
      value: report.total_clauses || 0,
      icon: Activity,
      color: 'bg-blue-100 text-blue-700',
      iconColor: 'text-blue-600'
    },
    {
      label: 'Alive Clauses',
      value: statusCounts.ALIVE || 0,
      icon: TrendingUp,
      color: 'bg-green-100 text-green-700',
      iconColor: 'text-green-600'
    },
    {
      label: 'Weak Clauses',
      value: statusCounts.WEAK || 0,
      icon: Shield,
      color: 'bg-yellow-100 text-yellow-700',
      iconColor: 'text-yellow-600'
    },
    {
      label: 'Avg Health',
      value: ((avgMetrics.health_score || 0) * 100).toFixed(0) + '%',
      icon: Award,
      color: 'bg-purple-100 text-purple-700',
      iconColor: 'text-purple-600'
    }
  ];

  const gradients = [
    'linear-gradient(135deg,#6366f1,#8b5cf6)',
    'linear-gradient(135deg,#10b981,#059669)',
    'linear-gradient(135deg,#f59e0b,#d97706)',
    'linear-gradient(135deg,#ec4899,#db2777)',
  ];
  const glows = ['rgba(99,102,241,0.25)', 'rgba(16,185,129,0.25)', 'rgba(245,158,11,0.25)', 'rgba(236,72,153,0.25)'];
  const borders = ['rgba(99,102,241,0.2)', 'rgba(16,185,129,0.2)', 'rgba(245,158,11,0.2)', 'rgba(236,72,153,0.2)'];
  const bgs = ['rgba(99,102,241,0.07)', 'rgba(16,185,129,0.07)', 'rgba(245,158,11,0.07)', 'rgba(236,72,153,0.07)'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <div
            key={index}
            className="rounded-2xl p-5 border relative overflow-hidden transition-transform hover:-translate-y-1"
            style={{background: bgs[index], borderColor: borders[index]}}
          >
            <div className="absolute top-0 right-0 w-24 h-24 rounded-full opacity-20 -translate-y-6 translate-x-6"
              style={{background: gradients[index], filter: 'blur(20px)'}} />
            <div className="flex items-start justify-between relative">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{stat.label}</p>
                <p className="text-4xl font-black text-white tracking-tight">{stat.value}</p>
              </div>
              <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{background: gradients[index], boxShadow: `0 4px 14px ${glows[index]}`}}>
                <Icon className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default HealthReportSummary;
