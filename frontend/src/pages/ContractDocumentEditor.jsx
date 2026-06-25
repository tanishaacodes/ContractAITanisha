import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import {
  ArrowLeft, Save, Download, Wand2, Sparkles,
  FileText, FileDown, Loader2, Check, X, AlertCircle
} from 'lucide-react';

const ContractDocumentEditor = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const editorRef = useRef(null);

  const [contract, setContract] = useState(null);
  const [documentText, setDocumentText] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedText, setSelectedText] = useState('');

  // AI Suggestion Modal
  const [showAISuggestion, setShowAISuggestion] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState(null);

  // Download format selector
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  useEffect(() => {
    fetchContractData();
  }, [contractId]);

  // Track text selection
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection.toString().trim();
      setSelectedText(text);
    };

    document.addEventListener('mouseup', handleSelection);
    document.addEventListener('keyup', handleSelection);

    return () => {
      document.removeEventListener('mouseup', handleSelection);
      document.removeEventListener('keyup', handleSelection);
    };
  }, []);

  const fetchContractData = async () => {
    try {
      setLoading(true);
      // Try to get full contract data with all fields
      const response = await api.get(`/contracts/${contractId}`);

      console.log('Contract data:', response.data); // Debug log

      if (response.data) {
        setContract(response.data);

        // Try multiple fields to get the full text
        let fullText = response.data.full_text ||
                      response.data.extracted_text ||
                      response.data.raw_text ||
                      response.data.content ||
                      '';

        // If still empty, try to fetch clauses and build from them
        if (!fullText || fullText.trim() === '') {
          console.log('No full_text found, fetching clauses...');
          try {
            const clausesResponse = await api.get(`/contracts/${contractId}/clauses/edit`);
            if (clausesResponse.data.success && clausesResponse.data.clauses) {
              // Build full text from clauses
              fullText = clausesResponse.data.clauses
                .map(c => `${c.clause_name}\n\n${c.current_text}\n\n`)
                .join('\n');
            }
          } catch (err) {
            console.error('Error fetching clauses:', err);
          }
        }

        setDocumentText(fullText);
        console.log('Loaded text length:', fullText.length);
      } else {
        alert('Failed to load contract');
        navigate(-1);
      }
    } catch (error) {
      console.error('Error fetching contract:', error);
      alert('Failed to load contract');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleTextChange = (e) => {
    setDocumentText(e.target.value);
  };

  const handleGetAISuggestion = async () => {
    if (!selectedText || selectedText.length < 10) {
      alert('Please select at least 10 characters of text to get AI suggestions');
      return;
    }

    try {
      setAiLoading(true);
      setShowAISuggestion(true);

      const response = await api.post('/ai/suggest-improvement', {
        selected_text: selectedText,
        context: documentText.substring(0, 500)
      });

      if (response.data.success) {
        setAiSuggestion(response.data);
      } else {
        alert(response.data.error || 'Failed to get AI suggestion');
        setShowAISuggestion(false);
      }
    } catch (error) {
      console.error('Error getting AI suggestion:', error);
      alert('Failed to get AI suggestion. Please try again.');
      setShowAISuggestion(false);
    } finally {
      setAiLoading(false);
    }
  };

  const handleAcceptSuggestion = () => {
    if (!aiSuggestion || !selectedText) return;

    // Replace selected text with suggestion in the textarea
    const textarea = editorRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    const newText = documentText.substring(0, start) +
                   aiSuggestion.suggested_text +
                   documentText.substring(end);

    setDocumentText(newText);
    setShowAISuggestion(false);
    setAiSuggestion(null);
    setSelectedText('');
  };

  const handleRejectSuggestion = () => {
    setShowAISuggestion(false);
    setAiSuggestion(null);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      localStorage.setItem(`contract_${contractId}_draft`, documentText);
      alert('✅ Contract saved successfully!');
    } catch (error) {
      console.error('Error saving:', error);
      alert('Failed to save contract');
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = async (format) => {
    try {
      setShowDownloadMenu(false);

      const response = await api.post(`/contracts/${contractId}/regenerate`, {
        output_format: format
      });

      if (response.data.success) {
        const versionId = response.data.contract_version.id;
        window.location.href = `${api.defaults.baseURL}/contract-versions/${versionId}/download`;
        alert(`✅ ${format.toUpperCase()} generated successfully!`);
      } else {
        alert(response.data.error || 'Failed to generate document');
      }
    } catch (error) {
      console.error('Error downloading:', error);
      alert(`Failed to generate ${format.toUpperCase()}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0f172a]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-400">Loading contract...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#0f172a] flex flex-col">
      {/* Top Bar - Dark theme matching dashboard */}
      <div className="bg-[#1e293b] border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition"
            >
              <ArrowLeft size={20} />
              Back
            </button>
            <div className="h-6 w-px bg-gray-600"></div>
            <h1 className="text-lg font-semibold text-white">
              Contract Editor
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {/* AI Suggestion Button */}
            {selectedText && selectedText.length >= 10 && (
              <button
                onClick={handleGetAISuggestion}
                className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-4 py-2 rounded-lg transition shadow-md"
                disabled={aiLoading}
              >
                {aiLoading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Wand2 size={18} />
                )}
                AI Suggest
              </button>
            )}

            <button
              onClick={handleSave}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition"
              disabled={saving}
            >
              {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
              Save
            </button>

            <div className="relative">
              <button
                onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
              >
                <Download size={18} />
                Download
              </button>

              {showDownloadMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-xl border border-gray-700 z-50">
                  <button
                    onClick={() => handleDownload('pdf')}
                    className="w-full text-left px-4 py-3 hover:bg-gray-700 text-white transition flex items-center gap-2"
                  >
                    <FileDown size={16} />
                    Download as PDF
                  </button>
                  <button
                    onClick={() => handleDownload('docx')}
                    className="w-full text-left px-4 py-3 hover:bg-gray-700 text-white transition flex items-center gap-2 border-t border-gray-700"
                  >
                    <FileText size={16} />
                    Download as DOCX
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      {selectedText && selectedText.length >= 10 && (
        <div className="bg-purple-900/30 border-b border-purple-700 px-6 py-3">
          <div className="flex items-start gap-2 text-purple-200">
            <Sparkles className="flex-shrink-0 mt-0.5" size={18} />
            <div className="text-sm">
              <strong>Text Selected!</strong> Click "AI Suggest" to get intelligent improvements.
            </div>
          </div>
        </div>
      )}

      {/* Editor - Full height white area */}
      <div className="flex-1 overflow-hidden p-6">
        <div className="h-full bg-white rounded-lg shadow-2xl flex flex-col">
          <textarea
            ref={editorRef}
            value={documentText}
            onChange={handleTextChange}
            className="flex-1 w-full p-12 border-none focus:outline-none focus:ring-0 resize-none"
            style={{
              fontFamily: 'Calibri, Arial, sans-serif',
              fontSize: '14px',
              lineHeight: '1.6',
              color: '#000000',
              whiteSpace: 'pre-wrap'
            }}
            placeholder="Contract text will appear here..."
          />
        </div>
      </div>

      {/* AI Suggestion Modal */}
      {showAISuggestion && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full border border-gray-700 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg">
                    <Sparkles className="text-white" size={24} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">AI Suggestion</h2>
                    <p className="text-gray-400 text-sm mt-1">Review and apply AI-powered improvements</p>
                  </div>
                </div>
                <button
                  onClick={handleRejectSuggestion}
                  className="text-gray-400 hover:text-white transition"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            <div className="p-6">
              {aiLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-12 h-12 animate-spin text-purple-500" />
                  <span className="ml-3 text-gray-300">Analyzing with AI...</span>
                </div>
              ) : aiSuggestion ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                      <AlertCircle className="text-orange-500" size={20} />
                      Original Text
                    </h3>
                    <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
                      <p className="text-gray-300 leading-relaxed">{aiSuggestion.original_text}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                      <Check className="text-green-500" size={20} />
                      Suggested Improvement
                    </h3>
                    <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
                      <p className="text-gray-300 leading-relaxed">{aiSuggestion.suggested_text}</p>
                    </div>
                  </div>

                  {aiSuggestion.improvements && aiSuggestion.improvements.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-3">Key Improvements</h3>
                      <ul className="space-y-2">
                        {aiSuggestion.improvements.map((improvement, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-gray-300">
                            <Check className="text-blue-500 flex-shrink-0 mt-1" size={16} />
                            <span>{improvement}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {aiSuggestion.reasoning && (
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-3">AI Reasoning</h3>
                      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
                        <p className="text-gray-300 leading-relaxed">{aiSuggestion.reasoning}</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            {!aiLoading && aiSuggestion && (
              <div className="p-6 border-t border-gray-700 flex justify-end gap-3">
                <button
                  onClick={handleRejectSuggestion}
                  className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
                >
                  Reject
                </button>
                <button
                  onClick={handleAcceptSuggestion}
                  className="px-6 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg transition flex items-center gap-2"
                >
                  <Check size={18} />
                  Accept & Apply
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractDocumentEditor;
