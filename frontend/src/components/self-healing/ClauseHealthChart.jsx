import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * Clause Health Visualization Chart
 * Shows health score distribution across clauses
 */
const ClauseHealthChart = ({ data }) => {
  // Prepare data for chart (top 10 by health score)
  const chartData = data
    .slice(0, 10)
    .map(clause => ({
      name: clause.clause_code.length > 20
        ? clause.clause_code.substring(0, 20) + '...'
        : clause.clause_code,
      health: (clause.health_score * 100).toFixed(1),
      success: (clause.success_rate * 100).toFixed(1),
      fullName: clause.clause_code
    }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#1a2951] p-4 rounded-lg shadow-lg border border-gray-600">
          <p className="font-semibold text-white mb-2">{data.fullName}</p>
          <p className="text-sm text-blue-400">
            Health Score: <span className="font-bold">{data.health}%</span>
          </p>
          <p className="text-sm text-green-400">
            Success Rate: <span className="font-bold">{data.success}%</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="rounded-2xl border border-white/5 p-6 mb-6 relative overflow-hidden"
      style={{background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(10px)'}}>
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl"
        style={{background: 'linear-gradient(90deg,#6366f1,#8b5cf6,#10b981)'}} />
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-base font-bold text-white">Top 10 Clauses by Health Score</h2>
          <p className="text-xs text-slate-600 mt-0.5">Health & success rate comparison</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-sm" style={{background:'#6366f1'}} /><span className="text-xs text-slate-500">Health</span></div>
          <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-sm" style={{background:'#10b981'}} /><span className="text-xs text-slate-500">Success</span></div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} barGap={4} barCategoryGap="25%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis dataKey="name" angle={-40} textAnchor="end" height={80} tick={{ fontSize: 10, fill: '#475569' }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#475569' }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="health" fill="#6366f1" name="Health Score" radius={[6, 6, 0, 0]} fillOpacity={0.9} />
          <Bar dataKey="success" fill="#10b981" name="Success Rate" radius={[6, 6, 0, 0]} fillOpacity={0.85} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ClauseHealthChart;
