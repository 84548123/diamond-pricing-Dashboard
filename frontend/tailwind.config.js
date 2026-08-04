/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      colors: {
        dark: { 50: '#f8fafc', 100: '#e2e8f0', 200: '#cbd5e1', 300: '#94a3b8', 400: '#64748b', 500: '#475569', 600: '#334155', 700: '#1e293b', 800: '#0f172a', 900: '#020617', 950: '#010313' },
        brand: { 50: '#f0f0ff', 100: '#dcdcff', 200: '#b4b4ff', 300: '#8b8bff', 400: '#6366f1', 500: '#4f46e5', 600: '#4338ca', 700: '#3730a3', 800: '#312e81', 900: '#1e1b4b' },
        accent: { cyan: '#22d3ee', emerald: '#34d399', amber: '#fbbf24', rose: '#fb7185' },
      },
      animation: { 'pulse-slow': 'pulse 3s ease-in-out infinite', 'slide-up': 'slideUp 0.3s ease-out', 'fade-in': 'fadeIn 0.5s ease-out' },
      keyframes: { slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } }, fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } } },
    },
  },
  plugins: [],
}
