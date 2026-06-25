import { useEffect, useState } from 'react';
import { Filter, X } from 'lucide-react';
import axios from 'axios';

const RiskMatrixFilters = ({ filters, onFilterChange, onClearFilters }) => {
  const [filterOptions, setFilterOptions] = useState({
    geographies: [],
    vendors: [],
    business_units: [],
    contract_types: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/risk-value-matrix-filters`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFilterOptions(response.data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    } finally {
      setLoading(false);
    }
  };

  const hasActiveFilters = filters.geography || filters.vendor || filters.business_unit || filters.contract_type;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Filters</h3>
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
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-slate-800 rounded w-20 mb-2"></div>
              <div className="h-9 bg-slate-800 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Geography Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-2 font-medium">
              Geography
            </label>
            <select
              value={filters.geography || ''}
              onChange={(e) => onFilterChange('geography', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            >
              <option value="">All Geographies</option>
              {filterOptions.geographies.map((geo) => (
                <option key={geo} value={geo}>
                  {geo}
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
              {filterOptions.vendors.map((vendor) => (
                <option key={vendor} value={vendor}>
                  {vendor}
                </option>
              ))}
            </select>
          </div>

          {/* Business Unit Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-2 font-medium">
              Business Unit
            </label>
            <select
              value={filters.business_unit || ''}
              onChange={(e) => onFilterChange('business_unit', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            >
              <option value="">All Business Units</option>
              {filterOptions.business_units.map((bu) => (
                <option key={bu} value={bu}>
                  {bu}
                </option>
              ))}
            </select>
          </div>

          {/* Contract Type Filter */}
          <div>
            <label className="block text-xs text-slate-400 mb-2 font-medium">
              Contract Type
            </label>
            <select
              value={filters.contract_type || ''}
              onChange={(e) => onFilterChange('contract_type', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            >
              <option value="">All Types</option>
              {filterOptions.contract_types.map((type) => (
                <option key={type} value={type}>
                  {type}
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
        </div>
      )}
    </div>
  );
};

export default RiskMatrixFilters;
