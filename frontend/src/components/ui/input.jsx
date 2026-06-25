import React from 'react';
import useThemeStore from '../../store/themeStore';

export const Input = React.forwardRef(
  ({ className = '', type = 'text', ...props }, ref) => {
    const { theme } = useThemeStore();

    return (
      <input
        type={type}
        className={`flex h-10 w-full rounded-lg border ${theme.colors.surfaceBorder} ${theme.colors.surface} px-3 py-2 text-sm ${theme.colors.textPrimary} placeholder:${theme.colors.textTertiary} focus:outline-none focus:ring-2 focus:ring-opacity-50 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50 transition-all ${className}`}
        ref={ref}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';
