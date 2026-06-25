import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FileText, Search, Filter, Eye, Download, Trash2, X, Calendar, AlertTriangle, ArrowLeft, Network, FlaskConical } from 'lucide-react';
import api from '../utils/api';
import DocumentGrid from '../components/DocumentGrid';
import useThemeStore from '../store/themeStore';

export default function Contracts() {
  const { theme } = useThemeStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const filter = searchParams.get('filter') || 'all';

  // Get drill-down filters from URL
  const riskParam = searchParams.get('risk');
  const sortParam = searchParams.get('sort');
  const statusParam = searchParams.get('status');

  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState(filter);
  const [drillDownActive, setDrillDownActive] = useState(false);

  // Advanced search filters
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState({
    vendor: '',
    dateFrom: '',
    dateTo: '',
    riskLevel: riskParam || '',
    contractType: '',
    hasAnalysis: ''
  });

  useEffect(() => {
    fetchContracts();
  }, [riskParam, sortParam, statusParam]);

  const fetchContracts = async () => {
    try {
      setLoading(true);

      // Check if drill-down filters from URL are present
      const hasDrillDownFilters = riskParam || sortParam || statusParam;
      const hasAdvancedFilters = filters.vendor || filters.dateFrom || filters.dateTo ||
                                   filters.riskLevel || filters.contractType || filters.hasAnalysis;

      if (hasDrillDownFilters) {
        // Use dashboard drill-down API
        const params = new URLSearchParams();
        if (riskParam) params.append('risk', riskParam);
        if (sortParam) params.append('sort', sortParam);
        if (statusParam) params.append('status', statusParam);

        const response = await api.get(`/dashboard/contracts?${params.toString()}`);
        setContracts(response.data.contracts || []);
        setDrillDownActive(true);
      } else if (searchTerm || hasAdvancedFilters) {
        // Use search API with filters
        const params = new URLSearchParams();
        if (searchTerm) params.append('q', searchTerm);
        if (filters.vendor) params.append('vendor', filters.vendor);
        if (filters.dateFrom) params.append('date_from', filters.dateFrom);
        if (filters.dateTo) params.append('date_to', filters.dateTo);
        if (filters.riskLevel) params.append('risk_level', filters.riskLevel);
        if (filters.contractType) params.append('contract_type', filters.contractType);
        if (filters.hasAnalysis) params.append('has_analysis', filters.hasAnalysis);

        const response = await api.get(`/contracts/search?${params.toString()}`);
        setContracts(response.data.contracts || []);
        setDrillDownActive(false);
      } else {
        // Use regular list API
        const response = await api.get('/contracts/list');
        setContracts(response.data.contracts || []);
        setDrillDownActive(false);
      }
    } catch (err) {
      console.error('Failed to fetch contracts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchContracts();
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilters({
      vendor: '',
      dateFrom: '',
      dateTo: '',
      riskLevel: '',
      contractType: '',
      hasAnalysis: ''
    });
    setShowAdvancedFilters(false);
    // Reload contracts after clearing filters
    setTimeout(() => {
      fetchContracts();
    }, 100);
  };

  const getFilteredContracts = () => {
    let filtered = contracts;

    // Apply status filter (for the quick filter buttons)
    switch (selectedFilter) {
      case 'analyzed':
        filtered = filtered.filter(c => c.has_analysis === true);
        break;
      case 'pending':
        filtered = filtered.filter(c => c.has_analysis === false);
        break;
      case 'all':
      default:
        break;
    }

    return filtered;
  };

  const filteredContracts = getFilteredContracts();

  const filterOptions = [
    { value: 'all', label: 'All Contracts', count: contracts.length },
    { value: 'analyzed', label: 'Analysis Complete', count: contracts.filter(c => c.has_analysis === true).length },
    { value: 'pending', label: 'Pending Review', count: contracts.filter(c => c.has_analysis === false).length },
  ];

  const viewContract = (contractId) => {
    navigate(`/contract/${contractId}/clauses`);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (contract) => {
    if (contract.has_analysis) {
      return (
        <span className="px-3 py-1 bg-green-900/30 text-green-400 text-xs font-medium rounded-full border border-green-800">
          Analyzed
        </span>
      );
    }
    return (
      <span className="px-3 py-1 bg-yellow-900/30 text-yellow-400 text-xs font-medium rounded-full border border-yellow-800">
        Pending
      </span>
    );
  };

  // Get drill-down filter label
  const getDrillDownLabel = () => {
    if (riskParam === 'high') return 'High-Risk Contracts';
    if (sortParam === 'value') return 'Contracts Sorted by Value';
    if (sortParam === 'risk') return 'Contracts Sorted by Risk';
    if (sortParam === 'date') return 'Recently Uploaded Contracts';
    if (statusParam === 'analyzed') return 'Analyzed Contracts';
    if (statusParam === 'pending') return 'Pending Review Contracts';
    return null;
  };

  const drillDownLabel = getDrillDownLabel();

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/dashboard')}
        className={`flex items-center gap-2 ${theme.colors.textSecondary} hover:${theme.colors.textPrimary} transition`}
      >
        <ArrowLeft size={20} />
        <span>Back to Dashboard</span>
      </button>

      {/* Drill-Down Filter Badge */}
      {drillDownLabel && (
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-blue-400" />
            <div>
              <p className="text-blue-400 font-semibold text-sm">Drill-Down Filter Active</p>
              <p className="text-slate-300 text-sm">{drillDownLabel}</p>
            </div>
          </div>
          <button
            onClick={() => {
              navigate('/contracts');
              setDrillDownActive(false);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition text-sm"
          >
            <X className="w-4 h-4" />
            Clear Filter
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className={`text-4xl font-bold ${theme.colors.textPrimary} mb-2`}>
            {drillDownLabel || 'My Contracts'}
          </h1>
          <p className={theme.colors.textSecondary}>Manage and review all your uploaded contracts</p>
        </div>
          <button
            onClick={() => navigate('/upload-contract')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition flex items-center gap-2 shadow-md"
          >
            <FileText className="w-5 h-5" />
            Upload Contract
          </button>
        </div>

        {/* Search & Filters */}
        <div className="space-y-4">
          {/* Main Search Bar */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${theme.colors.textSecondary}`} />
                <input
                  type="text"
                  placeholder="Search by contract name, vendor, type, or keywords..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className={`w-full ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl pl-10 pr-4 py-3 ${theme.colors.textPrimary} placeholder-${theme.colors.textSecondary} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                className={`px-4 py-3 rounded-xl font-medium transition flex items-center gap-2 ${
                  showAdvancedFilters
                    ? 'bg-blue-600 text-white'
                    : `${theme.colors.surface} ${theme.colors.textSecondary} hover:${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`
                }`}
              >
                <Filter className="w-4 h-4" />
                Advanced Filters
              </button>
              <button
                onClick={handleSearch}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition"
              >
                Search
              </button>
              {(searchTerm || filters.vendor || filters.dateFrom || filters.dateTo || filters.riskLevel || filters.contractType || filters.hasAnalysis) && (
                <button
                  onClick={clearFilters}
                  className={`${theme.colors.surfaceHover} hover:${theme.colors.surfaceHover} ${theme.colors.textSecondary} px-4 py-3 rounded-xl transition flex items-center gap-2`}
                >
                  <X className="w-4 h-4" />
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Advanced Filters Panel */}
          {showAdvancedFilters && (
            <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6`}>
              <h3 className={`${theme.colors.textPrimary} font-semibold mb-4 flex items-center gap-2`}>
                <Filter className="w-5 h-5" />
                Advanced Search Filters
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Vendor Filter */}
                <div>
                  <label className={`block text-sm font-medium ${theme.colors.textSecondary} mb-2`}>
                    Vendor/Party Name
                  </label>
                  <input
                    type="text"
                    placeholder="Enter vendor name"
                    value={filters.vendor}
                    onChange={(e) => setFilters({ ...filters, vendor: e.target.value })}
                    className={`w-full ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg px-3 py-2 ${theme.colors.textPrimary} placeholder-${theme.colors.textSecondary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                {/* Date From Filter */}
                <div>
                  <label className={`block text-sm font-medium ${theme.colors.textSecondary} mb-2`}>
                    <Calendar className="w-4 h-4 inline mr-1" />
                    From Date
                  </label>
                  <input
                    type="date"
                    value={filters.dateFrom}
                    onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                    className={`w-full ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg px-3 py-2 ${theme.colors.textPrimary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                {/* Date To Filter */}
                <div>
                  <label className={`block text-sm font-medium ${theme.colors.textSecondary} mb-2`}>
                    <Calendar className="w-4 h-4 inline mr-1" />
                    To Date
                  </label>
                  <input
                    type="date"
                    value={filters.dateTo}
                    onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                    className={`w-full ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg px-3 py-2 ${theme.colors.textPrimary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                {/* Risk Level Filter */}
                <div>
                  <label className={`block text-sm font-medium ${theme.colors.textSecondary} mb-2`}>
                    <AlertTriangle className="w-4 h-4 inline mr-1" />
                    Risk Level
                  </label>
                  <select
                    value={filters.riskLevel}
                    onChange={(e) => setFilters({ ...filters, riskLevel: e.target.value })}
                    className={`w-full ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg px-3 py-2 ${theme.colors.textPrimary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="">All Risk Levels</option>
                    <option value="High">High Risk</option>
                    <option value="Medium">Medium Risk</option>
                    <option value="Low">Low Risk</option>
                  </select>
                </div>

                {/* Contract Type Filter */}
                <div>
                  <label className={`block text-sm font-medium ${theme.colors.textSecondary} mb-2`}>
                    Contract Type
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., NDA, Service Agreement"
                    value={filters.contractType}
                    onChange={(e) => setFilters({ ...filters, contractType: e.target.value })}
                    className={`w-full ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg px-3 py-2 ${theme.colors.textPrimary} placeholder-${theme.colors.textSecondary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>

                {/* Analysis Status Filter */}
                <div>
                  <label className={`block text-sm font-medium ${theme.colors.textSecondary} mb-2`}>
                    Analysis Status
                  </label>
                  <select
                    value={filters.hasAnalysis}
                    onChange={(e) => setFilters({ ...filters, hasAnalysis: e.target.value })}
                    className={`w-full ${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder} rounded-lg px-3 py-2 ${theme.colors.textPrimary} focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="">All Contracts</option>
                    <option value="true">Has Analysis</option>
                    <option value="false">No Analysis</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Filter Buttons */}
          <div className="flex gap-2">
            {filterOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedFilter(option.value)}
                className={`px-4 py-3 rounded-xl font-medium transition flex items-center gap-2 ${
                  selectedFilter === option.value
                    ? 'bg-blue-600 text-white'
                    : `${theme.colors.surface} ${theme.colors.textSecondary} hover:${theme.colors.surfaceHover} border ${theme.colors.surfaceBorder}`
                }`}
              >
                <Filter className="w-4 h-4" />
                {option.label}
                <span className={`px-2 py-0.5 ${theme.colors.surfaceHover} rounded-full text-xs`}>
                  {option.count}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Grid View - Summary of Contract */}
        <DocumentGrid showPagination={true} itemsPerPage={6} />

        {/* Contracts List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : filteredContracts.length === 0 ? (
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-12 text-center`}>
            <FileText className={`w-16 h-16 ${theme.colors.textTertiary} mx-auto mb-4`} />
            <h3 className={`text-xl font-semibold ${theme.colors.textPrimary} mb-2`}>No contracts found</h3>
            <p className={`${theme.colors.textSecondary} mb-6`}>
              {searchTerm || selectedFilter !== 'all'
                ? 'Try adjusting your filters or search term'
                : 'Upload your first contract to get started'}
            </p>
            {!searchTerm && selectedFilter === 'all' && (
              <button
                onClick={() => navigate('/upload-contract')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition"
              >
                Upload Contract
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredContracts.map((contract) => (
              <div
                key={contract.id}
                className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-6 hover:border-${theme.colors.surfaceBorder} transition group`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="bg-blue-600/10 p-3 rounded-lg">
                      <FileText className="w-6 h-6 text-blue-400" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className={`text-lg font-semibold ${theme.colors.textPrimary}`}>
                          {contract.original_filename}
                        </h3>
                        {getStatusBadge(contract)}
                      </div>
                      <div className={`flex flex-wrap items-center gap-4 text-sm ${theme.colors.textSecondary}`}>
                        <span className="flex items-center gap-1">
                          <span className="font-medium">Type:</span>
                          {contract.contract_type || 'Unknown'}
                        </span>
                        {contract.confidence_score && (
                          <span className="flex items-center gap-1">
                            <span className="font-medium">Confidence:</span>
                            {contract.confidence_score.toFixed(1)}%
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <span className="font-medium">Uploaded:</span>
                          {formatDate(contract.uploaded_at)}
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="font-medium">Format:</span>
                          {contract.file_type}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={() => viewContract(contract.id)}
                      className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition"
                      title="View Contract"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/contracts/${contract.id}/graph-dashboard`);
                      }}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 rounded-lg transition"
                      title="Graph Intelligence"
                    >
                      <Network className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/contracts/${contract.id}/what-if`);
                      }}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded-lg transition"
                      title="What-If Analysis"
                    >
                      <FlaskConical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

      {/* Summary */}
      {!loading && filteredContracts.length > 0 && (
        <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl p-4`}>
          <p className={`text-sm ${theme.colors.textSecondary} text-center`}>
            Showing {filteredContracts.length} of {contracts.length} total contracts
          </p>
        </div>
      )}
    </div>
  );
}
