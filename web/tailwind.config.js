/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['Berkeley Mono', 'SF Mono', 'Fira Code', 'JetBrains Mono', 'Cascadia Code', 'monospace'],
      },
      colors: {
        terminal: {
          green: '#00ff00',
          red: '#ff6b6b',
          cyan: '#4ecdc4',
          dark: '#000000',
          darkBg: '#111111',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'typing': 'typing 1.5s steps(30, end), blink-caret 0.75s step-end infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        typing: {
          'from': { width: '0' },
          'to': { width: '100%' },
        },
        'blink-caret': {
          'from, to': { borderColor: 'transparent' },
          '50%': { borderColor: 'currentColor' },
        },
      },
    },
  },
  plugins: [],
}