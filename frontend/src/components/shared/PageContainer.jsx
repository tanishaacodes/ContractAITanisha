/**
 * Reusable page container with consistent layout and header
 */
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ContractSelector from '../enterprise/ContractSelector';

export default function PageContainer({
  children,
  title,
  subtitle,
  icon: Icon,
  showBack = true,
  showContractSelector = true,
  contractId,
  onContractSelect,
  headerActions
}) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            {showBack && (
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-slate-700/50 rounded-xl transition-all"
              >
                <ArrowLeft className="w-6 h-6" />
              </button>
            )}
            <div className="flex items-center gap-3">
              {Icon && <Icon className="w-8 h-8 text-cyan-400" />}
              <div>
                <h1 className="text-3xl font-bold">{title}</h1>
                {subtitle && <p className="text-slate-400 text-sm mt-1">{subtitle}</p>}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {headerActions}
            {showContractSelector && (
              <ContractSelector
                selectedContractId={contractId}
                onSelectContract={onContractSelect}
              />
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {children}
      </div>
    </div>
  );
}
