import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { themes, defaultTheme } from '../config/themes';

const useThemeStore = create(
  persist(
    (set, get) => ({
      // Current theme ID
      currentTheme: defaultTheme,

      // Get current theme object
      theme: themes[defaultTheme],

      // Set theme by ID
      setTheme: (themeId) => {
        if (themes[themeId]) {
          set({
            currentTheme: themeId,
            theme: themes[themeId],
          });

          // Update scrollbar colors and data-theme attribute
          const theme = themes[themeId];
          const root = document.documentElement;
          if (theme && theme.colors) {
            root.style.setProperty('--scrollbar-bg', theme.colors.scrollbarBg);
            root.style.setProperty('--scrollbar-thumb', theme.colors.scrollbarThumb);
            root.style.setProperty('--scrollbar-thumb-hover', theme.colors.scrollbarThumbHover);
            root.setAttribute('data-theme', themeId);
          }
        }
      },

      // Get all available themes
      getAvailableThemes: () => Object.values(themes),

      // Initialize theme on app load
      initializeTheme: () => {
        const { currentTheme } = get();
        const theme = themes[currentTheme] || themes[defaultTheme];

        // Set CSS variables for scrollbar and data-theme attribute
        const root = document.documentElement;
        if (theme && theme.colors) {
          root.style.setProperty('--scrollbar-bg', theme.colors.scrollbarBg);
          root.style.setProperty('--scrollbar-thumb', theme.colors.scrollbarThumb);
          root.style.setProperty('--scrollbar-thumb-hover', theme.colors.scrollbarThumbHover);
          root.setAttribute('data-theme', currentTheme);
        }
      },
    }),
    {
      name: 'contractai-theme',
      partialize: (state) => ({
        currentTheme: state.currentTheme,
      }),
    }
  )
);

export default useThemeStore;
