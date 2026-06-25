import { Scale } from 'lucide-react';

const NegotiationShift = ({ value }) => {
  // value ranges from -1 to +1, where negative is better (more leverage for you)
  const percentage = Math.abs(value) * 100;
  const direction = value < 0 ? 'Improved' : value > 0 ? 'Weakened' : 'Neutral';
  const color = value < 0 ? 'green' : value > 0 ? 'red' : 'slate';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-slate-400 uppercase tracking-wider">Negotiation Power</p>
        <Scale className={`w-4 h-4 text-${color}-400`} />
      </div>

      {/* Value Display */}
      <div className="mb-4">
        <p className={`text-3xl font-bold text-${color}-400`}>
          {value < 0 ? '+' : value > 0 ? '-' : ''}{percentage.toFixed(0)}%
        </p>
        <p className="text-xs text-slate-500 mt-1">{direction}</p>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-slate-800 rounded-full overflow-hidden mb-3">
        <div
          className={`absolute top-0 h-full rounded-full transition-all duration-700 ease-out ${
            color === 'green' ? 'bg-gradient-to-r from-green-500 to-emerald-400' :
            color === 'red' ? 'bg-gradient-to-r from-red-500 to-rose-400' :
            'bg-slate-600'
          }`}
          style={{
            width: `${percentage}%`,
            left: value < 0 ? '50%' : 'auto',
            right: value > 0 ? '50%' : 'auto'
          }}
        />
        {/* Center marker */}
        <div className="absolute top-0 left-1/2 w-0.5 h-full bg-slate-600" />
      </div>

      {/* Scale Labels */}
      <div className="flex justify-between text-xs text-slate-600">
        <span>Weaker</span>
        <span className="text-slate-500">Neutral</span>
        <span>Stronger</span>
      </div>

      {/* Explanation */}
      <div className="mt-3 pt-3 border-t border-slate-800">
        <p className="text-xs text-slate-500">
          {value < 0
            ? 'Risk reduction improves your bargaining position'
            : value > 0
            ? 'Risk increase weakens your negotiating leverage'
            : 'No change in negotiation dynamics'}
        </p>
      </div>
    </div>
  );
};

export default NegotiationShift;
