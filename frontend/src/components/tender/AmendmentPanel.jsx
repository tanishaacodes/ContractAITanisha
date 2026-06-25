/**
 * Amendment Panel Component
 * Upload amended tender PDFs and view version history with diff summary
 */
import React, { useState, useEffect } from 'react';
import tenderService from '../../services/tenderService';

const AmendmentPanel = ({ tenderId, amendments: initialAmendments, onAmendmentUploaded }) => {
  const [amendments, setAmendments] = useState(initialAmendments || []);
  const [file, setFile] = useState(null);
  const [note, setNote] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f && f.type === 'application/pdf') {
      setFile(f);
      setError(null);
    } else if (f) {
      setError('Please select a valid PDF file');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select an amended PDF file');
      return;
    }
    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await tenderService.uploadAmendment(tenderId, file, note);
      setSuccess(`Amendment v${result.version} uploaded and re-analyzed successfully.`);
      setFile(null);
      setNote('');
      // Reload amendments list
      const updatedAmendments = result.tender?.amendments || [];
      setAmendments(updatedAmendments);
      if (onAmendmentUploaded) onAmendmentUploaded(result.tender);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload amendment. Please try again.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const getSnapshotChanges = (snap) => {
    if (!snap) return [];
    const changes = [];
    if (snap.estimated_value && snap.estimated_value !== 'None') {
      changes.push(`Contract Value: ₹${(parseFloat(snap.estimated_value) / 10000000).toFixed(2)} Cr`);
    }
    if (snap.risks_count !== undefined) changes.push(`Risks: ${snap.risks_count}`);
    if (snap.conflicts_count !== undefined) changes.push(`Conflicts: ${snap.conflicts_count}`);
    if (snap.work_items_count !== undefined) changes.push(`Work Items: ${snap.work_items_count}`);
    return changes;
  };

  return (
    <div className="space-y-6">
      {/* Upload New Amendment */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-1">Upload Amendment</h3>
        <p className="text-slate-400 text-sm mb-5">
          Upload a revised version of the tender document. The system will re-analyze and track changes.
        </p>

        <div className="space-y-4">
          {/* File picker */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Amended Tender PDF
            </label>
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="amendment-file"
                disabled={uploading}
              />
              <label htmlFor="amendment-file" className="cursor-pointer flex flex-col items-center">
                <svg className="w-10 h-10 text-slate-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                {file ? (
                  <span className="text-blue-400 font-medium">{file.name}</span>
                ) : (
                  <span className="text-slate-400 text-sm">Click to upload amended PDF</span>
                )}
              </label>
            </div>
          </div>

          {/* Amendment note */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Amendment Note <span className="text-slate-500">(optional)</span>
            </label>
            <input
              type="text"
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="e.g. Corrigendum 1 – Revised BOQ and LD clause"
              disabled={uploading}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 text-white placeholder-slate-400 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Feedback */}
          {error && (
            <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 text-sm">{error}</div>
          )}
          {success && (
            <div className="p-3 bg-green-900/30 border border-green-700/50 rounded-lg text-green-300 text-sm">{success}</div>
          )}

          {/* Upload btn */}
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className={`flex items-center px-5 py-2.5 rounded-lg text-white font-medium transition-colors ${
              !file || uploading
                ? 'bg-slate-600 cursor-not-allowed opacity-60'
                : 'bg-orange-600 hover:bg-orange-700'
            }`}
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Uploading & Re-analyzing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Upload & Re-analyze
              </>
            )}
          </button>
        </div>
      </div>

      {/* Amendment History */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">
          Amendment History
          {amendments.length > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-orange-900/50 text-orange-300 text-xs rounded-full border border-orange-700/50">
              {amendments.length} version{amendments.length !== 1 ? 's' : ''}
            </span>
          )}
        </h3>

        {amendments.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-slate-400 text-sm">No amendments uploaded yet.</p>
            <p className="text-slate-500 text-xs mt-1">
              Upload an amended PDF above to track version changes.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {amendments.map((amendment, index) => {
              const snapshotChanges = getSnapshotChanges(amendment.snapshot);
              return (
                <div
                  key={amendment.id}
                  className="border border-slate-700 rounded-lg p-4 hover:border-orange-700/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      {/* Version badge */}
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-orange-900/50 border border-orange-700/50 flex items-center justify-center">
                        <span className="text-orange-300 text-sm font-bold">v{amendment.version_number}</span>
                      </div>
                      <div>
                        <div className="font-medium text-white text-sm">
                          {amendment.amendment_note || `Amendment version ${amendment.version_number}`}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          {formatDate(amendment.created_at)}
                          {amendment.uploaded_by_name && (
                            <span className="ml-2">by {amendment.uploaded_by_name}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {index === 0 && (
                      <span className="px-2 py-0.5 bg-blue-900/50 text-blue-300 text-xs rounded border border-blue-700/50 flex-shrink-0">
                        Latest
                      </span>
                    )}
                  </div>

                  {/* Snapshot summary */}
                  {snapshotChanges.length > 0 && (
                    <div className="mt-3 ml-13 pl-13">
                      <p className="text-xs text-slate-500 mb-2">State before this amendment:</p>
                      <div className="flex flex-wrap gap-2">
                        {snapshotChanges.map((change, i) => (
                          <span key={i} className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded">
                            {change}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default AmendmentPanel;
