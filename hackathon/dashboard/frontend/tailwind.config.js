/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-dark': '#0f172a',   // steel blue 900
        'brand-mid': '#1e293b',    // steel blue 800
        'brand-accent': '#38bdf8', // cyan 400
      },
    },
  },
  darkMode: 'class',
  plugins: [],
}