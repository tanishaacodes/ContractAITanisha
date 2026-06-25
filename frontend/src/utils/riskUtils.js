/**
 * Shared utility functions for risk calculations and formatting
 */

/**
 * Get color for risk score
 * @param {number} score - Risk score between 0 and 1
 * @returns {string} Hex color code
 */
export function getRiskColor(score) {
  if (score >= 0.7) return '#ef4444'; // red
  if (score >= 0.4) return '#f59e0b'; // amber
  return '#10b981'; // green
}

/**
 * Get label for risk score
 * @param {number} score - Risk score between 0 and 1
 * @returns {string} Risk level label
 */
export function getRiskLabel(score) {
  if (score >= 0.7) return 'HIGH';
  if (score >= 0.4) return 'MEDIUM';
  return 'LOW';
}

/**
 * Get Tailwind CSS classes for risk badge
 * @param {number} score - Risk score between 0 and 1
 * @returns {string} Tailwind classes
 */
export function getRiskBadgeClasses(score) {
  if (score >= 0.7) {
    return 'bg-red-500/15 text-red-400 border-red-500/30';
  }
  if (score >= 0.4) {
    return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  }
  return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
}

/**
 * Format large numbers for display (millions, billions, etc.)
 * @param {number} value - Numeric value
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted string
 */
export function formatLargeNumber(value, decimals = 1) {
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(decimals)}B`;
  }
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(decimals)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(decimals)}K`;
  }
  return `$${value.toFixed(decimals)}`;
}

/**
 * Format percentage with sign
 * @param {number} value - Percentage value
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage with + or -
 */
export function formatPercentage(value, decimals = 1) {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * Calculate Value at Risk (VaR) from exposure
 * @param {number} exposure - Total exposure amount
 * @param {number} confidence - Confidence level (0.95 or 0.99)
 * @returns {number} VaR amount
 */
export function calculateVaR(exposure, confidence = 0.95) {
  const multiplier = confidence === 0.99 ? 0.35 : 0.25;
  return exposure * multiplier;
}

/**
 * Categorize contracts by risk level
 * @param {Array} contracts - Array of contract objects with risk_score
 * @returns {Object} Categorized counts
 */
export function categorizeContractsByRisk(contracts) {
  return {
    high: contracts.filter(c => c.risk_score >= 0.7).length,
    medium: contracts.filter(c => c.risk_score >= 0.4 && c.risk_score < 0.7).length,
    low: contracts.filter(c => c.risk_score < 0.4).length,
    total: contracts.length
  };
}

/**
 * Sort array by multiple criteria
 * @param {Array} array - Array to sort
 * @param {string} sortBy - Field to sort by
 * @param {boolean} ascending - Sort direction
 * @returns {Array} Sorted array
 */
export function sortByField(array, sortBy, ascending = false) {
  const sorted = [...array].sort((a, b) => {
    const aVal = a[sortBy] || 0;
    const bVal = b[sortBy] || 0;
    return ascending ? aVal - bVal : bVal - aVal;
  });
  return sorted;
}
