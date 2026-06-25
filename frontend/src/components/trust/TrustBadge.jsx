import React from 'react';

/**
 * Trust Badge Component
 * Displays a trust badge with icon, label, and color
 */
const TrustBadge = ({ badge, label, color, icon, description, size = 'medium' }) => {
  const sizeClasses = {
    small: 'px-2 py-1 text-xs',
    medium: 'px-3 py-1.5 text-sm',
    large: 'px-4 py-2 text-base'
  };

  const iconSizes = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg'
  };

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full font-semibold ${sizeClasses[size]}`}
      style={{
        backgroundColor: `${color}20`,
        color: color,
        border: `2px solid ${color}`
      }}
      title={description}
    >
      <span className={iconSizes[size]}>{icon}</span>
      <span>{label}</span>
    </div>
  );
};

export default TrustBadge;
