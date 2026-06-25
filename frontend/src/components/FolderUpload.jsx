import React, { useState, useRef } from 'react';
import { Upload, FolderOpen, CheckCircle, XCircle, Loader, AlertCircle, FileText, ChevronRight, Files } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import UpgradePlanModal from './UpgradePlanModal';
import useThemeStore from '../store/themeStore';

export default function FolderUpload({ onUploadComplete }) {
  const { theme } = useThemeStore();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [limitData, setLimitData] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const MAX_FILE_SIZE = 25 * 1024 * 1024;
  const ALLOWED_TYPES = ['.pdf', '.docx', '.png', '.jpg', '.jpeg'];

  const validateFiles = (files) => {
    const errors = [];
    const validFiles = [];

    Array.from(files).forEach((file) => {
      const ext = '.' + file.name.split('.').pop().toLowerCase();

      if (!ALLOWED_TYPES.includes(ext)) {
        errors.push(`${file.name}: Unsupported file type (${ext})`);
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: File exceeds 25MB limit (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
        return;
      }

      validFiles.push(file);
    });

    return { validFiles, errors };
  };

  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;

    const { validFiles, errors } = validateFiles(files);

    if (validFiles.length === 0) {
      alert('No valid files to upload\n\n' + errors.join('\n'));
      return;
    }

    if (errors.length > 0) {
      const proceed = window.confirm(
        `${errors.length} file(s) will be skipped:\n\n${errors.slice(0, 5).join('\n')}${errors.length > 5 ? '\n...' : ''}\n\nContinue with ${validFiles.length} valid file(s)?`
      );
      if (!proceed) return;
    }

    setIsUploading(true);
    setResults(null);
    setUploadProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => Math.min(prev + Math.random() * 15, 90));
    }, 500);

    try {
      const formData = new FormData();
      validFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await api.post('/contracts/upload-folder', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      setResults(response.data);

      if (onUploadComplete) {
        onUploadComplete(response.data);
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Folder upload error:', error);

      if (error.response?.status === 402 &&
          (error.response?.data?.error === 'CONTRACT_LIMIT_REACHED' ||
           error.response?.data?.error === 'CONTRACT_LIMIT_EXCEEDED')) {
        setLimitData(error.response.data);
        setShowUpgradeModal(true);
      } else {
        alert(`Upload failed: ${error.response?.data?.message || error.message}`);
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleUpload(files);
    }
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
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleUpload(files);
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
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300 ${
          isDragging
            ? 'border-blue-500 bg-blue-500/10 scale-[1.02]'
            : 'border-slate-700 hover:border-blue-500/50 hover:bg-slate-800/30'
        } ${isUploading ? 'pointer-events-none' : 'cursor-pointer'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          webkitdirectory="true"
          className="hidden"
          onChange={handleFileSelect}
          disabled={isUploading}
        />

        {isUploading ? (
          /* Uploading State */
          <div className="space-y-6">
            <div className="relative inline-block">
              <div className="absolute inset-0 bg-blue-500 rounded-2xl blur-xl opacity-30 animate-pulse" />
              <div className="relative p-5 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700">
                <Loader className="w-12 h-12 text-blue-400 animate-spin" />
              </div>
            </div>
            <div>
              <p className="text-lg font-semibold text-white mb-2">Processing files...</p>
              <p className="text-sm text-slate-400 mb-4">
                This may take a few minutes for large batches
              </p>
              {/* Progress Bar */}
              <div className="max-w-xs mx-auto">
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-2">{Math.round(uploadProgress)}% complete</p>
              </div>
            </div>
          </div>
        ) : (
          /* Empty State */
          <div className="space-y-4">
            <div className="relative inline-block">
              <div className="absolute inset-0 bg-purple-500 rounded-2xl blur-xl opacity-20 animate-pulse" />
              <div className="relative p-5 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl border border-slate-700">
                <FolderOpen className="w-12 h-12 text-purple-400" />
              </div>
            </div>
            <div>
              <p className="text-lg font-semibold text-white mb-1">
                {isDragging ? 'Drop your folder here' : 'Upload Multiple Contracts'}
              </p>
              <p className="text-sm text-slate-400 mb-4">
                Drag and drop a folder here, or <span className="text-blue-400">browse</span> to select
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white rounded-xl font-medium text-sm transition-all shadow-lg shadow-purple-500/20"
              >
                <Files className="w-4 h-4" />
                Select Folder
              </button>
            </div>
            <div className="space-y-1 pt-4">
              <div className="flex flex-wrap justify-center gap-2">
                {['PDF', 'DOCX', 'PNG', 'JPG', 'JPEG'].map((type) => (
                  <span key={type} className="px-2.5 py-1 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-400">
                    {type}
                  </span>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-2">Max 25MB per file</p>
              <p className="text-xs text-amber-500/80">
                Note: Folder selection works best in Chrome and Edge
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-4 animate-fade-in">
          {/* Summary Card */}
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Upload Results</h3>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-semibold">{results.success_count} succeeded</span>
                </div>
                {results.failure_count > 0 && (
                  <div className="flex items-center gap-2 text-red-400">
                    <XCircle className="w-5 h-5" />
                    <span className="font-semibold">{results.failure_count} failed</span>
                  </div>
                )}
              </div>
            </div>

            {/* Progress Overview */}
            <div className="bg-slate-900/50 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Total Processed</span>
                <span className="text-white font-semibold">{results.total} files</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full mt-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-full"
                  style={{ width: `${(results.success_count / results.total) * 100}%` }}
                />
              </div>
            </div>

            {/* File List */}
            <div className="space-y-2 max-h-64 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-700">
              {results.results?.map((result, index) => (
                <div
                  key={index}
                  className={`flex items-center justify-between p-3 rounded-xl transition-all ${
                    result.success
                      ? 'bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/15'
                      : 'bg-red-500/10 border border-red-500/20'
                  }`}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="text-xl">{getFileIcon(result.filename)}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {result.filename}
                      </p>
                      {result.success && result.contractType && (
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                            {result.contractType}
                          </span>
                          <span className="text-xs text-slate-500">{result.status}</span>
                        </div>
                      )}
                      {!result.success && result.error && (
                        <p className="text-xs text-red-400 mt-0.5 truncate">{result.error}</p>
                      )}
                    </div>
                  </div>
                  {result.success ? (
                    <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          {results.success_count > 0 && (
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20"
              >
                View Contracts
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setResults(null);
                  setUploadProgress(0);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                }}
                className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-medium transition-all"
              >
                <FolderOpen className="w-4 h-4" />
                Upload Another
              </button>
            </div>
          )}
        </div>
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
        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: transparent;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: rgba(71, 85, 105, 0.5);
          border-radius: 3px;
        }
      `}</style>
    </div>
  );
}
