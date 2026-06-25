import { useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  Menu,
  X,
  Home,
  Upload,
  BarChart3,
  Lock,
  LogOut,
  User,
  Settings,
  FileText,
  FileStack,
  Shield,
  Brain,
  Briefcase,
  ClipboardCheck,
  GitCompare,
  Search,
  Target,
  Layers,
  MessageCircle,
  CheckSquare,
  Library,
  CloudUpload,
  UserCheck,
  Crown,
  ArrowUpCircle,
  Zap,
  CreditCard,
  Receipt,
  Beaker,
  AlertTriangle,
  Users,
  Database,
  Activity,
  Webhook,
  FileEdit,
  Sparkles,
  Radio,
  TrendingUp,
  BookOpen,
  Network,
  Scale,
  MessageSquare,
  Globe,
  ChevronDown,
  ChevronUp,
  Cpu,
} from 'lucide-react';
import useAuthStore from '../store/authStore';
import useThemeStore from '../store/themeStore';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { theme } = useThemeStore();
  const [hoveredItem, setHoveredItem] = useState(null);
  const [mounted, setMounted] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState(['enterprise']); // Enterprise group expanded by default

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  const toggleGroup = (groupId) => {
    setExpandedGroups(prev =>
      prev.includes(groupId)
        ? prev.filter(id => id !== groupId)
        : [...prev, groupId]
    );
  };

  const isGroupExpanded = (groupId) => expandedGroups.includes(groupId);

  // AI features for neural traces
  const aiFeatures = ['/chat', '/agentic-ai', '/drift-detection', '/counterfactual-engine', '/rag-search', '/risk-explanation', '/playbook', '/risk-intelligence', '/contract-graph', '/contract-differential', '/concept-correlation', '/arbitration-intelligence', '/dispute-predictor', '/legal-review', '/force-majeure', '/smart-search', '/ai-studio', '/contract-ai-suite', '/multimodal-ai', '/orchestrator', '/advanced-clause-library'];

  // 🔹 SuperAdmin gets different menu with user management & connectors
  const superAdminMenuItems = [
    { label: 'Dashboard', icon: Home, path: '/dashboard' },
    { label: 'Smart Search', icon: Sparkles, path: '/smart-search' },
    { label: 'User Management', icon: Users, path: '/superadmin/users' },
    { label: 'Fivetran Connector', icon: Database, path: '/integrations/fivetran' },
    { label: 'Kafka Connector', icon: Activity, path: '/integrations/kafka' },
    { label: 'SAP S/4HANA', icon: Database, path: '/integrations/sap' },
    { label: 'Infor ERP', icon: Database, path: '/integrations/infor' },
    { label: 'Integration Hub', icon: Globe, path: '/integrations/hub' },
    { label: 'System Stats', icon: BarChart3, path: '/superadmin/stats' },
  ];

  // 🔹 Regular users get standard menu
  const regularMenuItems = [

    // ── OVERVIEW ────────────────────────────────────────────────
    { section: 'Overview' },
    { label: 'Dashboard',           icon: Home,         path: '/dashboard' },
    { label: 'UniContractAI',       icon: Zap,          path: '/prime-dashboard' },
    { label: 'Executive Snapshot',  icon: Activity,     path: '/executive-snapshot' },
    { label: 'Executive Summary',   icon: Briefcase,    path: '/executive-summary' },
    { label: 'Strategic Radar',     icon: Radio,        path: '/strategic-radar' },

    // ── CONTRACTS ───────────────────────────────────────────────
    { section: 'Contracts' },
    { label: 'Upload Contracts',    icon: Upload,       path: '/upload' },
    { label: 'My Contracts',        icon: FileStack,    path: '/contracts' },
    { label: 'Assigned to Me',      icon: UserCheck,    path: '/assigned-contracts' },
    { label: 'Generate Contract',   icon: FileText,     path: '/generate' },
    { label: 'Contract Compare',    icon: GitCompare,   path: '/compare' },

    // ── SEARCH & AI CHAT ─────────────────────────────────────────
    { section: 'Search & AI' },
    { label: 'Smart Search',        icon: Sparkles,     path: '/smart-search' },
    { label: 'Search Contracts',    icon: Search,       path: '/search' },
    { label: 'AI Chat',             icon: MessageCircle,path: '/chat' },
    { label: 'Agentic AI',          icon: Zap,          path: '/agentic-ai' },
    { label: 'RAG Search',          icon: Brain,        path: '/rag-search' },

    // ── RISK INTELLIGENCE ────────────────────────────────────────
    { section: 'Risk Intelligence' },
    { label: 'Risk Value Matrix',   icon: TrendingUp,   path: '/risk-value-matrix' },
    { label: 'Risk Intelligence',   icon: Zap,          path: '/risk-intelligence' },
    { label: 'Risk & Exposure',     icon: Shield,       path: '/risk-exposure' },
    { label: 'AI Risk Explanation', icon: Brain,        path: '/risk-explanation' },
    { label: 'Dispute Predictor',   icon: AlertTriangle,path: '/dispute-predictor' },
    { label: 'Loss Sentinel',       icon: AlertTriangle,path: '/loss-sentinel' },
    { label: 'Force Majeure',       icon: Shield,       path: '/force-majeure' },
    { label: 'Drift Detection',     icon: AlertTriangle,path: '/drift-detection' },

    // ── CLAUSE INTELLIGENCE ──────────────────────────────────────
    { section: 'Clause Intelligence' },
    { label: 'Advanced Clause Library', icon: BookOpen, path: '/advanced-clause-library', badge: 'NEW' },
    { label: 'AI Clause Library',   icon: Library,      path: '/clause-library' },
    { label: 'Clause Heatmap',      icon: Target,       path: '/clause-heatmap' },
    { label: 'Clause Health',       icon: Activity,     path: '/clause-health' },
    { label: 'Clause Trust Score',  icon: Shield,       path: '/trust/statistics' },
    { label: 'RRIE',                icon: Zap,          path: '/rrie' },

    // ── LEGAL & NEGOTIATION ──────────────────────────────────────
    { section: 'Legal & Negotiation' },
    { label: 'Legal Playbook',      icon: Scale,        path: '/legal-playbook' },
    { label: 'Adv. Legal Review',   icon: Scale,        path: '/legal-review' },
    { label: 'Arbitration Risk',    icon: Scale,        path: '/arbitration-intelligence' },
    { label: 'Playbook Automation', icon: BookOpen,     path: '/playbook' },
    { label: 'Negotiation Intelligence', icon: TrendingUp, path: '/negotiation-intelligence' },
    { label: 'Negotiation Mode',    icon: MessageSquare,path: '/negotiation-mode' },
    { label: 'What-If Simulation',  icon: Sparkles,     path: '/counterfactual-simulation' },
    { label: 'Counterfactual Engine',icon: Beaker,      path: '/counterfactual-engine' },

    // ── PORTFOLIO & ANALYTICS ────────────────────────────────────
    { section: 'Portfolio & Analytics' },
    { label: 'Portfolio Intelligence', icon: Network,   path: '/portfolio-intelligence' },
    { label: 'Counterparty Risk',   icon: Users,        path: '/counterparty-portfolio' },
    { label: 'Analytics',           icon: BarChart3,    path: '/analytics' },
    { label: 'Portfolio Analytics', icon: Target,       path: '/portfolio-analytics' },
    { label: 'Contract Maps',       icon: TrendingUp,   path: '/contract-maps' },

    // ── AI STUDIO ────────────────────────────────────────────────
    { section: 'AI Studio' },
    { label: 'AI Studio',           icon: Cpu,          path: '/ai-studio' },
    { label: 'Contract AI Suite',   icon: Sparkles,     path: '/contract-ai-suite' },
    { label: 'Multi-Modal AI',      icon: Layers,       path: '/multimodal-ai' },

    // ── KNOWLEDGE GRAPH ──────────────────────────────────────────
    { section: 'Knowledge Graph' },
    { label: 'Contract Intelligence', icon: Brain,      path: '/contract-intelligence' },
    { label: 'Contract Graph',      icon: Network,      path: '/contract-graph' },
    { label: 'Contract Twin',       icon: Activity,     path: '/contract-twin' },
    { label: 'Contract Differential',icon: GitCompare,  path: '/contract-differential' },
    { label: 'Concept Topology',    icon: Network,      path: '/concept-correlation' },
    { label: 'Graph Status',        icon: Network,      path: '/graph-status' },

    // ── ENTERPRISE ───────────────────────────────────────────────
    { section: 'Enterprise' },
    {
      label: 'Enterprise Risk',
      icon: Globe,
      path: '/enterprise/risk-dashboard',
      groupId: 'enterprise',
      subItems: [
        { label: 'Global Risk Dashboard',    icon: Globe,       path: '/enterprise/risk-dashboard' },
        { label: 'Contract Knowledge Graph', icon: Network,     path: '/enterprise/contract-graph' },
        { label: 'Supply Chain Risk',        icon: Activity,    path: '/enterprise/supply-chain' },
        { label: 'Geo-Political Risk Map',   icon: Globe,       path: '/enterprise/geo-risk' },
        { label: 'Commodity Forecast',       icon: TrendingUp,  path: '/enterprise/commodity' },
        { label: 'Monte Carlo VaR',          icon: BarChart3,   path: '/enterprise/monte-carlo' },
        { label: 'Margin Sensitivity',       icon: Target,      path: '/enterprise/margin-sensitivity' },
        { label: 'Portfolio VaR',            icon: Briefcase,   path: '/enterprise/portfolio-var' },
      ]
    },
    { label: 'Tender Intelligence', icon: Briefcase,    path: '/tenders' },
    { label: 'Company Profile',     icon: User,         path: '/tenders/company-profile' },

    // ── WORKFLOW ─────────────────────────────────────────────────
    { section: 'Workflow' },
    { label: 'Obligation Tracker',  icon: ClipboardCheck, path: '/obligation-tracker' },
    { label: 'Approval Inbox',      icon: CheckSquare,  path: '/approvals/inbox' },
    { label: 'Contract Classify',   icon: Layers,       path: '/contract-classify' },

    // ── INTEGRATIONS ─────────────────────────────────────────────
    { section: 'Integrations' },
    { label: 'SAP S/4HANA',         icon: Database,     path: '/integrations/sap' },
    { label: 'Infor ERP',           icon: Database,     path: '/integrations/infor' },
    { label: 'Integration Hub',     icon: Globe,        path: '/integrations/hub' },
    { label: 'Alfresco Sync',       icon: CloudUpload,  path: '/alfresco-sync' },
    ...(user?.fivetranAccess ? [{ label: 'Fivetran', icon: Database, path: '/integrations/fivetran' }] : []),
    ...(user?.kafkaAccess    ? [{ label: 'Kafka',    icon: Activity, path: '/integrations/kafka'    }] : []),

    // ── ACCOUNT ──────────────────────────────────────────────────
    { section: 'Account' },
    { label: 'Your Plan',           icon: Crown,        path: '/my-plan' },
    { label: 'Payment History',     icon: Receipt,      path: '/payments/history' },
    ...(user?.role === 'Admin'
      ? [{ label: 'Admin Panel',    icon: Lock,         path: '/admin' }]
      : []),
  ];

  // Choose menu based on role
  const menuItems = user?.role === 'SuperAdmin' ? superAdminMenuItems : regularMenuItems;

  return (
    <>
      {/* Mobile toggle */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-3 rounded-xl bg-black/95 backdrop-blur-xl border border-cyan-500/20 text-cyan-400 hover:border-cyan-400/60 hover:shadow-[0_0_25px_rgba(6,182,212,0.3)] transition-all duration-500"
        >
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* AI Command Spine */}
      <aside
        className={`fixed left-0 top-0 h-screen w-72 transform transition-all duration-700 z-40 lg:translate-x-0 flex flex-col
        ${isOpen ? 'translate-x-0' : '-translate-x-full'} lg:static overflow-hidden`}
        style={{
          background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
          opacity: mounted ? 1 : 0,
          transition: 'opacity 0.8s cubic-bezier(0.22, 1, 0.36, 1)',
          boxShadow: '4px 0 40px rgba(0, 0, 0, 0.6), inset -1px 0 1px rgba(6, 182, 212, 0.15)',
        }}
      >
        {/* Animated neural mesh background */}
        <div className="absolute inset-0 opacity-20 pointer-events-none">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#06b6d420_1px,transparent_1px),linear-gradient(to_bottom,#06b6d420_1px,transparent_1px)] bg-[size:40px_40px] animate-neural-drift"></div>
        </div>

        {/* Scanning lines (idle animation) - brightened */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent animate-scan-slow"></div>
          <div className="absolute top-1/3 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-500/40 to-transparent animate-scan-slower"></div>
          <div className="absolute top-2/3 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-violet-500/30 to-transparent animate-scan-slowest"></div>
        </div>

        {/* Depth layers - ambient energy fields - brightened */}
        <div className="absolute top-0 left-0 w-full h-96 bg-gradient-radial from-cyan-500/10 via-transparent to-transparent pointer-events-none blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-0 w-full h-96 bg-gradient-radial from-violet-500/8 via-transparent to-transparent pointer-events-none blur-3xl animate-pulse-slower"></div>
        <div className="absolute top-1/2 left-0 w-full h-64 bg-gradient-radial from-blue-500/7 via-transparent to-transparent pointer-events-none blur-2xl"></div>

        {/* AI Core Header */}
        <div className="relative flex items-center gap-3 px-4 py-5 border-b border-cyan-500/20">
          <img src="/logo.png" alt="UniContractAI" className="w-12 h-12 object-contain flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-blue-300 tracking-tight leading-tight">UniContractAI</h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_6px_rgba(6,182,212,1)]"></div>
              <span className="text-[10px] text-cyan-400/80 font-medium">AI ACTIVE</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-4 py-6 relative">
          <div className="space-y-1.5">
            {menuItems.map((item, index) => {
              // Render section header
              if (item.section) {
                return (
                  <div key={`section-${item.section}`} className="pt-4 pb-1 px-2">
                    <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-500/70 select-none">
                      {item.section}
                    </p>
                  </div>
                );
              }

              const Icon = item.icon;
              const active = isActive(item.path);
              const isHovered = hoveredItem === item.path;
              const isAI = aiFeatures.includes(item.path);
              const hasSubItems = item.subItems && item.subItems.length > 0;
              const isExpanded = hasSubItems && isGroupExpanded(item.groupId);
              const isGroupActive = hasSubItems && item.subItems.some(sub => isActive(sub.path));

              // Section headers rendered separately below
              const showDivider = false;

              return (
                <div
                  key={`${index}-${item.path || item.groupId}`}
                  style={{
                    opacity: mounted ? 1 : 0,
                    transform: mounted ? 'translateY(0)' : 'translateY(10px)',
                    transition: `opacity 0.4s ease-out ${index * 30}ms, transform 0.4s ease-out ${index * 30}ms`,
                  }}
                >
                  {showDivider && (
                    <div className="my-4 h-px bg-gradient-to-r from-transparent via-slate-700/50 to-transparent"></div>
                  )}

                  <div className="relative group">
                    {/* Active energy spine - aggressive flowing animation */}
                    {(active || isGroupActive) && (
                      <div className="absolute -left-4 top-0 bottom-0 w-1.5 rounded-r-full overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-b from-cyan-400 via-blue-500 to-violet-600"></div>
                        <div className="absolute inset-0 bg-gradient-to-b from-cyan-300 via-blue-400 to-violet-500 animate-energy-flow"></div>
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/30 to-transparent animate-energy-pulse"></div>
                      </div>
                    )}

                    {/* AI neural traces with particle emission */}
                    {isAI && !active && !isGroupActive && (
                      <>
                        <div className="absolute -left-3 top-1/2 -translate-y-1/2 w-0.5 h-8 bg-gradient-to-b from-transparent via-cyan-500/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                        <div className="absolute -left-3 top-1/2 -translate-y-1/2">
                          <div className="w-1 h-1 bg-cyan-400 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-ping"></div>
                        </div>
                      </>
                    )}

                    <button
                      onClick={() => {
                        if (hasSubItems) {
                          toggleGroup(item.groupId);
                        } else {
                          navigate(item.path);
                          setIsOpen(false);
                        }
                      }}
                      onMouseEnter={() => setHoveredItem(item.path || item.groupId)}
                      onMouseLeave={() => setHoveredItem(null)}
                      className="relative w-full flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all overflow-hidden"
                      style={{
                        background: (active || isGroupActive)
                          ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.18) 0%, rgba(59, 130, 246, 0.15) 50%, rgba(139, 92, 246, 0.12) 100%)'
                          : isHovered
                          ? 'rgba(6, 182, 212, 0.08)'
                          : 'transparent',
                        backdropFilter: (active || isGroupActive) ? 'blur(12px)' : isHovered ? 'blur(8px)' : 'none',
                        border: (active || isGroupActive)
                          ? '1px solid rgba(6, 182, 212, 0.35)'
                          : isHovered
                          ? '1px solid rgba(6, 182, 212, 0.15)'
                          : '1px solid rgba(6, 182, 212, 0.05)',
                        boxShadow: (active || isGroupActive)
                          ? '0 0 30px rgba(6, 182, 212, 0.25), 0 8px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.12)'
                          : isHovered
                          ? '0 4px 12px rgba(6, 182, 212, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.05)'
                          : 'none',
                        transform: (active || isGroupActive)
                          ? 'translateX(4px) scale(1.01)'
                          : isHovered
                          ? 'translateX(3px) rotateY(1deg)'
                          : 'translateX(0) rotateY(0deg)',
                        transformStyle: 'preserve-3d',
                        transition: 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
                      }}
                    >
                      {/* Power-up shimmer on hover */}
                      {isHovered && !active && (
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/8 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1200"></div>
                      )}

                      {/* Active state: locked-in energy flow */}
                      {active && (
                        <>
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/12 to-transparent animate-locked-shimmer"></div>
                          <div className="absolute inset-0 border border-cyan-400/10 rounded-2xl animate-pulse-slow"></div>
                        </>
                      )}

                      {/* Icon - etched with depth */}
                      <div
                        className="relative transition-all duration-500 flex items-center justify-center"
                        style={{
                          transform: isHovered
                            ? 'translateZ(8px) scale(1.15) rotate(-5deg)'
                            : active
                            ? 'translateZ(6px) scale(1.1)'
                            : 'translateZ(0) scale(1) rotate(0deg)',
                          filter: active
                            ? 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))'
                            : isHovered
                            ? 'drop-shadow(0 0 6px rgba(6, 182, 212, 0.4))'
                            : 'none',
                        }}
                      >
                        <Icon
                          size={20}
                          strokeWidth={2.5}
                          style={{
                            color: active ? '#06b6d4' : isHovered ? '#67e8f9' : '#475569',
                          }}
                        />

                        {/* AI signature particles */}
                        {isAI && (
                          <>
                            <Sparkles
                              className="absolute -top-1 -right-1 w-3.5 h-3.5 text-cyan-400 opacity-0 group-hover:opacity-100 transition-all duration-500"
                              style={{
                                filter: 'drop-shadow(0 0 4px rgba(6, 182, 212, 0.8))',
                              }}
                            />
                            {/* Orbiting dot */}
                            <div className="absolute -top-1 -left-1 w-1.5 h-1.5 bg-cyan-400 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-orbit shadow-[0_0_6px_rgba(6,182,212,0.8)]"></div>
                          </>
                        )}
                      </div>

                      {/* Text - slides with inertia */}
                      <span
                        className="font-bold text-sm tracking-wide transition-all duration-500"
                        style={{
                          transform: isHovered
                            ? 'translateX(6px)'
                            : active
                            ? 'translateX(4px)'
                            : 'translateX(0)',
                          color: active
                            ? '#f0f9ff'
                            : isHovered
                            ? '#e0f2fe'
                            : '#64748b',
                          textShadow: active
                            ? '0 0 10px rgba(6, 182, 212, 0.3)'
                            : 'none',
                          letterSpacing: active ? '0.05em' : '0.025em',
                        }}
                      >
                        {item.label}
                      </span>


                      {/* Chevron icon for expandable groups */}
                      {hasSubItems && (
                        <div className={`ml-auto transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
                          <ChevronDown
                            size={18}
                            className="text-cyan-400"
                          />
                        </div>
                      )}

                      {/* AI module tooltip */}
                      {isAI && isHovered && (
                        <div className="absolute left-full ml-5 top-1/2 -translate-y-1/2 px-4 py-2.5 bg-black/98 backdrop-blur-xl border border-cyan-500/40 rounded-xl shadow-[0_0_30px_rgba(6,182,212,0.3)] whitespace-nowrap pointer-events-none z-50 animate-fadeIn">
                          <div className="flex items-center gap-2.5">
                            <div className="relative flex items-center justify-center">
                              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(6,182,212,0.8)]"></div>
                              <div className="absolute w-3 h-3 bg-cyan-400/30 rounded-full animate-ping"></div>
                            </div>
                            <span className="text-xs font-black text-cyan-300 uppercase tracking-wider">Neural Module</span>
                          </div>
                          <div className="absolute right-full top-1/2 -translate-y-1/2 border-[6px] border-transparent border-r-black/98"></div>
                        </div>
                      )}
                    </button>
                  </div>

                  {/* Sub-items (collapsible) */}
                  {hasSubItems && isExpanded && (
                    <div className="ml-4 mt-1 space-y-1 border-l-2 border-cyan-500/20 pl-2">
                      {item.subItems.map((subItem, subIndex) => {
                        const SubIcon = subItem.icon;
                        const subActive = isActive(subItem.path);
                        const subHovered = hoveredItem === subItem.path;

                        return (
                          <button
                            key={subItem.path}
                            onClick={() => {
                              navigate(subItem.path);
                              setIsOpen(false);
                            }}
                            onMouseEnter={() => setHoveredItem(subItem.path)}
                            onMouseLeave={() => setHoveredItem(null)}
                            className="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all overflow-hidden"
                            style={{
                              background: subActive
                                ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(59, 130, 246, 0.12) 50%, rgba(139, 92, 246, 0.1) 100%)'
                                : subHovered
                                ? 'rgba(6, 182, 212, 0.06)'
                                : 'transparent',
                              border: subActive
                                ? '1px solid rgba(6, 182, 212, 0.3)'
                                : subHovered
                                ? '1px solid rgba(6, 182, 212, 0.12)'
                                : '1px solid transparent',
                              boxShadow: subActive
                                ? '0 0 20px rgba(6, 182, 212, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                                : 'none',
                              transform: subActive ? 'translateX(2px)' : subHovered ? 'translateX(1px)' : 'translateX(0)',
                              opacity: mounted ? 1 : 0,
                              transition: `all 0.3s ease ${subIndex * 20}ms`,
                            }}
                          >
                            {/* Shimmer on hover */}
                            {subHovered && !subActive && (
                              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/6 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                            )}

                            {/* Icon */}
                            <div className="flex items-center justify-center">
                              <SubIcon
                                size={16}
                                strokeWidth={2.5}
                                style={{
                                  color: subActive ? '#06b6d4' : subHovered ? '#67e8f9' : '#64748b',
                                  filter: subActive ? 'drop-shadow(0 0 6px rgba(6, 182, 212, 0.5))' : 'none',
                                }}
                              />
                            </div>

                            {/* Text */}
                            <span
                              className="font-semibold text-xs tracking-wide"
                              style={{
                                color: subActive ? '#f0f9ff' : subHovered ? '#e0f2fe' : '#64748b',
                                textShadow: subActive ? '0 0 8px rgba(6, 182, 212, 0.2)' : 'none',
                              }}
                            >
                              {subItem.label}
                            </span>

                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </nav>

        {/* System Controls */}
        <div className="relative border-t border-cyan-500/20 px-4 py-5 bg-gradient-to-t from-slate-900/60 via-slate-950/30 to-transparent backdrop-blur-md">
          <div className="space-y-2">
            <button
              onClick={() => {
                navigate('/profile');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-500 hover:text-cyan-300 hover:bg-cyan-500/5 rounded-xl transition-all duration-500 group border border-transparent hover:border-cyan-500/20"
            >
              <User size={18} className="transition-all duration-500 group-hover:scale-125 group-hover:rotate-12" style={{
                filter: 'drop-shadow(0 0 0 transparent)',
              }} />
              <span className="font-bold tracking-wide transition-all duration-500 group-hover:translate-x-1">Operator Profile</span>
            </button>

            <button
              onClick={() => {
                navigate('/settings');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-slate-500 hover:text-cyan-300 hover:bg-cyan-500/5 rounded-xl transition-all duration-500 group border border-transparent hover:border-cyan-500/20"
            >
              <Settings size={18} className="transition-all duration-700 group-hover:rotate-180 group-hover:scale-125" style={{
                transformOrigin: 'center',
              }} />
              <span className="font-bold tracking-wide transition-all duration-500 group-hover:translate-x-1">Core Config</span>
            </button>

            {/* Disconnect button - feels like powering down */}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-500/70 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all duration-500 group border border-red-500/10 hover:border-red-500/30 hover:shadow-[0_0_20px_rgba(239,68,68,0.2)]"
            >
              <LogOut size={18} className="transition-all duration-500 group-hover:translate-x-2 group-hover:scale-110" />
              <span className="font-bold tracking-wide transition-all duration-500">Disconnect</span>
              <div className="ml-auto w-1.5 h-1.5 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 group-hover:animate-pulse transition-opacity duration-500"></div>
            </button>
          </div>

          {/* Operator status card */}
          {user && (
            <div className="mt-4 px-4 py-4 bg-gradient-to-br from-slate-800/70 via-slate-900/80 to-slate-950/70 backdrop-blur-md border border-cyan-500/30 rounded-2xl shadow-[0_0_20px_rgba(6,182,212,0.15),inset_0_1px_0_rgba(6,182,212,0.15)]">
              <div className="flex items-center gap-3">
                {/* Avatar with energy ring */}
                <div className="relative">
                  <div className="absolute -inset-1 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl blur-md opacity-60 animate-pulse-slow"></div>
                  <div className="relative w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-500 to-violet-600 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.4),inset_0_1px_0_rgba(255,255,255,0.2)] border border-cyan-400/30">
                    <span className="text-white font-black text-base" style={{
                      textShadow: '0 0 8px rgba(0, 0, 0, 0.8)',
                    }}>
                      {user.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-white truncate tracking-wide">{user.username}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <div className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_4px_rgba(6,182,212,0.8)]"></div>
                    <p className="text-[10px] text-cyan-400 font-black uppercase tracking-[0.15em]">{user.role || 'Operator'}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>

      <style>{`
        /* Neural drift background */
        @keyframes neural-drift {
          0% {
            transform: translate(0, 0);
          }
          33% {
            transform: translate(2px, -3px);
          }
          66% {
            transform: translate(-3px, 2px);
          }
          100% {
            transform: translate(0, 0);
          }
        }

        /* Scanning lines */
        @keyframes scan-slow {
          0% {
            transform: translateY(-100%);
            opacity: 0;
          }
          50% {
            opacity: 0.4;
          }
          100% {
            transform: translateY(100vh);
            opacity: 0;
          }
        }

        @keyframes scan-slower {
          0% {
            transform: translateY(-100%);
            opacity: 0;
          }
          50% {
            opacity: 0.3;
          }
          100% {
            transform: translateY(100vh);
            opacity: 0;
          }
        }

        @keyframes scan-slowest {
          0% {
            transform: translateY(-100%);
            opacity: 0;
          }
          50% {
            opacity: 0.2;
          }
          100% {
            transform: translateY(100vh);
            opacity: 0;
          }
        }

        /* Noise animation */
        @keyframes noise {
          0%, 100% {
            transform: translate(0, 0);
          }
          10% {
            transform: translate(-5%, -5%);
          }
          20% {
            transform: translate(-10%, 5%);
          }
          30% {
            transform: translate(5%, -10%);
          }
          40% {
            transform: translate(-5%, 15%);
          }
          50% {
            transform: translate(-10%, 5%);
          }
          60% {
            transform: translate(15%, 0);
          }
          70% {
            transform: translate(0, 10%);
          }
          80% {
            transform: translate(-15%, 0);
          }
          90% {
            transform: translate(10%, 5%);
          }
        }

        /* Energy flow */
        @keyframes energy-flow {
          0% {
            transform: translateY(-100%);
            opacity: 0.6;
          }
          50% {
            opacity: 1;
          }
          100% {
            transform: translateY(100%);
            opacity: 0.6;
          }
        }

        @keyframes energy-pulse {
          0%, 100% {
            opacity: 0.3;
          }
          50% {
            opacity: 0.8;
          }
        }

        /* Locked shimmer for active items */
        @keyframes locked-shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(200%);
          }
        }

        /* Orbital particle */
        @keyframes orbit {
          0% {
            transform: rotate(0deg) translateX(12px) rotate(0deg);
          }
          100% {
            transform: rotate(360deg) translateX(12px) rotate(-360deg);
          }
        }

        /* Slow rotation */
        @keyframes spin-slow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        /* Pulse variations */
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

        /* Gradient animation */
        @keyframes gradient {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }

        /* Fade in */
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        /* Apply animations */
        .animate-neural-drift {
          animation: neural-drift 20s ease-in-out infinite;
        }

        .animate-scan-slow {
          animation: scan-slow 8s linear infinite;
        }

        .animate-scan-slower {
          animation: scan-slower 12s linear infinite 2s;
        }

        .animate-scan-slowest {
          animation: scan-slowest 16s linear infinite 4s;
        }

        .animate-noise {
          animation: noise 8s steps(10) infinite;
        }

        .animate-energy-flow {
          animation: energy-flow 2s ease-in-out infinite;
        }

        .animate-energy-pulse {
          animation: energy-pulse 2s ease-in-out infinite;
        }

        .animate-locked-shimmer {
          animation: locked-shimmer 4s ease-in-out infinite;
        }

        .animate-orbit {
          animation: orbit 3s linear infinite;
        }

        .animate-spin-slow {
          animation: spin-slow 8s linear infinite;
        }

        .animate-pulse-slow {
          animation: pulse-slow 4s ease-in-out infinite;
        }

        .animate-pulse-slower {
          animation: pulse-slower 6s ease-in-out infinite;
        }

        .animate-gradient {
          animation: gradient 3s ease infinite;
        }

        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }

        /* Custom scrollbar - energy styled */
        nav::-webkit-scrollbar {
          width: 5px;
        }

        nav::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.6);
          border-radius: 10px;
        }

        nav::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%);
          border-radius: 10px;
          box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }

        nav::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #22d3ee 0%, #60a5fa 50%, #a78bfa 100%);
          box-shadow: 0 0 15px rgba(6, 182, 212, 0.8);
        }

        /* Radial gradient support */
        .bg-gradient-radial {
          background-image: radial-gradient(var(--tw-gradient-stops));
        }
      `}</style>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
