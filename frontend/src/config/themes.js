// Theme Configuration for ContractAI
// EXACT colors from Black Dashboard React by Creative Tim
// Repository: https://github.com/akashmavle5/black-dashboard-react

export const themes = {
  // Dark Theme - ORIGINAL Black Dashboard (Slate colors with Blue accents)
  dark: {
    id: 'dark',
    name: 'Black Dashboard',
    description: 'Original dark theme - DO NOT CHANGE',
    colors: {
      // Raw hex values - Tailwind Slate colors
      raw: {
        background: '#020617',        // slate-950
        backgroundAlt: '#0f172a',     // slate-900
        surface: '#0f172a',           // slate-900
        surfaceHover: '#1e293b',      // slate-800
        border: '#334155',            // slate-700
        textPrimary: '#ffffff',       // white
        textSecondary: '#94a3b8',     // slate-400
        textTertiary: '#64748b',      // slate-500
        primary: '#2563eb',           // blue-600
        primaryDark: '#1d4ed8',       // blue-700
        success: '#10b981',           // emerald-500
        warning: '#f59e0b',           // amber-500
        danger: '#ef4444',            // red-500
        info: '#3b82f6',              // blue-500
      },

      // Background gradients - ORIGINAL slate colors
      bgPrimary: 'from-slate-950 via-slate-900 to-slate-950',
      bgSecondary: 'from-slate-900/95 to-slate-950/95',
      bgTertiary: 'from-slate-900 to-slate-800',
      background: 'bg-slate-950',

      // Surface colors - ORIGINAL slate
      surface: 'bg-slate-900',
      surfaceHover: 'bg-slate-800',
      surfaceBorder: 'border-slate-700',

      // Text colors - ORIGINAL
      textPrimary: 'text-white',
      textSecondary: 'text-slate-400',
      textTertiary: 'text-slate-500',

      // Primary accent - ORIGINAL Blue
      primary: 'bg-gradient-to-r from-blue-600 to-blue-500',
      primarySolid: 'bg-blue-600',
      primaryHover: 'bg-blue-700',
      primaryText: 'text-blue-400',
      primaryBorder: 'border-blue-600',

      // Secondary/Default color
      secondary: 'bg-slate-700',
      secondaryHover: 'bg-slate-600',
      secondaryText: 'text-slate-300',

      // Status colors - keep consistent
      success: 'bg-emerald-500',
      successText: 'text-emerald-400',
      successBorder: 'border-emerald-500',

      warning: 'bg-amber-500',
      warningText: 'text-amber-400',
      warningBorder: 'border-amber-500',

      danger: 'bg-red-500',
      dangerText: 'text-red-400',
      dangerBorder: 'border-red-500',

      info: 'bg-blue-500',
      infoText: 'text-blue-400',
      infoBorder: 'border-blue-500',

      // Sidebar gradient
      sidebarGradient: 'from-slate-900 to-slate-800',

      // Shadows
      shadow: 'shadow-lg shadow-black/20',
      shadowHover: 'shadow-xl shadow-black/30',

      // Scrollbar
      scrollbarBg: '#020617',
      scrollbarThumb: '#334155',
      scrollbarThumbHover: '#475569',
    }
  },

  // Pure White Theme (Updated for better contrast)
  light: {
    id: 'light',
    name: 'Pure White',
    description: 'Clean light theme with professional elegance',
    colors: {
      // Raw hex values for custom styling
      raw: {
        background: '#ffffff',
        backgroundAlt: '#f7fafc',
        surface: '#ffffff',
        surfaceHover: '#f7fafc',
        border: '#e2e8f0',
        textPrimary: '#1a202c',
        textSecondary: '#4a5568',
        textTertiary: '#718096',
        primary: '#5e72e4',
        primaryDark: '#324cdd',
        success: '#2dce89',
        warning: '#fb6340',
        danger: '#f5365c',
        info: '#11cdef',
      },

      // Background gradients
      bgPrimary: 'from-white via-slate-50 to-gray-50',
      bgSecondary: 'from-white/95 to-slate-50/95',
      bgTertiary: 'from-slate-50 to-gray-100',
      background: 'bg-white',

      // Surface colors
      surface: 'bg-white',
      surfaceHover: 'bg-slate-50',
      surfaceBorder: 'border-slate-200',

      // Text colors
      textPrimary: 'text-slate-900',
      textSecondary: 'text-slate-600',
      textTertiary: 'text-slate-500',

      // Primary accent (Professional Blue)
      primary: 'bg-gradient-to-r from-[#5e72e4] to-[#825ee4]',
      primarySolid: 'bg-[#5e72e4]',
      primaryHover: 'bg-gradient-to-r from-[#4c63d2] to-[#7048d2]',
      primaryText: 'text-[#5e72e4]',
      primaryBorder: 'border-[#5e72e4]',

      // Secondary accent
      secondary: 'bg-slate-200',
      secondaryHover: 'bg-slate-300',
      secondaryText: 'text-slate-700',

      // Status colors (vibrant but professional)
      success: 'bg-[#2dce89]',
      successText: 'text-[#2dce89]',
      successBorder: 'border-[#2dce89]',

      warning: 'bg-[#fb6340]',
      warningText: 'text-[#fb6340]',
      warningBorder: 'border-[#fb6340]',

      danger: 'bg-[#f5365c]',
      dangerText: 'text-[#f5365c]',
      dangerBorder: 'border-[#f5365c]',

      info: 'bg-[#11cdef]',
      infoText: 'text-[#11cdef]',
      infoBorder: 'border-[#11cdef]',

      // Sidebar gradient - Light Blue (Professional)
      sidebarGradient: 'from-[#3b82f6] to-[#2563eb]',

      // Shadows and glows
      shadow: 'shadow-lg shadow-slate-200',
      shadowHover: 'shadow-xl shadow-slate-300',

      // Scrollbar
      scrollbarBg: '#ffffff',
      scrollbarThumb: '#cbd5e0',
      scrollbarThumbHover: '#a0aec0',
    }
  },

  // Tokyo Free White Theme - Improved visibility
  tokyo: {
    id: 'tokyo',
    name: 'Tokyo Light',
    description: 'Clean modern light theme with blue accents',
    colors: {
      // Raw hex values - Improved for better visibility
      raw: {
        background: '#e8ecf1',          // Darker, less bright
        backgroundAlt: '#ffffff',       // white
        surface: '#ffffff',             // paper
        surfaceHover: '#f5f7fa',        // subtle hover
        border: 'rgba(34, 51, 84, 0.15)', // More visible borders
        textPrimary: '#1a2332',         // Darker for better contrast
        textSecondary: '#526080',       // Darker secondary
        textTertiary: '#6E759F',        // Visible tertiary
        primary: '#5569ff',             // primary
        primaryDark: '#000C57',         // primaryAlt
        success: '#57CA22',             // success
        warning: '#FFA319',             // warning
        danger: '#FF1943',              // error
        info: '#33C2FF',                // info
      },

      // Background gradients
      bgPrimary: 'from-[#e8ecf1] via-[#f0f3f7] to-[#e8ecf1]',
      bgSecondary: 'from-[#ffffff]/95 to-[#e8ecf1]/95',
      bgTertiary: 'from-[#ffffff] to-[#e8ecf1]',
      background: 'bg-[#e8ecf1]',

      // Surface colors
      surface: 'bg-white',
      surfaceHover: 'bg-[#f5f7fa]',
      surfaceBorder: 'border-gray-300',

      // Text colors - Better contrast
      textPrimary: 'text-[#1a2332]',
      textSecondary: 'text-[#526080]',
      textTertiary: 'text-[#6E759F]',

      // Primary accent (Blue)
      primary: 'bg-gradient-to-r from-[#5569ff] to-[#6B73FF]',
      primarySolid: 'bg-[#5569ff]',
      primaryHover: 'bg-[#4054ea]',
      primaryText: 'text-[#5569ff]',
      primaryBorder: 'border-[#5569ff]',

      // Secondary accent
      secondary: 'bg-[#526080]',
      secondaryHover: 'bg-[#3d4a63]',
      secondaryText: 'text-[#526080]',

      // Status colors
      success: 'bg-[#57CA22]',
      successText: 'text-[#57CA22]',
      successBorder: 'border-[#57CA22]',

      warning: 'bg-[#FFA319]',
      warningText: 'text-[#FFA319]',
      warningBorder: 'border-[#FFA319]',

      danger: 'bg-[#FF1943]',
      dangerText: 'text-[#FF1943]',
      dangerBorder: 'border-[#FF1943]',

      info: 'bg-[#33C2FF]',
      infoText: 'text-[#33C2FF]',
      infoBorder: 'border-[#33C2FF]',

      // Sidebar - Visible gradient with contrast
      sidebarGradient: 'from-[#ffffff] to-[#f5f8fb]',

      // Shadows - More visible
      shadow: 'shadow-lg shadow-gray-300/50',
      shadowHover: 'shadow-xl shadow-gray-400/50',

      // Scrollbar
      scrollbarBg: '#e8ecf1',
      scrollbarThumb: '#526080',
      scrollbarThumbHover: '#5569ff',
    }
  },
};

export const defaultTheme = 'dark';
