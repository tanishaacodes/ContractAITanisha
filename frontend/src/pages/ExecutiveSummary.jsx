import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader, Briefcase, Upload, FileText, TrendingUp, AlertCircle, CheckCircle, RefreshCw, Plus, X, ArrowLeft } from 'lucide-react';
import api from '../utils/api';
import ReactMarkdown from 'react-markdown';

export default function ExecutiveSummary() {
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
  const [summary, setSummary] = useState(null);

  const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB
  const ALLOWED_TYPES = ['.docx', '.pdf', '.png', '.jpg', '.jpeg'];

  // Load contracts on mount
  useEffect(() => {
    loadContracts();
  }, []);

  // Load summary when contract is selected
  useEffect(() => {
    if (selectedContract) {
      loadSummary(selectedContract.id);
    } else {
      setSummary(null);
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

  const loadSummary = async (contractId) => {
    try {
      setError('');
      // Try to fetch existing summary/risk analysis
      const riskResponse = await api.get(`/contracts/${contractId}/risk-analysis`);

      if (riskResponse.data.riskAnalysis && riskResponse.data.riskAnalysis.executive_summary) {
        setSummary({
          text: riskResponse.data.riskAnalysis.executive_summary,
          riskAnalysis: riskResponse.data.riskAnalysis
        });
      } else {
        setSummary(null);
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setSummary(null);
      } else {
        console.error('Load summary error:', err);
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

  const handleGenerateSummary = async () => {
    if (!selectedContract) return;

    try {
      setGenerating(true);
      setError('');
      setSummary(null);

      const response = await api.post(`/contracts/${selectedContract.id}/generate-summary`);

      setSummary({
        text: response.data.executiveSummary,
        riskAnalysis: response.data.riskAnalysis
      });

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to generate summary';
      setError(errorMsg);
      console.error('Summary generation error:', err);
    } finally {
      setGenerating(false);
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'HIGH':
        return 'text-red-400 bg-red-900/30 border-red-800';
      case 'MEDIUM':
        return 'text-yellow-400 bg-yellow-900/30 border-yellow-800';
      case 'LOW':
        return 'text-green-400 bg-green-900/30 border-green-800';
      default:
        return 'text-slate-400 bg-slate-900/30 border-slate-800';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
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
          <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-2xl shadow-blue-500/50">
            <Briefcase className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-white">Executive Summary</h1>
            <p className="text-slate-400 mt-1">Generate AI-powered executive summaries</p>
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
              <FileText className="w-5 h-5 text-blue-400" />
              Select Contract
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setShowUpload(!showUpload)}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm"
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
                <Upload className="w-4 h-4 text-blue-400" />
                Upload New Contract
              </h3>

              <div className="bg-slate-800 border-2 border-dashed border-slate-700 rounded-xl p-6 hover:border-blue-500 hover:bg-slate-750 transition">
                <div className="text-center space-y-3">
                  <FileText className="w-10 h-10 mx-auto text-blue-400" />
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
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm"
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
                  className="mt-4 w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
              <Loader className="w-6 h-6 animate-spin text-blue-400" />
              <span className="ml-2 text-slate-400">Loading contracts...</span>
            </div>
          ) : contracts.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-400 mb-4">No contracts found. Upload a contract above or go to Upload page.</p>
              <button
                onClick={() => navigate('/upload')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
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
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition"
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

        {/* Generate Summary Button */}
        {selectedContract && !summary && !generating && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              Generate Summary
            </h2>
            <p className="text-slate-300 mb-4">
              No summary found for this contract. Click below to generate an executive summary using AI.
            </p>
            <button
              onClick={handleGenerateSummary}
              className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition flex items-center justify-center gap-2"
            >
              <Briefcase className="w-5 h-5" />
              Generate Executive Summary
            </button>
          </div>
        )}

        {/* Generating State */}
        {generating && (
          <div className="bg-slate-900 border border-blue-800 rounded-xl p-8">
            <div className="text-center space-y-4">
              <Loader className="w-12 h-12 animate-spin text-blue-400 mx-auto" />
              <div>
                <p className="text-xl font-semibold text-white">Generating Executive Summary...</p>
                <p className="text-slate-400 mt-2">This may take 30-60 seconds. Please wait.</p>
                <p className="text-slate-500 text-sm mt-1">AI is analyzing the contract and creating a comprehensive summary.</p>
              </div>
            </div>
          </div>
        )}

        {/* Summary Display */}
        {summary && !generating && (
          <div className="space-y-6">
            {/* Quick Metrics */}
            {summary.riskAnalysis && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className={`border rounded-xl p-4 ${getRiskLevelColor(summary.riskAnalysis.risk_level)}`}>
                  <p className="text-sm opacity-80 mb-1">Risk Level</p>
                  <p className="text-2xl font-bold">{summary.riskAnalysis.risk_level}</p>
                </div>
                <div className="border rounded-xl p-4 bg-slate-900/30 border-slate-800">
                  <p className="text-sm text-slate-300 mb-1">Risk Score</p>
                  <p className="text-2xl font-bold text-white">{summary.riskAnalysis.risk_score}/100</p>
                </div>
                <div className="border rounded-xl p-4 bg-slate-900/30 border-slate-800">
                  <p className="text-sm text-slate-300 mb-1">Total Issues</p>
                  <p className="text-2xl font-bold text-white">{summary.riskAnalysis.total_deviations}</p>
                </div>
                <div className="border rounded-xl p-4 bg-slate-900/30 border-slate-800">
                  <p className="text-sm text-slate-300 mb-1">Critical Issues</p>
                  <p className="text-2xl font-bold text-red-400">{summary.riskAnalysis.critical_issues}</p>
                </div>
              </div>
            )}

            {/* Executive Summary Card */}
            <div className="bg-gradient-to-br from-blue-900 to-blue-800 border border-blue-700 rounded-xl p-8">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3 mb-6">
                <Briefcase className="w-7 h-7 text-blue-300" />
                Executive Summary
              </h2>
              <div className="prose prose-invert max-w-none text-blue-50">
                <ReactMarkdown
                  components={{
                    h2: ({children}) => <h2 className="text-xl font-bold text-white mt-6 mb-3">{children}</h2>,
                    h3: ({children}) => <h3 className="text-lg font-semibold text-white mt-4 mb-2">{children}</h3>,
                    p: ({children}) => <p className="text-blue-100 mb-4 leading-relaxed">{children}</p>,
                    ul: ({children}) => <ul className="list-disc list-inside space-y-2 mb-4 text-blue-100">{children}</ul>,
                    li: ({children}) => <li className="text-blue-100 ml-2">{children}</li>,
                    strong: ({children}) => <strong className="text-white font-semibold">{children}</strong>,
                  }}
                >
                  {summary.text}
                </ReactMarkdown>
              </div>
            </div>

            {/* Action Buttons */}
            {selectedContract && (
              <div className="flex gap-4 justify-between pt-4">
                <button
                  onClick={() => handleGenerateSummary()}
                  disabled={generating}
                  className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition disabled:opacity-50"
                >
                  Regenerate Summary
                </button>
                <div className="flex gap-4">
                  <button
                    onClick={() => navigate(`/contract/${selectedContract.id}/clauses`)}
                    className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition"
                  >
                    View Contract Details
                  </button>
                  <button
                    onClick={() => window.print()}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                  >
                    Print Summary
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
