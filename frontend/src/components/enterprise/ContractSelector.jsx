import { useState, useEffect } from 'react';
import { FileText, ChevronDown, Globe, X } from 'lucide-react';
import enterpriseRiskService from '../../services/enterpriseRiskService';

/**
 * Reusable contract selector for Enterprise Risk Intelligence pages.
 * Shows a dropdown to pick a specific contract OR view global/all-contracts data.
 *
 * Props:
 *  selectedContractId  — current selected contractId (or null/"" for global)
 *  onSelect(id, name)  — called when user picks a contract or clears selection
 *  accentColor         — tailwind color name for theming (default: 'cyan')
 */
export default function ContractSelector({ selectedContractId, onSelect, accentColor = 'cyan' }) {
  const [contracts, setContracts] = useState([]);
  const [open, setOpen] = useState(false);
  const [loadingContracts, setLoadingContracts] = useState(false);

  // Color map for border / text / bg accents
  const colorMap = {
    cyan:   { border: 'border-cyan-500/30',   hover: 'hover:border-cyan-400/50',   text: 'text-cyan-400',   bg: 'bg-cyan-500/10'   },
    violet: { border: 'border-violet-500/30', hover: 'hover:border-violet-400/50', text: 'text-violet-400', bg: 'bg-violet-500/10' },
    emerald:{ border: 'border-emerald-500/30',hover: 'hover:border-emerald-400/50',text: 'text-emerald-400',bg: 'bg-emerald-500/10' },
    amber:  { border: 'border-amber-500/30',  hover: 'hover:border-amber-400/50',  text: 'text-amber-400',  bg: 'bg-amber-500/10'  },
    red:    { border: 'border-red-500/30',    hover: 'hover:border-red-400/50',    text: 'text-red-400',    bg: 'bg-red-500/10'    },
  };
  const c = colorMap[accentColor] || colorMap.cyan;

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    setLoadingContracts(true);
    try {
      const portfolio = await enterpriseRiskService.getPortfolioContracts();
      setContracts(portfolio.contracts || []);
    } catch {
      setContracts([]);
    } finally {
      setLoadingContracts(false);
    }
  };

  const selectedContract = contracts.find(c => c.id === selectedContractId);
  const displayLabel = selectedContract
    ? selectedContract.name || selectedContract.title || `Contract ${selectedContract.id.slice(0, 8)}`
    : 'All Contracts (Global)';

  const handleSelect = (contract) => {
    onSelect(contract ? contract.id : null, contract ? (contract.name || contract.title) : null);
    setOpen(false);
  };

  return (
    <div className="relative">
      {/* Trigger button */}
      <button
        onClick={() => setOpen(prev => !prev)}
        className={`flex items-center gap-3 px-4 py-2.5 rounded-xl bg-slate-800/80 border ${c.border} ${c.hover} backdrop-blur-xl transition-all hover:bg-slate-700/80`}
      >
        {selectedContractId ? (
          <FileText className={`w-4 h-4 ${c.text} flex-shrink-0`} />
        ) : (
          <Globe className={`w-4 h-4 ${c.text} flex-shrink-0`} />
        )}
        <span className="text-sm font-medium text-white max-w-[200px] truncate">
          {displayLabel}
        </span>
        {selectedContractId && (
          <span
            role="button"
            onClick={(e) => { e.stopPropagation(); handleSelect(null); }}
            className="ml-1 p-0.5 rounded hover:bg-slate-600 transition-all cursor-pointer flex-shrink-0"
          >
            <X className="w-3 h-3 text-slate-400 hover:text-white" />
          </span>
        )}
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute top-full mt-2 left-0 z-50 min-w-[280px] max-w-[360px] bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden">
          {/* Global option */}
          <button
            onClick={() => handleSelect(null)}
            className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-800 transition-colors border-b border-slate-700 ${!selectedContractId ? c.bg : ''}`}
          >
            <Globe className={`w-4 h-4 ${c.text} flex-shrink-0`} />
            <div>
              <p className="text-sm font-semibold text-white">All Contracts (Global)</p>
              <p className="text-xs text-slate-400">Aggregate view across all contracts</p>
            </div>
            {!selectedContractId && (
              <span className={`ml-auto px-2 py-0.5 text-xs rounded-full ${c.bg} ${c.text} border ${c.border}`}>
                Active
              </span>
            )}
          </button>

          {/* Contract list */}
          <div className="max-h-64 overflow-y-auto">
            {loadingContracts ? (
              <div className="px-4 py-3 text-sm text-slate-400">Loading contracts...</div>
            ) : contracts.length === 0 ? (
              <div className="px-4 py-3 text-sm text-slate-400">No contracts found</div>
            ) : (
              contracts.map((contract) => {
                const name = contract.name || contract.title || `Contract ${contract.id.slice(0, 8)}`;
                const isActive = contract.id === selectedContractId;
                return (
                  <button
                    key={contract.id}
                    onClick={() => handleSelect(contract)}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-800 transition-colors border-b border-slate-700/50 last:border-0 ${isActive ? c.bg : ''}`}
                  >
                    <FileText className={`w-4 h-4 ${isActive ? c.text : 'text-slate-500'} flex-shrink-0`} />
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${isActive ? 'text-white' : 'text-slate-300'}`}>
                        {name}
                      </p>
                      {contract.counterparty && (
                        <p className="text-xs text-slate-500 truncate">{contract.counterparty}</p>
                      )}
                    </div>
                    {isActive && (
                      <span className={`ml-auto px-2 py-0.5 text-xs rounded-full ${c.bg} ${c.text} border ${c.border} flex-shrink-0`}>
                        Active
                      </span>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Backdrop to close dropdown */}
      {open && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setOpen(false)}
        />
      )}
    </div>
  );
}
