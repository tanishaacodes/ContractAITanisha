import { useEffect, useState } from 'react';
import { Filter, X } from 'lucide-react';
import axios from 'axios';

const ClusterFilters = ({ filters, onFilterChange, onClearFilters }) => {
  const [filterOptions, setFilterOptions] = useState({
    industries: [],
    jurisdictions: [],
    vendors: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const token = localStorage.getItem('token');
      // Reuse the existing filter endpoint
      const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/risk-value-matrix-filters`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setFilterOptions({
        industries: response.data.business_units || [],
        jurisdictions: response.data.geographies || [],
        vendors: response.data.vendors || []
      });
    } catch (error) {
      console.error('Error fetching filter options:', error);
    } finally {
      setLoading(false);
    }
  };

  const hasActiveFilters = filters.industry || filters.jurisdiction || filters.vendor;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Cluster Filters</h3>
        </div>
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition"
          >
            <X className="w-3 h-3" />
            Clear All
          </button>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-slate-800 rounded w-20 mb-2"></div>
              <div className="h-9 bg-slate-800 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Industry / Business Unit Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-2 font-medium">
              Industry / Business Unit
            </label>
            <select
              value={filters.industry || ''}
              onChange={(e) => onFilterChange('industry', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            >
              <option value="">All Industries</option>
              {filterOptions.industries.map((industry, index) => (
                <option key={`industry-${index}`} value={industry}>
                  {industry}
                </option>
              ))}
            </select>
          </div>

          {/* Jurisdiction Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-2 font-medium">
              Jurisdiction / Geography
            </label>
            <select
              value={filters.jurisdiction || ''}
              onChange={(e) => onFilterChange('jurisdiction', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            >
              <option value="">All Jurisdictions</option>
              {filterOptions.jurisdictions.map((jurisdiction, index) => (
                <option key={`jurisdiction-${index}`} value={jurisdiction}>
                  {jurisdiction}
                </option>
              ))}
            </select>
          </div>

          {/* Vendor Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-2 font-medium">
              Vendor / Counterparty
            </label>
            <select
              value={filters.vendor || ''}
              onChange={(e) => onFilterChange('vendor', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            >
              <option value="">All Vendors</option>
              {filterOptions.vendors.map((vendor, index) => (
                <option key={`vendor-${index}`} value={vendor}>
                  {vendor}
                </option>
              ))}
            </select>
          </div>

          {/* Active Filters Count */}
          {hasActiveFilters && (
            <div className="pt-2 border-t border-slate-800">
              <p className="text-xs text-emerald-400">
                {Object.values(filters).filter(Boolean).length} filter(s) active
              </p>
            </div>
          )}

          {/* Info */}
          <div className="pt-2 border-t border-slate-800">
            <p className="text-xs text-slate-500">
              Filters refine the clustering analysis to show patterns within specific segments.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClusterFilters;
