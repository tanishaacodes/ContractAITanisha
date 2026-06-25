import React from 'react';

const PreBidQuestions = ({ questions = [] }) => {
  const categoryColors = {
    COMMERCIAL: 'bg-blue-100 text-blue-800',
    TECHNICAL: 'bg-purple-100 text-purple-800',
    RISK: 'bg-red-100 text-red-800',
    SCOPE: 'bg-green-100 text-green-800',
    ELIGIBILITY: 'bg-yellow-100 text-yellow-800',
    TIMELINE: 'bg-orange-100 text-orange-800',
  };

  return (
    <div className="space-y-4">
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6">
        <h3 className="text-lg font-bold mb-4">Pre-Bid Clarification Questions</h3>
        {questions.length === 0 ? (
          <p className="text-slate-400">No pre-bid questions generated yet</p>
        ) : (
          <div className="space-y-4">
            {questions.map((q, i) => (
              <div key={i} className="border border-slate-700 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${categoryColors[q.category] || 'bg-slate-800 text-white'}`}>
                    {q.category}
                  </span>
                </div>
                <p className="text-white font-medium mb-2">{q.question}</p>
                {q.rationale && <p className="text-sm text-slate-300">{q.rationale}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="flex justify-end">
        <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Export Questions
        </button>
      </div>
    </div>
  );
};

export default PreBidQuestions;
