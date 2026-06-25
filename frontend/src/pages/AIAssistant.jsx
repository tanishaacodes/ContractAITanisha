/**
 * AI Assistant - Conversational Contract Intelligence
 * =====================================================
 * Chat interface for asking questions about contracts, risks, and clauses.
 *
 * Features:
 * - RAG-powered responses with contract context
 * - Multi-turn conversations with history
 * - Source citations from relevant clauses
 * - Real-time streaming responses
 */

import { useState, useEffect, useRef } from 'react';
import { MessageCircle, Send, Trash2, FileText, AlertCircle, Sparkles, User, Bot } from 'lucide-react';
import axios from 'axios';
import { config } from '../config/api.config';

const AIAssistant = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI contract intelligence assistant. Ask me anything about contract clauses, risks, payment terms, or dispute probabilities.',
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(`session_${Date.now()}`);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${config.API_BASE_URL}/ai-chat/message`,
        {
          message: inputMessage,
          session_id: sessionId
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources || [],
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Chat error:', error);

      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please ensure the AI service is running and try again.',
        error: true,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${config.API_BASE_URL}/ai-chat/session/${sessionId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setSessionId(`session_${Date.now()}`);
      setMessages([
        {
          role: 'assistant',
          content: 'Chat cleared. How can I help you with contract analysis today?',
          timestamp: new Date().toISOString()
        }
      ]);

    } catch (error) {
      console.error('Clear chat error:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestionPrompts = [
    "What are common payment term clauses?",
    "Explain dispute resolution mechanisms",
    "What are the key risk factors in contracts?",
    "How do force majeure clauses work?"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950/20 to-slate-950 p-6">
      {/* Header */}
      <div className="max-w-5xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
              <MessageCircle className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">AI Contract Assistant</h1>
              <p className="text-sm text-slate-400">Powered by AI + RAG</p>
            </div>
          </div>

          <button
            onClick={clearChat}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg border border-slate-700 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Chat Container */}
      <div className="max-w-5xl mx-auto">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
          {/* Messages Area */}
          <div className="h-[600px] overflow-y-auto p-6 space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  </div>
                )}

                <div className={`max-w-3xl ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div
                    className={`inline-block p-4 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-purple-600 to-pink-600 text-white'
                        : message.error
                        ? 'bg-red-900/30 border border-red-500/30 text-red-200'
                        : 'bg-slate-800 border border-slate-700 text-slate-100'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>

                    {/* Source Citations */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-700">
                        <p className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          <span>Sources:</span>
                        </p>
                        <div className="space-y-2">
                          {message.sources.map((source, idx) => (
                            <div
                              key={idx}
                              className="text-xs bg-slate-900/50 rounded-lg p-2 border border-slate-700"
                            >
                              <div className="flex items-start gap-2">
                                <span className="text-purple-400 font-mono">#{source.id}</span>
                                <span className="text-slate-300 flex-1">
                                  {source.text}
                                </span>
                              </div>
                              {source.type && (
                                <div className="mt-1 text-slate-500">Type: {source.type}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <p className="text-xs text-slate-500 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>

                {message.role === 'user' && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
                      <User className="w-5 h-5 text-white" />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-4">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggestion Prompts */}
          {messages.length === 1 && (
            <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/50">
              <p className="text-xs text-slate-400 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                <span>Try asking:</span>
              </p>
              <div className="grid grid-cols-2 gap-2">
                {suggestionPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputMessage(prompt)}
                    className="text-left text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg p-3 border border-slate-700 transition-colors"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 border-t border-slate-800 bg-slate-900/50">
            <div className="flex gap-3">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about contracts, clauses, risks, or dispute probability..."
                className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                rows="2"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || loading}
                className="px-6 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white rounded-xl transition-all flex items-center gap-2 font-semibold"
              >
                <Send className="w-5 h-5" />
                <span>Send</span>
              </button>
            </div>

            <p className="text-xs text-slate-500 mt-2">
              Press Enter to send • Shift+Enter for new line
            </p>
          </div>
        </div>

        {/* Info Banner */}
        <div className="mt-4 bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-gray-300">
              <p className="font-semibold text-purple-400 mb-1">AI-Powered Intelligence</p>
              <p>
                This assistant uses <strong>AI</strong> with <strong>RAG (Retrieval-Augmented Generation)</strong> to provide
                accurate answers based on your contract database. Responses are generated using semantic search
                across {' '}
                <span className="text-purple-400 font-semibold">Legal-BERT embeddings</span>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
