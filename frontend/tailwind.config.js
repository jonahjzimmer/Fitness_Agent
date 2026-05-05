/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#FFF3EE',
          400: '#FD6C2E',
          500: '#FC4C02',
          600: '#E34902',
          700: '#CC4100',
        },
      },
    },
  },
  plugins: [],
}
