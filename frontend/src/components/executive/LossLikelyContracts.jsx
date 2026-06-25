import { useEffect, useState } from 'react';
import axios from 'axios';
import { FileWarning } from 'lucide-react';

const LossLikelyContracts = () => {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/loss-risk`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setContracts(response.data);
      } catch (error) {
        console.error('Error fetching loss risk contracts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
        <div className="animate-pulse">
          <div className="h-4 bg-slate-800 rounded w-48 mb-4"></div>
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-6 bg-slate-800 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full">
      <div className="flex items-center gap-2 mb-4">
        <FileWarning className="w-5 h-5 text-orange-500" />
        <span className="text-xs text-slate-400 uppercase tracking-wider">
          Contracts Likely to Cause Loss
        </span>
      </div>

      {contracts.length === 0 ? (
        <div className="text-sm text-slate-500 italic">
          No high-risk contracts found
        </div>
      ) : (
        <div className="space-y-3">
          {contracts.map((contract, index) => (
            <div
              key={contract.id}
              className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-6 h-6 bg-red-500/20 text-red-400 rounded-full text-xs font-bold">
                  {index + 1}
                </div>
                <div>
                  <div className="text-sm text-slate-200 font-medium">{contract.name}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold text-red-400">
                  ₹ {contract.expected_loss} Cr
                </div>
                <div className="text-xs text-slate-500">Potential Loss</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LossLikelyContracts;
