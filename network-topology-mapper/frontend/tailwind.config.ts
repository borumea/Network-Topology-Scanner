import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0B0D13', // Deep, rich dark background (Google Cloud Console style)
          secondary: '#161922', // Slightly lighter panel background
          tertiary: '#212530', // Borders and secondary elements
        },
        text: {
          primary: '#F0F4F8', // High contrast text
          secondary: '#94A3B8', // Muted text (Slate-400)
          muted: '#64748B', // Very muted text (Slate-500)
        },
        node: {
          router: '#818CF8', // Indigo-400
          switch: '#60A5FA', // Blue-400
          server: '#34D399', // Emerald-400
          firewall: '#FBBF24', // Amber-400
          ap: '#A78BFA', // Violet-400
          workstation: '#94A3B8', // Slate-400
          iot: '#F472B6', // Pink-400
          unknown: '#6B7280', // Gray-500
          printer: '#FB923C', // Orange-400
        },
        status: {
          online: '#34D399', // Emerald-400
          offline: '#F87171', // Red-400
          degraded: '#FBBF24', // Amber-400
          new: '#60A5FA', // Blue-400
        },
        risk: {
          low: '#34D399',
          medium: '#FBBF24',
          high: '#FB923C',
          critical: '#F87171',
        },
        edge: {
          ethernet: '#475569',
          fiber: '#818CF8',
          wireless: '#A78BFA',
          vpn: '#FBBF24',
          virtual: '#94A3B8',
        },
      },
      animation: {
        'pulse-blue': 'pulse-blue 1.5s ease-in-out infinite',
        'risk-pulse': 'risk-pulse 2s ease-in-out infinite',
        'slide-in-right': 'slide-in-right 0.2s ease-out',
        'slide-in-top': 'slide-in-top 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-out',
      },
      keyframes: {
        'pulse-blue': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(59, 130, 246, 0.4)' },
          '50%': { boxShadow: '0 0 0 12px rgba(59, 130, 246, 0)' },
        },
        'risk-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-in-top': {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
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
