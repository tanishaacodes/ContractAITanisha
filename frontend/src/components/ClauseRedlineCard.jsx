import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  Edit3,
  RefreshCw,
  Scale,
  AlertTriangle,
  Info,
  Loader
} from 'lucide-react';

const ClauseRedlineCard = ({
  clause,
  index,
  isExpanded,
  onToggle,
  onAccept,
  onReject,
  onModify,
  onRegenerate
}) => {
  const [editMode, setEditMode] = useState(false);
  const [editedText, setEditedText] = useState(clause.suggested_text || '');
  const [regenerating, setRegenerate] = useState(false);
  const [showLegalDetails, setShowLegalDetails] = useState(false);

  const getRiskBadge = (score) => {
    if (score >= 70) return { label: 'HIGH RISK', color: 'bg-red-600', border: 'border-red-500' };
    if (score >= 40) return { label: 'MEDIUM RISK', color: 'bg-yellow-600', border: 'border-yellow-500' };
    return { label: 'LOW RISK', color: 'bg-green-600', border: 'border-green-500' };
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACCEPTED':
        return { label: 'Accepted', color: 'bg-green-600', icon: CheckCircle };
      case 'REJECTED':
        return { label: 'Rejected', color: 'bg-red-600', icon: XCircle };
      case 'MODIFIED':
        return { label: 'Modified', color: 'bg-blue-600', icon: Edit3 };
      default:
        return { label: 'Pending', color: 'bg-slate-600', icon: null };
    }
  };

  const handleRegenerate = async (perspective) => {
    setRegenerate(true);
    try {
      await onRegenerate(perspective);
    } finally {
      setRegenerate(false);
    }
  };

  const handleAccept = () => {
    if (editMode) {
      onModify(editedText);
      setEditMode(false);
    } else {
      onAccept(clause.suggested_text);
    }
  };

  const riskBadge = getRiskBadge(clause.risk_score);
  const statusBadge = getStatusBadge(clause.status);
  const StatusIcon = statusBadge.icon;

  return (
    <div className={`bg-slate-800 rounded-xl border-2 overflow-hidden transition-all ${
      clause.status === 'ACCEPTED' ? 'border-green-500/50' :
      clause.status === 'REJECTED' ? 'border-red-500/50' :
      clause.status === 'MODIFIED' ? 'border-blue-500/50' :
      riskBadge.border
    }`}>
      {/* Header */}
      <div
        onClick={onToggle}
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-700/50 transition"
      >
        <div className="flex items-center gap-4">
          {/* Index badge */}
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg font-bold text-sm ${
            clause.risk_score >= 70 ? 'bg-red-900/50 text-red-400 border border-red-700' :
            clause.risk_score >= 40 ? 'bg-yellow-900/50 text-yellow-400 border border-yellow-700' :
            'bg-green-900/50 text-green-400 border border-green-700'
          }`}>
            {index}
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white">{clause.clause_name}</h3>
            <div className="flex items-center gap-3 mt-1">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${riskBadge.color} text-white`}>
                {riskBadge.label} ({clause.risk_score}/100)
              </span>
              <span className="text-sm text-slate-400">{clause.risk_type}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {clause.status !== 'PENDING' && (
            <span className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold ${statusBadge.color} text-white`}>
              {StatusIcon && <StatusIcon size={14} />}
              {statusBadge.label}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp size={24} className="text-slate-400" />
          ) : (
            <ChevronDown size={24} className="text-slate-400" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-slate-700 p-6 space-y-6">
          {/* Risk Explanation */}
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
            <div className="flex items-start gap-3">
              <AlertTriangle className={`flex-shrink-0 ${
                clause.risk_score >= 70 ? 'text-red-400' :
                clause.risk_score >= 40 ? 'text-yellow-400' :
                'text-green-400'
              }`} size={20} />
              <div>
                <h4 className="font-medium text-white mb-1">Risk Analysis</h4>
                <p className="text-sm text-slate-300">{clause.risk_explanation}</p>
              </div>
            </div>
          </div>

          {/* Track Changes View */}
          <div className="grid md:grid-cols-2 gap-4">
            {/* Original Text */}
            <div>
              <h4 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-2">
                <XCircle size={16} />
                Original Clause
              </h4>
              <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                <p className="text-red-300 line-through whitespace-pre-wrap text-sm">
                  {clause.original_text}
                </p>
              </div>
            </div>

            {/* Suggested Text */}
            <div>
              <h4 className="text-sm font-medium text-green-400 mb-2 flex items-center gap-2">
                <CheckCircle size={16} />
                Suggested Revision
              </h4>
              <div className="bg-green-900/20 border border-green-800 rounded-lg p-4">
                {editMode ? (
                  <textarea
                    value={editedText}
                    onChange={(e) => setEditedText(e.target.value)}
                    className="w-full bg-slate-800 text-white rounded-lg p-3 border border-slate-600 focus:border-blue-500 focus:outline-none text-sm min-h-[150px]"
                    placeholder="Edit the suggested text..."
                  />
                ) : (
                  <p className="text-green-300 whitespace-pre-wrap text-sm">
                    {clause.accepted_text || clause.suggested_text}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Legal Explainability */}
          {(clause.legal_doctrine || clause.court_reasoning) && (
            <div>
              <button
                onClick={() => setShowLegalDetails(!showLegalDetails)}
                className="flex items-center gap-2 text-slate-300 hover:text-white transition mb-3"
              >
                <Scale size={18} />
                <span className="font-medium">Legal Analysis</span>
                {showLegalDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showLegalDetails && (
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700 space-y-4">
                  {clause.legal_doctrine && (
                    <div>
                      <h5 className="text-sm font-medium text-slate-300 mb-1">Legal Doctrine</h5>
                      <p className="text-sm text-slate-400">{clause.legal_doctrine}</p>
                    </div>
                  )}

                  {clause.court_reasoning && (
                    <div>
                      <h5 className="text-sm font-medium text-slate-300 mb-1">Court Reasoning</h5>
                      <p className="text-sm text-slate-400">{clause.court_reasoning}</p>
                    </div>
                  )}

                  {clause.litigation_risk && (
                    <div>
                      <h5 className="text-sm font-medium text-slate-300 mb-1">Litigation Risk</h5>
                      <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        clause.litigation_risk.includes('High') || clause.litigation_risk.includes('Very')
                          ? 'bg-red-900/50 text-red-400'
                          : clause.litigation_risk.includes('Moderate')
                          ? 'bg-yellow-900/50 text-yellow-400'
                          : 'bg-green-900/50 text-green-400'
                      }`}>
                        {clause.litigation_risk}
                      </span>
                    </div>
                  )}

                  {clause.judicial_treatment && (
                    <div>
                      <h5 className="text-sm font-medium text-slate-300 mb-1">Typical Judicial Treatment</h5>
                      <p className="text-sm text-slate-400">{clause.judicial_treatment}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          {clause.status === 'PENDING' && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-700">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">Regenerate as:</span>
                <button
                  onClick={() => handleRegenerate('balanced')}
                  disabled={regenerating}
                  className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50"
                >
                  Balanced
                </button>
                <button
                  onClick={() => handleRegenerate('buyer_favorable')}
                  disabled={regenerating}
                  className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50"
                >
                  Buyer-Friendly
                </button>
                <button
                  onClick={() => handleRegenerate('seller_favorable')}
                  disabled={regenerating}
                  className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50"
                >
                  Seller-Friendly
                </button>
                {regenerating && <Loader size={16} className="animate-spin text-blue-400" />}
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    setEditedText(clause.suggested_text || '');
                    setEditMode(!editMode);
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition"
                >
                  <Edit3 size={16} />
                  {editMode ? 'Cancel Edit' : 'Edit'}
                </button>
                <button
                  onClick={onReject}
                  className="flex items-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-600 rounded-lg transition"
                >
                  <XCircle size={16} />
                  Keep Original
                </button>
                <button
                  onClick={handleAccept}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
                >
                  <CheckCircle size={16} />
                  {editMode ? 'Save Changes' : 'Accept Suggestion'}
                </button>
              </div>
            </div>
          )}

          {/* Already reviewed */}
          {clause.status !== 'PENDING' && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-700">
              <div className="flex items-center gap-2 text-slate-400">
                <Info size={16} />
                <span className="text-sm">
                  This clause has been {clause.status.toLowerCase()}.
                  {clause.reviewed_at && ` Reviewed on ${new Date(clause.reviewed_at).toLocaleDateString()}`}
                </span>
              </div>

              {clause.accepted_text && clause.status === 'MODIFIED' && (
                <div className="text-sm text-slate-300">
                  <span className="font-medium">Final Text:</span> {clause.accepted_text.substring(0, 100)}...
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ClauseRedlineCard;
