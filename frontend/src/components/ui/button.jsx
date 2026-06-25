import React from 'react';
import useThemeStore from '../../store/themeStore';

export const Button = ({
  children,
  variant = 'default',
  size = 'default',
  className = '',
  disabled = false,
  ...props
}) => {
  const { theme } = useThemeStore();

  const baseStyles = 'inline-flex items-center justify-center rounded-lg font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    default: `${theme.colors.primary} text-white ${theme.colors.shadow} focus:ring-opacity-50`,
    outline: `border-2 ${theme.colors.surfaceBorder} ${theme.colors.textSecondary} hover:${theme.colors.surfaceHover} hover:${theme.colors.textPrimary} focus:ring-opacity-50`,
    destructive: 'bg-gradient-to-r from-red-600 to-red-500 text-white hover:from-red-700 hover:to-red-600 shadow-md shadow-red-500/30 focus:ring-red-500',
    ghost: `${theme.colors.textSecondary} hover:${theme.colors.surfaceHover} hover:${theme.colors.textPrimary} focus:ring-opacity-50`,
    link: `${theme.colors.primaryText} hover:opacity-80 underline-offset-4 hover:underline`,
  };

  const sizes = {
    default: 'px-4 py-2 text-sm',
    sm: 'px-3 py-1.5 text-xs',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
