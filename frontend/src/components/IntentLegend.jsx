import { Info } from 'lucide-react';

export default function IntentLegend() {
  return (
    <div className="mb-6 bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className="flex items-start">
        <Info className="w-5 h-5 text-blue-400 mr-3 mt-1 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-white font-semibold mb-3">Intent Categories Explained</h3>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-sm">
            <div>
              <p className="font-semibold text-cyan-400 mb-1">Risk Transfer</p>
              <p className="text-gray-400 text-xs">
                Shifting liability and responsibility from one party to another
              </p>
            </div>

            <div>
              <p className="font-semibold text-purple-400 mb-1">Liability Shielding</p>
              <p className="text-gray-400 text-xs">
                Limiting or capping damages, excluding consequential losses
              </p>
            </div>

            <div>
              <p className="font-semibold text-yellow-400 mb-1">Payment Control</p>
              <p className="text-gray-400 text-xs">
                Terms affecting payment timing, withholding, or dispute resolution
              </p>
            </div>

            <div>
              <p className="font-semibold text-orange-400 mb-1">Termination</p>
              <p className="text-gray-400 text-xs">
                Leverage over contract termination and exit conditions
              </p>
            </div>

            <div>
              <p className="font-semibold text-red-400 mb-1">Compliance</p>
              <p className="text-gray-400 text-xs">
                Regulatory, certification, and audit obligations placed on parties
              </p>
            </div>
          </div>

          <div className="mt-4 flex items-center space-x-6 text-xs">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-green-500 rounded mr-2"></div>
              <span className="text-gray-400">Low (0-0.3): Minimal intent</span>
            </div>
            <div className="flex items-center">
              <div className="w-6 h-6 bg-yellow-500 rounded mr-2"></div>
              <span className="text-gray-400">Medium (0.3-0.6): Moderate intent</span>
            </div>
            <div className="flex items-center">
              <div className="w-6 h-6 bg-red-500 rounded mr-2"></div>
              <span className="text-gray-400">High (0.6-1.0): Strong intent</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
