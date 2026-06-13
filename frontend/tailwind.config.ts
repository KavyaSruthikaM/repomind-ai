import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#07090f",
        card: "#0f1220",
        border: "#1d2234",
        foreground: "#f4f6ff",
        muted: "#9aa2c0",
        accent: "#6d7dff"
      },
      borderRadius: {
        lg: "0.9rem"
      }
    }
  },
  plugins: []
};

export default config;
