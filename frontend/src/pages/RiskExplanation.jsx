import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader, AlertTriangle, CheckCircle, Info, Shield, Brain, FileText, ChevronDown, ChevronUp, ArrowLeft, Upload, X, Clock } from 'lucide-react';
import api from '../utils/api';
import ReactMarkdown from 'react-markdown';

export default function RiskExplanation() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [showDeviations, setShowDeviations] = useState(true);
  const [uploadProgress, setUploadProgress] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null); // For category details modal
  const [selectedKeyword, setSelectedKeyword] = useState(null); // For keyword sentence highlighting
  const [keywordSentences, setKeywordSentences] = useState([]);
  const [loadingSentences, setLoadingSentences] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [generationProgress, setGenerationProgress] = useState('');

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/contracts/list');

      // Show all contracts, not just ones with analysis
      setContracts(response.data.contracts || []);
      setError('');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load contracts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError('');
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    try {
      setUploading(true);
      setProcessing(true);
      setError('');
      setUploadProgress('Uploading contract...');

      // Step 1: Upload contract
      const formData = new FormData();
      formData.append('file', selectedFile);

      const uploadResponse = await api.post('/contracts/upload', formData);
      const contractId = uploadResponse.data.contractId;

      setUploadProgress('Extracting clauses...');

      // Step 2: Extract clauses
      await api.post(`/contracts/${contractId}/extract-clauses`);

      setUploadProgress('Analyzing risks...');

      // Step 3: Analyze risks
      await api.post(`/contracts/${contractId}/analyze-risk`);

      setUploadProgress('Complete!');

      // Refresh contracts list
      await fetchContracts();

      // Clear file selection
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Show success message
      setTimeout(() => {
        setUploadProgress('');
        alert('Contract uploaded and analyzed successfully! Select it below to view AI explanation.');
      }, 500);

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Upload failed';
      setError(errorMsg);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
      setProcessing(false);
    }
  };

  const handleKeywordClick = async (keyword) => {
    if (!explanation?.contract_id) return;

    try {
      setLoadingSentences(true);
      setSelectedKeyword(keyword);
      setKeywordSentences([]);

      const response = await api.post(`/contracts/${explanation.contract_id}/keyword-sentences`, {
        keyword: keyword
      });

      if (response.data && response.data.sentences) {
        setKeywordSentences(response.data.sentences);
      }
    } catch (err) {
      console.error('Failed to fetch keyword sentences:', err);
      setError(err.response?.data?.error || 'Failed to fetch keyword sentences');
    } finally {
      setLoadingSentences(false);
    }
  };

  const handleGenerateExplanation = async (contractId) => {
    try {
      setGenerating(true);
      setError('');
      setExplanation(null);
      setGenerationProgress('Analyzing contract and generating AI explanation... This may take 30-60 seconds.');

      console.log('Generating explanation for contract:', contractId);

      // Increase timeout for LLM generation (can take 30-60 seconds)
      const response = await api.post(`/contracts/${contractId}/explain-risks`, {}, {
        timeout: 120000 // 2 minutes timeout
      });

      console.log('API Response:', response.data);
      setGenerationProgress('Explanation generated successfully!');

      if (response.data && response.data.data) {
        setExplanation(response.data.data);
        setSelectedContract(contractId);
        console.log('Explanation set:', response.data.data);

        // Scroll to explanation section
        setTimeout(() => {
          const element = document.getElementById('explanation-section');
          console.log('Scrolling to element:', element);
          element?.scrollIntoView({
            behavior: 'smooth'
          });
        }, 100);
      } else {
        setError('Invalid response format from server');
        console.error('Invalid response format:', response.data);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to generate explanation';
      setError(errorMsg);
      setGenerationProgress('');
      console.error('Risk explanation error:', err);
      console.error('Error response:', err.response);

      // Show more detailed error if available
      if (err.response?.data?.message?.includes('clause')) {
        alert('Please extract clauses first before generating risk explanation.');
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        alert('Request timed out. The AI is taking longer than expected. Please try again.');
      } else {
        alert(`Error: ${errorMsg}`);
      }
    } finally {
      setGenerating(false);
      setTimeout(() => setGenerationProgress(''), 3000);
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-red-500 bg-red-950/50 border-red-700';
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

  const getSeverityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'HIGH':
        return 'bg-red-900/50 text-red-300 border-red-800';
      case 'MEDIUM':
        return 'bg-yellow-900/50 text-yellow-300 border-yellow-800';
      case 'LOW':
        return 'bg-green-900/50 text-green-300 border-green-800';
      default:
        return 'bg-slate-900/50 text-slate-300 border-slate-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-300">Loading contracts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="p-2 hover:bg-slate-800 rounded-lg transition"
        >
          <ArrowLeft className="w-6 h-6 text-blue-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="w-8 h-8 text-blue-400" />
            <h1 className="text-4xl font-bold text-white">AI Risk Explanation</h1>
          </div>
          <p className="text-slate-400">
            Get detailed AI-powered explanations of contract risks and recommendations
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-red-300 font-semibold">Error</p>
            <p className="text-red-200 text-sm">{error}</p>
          </div>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-300">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Processing Status */}
      {uploadProgress && (
        <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-4 flex items-center gap-3">
          <Loader className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
          <div>
            <p className="text-blue-300 font-semibold">{uploadProgress}</p>
            <p className="text-slate-400 text-sm">Please wait...</p>
          </div>
        </div>
      )}

      {/* Generation Progress */}
      {generationProgress && (
        <div className="bg-purple-900/20 border border-purple-800 rounded-xl p-4 flex items-center gap-3">
          <Loader className="w-5 h-5 text-purple-400 animate-spin flex-shrink-0" />
          <div>
            <p className="text-purple-300 font-semibold">AI is analyzing...</p>
            <p className="text-slate-300 text-sm">{generationProgress}</p>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-blue-300 font-semibold mb-2">How it works</p>
            <p className="text-slate-300 text-sm leading-relaxed">
              Upload a contract or select an existing one below to generate a comprehensive, AI-powered risk explanation.
              The system will automatically extract clauses, analyze risks, and provide actionable insights and recommendations.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-900/50 border border-slate-800 rounded-xl p-6">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <Upload className="w-6 h-6 text-blue-400" />
          Upload New Contract
        </h2>

        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                accept=".pdf,.docx,.doc,.png,.jpg,.jpeg"
                disabled={uploading}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              {selectedFile && (
                <p className="text-sm text-slate-400 mt-2">
                  Selected: <span className="text-slate-300">{selectedFile.name}</span>
                </p>
              )}
            </div>
            <button
              onClick={handleUploadAndAnalyze}
              disabled={!selectedFile || uploading}
              className={`px-8 py-3 rounded-lg font-semibold transition whitespace-nowrap ${
                uploading || !selectedFile
                  ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {uploading ? (
                <div className="flex items-center gap-2">
                  <Loader className="w-5 h-5 animate-spin" />
                  Processing...
                </div>
              ) : (
                'Upload & Analyze'
              )}
            </button>
          </div>
          <p className="text-xs text-slate-500">
            Supported formats: PDF, DOCX, PNG, JPG (Max 25MB)
          </p>
        </div>
      </div>

      {/* Contract Selection */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-400" />
          Your Contracts ({contracts.length})
        </h2>

        {contracts.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
            <Shield className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 text-lg mb-2">No contracts found</p>
            <p className="text-slate-500 text-sm">
              Upload a contract above to get started with AI risk analysis
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {contracts.map((contract) => (
              <div
                key={contract.id}
                className={`bg-slate-900 border rounded-xl p-6 transition ${
                  selectedContract === contract.id ? 'border-blue-600 bg-slate-900/80' : 'border-slate-800 hover:border-blue-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {contract.originalFilename || contract.filename}
                    </h3>
                    <div className="flex flex-wrap gap-3 text-sm mb-3">
                      <span className="text-slate-400">
                        Type: <span className="text-slate-300">{contract.contractType}</span>
                      </span>
                      <span className="text-slate-400">
                        Uploaded: <span className="text-slate-300">
                          {new Date(contract.uploadedAt).toLocaleDateString()}
                        </span>
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {contract.hasRiskAnalysis && (
                        <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs border border-green-800">
                          ✓ Risk Analysis Done
                        </span>
                      )}
                      {contract.hasClauses && (
                        <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs border border-blue-800">
                          ✓ Clauses Extracted
                        </span>
                      )}
                      {!contract.hasClauses && !contract.hasRiskAnalysis && (
                        <span className="px-2 py-1 bg-yellow-900/50 text-yellow-300 rounded text-xs border border-yellow-800">
                          ⚠ Analysis Pending
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleGenerateExplanation(contract.id)}
                    disabled={generating || !contract.hasClauses}
                    className={`px-6 py-2 rounded-lg font-medium transition ${
                      generating || !contract.hasClauses
                        ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {generating && selectedContract === contract.id ? (
                      <div className="flex items-center gap-2">
                        <Loader className="w-4 h-4 animate-spin" />
                        Generating...
                      </div>
                    ) : (
                      'Generate Explanation'
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Risk Explanation Section */}
      {explanation && (
        <div id="explanation-section" className="space-y-6">
          {/* Risk Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className={`border rounded-xl p-4 ${getRiskLevelColor(explanation.risk_level)}`}>
              <p className="text-sm text-slate-300 mb-1">Risk Level</p>
              <p className="text-2xl font-bold">{explanation.risk_level}</p>
            </div>
            <div className="border rounded-xl p-4 bg-slate-900/30 border-slate-800">
              <p className="text-sm text-slate-300 mb-1">Risk Score</p>
              <p className="text-2xl font-bold text-white">{explanation.risk_score}/100</p>
            </div>
            <div className="border rounded-xl p-4 bg-slate-900/30 border-slate-800">
              <p className="text-sm text-slate-300 mb-1">Total Issues</p>
              <p className="text-2xl font-bold text-white">{explanation.total_deviations}</p>
            </div>
            <div className="border rounded-xl p-4 bg-slate-900/30 border-slate-800">
              <p className="text-sm text-slate-300 mb-1">Critical Issues</p>
              <p className="text-2xl font-bold text-red-400">{explanation.critical_issues}</p>
            </div>
          </div>

          {/* Processing Time */}
          {explanation.timings && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-5 h-5 text-blue-400" />
                <p className="text-slate-300 text-sm font-semibold">Processing Time</p>
              </div>
              <div className="flex gap-3">
                {explanation.timings.llm_generation && (
                  <div className="bg-slate-800 rounded px-3 py-2">
                    <p className="text-xs text-slate-400">LLM Generation</p>
                    <p className="text-sm font-semibold text-white">{explanation.timings.llm_generation}s</p>
                  </div>
                )}
                {explanation.timings.total && (
                  <div className="bg-blue-900/30 border border-blue-800 rounded px-3 py-2">
                    <p className="text-xs text-blue-400">Total</p>
                    <p className="text-sm font-semibold text-blue-300">{explanation.timings.total}s</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 20 Category Risk Breakdown */}
          {explanation.detailed_breakdown && Object.keys(explanation.detailed_breakdown).length > 0 && (
            <div className="bg-gradient-to-br from-slate-900 to-slate-900/50 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <Shield className="w-6 h-6 text-purple-400" />
                <h2 className="text-2xl font-bold text-white">20-Category Risk Analysis</h2>
              </div>
              <p className="text-slate-400 text-sm mb-6">
                Comprehensive risk scoring across 20 distinct categories using keyword-based detection. Each category scored 0-5.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(explanation.detailed_breakdown)
                  .sort((a, b) => b[1].score - a[1].score) // Sort by score descending
                  .map(([category, data]) => {
                    const scorePercentage = (data.score / 5) * 100;
                    const getScoreColor = (score) => {
                      if (score >= 4) return 'bg-red-500';
                      if (score >= 3) return 'bg-orange-500';
                      if (score >= 2) return 'bg-yellow-500';
                      if (score >= 1) return 'bg-blue-500';
                      return 'bg-green-500';
                    };

                    return (
                      <button
                        key={category}
                        onClick={() => setSelectedCategory({ category, data })}
                        className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 hover:bg-slate-800 hover:border-blue-500 transition cursor-pointer text-left w-full"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <h3 className="text-sm font-semibold text-white flex-1">
                            {data.display_name}
                          </h3>
                          <span className={`text-lg font-bold ml-2 ${
                            data.score >= 4 ? 'text-red-400' :
                            data.score >= 3 ? 'text-orange-400' :
                            data.score >= 2 ? 'text-yellow-400' :
                            data.score >= 1 ? 'text-blue-400' :
                            'text-green-400'
                          }`}>
                            {data.score.toFixed(1)}
                          </span>
                        </div>

                        {/* Progress bar */}
                        <div className="w-full bg-slate-700 rounded-full h-2 mb-2">
                          <div
                            className={`h-2 rounded-full transition-all ${getScoreColor(data.score)}`}
                            style={{ width: `${scorePercentage}%` }}
                          ></div>
                        </div>

                        {/* Keyword info */}
                        {data.keyword_hits > 0 && (
                          <div className="text-xs text-slate-400 mt-2">
                            <p className="mb-1">{data.keyword_hits} risk keyword{data.keyword_hits !== 1 ? 's' : ''} detected</p>
                            {data.found_keywords && data.found_keywords.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {data.found_keywords.slice(0, 3).map((kw, idx) => (
                                  <span key={idx} className="text-xs px-2 py-0.5 bg-slate-900/50 text-slate-300 rounded border border-slate-700">
                                    {kw}
                                  </span>
                                ))}
                                {data.found_keywords.length > 3 && (
                                  <span className="text-xs px-2 py-0.5 text-slate-400">
                                    +{data.found_keywords.length - 3} more
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                        <div className="text-xs text-blue-400 mt-2 text-center">
                          Click to view details →
                        </div>
                      </button>
                    );
                  })}
              </div>
            </div>
          )}

          {/* LLM Explanation */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-900/50 border border-slate-800 rounded-xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <Brain className="w-6 h-6 text-blue-400" />
              <h2 className="text-2xl font-bold text-white">AI-Powered Risk Analysis</h2>
            </div>

            <div className="prose prose-invert prose-slate max-w-none text-slate-300 leading-relaxed">
              <ReactMarkdown
                components={{
                  h2: ({children}) => (
                    <h2 className="text-xl font-bold text-white mt-8 mb-4 flex items-center gap-2">{children}</h2>
                  ),
                  h3: ({children}) => (
                    <h3 className="text-lg font-semibold text-white mt-6 mb-3">{children}</h3>
                  ),
                  ul: ({children}) => (
                    <ul className="list-disc list-inside space-y-2 text-slate-300 ml-4">{children}</ul>
                  ),
                  li: ({children}) => (
                    <li className="text-slate-300 leading-relaxed">{children}</li>
                  ),
                  p: ({children}) => (
                    <p className="text-slate-300 mb-4 leading-relaxed">{children}</p>
                  ),
                  strong: ({children}) => (
                    <strong className="text-white font-semibold">{children}</strong>
                  ),
                }}
              >
                {explanation.llm_explanation}
              </ReactMarkdown>
            </div>
          </div>

          {/* Deviations Detail */}
          {explanation.deviations && explanation.deviations.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <button
                onClick={() => setShowDeviations(!showDeviations)}
                className="w-full flex items-center justify-between mb-4"
              >
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  Identified Deviations ({explanation.deviations.length})
                </h2>
                {showDeviations ? (
                  <ChevronUp className="w-5 h-5 text-slate-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-slate-400" />
                )}
              </button>

              {showDeviations && (
                <div className="space-y-4">
                  {explanation.deviations.map((deviation, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-800/50 border border-slate-700 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="text-lg font-semibold text-white">
                          {deviation.clause_name}
                        </h3>
                        <div className="flex gap-2">
                          <span className={`text-xs px-2 py-1 rounded border ${getSeverityBadge(deviation.severity)}`}>
                            {deviation.severity}
                          </span>
                          <span className="text-xs px-2 py-1 rounded bg-slate-900/50 text-slate-300 border border-slate-700">
                            {deviation.deviation_type}
                          </span>
                        </div>
                      </div>
                      <p className="text-slate-300 text-sm mb-3">{deviation.description}</p>
                      <div className="bg-blue-900/20 border border-blue-800 rounded p-3">
                        <p className="text-blue-300 text-xs font-semibold mb-1">Recommendation</p>
                        <p className="text-slate-300 text-sm">{deviation.recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4 justify-end">
            <button
              onClick={() => navigate(`/contract/${explanation.contract_id}/clauses`)}
              className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition"
            >
              View Contract Details
            </button>
            <button
              onClick={() => window.print()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
            >
              Print Report
            </button>
          </div>
        </div>
      )}

      {/* Category Details Modal */}
      {selectedCategory && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedCategory(null)}>
          <div className="bg-slate-900 rounded-2xl border border-slate-700 max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">
                  {selectedCategory.data.display_name}
                </h2>
                <p className="text-sm text-slate-400">
                  Risk Score: <span className={`font-semibold ${
                    selectedCategory.data.score >= 4 ? 'text-red-400' :
                    selectedCategory.data.score >= 3 ? 'text-orange-400' :
                    selectedCategory.data.score >= 2 ? 'text-yellow-400' :
                    selectedCategory.data.score >= 1 ? 'text-blue-400' :
                    'text-green-400'
                  }`}>{selectedCategory.data.score.toFixed(1)}/5</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedCategory(null)}
                className="p-2 hover:bg-slate-800 rounded-lg transition"
              >
                <X className="w-6 h-6 text-slate-400 hover:text-white" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {selectedCategory.data.keyword_hits > 0 ? (
                <div>
                  <p className="text-slate-300 mb-4">
                    Found <span className="font-semibold text-white">{selectedCategory.data.keyword_hits}</span> risk keyword
                    {selectedCategory.data.keyword_hits !== 1 ? 's' : ''} in this category:
                  </p>
                  <p className="text-sm text-blue-400 mb-3">Click any keyword to see full sentences containing it</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedCategory.data.found_keywords.map((kw, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleKeywordClick(kw)}
                        className="px-3 py-1.5 bg-slate-800 text-slate-200 rounded-lg border border-slate-700 text-sm hover:bg-slate-700 hover:border-blue-500 transition cursor-pointer"
                      >
                        {kw}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                  <p className="text-slate-300">No risk keywords detected in this category</p>
                  <p className="text-slate-400 text-sm mt-2">This is a positive indicator</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Keyword Sentences Modal */}
      {selectedKeyword && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] flex items-center justify-center p-4"
          onClick={() => {
            setSelectedKeyword(null);
            setKeywordSentences([]);
          }}
        >
          <div
            className="bg-slate-900 rounded-2xl border border-slate-700 max-w-4xl w-full max-h-[80vh] overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">
                  Sentences containing "{selectedKeyword}"
                </h2>
                <p className="text-sm text-slate-400">
                  {loadingSentences ? 'Loading...' : `${keywordSentences.length} occurrence${keywordSentences.length !== 1 ? 's' : ''} found`}
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedKeyword(null);
                  setKeywordSentences([]);
                }}
                className="p-2 hover:bg-slate-800 rounded-lg transition"
              >
                <X className="w-6 h-6 text-slate-400 hover:text-white" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {loadingSentences ? (
                <div className="flex items-center justify-center py-12">
                  <Loader className="w-8 h-8 text-blue-400 animate-spin" />
                </div>
              ) : keywordSentences.length > 0 ? (
                <div className="space-y-4">
                  {keywordSentences.map((sentence, idx) => (
                    <div key={idx} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                          {idx + 1}
                        </div>
                        <div className="flex-1">
                          <p className="text-slate-200 leading-relaxed">
                            {sentence.context.split(new RegExp(`(${selectedKeyword})`, 'gi')).map((part, i) =>
                              part.toLowerCase() === selectedKeyword.toLowerCase() ? (
                                <mark key={i} className="bg-yellow-400 text-black font-semibold px-1 rounded">
                                  {part}
                                </mark>
                              ) : (
                                <span key={i}>{part}</span>
                              )
                            )}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <AlertTriangle className="w-12 h-12 text-yellow-400 mx-auto mb-3" />
                  <p className="text-slate-300">No sentences found containing "{selectedKeyword}"</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
