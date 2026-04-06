/// <reference types="vitest/config" />

import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@site": path.resolve(__dirname, "../site"),
    },
  },
  server: {
    port: 3000,
    host: true,
  },
  optimizeDeps: {
    include: ["monaco-editor"],
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
  },
});
