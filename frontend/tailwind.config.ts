import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1120",
        panel: "#111a2f",
        panel2: "#17233c",
        line: "rgba(255,255,255,0.08)",
        accent: "#7dd3fc",
        accent2: "#f59e0b",
      },
      boxShadow: {
        soft: "0 20px 60px rgba(0,0,0,0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
