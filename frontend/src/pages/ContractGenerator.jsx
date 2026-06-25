import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowLeft,
  Download,
  Database,
  Trash2,
  Plus
} from 'lucide-react';
import api from '../utils/api';
import { config } from '../config/api.config';
import useThemeStore from '../store/themeStore';

export default function ContractGenerator() {
  const navigate = useNavigate();
  const { theme } = useThemeStore();
  const [mode, setMode] = useState('upload'); // 'upload' or 'generate'

  // Upload state
  const [files, setFiles] = useState([]);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [indexedInfo, setIndexedInfo] = useState(null);

  // Generation state
  const [contractTitle, setContractTitle] = useState('');
  const [contractPrompt, setContractPrompt] = useState('');
  const [generatedContract, setGeneratedContract] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState('');

  // Stats state
  const [stats, setStats] = useState(null);

  // Force dark theme to match the rest of the UI
  const isDark = true; // Always use dark theme

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get(config.RAG_STATS_URL.replace(config.API_BASE_URL, ''));
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 5) {
      alert('Maximum 5 files allowed');
      return;
    }
    setFiles(selectedFiles);
    setUploadSuccess(false);
  };

  const handleUploadAndIndex = async () => {
    if (files.length === 0) {
      alert('Please select at least one contract file');
      return;
    }

    try {
      setUploadLoading(true);
      setUploadStatus('Uploading and indexing contract samples...');

      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await api.post(
        config.RAG_UPLOAD_FILES_URL.replace(config.API_BASE_URL, ''),
        formData
      );

      setUploadStatus('✓ Sample contracts indexed successfully!');
      setUploadSuccess(true);
      setIndexedInfo(response.data);
      setFiles([]);

      // Refresh stats
      await fetchStats();

      // Auto-switch to generate mode after successful upload
      setTimeout(() => {
        setMode('generate');
      }, 1500);

    } catch (error) {
      setUploadStatus('Error: ' + (error.response?.data?.error || error.message));
      setUploadSuccess(false);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleGenerateContract = async () => {
    if (!contractPrompt.trim()) {
      alert('Please describe the contract you want to generate');
      return;
    }

    try {
      setGenerating(true);
      setGenerationStatus('Generating contract from sample templates... This may take a minute.');

      const response = await api.post(
        config.RAG_GENERATE_FROM_SAMPLES_URL.replace(config.API_BASE_URL, ''),
        {
          prompt: contractPrompt,
          title: contractTitle || 'Generated Contract'
        }
      );

      setGeneratedContract(response.data.contract);

      const successMsg = `✓ Contract generated successfully!
📊 Model: ${response.data.model_used || 'Unknown'}
📚 Context chunks used: ${response.data.context_chunks_used || 0}
${response.data.has_context ? '✓ Generated with sample contract context' : '⚠️ No sample context found - consider uploading samples first'}`;

      setGenerationStatus(successMsg);

    } catch (error) {
      setGenerationStatus('Error: ' + (error.response?.data?.error || error.message));
      setGeneratedContract('');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!generatedContract) {
      alert('No contract to download');
      return;
    }

    try {
      const response = await fetch(config.GENERATE_PDF_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          contract_text: generatedContract
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${contractTitle || 'Contract'}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('Failed to generate PDF');
      }
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error downloading PDF: ' + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 rounded-lg transition-colors hover:bg-slate-700 text-slate-300"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-white">
                AI Contract Generator
              </h1>
              <p className="mt-1 text-slate-400">
                Upload sample contracts and generate new ones with AI
              </p>
            </div>
          </div>

          {stats && (
            <div className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700">
              <div className="flex items-center space-x-2">
                <Database className="w-4 h-4 text-blue-400" />
                <span className="text-slate-300">
                  {stats.total_vectors || 0} indexed chunks
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Mode Switcher */}
        <div className="mb-6 flex space-x-2">
          <button
            onClick={() => setMode('upload')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              mode === 'upload'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/50'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Upload className="w-5 h-5" />
              <span>Upload Samples</span>
            </div>
          </button>

          <button
            onClick={() => setMode('generate')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              mode === 'generate'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/50'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5" />
              <span>Generate Contract</span>
            </div>
          </button>
        </div>

        {/* Upload Mode */}
        {mode === 'upload' && (
          <div className="p-8 rounded-2xl shadow-2xl bg-slate-800 border border-slate-700">
            <h2 className="text-2xl font-semibold mb-6 text-white">
              Upload Sample Contracts
            </h2>

            <div className="space-y-6">
              {/* File Input */}
              <div>
                <label className="block text-sm font-medium mb-2 text-slate-300">
                  Select Contract Files (PDF, DOCX, TXT)
                </label>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileChange}
                  className="w-full px-4 py-3 rounded-lg border bg-slate-900 border-slate-600 text-white focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-2 text-sm text-slate-400">
                  Maximum 5 files. Supported formats: PDF, DOCX, TXT
                </p>
              </div>

              {/* Selected Files */}
              {files.length > 0 && (
                <div className={`p-4 rounded-lg bg-slate-900`}>
                  <h3 className={`text-sm font-medium mb-3 text-slate-300`}>
                    Selected Files ({files.length}/5)
                  </h3>
                  <ul className="space-y-2">
                    {files.map((file, index) => (
                      <li
                        key={index}
                        className={`flex items-center justify-between p-2 rounded bg-slate-800`}
                      >
                        <div className="flex items-center space-x-2">
                          <FileText className="w-4 h-4 text-blue-500" />
                          <span className="text-slate-300">
                            {file.name}
                          </span>
                          <span className={`text-xs text-slate-500`}>
                            ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Upload Button */}
              <button
                onClick={handleUploadAndIndex}
                disabled={uploadLoading || files.length === 0}
                className={`w-full py-4 rounded-lg font-medium transition-all ${
                  uploadLoading || files.length === 0
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 shadow-lg shadow-blue-500/50'
                }`}
              >
                {uploadLoading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Indexing Contracts...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-2">
                    <Upload className="w-5 h-5" />
                    <span>Upload & Index Contracts</span>
                  </div>
                )}
              </button>

              {/* Status Message */}
              {uploadStatus && (
                <div
                  className={`p-4 rounded-lg flex items-start space-x-3 ${
                    uploadSuccess
                      ? 'bg-green-900/30 border border-green-700/50'
                      : 'bg-red-900/30 border border-red-700/50'
                  }`}
                >
                  {uploadSuccess ? (
                    <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p
                      className={`whitespace-pre-wrap ${
                        uploadSuccess ? 'text-green-300' : 'text-red-300'
                      }`}
                    >
                      {uploadStatus}
                    </p>
                    {indexedInfo && (
                      <div className={`mt-2 text-sm text-slate-400`}>
                        <p>Files indexed: {indexedInfo.files_indexed}</p>
                        <p>Chunks created: {indexedInfo.chunks_created}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Generate Mode */}
        {mode === 'generate' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Panel */}
            <div className={`p-8 rounded-2xl shadow-2xl bg-slate-800 border border-slate-700`}>
              <h2 className={`text-2xl font-semibold mb-6 text-white`}>
                Generate New Contract
              </h2>

              <div className="space-y-6">
                {/* Contract Title */}
                <div>
                  <label className="block text-sm font-medium mb-2 text-slate-300">
                    Contract Title (Optional)
                  </label>
                  <input
                    type="text"
                    value={contractTitle}
                    onChange={(e) => setContractTitle(e.target.value)}
                    placeholder="e.g., Software Consulting Agreement"
                    className="w-full px-4 py-3 rounded-lg border bg-slate-900 border-slate-600 text-white placeholder-slate-500 focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Contract Description */}
                <div>
                  <label className="block text-sm font-medium mb-2 text-slate-300">
                    Describe the Contract <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={contractPrompt}
                    onChange={(e) => setContractPrompt(e.target.value)}
                    placeholder="Describe what kind of contract you need. For example:&#10;&#10;- Generate a consulting agreement for software development services&#10;- Create a non-disclosure agreement for technology partners&#10;- Draft a service agreement for marketing services"
                    rows={8}
                    className="w-full px-4 py-3 rounded-lg border bg-slate-900 border-slate-600 text-white placeholder-slate-500 focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Generate Button */}
                <button
                  onClick={handleGenerateContract}
                  disabled={generating || !contractPrompt.trim()}
                  className={`w-full py-4 rounded-lg font-medium transition-all ${
                    generating || !contractPrompt.trim()
                      ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-purple-600 to-purple-700 text-white hover:from-purple-700 hover:to-purple-800 shadow-lg shadow-purple-500/50'
                  }`}
                >
                  {generating ? (
                    <div className="flex items-center justify-center space-x-2">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Generating Contract...</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center space-x-2">
                      <Sparkles className="w-5 h-5" />
                      <span>Generate with AI</span>
                    </div>
                  )}
                </button>

                {/* Status Message */}
                {generationStatus && (
                  <div
                    className={`p-4 rounded-lg flex items-start space-x-3 ${
                      generatedContract
                        ? 'bg-green-900/30 border border-green-700/50'
                        : 'bg-blue-900/30 border border-blue-700/50'
                    }`}
                  >
                    {generatedContract ? (
                      <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-blue-400 mt-0.5" />
                    )}
                    <p
                      className={`whitespace-pre-wrap text-sm ${
                        generatedContract ? 'text-green-300' : 'text-blue-300'
                      }`}
                    >
                      {generationStatus}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Output Panel */}
            <div className={`p-8 rounded-2xl shadow-2xl bg-slate-800 border border-slate-700`}>
              <div className="flex items-center justify-between mb-6">
                <h2 className={`text-2xl font-semibold text-white`}>
                  Generated Contract
                </h2>
                {generatedContract && (
                  <button
                    onClick={handleDownloadPDF}
                    className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-green-600 to-green-700 text-white hover:from-green-700 hover:to-green-800 transition-all"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download PDF</span>
                  </button>
                )}
              </div>

              <textarea
                value={generatedContract}
                onChange={(e) => setGeneratedContract(e.target.value)}
                placeholder="Your generated contract will appear here. You can edit it before downloading."
                rows={20}
                className="w-full px-4 py-3 rounded-lg border font-mono text-sm bg-slate-900 border-slate-600 text-slate-200 placeholder-slate-500 focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
