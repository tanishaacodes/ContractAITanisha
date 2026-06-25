import { useState, useEffect } from 'react';
import { GitCompare, Search, AlertCircle, CheckCircle, XCircle, Upload, FileText, Minus, ArrowLeft, X, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

const ContractCompare = () => {
  const navigate = useNavigate();
  const [referenceFile, setReferenceFile] = useState(null);
  const [compareFiles, setCompareFiles] = useState([]);
  const [keywords, setKeywords] = useState('');
  const [loading, setLoading] = useState(false);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [keywordModal, setKeywordModal] = useState(null); // { keyword, contractName, occurrences }
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Trigger entrance animations
    setIsVisible(true);
  }, []);

  const handleReferenceFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setReferenceFile(file);
    }
  };

  const handleCompareFilesChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 3) {
      alert('Maximum 3 contracts can be selected for comparison');
      return;
    }
    setCompareFiles(files);
  };

  const removeCompareFile = (index) => {
    setCompareFiles(compareFiles.filter((_, i) => i !== index));
  };

  const handleCompare = async () => {
    if (!referenceFile) {
      alert('Please select a reference contract file');
      return;
    }

    if (compareFiles.length === 0) {
      alert('Please select at least 1 contract to compare');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('reference_file', referenceFile);
      compareFiles.forEach((file) => {
        formData.append('compare_files', file);
      });

      if (keywords.trim()) {
        formData.append('keywords', keywords);
      }

      const res = await api.post('/contracts/compare-upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setComparisonResults(res.data);
    } catch (error) {
      console.error('Error comparing contracts:', error);
      alert('Error comparing contracts: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL': return 'text-red-500';
      case 'HIGH': return 'text-orange-500';
      case 'MEDIUM': return 'text-yellow-500';
      case 'LOW': return 'text-green-500';
      default: return 'text-gray-500';
    }
  };

  const getRiskBgColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL': return 'bg-red-900/20 border-red-800';
      case 'HIGH': return 'bg-orange-900/20 border-orange-800';
      case 'MEDIUM': return 'bg-yellow-900/20 border-yellow-800';
      case 'LOW': return 'bg-green-900/20 border-green-800';
      default: return 'bg-gray-900/20 border-gray-800';
    }
  };

  return (
    <div className="space-y-6 min-h-screen">
      {/* Animated Background Gradient */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-2xl opacity-10"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-2xl opacity-10"></div>
      </div>

      {/* Header */}
      <div className={`flex items-center justify-between transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
        <div>
          <button
            onClick={() => navigate(-1)}
            className="group flex items-center gap-2 text-slate-400 hover:text-white transition-all duration-300 mb-4 hover:gap-3"
          >
            <ArrowLeft size={20} className="transition-transform group-hover:-translate-x-1" />
            <span>Back</span>
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent">
              Contract Comparison
            </h1>
            <Sparkles className="w-6 h-6 text-purple-400 animate-pulse" />
          </div>
          <p className="text-slate-400">Compare up to 4 contracts side-by-side with semantic analysis</p>
        </div>
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity duration-300"></div>
          <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 shadow-lg shadow-purple-500/50 group-hover:scale-110 transition-transform duration-300">
            <GitCompare className="w-8 h-8 text-white group-hover:rotate-12 transition-transform duration-300" />
          </div>
        </div>
      </div>

      {/* Reference File Upload */}
      <div className={`bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-all duration-500 transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'} hover:shadow-xl hover:shadow-blue-500/10`} style={{ transitionDelay: '100ms' }}>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-yellow-400 animate-pulse" />
          Select Reference File
        </h2>
        <p className="text-sm text-slate-400 mb-4">
          Upload the baseline contract that others will be compared against
        </p>

        <div className="space-y-4">
          <label className="block group">
            <div className="relative flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-slate-700 rounded-lg hover:border-blue-500 transition-all duration-300 cursor-pointer bg-slate-800/50 group-hover:bg-slate-800/70 group-hover:scale-[1.02]">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/5 to-purple-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg"></div>
              <div className="text-center relative z-10">
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2 group-hover:text-blue-400 group-hover:scale-110 transition-all duration-300" />
                <p className="text-sm text-slate-300 mb-1">
                  {referenceFile ? referenceFile.name : 'Click to upload reference contract'}
                </p>
                <p className="text-xs text-slate-500">PDF or DOCX</p>
              </div>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleReferenceFileChange}
                className="hidden"
              />
            </div>
          </label>

          {referenceFile && (
            <div className="flex items-center gap-2 p-3 bg-blue-900/20 border border-blue-800 rounded-lg animate-slideIn hover:bg-blue-900/30 transition-all duration-300 hover:scale-[1.02]">
              <FileText className="w-5 h-5 text-blue-400 flex-shrink-0 animate-bounce" />
              <div className="flex-1">
                <p className="text-sm text-white font-semibold">{referenceFile.name}</p>
                <p className="text-xs text-slate-400">{(referenceFile.size / 1024).toFixed(2)} KB</p>
              </div>
              <span className="text-yellow-400 text-lg animate-pulse">⭐</span>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Files Upload */}
      <div className={`bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-all duration-500 transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'} hover:shadow-xl hover:shadow-green-500/10`} style={{ transitionDelay: '200ms' }}>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-400 animate-pulse" />
          Select Contracts for Comparing
        </h2>
        <p className="text-sm text-slate-400 mb-4">
          Upload 1-3 contracts to compare against the reference (Max: 3 files)
        </p>

        <div className="space-y-4">
          <label className="block group">
            <div className="relative flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-slate-700 rounded-lg hover:border-green-500 transition-all duration-300 cursor-pointer bg-slate-800/50 group-hover:bg-slate-800/70 group-hover:scale-[1.02]">
              <div className="absolute inset-0 bg-gradient-to-r from-green-500/0 via-green-500/5 to-emerald-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg"></div>
              <div className="text-center relative z-10">
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2 group-hover:text-green-400 group-hover:scale-110 transition-all duration-300" />
                <p className="text-sm text-slate-300 mb-1">
                  Click to upload contracts for comparison
                </p>
                <p className="text-xs text-slate-500">PDF or DOCX (Max 3 files)</p>
              </div>
              <input
                type="file"
                accept=".pdf,.docx"
                multiple
                onChange={handleCompareFilesChange}
                className="hidden"
              />
            </div>
          </label>

          {compareFiles.length > 0 && (
            <div className="space-y-2 animate-slideIn">
              <p className="text-sm text-slate-300 font-semibold flex items-center gap-2">
                Selected: {compareFiles.length} file(s)
                <span className="inline-flex items-center justify-center w-6 h-6 text-xs font-bold text-white bg-green-500 rounded-full animate-pulse">
                  {compareFiles.length}
                </span>
              </p>
              {compareFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-3 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700/50 hover:border-green-500/50 transition-all duration-300 hover:scale-[1.02] animate-slideIn group"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <FileText className="w-5 h-5 text-green-400 flex-shrink-0 group-hover:scale-110 transition-transform duration-300" />
                  <div className="flex-1">
                    <p className="text-sm text-white font-semibold">{file.name}</p>
                    <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(2)} KB</p>
                  </div>
                  <button
                    onClick={() => removeCompareFile(index)}
                    className="p-1 hover:bg-red-500/20 rounded transition-all duration-300 group/btn"
                  >
                    <X className="w-4 h-4 text-slate-400 group-hover/btn:text-red-400 group-hover/btn:rotate-90 transition-all duration-300" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Keyword Search */}
      <div className={`bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-all duration-500 transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'} hover:shadow-xl hover:shadow-purple-500/10`} style={{ transitionDelay: '300ms' }}>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Search className="w-5 h-5 text-purple-400 animate-pulse" />
          Keyword Search
        </h2>
        <div className="relative group">
          <input
            type="text"
            placeholder="Enter keywords separated by commas (e.g., liability, indemnity, termination)"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all duration-300 hover:border-slate-600"
          />
          {keywords && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-purple-400 bg-purple-500/10 px-2 py-1 rounded animate-fadeIn">
              {keywords.split(',').filter(k => k.trim()).length} keyword(s)
            </div>
          )}
        </div>
      </div>

      {/* Compare Button */}
      <div className={`transition-all duration-500 transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} style={{ transitionDelay: '400ms' }}>
        <button
          onClick={handleCompare}
          disabled={loading || !referenceFile || compareFiles.length === 0}
          className="group relative w-full flex items-center justify-center gap-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-4 px-6 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/30 hover:shadow-2xl hover:shadow-blue-500/50 hover:scale-[1.02] overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <div className="relative z-10 flex items-center gap-3">
            {loading ? (
              <>
                <div className="relative">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  <div className="absolute inset-0 animate-ping rounded-full h-5 w-5 border border-white opacity-30"></div>
                </div>
                <span className="animate-pulse">Analyzing & Comparing Contracts...</span>
              </>
            ) : (
              <>
                <GitCompare className="w-5 h-5 group-hover:rotate-12 transition-transform duration-300" />
                <span>Compare Contracts</span>
                <Sparkles className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </>
            )}
          </div>
        </button>
      </div>

      {/* Comparison Results */}
      {comparisonResults && (
        <div className="space-y-6 animate-fadeIn">
          {/* Risk Comparison Summary */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/10 animate-slideIn">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <AlertCircle className="w-6 h-6 text-purple-400 animate-pulse" />
              Risk Analysis Comparison
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {comparisonResults.risk_comparison?.map((risk, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border ${getRiskBgColor(risk.risk_level)} hover:scale-105 transition-all duration-300 hover:shadow-lg animate-slideIn group cursor-pointer`}
                  style={{ animationDelay: `${idx * 100}ms` }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-white font-semibold text-sm line-clamp-1 group-hover:text-purple-300 transition-colors duration-300">
                      {risk.contract_name || `Contract ${idx + 1}`}
                    </h3>
                    {risk.is_reference && (
                      <span className="text-yellow-400 animate-pulse">⭐</span>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between group/item">
                      <span className="text-slate-300 text-xs">Risk Level:</span>
                      <span className={`font-bold text-sm ${getRiskColor(risk.risk_level)} group-hover/item:scale-110 transition-transform duration-300`}>
                        {risk.risk_level}
                      </span>
                    </div>
                    <div className="flex items-center justify-between group/item">
                      <span className="text-slate-300 text-xs">Risk Score:</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-400 transition-all duration-1000 ease-out"
                            style={{ width: `${risk.risk_score}%` }}
                          ></div>
                        </div>
                        <span className="text-white font-bold group-hover/item:scale-110 transition-transform duration-300">{risk.risk_score}/100</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between group/item">
                      <span className="text-slate-300 text-xs">Deviations:</span>
                      <span className="text-orange-400 font-semibold group-hover/item:scale-110 transition-transform duration-300">{risk.total_deviations}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Clause Comparison */}
          {comparisonResults.clause_comparison && (
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-all duration-300 hover:shadow-xl hover:shadow-green-500/10 animate-slideIn" style={{ animationDelay: '100ms' }}>
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <CheckCircle className="w-6 h-6 text-green-400 animate-pulse" />
                Clause Alignment & Similarity
              </h2>

              <div className="space-y-4">
                {comparisonResults.clause_comparison.aligned_clauses?.map((alignment, idx) => (
                  <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:bg-slate-800/70 hover:border-green-500/50 transition-all duration-300 hover:scale-[1.01] animate-slideIn group/clause" style={{ animationDelay: `${idx * 50}ms` }}>
                    <div className="mb-3 flex items-center justify-between">
                      <h3 className="text-white font-semibold group-hover/clause:text-green-300 transition-colors duration-300">
                        {alignment.clause_type || `Clause ${idx + 1}`}
                      </h3>
                      <div className="flex items-center gap-2">
                        {alignment.similarity_score >= 0.8 ? (
                          <CheckCircle className="w-4 h-4 text-green-400 animate-pulse" />
                        ) : alignment.similarity_score >= 0.5 ? (
                          <Minus className="w-4 h-4 text-yellow-400 animate-pulse" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400 animate-pulse" />
                        )}
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all duration-1000 ease-out ${
                                alignment.similarity_score >= 0.8
                                  ? 'bg-gradient-to-r from-green-400 to-emerald-400'
                                  : alignment.similarity_score >= 0.5
                                  ? 'bg-gradient-to-r from-yellow-400 to-orange-400'
                                  : 'bg-gradient-to-r from-red-400 to-rose-400'
                              }`}
                              style={{ width: `${alignment.similarity_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-slate-300 font-semibold">
                            {(alignment.similarity_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {alignment.clauses?.map((clause, cIdx) => (
                        <div key={cIdx} className="bg-slate-900 rounded p-3 border border-slate-700 hover:bg-slate-800 hover:border-blue-500/50 transition-all duration-300 hover:scale-[1.02] group/item">
                          <div className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                            <span className="group-hover/item:text-blue-400 transition-colors duration-300">
                              {clause.contract_name || `Contract ${cIdx + 1}`}
                            </span>
                            {clause.is_reference && <span className="animate-pulse">⭐</span>}
                          </div>
                          <p className="text-sm text-slate-200 line-clamp-3 group-hover/item:text-white transition-colors duration-300">
                            {clause.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing Clauses */}
          {comparisonResults.missing_clauses && comparisonResults.missing_clauses.length > 0 && (
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-all duration-300 hover:shadow-xl hover:shadow-orange-500/10 animate-slideIn" style={{ animationDelay: '200ms' }}>
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-orange-400 animate-pulse" />
                Missing or Unique Clauses
              </h2>

              <div className="space-y-3">
                {comparisonResults.missing_clauses.map((missing, idx) => (
                  <div key={idx} className="bg-orange-900/20 border border-orange-800 rounded-lg p-4 hover:bg-orange-900/30 hover:border-orange-700 transition-all duration-300 hover:scale-[1.01] animate-slideIn" style={{ animationDelay: `${idx * 50}ms` }}>
                    <div className="flex items-start gap-3">
                      <XCircle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h3 className="text-white font-semibold mb-1">
                          {missing.clause_type}
                        </h3>
                        <p className="text-sm text-slate-300 mb-2">
                          Present in: {missing.present_in_contract} |
                          Missing in: {missing.missing_in_contracts?.join(', ')}
                        </p>
                        <p className="text-sm text-slate-400 italic">
                          {missing.text?.substring(0, 200)}...
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Keyword Matches */}
          {comparisonResults.keyword_matches && Object.keys(comparisonResults.keyword_matches).length > 0 && (
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 animate-slideIn" style={{ animationDelay: '300ms' }}>
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <Search className="w-6 h-6 text-blue-400 animate-pulse" />
                Keyword Analysis
              </h2>

              <div className="space-y-4">
                {Object.entries(comparisonResults.keyword_matches).map(([keyword, matches], kwIdx) => (
                  <div key={keyword} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:bg-slate-800/70 hover:border-blue-500/50 transition-all duration-300 animate-slideIn" style={{ animationDelay: `${kwIdx * 50}ms` }}>
                    <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                      Keyword: <span className="text-blue-400 px-2 py-1 bg-blue-500/10 rounded animate-pulse">{keyword}</span>
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {matches.map((match, idx) => (
                        <button
                          key={idx}
                          onClick={() => setKeywordModal({
                            keyword: keyword,
                            contractName: match.contract_name || `Contract ${idx + 1}`,
                            isReference: match.is_reference,
                            occurrences: match.occurrences || []
                          })}
                          className="group/kw bg-slate-900 rounded p-3 border border-slate-700 hover:border-blue-500 hover:bg-slate-800 transition-all duration-300 cursor-pointer text-left hover:scale-[1.02] hover:shadow-lg hover:shadow-blue-500/20"
                        >
                          <div className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                            <span className="group-hover/kw:text-blue-400 transition-colors duration-300">
                              {match.contract_name || `Contract ${idx + 1}`}
                            </span>
                            {match.is_reference && <span className="animate-pulse">⭐</span>}
                          </div>
                          <p className="text-sm text-slate-300 flex items-center justify-between group-hover/kw:text-white transition-colors duration-300">
                            <span>
                              Found: <span className="text-green-400 font-semibold group-hover/kw:scale-110 inline-block transition-transform duration-300">{match.count}</span> times
                            </span>
                            <span className="text-xs text-blue-400 opacity-0 group-hover/kw:opacity-100 transition-all duration-300 transform translate-x-2 group-hover/kw:translate-x-0">→ View</span>
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Keyword Context Modal */}
      {keywordModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-slate-900 rounded-2xl border border-slate-700 max-w-4xl w-full max-h-[80vh] overflow-hidden shadow-2xl animate-slideUp hover:shadow-blue-500/20 transition-shadow duration-300">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
                  Keyword: <span className="text-blue-400 px-3 py-1 bg-blue-500/10 rounded-lg animate-pulse">{keywordModal.keyword}</span>
                </h2>
                <p className="text-sm text-slate-400 flex items-center gap-1">
                  Contract: <span className="text-white font-semibold">{keywordModal.contractName}</span> {keywordModal.isReference && <span className="animate-pulse">⭐</span>}
                </p>
              </div>
              <button
                onClick={() => setKeywordModal(null)}
                className="group p-2 hover:bg-slate-800 rounded-lg transition-all duration-300 hover:rotate-90"
              >
                <X className="w-6 h-6 text-slate-400 group-hover:text-red-400 transition-colors duration-300" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)] custom-scrollbar">
              {keywordModal.occurrences && keywordModal.occurrences.length > 0 ? (
                <div className="space-y-4">
                  {keywordModal.occurrences.map((occurrence, idx) => (
                    <div key={idx} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 hover:bg-slate-800 hover:border-blue-500/50 transition-all duration-300 hover:scale-[1.01] animate-slideIn" style={{ animationDelay: `${idx * 50}ms` }}>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs font-semibold text-slate-400 bg-slate-700 px-3 py-1 rounded-full hover:bg-blue-500/20 hover:text-blue-400 transition-all duration-300">
                          Occurrence #{idx + 1}
                        </span>
                      </div>
                      <p className="text-slate-200 leading-relaxed">
                        {occurrence.context.split(new RegExp(`(${keywordModal.keyword})`, 'gi')).map((part, i) =>
                          part.toLowerCase() === keywordModal.keyword.toLowerCase() ? (
                            <mark key={i} className="bg-yellow-400 text-black font-semibold px-1.5 py-0.5 rounded animate-pulse">
                              {part}
                            </mark>
                          ) : (
                            <span key={i}>{part}</span>
                          )
                        )}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 animate-fadeIn">
                  <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3 animate-pulse" />
                  <p className="text-slate-400">No occurrences found</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractCompare;
