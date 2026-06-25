import { useState, useRef } from 'react';
import { Upload, AlertCircle, CheckCircle, Loader, ArrowLeft, FileText, FolderOpen, Sparkles, File, X, Clock, Zap, Shield, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import useThemeStore from '../store/themeStore';
import FolderUpload from '../components/FolderUpload';
import UpgradePlanModal from '../components/UpgradePlanModal';

export default function UploadContract() {
  const { theme } = useThemeStore();
  const [activeTab, setActiveTab] = useState('single');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [limitData, setLimitData] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 25 * 1024 * 1024;
  const ALLOWED_TYPES = ['.docx', '.pdf', '.png', '.jpg', '.jpeg'];

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setError('');
    setUploadResult(null);

    const fileExt = '.' + selectedFile.name.split('.').pop().toLowerCase();
    if (!ALLOWED_TYPES.includes(fileExt)) {
      setError('Unsupported file type. Allowed: DOCX, PDF, PNG, JPG, JPEG');
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File exceeds 25MB limit (${(selectedFile.size / 1024 / 1024).toFixed(2)}MB)`);
      return;
    }

    setFile(selectedFile);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      const fakeEvent = { target: { files: [droppedFile] } };
      handleFileSelect(fakeEvent);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/contracts/upload', formData);

      console.log('📄 Upload response:', response.data);
      setUploadResult(response.data);
      setFile(null);

      // Success - display extracted text and action buttons
      if (response.data?.contractId) {
        console.log('✅ Contract uploaded, ID:', response.data.contractId);
      } else {
        console.error('❌ No contractId in response:', response.data);
        setError('Upload succeeded but no contract ID was returned. Please refresh and try again.');
      }
    } catch (err) {
      if (err.response?.status === 402 && err.response?.data?.error === 'CONTRACT_LIMIT_REACHED') {
        setLimitData(err.response.data);
        setShowUpgradeModal(true);
        setFile(null);
      } else {
        const errorDetail = err.response?.data?.error || err.response?.data?.message || err.message || 'Upload failed';
        const suggestion = err.response?.data?.suggestion || '';
        setError(`Error: ${errorDetail}${suggestion ? '\n' + suggestion : ''}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (filename) => {
    const ext = filename?.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return '📄';
    if (ext === 'docx') return '📝';
    if (['png', 'jpg', 'jpeg'].includes(ext)) return '🖼️';
    return '📁';
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition-all group"
      >
        <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
        <span className="text-sm font-medium">Back</span>
      </button>

      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-emerald-600/10 border border-slate-800 rounded-2xl p-6">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg shadow-blue-500/20">
              <Upload className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Upload Contract</h1>
              <p className="text-slate-400 text-sm">AI-powered processing and analysis</p>
            </div>
          </div>

          {/* Features */}
          <div className="flex flex-wrap gap-4 mt-4">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span>Instant Analysis</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Risk Detection</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Smart Extraction</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-2 p-1 bg-slate-800/50 rounded-xl border border-slate-700/50">
        <button
          onClick={() => setActiveTab('single')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium text-sm transition-all duration-200 ${
            activeTab === 'single'
              ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Single File</span>
        </button>
        <button
          onClick={() => setActiveTab('folder')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium text-sm transition-all duration-200 ${
            activeTab === 'folder'
              ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <FolderOpen className="w-4 h-4" />
          <span>Folder Upload</span>
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'single' ? (
        <div className="space-y-4">
          {/* Upload Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !file && fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
              isDragging
                ? 'border-blue-500 bg-blue-500/10 scale-[1.02]'
                : file
                ? 'border-emerald-500/50 bg-emerald-500/5'
                : 'border-slate-700 hover:border-blue-500/50 hover:bg-slate-800/30'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              accept=".docx,.pdf,.png,.jpg,.jpeg"
              className="hidden"
            />

            {file ? (
              /* File Selected State */
              <div className="space-y-4">
                <div className="inline-flex p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/30">
                  <span className="text-4xl">{getFileIcon(file.name)}</span>
                </div>
                <div>
                  <p className="text-lg font-semibold text-white mb-1 truncate max-w-md mx-auto">{file.name}</p>
                  <p className="text-sm text-slate-400">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded-lg text-sm transition-all"
                >
                  <X className="w-4 h-4" />
                  Remove
                </button>
              </div>
            ) : (
              /* Empty State */
              <div className="space-y-4">
                <div className="relative inline-block">
                  <div className="absolute inset-0 bg-blue-500 rounded-2xl blur-xl opacity-20 animate-pulse" />
                  <div className="relative p-4 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700">
                    <Upload className="w-10 h-10 text-blue-400" />
                  </div>
                </div>
                <div>
                  <p className="text-lg font-semibold text-white mb-1">
                    {isDragging ? 'Drop your file here' : 'Drag & drop your contract'}
                  </p>
                  <p className="text-sm text-slate-400">
                    or <span className="text-blue-400 hover:underline">browse</span> to select
                  </p>
                </div>
                <div className="flex flex-wrap justify-center gap-2 mt-4">
                  {['PDF', 'DOCX', 'PNG', 'JPG'].map((type) => (
                    <span key={type} className="px-2.5 py-1 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-400">
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/30 rounded-xl p-4 animate-fade-in">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className={`w-full flex items-center justify-center gap-3 px-6 py-4 rounded-xl font-semibold text-base transition-all duration-200 ${
              file && !loading
                ? 'bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white shadow-lg shadow-blue-500/20 hover:shadow-xl hover:shadow-blue-500/30'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Upload & Analyze</span>
              </>
            )}
          </button>

          {/* Supported Formats */}
          <p className="text-center text-xs text-slate-500">
            Maximum file size: 25MB
          </p>

          {/* Success Results */}
          {uploadResult && (
            <div className="space-y-4 animate-fade-in">
              {/* Success Banner */}
              <div className="flex items-center gap-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <p className="font-semibold text-emerald-300">{uploadResult.message}</p>
                  <p className="text-sm text-emerald-400/70">{uploadResult.filename}</p>
                </div>
              </div>

              {/* Contract Info Card */}
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between pb-4 border-b border-slate-700/50">
                  <span className="text-slate-400">Contract Type</span>
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg font-semibold">
                    {uploadResult.contractType}
                  </span>
                </div>

                {/* Confidence Score */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Confidence Score</span>
                    <span className={`font-semibold ${
                      uploadResult.confidenceScore >= 75 ? 'text-emerald-400' :
                      uploadResult.confidenceScore >= 50 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {uploadResult.confidenceScore?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        uploadResult.confidenceScore >= 75 ? 'bg-emerald-500' :
                        uploadResult.confidenceScore >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${uploadResult.confidenceScore}%` }}
                    />
                  </div>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">File Type</p>
                    <p className="text-sm font-medium text-white">{uploadResult.type}</p>
                  </div>
                  {uploadResult.pages && (
                    <div className="bg-slate-900/50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 mb-1">Pages</p>
                      <p className="text-sm font-medium text-white">{uploadResult.pages}</p>
                    </div>
                  )}
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">OCR Used</p>
                    <p className="text-sm font-medium text-white">
                      {uploadResult.ocr_performed ? 'Yes' : 'No'}
                    </p>
                  </div>
                  {uploadResult.timings?.total && (
                    <div className="bg-slate-900/50 rounded-lg p-3">
                      <p className="text-xs text-slate-500 mb-1">Process Time</p>
                      <p className="text-sm font-medium text-white">{uploadResult.timings.total}s</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Extracted Text - Full View */}
              {(uploadResult.full_text || uploadResult.text_preview) && (
                <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-slate-300">
                      Extracted Text ({(uploadResult.full_text || uploadResult.text_preview || '').length.toLocaleString()} characters)
                    </p>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(uploadResult.full_text || uploadResult.text_preview || '');
                        alert('Full text copied to clipboard!');
                      }}
                      className="text-xs px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition"
                    >
                      Copy All
                    </button>
                  </div>
                  <div className="bg-slate-900/50 rounded-lg p-4 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700">
                    <p className="text-sm text-slate-400 whitespace-pre-wrap font-mono leading-relaxed">
                      {uploadResult.full_text || uploadResult.text_preview || ''}
                    </p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => navigate(`/contract/${uploadResult.contractId}/clauses`)}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white rounded-xl font-medium transition-all shadow-lg shadow-emerald-500/20"
                >
                  <Sparkles className="w-4 h-4" />
                  Extract Clauses
                </button>
                <button
                  onClick={() => navigate(`/contracts/${uploadResult.contractId}`)}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-all"
                >
                  View Contract
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Upload Another */}
              <button
                onClick={() => {
                  setUploadResult(null);
                  setFile(null);
                }}
                className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-700/50 text-slate-300 rounded-xl font-medium transition-all border border-slate-700/50"
              >
                Upload Another Contract
              </button>
            </div>
          )}
        </div>
      ) : (
        /* Folder Upload Tab */
        <FolderUpload
          onUploadComplete={(data) => {
            console.log('Folder upload complete:', data);
          }}
        />
      )}

      {/* Upgrade Plan Modal */}
      <UpgradePlanModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        limitData={limitData}
      />

      {/* Animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
