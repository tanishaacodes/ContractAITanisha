import { FileEdit, Download, Send, Zap } from 'lucide-react';

const ActionPanel = ({ onGenerateCounterProposal, onExportRedlines, onTriggerApproval }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-6">
        <Zap className="w-5 h-5 text-yellow-400" />
        <h3 className="text-sm font-semibold text-white">Legal Actions</h3>
      </div>

      {/* Action Buttons */}
      <div className="space-y-4">
        {/* Generate Counter-Proposal */}
        <button
          onClick={onGenerateCounterProposal}
          className="w-full group relative overflow-hidden bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-lg p-4 transition-all duration-300 transform hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <FileEdit className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold">Generate Counter-Proposal</p>
                <p className="text-xs text-purple-200 mt-0.5">
                  Create formal counter-proposal document
                </p>
              </div>
            </div>
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold">1</span>
            </div>
          </div>

          {/* Animated background */}
          <div className="absolute inset-0 bg-gradient-to-r from-purple-400/0 via-white/10 to-purple-400/0 transform -skew-x-12 group-hover:translate-x-full transition-transform duration-1000"></div>
        </button>

        {/* Export Redlines */}
        <button
          onClick={onExportRedlines}
          className="w-full group relative overflow-hidden bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-lg p-4 transition-all duration-300 transform hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Download className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold">Export Redlines (DOCX)</p>
                <p className="text-xs text-blue-200 mt-0.5">
                  Download marked-up contract document
                </p>
              </div>
            </div>
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold">2</span>
            </div>
          </div>

          {/* Animated background */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-400/0 via-white/10 to-blue-400/0 transform -skew-x-12 group-hover:translate-x-full transition-transform duration-1000"></div>
        </button>

        {/* Trigger Approval Workflow */}
        <button
          onClick={onTriggerApproval}
          className="w-full group relative overflow-hidden bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white rounded-lg p-4 transition-all duration-300 transform hover:scale-[1.02]"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Send className="w-5 h-5" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold">Send for Approval</p>
                <p className="text-xs text-green-200 mt-0.5">
                  Trigger legal team approval workflow
                </p>
              </div>
            </div>
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
              <span className="text-xs font-bold">3</span>
            </div>
          </div>

          {/* Animated background */}
          <div className="absolute inset-0 bg-gradient-to-r from-green-400/0 via-white/10 to-green-400/0 transform -skew-x-12 group-hover:translate-x-full transition-transform duration-1000"></div>
        </button>
      </div>

      {/* Info Panel */}
      <div className="mt-6 p-4 bg-purple-900/20 border border-purple-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <Zap className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-purple-400 font-semibold mb-1">Workflow Steps</p>
            <ol className="text-xs text-slate-400 space-y-1 list-decimal list-inside">
              <li>Generate counter-proposal with recommended language</li>
              <li>Export redlines for internal review and markup</li>
              <li>Send to legal team for final approval and execution</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mt-4 pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500 text-center">
          All actions are AI-assisted • Final review by legal counsel required
        </p>
      </div>
    </div>
  );
};

export default ActionPanel;
