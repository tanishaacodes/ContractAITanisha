import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader, ClipboardCheck, FileText, TrendingUp, AlertCircle, CheckCircle, ChevronDown, ChevronUp, Calendar, User, Tag, AlertTriangle, RefreshCw, Upload, Plus, X, ArrowLeft } from 'lucide-react';
import api from '../utils/api';

export default function ObligationTracker() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [obligations, setObligations] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [expandedObligations, setExpandedObligations] = useState({});

  const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB
  const ALLOWED_TYPES = ['.docx', '.pdf', '.png', '.jpg', '.jpeg'];

  // Load contracts on mount
  useEffect(() => {
    loadContracts();
  }, []);

  // Load obligations when contract is selected
  useEffect(() => {
    if (selectedContract) {
      loadObligations(selectedContract.id);
    } else {
      setObligations([]);
    }
  }, [selectedContract]);

  const loadContracts = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await api.get('/contracts/list');
      const contractsList = response.data.contracts || [];
      setContracts(contractsList);
    } catch (err) {
      setError('Failed to load contracts');
      console.error('Load contracts error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadObligations = async (contractId) => {
    try {
      setError('');
      const response = await api.get(`/contracts/${contractId}/obligations`);
      setObligations(response.data.obligations || []);
    } catch (err) {
      if (err.response?.status === 404) {
        setObligations([]);
      } else {
        setError('Failed to load obligations');
        console.error('Load obligations error:', err);
      }
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setError('');

    // Validate file type
    const fileExt = '.' + selectedFile.name.split('.').pop().toLowerCase();
    if (!ALLOWED_TYPES.includes(fileExt)) {
      setError('Unsupported file type. Allowed: DOCX, PDF, PNG, JPG, JPEG');
      return;
    }

    // Validate file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File exceeds 25MB limit (${(selectedFile.size / 1024 / 1024).toFixed(2)}MB)`);
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    try {
      setUploading(true);
      setError('');

      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/contracts/upload', formData);

      // Reload contracts list
      await loadContracts();

      // Auto-select the newly uploaded contract
      const newContract = {
        id: response.data.contractId,
        originalFilename: response.data.filename,
        original_filename: response.data.filename,
        contractType: response.data.contractType,
        contract_type: response.data.contractType,
      };

      setSelectedContract(newContract);
      setFile(null);
      setShowUpload(false);

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Upload failed';
      setError(errorMsg);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateObligations = async () => {
    if (!selectedContract) return;

    try {
      setGenerating(true);
      setError('');
      setObligations([]);

      const response = await api.post(`/contracts/${selectedContract.id}/generate-obligations`);
      setObligations(response.data.obligations || []);

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to generate obligations';
      setError(errorMsg);
      console.error('Obligation generation error:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleObligation = async (obligation) => {
    try {
      const newStatus = !obligation.is_completed;

      const response = await api.patch(`/obligations/${obligation.id}/update`, {
        is_completed: newStatus
      });

      setObligations(prevObligations =>
        prevObligations.map(obl =>
          obl.id === obligation.id
            ? { ...obl, is_completed: newStatus, completed_at: response.data.obligation.completed_at }
            : obl
        )
      );

    } catch (err) {
      console.error('Toggle error:', err);
      setError('Failed to update obligation status');
    }
  };

  const toggleExpand = (obligationId) => {
    setExpandedObligations(prev => ({
      ...prev,
      [obligationId]: !prev[obligationId]
    }));
  };

  const getCategoryColor = (category) => {
    const colors = {
      PAYMENT: 'bg-green-900/30 text-green-400 border-green-800',
      DELIVERY: 'bg-blue-900/30 text-blue-400 border-blue-800',
      COMPLIANCE: 'bg-purple-900/30 text-purple-400 border-purple-800',
      REPORTING: 'bg-yellow-900/30 text-yellow-400 border-yellow-800',
      NOTICE: 'bg-cyan-900/30 text-cyan-400 border-cyan-800',
      TERMINATION: 'bg-red-900/30 text-red-400 border-red-800',
      OTHER: 'bg-slate-900/30 text-slate-400 border-slate-800',
    };
    return colors[category] || colors.OTHER;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      HIGH: 'bg-red-900/30 text-red-400 border-red-800',
      MEDIUM: 'bg-yellow-900/30 text-yellow-400 border-yellow-800',
      LOW: 'bg-green-900/30 text-green-400 border-green-800',
    };
    return colors[priority] || colors.MEDIUM;
  };

  const getPartyIcon = (party) => {
    if (party === 'YOUR_COMPANY') return '👤 You';
    if (party === 'COUNTERPARTY') return '🏢 Them';
    return '🤝 Both';
  };

  const filteredObligations = obligations.filter(obl => {
    if (filter === 'ALL') return true;
    if (filter === 'PENDING') return !obl.is_completed;
    if (filter === 'COMPLETED') return obl.is_completed;
    return obl.responsible_party === filter;
  });

  const stats = {
    total: obligations.length,
    completed: obligations.filter(o => o.is_completed).length,
    pending: obligations.filter(o => !o.is_completed).length,
    yourCompany: obligations.filter(o => o.responsible_party === 'YOUR_COMPANY').length,
    counterparty: obligations.filter(o => o.responsible_party === 'COUNTERPARTY').length,
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition"
        >
          <ArrowLeft size={20} />
          <span>Back</span>
        </button>

        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-purple-500/50">
            <ClipboardCheck className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-white">Obligation Tracker</h1>
            <p className="text-slate-400 mt-1">Extract and track contractual obligations</p>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-300 font-semibold">Error</p>
              <p className="text-red-200 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Contract Selector */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-purple-400" />
              Select Contract
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="flex items-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition text-sm"
              >
                {showUpload ? (
                  <>
                    <X className="w-4 h-4" />
                    Cancel
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Upload New
                  </>
                )}
              </button>
              <button
                onClick={loadContracts}
                disabled={loading}
                className="p-2 hover:bg-slate-800 rounded-lg transition text-slate-400 hover:text-white"
                title="Refresh contracts"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Upload Form - Collapsible */}
          {showUpload && (
            <div className="mb-6 p-4 bg-slate-800/50 border border-slate-700 rounded-xl">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Upload className="w-4 h-4 text-purple-400" />
                Upload New Contract
              </h3>

              <div className="bg-slate-800 border-2 border-dashed border-slate-700 rounded-xl p-6 hover:border-purple-500 hover:bg-slate-750 transition">
                <div className="text-center space-y-3">
                  <FileText className="w-10 h-10 mx-auto text-purple-400" />
                  <div>
                    <p className="text-sm font-semibold text-white">Select your contract file</p>
                    <p className="text-xs text-slate-400 mt-1">DOCX, PDF, PNG, JPG, JPEG (Max 25MB)</p>
                  </div>

                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileSelect}
                    accept=".docx,.pdf,.png,.jpg,.jpeg"
                    className="hidden"
                  />

                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition text-sm"
                  >
                    Choose File
                  </button>

                  {file && (
                    <div className="mt-3 p-2 bg-slate-900 rounded-lg">
                      <p className="text-xs text-slate-300">
                        <span className="font-semibold text-white">Selected:</span> {file.name}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        Size: {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {file && (
                <button
                  type="button"
                  onClick={handleUpload}
                  disabled={uploading}
                  className="mt-4 w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Upload Contract
                    </>
                  )}
                </button>
              )}
            </div>
          )}

          {/* Contract Dropdown */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader className="w-6 h-6 animate-spin text-purple-400" />
              <span className="ml-2 text-slate-400">Loading contracts...</span>
            </div>
          ) : contracts.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-400 mb-4">No contracts found. Upload a contract above or go to Upload page.</p>
              <button
                onClick={() => navigate('/upload')}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
              >
                Go to Upload Page
              </button>
            </div>
          ) : (
            <select
              value={selectedContract?.id || ''}
              onChange={(e) => {
                const contract = contracts.find(c => c.id === e.target.value);
                setSelectedContract(contract);
              }}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
            >
              <option value="">-- Select a contract --</option>
              {contracts.map((contract) => (
                <option key={contract.id} value={contract.id}>
                  {contract.originalFilename || contract.original_filename}
                  {contract.contractType && ` (${contract.contractType})`}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Generate Button */}
        {selectedContract && obligations.length === 0 && !generating && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-400" />
              Generate Obligations
            </h2>
            <p className="text-slate-300 mb-4">
              No obligations found for this contract. Click below to extract obligations using AI.
            </p>
            <button
              onClick={handleGenerateObligations}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold rounded-lg transition flex items-center justify-center gap-2"
            >
              <ClipboardCheck className="w-5 h-5" />
              Generate Obligations
            </button>
          </div>
        )}

        {/* Generating State */}
        {generating && (
          <div className="bg-slate-900 border border-purple-800 rounded-xl p-8">
            <div className="text-center space-y-4">
              <Loader className="w-12 h-12 animate-spin text-purple-400 mx-auto" />
              <div>
                <p className="text-xl font-semibold text-white">Extracting Obligations...</p>
                <p className="text-slate-400 mt-2">This may take 30-60 seconds. Please wait.</p>
                <p className="text-slate-500 text-sm mt-1">AI is analyzing the contract and identifying all obligations.</p>
              </div>
            </div>
          </div>
        )}

        {/* Obligations Display */}
        {obligations.length > 0 && !generating && (
          <div className="space-y-6">
            {/* Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <p className="text-sm text-slate-400 mb-1">Total</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <div className="bg-green-900/20 border border-green-800 rounded-xl p-4">
                <p className="text-sm text-green-300 mb-1">Completed</p>
                <p className="text-2xl font-bold text-green-400">{stats.completed}</p>
              </div>
              <div className="bg-yellow-900/20 border border-yellow-800 rounded-xl p-4">
                <p className="text-sm text-yellow-300 mb-1">Pending</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.pending}</p>
              </div>
              <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-4">
                <p className="text-sm text-blue-300 mb-1">Your Obligations</p>
                <p className="text-2xl font-bold text-blue-400">{stats.yourCompany}</p>
              </div>
              <div className="bg-purple-900/20 border border-purple-800 rounded-xl p-4">
                <p className="text-sm text-purple-300 mb-1">Their Obligations</p>
                <p className="text-2xl font-bold text-purple-400">{stats.counterparty}</p>
              </div>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2 flex-wrap">
              {['ALL', 'YOUR_COMPANY', 'COUNTERPARTY', 'PENDING', 'COMPLETED'].map((filterOption) => (
                <button
                  key={filterOption}
                  onClick={() => setFilter(filterOption)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    filter === filterOption
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {filterOption === 'YOUR_COMPANY' && 'Your Obligations'}
                  {filterOption === 'COUNTERPARTY' && 'Their Obligations'}
                  {filterOption === 'ALL' && 'All'}
                  {filterOption === 'PENDING' && 'Pending'}
                  {filterOption === 'COMPLETED' && 'Completed'}
                </button>
              ))}
            </div>

            {/* Obligations List */}
            <div className="space-y-3">
              {filteredObligations.length === 0 ? (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center">
                  <p className="text-slate-400">No obligations found for this filter.</p>
                </div>
              ) : (
                filteredObligations.map((obligation) => (
                  <div
                    key={obligation.id}
                    className={`bg-slate-900 border rounded-xl p-4 transition ${
                      obligation.is_completed
                        ? 'border-green-800 bg-green-900/10'
                        : 'border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Checkbox */}
                      <input
                        type="checkbox"
                        checked={obligation.is_completed}
                        onChange={() => handleToggleObligation(obligation)}
                        className="mt-1 w-5 h-5 rounded border-slate-600 text-purple-600 focus:ring-purple-500 focus:ring-offset-slate-900 cursor-pointer"
                      />

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Title and Expand Button */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h3 className={`font-semibold text-lg ${
                            obligation.is_completed ? 'text-slate-500 line-through' : 'text-white'
                          }`}>
                            {obligation.title}
                          </h3>
                          <button
                            type="button"
                            onClick={() => toggleExpand(obligation.id)}
                            className="flex-shrink-0 p-1 hover:bg-slate-800 rounded transition"
                          >
                            {expandedObligations[obligation.id] ? (
                              <ChevronUp className="w-5 h-5 text-slate-400" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-slate-400" />
                            )}
                          </button>
                        </div>

                        {/* Badges */}
                        <div className="flex flex-wrap gap-2 mb-3">
                          <span className={`text-xs px-2 py-1 rounded border ${getCategoryColor(obligation.category)}`}>
                            <Tag className="w-3 h-3 inline mr-1" />
                            {obligation.category}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded border ${getPriorityColor(obligation.priority)}`}>
                            <AlertTriangle className="w-3 h-3 inline mr-1" />
                            {obligation.priority}
                          </span>
                          <span className="text-xs px-2 py-1 rounded border bg-slate-800 text-slate-300 border-slate-700">
                            <User className="w-3 h-3 inline mr-1" />
                            {getPartyIcon(obligation.responsible_party)}
                          </span>
                          {obligation.due_date_text && (
                            <span className="text-xs px-2 py-1 rounded border bg-slate-800 text-slate-300 border-slate-700">
                              <Calendar className="w-3 h-3 inline mr-1" />
                              {obligation.due_date_text}
                            </span>
                          )}
                        </div>

                        {/* Description */}
                        <p className={`text-sm mb-2 ${
                          obligation.is_completed ? 'text-slate-500' : 'text-slate-300'
                        }`}>
                          {expandedObligations[obligation.id]
                            ? obligation.description
                            : obligation.description.substring(0, 150) + (obligation.description.length > 150 ? '...' : '')}
                        </p>

                        {/* Expanded Details */}
                        {expandedObligations[obligation.id] && (
                          <div className="mt-4 pt-4 border-t border-slate-800 space-y-2">
                            {obligation.clause_reference && (
                              <div>
                                <p className="text-xs text-slate-400 mb-1">Clause Reference:</p>
                                <p className="text-sm text-slate-300">{obligation.clause_reference}</p>
                              </div>
                            )}
                            {obligation.completed_at && (
                              <div>
                                <p className="text-xs text-green-400 mb-1">Completed:</p>
                                <p className="text-sm text-slate-300">
                                  {new Date(obligation.completed_at).toLocaleString()}
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Action Buttons */}
            {selectedContract && (
              <div className="flex gap-4 justify-between pt-4">
                <button
                  onClick={() => handleGenerateObligations()}
                  disabled={generating}
                  className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition disabled:opacity-50"
                >
                  Regenerate Obligations
                </button>
                <button
                  onClick={() => navigate(`/contract/${selectedContract.id}/clauses`)}
                  className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
                >
                  View Contract Details
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
