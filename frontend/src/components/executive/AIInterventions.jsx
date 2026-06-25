import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Brain, ArrowRight } from 'lucide-react';

const AIInterventions = () => {
  const navigate = useNavigate();
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/executive/interventions`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setInterventions(response.data);
      } catch (error) {
        console.error('Error fetching interventions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-slate-800 rounded w-48 mb-4"></div>
          <div className="flex gap-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-8 bg-slate-800 rounded w-32"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-purple-500" />
        <span className="text-xs text-slate-400 uppercase tracking-wider">
          AI-Recommended Interventions
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {interventions.map((intervention, index) => {
          // Map interventions to appropriate navigation targets
          const getNavigationPath = (text) => {
            const lowerText = text.toLowerCase();
            if (lowerText.includes('liability') || lowerText.includes('cap')) {
              return '/contracts'; // Navigate to contracts to review liability
            } else if (lowerText.includes('arbitration')) {
              return '/contracts'; // Navigate to contracts to add arbitration
            } else if (lowerText.includes('indemnity') || lowerText.includes('rewrite')) {
              return '/contracts'; // Navigate to contracts for clause editing
            } else if (lowerText.includes('termination') || lowerText.includes('notice')) {
              return '/contracts'; // Navigate to contracts for termination clauses
            } else if (lowerText.includes('payment') || lowerText.includes('escrow')) {
              return '/contracts'; // Navigate to contracts for payment terms
            }
            return '/contracts'; // Default to contracts page
          };

          return (
            <div
              key={index}
              onClick={() => {
                const path = getNavigationPath(intervention);
                navigate(path);
              }}
              className="group bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-lg p-4 hover:border-purple-500/60 hover:shadow-lg hover:shadow-purple-500/20 transition-all cursor-pointer transform hover:scale-105 active:scale-95"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center group-hover:bg-purple-500/30 transition-colors">
                  <span className="text-xs font-bold text-purple-400">{index + 1}</span>
                </div>
                <div className="flex-1">
                  <div className="text-sm text-slate-200 leading-snug group-hover:text-white transition-colors">
                    {intervention}
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-purple-400 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 text-xs text-slate-500 text-center">
        Click any recommendation to view detailed analysis
      </div>
    </div>
  );
};

export default AIInterventions;
