import { useState } from 'react';
import { Network, Sparkles } from 'lucide-react';
import useThemeStore from '../store/themeStore';
import Galaxy2D from '../components/portfolio/Galaxy2D';
import ClusterFilters from '../components/portfolio/ClusterFilters';

const PortfolioIntelligence = () => {
  const { theme } = useThemeStore();
  const [filters, setFilters] = useState({
    industry: '',
    jurisdiction: '',
    vendor: ''
  });

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleClearFilters = () => {
    setFilters({
      industry: '',
      jurisdiction: '',
      vendor: ''
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Network className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h1 className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
              Portfolio Intelligence
            </h1>
            <p className="text-sm text-slate-400">
              Contract Clustering Galaxy — Discover hidden patterns & systemic risk templates
            </p>
          </div>
        </div>
      </div>

      {/* AI Insight Banner */}
      <div className="mb-6 bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-purple-400 mt-1 flex-shrink-0" />
          <div>
            <p className="text-purple-400 font-semibold mb-1">AI-Powered Semantic Clustering</p>
            <p className="text-gray-300 text-sm">
              Contracts are embedded using{' '}
              <span className="font-semibold text-white">AI embeddings</span> and clustered via{' '}
              <span className="font-semibold text-white">KMeans + PCA</span>. Outliers (red dots) indicate
              non-standard templates or anomalous risk patterns requiring investigation.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content with Filters */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <ClusterFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
          />

          {/* Legend Card */}
          <div className="mt-6 bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4">Understanding the Galaxy</h3>
            <div className="space-y-3 text-xs">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-slate-300 font-medium">Green Dots</span>
                </div>
                <p className="text-slate-500 text-xs ml-5">Low risk contracts (&lt;40 risk score)</p>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                  <span className="text-slate-300 font-medium">Amber Dots</span>
                </div>
                <p className="text-slate-500 text-xs ml-5">High risk contracts (≥70 risk score)</p>
              </div>

              <div>
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-white"></div>
                  <span className="text-slate-300 font-medium">Red Outlined</span>
                </div>
                <p className="text-slate-500 text-xs ml-5">Outliers - Structural anomalies (top 5%)</p>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <p className="text-slate-500 text-xs">
                  <span className="text-slate-400 font-medium">Clusters:</span> Contracts grouped by semantic similarity
                </p>
              </div>

              <div>
                <p className="text-slate-500 text-xs">
                  <span className="text-slate-400 font-medium">Proximity:</span> Closer dots = more similar templates
                </p>
              </div>

              <div>
                <p className="text-slate-500 text-xs">
                  <span className="text-slate-400 font-medium">Isolation:</span> Distant dots = unique patterns
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Galaxy Visualization */}
        <div className="lg:col-span-3">
          <Galaxy2D filters={filters} />
        </div>
      </div>

      {/* Insights Section */}
      <div className="mt-6 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-3">What This Tells You</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-300">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-purple-500"></div>
              <span className="font-medium text-purple-400">Hidden Patterns</span>
            </div>
            <p className="text-slate-400 text-xs">
              Discover systemic risk templates, vendor-specific pathologies, and jurisdiction bias across your portfolio
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <span className="font-medium text-blue-400">Risk Archetypes</span>
            </div>
            <p className="text-slate-400 text-xs">
              Identify which contract templates carry unlimited liability, lack arbitration, or drift from market norms
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
              <span className="font-medium text-emerald-400">Outlier Detection</span>
            </div>
            <p className="text-slate-400 text-xs">
              Auto-flags non-standard contracts that need immediate review - the ones that don't fit any cluster
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioIntelligence;
