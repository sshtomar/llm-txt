import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#0b0b0c',
          panel: '#111111',
          border: '#222222',
          text: '#eaeaea',
          // Soothing dev-friendly green (Tailwind green-500)
          green: '#22c55e',
          teal: '#14b8a6',
          red: '#ff6b6b',
          yellow: '#f7d154',
        }
      },
      fontFamily: {
        mono: [
          'Berkeley Mono',
          'SF Mono',
          'Fira Code',
          'JetBrains Mono',
          'Cascadia Code',
          'ui-monospace',
          'Menlo',
          'Monaco',
          'Consolas',
          'Liberation Mono',
          'monospace',
        ]
      }
    },
  },
  plugins: [],
} satisfies Config
