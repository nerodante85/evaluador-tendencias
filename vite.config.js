import { resolve } from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  // Rutas relativas: así el sitio funciona igual en GitHub Pages
  // (usuario.github.io/evaluador-tendencias/) que abriendo el build local,
  // sin tener que escribir el nombre del repositorio en ningún lado.
  base: "./",
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      // Segundo punto de entrada para Radar 2.0 (v2.html / src/main-v2.jsx),
      // sin tocar el index.html ni el main.jsx de la v1. Los dos quedan
      // publicados juntos en dist/ y GitHub Pages los sirve a ambos.
      input: {
        main: resolve(__dirname, "index.html"),
        v2: resolve(__dirname, "v2.html"),
      },
    },
  },
});
