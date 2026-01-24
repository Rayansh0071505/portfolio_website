/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      colors: {
        primary: {
          blue: '#3b82f6',
          teal: '#14b8a6',
          cyan: '#06b6d4',
        },
        accent: {
          purple: '#8b5cf6',
          pink: '#ec4899',
        },
      },
      animation: {
        'gradient': 'gradient 8s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'rotate-slow': 'rotate 20s linear infinite',
        'rotate-border': 'rotate-border 8s linear infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 3s infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        glow: {
          from: { boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)' },
          to: { boxShadow: '0 0 20px rgba(59, 130, 246, 0.8)' },
        },
        'glow-pulse': {
          '0%, 100%': {
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.4), 0 0 40px rgba(20, 184, 166, 0.2)'
          },
          '50%': {
            boxShadow: '0 0 40px rgba(59, 130, 246, 0.6), 0 0 60px rgba(20, 184, 166, 0.4)'
          },
        },
        rotate: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'rotate-border': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      transitionTimingFunction: {
        'bounce-in': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
    },
  },
  plugins: [],
};
