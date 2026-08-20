import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

// Tests unitaires du front. Volontairement minimal : pas de plugin React, on ne
// teste ici que de la logique pure (le client d'API). Les ecrans se verifient
// dans un navigateur, pas dans un DOM simule.
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    include: ["src/**/*.test.ts"],
  },
});
