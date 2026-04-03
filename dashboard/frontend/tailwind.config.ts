import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#000000",
        surface: "#111111",
        "surface-2": "#1a1a1a",
        border: "#333333",
        "border-subtle": "#222222",
        primary: "#ffffff",
        secondary: "#888888",
        muted: "#555555",
        accent: "#00dc82",
        "accent-hover": "#00b36a",
        buy: "#00dc82",
        sell: "#ef4444",
        "chart-close": "#ffffff",
        "chart-blue": "#3b82f6",
        "chart-amber": "#f59e0b",
        "chart-purple": "#8b5cf6",
        "chart-slate": "#64748b",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
      },
      animation: {
        "pulse-subtle": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
