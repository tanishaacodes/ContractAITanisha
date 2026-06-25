import React, { useState } from 'react';
import tenderService from '../../services/tenderService';

const NegotiationPanel = ({ tenderId, negotiations: initial, risks }) => {
  const [negotiations, setNegotiations] = useState(initial || []);
  const [loading, setLoading] = useState(false);

  const generateNegotiations = async () => {
    setLoading(true);
    try {
      const data = await tenderService.generateNegotiations(tenderId);
      setNegotiations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
        <h3 className="text-lg font-bold mb-4">Negotiation Strategy</h3>
        {negotiations.length === 0 ? (
          <button onClick={generateNegotiations} disabled={loading} className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            {loading ? 'Generating...' : 'Generate Counter-Proposals'}
          </button>
        ) : (
          <div className="space-y-4">
            {negotiations.map((neg, i) => (
              <div key={i} className="border border-slate-700 rounded-lg p-4">
                <h4 className="font-bold mb-2">{neg.issue_type}</h4>
                <p className="text-sm text-slate-200 mb-2"><strong>Original:</strong> {neg.original_clause}</p>
                <p className="text-sm text-green-700"><strong>Counter:</strong> {neg.counter_proposal}</p>
                {neg.acceptance_probability && (
                  <p className="text-xs text-slate-400 mt-2">Acceptance Probability: {(neg.acceptance_probability * 100).toFixed(0)}%</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NegotiationPanel;
