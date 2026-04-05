/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        md: {
          primary: "var(--color-primary)",
          black: "var(--color-black)",
          purple: "var(--color-purple)",
          orange: "var(--color-orange)",
          blue: "var(--color-blue)",
          green: "var(--color-green)",
          muted: "var(--color-bg-muted)",
          page: "var(--color-bg-page)",
          border: "var(--color-border)",
          secondary: "var(--color-text-secondary)",
        },
      },
      maxWidth: {
        layout: "var(--layout-max)",
        "layout-wide": "var(--layout-max-wide)",
      },
      spacing: {
        sidebar: "var(--layout-sidebar)",
      },
      borderRadius: {
        md: "var(--radius-md)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
    },
  },
  plugins: [],
};
