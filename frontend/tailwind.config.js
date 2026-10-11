/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0F1420",
        surface: "#161C2C",
        surfacealt: "#1E2638",
        border: "#2A3348",
        text: "#E7EAF2",
        muted: "#8891A6",
        amber: {
          DEFAULT: "#E8A33D",
          dim: "#8A6425",
        },
        mint: {
          DEFAULT: "#3ECF8E",
          dim: "#1F6B49",
        },
        coral: {
          DEFAULT: "#F2555A",
          dim: "#7A2A2D",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        sans: ["Inter", "sans-serif"],
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
};
