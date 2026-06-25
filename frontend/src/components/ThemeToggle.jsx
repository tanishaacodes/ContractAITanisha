import { Sun, Moon } from 'lucide-react';
import useThemeStore from '../store/themeStore';

const ThemeToggle = () => {
  const { currentTheme, setTheme, theme } = useThemeStore();

  const toggleTheme = () => {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  const isDark = currentTheme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className={`
        relative flex items-center justify-center
        w-10 h-10 rounded-lg
        ${theme.colors.surface} ${theme.colors.surfaceBorder} border
        hover:${theme.colors.surfaceHover}
        transition-all duration-200
        ${theme.colors.shadow}
        group
      `}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {isDark ? (
        <Sun
          size={20}
          className={`${theme.colors.textPrimary} transition-transform group-hover:rotate-45`}
        />
      ) : (
        <Moon
          size={20}
          className={`${theme.colors.textPrimary} transition-transform group-hover:-rotate-12`}
        />
      )}
    </button>
  );
};

export default ThemeToggle;
