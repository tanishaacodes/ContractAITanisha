import { Activity } from 'lucide-react';
import useThemeStore from '../store/themeStore';
import TotalExposureGauge from '../components/executive/TotalExposureGauge';
import RiskTrend from '../components/executive/RiskTrend';
import TopRiskDrivers from '../components/executive/TopRiskDrivers';
import LossLikelyContracts from '../components/executive/LossLikelyContracts';
import AIInterventions from '../components/executive/AIInterventions';

const ExecutiveSnapshot = () => {
  const { theme } = useThemeStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Activity className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h1 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
              Executive Risk Snapshot
            </h1>
            <p className="text-sm text-slate-400">
              CXO / Board Mode — Real-time portfolio overview
            </p>
          </div>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Row 1 */}
        <TotalExposureGauge />
        <RiskTrend />

        {/* Row 2 */}
        <TopRiskDrivers />
        <LossLikelyContracts />
      </div>

      {/* Full Width Section */}
      <AIInterventions />
    </div>
  );
};

export default ExecutiveSnapshot;
