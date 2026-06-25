import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Loader, FileText, Shield, AlertTriangle, CheckCircle, Sparkles, BookOpen, FileSearch, Plus, Square, Search, X, Clock, ChevronDown, ChevronRight, Bot, User, Mic } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import Sidebar from '../components/Sidebar';
import VoiceInput from '../components/VoiceInput';
import ExportChat from '../components/ExportChat';
import EnhancedMessage from '../components/EnhancedMessage';

// Typing indicator component
const TypingIndicator = () => (
  <div className="flex items-center gap-1 px-3 py-2">
    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
  </div>
);

export default function UnifiedChat() {
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [chatHistorySidebarOpen, setChatHistorySidebarOpen] = useState(true);
  const [mainSidebarOpen, setMainSidebarOpen] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const abortControllerRef = useRef(null);

  useEffect(() => {
    const saved = localStorage.getItem('contractAI_chatSessions');
    if (saved) {
      const sessions = JSON.parse(saved);
      setChatSessions(sessions);
      if (sessions.length > 0) {
        const mostRecent = sessions[0];
        setCurrentSessionId(mostRecent.id);
        setMessages(mostRecent.messages || []);
      }
    }
  }, []);

  useEffect(() => {
    if (chatSessions.length > 0) {
      localStorage.setItem('contractAI_chatSessions', JSON.stringify(chatSessions));
    }
  }, [chatSessions]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const createNewChat = () => {
    const newSession = {
      id: Date.now().toString(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    setChatSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    setMessages([]);
    setQuery('');
    inputRef.current?.focus();
  };

  const loadChatSession = (sessionId) => {
    const session = chatSessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      setMessages(session.messages || []);
    }
  };

  const updateCurrentSession = (newMessages) => {
    if (!currentSessionId) return;
    setChatSessions(prev => prev.map(session => {
      if (session.id === currentSessionId) {
        const title = newMessages.length > 0 && newMessages[0].type === 'user'
          ? newMessages[0].content.slice(0, 50) + (newMessages[0].content.length > 50 ? '...' : '')
          : 'New Conversation';
        return {
          ...session,
          messages: newMessages,
          title: session.title === 'New Conversation' ? title : session.title,
          updatedAt: new Date().toISOString()
        };
      }
      return session;
    }));
  };

  const deleteSession = (sessionId) => {
    setChatSessions(prev => prev.filter(s => s.id !== sessionId));
    if (sessionId === currentSessionId) {
      const remaining = chatSessions.filter(s => s.id !== sessionId);
      if (remaining.length > 0) {
        loadChatSession(remaining[0].id);
      } else {
        createNewChat();
      }
    }
  };

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
    }
  };

  const toggleSources = (index) => {
    setExpandedSources(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    if (!currentSessionId) {
      createNewChat();
    }

    const userMessage = query.trim();
    setQuery('');

    const newMessages = [...messages, { type: 'user', content: userMessage }];
    setMessages(newMessages);
    updateCurrentSession(newMessages);
    setLoading(true);

    abortControllerRef.current = new AbortController();

    try {
      const response = await api.post('/rag/chat',
        { query: userMessage },
        { signal: abortControllerRef.current.signal }
      );

      const updatedMessages = [
        ...newMessages,
        {
          type: 'ai',
          content: response.data.answer,
          sources: response.data.sources || [],
          sourceCount: response.data.source_count || 0,
          contracts: response.data.contracts || [],
          contractCount: response.data.contract_count || 0,
          searchType: response.data.search_type,
          filtersApplied: response.data.filters_applied,
          intent: response.data.intent,
          hasContractContext: response.data.has_contract_context
        }
      ];

      setMessages(updatedMessages);
      updateCurrentSession(updatedMessages);
    } catch (error) {
      if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
        return;
      }

      const errorData = error.response?.data;
      let errorMessage = error.response?.data?.error || error.message || 'Failed to get response';
      if (errorData?.details) {
        errorMessage += `\n\n${errorData.details}`;
      }

      const updatedMessages = [
        ...newMessages,
        { type: 'error', content: errorMessage }
      ];

      setMessages(updatedMessages);
      updateCurrentSession(updatedMessages);
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const filteredSessions = chatSessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const groupedSessions = { today: [], pastWeek: [], older: [] };
  const now = new Date();
  const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  filteredSessions.forEach(session => {
    const sessionDate = new Date(session.updatedAt);
    if (sessionDate > oneDayAgo) {
      groupedSessions.today.push(session);
    } else if (sessionDate > oneWeekAgo) {
      groupedSessions.pastWeek.push(session);
    } else {
      groupedSessions.older.push(session);
    }
  });

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const suggestedPrompts = [
    { text: 'Show me high risk contracts', icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
    { text: 'What are the termination clauses?', icon: FileSearch, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20' },
    { text: 'Find employment contracts', icon: FileText, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' },
    { text: 'Explain force majeure clauses', icon: BookOpen, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      <Sidebar isOpen={mainSidebarOpen} setIsOpen={setMainSidebarOpen} />

      {/* Enhanced Chat History Sidebar */}
      {chatHistorySidebarOpen && (
        <div className="w-72 bg-gradient-to-b from-slate-900 to-slate-950 border-r border-slate-800 flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-slate-800/50">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto py-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
            {groupedSessions.today.length > 0 && (
              <div className="px-3 py-2">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-2">Today</h3>
                {groupedSessions.today.map(session => (
                  <button
                    key={session.id}
                    onClick={() => loadChatSession(session.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl mb-1 group transition-all duration-200 ${
                      session.id === currentSessionId
                        ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                        : 'hover:bg-slate-800/50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <span className={`text-sm font-medium truncate block ${session.id === currentSessionId ? 'text-blue-300' : 'text-slate-300'}`}>
                          {session.title}
                        </span>
                        <span className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                          <Clock className="w-3 h-3" />
                          {formatTime(session.updatedAt)}
                        </span>
                      </div>
                      <div
                        onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded-lg cursor-pointer transition-all"
                      >
                        <X className="w-3 h-3 text-slate-400 hover:text-red-400" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {groupedSessions.pastWeek.length > 0 && (
              <div className="px-3 py-2">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-2">Past Week</h3>
                {groupedSessions.pastWeek.map(session => (
                  <button
                    key={session.id}
                    onClick={() => loadChatSession(session.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl mb-1 group transition-all duration-200 ${
                      session.id === currentSessionId
                        ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30'
                        : 'hover:bg-slate-800/50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <span className={`text-sm font-medium truncate block ${session.id === currentSessionId ? 'text-blue-300' : 'text-slate-300'}`}>
                          {session.title}
                        </span>
                      </div>
                      <div
                        onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded-lg cursor-pointer transition-all"
                      >
                        <X className="w-3 h-3 text-slate-400 hover:text-red-400" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {groupedSessions.older.length > 0 && (
              <div className="px-3 py-2">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-2">Older</h3>
                {groupedSessions.older.map(session => (
                  <button
                    key={session.id}
                    onClick={() => loadChatSession(session.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl mb-1 group transition-all duration-200 ${
                      session.id === currentSessionId
                        ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30'
                        : 'hover:bg-slate-800/50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <span className={`text-sm font-medium truncate block ${session.id === currentSessionId ? 'text-blue-300' : 'text-slate-300'}`}>
                          {session.title}
                        </span>
                      </div>
                      <div
                        onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 rounded-lg cursor-pointer transition-all"
                      >
                        <X className="w-3 h-3 text-slate-400 hover:text-red-400" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {filteredSessions.length === 0 && (
              <div className="px-4 py-12 text-center">
                <MessageCircle className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">No conversations yet</p>
                <p className="text-slate-600 text-xs mt-1">Start a new chat to begin</p>
              </div>
            )}
          </div>

          {/* New Chat Button */}
          <div className="p-3 border-t border-slate-800/50">
            <button
              onClick={createNewChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white rounded-xl font-medium text-sm transition-all duration-200 shadow-lg shadow-blue-500/20"
            >
              <Plus className="w-4 h-4" />
              New Conversation
            </button>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Enhanced Header */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-slate-700/50 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-blue-500 rounded-xl blur-lg opacity-30 animate-pulse" />
              <div className="relative bg-gradient-to-br from-blue-500 to-blue-600 p-2.5 rounded-xl shadow-lg">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white flex items-center gap-2">
                Contract AI Chat
                <span className="px-2 py-0.5 bg-gradient-to-r from-emerald-500/20 to-emerald-600/20 text-emerald-400 text-[10px] font-semibold rounded-full border border-emerald-500/30">
                  BETA
                </span>
              </h1>
              <p className="text-slate-400 text-xs">Ask anything about your contracts</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <ExportChat
                messages={messages}
                conversationTitle={chatSessions.find(s => s.id === currentSessionId)?.title || 'Chat'}
                className="px-3 py-2 text-xs bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-600/30 rounded-lg transition-all"
              />
            )}
            <button
              onClick={createNewChat}
              className="p-2 hover:bg-slate-700/50 rounded-lg transition-all border border-transparent hover:border-slate-600"
              title="New chat"
            >
              <Plus className="w-5 h-5 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto bg-gradient-to-b from-slate-900 to-slate-950 px-6 py-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          {messages.length === 0 ? (
            /* Enhanced Empty State */
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="relative mb-6">
                <div className="absolute inset-0 bg-blue-500 rounded-full blur-2xl opacity-20 animate-pulse" />
                <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-2xl border border-slate-700/50">
                  <Bot className="w-12 h-12 text-blue-400" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">How can I help you today?</h2>
              <p className="text-slate-400 max-w-md text-sm mb-8">
                Ask me anything about your contracts - from specific clauses to general legal questions.
              </p>

              <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                {suggestedPrompts.map((prompt, idx) => {
                  const Icon = prompt.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => setQuery(prompt.text)}
                      className={`flex items-center gap-3 px-4 py-3 ${prompt.bg} border rounded-xl text-left hover:scale-[1.02] transition-all duration-200 group`}
                    >
                      <Icon className={`w-5 h-5 ${prompt.color} flex-shrink-0`} />
                      <span className="text-sm text-slate-300 group-hover:text-white transition-colors">{prompt.text}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Messages */
            messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {msg.type === 'user' ? (
                  /* User Message */
                  <div className="flex items-start gap-3 max-w-2xl">
                    <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white px-4 py-3 rounded-2xl rounded-tr-md shadow-lg">
                      <p className="text-sm">{msg.content}</p>
                    </div>
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  </div>
                ) : msg.type === 'error' ? (
                  /* Error Message */
                  <div className="flex items-start gap-3 max-w-2xl">
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center shadow-lg">
                      <AlertTriangle className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-red-900/20 border border-red-800/50 text-red-200 px-4 py-3 rounded-2xl rounded-tl-md">
                      <p className="text-sm">{msg.content}</p>
                    </div>
                  </div>
                ) : (msg.type === 'assistant') && !msg.contracts ? (
                  <EnhancedMessage message={msg} />
                ) : (
                  /* AI Message */
                  <div className="flex items-start gap-3 max-w-3xl">
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-slate-800/80 border border-slate-700/50 backdrop-blur-sm px-4 py-3 rounded-2xl rounded-tl-md shadow-lg">
                      {/* Intent Badge */}
                      {msg.intent && (
                        <div className="mb-3 flex items-center gap-2">
                          {msg.intent === 'general' && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                              <Sparkles className="w-3 h-3 mr-1.5" />
                              General Knowledge
                            </span>
                          )}
                          {msg.intent === 'contract' && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-green-500/20 text-green-300 border border-green-500/30">
                              <FileSearch className="w-3 h-3 mr-1.5" />
                              From Your Contracts
                            </span>
                          )}
                          {msg.intent === 'hybrid' && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30">
                              <BookOpen className="w-3 h-3 mr-1.5" />
                              Contracts + Knowledge
                            </span>
                          )}
                          {msg.intent === 'no_contracts' && (
                            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-orange-500/20 text-orange-300 border border-orange-500/30">
                              <AlertTriangle className="w-3 h-3 mr-1.5" />
                              No Contracts Uploaded
                            </span>
                          )}
                        </div>
                      )}

                      <div className="prose prose-invert max-w-none prose-sm">
                        <p className="text-slate-200 whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                      </div>

                      {/* Contract Results */}
                      {msg.contracts && msg.contracts.length > 0 && msg.searchType === 'metadata_search' && (
                        <div className="mt-4 space-y-2">
                          {msg.contracts.map((contract) => (
                            <div
                              key={contract.id}
                              className="bg-slate-900/70 border border-slate-700/50 rounded-xl p-3 hover:bg-slate-900 hover:border-slate-600 transition-all cursor-pointer group"
                              onClick={() => navigate(`/contract/${contract.id}`)}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <FileText className="w-4 h-4 text-blue-400" />
                                  <span className="text-sm font-medium text-white truncate">{contract.filename}</span>
                                </div>
                                {contract.risk_level && (
                                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold ${
                                    contract.risk_level === 'LOW' ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                                    contract.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                                    'bg-red-500/20 text-red-400 border border-red-500/30'
                                  }`}>
                                    {contract.risk_level}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-400 mt-1">{contract.contract_type}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Sources Accordion */}
                      {msg.sources && msg.sources.length > 0 && (msg.searchType === 'semantic_rag' || msg.searchType === 'simple_rag') && (
                        <div className="mt-4 pt-3 border-t border-slate-700/50">
                          <button
                            onClick={() => toggleSources(index)}
                            className="flex items-center justify-between w-full text-left"
                          >
                            <span className="text-xs font-semibold text-slate-400">
                              Sources ({msg.sourceCount})
                            </span>
                            {expandedSources[index] ? (
                              <ChevronDown className="w-4 h-4 text-slate-400" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-slate-400" />
                            )}
                          </button>

                          {expandedSources[index] && (
                            <div className="mt-2 space-y-2 animate-fade-in">
                              {msg.sources.map((source, idx) => (
                                <div key={idx} className="bg-slate-900/50 rounded-lg p-2.5 border border-slate-700/30 hover:border-slate-600/50 transition-all">
                                  <div className="flex items-start gap-2">
                                    <FileText className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                                    <div className="flex-1 min-w-0">
                                      <p className="text-xs font-medium text-blue-400 truncate">{source.filename}</p>
                                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">{source.text}</p>
                                    </div>
                                    {source.contract_id && (
                                      <button
                                        onClick={(e) => { e.stopPropagation(); navigate(`/contract/${source.contract_id}`); }}
                                        className="text-[10px] px-2 py-1 bg-blue-500/20 text-blue-400 rounded-md hover:bg-blue-500/30 transition-all"
                                      >
                                        View
                                      </button>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Related Contracts */}
                          {msg.contracts && msg.contracts.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-slate-700/50">
                              <p className="text-xs font-semibold text-slate-400 mb-2">Related Contracts</p>
                              <div className="flex flex-wrap gap-2">
                                {msg.contracts.map((contract, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => navigate(`/contract/${contract.id}`)}
                                    className="bg-slate-900/50 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 flex items-center gap-1.5 transition-all"
                                  >
                                    <FileText className="w-3 h-3 text-slate-400" />
                                    <span className="truncate max-w-[120px]">{contract.filename}</span>
                                    {contract.risk_level && (
                                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                                        contract.risk_level === 'LOW' ? 'bg-green-500/20 text-green-400' :
                                        contract.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-red-500/20 text-red-400'
                                      }`}>
                                        {contract.risk_level}
                                      </span>
                                    )}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex justify-start animate-fade-in">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-slate-800/80 border border-slate-700/50 backdrop-blur-sm rounded-2xl rounded-tl-md shadow-lg">
                  <TypingIndicator />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Enhanced Input Area */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-t border-slate-700/50 px-6 py-4">
          <form onSubmit={handleAsk} className="relative">
            <div className="flex items-center gap-3">
              <div className="flex-1 relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-emerald-500 rounded-xl opacity-0 group-focus-within:opacity-30 blur transition-all duration-300" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about your contracts..."
                  disabled={loading}
                  className="relative w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 disabled:opacity-50 transition-all"
                />
              </div>
              <VoiceInput
                onTranscript={(text) => setQuery(text)}
                className="p-3 bg-slate-800 hover:bg-slate-700 border border-slate-700/50 rounded-xl transition-all"
              />
              {loading ? (
                <button
                  type="button"
                  onClick={stopGeneration}
                  className="flex items-center gap-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white px-5 py-3 rounded-xl font-medium transition-all shadow-lg shadow-red-500/20"
                >
                  <Square className="w-4 h-4" />
                  <span>Stop</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!query.trim()}
                  className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white px-5 py-3 rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20 disabled:shadow-none"
                >
                  <Send className="w-4 h-4" />
                  <span>Send</span>
                </button>
              )}
            </div>
          </form>
        </div>
      </div>

      {/* Animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out forwards;
        }
        .scrollbar-thin::-webkit-scrollbar {
          width: 6px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: transparent;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: rgba(71, 85, 105, 0.5);
          border-radius: 3px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: rgba(71, 85, 105, 0.8);
        }
      `}</style>
    </div>
  );
}
