import { eur, mm, pourcent } from "@/lib/format";
import type { OutilAFabriquer } from "@/lib/api/types";

/**
 * « Fabriquer un outil neuf » quand aucun cylindre du parc ne convient.
 * Le contrat est formel : c'est une ALTERNATIVE, pas un echec. D'ou le ton et
 * l'absence de rouge.
 *
 * ⚠️ Le contrat v1 ne fige pas les champs de cette proposition. On ne les
 * invente donc pas : on rend ce qui arrive, en deduisant l'unite du suffixe de
 * la cle (`_eur`, `_mm`, `_pct`). Des que CC1 aura fige la forme, ce rendu
 * generique laissera la place a une mise en page dediee.
 */
function humaniser(cle: string): string {
  const mots = cle.replace(/_(eur|mm|pct|min|max)$/, "").split("_");
  const phrase = mots.join(" ");
  return phrase.charAt(0).toUpperCase() + phrase.slice(1);
}

function rendre(cle: string, valeur: unknown): string | null {
  if (valeur === null || valeur === undefined) return null;
  if (typeof valeur === "boolean") return valeur ? "oui" : "non";
  if (typeof valeur !== "string" && typeof valeur !== "number") return null;

  const texte = String(valeur);
  if (cle.endsWith("_eur")) return eur(texte);
  if (cle.endsWith("_mm")) return mm(texte);
  if (cle.endsWith("_pct")) return pourcent(texte);
  return texte;
}

export function PropositionOutil({ outil }: { outil: OutilAFabriquer }) {
  const lignes = Object.entries(outil)
    .map(([cle, valeur]) => [cle, rendre(cle, valeur)] as const)
    .filter(([, valeur]) => valeur !== null);

  return (
    <section className="flex flex-col gap-3 rounded-lg border border-bordure bg-surface p-4 sm:p-5">
      <h3 className="text-base font-semibold">Fabriquer un outil neuf</h3>
      <p className="text-sm text-texte-doux">
        Aucun cylindre du parc ne tient les contraintes de ce format. Voici
        l&apos;outil qu&apos;il faudrait faire faire, et ce qu&apos;il coute :
        c&apos;est une option a chiffrer, pas une impasse.
      </p>

      {lignes.length > 0 ? (
        <dl className="grid grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2">
          {lignes.map(([cle, valeur]) => (
            <div key={cle} className="flex flex-col gap-0.5">
              <dt className="text-xs uppercase tracking-wide text-texte-doux">
                {humaniser(cle)}
              </dt>
              <dd className="text-sm font-medium tabular-nums">{valeur}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </section>
  );
}
