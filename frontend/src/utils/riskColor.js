/**
 * Risk Color Utilities for Silent Risk Heatmap
 * Maps financial exposure and confidence to color codes
 */

/**
 * Convert risk exposure and confidence to a color
 * @param {number} exposure - Financial exposure amount
 * @param {number} confidence - Confidence score (0-1)
 * @returns {string} Tailwind CSS color class
 */
export function riskToColor(exposure, confidence) {
  // Normalize exposure (assuming max of 100 for display purposes)
  const normalizedExposure = Math.min(exposure / 100, 1);

  // Calculate weighted risk score
  const riskScore = normalizedExposure * 0.5 + confidence * 0.5;

  if (confidence > 0.8 && normalizedExposure > 0.3) {
    return 'bg-red-900 text-white'; // Dark Red - Critical
  }
  if (confidence > 0.7 && riskScore > 0.6) {
    return 'bg-red-600 text-white'; // Red - High Risk
  }
  if (confidence > 0.5 && riskScore > 0.4) {
    return 'bg-yellow-500 text-gray-900'; // Amber - Medium Risk
  }
  if (confidence > 0.3) {
    return 'bg-green-400 text-gray-900'; // Green - Low Risk
  }
  return 'bg-gray-200 text-gray-600'; // Gray - No significant risk
}

/**
 * Get risk severity badge color
 * @param {string} severity - Severity level (LOW, MEDIUM, HIGH, CRITICAL)
 * @returns {string} Tailwind CSS color class
 */
export function severityToColor(severity) {
  const colors = {
    'CRITICAL': 'bg-red-900 text-white',
    'HIGH': 'bg-red-600 text-white',
    'MEDIUM': 'bg-yellow-500 text-gray-900',
    'LOW': 'bg-green-500 text-white',
  };
  return colors[severity] || 'bg-gray-400 text-white';
}

/**
 * Get risk type badge color
 * @param {string} riskType - Type of risk
 * @returns {string} Tailwind CSS color class
 */
export function riskTypeToBadgeColor(riskType) {
  const colors = {
    'CROSS_CLAUSE_CONFLICT': 'bg-purple-600 text-white',
    'LATENT_FINANCIAL_TRIGGER': 'bg-orange-600 text-white',
    'DELAYED_LIABILITY': 'bg-red-700 text-white',
    'HIDDEN_COST_ESCALATION': 'bg-amber-600 text-white',
    'NON_RECOVERABLE_SPEND': 'bg-rose-600 text-white',
    'LONG_TAIL_LIABILITY': 'bg-indigo-600 text-white',
    'TERMINATION_PAYMENT_MISMATCH': 'bg-pink-600 text-white',
  };
  return colors[riskType] || 'bg-gray-600 text-white';
}

/**
 * Format financial exposure for display
 * @param {number} exposure - Exposure amount
 * @param {string} currency - Currency symbol (default: ₹)
 * @returns {string} Formatted string
 */
export function formatExposure(exposure, currency = '₹') {
  if (exposure >= 10000000) {
    return `${currency}${(exposure / 10000000).toFixed(1)} Cr`;
  }
  if (exposure >= 100000) {
    return `${currency}${(exposure / 100000).toFixed(1)} L`;
  }
  return `${currency}${exposure.toLocaleString()}`;
}
