import React, { useState, useEffect, useRef } from 'react';
import api from '../utils/api';
import {
  MessageSquare, Send, Bot, User, CheckCircle, XCircle,
  AlertTriangle, TrendingDown, TrendingUp, Minus,
  ChevronRight, FileText, Plus, X, Zap, Shield, Scale,
  Activity, Clock, Target, Sparkles, Brain, BarChart2,
  ChevronDown, Wifi, WifiOff, Circle, ArrowRight, Hash
} from 'lucide-react';

const NegotiationMode = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [clauses, setClauses] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [contracts, setContracts] = useState([]);
  const messagesEndRef = useRef(null);

  const websocketRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [intent, setIntent] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [similarClauses, setSimilarClauses] = useState([]);

  const [newSession, setNewSession] = useState({
    contract_id: '',
    session_name: '',
    our_party_role: 'CLIENT',
    counterparty_name: '',
    objectives: [],
    risk_tolerance: 'MEDIUM'
  });

  useEffect(() => {
    fetchSessions();
    fetchContracts();
  }, []);

  useEffect(() => {
    if (currentSession) {
      fetchSessionDetails();
      fetchClauses();
      connectWebSocket();
    }
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
    };
  }, [currentSession]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessions = async () => {
    try {
      const response = await api.get('/copilot/sessions/');
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const fetchContracts = async () => {
    try {
      const response = await api.get('/contracts/list');
      setContracts(response.data.contracts || []);
    } catch (error) {
      console.error('Error fetching contracts:', error);
    }
  };

  const fetchSessionDetails = async () => {
    try {
      const response = await api.get(`/copilot/sessions/${currentSession.id}/`);
      setMessages(response.data.messages || []);
      setSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error('Error fetching session details:', error);
    }
  };

  const fetchClauses = async () => {
    try {
      const response = await api.get(`/copilot/sessions/${currentSession.id}/clauses/`);
      setClauses(response.data.clauses || []);
    } catch (error) {
      console.error('Error fetching clauses:', error);
    }
  };

  const createSession = async () => {
    if (!newSession.contract_id) return;
    try {
      setLoading(true);
      const response = await api.post('/copilot/sessions/', newSession);
      setShowNewSessionModal(false);
      fetchSessions();
      setCurrentSession(response.data.session);
      setNewSession({ contract_id: '', session_name: '', our_party_role: 'CLIENT', counterparty_name: '', objectives: [], risk_tolerance: 'MEDIUM' });
    } catch (error) {
      console.error('Error creating session:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    if (!currentSession) return;
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8002';
    const wsBase = apiBase.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsBase}/ws/negotiation/${currentSession.id}/`);
    ws.onopen = () => { setWsConnected(true); };
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'chat_response') {
        setMessages(prev => [...prev, data.user_message, data.ai_message]);
        setIntent(data.intent);
        setPrediction(data.prediction);
        setSimilarClauses(data.similar_clauses || []);
        setLoading(false);
      } else if (data.type === 'error') {
        setLoading(false);
      }
    };
    ws.onerror = () => setWsConnected(false);
    ws.onclose = () => setWsConnected(false);
    websocketRef.current = ws;
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !currentSession) return;
    if (websocketRef.current && wsConnected) {
      setLoading(true);
      websocketRef.current.send(JSON.stringify({ text: inputMessage, clause_id: null }));
      setInputMessage('');
    } else {
      sendMessageREST();
    }
  };

  const sendMessageREST = async () => {
    if (!inputMessage.trim() || !currentSession) return;
    try {
      setLoading(true);
      const response = await api.post(`/copilot/sessions/${currentSession.id}/messages/`, { content: inputMessage });
      setMessages([...messages, response.data.user_message, response.data.ai_message]);
      setInputMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskScore = (score) => {
    const pct = ((score || 0) * 100).toFixed(0);
    if (score >= 0.7) return { pct, color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'HIGH', glow: '0 0 12px rgba(239,68,68,0.4)' };
    if (score >= 0.4) return { pct, color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'MED', glow: '0 0 12px rgba(245,158,11,0.4)' };
    return { pct, color: '#10b981', bg: 'rgba(16,185,129,0.12)', label: 'LOW', glow: '0 0 12px rgba(16,185,129,0.4)' };
  };

  const getRiskIcon = (impact) => {
    if (impact === 'REDUCES_RISK') return <TrendingDown className="w-3.5 h-3.5" style={{ color: '#10b981' }} />;
    if (impact === 'INCREASES_RISK') return <TrendingUp className="w-3.5 h-3.5" style={{ color: '#ef4444' }} />;
    return <Minus className="w-3.5 h-3.5 text-gray-500" />;
  };

  const highRiskClauses = clauses.filter(c => (c.risk_score || 0) >= 0.7);

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #060d1f 0%, #0a1628 50%, #060d1f 100%)', fontFamily: "'Inter', sans-serif" }}>
      {/* Ambient glows */}
      <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none', zIndex: 0 }}>
        <div style={{ position: 'absolute', top: '-20%', left: '-10%', width: '600px', height: '600px', background: 'radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div style={{ position: 'absolute', bottom: '-20%', right: '-10%', width: '500px', height: '500px', background: 'radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 70%)', borderRadius: '50%' }} />
      </div>

      <div style={{ position: 'relative', zIndex: 1, padding: '28px 32px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '14px', background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 24px rgba(59,130,246,0.4)' }}>
              <Scale className="w-6 h-6 text-white" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#fff', margin: 0 }}>Live Clause Co-Pilot</h1>
                <span style={{ padding: '2px 10px', background: 'linear-gradient(90deg, rgba(59,130,246,0.3), rgba(139,92,246,0.3))', border: '1px solid rgba(139,92,246,0.4)', borderRadius: '20px', fontSize: '11px', fontWeight: 600, color: '#a78bfa', letterSpacing: '0.5px' }}>LIVE</span>
              </div>
              <p style={{ color: '#64748b', fontSize: '13px', margin: '2px 0 0' }}>Real-time AI-powered negotiation assistance</p>
            </div>
          </div>
          <button
            onClick={() => setShowNewSessionModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: 'linear-gradient(135deg, #3b82f6, #6366f1)', border: 'none', borderRadius: '10px', color: '#fff', fontWeight: 600, fontSize: '14px', cursor: 'pointer', boxShadow: '0 0 20px rgba(59,130,246,0.35)', transition: 'all 0.2s' }}
            onMouseEnter={e => e.currentTarget.style.boxShadow = '0 0 30px rgba(59,130,246,0.55)'}
            onMouseLeave={e => e.currentTarget.style.boxShadow = '0 0 20px rgba(59,130,246,0.35)'}
          >
            <Plus className="w-4 h-4" />
            New Session
          </button>
        </div>

        {/* Stats Bar */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '24px' }}>
          {[
            { icon: <MessageSquare className="w-4 h-4" />, label: 'Active Sessions', value: sessions.length, color: '#3b82f6' },
            { icon: <AlertTriangle className="w-4 h-4" />, label: 'High Risk Clauses', value: highRiskClauses.length, color: '#ef4444' },
            { icon: <Brain className="w-4 h-4" />, label: 'AI Suggestions', value: suggestions.length, color: '#8b5cf6' },
            { icon: <Activity className="w-4 h-4" />, label: 'Messages', value: messages.length, color: '#10b981' },
          ].map((stat, i) => (
            <div key={i} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '12px', backdropFilter: 'blur(10px)' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: `${stat.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: stat.color }}>
                {stat.icon}
              </div>
              <div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: '#fff', lineHeight: 1 }}>{stat.value}</div>
                <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{stat.label}</div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '20px' }}>
          {/* Sessions Sidebar */}
          <div>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '16px', padding: '18px', backdropFilter: 'blur(12px)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Hash className="w-4 h-4" style={{ color: '#64748b' }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', letterSpacing: '0.8px', textTransform: 'uppercase' }}>Sessions</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {sessions.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '24px 0' }}>
                    <MessageSquare className="w-8 h-8 mx-auto" style={{ color: '#1e3a5f', marginBottom: '8px' }} />
                    <p style={{ color: '#475569', fontSize: '12px' }}>No active sessions</p>
                  </div>
                ) : (
                  sessions.map((session) => {
                    const isActive = currentSession?.id === session.id;
                    return (
                      <div
                        key={session.id}
                        onClick={() => setCurrentSession(session)}
                        style={{
                          padding: '12px 14px', borderRadius: '10px', cursor: 'pointer', transition: 'all 0.2s',
                          background: isActive ? 'linear-gradient(135deg, rgba(59,130,246,0.25), rgba(99,102,241,0.2))' : 'rgba(255,255,255,0.03)',
                          border: isActive ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.05)',
                          boxShadow: isActive ? '0 0 16px rgba(59,130,246,0.15)' : 'none',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: isActive ? '#3b82f6' : '#334155', flexShrink: 0 }} />
                          <div style={{ fontSize: '13px', fontWeight: 600, color: isActive ? '#fff' : '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {session.session_name}
                          </div>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingLeft: '14px' }}>
                          <span style={{ fontSize: '11px', color: '#475569' }}>{session.message_count} messages</span>
                          {session.pending_suggestions > 0 && (
                            <span style={{ fontSize: '10px', padding: '1px 7px', background: 'rgba(245,158,11,0.2)', color: '#f59e0b', borderRadius: '10px', border: '1px solid rgba(245,158,11,0.3)' }}>
                              {session.pending_suggestions} tips
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div>
            {!currentSession ? (
              /* Empty state */
              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '16px', padding: '80px 40px', textAlign: 'center', backdropFilter: 'blur(12px)' }}>
                <div style={{ width: '80px', height: '80px', borderRadius: '24px', background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))', border: '1px solid rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
                  <Scale className="w-10 h-10" style={{ color: '#6366f1' }} />
                </div>
                <h3 style={{ fontSize: '22px', fontWeight: 700, color: '#fff', margin: '0 0 10px' }}>No Session Selected</h3>
                <p style={{ color: '#475569', fontSize: '14px', marginBottom: '28px', maxWidth: '400px', margin: '0 auto 28px' }}>
                  Select a session from the sidebar or create a new one to start your AI-powered negotiation
                </p>
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
                  {[
                    { icon: <Brain className="w-4 h-4" />, text: 'AI Clause Analysis', color: '#3b82f6' },
                    { icon: <Shield className="w-4 h-4" />, text: 'Risk Detection', color: '#8b5cf6' },
                    { icon: <Zap className="w-4 h-4" />, text: 'Live Suggestions', color: '#10b981' },
                  ].map((f, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', background: `${f.color}15`, border: `1px solid ${f.color}30`, borderRadius: '20px', color: f.color, fontSize: '12px', fontWeight: 500 }}>
                      {f.icon}{f.text}
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => setShowNewSessionModal(true)}
                  style={{ marginTop: '32px', display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 28px', background: 'linear-gradient(135deg, #3b82f6, #6366f1)', border: 'none', borderRadius: '10px', color: '#fff', fontWeight: 600, fontSize: '14px', cursor: 'pointer', boxShadow: '0 0 24px rgba(59,130,246,0.4)' }}
                >
                  <Plus className="w-4 h-4" />
                  Start Negotiating
                </button>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '16px' }}>
                {/* Chat Panel */}
                <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '16px', display: 'flex', flexDirection: 'column', height: '72vh', backdropFilter: 'blur(12px)', overflow: 'hidden' }}>
                  {/* Chat Header */}
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.2)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>{currentSession.session_name}</div>
                        <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>{currentSession.contract?.filename}</div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {intent && intent !== 'GENERAL' && (
                          <div style={{ padding: '4px 10px', background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                            <Target className="w-3 h-3" style={{ color: '#f59e0b' }} />
                            <span style={{ fontSize: '11px', color: '#f59e0b', fontWeight: 500 }}>{intent.replace(/_/g, ' ')}</span>
                          </div>
                        )}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 10px', background: wsConnected ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)', border: `1px solid ${wsConnected ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`, borderRadius: '20px' }}>
                          {wsConnected ? <Wifi className="w-3 h-3" style={{ color: '#10b981' }} /> : <WifiOff className="w-3 h-3" style={{ color: '#ef4444' }} />}
                          <span style={{ fontSize: '11px', fontWeight: 600, color: wsConnected ? '#10b981' : '#ef4444' }}>{wsConnected ? 'Live' : 'Offline'}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Messages */}
                  <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {messages.length === 0 && (
                      <div style={{ textAlign: 'center', padding: '40px 0', color: '#334155' }}>
                        <Sparkles className="w-8 h-8 mx-auto mb-3" style={{ color: '#1e3a5f' }} />
                        <p style={{ fontSize: '13px' }}>Start the conversation to get AI-powered clause analysis</p>
                      </div>
                    )}
                    {messages.map((msg, idx) => {
                      const isUser = msg.message_type === 'USER';
                      return (
                        <div key={idx} style={{ display: 'flex', gap: '10px', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
                          {!isUser && (
                            <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: 'linear-gradient(135deg, #3b82f6, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 0 12px rgba(59,130,246,0.3)' }}>
                              <Bot className="w-4 h-4 text-white" />
                            </div>
                          )}
                          <div style={{
                            maxWidth: '70%', padding: '12px 16px', borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                            background: isUser ? 'linear-gradient(135deg, #3b82f6, #6366f1)' : 'rgba(255,255,255,0.05)',
                            border: isUser ? 'none' : '1px solid rgba(255,255,255,0.07)',
                            boxShadow: isUser ? '0 0 16px rgba(59,130,246,0.25)' : 'none',
                          }}>
                            <div style={{ fontSize: '13px', color: isUser ? '#fff' : '#cbd5e1', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                            {msg.ai_confidence && (
                              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <div style={{ flex: 1, height: '2px', background: 'rgba(255,255,255,0.1)', borderRadius: '1px', overflow: 'hidden' }}>
                                  <div style={{ height: '100%', width: `${msg.ai_confidence * 100}%`, background: '#10b981', borderRadius: '1px' }} />
                                </div>
                                <span style={{ fontSize: '10px', color: '#10b981' }}>{(msg.ai_confidence * 100).toFixed(0)}%</span>
                              </div>
                            )}
                          </div>
                          {isUser && (
                            <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                              <User className="w-4 h-4 text-gray-300" />
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {loading && (
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: 'linear-gradient(135deg, #3b82f6, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                          <Bot className="w-4 h-4 text-white" />
                        </div>
                        <div style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '4px 16px 16px 16px', display: 'flex', gap: '5px', alignItems: 'center' }}>
                          {[0, 1, 2].map(i => (
                            <div key={i} style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3b82f6', animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
                          ))}
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <div style={{ padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.15)' }}>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                      <div style={{ flex: 1, display: 'flex', alignItems: 'center', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '10px 14px', gap: '8px' }}>
                        <Sparkles className="w-4 h-4 flex-shrink-0" style={{ color: '#6366f1' }} />
                        <input
                          type="text"
                          value={inputMessage}
                          onChange={(e) => setInputMessage(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                          placeholder="Ask about clauses, risks, or get suggestions..."
                          disabled={loading}
                          style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: '#fff', fontSize: '13px' }}
                        />
                      </div>
                      <button
                        onClick={sendMessage}
                        disabled={loading || !inputMessage.trim()}
                        style={{ width: '44px', height: '44px', borderRadius: '12px', background: inputMessage.trim() ? 'linear-gradient(135deg, #3b82f6, #6366f1)' : 'rgba(255,255,255,0.05)', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: inputMessage.trim() ? 'pointer' : 'not-allowed', flexShrink: 0, boxShadow: inputMessage.trim() ? '0 0 16px rgba(59,130,246,0.4)' : 'none', transition: 'all 0.2s' }}
                      >
                        <Send className="w-4 h-4" style={{ color: inputMessage.trim() ? '#fff' : '#334155' }} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Right Panel */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto', maxHeight: '72vh' }}>
                  {/* Session Stats */}
                  <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '14px', padding: '16px', backdropFilter: 'blur(12px)' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', letterSpacing: '0.8px', textTransform: 'uppercase', marginBottom: '12px' }}>Session Stats</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {[
                        { label: 'Total Clauses', value: clauses.length, color: '#3b82f6' },
                        { label: 'High Risk', value: highRiskClauses.length, color: '#ef4444' },
                        { label: 'Messages', value: messages.length, color: '#10b981' },
                        { label: 'Suggestions', value: suggestions.length, color: '#8b5cf6' },
                      ].map((s, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '12px', color: '#64748b' }}>{s.label}</span>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: s.color }}>{s.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* High Risk Clauses */}
                  <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '14px', padding: '16px', backdropFilter: 'blur(12px)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                      <AlertTriangle className="w-3.5 h-3.5" style={{ color: '#ef4444' }} />
                      <span style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', letterSpacing: '0.8px', textTransform: 'uppercase' }}>High Risk Clauses</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {highRiskClauses.slice(0, 4).map((clause) => {
                        const r = getRiskScore(clause.risk_score);
                        return (
                          <div key={clause.id} style={{ padding: '10px 12px', background: r.bg, border: `1px solid ${r.color}30`, borderRadius: '10px' }}>
                            <div style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginBottom: '4px' }}>{clause.clause_name}</div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <div style={{ flex: 1, height: '3px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${r.pct}%`, background: r.color, borderRadius: '2px', boxShadow: r.glow }} />
                              </div>
                              <span style={{ fontSize: '11px', fontWeight: 700, color: r.color }}>{r.pct}%</span>
                            </div>
                          </div>
                        );
                      })}
                      {highRiskClauses.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '16px 0' }}>
                          <CheckCircle className="w-6 h-6 mx-auto mb-2" style={{ color: '#10b981' }} />
                          <p style={{ fontSize: '11px', color: '#475569' }}>No high-risk clauses</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Similar Clauses RAG */}
                  {similarClauses.length > 0 && (
                    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: '14px', padding: '16px', backdropFilter: 'blur(12px)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                        <Brain className="w-3.5 h-3.5" style={{ color: '#8b5cf6' }} />
                        <span style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', letterSpacing: '0.8px', textTransform: 'uppercase' }}>Similar Clauses (RAG)</span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {similarClauses.slice(0, 3).map((clause, idx) => (
                          <div key={idx} style={{ padding: '10px 12px', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.15)', borderRadius: '10px' }}>
                            <div style={{ fontSize: '12px', fontWeight: 600, color: '#c4b5fd', marginBottom: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{clause.name}</div>
                            <div style={{ fontSize: '11px', color: '#64748b' }}>Score: {clause.score?.toFixed(2)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AI Suggestions */}
                  <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '14px', padding: '16px', backdropFilter: 'blur(12px)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                      <Sparkles className="w-3.5 h-3.5" style={{ color: '#f59e0b' }} />
                      <span style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', letterSpacing: '0.8px', textTransform: 'uppercase' }}>AI Suggestions</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {suggestions.slice(0, 4).map((suggestion) => (
                        <div key={suggestion.id} style={{ padding: '10px 12px', background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.15)', borderRadius: '10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
                            {getRiskIcon(suggestion.risk_impact)}
                            <span style={{ fontSize: '12px', fontWeight: 600, color: '#fcd34d', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>{suggestion.clause_name}</span>
                          </div>
                          <div style={{ fontSize: '11px', color: '#64748b' }}>{suggestion.suggestion_type}</div>
                        </div>
                      ))}
                      {suggestions.length === 0 && (
                        <p style={{ fontSize: '11px', color: '#475569', textAlign: 'center', padding: '8px 0' }}>No pending suggestions</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Session Modal */}
      {showNewSessionModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div style={{ background: 'linear-gradient(135deg, #0f1e3d, #0a1628)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '20px', padding: '28px', width: '100%', maxWidth: '460px', boxShadow: '0 0 60px rgba(59,130,246,0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, #3b82f6, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Plus className="w-5 h-5 text-white" />
                </div>
                <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#fff', margin: 0 }}>New Negotiation Session</h3>
              </div>
              <button onClick={() => setShowNewSessionModal(false)} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '6px', cursor: 'pointer', color: '#64748b' }}>
                <X className="w-4 h-4" />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {[
                { label: 'Contract', type: 'select', key: 'contract_id', options: [{ value: '', label: 'Select a contract' }, ...contracts.map(c => ({ value: c.id, label: c.originalFilename }))] },
                { label: 'Session Name', type: 'text', key: 'session_name', placeholder: 'e.g., Q1 2026 Vendor Agreement' },
                { label: 'Our Role', type: 'select', key: 'our_party_role', options: [{ value: 'CLIENT', label: 'Client' }, { value: 'BUYER', label: 'Buyer' }, { value: 'SELLER', label: 'Seller' }, { value: 'SERVICE_PROVIDER', label: 'Service Provider' }, { value: 'OTHER', label: 'Other' }] },
                { label: 'Counterparty Name', type: 'text', key: 'counterparty_name', placeholder: 'e.g., Acme Corp' },
                { label: 'Risk Tolerance', type: 'select', key: 'risk_tolerance', options: [{ value: 'LOW', label: 'Low (Conservative)' }, { value: 'MEDIUM', label: 'Medium (Balanced)' }, { value: 'HIGH', label: 'High (Aggressive)' }] },
              ].map((field) => (
                <div key={field.key}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '7px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{field.label}</label>
                  {field.type === 'select' ? (
                    <select
                      value={newSession[field.key]}
                      onChange={(e) => setNewSession({ ...newSession, [field.key]: e.target.value })}
                      style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', color: '#fff', fontSize: '13px', outline: 'none', cursor: 'pointer' }}
                    >
                      {field.options.map(opt => <option key={opt.value} value={opt.value} style={{ background: '#0f1e3d' }}>{opt.label}</option>)}
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={newSession[field.key]}
                      onChange={(e) => setNewSession({ ...newSession, [field.key]: e.target.value })}
                      placeholder={field.placeholder}
                      style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', color: '#fff', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }}
                    />
                  )}
                </div>
              ))}

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button onClick={() => setShowNewSessionModal(false)} style={{ flex: 1, padding: '11px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', color: '#94a3b8', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}>
                  Cancel
                </button>
                <button
                  onClick={createSession}
                  disabled={loading || !newSession.contract_id}
                  style={{ flex: 1, padding: '11px', background: newSession.contract_id ? 'linear-gradient(135deg, #3b82f6, #6366f1)' : 'rgba(255,255,255,0.05)', border: 'none', borderRadius: '10px', color: newSession.contract_id ? '#fff' : '#475569', fontSize: '13px', fontWeight: 600, cursor: newSession.contract_id ? 'pointer' : 'not-allowed', boxShadow: newSession.contract_id ? '0 0 16px rgba(59,130,246,0.35)' : 'none' }}
                >
                  {loading ? 'Creating...' : 'Start Session'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
        * { scrollbar-width: thin; scrollbar-color: rgba(59,130,246,0.3) transparent; }
        *::-webkit-scrollbar { width: 4px; }
        *::-webkit-scrollbar-track { background: transparent; }
        *::-webkit-scrollbar-thumb { background: rgba(59,130,246,0.3); border-radius: 2px; }
      `}</style>
    </div>
  );
};

export default NegotiationMode;
