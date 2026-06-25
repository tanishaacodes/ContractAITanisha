import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, Sparkles, CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import api from "./utils/api";
import { config } from "./config/api.config";

export default function GenerateContract() {
  const navigate = useNavigate();
  const [files, setFiles] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [instr, setInstr] = useState("");
  const [genResult, setGenResult] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [extractedText, setExtractedText] = useState("");

  const handleFiles = (e) => {
    setFiles(e.target.files);
    setUploadSuccess(false);
  };

  const uploadAndIngest = async () => {
    if (!files) {
      setStatus("error");
      alert("Please choose a reference contract file first");
      return;
    }

    try {
      setLoading(true);
      const form = new FormData();
      form.append('file', files[0]); // Only use first file as reference

      setStatus('Uploading and extracting text from reference contract...');
      const response = await api.post('/rag/upload-extract', form);

      // Store extracted text
      setExtractedText(response.data.extracted_text || '');

      setStatus('Ready! Reference contract text extracted successfully.');
      setUploadSuccess(true);
    } catch (error) {
      setStatus('Error: ' + (error.response?.data?.error || error.message));
      setUploadSuccess(false);
      setExtractedText('');
    } finally {
      setLoading(false);
    }
  };

  const runGenerate = async () => {
    if (!extractedText) {
      alert("Please upload a reference contract first");
      return;
    }

    if (!instr.trim()) {
      alert("Please enter generation instructions (e.g., 'change date to 2025-01-01', 'change party name to Acme Corp')");
      return;
    }

    try {
      setLoading(true);
      setStatus('Modifying contract based on your instructions... This may take a minute.');
      const resp = await api.post('/rag/generate', {
        instruction: instr,
        extracted_text: extractedText
      });

      const modifiedContract = resp.data.modified_contract || resp.data.contract || resp.data;
      setGenResult(modifiedContract);

      // Show success message with model info
      let successMsg = 'Contract modified successfully!';
      if (resp.data.model_used) {
        successMsg += `\n📊 Model: ${resp.data.model_used}`;
      }
      if (resp.data.original_length && resp.data.modified_length) {
        successMsg += `\n📏 Original: ${resp.data.original_length} chars → Modified: ${resp.data.modified_length} chars`;
      }
      if (resp.data.length_ratio) {
        successMsg += ` (${resp.data.length_ratio})`;
      }

      // Display warnings if present (can be array or single string)
      if (resp.data.warnings && Array.isArray(resp.data.warnings)) {
        const warningText = resp.data.warnings.join('\n');
        setStatus(`${successMsg}\n\n${warningText}`);
      } else if (resp.data.warning) {
        setStatus(`${successMsg}\n\n⚠️ ${resp.data.warning}`);
      } else {
        setStatus(successMsg);
      }
    } catch (error) {
      setStatus('Error: ' + (error.response?.data?.error || error.message));
      setGenResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition"
      >
        <ArrowLeft size={20} />
        <span>Back</span>
      </button>

      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">AI Contract Generator</h1>
        <p className="text-slate-400">Use RAG and AI to analyze and generate contracts based on your existing documents</p>
      </div>

      {/* Status Bar */}
      {status && (
        <div className={`rounded-lg p-4 flex items-start gap-3 ${
          status.includes('Error')
            ? 'bg-red-900/20 border border-red-800'
            : uploadSuccess
            ? 'bg-green-900/20 border border-green-800'
            : 'bg-blue-900/20 border border-blue-800'
        }`}>
          {loading ? (
            <Loader2 className="h-5 w-5 text-blue-400 animate-spin flex-shrink-0 mt-0.5" />
          ) : status.includes('Error') ? (
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          ) : uploadSuccess ? (
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
          ) : (
            <CheckCircle className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
          )}
          <p className={`text-sm ${
            status.includes('Error')
              ? 'text-red-200'
              : uploadSuccess
              ? 'text-green-200'
              : 'text-blue-200'
          }`}>
            {status}
          </p>
        </div>
      )}

      {/* Upload Section */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-blue-600 to-blue-400">
            <Upload className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Upload Reference Contract</h2>
            <p className="text-slate-400 text-sm">Upload a single contract (PDF or DOCX) to use as base template</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Select Reference Contract
            </label>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFiles}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
            />
            {files && (
              <p className="text-sm text-slate-400 mt-2">
                📄 {files[0].name} selected
              </p>
            )}
            {extractedText && (
              <p className="text-sm text-green-400 mt-2">
                ✓ Text extracted ({extractedText.length} characters)
              </p>
            )}
          </div>

          <button
            onClick={uploadAndIngest}
            disabled={loading || !files}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="h-5 w-5" />
                Upload & Process
              </>
            )}
          </button>
        </div>
      </div>

      {/* Generate Contract Section */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-purple-600 to-purple-400">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Modify Contract</h2>
            <p className="text-slate-400 text-sm">Modify the extracted text from reference contract using AI-powered instructions</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Modification Instructions
            </label>
            <textarea
              rows={6}
              value={instr}
              onChange={(e) => setInstr(e.target.value)}
              placeholder={`Enter modifications to apply to the extracted contract text:\n\nExamples:\n• Change the date from 2024-01-01 to 2026-01-01\n• Replace party name "ABC Corp" with "XYZ Industries"\n• Change payment terms to Net 30 days\n• Update governing law to New York\n• Modify termination notice period to 60 days`}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={runGenerate}
            disabled={loading || !instr.trim()}
            className="w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Modifying...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                Modify Contract
              </>
            )}
          </button>

          {genResult && (
            <div className="mt-4 p-6 bg-slate-800 border border-slate-700 rounded-lg">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <FileText className="h-5 w-5 text-purple-400" />
                Modified Contract Text:
              </h3>
              <div className="text-slate-300 text-sm whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                {typeof genResult === 'string' ? genResult : JSON.stringify(genResult, null, 2)}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-700 flex justify-end">
                <button
                  onClick={async () => {
                    try {
                      const token = localStorage.getItem('token');
                      const response = await fetch(config.GENERATE_PDF_URL, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                          contract_text: genResult
                        })
                      });

                      if (!response.ok) {
                        throw new Error('Failed to generate PDF');
                      }

                      // Get PDF blob and download
                      const blob = await response.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = 'Modified_Contract.pdf';
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(url);
                    } catch (error) {
                      console.error('PDF download error:', error);
                      alert('Failed to download PDF: ' + error.message);
                    }
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
                >
                  Download as PDF
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-xl p-6">
        <p className="text-blue-100 text-sm">
          <strong>💡 How it works:</strong> Upload a reference contract (PDF/DOCX) to extract its text. Then provide modification instructions in plain English (e.g., "change date to 2026-01-01", "replace party name"). The AI will intelligently modify the extracted contract text based on your instructions using advanced language understanding.
        </p>
      </div>
    </div>
  );
}
