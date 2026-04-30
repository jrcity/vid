/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
        mono: ['Space Grotesk', 'monospace'],
      },
      colors: {
        brand: {
          dark: "#050505",    // Sleek Black
          accent: "#D4AF37",  // Rich Gold
          muted: "#1A1A1A",   // Charcoal Slate
        },
      },
      borderRadius: {
        'native': '24px',     // iOS-style rounded corners
      },
      boxShadow: {
        'premium': '0 10px 30px -5px rgba(0, 0, 0, 0.3)',
      },
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.5s infinite',
      },
    },
  },
  plugins: [],
}
