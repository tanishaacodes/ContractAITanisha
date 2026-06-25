import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Zap } from 'lucide-react';
import ClauseAddition from '../components/clauses/ClauseAddition';
import useThemeStore from '../store/themeStore';

function AddClausePage() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const { theme } = useThemeStore();

  const handleClauseAdded = (result) => {
    console.log('Clause added successfully:', result);
    // Show success notification
    alert(`Clause added successfully!\nRisk Level: ${result.risk_level}\nRisk Score: ${(result.risk_score * 100).toFixed(0)}%`);

    // Optional: Navigate back to contract details
    // navigate(`/contract/${contractId}`);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: theme === 'dark'
          ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)'
          : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      }}
    >
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate(`/contract/${contractId}`)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-slate-700/50 transition-colors"
          >
            <ArrowLeft size={20} />
            <span>Back to Contract</span>
          </button>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{
              background: '#06b6d414',
              border: '1px solid #06b6d428',
            }}>
              <Zap size={20} style={{ color: '#06b6d4' }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Add New Clause</h1>
              <p className="text-sm text-gray-400">Add clause with automatic risk assessment</p>
            </div>
          </div>
        </div>

        {/* Clause Addition Component */}
        <ClauseAddition
          contractId={contractId}
          onClauseAdded={handleClauseAdded}
        />
      </div>
    </div>
  );
}

export default AddClausePage;
