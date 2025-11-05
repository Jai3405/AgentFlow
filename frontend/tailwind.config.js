/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'beige': {
          100: '#f5f2ee',
          200: '#e8e3dd',
          300: '#d4cfc7',
          400: '#c8c3bb',
          500: '#b5b0a7',
          600: '#9a9590',
        }
      },
      animation: {
        'fadeIn': 'fadeIn 0.3s ease',
        'slideIn': 'slideIn 0.4s ease',
        'bounce': 'bounce 1.4s infinite ease-in-out both',
        'shimmer': 'shimmer 2s infinite',
      },
      keyframes: {
        fadeIn: {
          'from': { 
            opacity: '0', 
            transform: 'translateY(10px)' 
          },
          'to': { 
            opacity: '1', 
            transform: 'translateY(0)' 
          }
        },
        slideIn: {
          'from': { 
            opacity: '0', 
            transform: 'translateX(-20px)' 
          },
          'to': { 
            opacity: '1', 
            transform: 'translateX(0)' 
          }
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' }
        }
      },
      backdropBlur: {
        xs: '2px',
      },
      fontFamily: {
        'inter': ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}