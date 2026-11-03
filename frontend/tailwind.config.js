/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        claude: {
          canvas: '#faf9f5',
          'surface-soft': '#f5f0e8',
          'surface-card': '#efe9de',
          'surface-cream-strong': '#e8e0d2',
          'surface-dark': '#181715',
          'surface-dark-elevated': '#252320',
          'surface-dark-soft': '#1f1e1b',
          primary: '#cc785c',
          'primary-active': '#a9583e',
          'primary-disabled': '#e6dfd8',
          ink: '#141413',
          body: '#3d3d3a',
          'body-strong': '#252523',
          muted: '#6c6a64',
          'muted-soft': '#8e8b82',
          hairline: '#e6dfd8',
          'hairline-soft': '#ebe6df',
          'on-primary': '#ffffff',
          'on-dark': '#faf9f5',
          'on-dark-soft': '#a09d96',
          teal: '#5db8a6',
          amber: '#e8a55a',
          success: '#5db872',
          warning: '#d4a017',
          error: '#c64545',
        },
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Tiempos Headline', 'Copernicus', 'Georgia', 'serif'],
        sans: ['Inter', 'StyreneB', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'monospace'],
      },
      borderRadius: {
        'claude-xs': '4px',
        'claude-sm': '6px',
        'claude-md': '8px',
        'claude-lg': '12px',
        'claude-xl': '16px',
      },
      boxShadow: {
        'claude-card': '0 1px 3px rgba(20, 20, 19, 0.04), 0 1px 2px rgba(20, 20, 19, 0.02)',
        'claude-elevated': '0 4px 16px rgba(20, 20, 19, 0.08)',
        'claude-dark': '0 12px 36px -4px rgba(0, 0, 0, 0.5)',
      },
    },
  },
  plugins: [],
};
