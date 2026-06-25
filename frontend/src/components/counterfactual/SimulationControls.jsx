import { useState } from 'react';
import { Settings, Play } from 'lucide-react';

const SimulationControls = ({ onRun, loading }) => {
  const [state, setState] = useState({
    remove_clause: false,
    add_indemnity: false,
    add_arbitration: false,
    termination_rights: false,
    liability_cap: 1,
    governing_law: 'India'
  });

  const handleSubmit = () => {
    onRun(state);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Settings className="w-5 h-5 text-purple-400" />
        <h3 className="text-sm font-semibold text-white">What-If Controls</h3>
      </div>

      {/* Clause Modifications */}
      <div className="space-y-3">
        <p className="text-xs text-slate-400 uppercase tracking-wider mb-3">Clause Modifications</p>

        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={state.remove_clause}
            onChange={(e) => setState({ ...state, remove_clause: e.target.checked })}
            className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-purple-500 focus:ring-2 focus:ring-purple-500"
          />
          <span className="text-sm text-slate-300 group-hover:text-white transition">
            Remove unfavorable clause
          </span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={state.add_indemnity}
            onChange={(e) => setState({ ...state, add_indemnity: e.target.checked })}
            className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-purple-500 focus:ring-2 focus:ring-purple-500"
          />
          <span className="text-sm text-slate-300 group-hover:text-white transition">
            Add indemnity clause
          </span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={state.add_arbitration}
            onChange={(e) => setState({ ...state, add_arbitration: e.target.checked })}
            className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-purple-500 focus:ring-2 focus:ring-purple-500"
          />
          <span className="text-sm text-slate-300 group-hover:text-white transition">
            Add arbitration clause
          </span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={state.termination_rights}
            onChange={(e) => setState({ ...state, termination_rights: e.target.checked })}
            className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-purple-500 focus:ring-2 focus:ring-purple-500"
          />
          <span className="text-sm text-slate-300 group-hover:text-white transition">
            Add termination rights
          </span>
        </label>
      </div>

      {/* Liability Cap Slider */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Liability Cap</p>
          <span className="text-sm font-semibold text-purple-400">{state.liability_cap}x</span>
        </div>
        <input
          type="range"
          min="1"
          max="5"
          step="1"
          value={state.liability_cap}
          onChange={(e) => setState({ ...state, liability_cap: parseInt(e.target.value) })}
          className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider-thumb"
        />
        <div className="flex justify-between text-xs text-slate-500">
          <span>1x</span>
          <span>2x</span>
          <span>3x</span>
          <span>4x</span>
          <span>5x</span>
        </div>
      </div>

      {/* Governing Law */}
      <div className="space-y-3">
        <p className="text-xs text-slate-400 uppercase tracking-wider">Governing Law</p>
        <select
          value={state.governing_law}
          onChange={(e) => setState({ ...state, governing_law: e.target.value })}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
        >
          <option value="India">🇮🇳 India</option>
          <option value="UK">🇬🇧 United Kingdom</option>
          <option value="US">🇺🇸 United States</option>
          <option value="Singapore">🇸🇬 Singapore</option>
        </select>
      </div>

      {/* Run Button */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold transition ${
          loading
            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white'
        }`}
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Running Simulation...</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            <span>Run Simulation</span>
          </>
        )}
      </button>

      {/* Info */}
      <div className="pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500">
          Simulation uses 1,000 Monte Carlo trials to model risk distribution and calculate expected losses with 95% confidence intervals.
        </p>
      </div>

      <style jsx>{`
        .slider-thumb::-webkit-slider-thumb {
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #a855f7;
          cursor: pointer;
          box-shadow: 0 0 0 4px rgba(168, 85, 247, 0.2);
        }
        .slider-thumb::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #a855f7;
          cursor: pointer;
          border: none;
          box-shadow: 0 0 0 4px rgba(168, 85, 247, 0.2);
        }
      `}</style>
    </div>
  );
};

export default SimulationControls;
