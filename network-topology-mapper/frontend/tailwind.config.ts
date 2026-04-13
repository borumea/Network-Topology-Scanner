import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Doto', 'Space Mono', 'monospace'],
        sans: ['Space Grotesk', 'DM Sans', 'system-ui', 'sans-serif'],
        mono: ['Space Mono', 'JetBrains Mono', 'SF Mono', 'monospace'],
      },
      fontSize: {
        'display-xl': ['72px', { lineHeight: '1.0', letterSpacing: '-0.03em' }],
        'display-lg': ['48px', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        'display-md': ['36px', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'heading': ['24px', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        'subheading': ['18px', { lineHeight: '1.3', letterSpacing: '0' }],
        'body': ['16px', { lineHeight: '1.5', letterSpacing: '0' }],
        'body-sm': ['14px', { lineHeight: '1.5', letterSpacing: '0.01em' }],
        'caption': ['12px', { lineHeight: '1.4', letterSpacing: '0.04em' }],
        'label': ['11px', { lineHeight: '1.2', letterSpacing: '0.08em' }],
      },
      colors: {
        nd: {
          black: 'var(--nd-black)',
          surface: 'var(--nd-surface)',
          'surface-raised': 'var(--nd-surface-raised)',
          border: 'var(--nd-border)',
          'border-visible': 'var(--nd-border-visible)',
          'text-disabled': 'var(--nd-text-disabled)',
          'text-secondary': 'var(--nd-text-secondary)',
          'text-primary': 'var(--nd-text-primary)',
          'text-display': 'var(--nd-text-display)',
          accent: '#D71921',
          'accent-subtle': 'rgba(215,25,33,0.15)',
          success: '#4A9E5C',
          warning: '#D4A843',
          interactive: '#007AFF',
        },
      },
      spacing: {
        'nd-2xs': '2px',
        'nd-xs': '4px',
        'nd-sm': '8px',
        'nd-md': '16px',
        'nd-lg': '24px',
        'nd-xl': '32px',
        'nd-2xl': '48px',
        'nd-3xl': '64px',
        'nd-4xl': '96px',
      },
      borderRadius: {
        'nd-technical': '4px',
        'nd-compact': '8px',
        'nd-card': '12px',
        'nd-pill': '999px',
      },
      animation: {
        'fade-in': 'fade-in 0.15s cubic-bezier(0.25, 0.1, 0.25, 1)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

export default config
