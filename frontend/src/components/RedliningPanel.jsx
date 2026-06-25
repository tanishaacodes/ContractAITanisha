import { useState } from 'react';
import { CheckCircle, XCircle, Edit3, Loader } from 'lucide-react';

const RedliningPanel = ({ clause, onAccept, onReject, onEdit }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(clause.suggested_text || '');

  const handleEdit = () => {
    if (isEditing) {
      // Save edited text
      onEdit(editedText);
      setIsEditing(false);
    } else {
      setIsEditing(true);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      HIGH: 'text-red-300 bg-red-900/30 border border-red-700',
      MEDIUM: 'text-yellow-300 bg-yellow-900/30 border border-yellow-700',
      LOW: 'text-blue-300 bg-blue-900/30 border border-blue-700',
    };
    return colors[severity] || 'text-slate-300 bg-slate-900/30 border border-slate-700';
  };

  return (
    <div className="bg-slate-800 rounded-lg shadow-lg border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">{clause.clause_name}</h3>
            <p className="text-sm text-slate-300 mt-1">{clause.deviation_type?.replace('_', ' ')}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getSeverityColor(clause.severity)}`}>
              {clause.severity} RISK
            </span>
          </div>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 border-t border-slate-700">

        {/* LEFT: Original Clause */}
        <div className="bg-red-900/20 border-r border-slate-700/50 p-6">
          <div className="flex items-center gap-2 mb-3">
            <XCircle size={18} className="text-red-400" />
            <h4 className="font-semibold text-red-300">Original Clause</h4>
          </div>
          <div className="bg-slate-900 rounded-lg p-4 border-2 border-red-700 shadow-sm">
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {clause.original_text}
            </p>
          </div>

          {/* Recommendation */}
          {clause.recommendation && (
            <div className="mt-4 bg-yellow-900/20 border border-yellow-700 rounded-lg p-3">
              <p className="text-xs font-semibold text-yellow-300 mb-1">⚠️ Issue Identified:</p>
              <p className="text-xs text-yellow-200">{clause.recommendation}</p>
            </div>
          )}
        </div>

        {/* RIGHT: Suggested Clause */}
        <div className="bg-green-900/20 p-6">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle size={18} className="text-green-400" />
            <h4 className="font-semibold text-green-300">
              {isEditing ? 'Edit Suggestion' : 'AI-Suggested Alternative'}
            </h4>
          </div>

          {!clause.suggested_text ? (
            <div className="bg-slate-900 rounded-lg p-4 border-2 border-green-700 shadow-sm flex items-center justify-center min-h-[120px]">
              <div className="text-center text-slate-400">
                <Loader size={24} className="animate-spin mx-auto mb-2" />
                <p className="text-sm">Generating safer alternative...</p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 rounded-lg p-4 border-2 border-green-700 shadow-sm">
              {isEditing ? (
                <textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  className="w-full min-h-[120px] text-sm text-slate-200 leading-relaxed bg-slate-800 border border-green-600 rounded p-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              ) : (
                <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {clause.suggested_text}
                </p>
              )}
            </div>
          )}

          {/* Explanation */}
          {clause.explanation && (
            <div className="mt-4 bg-blue-900/20 border border-blue-700 rounded-lg p-3">
              <p className="text-xs font-semibold text-blue-300 mb-1">✨ AI Explanation:</p>
              <p className="text-xs text-blue-200">{clause.explanation}</p>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-slate-800 px-6 py-4 border-t border-slate-700 flex items-center justify-end gap-3">
        <button
          onClick={onReject}
          className="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 bg-slate-700 border border-slate-600 hover:bg-slate-600 transition flex items-center gap-2"
        >
          <XCircle size={16} />
          Keep Original
        </button>

        <button
          onClick={handleEdit}
          disabled={!clause.suggested_text}
          className="px-4 py-2 rounded-lg text-sm font-medium text-blue-300 bg-slate-700 border border-blue-600 hover:bg-slate-600 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Edit3 size={16} />
          {isEditing ? 'Save Edit' : 'Edit Suggestion'}
        </button>

        <button
          onClick={() => onAccept(isEditing ? editedText : clause.suggested_text)}
          disabled={!clause.suggested_text}
          className="px-4 py-2 rounded-lg text-sm font-medium text-white bg-green-600 hover:bg-green-700 transition flex items-center gap-2 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <CheckCircle size={16} />
          Accept Suggestion
        </button>
      </div>
    </div>
  );
};

export default RedliningPanel;
