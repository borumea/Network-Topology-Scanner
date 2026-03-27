import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      colors: {
        bg: {
          primary: '#111113',
          secondary: '#19191B',
          tertiary: '#222225',
          surface: '#19191B',
        },
        text: {
          primary: '#ECECED',
          secondary: '#8B8B8E',
          muted: '#5C5C5F',
        },
        accent: {
          DEFAULT: '#6366F1',
          light: '#818CF8',
          muted: '#4F46E5',
        },
        node: {
          router: '#818CF8',
          switch: '#60A5FA',
          server: '#34D399',
          firewall: '#FBBF24',
          ap: '#A78BFA',
          workstation: '#94A3B8',
          iot: '#F472B6',
          unknown: '#5C5C5F',
          printer: '#FB923C',
        },
        status: {
          online: '#34D399',
          offline: '#F87171',
          degraded: '#FBBF24',
          new: '#60A5FA',
        },
        risk: {
          low: '#34D399',
          medium: '#FBBF24',
          high: '#FB923C',
          critical: '#F87171',
        },
        edge: {
          ethernet: '#3F3F46',
          fiber: '#818CF8',
          wireless: '#A78BFA',
          vpn: '#FBBF24',
          virtual: '#8B8B8E',
        },
        border: {
          DEFAULT: '#27272A',
          light: '#2E2E32',
        },
      },
      animation: {
        'slide-in-right': 'slide-in-right 0.2s ease-out',
        'slide-in-top': 'slide-in-top 0.25s ease-out',
        'fade-in': 'fade-in 0.15s ease-out',
      },
      keyframes: {
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-in-top': {
          '0%': { transform: 'translateY(-8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
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
