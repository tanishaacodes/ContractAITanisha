import { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const INTENT_LABELS = {
  risk_transfer: 'Risk Transfer',
  liability_shielding: 'Liability Shield',
  payment_control: 'Payment Control',
  termination_leverage: 'Termination',
  compliance_burden: 'Compliance'
};

export default function IntentHeatmapGrid({ rows }) {
  const navigate = useNavigate();
  const [expandedRow, setExpandedRow] = useState(null);

  const getIntentColor = (score) => {
    if (score < 0.3) return 'bg-green-500 text-white';
    if (score < 0.6) return 'bg-yellow-500 text-gray-900';
    return 'bg-red-500 text-white';
  };

  const getIntentColorRing = (score) => {
    if (score < 0.3) return 'border-green-500';
    if (score < 0.6) return 'border-yellow-500';
    return 'border-red-500';
  };

  const toggleRow = (index) => {
    setExpandedRow(expandedRow === index ? null : index);
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
      {/* Header Row */}
      <div className="grid grid-cols-7 bg-gray-900/50 border-b border-gray-700 font-semibold text-gray-300 text-sm">
        <div className="p-4 col-span-2">Clause / Section</div>
        {Object.values(INTENT_LABELS).map((label) => (
          <div key={label} className="p-4 text-center">
            {label}
          </div>
        ))}
      </div>

      {/* Data Rows */}
      {rows.map((row, index) => (
        <div key={index}>
          {/* Main Row */}
          <div
            className={`grid grid-cols-7 border-b border-gray-700 hover:bg-gray-750 transition cursor-pointer ${
              expandedRow === index ? 'bg-gray-750' : ''
            }`}
            onClick={() => toggleRow(index)}
          >
            {/* Section Name */}
            <div className="p-4 col-span-2 flex items-center justify-between">
              <div>
                <p className="text-white font-medium">{row.section}</p>
                {row.clause_id && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/clauses/${row.clause_id}/intelligence`);
                    }}
                    className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center mt-1"
                  >
                    View Details
                    <ExternalLink className="w-3 h-3 ml-1" />
                  </button>
                )}
              </div>
              {expandedRow === index ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </div>

            {/* Intent Scores */}
            {Object.keys(INTENT_LABELS).map((intent) => {
              const score = row[intent] || 0;
              return (
                <div key={intent} className="p-4 flex items-center justify-center">
                  <div
                    className={`w-16 h-16 rounded-lg ${getIntentColor(score)} flex items-center justify-center font-bold text-lg shadow-lg border-2 ${getIntentColorRing(score)}`}
                  >
                    {score.toFixed(2)}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Expanded Details */}
          {expandedRow === index && (
            <div className="bg-gray-900/50 border-b border-gray-700 p-6">
              <h4 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wide">
                Intent Breakdown
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {Object.entries(INTENT_LABELS).map(([intent, label]) => {
                  const score = row[intent] || 0;
                  return (
                    <div key={intent} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                      <p className="text-xs text-gray-500 mb-2">{label}</p>
                      <p className="text-2xl font-bold text-white mb-2">
                        {(score * 100).toFixed(0)}%
                      </p>
                      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getIntentColor(score).split(' ')[0]}`}
                          style={{ width: `${score * 100}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        {score > 0.7 ? 'Strong' :
                         score > 0.4 ? 'Moderate' :
                         score > 0.2 ? 'Weak' : 'Minimal'}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
