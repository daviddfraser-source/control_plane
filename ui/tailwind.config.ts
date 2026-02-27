import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        token: {
          primary: "var(--primary)",
          "primary-50": "var(--primary-50)",
          "primary-100": "var(--primary-100)",
          "primary-200": "var(--primary-200)",
          "primary-300": "var(--primary-300)",
          "primary-400": "var(--primary-400)",
          "primary-500": "var(--primary-500)",
          "primary-600": "var(--primary-600)",
          "primary-700": "var(--primary-700)",
          "primary-800": "var(--primary-800)",
          "primary-900": "var(--primary-900)",

          success: "var(--success)",
          "success-50": "var(--success-50)",
          "success-100": "var(--success-100)",
          "success-200": "var(--success-200)",
          "success-500": "var(--success-500)",
          "success-600": "var(--success-600)",
          "success-700": "var(--success-700)",

          warning: "var(--warning)",
          "warning-50": "var(--warning-50)",
          "warning-100": "var(--warning-100)",
          "warning-200": "var(--warning-200)",
          "warning-500": "var(--warning-500)",
          "warning-600": "var(--warning-600)",
          "warning-700": "var(--warning-700)",

          danger: "var(--danger)",
          "danger-50": "var(--danger-50)",
          "danger-100": "var(--danger-100)",
          "danger-200": "var(--danger-200)",
          "danger-500": "var(--danger-500)",
          "danger-600": "var(--danger-600)",
          "danger-700": "var(--danger-700)",
        }
      }
    },
  },
  plugins: [],
};

export default config;
