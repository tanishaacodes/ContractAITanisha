/**
 * Proposal Builder Component
 * Generates, displays, and exports the tender proposal
 */
import React, { useState } from 'react';
import tenderService from '../../services/tenderService';

// Render inline markdown: **bold** and plain text
const InlineMarkdown = ({ text }) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith('**') && part.endsWith('**')
          ? <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>
          : <span key={i}>{part}</span>
      )}
    </>
  );
};

// Render section text: bullet lines with bold inline support
const SectionContent = ({ text }) => {
  if (!text) return null;
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  return (
    <ul className="space-y-3">
      {lines.map((line, i) => {
        const content = line.replace(/^[-•*]\s*/, '');
        if (!content) return null;
        return (
          <li key={i} className="flex items-start gap-2 text-slate-300 text-sm leading-relaxed">
            <span className="text-blue-400 mt-0.5 shrink-0 text-base">›</span>
            <span><InlineMarkdown text={content} /></span>
          </li>
        );
      })}
    </ul>
  );
};

const SECTIONS = [
  { key: 'technical_compliance', label: 'Technical Compliance Matrix', icon: '✅' },
  { key: 'construction_methodology', label: 'Construction Methodology', icon: '🏗️' },
  { key: 'resource_mobilization', label: 'Resource Mobilisation', icon: '👷' },
  { key: 'risk_mitigation', label: 'Risk Mitigation Strategy', icon: '🛡️' },
  { key: 'commercial_positioning', label: 'Commercial Positioning', icon: '💼' },
  { key: 'schedule_assurance', label: 'Schedule Assurance', icon: '📅' },
  { key: 'value_engineering', label: 'Value Engineering', icon: '💡' },
];

const ProposalBuilder = ({ tenderId, proposal: initialProposal }) => {
  const [proposal, setProposal] = useState(initialProposal);
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [activeSection, setActiveSection] = useState('full_proposal');
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const data = await tenderService.generateProposal(tenderId);
      setProposal(data);
    } catch (err) {
      setError('Failed to generate proposal. Please try again.');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await tenderService.exportReport(tenderId);
    } catch (err) {
      setError('Failed to export report. Please try again.');
      console.error(err);
    } finally {
      setExporting(false);
    }
  };

  const hasContent = proposal && (
    proposal.full_proposal ||
    SECTIONS.some(s => proposal[s.key])
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-white">Tender Proposal</h3>
            <p className="text-slate-400 text-sm mt-1">
              AI-generated bid proposal with competitive positioning
            </p>
          </div>
          <div className="flex gap-3">
            {hasContent && (
              <button
                onClick={handleExport}
                disabled={exporting}
                className="flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                {exporting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                )}
                {exporting ? 'Exporting...' : 'Export Full Report'}
              </button>
            )}
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {generating ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              )}
              {generating ? 'Generating...' : hasContent ? 'Regenerate' : 'Generate Proposal'}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Content */}
      {!hasContent ? (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
          <div className="text-5xl mb-4">📄</div>
          <h4 className="text-lg font-semibold text-white mb-2">No Proposal Generated Yet</h4>
          <p className="text-slate-400 text-sm mb-6">
            Click "Generate Proposal" above to create a comprehensive AI-powered bid proposal
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl mx-auto">
            {['Technical Compliance Matrix', 'Commercial Positioning', 'Risk Mitigation Strategy'].map(item => (
              <div key={item} className="bg-slate-700/50 rounded-lg p-3 text-xs text-slate-300">
                <div className="text-blue-400 font-medium mb-1">✓ {item}</div>
                <div className="text-slate-400">Auto-generated section</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar nav */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 sticky top-4">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Sections</h4>
              <nav className="space-y-1">
                <button
                  onClick={() => setActiveSection('full_proposal')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    activeSection === 'full_proposal'
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  📋 Full Proposal
                </button>
                {SECTIONS.map(section => (
                  proposal[section.key] && (
                    <button
                      key={section.key}
                      onClick={() => setActiveSection(section.key)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        activeSection === section.key
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {section.icon} {section.label}
                    </button>
                  )
                ))}
              </nav>
            </div>
          </div>

          {/* Content pane */}
          <div className="lg:col-span-3">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              {activeSection === 'full_proposal' ? (
                <>
                  <h4 className="text-lg font-semibold text-white mb-4">Full Proposal</h4>
                  <div className="bg-slate-900 rounded-lg p-5 space-y-6">
                    {SECTIONS.map(section => proposal[section.key] && (
                      <div key={section.key}>
                        <h5 className="text-blue-400 font-semibold text-sm mb-3">
                          {section.icon} {section.label}
                        </h5>
                        <SectionContent text={proposal[section.key]} />
                        <hr className="border-slate-700 mt-4" />
                      </div>
                    ))}
                    {!SECTIONS.some(s => proposal[s.key]) && (
                      <p className="text-slate-400 text-sm">Full proposal content will appear here after generation.</p>
                    )}
                  </div>
                </>
              ) : (
                <>
                  {SECTIONS.filter(s => s.key === activeSection).map(section => (
                    <div key={section.key}>
                      <h4 className="text-lg font-semibold text-white mb-4">
                        {section.icon} {section.label}
                      </h4>
                      <div className="bg-slate-900 rounded-lg p-5">
                        <SectionContent text={proposal[section.key]} />
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProposalBuilder;
