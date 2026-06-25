import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  X,
  Calendar,
  MapPin,
  DollarSign,
  Shield,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Scale,
} from 'lucide-react';
import api from '../utils/api';

const ContractSearch = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Filter states
  const [filters, setFilters] = useState({
    vendor: '',
    dateFrom: '',
    dateTo: '',
    contractType: '',
    riskLevel: '',
    jurisdiction: '',
    paymentTerms: '',
    liabilityLevel: '',
    hasAnalysis: '',
    hasArbitration: '',
  });

  const [stats, setStats] = useState({
    total: 0,
    highRisk: 0,
    mediumRisk: 0,
    lowRisk: 0,
  });

  // Perform search
  const handleSearch = async () => {
    setLoading(true);
    setError('');
    try {
      let query = searchQuery;
      let liabilityLevel = filters.liabilityLevel;

      // Check if search query matches a liability level name
      const liabilityLevelMap = {
        'low liability': 'LOW',
        'low': 'LOW',
        'medium liability': 'MEDIUM',
        'medium': 'MEDIUM',
        'high liability': 'HIGH',
        'high': 'HIGH',
      };

      const queryLower = searchQuery?.toLowerCase().trim();
      if (queryLower && liabilityLevelMap[queryLower]) {
        liabilityLevel = liabilityLevelMap[queryLower];
        query = ''; // Clear the search query since we're filtering by liability level
      }

      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (filters.vendor) params.append('vendor', filters.vendor);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      if (filters.contractType) params.append('contract_type', filters.contractType);
      if (filters.riskLevel) params.append('risk_level', filters.riskLevel);
      if (filters.jurisdiction) params.append('jurisdiction', filters.jurisdiction);
      if (filters.paymentTerms) params.append('payment_terms', filters.paymentTerms);
      if (liabilityLevel) params.append('liability_level', liabilityLevel);
      if (filters.hasAnalysis) params.append('has_analysis', filters.hasAnalysis);
      if (filters.hasArbitration) params.append('has_arbitration', filters.hasArbitration);

      const response = await api.get(`/contracts/search?${params.toString()}`);
      setContracts(response.data.contracts || []);

      // Calculate stats
      const total = response.data.contracts?.length || 0;
      setStats({
        total,
        highRisk: response.data.contracts?.filter(c => c.liabilityLevel === 'HIGH').length || 0,
        mediumRisk: response.data.contracts?.filter(c => c.liabilityLevel === 'MEDIUM').length || 0,
        lowRisk: response.data.contracts?.filter(c => c.liabilityLevel === 'LOW').length || 0,
      });
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to search contracts';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setFilters({
      vendor: '',
      dateFrom: '',
      dateTo: '',
      contractType: '',
      riskLevel: '',
      jurisdiction: '',
      paymentTerms: '',
      liabilityLevel: '',
      hasAnalysis: '',
      hasArbitration: '',
    });
    setContracts([]);
  };

  // Load initial contracts on mount
  useEffect(() => {
    handleSearch();
  }, []);

  const getRiskBadgeColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'HIGH':
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'LOW':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto bg-slate-900 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Search Contracts</h1>
        <p className="text-slate-400">
          Search and filter contracts by name, jurisdiction, risk level, payment terms, and more
        </p>
      </div>

      {/* Main Search Bar */}
      <div className="bg-slate-800 rounded-xl shadow-lg border border-slate-700 p-6 mb-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              placeholder="Search by contract name, vendor, type, jurisdiction..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-12 pr-4 py-3 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition flex items-center gap-2"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="px-6 py-3 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition flex items-center gap-2"
          >
            <Filter size={20} />
            Advanced
            {showAdvancedFilters ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="mt-6 pt-6 border-t border-slate-700">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Vendor/Party */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <MapPin size={16} className="inline mr-2" />
                  Vendor/Party Name
                </label>
                <input
                  type="text"
                  placeholder="Enter vendor name"
                  value={filters.vendor}
                  onChange={(e) => setFilters({ ...filters, vendor: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Contract Type */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <FileText size={16} className="inline mr-2" />
                  Contract Type
                </label>
                <input
                  type="text"
                  placeholder="e.g., NDA, MSA, Service Agreement"
                  value={filters.contractType}
                  onChange={(e) => setFilters({ ...filters, contractType: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Jurisdiction */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <MapPin size={16} className="inline mr-2" />
                  Jurisdiction
                </label>
                <input
                  type="text"
                  placeholder="e.g., Dubai, USA, UK, Singapore"
                  value={filters.jurisdiction}
                  onChange={(e) => setFilters({ ...filters, jurisdiction: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Payment Terms */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <DollarSign size={16} className="inline mr-2" />
                  Payment Terms
                </label>
                <input
                  type="text"
                  placeholder="e.g., NET 30, Upon delivery"
                  value={filters.paymentTerms}
                  onChange={(e) => setFilters({ ...filters, paymentTerms: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Risk Level */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <AlertTriangle size={16} className="inline mr-2" />
                  Risk Level
                </label>
                <select
                  value={filters.riskLevel}
                  onChange={(e) => setFilters({ ...filters, riskLevel: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Levels</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>

              {/* Liability Level */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Shield size={16} className="inline mr-2" />
                  Liability Level
                </label>
                <select
                  value={filters.liabilityLevel}
                  onChange={(e) => setFilters({ ...filters, liabilityLevel: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Levels</option>
                  <option value="LOW">Low Liability</option>
                  <option value="MEDIUM">Medium Liability</option>
                  <option value="HIGH">High Liability</option>
                </select>
              </div>

              {/* Date From */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Calendar size={16} className="inline mr-2" />
                  Uploaded From
                </label>
                <input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Date To */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Calendar size={16} className="inline mr-2" />
                  Uploaded To
                </label>
                <input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Analysis Status */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <CheckCircle size={16} className="inline mr-2" />
                  Analysis Status
                </label>
                <select
                  value={filters.hasAnalysis}
                  onChange={(e) => setFilters({ ...filters, hasAnalysis: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Contracts</option>
                  <option value="true">Has Analysis</option>
                  <option value="false">No Analysis</option>
                </select>
              </div>

              {/* Arbitration Clause */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Scale size={16} className="inline mr-2" />
                  Arbitration Clause
                </label>
                <select
                  value={filters.hasArbitration}
                  onChange={(e) => setFilters({ ...filters, hasArbitration: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Contracts</option>
                  <option value="true">With Arbitration</option>
                  <option value="false">Without Arbitration</option>
                </select>
              </div>
            </div>

            <div className="mt-4 flex gap-3">
              <button
                onClick={handleSearch}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Apply Filters
              </button>
              <button
                onClick={clearFilters}
                className="px-6 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition flex items-center gap-2"
              >
                <X size={16} />
                Clear All
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      {stats.total > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg shadow-lg border border-slate-700 p-4">
            <div className="text-sm text-slate-400 mb-1">Total Found</div>
            <div className="text-2xl font-bold text-white">{stats.total}</div>
          </div>
          <div className="bg-red-900/20 rounded-lg shadow-lg border border-red-800/50 p-4">
            <div className="text-sm text-red-400 mb-1">High Liability</div>
            <div className="text-2xl font-bold text-red-300">{stats.highRisk}</div>
          </div>
          <div className="bg-yellow-900/20 rounded-lg shadow-lg border border-yellow-800/50 p-4">
            <div className="text-sm text-yellow-400 mb-1">Medium Liability</div>
            <div className="text-2xl font-bold text-yellow-300">{stats.mediumRisk}</div>
          </div>
          <div className="bg-green-900/20 rounded-lg shadow-lg border border-green-800/50 p-4">
            <div className="text-sm text-green-400 mb-1">Low Liability</div>
            <div className="text-2xl font-bold text-green-300">{stats.lowRisk}</div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-800/50 text-red-300 rounded-lg p-4 mb-6">
          <AlertTriangle size={20} className="inline mr-2" />
          {error}
        </div>
      )}

      {/* Results */}
      <div className="bg-slate-800 rounded-xl shadow-lg border border-slate-700">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">
            Search Results {contracts.length > 0 && `(${contracts.length})`}
          </h2>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-slate-400">Searching contracts...</p>
          </div>
        ) : contracts.length === 0 ? (
          <div className="p-12 text-center">
            <Search size={48} className="mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No contracts found</h3>
            <p className="text-slate-400">Try adjusting your search criteria or filters</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700">
            {contracts.map((contract) => (
              <div
                key={contract.id}
                className="p-6 hover:bg-slate-700/50 transition cursor-pointer"
                onClick={() => navigate(`/contract/${contract.id}/clauses`)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {contract.originalFilename || contract.original_filename}
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 text-sm">
                      {contract.contractType && (
                        <div className="flex items-center gap-2 text-slate-400">
                          <FileText size={16} />
                          <span>{contract.contractType}</span>
                        </div>
                      )}
                      {contract.jurisdiction && (
                        <div className="flex items-center gap-2 text-slate-400">
                          <MapPin size={16} />
                          <span>{contract.jurisdiction}</span>
                        </div>
                      )}
                      {contract.paymentTerms && (
                        <div className="flex items-center gap-2 text-slate-400">
                          <DollarSign size={16} />
                          <span>{contract.paymentTerms}</span>
                        </div>
                      )}
                      {contract.partyName && (
                        <div className="flex items-center gap-2 text-slate-400">
                          <span className="font-medium text-slate-300">Parties:</span>
                          <span>{contract.partyName}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2 text-slate-400">
                        <Clock size={16} />
                        <span>{new Date(contract.uploadedAt).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 ml-4">
                    {contract.liabilityLevel && (
                      <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getRiskBadgeColor(contract.liabilityLevel)}`}>
                        {contract.liabilityLevel} Liability
                      </span>
                    )}
                    {contract.hasArbitration && (
                      <span className="px-3 py-1 text-xs font-medium rounded-full border bg-purple-900/30 text-purple-300 border-purple-700 flex items-center gap-1">
                        <Scale size={12} />
                        Arbitration
                      </span>
                    )}
                    {contract.hasRiskAnalysis && (
                      <span className="px-3 py-1 text-xs font-medium rounded-full border bg-blue-900/30 text-blue-300 border-blue-700">
                        Analyzed
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContractSearch;
