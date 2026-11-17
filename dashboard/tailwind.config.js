/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#080808',
          sidebar: '#0A0A0A',
          topnav: '#0D0D0D',
          card: '#111111',
          elevated: '#171717',
          input: '#141414',
          border: '#262626',
          borderHover: '#383838',
          accent: '#2D63C9',
          accentHover: '#2455B3',
          accentLight: '#3B82F6',
          secondary: '#89B4FF',
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#EF4444',
          textPrimary: '#FFFFFF',
          textSecondary: '#A1A1AA',
          textMuted: '#71717A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0, 0, 0, 0.6), 0 1px 2px -1px rgba(0, 0, 0, 0.6)',
        glow: '0 2px 8px -1px rgba(45, 99, 201, 0.3)',
        glowSuccess: '0 2px 8px -1px rgba(16, 185, 129, 0.3)',
      },
    },
  },
  plugins: [],
};
