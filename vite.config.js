import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  // Rutas relativas: así el sitio funciona igual en GitHub Pages
  // (usuario.github.io/evaluador-tendencias/) que abriendo el build local,
  // sin tener que escribir el nombre del repositorio en ningún lado.
  base: "./",
  plugins: [react(), tailwindcss()],
});
