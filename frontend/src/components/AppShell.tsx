"use client";

import { useEffect, useState } from "react";
import { chargerContexte, MODE_FIXTURES } from "@/lib/api";
import type { Contexte } from "@/lib/api/types";

/**
 * Cadre de l'application : en-tete, largeur de lecture, et les deux bandeaux
 * qui doivent etre vus AVANT le contenu (mode demo, donnees de demonstration).
 *
 * Pas de barre de navigation tant qu'il n'y a qu'un ecran : un onglet grise
 * « bientot » est une promesse, donc une dette (contrat, derniere section).
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [contexte, setContexte] = useState<Contexte | null>(null);
  const [backendInjoignable, setBackendInjoignable] = useState(false);

  useEffect(() => {
    chargerContexte()
      .then(setContexte)
      .catch(() => setBackendInjoignable(true));
  }, []);

  return (
    <div className="min-h-screen bg-fond">
      <header className="border-b border-bordure bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-4 sm:px-6">
          <span className="text-lg font-semibold tracking-tight">FlexoSuite</span>
          <span className="text-sm text-texte-doux">
            Optimisation de pose et chiffrage
          </span>
        </div>
      </header>

      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 sm:px-6">
        {MODE_FIXTURES ? (
          <p className="rounded-md border border-attention/40 bg-attention-doux px-3 py-2 text-sm">
            <strong>Donnees de demonstration.</strong> Les configurations et les
            prix affiches sont fictifs : les endpoints correspondants ne sont pas
            encore livres. Rien de ce qui s&apos;affiche ici ne vient de votre
            atelier.
          </p>
        ) : null}

        {contexte?.mode_demo ? (
          <p className="rounded-md border border-bordure bg-accent-doux px-3 py-2 text-sm">
            <strong>Mode demonstration.</strong> La consultation est libre,
            l&apos;enregistrement est desactive.
          </p>
        ) : null}

        {backendInjoignable ? (
          <p className="rounded-md border border-attention/40 bg-attention-doux px-3 py-2 text-sm">
            <strong>Serveur injoignable.</strong> L&apos;application ne peut pas
            joindre son service. Verifiez qu&apos;il est demarre, puis rechargez
            la page.
          </p>
        ) : null}

        {children}
      </div>
    </div>
  );
}
