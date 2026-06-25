// Centralized API Configuration
// All API URLs should be configured here and imported throughout the application

const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

// Export configured API URLs
export const config = {
  // Base API URL
  API_BASE_URL: `${API_BASE_URL}/api`,

  // Payment APIs
  PAYMENT_HISTORY_URL: `${API_BASE_URL}/api/payments/history`,
  PAYPAL_CREATE_ORDER_URL: `${API_BASE_URL}/api/payments/paypal/create-order`,
  PAYPAL_CAPTURE_ORDER_URL: `${API_BASE_URL}/api/payments/paypal/capture-order`,
  STRIPE_CREATE_INTENT_URL: `${API_BASE_URL}/api/payments/stripe/create-intent`,
  STRIPE_CONFIRM_URL: `${API_BASE_URL}/api/payments/stripe/confirm`,

  // Contract APIs
  CONTRACTS_LIST_URL: `${API_BASE_URL}/api/contracts/list`,
  CONTRACT_DOWNLOAD_URL: (contractId) => `${API_BASE_URL}/api/contracts/${contractId}/download-modified`,

  // User/Subscription APIs
  PRICING_PLANS_URL: `${API_BASE_URL}/api/pricing/plans`,
  CURRENT_SUBSCRIPTION_URL: `${API_BASE_URL}/api/subscription/current`,
  SELECT_PLAN_URL: `${API_BASE_URL}/api/user/select-plan`,

  // RAG APIs
  RAG_UPLOAD_FILES_URL: `${API_BASE_URL}/api/rag/upload`,
  RAG_GENERATE_FROM_SAMPLES_URL: `${API_BASE_URL}/api/rag/generate-from-samples`,
  RAG_STATS_URL: `${API_BASE_URL}/api/rag/stats`,
  GENERATE_PDF_URL: `${API_BASE_URL}/api/rag/generate-pdf`,

  // SAP S/4HANA Integration APIs
  SAP_HEALTH_URL: `${API_BASE_URL}/api/sap/health`,
  SAP_CONTRACTS_URL: `${API_BASE_URL}/api/sap/contracts`,
  SAP_CONTRACT_DETAIL_URL: (contractId) => `${API_BASE_URL}/api/sap/contracts/${contractId}`,
  SAP_SYNC_URL: `${API_BASE_URL}/api/sap/contracts/sync`,
  SAP_RISK_ANALYSIS_URL: (contractId) => `${API_BASE_URL}/api/sap/contracts/${contractId}/risk`,

  // Base URL for file downloads
  BASE_URL: API_BASE_URL,
};

// Default export for backward compatibility
export default config.API_BASE_URL;
