import React from 'react';
import useThemeStore from '../../store/themeStore';

export const Badge = ({ children, variant = 'default', className = '', ...props }) => {
  const { theme } = useThemeStore();

  const baseStyles = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold transition-colors';

  const variants = {
    default: `bg-blue-600/20 text-blue-300 border border-blue-500/30`,
    outline: `border ${theme.colors.surfaceBorder} ${theme.colors.textSecondary} hover:${theme.colors.surfaceHover}`,
    destructive: 'bg-red-600/20 text-red-300 border border-red-500/30',
    success: 'bg-green-600/20 text-green-300 border border-green-500/30',
    warning: 'bg-yellow-600/20 text-yellow-300 border border-yellow-500/30',
    secondary: `${theme.colors.surfaceHover} ${theme.colors.textSecondary} border ${theme.colors.surfaceBorder}`,
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
};
