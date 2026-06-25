/**
 * Tender Upload — Premium Redesign
 */
import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import useAuthStore from '../../store/authStore';

const FEATURES = [
  {
    icon: (
      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
    title: 'Auto Extraction',
    desc: 'Extracts BOQ, commercials, deadlines and eligibility criteria from PDF',
    accent: 'blue',
  },
  {
    icon: (
      <svg className="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    title: 'Risk Detection',
    desc: 'Identifies unfavourable clauses, conflicts and liability traps automatically',
    accent: 'rose',
  },
  {
    icon: (
      <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
    title: 'Bid Intelligence',
    desc: 'Generates win probability, margin scenarios and full AI proposal',
    accent: 'emerald',
  },
];

const STEPS = ['Uploading PDF', 'Parsing document', 'Extracting BOQ & risks', 'Vectorising sections', 'Analysis complete'];

const TenderUpload = () => {
  const navigate  = useNavigate();
  const { token } = useAuthStore();
  const inputRef  = useRef(null);

  const [file, setFile]       = useState(null);
  const [title, setTitle]     = useState('');
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [step, setStep]       = useState(0);
  const [error, setError]     = useState(null);

  const pickFile = (f) => {
    if (!f) return;
    if (f.type !== 'application/pdf') { setError('Please select a valid PDF file.'); return; }
    setFile(f);
    setError(null);
    if (!title) setTitle(f.name.replace(/\.pdf$/i, ''));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) { setError('Please select a PDF file first.'); return; }
    setUploading(true);
    setError(null);
    setStep(0);

    // Fake step progression while real upload runs
    const ticker = setInterval(() => setStep(s => Math.min(s + 1, STEPS.length - 2)), 4000);

    try {
      const fd = new FormData();
      fd.append('pdf_file', file);
      fd.append('title', title || file.name);

      const res = await axios.post(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/tenders/tenders/upload_and_analyze/`,
        fd,
        { headers: { 'Content-Type': 'multipart/form-data', Authorization: `Bearer ${token}` } }
      );

      clearInterval(ticker);
      setStep(STEPS.length - 1);
      setTimeout(() => navigate(`/tenders/${res.data.id}`), 1200);
    } catch (err) {
      clearInterval(ticker);
      setError(err.response?.data?.error || err.message || 'Upload failed. Please try again.');
      setUploading(false);
      setStep(0);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">

      {/* ── Top bar ── */}
      <div className="border-b border-slate-800/60 bg-slate-900/80 backdrop-blur-sm px-6 py-4 flex items-center justify-between">
        <button
          onClick={() => navigate('/tenders')}
          className="flex items-center gap-1.5 text-slate-500 hover:text-blue-400 text-sm transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Tender Intelligence
        </button>
        <button
          onClick={() => navigate('/tenders/company-profile')}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-white border border-slate-700/50
                     bg-slate-800/50 hover:bg-slate-700/50 px-3 py-1.5 rounded-lg transition-all"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          Company Profile
        </button>
      </div>

      {/* ── Content ── */}
      <div className="flex-1 flex items-start justify-center px-6 py-10">
        <div className="w-full max-w-2xl">

          {/* Page title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600
                            shadow-xl shadow-blue-900/40 mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-1.5">Upload Tender Document</h1>
            <p className="text-slate-500 text-sm max-w-md mx-auto">
              Upload a government tender PDF for automated AI analysis — BOQ extraction, risk detection, eligibility check and bid intelligence
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 space-y-5">

            {/* Title input */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Tender Title
              </label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g. Construction of Bridge — NIT/CPWD/2026"
                disabled={uploading}
                className="w-full px-4 py-3 bg-slate-900/60 border border-slate-700/50 text-white placeholder-slate-600
                           rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 text-sm transition-all"
              />
            </div>

            {/* Drop zone */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                PDF Document
              </label>
              <div
                onDragOver={e => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => !uploading && inputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center p-10 rounded-2xl border-2 border-dashed cursor-pointer
                            transition-all duration-300 text-center
                            ${dragging
                              ? 'border-blue-500/70 bg-blue-500/8 shadow-lg shadow-blue-900/20'
                              : file
                                ? 'border-emerald-500/40 bg-emerald-500/5'
                                : 'border-slate-700/50 bg-slate-900/30 hover:border-slate-500/50 hover:bg-slate-800/40'
                            }
                            ${uploading ? 'pointer-events-none opacity-60' : ''}`}
              >
                <input
                  ref={inputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={e => pickFile(e.target.files[0])}
                  disabled={uploading}
                />

                {file ? (
                  <>
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/15 flex items-center justify-center mb-3">
                      <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <p className="text-sm font-semibold text-emerald-300 mb-0.5">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB · PDF</p>
                    {!uploading && (
                      <button
                        onClick={e => { e.stopPropagation(); setFile(null); setTitle(''); }}
                        className="mt-3 text-xs text-slate-500 hover:text-red-400 underline transition-colors"
                      >
                        Remove file
                      </button>
                    )}
                  </>
                ) : (
                  <>
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-3 transition-colors ${
                      dragging ? 'bg-blue-500/20' : 'bg-slate-700/40'
                    }`}>
                      <svg className={`w-6 h-6 transition-colors ${dragging ? 'text-blue-400' : 'text-slate-500'}`}
                        fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-slate-300 mb-1">
                      {dragging ? 'Drop to upload' : 'Drop PDF here or click to browse'}
                    </p>
                    <p className="text-xs text-slate-600">PDF files only · Max 50 MB</p>
                  </>
                )}
              </div>
            </div>

            {/* Upload progress */}
            {uploading && (
              <div className="bg-slate-900/60 border border-slate-700/40 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-white">{STEPS[step]}</p>
                    <p className="text-xs text-slate-500">Step {step + 1} of {STEPS.length}</p>
                  </div>
                </div>
                {/* Step dots */}
                <div className="flex items-center gap-1.5">
                  {STEPS.map((s, i) => (
                    <div key={i} className="flex-1 h-1 rounded-full overflow-hidden bg-slate-700/60">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          i < step ? 'bg-blue-500' :
                          i === step ? 'bg-blue-400 animate-pulse' :
                          'bg-transparent'
                        }`}
                        style={{ width: i <= step ? '100%' : '0%' }}
                      />
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-600 mt-2">This may take 30–60 seconds for large PDFs…</p>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="flex items-start gap-3 bg-red-900/20 border border-red-700/30 rounded-xl p-4">
                <svg className="w-5 h-5 text-red-400 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-300">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={() => navigate('/tenders')}
                disabled={uploading}
                className="px-5 py-2.5 border border-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700/40
                           rounded-xl text-sm font-medium transition-all disabled:opacity-40"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all
                  ${!file || uploading
                    ? 'bg-slate-700/40 text-slate-600 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-900/30'
                  }`}
              >
                {uploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analysing…
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Upload & Analyse Tender
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Feature cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-6">
            {FEATURES.map(f => {
              const accents = {
                blue:    'from-blue-900/30 to-slate-900/60 border-blue-700/20',
                rose:    'from-rose-900/30 to-slate-900/60 border-rose-700/20',
                emerald: 'from-emerald-900/30 to-slate-900/60 border-emerald-700/20',
              };
              return (
                <div key={f.title} className={`bg-gradient-to-br ${accents[f.accent]} border rounded-xl p-4`}>
                  <div className="mb-3">{f.icon}</div>
                  <p className="text-sm font-semibold text-white mb-1">{f.title}</p>
                  <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenderUpload;
