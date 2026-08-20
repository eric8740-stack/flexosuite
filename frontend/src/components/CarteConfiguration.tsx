"use client";

import { Alertes } from "./Alertes";
import { coefficient, entier, mm, pourcent } from "@/lib/format";
import type { Configuration } from "@/lib/api/types";

function Fait({ libelle, valeur }: { libelle: string; valeur: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs uppercase tracking-wide text-texte-doux">
        {libelle}
      </dt>
      <dd className="text-sm font-medium tabular-nums">{valeur}</dd>
    </div>
  );
}

/**
 * Une configuration realisable avec le parc existant.
 *
 * Le rang vient du backend et le tri est deja fait : on affiche dans l'ordre
 * recu, sans re-trier. Tous les chiffres affiches sont ceux du backend - en
 * particulier `metrage.ml_total`, qui est un ENTIER de metres deja arrondi au
 * superieur (deux montees successives : tour entame fini, puis metre superieur).
 */
export function CarteConfiguration({
  configuration,
  choisie,
  onChiffrer,
}: {
  configuration: Configuration;
  choisie: boolean;
  onChiffrer: (configuration: Configuration) => void;
}) {
  const c = configuration;

  return (
    <article
      className={
        choisie
          ? "flex flex-col gap-4 rounded-lg border-2 border-accent bg-surface p-4 sm:p-5"
          : "flex flex-col gap-4 rounded-lg border border-bordure bg-surface p-4 sm:p-5"
      }
    >
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <span className="rounded-md bg-accent-doux px-2 py-1 text-sm font-semibold text-accent">
            {c.rang === 1 ? "Meilleure" : `N° ${c.rang}`}
          </span>
          <h3 className="text-base font-semibold">{c.machine.nom}</h3>
        </div>
        <p className="text-sm text-texte-doux">
          Cylindre {c.cylindre.nb_dents} dents · developpe{" "}
          {mm(c.cylindre.developpe_mm)}
        </p>
      </header>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
        <Fait
          libelle="Poses"
          valeur={`${c.poses.laize} en laize × ${c.poses.developpe} en dev = ${c.poses.total}`}
        />
        <Fait libelle="Intervalle laize" valeur={mm(c.intervalles_mm.laize)} />
        <Fait libelle="Intervalle dev" valeur={mm(c.intervalles_mm.developpe)} />
        <Fait libelle="Laize plaque" valeur={mm(c.laizes_mm.plaque)} />
        <Fait libelle="Laize papier" valeur={mm(c.laizes_mm.papier)} />
        <Fait
          libelle="Chute par cote"
          valeur={mm(c.laizes_mm.chute_par_cote)}
        />
        <Fait libelle="Tours" valeur={entier(c.metrage.nb_tours)} />
        <Fait
          libelle="Metrage"
          valeur={`${entier(c.metrage.ml_total)} ml`}
        />
        <Fait libelle="Rendement" valeur={pourcent(c.rendement_pct)} />
      </dl>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-bordure pt-3 text-sm text-texte-doux">
        <span>
          Score <strong className="text-texte">{coefficient(c.score)}</strong>
        </span>
        <span>
          Vitesse ×{" "}
          <strong className="text-texte">
            {coefficient(c.coefficients.vitesse)}
          </strong>
        </span>
        <span>
          Gache ×{" "}
          <strong className="text-texte">
            {coefficient(c.coefficients.gache)}
          </strong>
        </span>
      </div>

      <Alertes alertes={c.alertes} />

      <button
        type="button"
        onClick={() => onChiffrer(c)}
        aria-pressed={choisie}
        className={
          choisie
            ? "min-h-12 rounded-md border-2 border-accent bg-accent-doux px-4 py-3 text-base font-semibold text-accent"
            : "min-h-12 rounded-md border border-bordure px-4 py-3 text-base font-semibold"
        }
      >
        {choisie ? "Configuration chiffree" : "Chiffrer cette configuration"}
      </button>
    </article>
  );
}
