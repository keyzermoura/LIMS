import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Separa bibliotecas de terceiros do código da aplicação: melhora o
        // cache entre deploys e evita um único chunk acima do limite do Vite.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          data: [
            "@tanstack/react-query",
            "zod",
            "react-hook-form",
            "@hookform/resolvers",
          ],
          ui: [
            "@radix-ui/react-dialog",
            "@radix-ui/react-label",
            "@radix-ui/react-select",
            "@radix-ui/react-slot",
            "lucide-react",
            "class-variance-authority",
            "clsx",
            "tailwind-merge",
          ],
        },
      },
    },
  },
});
