import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { ArrowLeft, BarChart3, TrendingUp, PieChart, Activity, LineChart } from 'lucide-react';
import api from '../utils/api';

const Analytics = () => {
  const navigate = useNavigate();
  const [totalContracts, setTotalContracts] = useState(0);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/dashboard/stats');
        setTotalContracts(response.data.totalContracts);
      } catch (err) {
        console.error('Failed to fetch analytics stats:', err);
      }
    };
    fetchStats();
  }, []);

  const analyticsMetrics = [
    {
      title: 'Total Contracts Analyzed',
      value: String(totalContracts),
      icon: '📑',
      description: 'Upload contracts to start tracking',
    },
    {
      title: 'Average Processing Time',
      value: '< 5s',
      icon: '⚡',
      description: 'Per contract with AI analysis',
    },
    {
      title: 'Risk Identification Rate',
      value: '95%+',
      icon: '🎯',
      description: 'Accuracy in detecting risks',
    },
  ];

  const features = [
    {
      title: 'Contract Type Distribution',
      description: 'Track the types of contracts you upload (NDA, MSA, SOW, etc.)',
      icon: '📊',
    },
    {
      title: 'Risk Trend Analysis',
      description: 'Monitor risk patterns across your contract portfolio',
      icon: '📈',
    },
    {
      title: 'Processing Metrics',
      description: 'View analytics on document extraction and analysis performance',
      icon: '⚙️',
    },
    {
      title: 'Team Collaboration',
      description: 'Track contract reviews and approvals across your team',
      icon: '👥',
    },
    {
      title: 'Historical Reports',
      description: 'Access detailed reports on all analyzed contracts',
      icon: '📋',
    },
    {
      title: 'Export & Integration',
      description: 'Download reports and integrate with your existing tools',
      icon: '🔗',
    },
  ];

  const upcomingFeatures = [
    'Real-time dashboard with live metrics',
    'Custom report generation',
    'Advanced filtering and search',
    'Contract performance benchmarking',
    'Predictive analytics for contract outcomes',
    'API integration for third-party tools',
  ];

  return (
    <div className="space-y-8">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 hover:bg-slate-800 rounded-lg transition"
          >
            <ArrowLeft className="w-6 h-6 text-blue-400" />
          </button>
          <div>
            <h1 className="text-4xl font-bold text-white">Analytics</h1>
            <p className="text-slate-400">Track and monitor your contract workflows with comprehensive insights</p>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {analyticsMetrics.map((metric, index) => (
            <button
              key={metric.title}
              onClick={() => {
                // Make only the first card (Total Contracts Analyzed) clickable
                if (index === 0) {
                  navigate('/contracts');
                }
              }}
              disabled={index !== 0}
              className={`bg-slate-900 border border-slate-800 rounded-xl p-6 transition text-left ${
                index === 0
                  ? 'hover:border-blue-600 hover:shadow-lg hover:shadow-blue-600/20 cursor-pointer'
                  : 'hover:border-slate-700'
              }`}
            >
              <div className="text-4xl mb-3">{metric.icon}</div>
              <p className="text-slate-400 text-sm mb-2">{metric.title}</p>
              <p className="text-3xl font-bold text-white mb-2">{metric.value}</p>
              <p className="text-slate-500 text-xs">
                {index === 0 ? 'Click to view all contracts' : metric.description}
              </p>
            </button>
          ))}
        </div>

        {/* Analytics Features */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            <h3 className="text-2xl font-bold text-white">Available Analytics</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature) => (
              <div key={feature.title} className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition">
                <div className="flex items-start gap-4">
                  <span className="text-3xl">{feature.icon}</span>
                  <div>
                    <h4 className="font-semibold text-white mb-2">{feature.title}</h4>
                    <p className="text-slate-400 text-sm">{feature.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Dashboard Preview */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <LineChart className="w-6 h-6 text-blue-400" />
            <h3 className="text-2xl font-bold text-white">Dashboard Preview</h3>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
            <div className="text-center py-12">
              <Activity className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p className="text-slate-300 mb-2">Your analytics dashboard will appear here once you upload contracts</p>
              <p className="text-sm text-slate-400">Upload a contract to see real-time analytics and insights</p>
            </div>
          </div>
        </div>

        {/* Upcoming Features */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <PieChart className="w-6 h-6 text-blue-400" />
            <h3 className="text-2xl font-bold text-white">Coming Soon</h3>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {upcomingFeatures.map((feature) => (
                <div key={feature} className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
                  <p className="text-slate-300">{feature}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Benefits */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl p-8">
          <h3 className="text-2xl font-bold mb-4">Why Use Analytics?</h3>
          <ul className="space-y-3">
            <li className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-blue-200 flex-shrink-0" />
              <span>Make data-driven decisions about contract management</span>
            </li>
            <li className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-blue-200 flex-shrink-0" />
              <span>Identify trends and patterns in your contracts</span>
            </li>
            <li className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-blue-200 flex-shrink-0" />
              <span>Monitor team productivity and approval workflows</span>
            </li>
            <li className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-blue-200 flex-shrink-0" />
              <span>Discover cost-saving opportunities</span>
            </li>
          </ul>
        </div>

        {/* Action Button */}
        <div className="flex gap-4 justify-end">
          <button
            onClick={() => navigate('/upload')}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition shadow-lg"
          >
            Start Uploading Contracts
          </button>
        </div>
    </div>
  );
};

export default Analytics;
