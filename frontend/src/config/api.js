// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api`;

export const API_ENDPOINTS = {
  // Auth
  login: '/auth/login',
  register: '/auth/register',

  // Contracts
  contracts: '/contracts',

  // Self-Healing Clause Library
  clauseHealth: '/clauses/health',
  clauseHealthReport: '/clauses/health/report',
  clausePromote: '/clauses/promote',
  clauseRetire: '/clauses/retire',
  clauseAnalyze: '/clauses/analyze',
  clauseEvents: '/clauses/events',
  clauseSimilar: '/clauses/similar',
};

export default API_BASE_URL;
