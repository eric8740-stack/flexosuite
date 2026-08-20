"use client";

import type { SensEnroulement } from "@/lib/api/types";

/**
 * Etiquette dessinee, tournee de `rotation` degres HORAIRES.
 * 0 = tete en haut, 90 = tete a droite, 180 = tete en bas, 270 = tete a gauche.
 *
 * Le glyphe est volontairement ASYMETRIQUE dans les deux axes (bande de tete +
 * lettre F) : une forme symetrique rendrait 0 et 180 identiques a l'oeil, ce qui
 * est exactement l'erreur qu'on cherche a rendre impossible.
 */
function Etiquette({ rotation }: { rotation: number }) {
  return (
    <g transform={`rotate(${rotation} 0 0)`}>
      <rect
        x="-30"
        y="-22"
        width="60"
        height="44"
        rx="3"
        fill="var(--surface)"
        stroke="var(--texte)"
        strokeWidth="1.5"
      />
      <rect x="-30" y="-22" width="60" height="9" rx="3" fill="var(--accent)" />
      <text
        x="0"
        y="-15"
        textAnchor="middle"
        fontSize="6"
        fill="#ffffff"
        fontFamily="system-ui, sans-serif"
      >
        TETE
      </text>
      <text
        x="0"
        y="10"
        textAnchor="middle"
        fontSize="18"
        fontWeight="700"
        fill="var(--texte)"
        fontFamily="system-ui, sans-serif"
      >
        F
      </text>
    </g>
  );
}

/** Une vue : le sens de defilement (fixe) et l'etiquette (tournee). */
function Vue({
  titre,
  precision,
  rotation,
  defilement,
}: {
  titre: string;
  precision: string;
  rotation: number;
  defilement: "bas" | "droite";
}) {
  return (
    <figure className="flex flex-col gap-2">
      <figcaption>
        <span className="block text-sm font-semibold">{titre}</span>
        <span className="block text-xs text-texte-doux">{precision}</span>
      </figcaption>
      <svg
        viewBox="0 0 160 120"
        className="h-auto w-full max-w-56 rounded-md border border-bordure bg-fond"
        role="img"
        aria-label={`${titre} : etiquette tournee de ${rotation} degres`}
      >
        <g transform="translate(80 60)">
          <Etiquette rotation={rotation} />
        </g>
        {defilement === "bas" ? (
          <g stroke="var(--texte-doux)" strokeWidth="1.5" fill="none">
            <line x1="18" y1="20" x2="18" y2="96" />
            <polyline points="12,88 18,100 24,88" />
            <text
              x="30"
              y="60"
              fontSize="9"
              fill="var(--texte-doux)"
              stroke="none"
              fontFamily="system-ui, sans-serif"
            >
              avance
            </text>
          </g>
        ) : (
          <g stroke="var(--texte-doux)" strokeWidth="1.5" fill="none">
            <line x1="16" y1="106" x2="140" y2="106" />
            <polyline points="132,100 144,106 132,112" />
            <text
              x="60"
              y="100"
              fontSize="9"
              fill="var(--texte-doux)"
              stroke="none"
              fontFamily="system-ui, sans-serif"
            >
              defilement
            </text>
          </g>
        )}
      </svg>
    </figure>
  );
}

/**
 * Choix du sens d'enroulement, parmi les 8 de la convention flexographique.
 *
 * ⚠️ Le piege que cet ecran doit rendre impossible : les paires (1,5) (2,6)
 * (3,7) (4,8) ont EXACTEMENT les memes rotations sur les deux vues. Seule la
 * face imprimee les distingue. La face est donc ecrite en toutes lettres, et le
 * jumeau est nomme explicitement - jamais laisse a deviner, jamais dans une
 * infobulle.
 */
export function ChoixSensEnroulement({
  sens,
  numeroChoisi,
  onChoisir,
}: {
  sens: SensEnroulement[];
  numeroChoisi: number | null;
  onChoisir: (numero: number) => void;
}) {
  const choisi = sens.find((s) => s.numero === numeroChoisi) ?? null;
  const jumeau = choisi
    ? sens.find(
        (s) =>
          s.numero !== choisi.numero &&
          s.rotation_vue_planche === choisi.rotation_vue_planche &&
          s.rotation_vue_bobine === choisi.rotation_vue_bobine,
      ) ?? null
    : null;

  return (
    <section className="flex flex-col gap-4 rounded-lg border border-bordure bg-surface p-4 sm:p-5">
      <div>
        <h2 className="text-base font-semibold">Sens d&apos;enroulement</h2>
        <p className="text-sm text-texte-doux">
          La vue planche est celle que lit le poseur de cliches. Fausse, c&apos;est
          un cliche pose a l&apos;envers et un tirage entier a jeter.
        </p>
      </div>

      <div
        role="group"
        aria-label="Les huit sens d&apos;enroulement"
        className="grid grid-cols-4 gap-2 sm:grid-cols-8"
      >
        {sens.map((s) => (
          <button
            key={s.numero}
            type="button"
            onClick={() => onChoisir(s.numero)}
            aria-pressed={s.numero === choisi?.numero}
            className={
              s.numero === choisi?.numero
                ? "flex min-h-12 flex-col items-center justify-center rounded-md border-2 border-accent bg-accent-doux py-2 text-sm font-semibold text-accent"
                : "flex min-h-12 flex-col items-center justify-center rounded-md border border-bordure py-2 text-sm font-semibold"
            }
          >
            {s.numero}
            <span className="text-[10px] font-normal text-texte-doux">
              {s.face === "exterieur" ? "ext." : "int."}
            </span>
          </button>
        ))}
      </div>

      {choisi ? (
        <div className="flex flex-col gap-4">
          <p className="text-sm">
            <strong>
              Sens {choisi.numero} — {choisi.libelle}
            </strong>
          </p>

          <p className="rounded-md border border-bordure bg-accent-doux px-3 py-2 text-sm">
            Face imprimee :{" "}
            <strong>
              {choisi.face === "exterieur"
                ? "a l'exterieur du rouleau"
                : "a l'interieur du rouleau"}
            </strong>
          </p>

          {jumeau ? (
            <p className="rounded-md border border-attention/40 bg-attention-doux px-3 py-2 text-sm">
              <strong>
                Les sens {choisi.numero} et {jumeau.numero} se dessinent a
                l&apos;identique.
              </strong>{" "}
              Memes rotations sur les deux vues : seule la face imprimee les
              distingue. Verifiez la face avant de lancer les cliches.
            </p>
          ) : null}

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <Vue
              titre="Vue planche presse"
              precision={`Rotation ${choisi.rotation_vue_planche}° — l'avance descend`}
              rotation={choisi.rotation_vue_planche}
              defilement="bas"
            />
            <Vue
              titre="Vue bobine deroulee"
              precision={`Rotation ${choisi.rotation_vue_bobine}° — chez le client`}
              rotation={choisi.rotation_vue_bobine}
              defilement="droite"
            />
          </div>
        </div>
      ) : (
        <p className="text-sm text-texte-doux">
          Choisissez un sens pour voir la planche et la bobine.
        </p>
      )}
    </section>
  );
}
