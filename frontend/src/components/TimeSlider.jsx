/**
 * Time Slider Component
 * Allows filtering contracts by version for time-series analysis
 */
import React from 'react';

const TimeSlider = ({ version, setVersion, minVersion = 1, maxVersion = 10 }) => {
  return (
    <div className="w-full px-4 py-6 bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-semibold text-gray-300">
          Contract Version
        </label>
        <span className="text-lg font-bold text-blue-400">
          v{version}
        </span>
      </div>

      <input
        type="range"
        min={minVersion}
        max={maxVersion}
        step={1}
        value={version}
        onChange={(e) => {
          const newVersion = parseInt(e.target.value);
          console.log('Slider changed to version:', newVersion);
          setVersion(newVersion);
        }}
        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
        style={{
          background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((version - minVersion) / (maxVersion - minVersion)) * 100}%, #374151 ${((version - minVersion) / (maxVersion - minVersion)) * 100}%, #374151 100%)`
        }}
      />

      <div className="flex justify-between text-xs text-gray-500 mt-2">
        <span>v{minVersion}</span>
        <span>v{maxVersion}</span>
      </div>
    </div>
  );
};

export default TimeSlider;
