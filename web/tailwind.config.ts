import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f3efe6",
        card: "#fffdf8",
        ink: "#1c2430",
        muted: "#5c6670",
        line: "#e4d9c8",
        teal: "#0f5c56",
        deep: "#0c3330",
        clay: "#b5522a",
      },
      fontFamily: {
        serif: ["Iowan Old Style", "Palatino Linotype", "Palatino", "Songti SC", "Noto Serif CJK SC", "Source Han Serif SC", "serif"],
        sans: ["Avenir Next", "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei", "sans-serif"],
      },
      maxWidth: { page: "1120px" },
    },
  },
  plugins: [],
};

export default config;
