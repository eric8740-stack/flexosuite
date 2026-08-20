"use client";

import { useEffect, useState } from "react";
import { appel } from "@/lib-api";

export default function Accueil() {
  const [statut, setStatut] = useState<string>("verification...");

  useEffect(() => {
    appel<{ statut: string }>("/sante")
      .then((d) => setStatut(d.statut === "ok" ? "en ligne" : d.statut))
      .catch(() => setStatut("injoignable"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui", padding: "3rem", lineHeight: 1.6 }}>
      <h1>FlexoSuite</h1>
      <p>Devis pour imprimeurs flexographiques.</p>
      <p>
        Backend : <strong>{statut}</strong>
      </p>
    </main>
  );
}
