import { useState } from 'react';
import { TrendingUp } from 'lucide-react';
import useThemeStore from '../store/themeStore';
import RiskValueMatrix from '../components/executive/RiskValueMatrix';
import RiskMatrixFilters from '../components/executive/RiskMatrixFilters';

const RiskValueMatrixPage = () => {
  const { theme } = useThemeStore();
  const [filters, setFilters] = useState({
    geography: '',
    vendor: '',
    business_unit: '',
    contract_type: ''
  });

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({
      geography: '',
      vendor: '',
      business_unit: '',
      contract_type: ''
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <TrendingUp className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
              Risk vs Value Matrix
            </h1>
            <p className="text-sm text-slate-400">
              Bubble chart visualization — Contract value vs risk exposure
            </p>
          </div>
        </div>
      </div>

      {/* Main Content with Filters */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <RiskMatrixFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
          />
        </div>

        {/* Matrix Visualization */}
        <div className="lg:col-span-3">
          <RiskValueMatrix filters={filters} />
        </div>
      </div>

      {/* Info Section */}
      <div className="mt-6 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-3">How to Read This Chart</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-300">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <span className="font-medium text-blue-400">X-Axis (Horizontal)</span>
            </div>
            <p className="text-slate-400">
              Contract value in INR Crores. Higher values indicate larger financial commitments.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-purple-500"></div>
              <span className="font-medium text-purple-400">Y-Axis (Vertical)</span>
            </div>
            <p className="text-slate-400">
              Risk score (0-100) based on liability, arbitration, and contract value factors.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-pink-500"></div>
              <span className="font-medium text-pink-400">Bubble Size</span>
            </div>
            <p className="text-slate-400">
              Represents potential exposure (20% estimated loss). Larger bubbles = higher risk exposure.
            </p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800">
          <h4 className="text-sm font-medium text-white mb-2">Risk Zones</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="flex items-start gap-2">
              <div className="w-4 h-4 rounded-full bg-green-500/20 border border-green-500 flex-shrink-0 mt-0.5"></div>
              <div>
                <span className="text-green-400 font-medium">Low Risk (&lt;40)</span>
                <p className="text-slate-500 mt-1">Well-protected contracts with adequate safeguards</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-4 h-4 rounded-full bg-amber-500/20 border border-amber-500 flex-shrink-0 mt-0.5"></div>
              <div>
                <span className="text-amber-400 font-medium">Medium Risk (40-70)</span>
                <p className="text-slate-500 mt-1">Moderate concerns, review recommended</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-4 h-4 rounded-full bg-red-500/20 border border-red-500 flex-shrink-0 mt-0.5"></div>
              <div>
                <span className="text-red-400 font-medium">High Risk (&gt;70)</span>
                <p className="text-slate-500 mt-1">Critical attention needed, immediate action required</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskValueMatrixPage;
