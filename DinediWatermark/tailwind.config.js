/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        /* M3 Light Theme + Golden dominant */
        surface: {
          bg: "#FEF3C7", // Amber 50 - Light golden background
          paper: "#FAFAF9", // Stone 50
          glass: "rgba(255, 255, 255, 0.7)",
          "glass-heavy": "rgba(255, 255, 255, 0.9)",
        },
        primary: {
          DEFAULT: "#D97706", // Amber 600 - Main active elements
          light: "#F59E0B",
          dark: "#B45309",
          container: "#FEF08A", // Amber 200
          "on-container": "#78350F", // Amber 900
        },
        secondary: {
          DEFAULT: "#0F172A", // Slate 900 - High contrast text
          light: "#334155", // Slate 700 - Subtext
        },
        accent: {
          DEFAULT: "#2563EB", // Blue 600
          container: "#DBEAFE", // Blue 100
        }
      },
      fontFamily: {
        primary: ['"Outfit"', 'system-ui', 'sans-serif'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(217, 119, 6, 0.1)',
        'glass-hover': '0 12px 48px 0 rgba(217, 119, 6, 0.2)',
        '3d': '0 20px 40px -10px rgba(15, 23, 42, 0.15), 0 10px 20px -5px rgba(15, 23, 42, 0.1)',
        'inner-light': 'inset 0 2px 4px 0 rgba(255, 255, 255, 0.8)',
      },
      animation: {
        'float-slow': 'float 8s ease-in-out infinite',
        'float-fast': 'float 4s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0) rotate(0)' },
          '50%': { transform: 'translateY(-15px) rotate(2deg)' },
        }
      }
    },
  },
  plugins: [],
};
 