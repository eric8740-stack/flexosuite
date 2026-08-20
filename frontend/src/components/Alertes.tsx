import type { Alerte } from "@/lib/api/types";

/**
 * Les alertes du backend sont redigees POUR UN DEVISEUR : le contrat impose de
 * les afficher telles quelles. On ne les reformule pas, on ne les tronque pas,
 * et surtout on ne les cache pas derriere un survol - l'ecran est tactile.
 */
export function Alertes({ alertes }: { alertes: Alerte[] }) {
  if (alertes.length === 0) return null;

  return (
    <ul className="flex flex-col gap-2">
      {alertes.map((alerte, i) => (
        <li
          key={i}
          className={
            alerte.niveau === "attention"
              ? "flex gap-2 rounded-md border border-attention/40 bg-attention-doux px-3 py-2 text-sm text-texte"
              : "flex gap-2 rounded-md border border-bordure bg-accent-doux px-3 py-2 text-sm text-texte"
          }
        >
          <span aria-hidden="true" className="font-semibold">
            {alerte.niveau === "attention" ? "!" : "i"}
          </span>
          <span>
            <span className="sr-only">
              {alerte.niveau === "attention" ? "Attention : " : "Information : "}
            </span>
            {alerte.message}
          </span>
        </li>
      ))}
    </ul>
  );
}
