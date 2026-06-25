import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import useThemeStore from '../store/themeStore';

const RiskCharts = ({ portfolioData }) => {
  const { theme } = useThemeStore();

  // Risk Control Data (Donut Chart)
  const riskControlData = [
    { name: 'Effective-High', value: 30, color: '#22c55e' },
    { name: 'Effective', value: 20, color: '#84cc16' },
    { name: 'Effect-Medium', value: 10, color: '#eab308' },
    { name: 'Effect-Low', value: 15, color: '#f97316' },
    { name: 'Overdue', value: 25, color: '#ef4444' }
  ];

  // Impact of Risks Data (Donut Chart)
  const impactData = [
    { name: 'Impact-High', value: 30, color: '#ef4444' },
    { name: 'Impact-Medium', value: 40, color: '#eab308' },
    { name: 'Impact-Low', value: 20, color: '#84cc16' },
    { name: 'Overdue', value: 10, color: '#6b7280' }
  ];

  // Different Risks Impact (Bar Chart)
  const risksImpactData = [
    { category: 'Information Technology', low: 10, medium: 15, high: 8, critical: 5 },
    { category: 'Legal', low: 8, medium: 12, high: 10, critical: 7 },
    { category: 'Physical Security', low: 12, medium: 10, high: 6, critical: 3 },
    { category: 'Code of Conduct', low: 15, medium: 8, high: 5, critical: 2 },
    { category: 'Macro-Market Dynamics', low: 9, medium: 14, high: 11, critical: 6 },
    { category: 'Sales', low: 5, medium: 8, high: 4, critical: 2 },
    { category: 'Supply Chain', low: 13, medium: 16, high: 9, critical: 4 },
    { category: 'People', low: 11, medium: 13, high: 7, critical: 3 }
  ];

  const COLORS = {
    low: '#22c55e',
    medium: '#eab308',
    high: '#f97316',
    critical: '#ef4444'
  };

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="mb-4">
        <h2 className={`text-2xl font-bold ${theme.colors.textPrimary} mb-2 flex items-center gap-2`}>
          <svg className="w-7 h-7 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Risk Profile Dashboard
        </h2>
        <p className={theme.colors.textSecondary}>
          Comprehensive analysis of risk controls and impact distribution
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Control Donut Chart */}
        <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} shadow-sm hover:shadow-lg transition-all`}>
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
              <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Risk Control</h3>
          </div>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={riskControlData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              labelStyle={{ fill: '#ffffff', fontSize: 11, fontWeight: 600 }}
            >
              {riskControlData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#e5e7eb'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

        {/* Impact of Risks Donut Chart */}
        <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} shadow-sm hover:shadow-lg transition-all`}>
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
              <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Impact of Risks</h3>
          </div>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={impactData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              labelStyle={{ fill: '#ffffff', fontSize: 11, fontWeight: 600 }}
            >
              {impactData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#e5e7eb'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      </div>

      {/* Different Risks Impact Bar Chart - Full Width */}
      <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} shadow-sm`}>
        <div className="flex items-center gap-2 mb-6">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className={`text-xl font-bold ${theme.colors.textPrimary}`}>Risk Impact by Category</h3>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={risksImpactData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
          >
            <XAxis
              type="number"
              stroke="#6b7280"
              tick={{ fill: '#9ca3af' }}
            />
            <YAxis
              type="category"
              dataKey="category"
              stroke="#6b7280"
              width={140}
              tick={{ fill: '#e5e7eb', fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#e5e7eb'
              }}
              itemStyle={{ color: '#e5e7eb' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Legend
              wrapperStyle={{ color: '#e5e7eb' }}
              iconType="square"
            />
            <Bar dataKey="low" name="Low Risk" stackId="a" fill={COLORS.low} />
            <Bar dataKey="medium" name="Medium Risk" stackId="a" fill={COLORS.medium} />
            <Bar dataKey="high" name="High Risk" stackId="a" fill={COLORS.high} />
            <Bar dataKey="critical" name="Critical Risk" stackId="a" fill={COLORS.critical} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default RiskCharts;
