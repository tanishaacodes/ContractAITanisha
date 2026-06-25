# Theme System - Quick Start Guide

## 🎨 What's New?

Your ContractAI application now has a powerful theme configuration system with **6 beautiful themes** that users can switch between instantly!

## 🚀 For Users

### How to Change Your Theme:

1. **Navigate to Settings**
   - Click on your profile
   - Select "Settings" from the menu

2. **Choose Your Theme**
   - Scroll to the "Theme Customization" section
   - Click on any theme card to preview and apply it
   - Your choice is saved automatically!

### Available Themes:

| Theme | Description | Best For |
|-------|-------------|----------|
| 🌙 **Dark Night** | Professional dark theme with blue accents | Default, general use |
| ☀️ **Clean Light** | Crisp light theme with subtle gradients | Bright environments |
| 🌊 **Ocean Depths** | Deep ocean theme with cyan highlights | Cool color lovers |
| 🌅 **Sunset Glow** | Warm purple and orange tones | Evening work |
| 🌲 **Forest Green** | Calm green accents | Long reading sessions |
| 🌑 **Midnight** | Ultra-dark with minimal distractions | Late night, OLED screens |

## 👨‍💻 For Developers

### Quick Integration in Components:

```jsx
import useThemeStore from '../store/themeStore';

function MyComponent() {
  const { theme } = useThemeStore();

  return (
    <div className={`${theme.colors.surface} ${theme.colors.surfaceBorder}`}>
      <h1 className={theme.colors.textPrimary}>Title</h1>
      <p className={theme.colors.textSecondary}>Description</p>
      <button className={`${theme.colors.primary} hover:${theme.colors.primaryHover} text-white`}>
        Button
      </button>
    </div>
  );
}
```

### Common Patterns:

#### Background Gradients
```jsx
<div className={`bg-gradient-to-br ${theme.colors.bgPrimary}`}>
```

#### Cards
```jsx
<div className={`${theme.colors.surface} rounded-xl border ${theme.colors.surfaceBorder} p-6`}>
```

#### Buttons
```jsx
<button className={`${theme.colors.primary} hover:${theme.colors.primaryHover} text-white px-6 py-3 rounded-lg`}>
```

#### Text
```jsx
<h1 className={theme.colors.textPrimary}>Primary Text</h1>
<p className={theme.colors.textSecondary}>Secondary Text</p>
```

#### Status Colors
```jsx
<span className={`${theme.colors.success} text-white px-3 py-1 rounded-full`}>Success</span>
<span className={`${theme.colors.warning} text-white px-3 py-1 rounded-full`}>Warning</span>
<span className={`${theme.colors.danger} text-white px-3 py-1 rounded-full`}>Error</span>
```

### Switching Themes Programmatically:

```jsx
const { setTheme } = useThemeStore();

// Switch to ocean theme
setTheme('ocean');

// Get current theme
const { currentTheme } = useThemeStore();
console.log(currentTheme); // e.g., 'dark'
```

### List All Themes:

```jsx
const { getAvailableThemes } = useThemeStore();
const allThemes = getAvailableThemes();

allThemes.forEach(theme => {
  console.log(theme.id, theme.name, theme.description);
});
```

## 📁 File Structure

```
frontend/
├── src/
│   ├── config/
│   │   └── themes.js          # Theme definitions
│   ├── store/
│   │   └── themeStore.js      # Zustand store
│   ├── pages/
│   │   └── Settings.jsx       # Theme switcher UI
│   ├── components/
│   │   └── ThemeExample.jsx   # Usage example
│   └── index.css              # CSS variables
└── THEME_QUICK_START.md       # This file
```

## ✨ Key Features

- ✅ 6 professionally designed themes
- ✅ Instant theme switching
- ✅ Persistent user preferences (localStorage)
- ✅ Custom scrollbar colors per theme
- ✅ Beautiful theme selector UI
- ✅ Fully responsive
- ✅ Zero configuration needed

## 🎯 Best Practices

1. **Use theme colors everywhere** - Don't hardcode color classes
2. **Test all themes** - Ensure components look good in all themes
3. **Semantic naming** - Use `primary`, `success`, etc. instead of specific colors
4. **Accessibility** - All themes maintain proper contrast ratios

## 🐛 Troubleshooting

**Theme not saving?**
- Check browser localStorage is enabled
- Clear cache and try again

**Colors not changing?**
- Make sure you're using `theme.colors.x` not hardcoded classes
- Verify `useThemeStore` is imported

**Need help?**
- Check `THEME_SYSTEM.md` for detailed documentation
- See `ThemeExample.jsx` for usage examples

## 🔮 Coming Soon

- Custom theme builder
- Import/export themes
- System theme detection (auto dark/light)
- Animated theme transitions

---

**Enjoy customizing your ContractAI experience!** 🎨
