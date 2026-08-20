import type { NextConfig } from "next";

// Livraison locale (deploy/windows) : `NEXT_OUTPUT=export` produit un EXPORT
// STATIQUE (dossier `out/`) servi directement par le backend FastAPI, sans Node
// au runtime. Sans cette variable, comportement inchange (dev, deploiement
// Linux). `trailingSlash` + `images.unoptimized` sont REQUIS pour servir
// l'export depuis un hote statique generique.
const exportStatique = process.env.NEXT_OUTPUT === "export";

const nextConfig: NextConfig = {
  ...(exportStatique
    ? {
        output: "export",
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {}),
};

export default nextConfig;
