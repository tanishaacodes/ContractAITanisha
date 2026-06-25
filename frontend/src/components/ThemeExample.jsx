import useThemeStore from '../store/themeStore';

/**
 * Theme Usage Example Component
 *
 * This component demonstrates how to use the theme system throughout your application.
 * You can use this as a reference for applying themes to any component.
 */

const ThemeExample = () => {
  const { theme } = useThemeStore();

  return (
    <div className={`min-h-screen bg-gradient-to-br ${theme.colors.bgPrimary} p-8`}>
      {/* Card with theme colors */}
      <div className={`${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder} p-6 max-w-4xl mx-auto`}>

        {/* Header */}
        <h1 className={`text-3xl font-bold ${theme.colors.textPrimary} mb-2`}>
          Theme System Example
        </h1>
        <p className={`${theme.colors.textSecondary} mb-6`}>
          This demonstrates how to use the dynamic theme system
        </p>

        {/* Buttons */}
        <div className="flex gap-4 mb-8">
          <button className={`${theme.colors.primary} hover:${theme.colors.primaryHover} text-white px-6 py-3 rounded-lg font-semibold transition`}>
            Primary Button
          </button>
          <button className={`${theme.colors.secondary} hover:${theme.colors.secondaryHover} text-white px-6 py-3 rounded-lg font-semibold transition`}>
            Secondary Button
          </button>
        </div>

        {/* Status Badges */}
        <div className="flex gap-3 mb-8">
          <span className={`${theme.colors.success} text-white px-4 py-2 rounded-lg text-sm font-medium`}>
            Success
          </span>
          <span className={`${theme.colors.warning} text-white px-4 py-2 rounded-lg text-sm font-medium`}>
            Warning
          </span>
          <span className={`${theme.colors.danger} text-white px-4 py-2 rounded-lg text-sm font-medium`}>
            Danger
          </span>
          <span className={`${theme.colors.info} text-white px-4 py-2 rounded-lg text-sm font-medium`}>
            Info
          </span>
        </div>

        {/* Text variations */}
        <div className="space-y-2">
          <p className={theme.colors.textPrimary}>Primary text color</p>
          <p className={theme.colors.textSecondary}>Secondary text color</p>
          <p className={theme.colors.textTertiary}>Tertiary text color</p>
          <p className={theme.colors.primaryText}>Accent text color</p>
        </div>

        {/* Card with hover effect */}
        <div className={`mt-6 p-4 ${theme.colors.surfaceHover} rounded-lg border ${theme.colors.surfaceBorder} hover:${theme.colors.shadow} transition-all cursor-pointer`}>
          <h3 className={`${theme.colors.textPrimary} font-semibold mb-2`}>Interactive Card</h3>
          <p className={theme.colors.textSecondary}>This card changes on hover using theme colors</p>
        </div>
      </div>
    </div>
  );
};

export default ThemeExample;
