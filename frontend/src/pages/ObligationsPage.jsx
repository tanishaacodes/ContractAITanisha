import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckSquare } from 'lucide-react';
import ObligationExtractor from '../components/obligations/ObligationExtractor';
import useThemeStore from '../store/themeStore';

function ObligationsPage() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const { theme } = useThemeStore();

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
              background: '#10b98114',
              border: '1px solid #10b98128',
            }}>
              <CheckSquare size={20} style={{ color: '#10b981' }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Contract Obligations</h1>
              <p className="text-sm text-gray-400">Extract and manage contract obligations</p>
            </div>
          </div>
        </div>

        {/* Obligation Extractor Component */}
        <ObligationExtractor contractId={contractId} />
      </div>
    </div>
  );
}

export default ObligationsPage;
