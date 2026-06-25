import React from 'react';
import useThemeStore from '../../store/themeStore';

export const Card = ({ children, className = '', ...props }) => {
  const { theme } = useThemeStore();
  return (
    <div
      className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-xl ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '', ...props }) => {
  const { theme } = useThemeStore();
  return (
    <div className={`px-6 py-5 border-b ${theme.colors.surfaceBorder} ${className}`} {...props}>
      {children}
    </div>
  );
};

export const CardTitle = ({ children, className = '', ...props }) => {
  const { theme } = useThemeStore();
  return (
    <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} ${className}`} {...props}>
      {children}
    </h3>
  );
};

export const CardDescription = ({ children, className = '', ...props }) => {
  const { theme } = useThemeStore();
  return (
    <p className={`text-sm ${theme.colors.textSecondary} mt-1 ${className}`} {...props}>
      {children}
    </p>
  );
};

export const CardContent = ({ children, className = '', ...props }) => {
  return (
    <div className={`px-6 py-5 ${className}`} {...props}>
      {children}
    </div>
  );
};
