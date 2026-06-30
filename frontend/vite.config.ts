import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    // HMR a través del puerto publicado en el host (remapeado en Docker).
    hmr: process.env.VITE_HMR_PORT
      ? { clientPort: Number(process.env.VITE_HMR_PORT) }
      : undefined,
    proxy: {
      // En dev, redirige las llamadas /api al backend FastAPI.
      // En Docker el backend es accesible como host "backend".
      "/api": {
        target: process.env.VITE_API_PROXY || "http://localhost:18080",
        changeOrigin: true,
      },
    },
  },
});
