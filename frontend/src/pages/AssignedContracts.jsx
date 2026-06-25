import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCheck, FileText, Search, ArrowLeft, Eye, Calendar, AlertTriangle, Activity, Zap, Radio } from 'lucide-react';
import api from '../utils/api';
import useAuthStore from '../store/authStore';

export default function AssignedContracts() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [mounted, setMounted] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  const [idleMessageIndex, setIdleMessageIndex] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const containerRef = useRef(null);

  const idleMessages = [
    "Awaiting assignments…",
    "AI monitoring incoming contracts",
    "No active tasks detected",
    "System ready for deployment",
    "Standing by for contract intelligence"
  ];

  useEffect(() => {
    setMounted(true);
    fetchAssignedContracts();

    // Cycle idle messages
    const messageInterval = setInterval(() => {
      setIdleMessageIndex((prev) => (prev + 1) % idleMessages.length);
    }, 4000);

    // Track mouse for empty state parallax
    const handleMouseMove = (e) => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setMousePosition({
          x: (e.clientX - rect.left - rect.width / 2) / 50,
          y: (e.clientY - rect.top - rect.height / 2) / 50
        });
      }
    };

    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      clearInterval(messageInterval);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  const fetchAssignedContracts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/contracts/list');
      // Filter to only show contracts that were assigned (not uploaded by user)
      const assigned = (response.data.contracts || []).filter(c => c.assigned_by || c.assignedBy);
      setContracts(assigned);
    } catch (err) {
      console.error('Failed to fetch contracts:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredContracts = contracts.filter((contract) =>
    contract.original_filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.contract_type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (contract) => {
    const status = contract.status || 'DRAFT';
    const statusConfig = {
      'DRAFT': { label: 'Draft', color: 'bg-slate-600 text-slate-200' },
      'REVIEW': { label: 'Review', color: 'bg-blue-600 text-blue-100' },
      'NEGOTIATION': { label: 'Negotiation', color: 'bg-yellow-600 text-yellow-100' },
      'FINAL': { label: 'Final', color: 'bg-green-600 text-green-100' }
    };
    const config = statusConfig[status] || statusConfig['DRAFT'];
    return (
      <span className={`px-3 py-1 ${config.color} text-xs font-medium rounded-full`}>
        {config.label}
      </span>
    );
  };

  const getRiskBadge = (contract) => {
    if (!contract.hasRiskAnalysis) return null;

    const riskLevel = contract.risk_level || 'LOW';
    const riskConfig = {
      'CRITICAL': { color: 'bg-red-600', text: 'Critical' },
      'HIGH': { color: 'bg-orange-600', text: 'High' },
      'MEDIUM': { color: 'bg-yellow-600', text: 'Medium' },
      'LOW': { color: 'bg-green-600', text: 'Low' }
    };
    const config = riskConfig[riskLevel] || riskConfig['LOW'];

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 ${config.color} text-white text-xs font-medium rounded-full`}>
        <AlertTriangle size={12} />
        {config.text} Risk
      </span>
    );
  };

  return (
    <div
      ref={containerRef}
      className="relative min-h-screen"
      style={{
        background: 'linear-gradient(180deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%)',
      }}
    >
      {/* Animated neural background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {/* Moving light bands */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent animate-light-sweep"></div>
        <div className="absolute top-1/3 right-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-500/20 to-transparent animate-light-sweep-slow"></div>
        <div className="absolute top-2/3 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-violet-500/15 to-transparent animate-light-sweep-slower"></div>

        {/* Neural grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#06b6d408_1px,transparent_1px),linear-gradient(to_bottom,#06b6d408_1px,transparent_1px)] bg-[size:60px_60px] opacity-20"></div>

        {/* Ambient glows */}
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-violet-500/5 rounded-full blur-3xl animate-pulse-slower"></div>

        {/* AI heartbeat particles */}
        <div className="absolute top-40 left-10 w-1 h-1 bg-cyan-400 rounded-full animate-ping"></div>
        <div className="absolute top-60 right-20 w-1 h-1 bg-blue-400 rounded-full animate-ping" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-40 left-1/3 w-1 h-1 bg-violet-400 rounded-full animate-ping" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="relative space-y-6 px-4 py-6 max-w-7xl mx-auto">
        {/* Back Button - rewinding context */}
        <button
          onClick={() => navigate(-1)}
          className="group flex items-center gap-2 text-slate-500 hover:text-cyan-400 transition-all duration-500"
          style={{
            opacity: mounted ? 1 : 0,
            transform: mounted ? 'translateX(0)' : 'translateX(-20px)',
            transition: 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
          }}
        >
          <ArrowLeft size={20} className="transition-transform duration-500 group-hover:-translate-x-1" />
          <span className="font-semibold">Return to Command</span>
        </button>

        {/* Header - slides down */}
        <div
          className="flex flex-col md:flex-row md:items-center md:justify-between gap-6"
          style={{
            opacity: mounted ? 1 : 0,
            transform: mounted ? 'translateY(0)' : 'translateY(-30px)',
            transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s',
          }}
        >
          <div className="flex items-center gap-4">
            {/* Animated AI avatar */}
            <div className="relative group">
              <div className="absolute -inset-3 bg-gradient-to-br from-cyan-500/30 via-blue-500/20 to-violet-500/30 rounded-2xl blur-xl opacity-60 group-hover:opacity-100 transition-all duration-700 animate-pulse-slow"></div>
              <div className="relative h-16 w-16 rounded-2xl bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 flex items-center justify-center border border-cyan-500/30 shadow-[inset_0_1px_2px_rgba(6,182,212,0.4),0_0_30px_rgba(6,182,212,0.2)]">
                <div className="absolute inset-0 rounded-2xl border border-cyan-400/40 animate-spin-slow"></div>
                <div className="absolute inset-2 bg-gradient-to-br from-cyan-500/30 to-blue-500/30 rounded-xl blur-md"></div>
                <UserCheck className="relative w-8 h-8 text-cyan-400" style={{
                  filter: 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))',
                }} />
                <div className="absolute -top-1 -right-1">
                  <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_12px_rgba(6,182,212,1)]"></div>
                </div>
              </div>
            </div>

            <div>
              <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-100 to-blue-200">
                Assignment Inbox
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
                <p className="text-xs text-cyan-400/90 font-bold tracking-widest uppercase">
                  Operator: {user?.firstName || user?.username || 'Active'}
                </p>
              </div>
            </div>
          </div>

          {/* Stats - hover with light sweep */}
          <div className="flex gap-4">
            <div
              className="relative group bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-slate-950/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl px-6 py-4 overflow-hidden transition-all duration-500 hover:border-cyan-500/40 hover:shadow-[0_0_30px_rgba(6,182,212,0.2)]"
              style={{
                opacity: mounted ? 1 : 0,
                transform: mounted ? 'translateY(0)' : 'translateY(20px)',
                transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) 0.3s',
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
              <div className="relative">
                <div className="text-3xl font-black text-white tabular-nums">
                  {contracts.length}
                </div>
                <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">Total Assigned</div>
              </div>
            </div>

            <div
              className="relative group bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-slate-950/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl px-6 py-4 overflow-hidden transition-all duration-500 hover:border-cyan-500/40 hover:shadow-[0_0_30px_rgba(6,182,212,0.2)]"
              style={{
                opacity: mounted ? 1 : 0,
                transform: mounted ? 'translateY(0)' : 'translateY(20px)',
                transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) 0.4s',
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
              <div className="relative">
                <div className="text-3xl font-black text-cyan-400 tabular-nums" style={{
                  textShadow: '0 0 20px rgba(6, 182, 212, 0.4)',
                }}>
                  {contracts.filter(c => c.has_analysis).length}
                </div>
                <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">AI Analyzed</div>
              </div>
            </div>
          </div>
        </div>

        {/* Search Bar - powers on with glow scan */}
        <div
          className="relative"
          style={{
            opacity: mounted ? 1 : 0,
            transform: mounted ? 'scale(1)' : 'scale(0.95)',
            transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) 0.5s',
          }}
        >
          {/* Glow scan on focus */}
          {searchFocused && (
            <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500/20 via-blue-500/20 to-violet-500/20 rounded-2xl blur-xl animate-pulse-slow"></div>
          )}

          <div className={`relative transition-all duration-500 ${searchFocused ? 'scale-[1.02]' : 'scale-100'}`}>
            {/* Breathing glow when idle */}
            {!searchFocused && (
              <div className="absolute -inset-[1px] bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-violet-500/10 rounded-2xl animate-breathing"></div>
            )}

            <div className="relative">
              <Search
                className={`absolute left-5 top-1/2 transform -translate-y-1/2 w-5 h-5 transition-all duration-500 ${
                  searchFocused ? 'text-cyan-400 scale-110' : 'text-slate-500'
                }`}
                style={{
                  filter: searchFocused ? 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))' : 'none',
                }}
              />
              <input
                type="text"
                placeholder="Search intelligence objects..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
                className={`w-full bg-gradient-to-br from-slate-900/90 via-slate-900/70 to-slate-950/90 backdrop-blur-md border rounded-2xl pl-14 pr-6 py-5 text-white placeholder-slate-500 focus:outline-none transition-all duration-500 ${
                  searchFocused
                    ? 'border-cyan-500/50 shadow-[0_0_40px_rgba(6,182,212,0.3),inset_0_1px_0_rgba(255,255,255,0.1)]'
                    : 'border-cyan-500/20 shadow-[0_0_20px_rgba(6,182,212,0.1)]'
                }`}
              />

              {/* AI monitoring indicator */}
              {searchTerm && (
                <div className="absolute right-5 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
                  <span className="text-xs text-cyan-400 font-bold">SCANNING</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Contracts List / Empty State */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32">
            <div className="relative">
              <div className="absolute inset-0 animate-ping">
                <div className="w-16 h-16 border-4 border-cyan-400/30 rounded-full"></div>
              </div>
              <div className="relative w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
            <p className="mt-6 text-sm text-cyan-400 font-bold uppercase tracking-wider">Initializing AI workspace...</p>
          </div>
        ) : filteredContracts.length === 0 ? (
          // CINEMATIC EMPTY STATE - AI IDLE MODE
          <div
            className="relative min-h-[600px] flex items-center justify-center"
            style={{
              opacity: mounted ? 1 : 0,
              transition: 'opacity 1s ease-out 0.8s',
            }}
          >
            {/* Central AI avatar with parallax */}
            <div
              className="relative"
              style={{
                transform: `translate(${mousePosition.x}px, ${mousePosition.y}px)`,
                transition: 'transform 0.3s ease-out',
              }}
            >
              {/* Outer orbital rings */}
              <div className="absolute -inset-32">
                <div className="absolute inset-0 border border-cyan-500/10 rounded-full animate-spin-slow"></div>
                <div className="absolute inset-8 border border-blue-500/10 rounded-full animate-spin-slower" style={{ animationDirection: 'reverse' }}></div>
                <div className="absolute inset-16 border border-violet-500/10 rounded-full animate-spin-slowest"></div>
              </div>

              {/* Energy pulses */}
              <div className="absolute -inset-20 bg-gradient-to-br from-cyan-500/5 via-blue-500/5 to-violet-500/5 rounded-full blur-3xl animate-pulse-slow"></div>

              {/* Central neural glyph */}
              <div className="relative w-32 h-32 rounded-full bg-gradient-to-br from-slate-900/80 via-slate-950/90 to-black/80 backdrop-blur-xl border border-cyan-500/30 shadow-[inset_0_2px_4px_rgba(6,182,212,0.3),0_0_60px_rgba(6,182,212,0.2)] flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-2 border-cyan-400/20 animate-ping"></div>
                <div className="absolute inset-4 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-full blur-xl animate-pulse"></div>

                <UserCheck className="relative w-16 h-16 text-cyan-400" style={{
                  filter: 'drop-shadow(0 0 12px rgba(6, 182, 212, 0.8))',
                  animation: 'float 6s ease-in-out infinite',
                }} />
              </div>

              {/* Cycling status messages */}
              <div className="absolute -bottom-24 left-1/2 -translate-x-1/2 w-96 text-center">
                <div className="relative h-8 overflow-hidden">
                  {idleMessages.map((message, index) => (
                    <p
                      key={index}
                      className={`absolute inset-0 flex items-center justify-center text-sm font-bold text-cyan-400/90 uppercase tracking-widest transition-all duration-700 ${
                        index === idleMessageIndex ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                      }`}
                      style={{
                        textShadow: '0 0 20px rgba(6, 182, 212, 0.5)',
                      }}
                    >
                      <Radio className="w-3 h-3 mr-2 animate-pulse" />
                      {message}
                    </p>
                  ))}
                </div>

                {/* AI monitoring sub-text */}
                <div className="mt-4 flex items-center justify-center gap-2">
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></div>
                  <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                    {searchTerm ? 'No matching intelligence objects' : 'AI standing by'}
                  </p>
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // CONTRACT CARDS - slide in like tasks being assigned
          <div className="space-y-4">
            {filteredContracts.map((contract, index) => (
              <div
                key={contract.id}
                className="relative group"
                style={{
                  opacity: mounted ? 1 : 0,
                  transform: mounted ? 'translateX(0) rotateY(0deg)' : 'translateX(30px) rotateY(-2deg)',
                  transition: `all 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) ${(index * 100) + 700}ms`,
                }}
              >
                {/* Card glow on hover */}
                <div className="absolute -inset-[1px] bg-gradient-to-r from-cyan-500/0 via-cyan-500/20 to-cyan-500/0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm"></div>

                <div
                  className="relative bg-gradient-to-br from-slate-900/90 via-slate-900/70 to-slate-950/90 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-6 cursor-pointer overflow-hidden transition-all duration-500 group-hover:border-cyan-500/40 group-hover:shadow-[0_0_40px_rgba(6,182,212,0.2)] group-hover:translate-x-1"
                  onClick={() => navigate(`/contracts/${contract.id}`)}
                >
                  {/* Shimmer sweep on hover */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>

                  <div className="relative flex items-start justify-between gap-4">
                    <div className="flex items-start gap-4 flex-1">
                      {/* Icon with depth */}
                      <div className="relative">
                        <div className="absolute inset-0 bg-cyan-500/20 rounded-xl blur-md group-hover:blur-lg transition-all duration-500"></div>
                        <div className="relative bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950 p-3 rounded-xl border border-cyan-500/30 group-hover:border-cyan-400/50 transition-all duration-500">
                          <FileText className="w-6 h-6 text-cyan-400 transition-transform duration-500 group-hover:scale-110" style={{
                            filter: 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))',
                          }} />
                        </div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2 flex-wrap">
                          <h3 className="text-lg font-bold text-white truncate group-hover:text-cyan-100 transition-colors duration-500">
                            {contract.original_filename}
                          </h3>
                          {getStatusBadge(contract)}
                          {getRiskBadge(contract)}
                        </div>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
                          <span className="flex items-center gap-1">
                            <span className="font-semibold text-slate-500">Type:</span>
                            {contract.contract_type || 'Unknown'}
                          </span>
                          {contract.contract_value && (
                            <span className="flex items-center gap-1">
                              <span className="font-semibold text-slate-500">Value:</span>
                              {contract.contract_value}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(contract.uploaded_at)}
                          </span>
                          {contract.party_a && (
                            <span className="flex items-center gap-1">
                              <span className="font-semibold text-slate-500">Party:</span>
                              {contract.party_a}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Action Button - powers up on hover */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/contracts/${contract.id}`);
                      }}
                      className="opacity-0 group-hover:opacity-100 bg-gradient-to-br from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white px-4 py-2 rounded-xl transition-all duration-500 flex items-center gap-2 shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:scale-105"
                      title="Access Intelligence Object"
                    >
                      <Eye className="w-4 h-4" />
                      <span className="text-sm font-bold">ACCESS</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary */}
        {!loading && filteredContracts.length > 0 && (
          <div className="bg-gradient-to-r from-slate-900/60 via-slate-900/40 to-slate-900/60 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-4">
            <p className="text-sm text-slate-400 text-center font-semibold">
              <span className="text-cyan-400">{filteredContracts.length}</span> of <span className="text-cyan-400">{contracts.length}</span> intelligence objects loaded
            </p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes light-sweep {
          0% {
            transform: translateX(-100vw);
          }
          100% {
            transform: translateX(200vw);
          }
        }

        @keyframes light-sweep-slow {
          0% {
            transform: translateX(200vw);
          }
          100% {
            transform: translateX(-100vw);
          }
        }

        @keyframes light-sweep-slower {
          0% {
            transform: translateX(-100vw);
          }
          100% {
            transform: translateX(200vw);
          }
        }

        @keyframes breathing {
          0%, 100% {
            opacity: 0.3;
          }
          50% {
            opacity: 0.6;
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-10px);
          }
        }

        @keyframes spin-slow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes spin-slower {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes spin-slowest {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes pulse-slow {
          0%, 100% {
            opacity: 0.4;
          }
          50% {
            opacity: 0.8;
          }
        }

        @keyframes pulse-slower {
          0%, 100% {
            opacity: 0.3;
          }
          50% {
            opacity: 0.6;
          }
        }

        .animate-light-sweep {
          animation: light-sweep 15s linear infinite;
        }

        .animate-light-sweep-slow {
          animation: light-sweep-slow 20s linear infinite;
        }

        .animate-light-sweep-slower {
          animation: light-sweep-slower 25s linear infinite;
        }

        .animate-breathing {
          animation: breathing 4s ease-in-out infinite;
        }

        .animate-spin-slow {
          animation: spin-slow 20s linear infinite;
        }

        .animate-spin-slower {
          animation: spin-slower 30s linear infinite;
        }

        .animate-spin-slowest {
          animation: spin-slowest 40s linear infinite;
        }

        .animate-pulse-slow {
          animation: pulse-slow 4s ease-in-out infinite;
        }

        .animate-pulse-slower {
          animation: pulse-slower 6s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
