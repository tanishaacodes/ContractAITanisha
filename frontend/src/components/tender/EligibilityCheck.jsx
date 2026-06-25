import React, { useState } from 'react';
import tenderService from '../../services/tenderService';

const EligibilityCheck = ({ tenderId, eligibility }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const checkEligibility = async () => {
    setLoading(true);
    try {
      const data = await tenderService.checkEligibility(tenderId);
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
        <h3 className="text-lg font-bold mb-4">Eligibility Requirements</h3>
        {eligibility ? (
          <div className="space-y-2">
            <p className="text-white">
              Min Turnover: {eligibility.min_turnover && eligibility.min_turnover > 0 ?
                `₹${(eligibility.min_turnover / 10000000).toFixed(2)} Cr` :
                <span className="text-slate-400">N/A</span>}
            </p>
            <p className="text-white">
              Min Projects: {eligibility.min_projects || <span className="text-slate-400">N/A</span>}
            </p>
          </div>
        ) : (
          <p className="text-slate-400">No eligibility criteria specified</p>
        )}
        <button onClick={checkEligibility} disabled={loading} className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          {loading ? 'Checking...' : 'Check My Eligibility'}
        </button>
      </div>
      {result && (
        <div className={`p-6 rounded-lg ${result.eligible ? 'bg-green-900/30 border-green-700/50' : 'bg-red-900/30 border-red-700/50'} border`}>
          <h4 className="font-bold mb-2">{result.eligible ? '✅ Eligible' : '❌ Not Eligible'}</h4>
          {result.missing_criteria && result.missing_criteria.map((item, i) => (
            <p key={i} className="text-sm text-red-600">{item}</p>
          ))}
        </div>
      )}
    </div>
  );
};

export default EligibilityCheck;
