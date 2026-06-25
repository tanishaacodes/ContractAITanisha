import { useState } from 'react';
import useThemeStore from '../store/themeStore';
import { AlertTriangle, CheckCircle, Clock, User } from 'lucide-react';

const RiskCategoryTable = ({ risks = [] }) => {
  const { theme } = useThemeStore();
  const [sortBy, setSortBy] = useState('severity');
  const [filterCategory, setFilterCategory] = useState('all');

  // Sample risk data if none provided
  const defaultRisks = [
    {
      ref_id: '10001',
      date_raised: '05/05/2020',
      category: 'Operational',
      description: 'If there are change in plans that require additional or different resources.',
      probability: 1,
      impact: 8,
      severity: 8,
      criteria: 'Criteria for the risk',
      mitigation: 'A designated team member will continually monitor any proposed changes to plans.',
      frequency: 'No current issue',
      owner: 'Joe Smith-Jobson'
    },
    {
      ref_id: '10002',
      date_raised: '06/08/2020',
      category: 'IT',
      description: 'If contractual issues arise, there will be delays or cost overruns.',
      probability: 2,
      impact: 4,
      severity: 8,
      criteria: 'Criteria for the risk',
      mitigation: 'The contracts manager will alert the contracts when there are issues.',
      frequency: 'All deadlines currently being monitored',
      owner: 'Jane Johnson-manager'
    },
    {
      ref_id: '10003',
      date_raised: '06/08/2020',
      category: 'Financial',
      description: 'Financial risk in the project',
      probability: 2,
      impact: 8,
      severity: 16,
      criteria: 'Criteria for the risk',
      mitigation: 'All deadlines currently being monitored',
      frequency: 'All deadlines currently being monitored',
      owner: 'Dale Swenson-manager'
    },
    {
      ref_id: '10004',
      date_raised: '06/08/2020',
      category: 'Legal/Regulatory',
      description: 'Regulatory compliance issues',
      probability: 1,
      impact: 8,
      severity: 8,
      criteria: 'Criteria for the risk',
      mitigation: 'Regular compliance audits',
      frequency: 'Monthly',
      owner: 'Legal Team'
    }
  ];

  const displayRisks = risks.length > 0 ? risks : defaultRisks;

  const getSeverityColor = (severity) => {
    if (severity <= 5) return '#22c55e';
    if (severity <= 9) return '#eab308';
    if (severity <= 12) return '#f97316';
    return '#ef4444';
  };

  const getSeverityLabel = (severity) => {
    if (severity <= 5) return 'LOW';
    if (severity <= 9) return 'MEDIUM';
    if (severity <= 12) return 'HIGH';
    return 'CRITICAL';
  };

  const categories = ['all', ...new Set(displayRisks.map(r => r.category))];

  const filteredRisks = displayRisks.filter(risk =>
    filterCategory === 'all' || risk.category === filterCategory
  ).sort((a, b) => {
    if (sortBy === 'severity') return b.severity - a.severity;
    if (sortBy === 'date') return new Date(b.date_raised) - new Date(a.date_raised);
    return 0;
  });

  return (
    <div className={`${theme.colors.surface} rounded-xl p-6 border ${theme.colors.surfaceBorder} shadow-sm`}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <svg className="w-7 h-7 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h2 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
            Risk Category Register
          </h2>
        </div>
        <p className={theme.colors.textSecondary}>
            Comprehensive risk tracking with mitigation plans and ownership
          </p>
      </div>

      {/* Filters and Sorting */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className={`px-4 py-2 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface} ${theme.colors.textPrimary}`}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat}
              </option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className={`px-4 py-2 rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface} ${theme.colors.textPrimary}`}
          >
            <option value="severity">Sort by Severity</option>
            <option value="date">Sort by Date</option>
          </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className={`border-b ${theme.colors.surfaceBorder}`}>
              <th className={`text-left p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>REF ID</th>
              <th className={`text-left p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>DATE RAISED</th>
              <th className={`text-left p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>RISK CATEGORY</th>
              <th className={`text-left p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>RISK DESCRIPTION</th>
              <th className={`text-center p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>PROBABILITY<br/>(1-5)</th>
              <th className={`text-center p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>IMPACT<br/>(1-16)</th>
              <th className={`text-center p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>RISK SEVERITY<br/>SCORE</th>
              <th className={`text-left p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>MITIGATION/RESPONSE PLAN</th>
              <th className={`text-left p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>MONITORING<br/>FREQUENCY</th>
              <th className={`text-left p-3 text-sm font-semibold ${theme.colors.textPrimary}`}>OWNER</th>
            </tr>
          </thead>
          <tbody>
            {filteredRisks.map((risk, index) => (
              <tr
                key={risk.ref_id || index}
                className={`border-b ${theme.colors.surfaceBorder} hover:${theme.colors.surfaceHover} transition`}
              >
                <td className={`p-3 ${theme.colors.textPrimary} font-medium`}>
                  {risk.ref_id}
                </td>
                <td className={`p-3 ${theme.colors.textSecondary} text-sm`}>
                  {risk.date_raised}
                </td>
                <td className={`p-3`}>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400">
                    {risk.category}
                  </span>
                </td>
                <td className={`p-3 ${theme.colors.textSecondary} text-sm max-w-xs`}>
                  {risk.description}
                </td>
                <td className="p-3 text-center">
                  <div
                    className="inline-flex items-center justify-center w-8 h-8 rounded font-bold text-white"
                    style={{ backgroundColor: risk.probability <= 2 ? '#22c55e' : risk.probability <= 3 ? '#eab308' : '#ef4444' }}
                  >
                    {risk.probability}
                  </div>
                </td>
                <td className="p-3 text-center">
                  <div
                    className="inline-flex items-center justify-center w-8 h-8 rounded font-bold text-white"
                    style={{ backgroundColor: risk.impact <= 5 ? '#22c55e' : risk.impact <= 9 ? '#eab308' : '#ef4444' }}
                  >
                    {risk.impact}
                  </div>
                </td>
                <td className="p-3 text-center">
                  <div
                    className="inline-flex items-center justify-center w-12 h-12 rounded-lg font-bold text-white text-lg"
                    style={{ backgroundColor: getSeverityColor(risk.severity) }}
                  >
                    {risk.severity}
                  </div>
                  <div className="text-xs mt-1 font-semibold" style={{ color: getSeverityColor(risk.severity) }}>
                    {getSeverityLabel(risk.severity)}
                  </div>
                </td>
                <td className={`p-3 ${theme.colors.textSecondary} text-sm max-w-xs`}>
                  {risk.mitigation}
                </td>
                <td className={`p-3 ${theme.colors.textSecondary} text-sm`}>
                  <div className="flex items-center gap-2">
                    <Clock size={14} />
                    {risk.frequency}
                  </div>
                </td>
                <td className={`p-3 ${theme.colors.textPrimary} text-sm`}>
                  <div className="flex items-center gap-2">
                    <User size={14} />
                    {risk.owner}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle size={20} className="text-green-500" />
            <span className="text-sm font-semibold text-green-400">Low Risk</span>
          </div>
          <div className="text-2xl font-bold text-green-400">
            {filteredRisks.filter(r => r.severity <= 5).length}
          </div>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={20} className="text-yellow-500" />
            <span className="text-sm font-semibold text-yellow-400">Medium Risk</span>
          </div>
          <div className="text-2xl font-bold text-yellow-400">
            {filteredRisks.filter(r => r.severity > 5 && r.severity <= 9).length}
          </div>
        </div>
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={20} className="text-orange-500" />
            <span className="text-sm font-semibold text-orange-400">High Risk</span>
          </div>
          <div className="text-2xl font-bold text-orange-400">
            {filteredRisks.filter(r => r.severity > 9 && r.severity <= 12).length}
          </div>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={20} className="text-red-500" />
            <span className="text-sm font-semibold text-red-400">Critical Risk</span>
          </div>
          <div className="text-2xl font-bold text-red-400">
            {filteredRisks.filter(r => r.severity > 12).length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskCategoryTable;
