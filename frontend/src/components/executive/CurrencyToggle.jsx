import { DollarSign, IndianRupee } from 'lucide-react';

const CurrencyToggle = ({ currency, onCurrencyChange }) => {
  return (
    <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg p-1">
      <button
        onClick={() => onCurrencyChange('INR')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition ${
          currency === 'INR'
            ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
            : 'text-slate-400 hover:text-white hover:bg-slate-800'
        }`}
      >
        <IndianRupee className="w-4 h-4" />
        INR
      </button>
      <button
        onClick={() => onCurrencyChange('USD')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition ${
          currency === 'USD'
            ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
            : 'text-slate-400 hover:text-white hover:bg-slate-800'
        }`}
      >
        <DollarSign className="w-4 h-4" />
        USD
      </button>
    </div>
  );
};

export default CurrencyToggle;
