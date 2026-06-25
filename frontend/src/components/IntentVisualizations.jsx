import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { TrendingUp, PieChart as PieChartIcon, BarChart3, Activity } from 'lucide-react';
import IntentNetworkGraph from './IntentNetworkGraph';

const IntentVisualizations = ({ intentsData }) => {
  if (!intentsData || !intentsData.intents || intentsData.intents.length === 0) {
    return null;
  }

  // Prepare data for Intent Distribution Pie Chart
  const intentDistributionData = intentsData.intents.map(item => ({
    name: item.intent.name,
    value: item.intent.occurrence_count,
    confidence: item.intent.confidence,
  }));

  // Prepare data for Obligations Priority Distribution
  const priorityCount = { HIGH: 0, MEDIUM: 0, LOW: 0 };
  intentsData.intents.forEach(item => {
    if (item.obligations) {
      item.obligations.forEach(obl => {
        priorityCount[obl.priority] = (priorityCount[obl.priority] || 0) + 1;
      });
    }
  });

  const priorityData = [
    { name: 'High Priority', value: priorityCount.HIGH, color: '#ef4444' },
    { name: 'Medium Priority', value: priorityCount.MEDIUM, color: '#f59e0b' },
    { name: 'Low Priority', value: priorityCount.LOW, color: '#10b981' },
  ].filter(item => item.value > 0);

  // Prepare data for Party Distribution
  const partyCount = { YOUR_COMPANY: 0, COUNTERPARTY: 0, BOTH: 0 };
  intentsData.intents.forEach(item => {
    if (item.obligations) {
      item.obligations.forEach(obl => {
        partyCount[obl.party] = (partyCount[obl.party] || 0) + 1;
      });
    }
    if (item.rights) {
      item.rights.forEach(right => {
        partyCount[right.party] = (partyCount[right.party] || 0) + 1;
      });
    }
  });

  const partyData = [
    { party: 'Your Company', obligations: 0, rights: 0 },
    { party: 'Counterparty', obligations: 0, rights: 0 },
    { party: 'Both Parties', obligations: 0, rights: 0 },
  ];

  intentsData.intents.forEach(item => {
    if (item.obligations) {
      item.obligations.forEach(obl => {
        if (obl.party === 'YOUR_COMPANY') partyData[0].obligations++;
        if (obl.party === 'COUNTERPARTY') partyData[1].obligations++;
        if (obl.party === 'BOTH') partyData[2].obligations++;
      });
    }
    if (item.rights) {
      item.rights.forEach(right => {
        if (right.party === 'YOUR_COMPANY') partyData[0].rights++;
        if (right.party === 'COUNTERPARTY') partyData[1].rights++;
        if (right.party === 'BOTH') partyData[2].rights++;
      });
    }
  });

  // Prepare data for Risk Analysis by Intent
  const riskByIntentData = intentsData.intents.map(item => {
    const obligations = item.obligations || [];
    const rights = item.rights || [];

    const avgOblRisk = obligations.length > 0
      ? obligations.reduce((sum, obl) => sum + obl.risk_score, 0) / obligations.length
      : 0;

    const avgRightRisk = rights.length > 0
      ? rights.reduce((sum, right) => sum + right.risk_score, 0) / rights.length
      : 0;

    return {
      intent: item.intent.name.length > 20 ? item.intent.name.substring(0, 20) + '...' : item.intent.name,
      obligationRisk: parseFloat((avgOblRisk * 100).toFixed(1)),
      rightRisk: parseFloat((avgRightRisk * 100).toFixed(1)),
      obligations: obligations.length,
      rights: rights.length,
    };
  }).slice(0, 8); // Top 8 intents

  const COLORS = [
    '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
    '#10b981', '#06b6d4', '#6366f1', '#14b8a6',
    '#f97316', '#84cc16'
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl">
          <p className="text-white font-semibold mb-1">{payload[0].name}</p>
          <p className="text-slate-300 text-sm">Count: {payload[0].value}</p>
        </div>
      );
    }
    return null;
  };

  const RiskTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl">
          <p className="text-white font-semibold mb-2">{payload[0].payload.intent}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 mb-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-blue-400">Total Intents</span>
            <TrendingUp className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-3xl font-bold text-white">{intentsData.total_intents}</div>
        </div>

        <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/20 border border-yellow-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-yellow-400">Total Obligations</span>
            <Activity className="w-5 h-5 text-yellow-400" />
          </div>
          <div className="text-3xl font-bold text-white">
            {intentsData.intents.reduce((sum, item) => sum + (item.obligation_count || 0), 0)}
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-green-400">Total Rights</span>
            <BarChart3 className="w-5 h-5 text-green-400" />
          </div>
          <div className="text-3xl font-bold text-white">
            {intentsData.intents.reduce((sum, item) => sum + (item.rights_count || 0), 0)}
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-purple-400">Avg Confidence</span>
            <PieChartIcon className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-white">
            {((intentsData.intents.reduce((sum, item) => sum + item.intent.confidence, 0) / intentsData.intents.length) * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Intent Distribution Pie Chart */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <PieChartIcon className="w-5 h-5" />
            Intent Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={intentDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {intentDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Obligation Priority Distribution */}
        {priorityData.length > 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Obligation Priority Breakdown
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={priorityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {priorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Party Exposure Analysis */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Party Exposure Analysis
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={partyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="party" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '0.5rem'
                }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend />
              <Bar dataKey="obligations" fill="#f59e0b" name="Obligations" />
              <Bar dataKey="rights" fill="#10b981" name="Rights" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Analysis by Intent */}
        {riskByIntentData.length > 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Risk Scores by Intent
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={riskByIntentData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="intent"
                  stroke="#94a3b8"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  fontSize={12}
                />
                <YAxis stroke="#94a3b8" label={{ value: 'Risk %', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip content={<RiskTooltip />} />
                <Legend />
                <Bar dataKey="obligationRisk" fill="#ef4444" name="Avg Obligation Risk" />
                <Bar dataKey="rightRisk" fill="#f59e0b" name="Avg Right Risk" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Intent Network Graph - Full Width */}
      <IntentNetworkGraph intentsData={intentsData} />
    </div>
  );
};

export default IntentVisualizations;
