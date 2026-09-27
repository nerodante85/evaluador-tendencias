import { defineConfig } from "vitest/config";

// Pruebas del motor de decisión (src/engine.js, src/engineV2.js): lógica
// pura, sin componentes React — no hace falta jsdom ni el plugin de React
// para esto, solo el pipeline de transformación de Vite (incluido el
// soporte nativo de imports de JSON que ya usan ambos motores).
export default defineConfig({
  test: {
    environment: "node",
  },
});
