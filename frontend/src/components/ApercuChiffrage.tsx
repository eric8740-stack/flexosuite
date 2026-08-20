"use client";

import { useCallback, useEffect, useState } from "react";
import { Alertes } from "./Alertes";
import { Champ, classesSaisie } from "./Champ";
import { chiffrer } from "@/lib/api";
import { ErreurApi } from "@/lib/api/client";
import { coefficient, entier, eur, pourcent } from "@/lib/format";
import type {
  ApercuChiffrage as Apercu,
  Configuration,
  LotChiffrage,
} from "@/lib/api/types";

function lotInitial(
  configuration: Configuration,
  matiereId: number,
  quantite: number,
  nbCouleurs: number,
  optionsCodes: string[],
): LotChiffrage {
  const quadri = Math.min(4, nbCouleurs);
  return {
    configuration_id: configuration.id,
    matiere_id: matiereId,
    quantite,
    nb_couleurs_par_type: { quadri, pantone: Math.max(0, nbCouleurs - quadri) },
    changement_outil_cliche: false,
    options_codes: optionsCodes,
    forfaits_sous_traitance: [],
    outil_existant: true,
    nb_traces: 1,
    forme_speciale: false,
  };
}

function LigneResultat({
  libelle,
  valeur,
  fort,
}: {
  libelle: string;
  valeur: string;
  fort?: boolean;
}) {
  return (
    <div
      className={
        fort
          ? "flex flex-wrap items-baseline justify-between gap-2 border-t border-bordure pt-3"
          : "flex flex-wrap items-baseline justify-between gap-2"
      }
    >
      <span className={fort ? "text-base font-semibold" : "text-sm"}>
        {libelle}
      </span>
      <span
        className={
          fort
            ? "text-lg font-semibold tabular-nums"
            : "text-sm font-medium tabular-nums"
        }
      >
        {valeur}
      </span>
    </div>
  );
}

/**
 * Apercu de chiffrage : le prix se recalcule a chaque modification, sans rien
 * enregistrer. Trois obligations du contrat sont tenues ici :
 *   1. le COEFFICIENT s'affiche a cote du pourcentage de marge - « 30 % » lu
 *      comme un taux de marque fait facturer 9 % en dessous ;
 *   2. le DETAIL PAR LOT est affiche, jamais seulement le total ;
 *   3. le CALAGE MUTUALISE est montre : c'est l'argument commercial du
 *      groupage, pas une ligne technique.
 */
export function ApercuChiffrage({
  configuration,
  matiereId,
  quantite,
  nbCouleurs,
  optionsCodes,
}: {
  configuration: Configuration;
  matiereId: number;
  quantite: number;
  nbCouleurs: number;
  optionsCodes: string[];
}) {
  const [lots, setLots] = useState<LotChiffrage[]>(() => [
    lotInitial(configuration, matiereId, quantite, nbCouleurs, optionsCodes),
  ]);
  const [margeOverride, setMargeOverride] = useState("");
  const [apercu, setApercu] = useState<Apercu | null>(null);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  const modifierLot = useCallback(
    (index: number, modification: Partial<LotChiffrage>) => {
      setLots((actuels) =>
        actuels.map((lot, i) =>
          i === index ? { ...lot, ...modification } : lot,
        ),
      );
    },
    [],
  );

  // Recalcul a chaque modification, temporise : sans cette pause, chaque touche
  // frappee dans « quantite » declencherait un appel.
  useEffect(() => {
    let abandonne = false;
    const minuterie = setTimeout(() => {
      setEnCours(true);
      chiffrer({
        lots,
        marge_pct_override: margeOverride === "" ? null : margeOverride,
      })
        .then((resultat) => {
          if (!abandonne) {
            setApercu(resultat);
            setErreur(null);
          }
        })
        .catch((e: unknown) => {
          if (abandonne) return;
          setApercu(null);
          setErreur(
            e instanceof ErreurApi
              ? e.message
              : "Le chiffrage n'a pas pu etre calcule.",
          );
        })
        .finally(() => {
          if (!abandonne) setEnCours(false);
        });
    }, 400);

    return () => {
      abandonne = true;
      clearTimeout(minuterie);
    };
  }, [lots, margeOverride]);

  return (
    <section className="flex flex-col gap-5 rounded-lg border border-bordure bg-surface p-4 sm:p-5">
      <div>
        <h2 className="text-base font-semibold">Chiffrage</h2>
        <p className="text-sm text-texte-doux">
          Configuration {configuration.machine.nom} · cylindre{" "}
          {configuration.cylindre.nb_dents} dents. Rien n&apos;est enregistre.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        {lots.map((lot, index) => (
          <div
            key={index}
            className="flex flex-col gap-4 rounded-md border border-bordure p-3"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-sm font-semibold">
                {lots.length > 1 ? `Lot ${index + 1}` : "Le lot"}
              </h3>
              {lots.length > 1 ? (
                <button
                  type="button"
                  onClick={() =>
                    setLots((actuels) => actuels.filter((_, i) => i !== index))
                  }
                  className="min-h-11 rounded-md border border-bordure px-3 text-sm"
                >
                  Retirer
                </button>
              ) : null}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Champ libelle="Quantite" htmlFor={`q-${index}`}>
                <input
                  id={`q-${index}`}
                  className={classesSaisie}
                  type="number"
                  inputMode="numeric"
                  min="1"
                  step="1"
                  value={lot.quantite}
                  onChange={(e) =>
                    modifierLot(index, { quantite: Number(e.target.value) })
                  }
                />
              </Champ>
              <Champ libelle="Couleurs quadri" htmlFor={`quadri-${index}`}>
                <input
                  id={`quadri-${index}`}
                  className={classesSaisie}
                  type="number"
                  inputMode="numeric"
                  min="0"
                  max="4"
                  step="1"
                  value={lot.nb_couleurs_par_type.quadri}
                  onChange={(e) =>
                    modifierLot(index, {
                      nb_couleurs_par_type: {
                        ...lot.nb_couleurs_par_type,
                        quadri: Number(e.target.value),
                      },
                    })
                  }
                />
              </Champ>
              <Champ libelle="Couleurs Pantone" htmlFor={`pantone-${index}`}>
                <input
                  id={`pantone-${index}`}
                  className={classesSaisie}
                  type="number"
                  inputMode="numeric"
                  min="0"
                  max="8"
                  step="1"
                  value={lot.nb_couleurs_par_type.pantone}
                  onChange={(e) =>
                    modifierLot(index, {
                      nb_couleurs_par_type: {
                        ...lot.nb_couleurs_par_type,
                        pantone: Number(e.target.value),
                      },
                    })
                  }
                />
              </Champ>
            </div>

            <details className="rounded-md border border-bordure">
              <summary className="min-h-11 cursor-pointer list-none px-3 py-3 text-sm font-medium">
                Outillage et decoupe
              </summary>
              <div className="flex flex-col gap-3 border-t border-bordure px-3 py-4">
                <label className="flex min-h-11 items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    className="size-5"
                    checked={lot.outil_existant}
                    onChange={(e) =>
                      modifierLot(index, { outil_existant: e.target.checked })
                    }
                  />
                  L&apos;outil de decoupe existe deja
                </label>
                <label className="flex min-h-11 items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    className="size-5"
                    checked={lot.changement_outil_cliche}
                    onChange={(e) =>
                      modifierLot(index, {
                        changement_outil_cliche: e.target.checked,
                      })
                    }
                  />
                  Changement d&apos;outil ou de cliches en cours de tirage
                </label>
                <label className="flex min-h-11 items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    className="size-5"
                    checked={lot.forme_speciale}
                    onChange={(e) =>
                      modifierLot(index, { forme_speciale: e.target.checked })
                    }
                  />
                  Forme speciale
                </label>
                <Champ libelle="Nombre de traces" htmlFor={`traces-${index}`}>
                  <input
                    id={`traces-${index}`}
                    className={classesSaisie}
                    type="number"
                    inputMode="numeric"
                    min="1"
                    step="1"
                    value={lot.nb_traces}
                    onChange={(e) =>
                      modifierLot(index, { nb_traces: Number(e.target.value) })
                    }
                  />
                </Champ>
              </div>
            </details>
          </div>
        ))}

        <button
          type="button"
          onClick={() =>
            setLots((actuels) => [
              ...actuels,
              { ...actuels[actuels.length - 1] },
            ])
          }
          className="min-h-12 rounded-md border border-bordure px-4 py-3 text-sm font-semibold"
        >
          Ajouter un lot
        </button>
      </div>

      <Champ
        libelle="Marge appliquee (%)"
        htmlFor="marge"
        aide="Laisser vide pour garder la marge des parametres de l'atelier."
      >
        <input
          id="marge"
          className={classesSaisie}
          type="number"
          inputMode="decimal"
          min="0"
          step="0.5"
          value={margeOverride}
          onChange={(e) => setMargeOverride(e.target.value)}
        />
      </Champ>

      {erreur ? (
        <p className="rounded-md border border-attention/40 bg-attention-doux px-3 py-2 text-sm">
          {erreur}
        </p>
      ) : null}

      {apercu ? (
        <div
          aria-busy={enCours}
          className={
            enCours
              ? "flex flex-col gap-5 opacity-60 transition-opacity"
              : "flex flex-col gap-5 transition-opacity"
          }
        >
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold">Les sept postes</h3>
            <dl className="flex flex-col gap-2">
              {apercu.postes.map((poste) => (
                <div
                  key={poste.numero}
                  className="flex flex-wrap items-baseline justify-between gap-2"
                >
                  <dt className="text-sm">
                    <span className="text-texte-doux">{poste.numero}.</span>{" "}
                    {poste.libelle}
                  </dt>
                  <dd className="text-sm font-medium tabular-nums">
                    {eur(poste.montant_eur)}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="flex flex-col gap-3">
            <LigneResultat
              libelle="Cout de revient"
              valeur={eur(apercu.cout_revient_eur)}
              fort
            />
            <LigneResultat
              libelle={`Marge ${pourcent(apercu.marge_pct)} — coefficient × ${coefficient(apercu.coefficient)}`}
              valeur=""
            />
            <p className="text-xs text-texte-doux">
              La marge s&apos;applique sur le cout de revient : le prix est
              multiplie par {coefficient(apercu.coefficient)}. Ce n&apos;est pas
              un taux de marque.
            </p>
            <LigneResultat
              libelle="Prix de vente HT"
              valeur={eur(apercu.prix_vente_ht_eur)}
              fort
            />
            <LigneResultat
              libelle="Prix au mille"
              valeur={eur(apercu.prix_au_mille_eur)}
            />
            <LigneResultat
              libelle="Calages"
              valeur={entier(apercu.nb_calages)}
            />
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold">Detail par lot</h3>
            <ul className="flex flex-col gap-2">
              {apercu.details_par_lot.map((detail) => (
                <li
                  key={detail.ordre}
                  className="flex flex-col gap-1 rounded-md border border-bordure p-3"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="text-sm font-semibold">
                      Lot {detail.ordre + 1}
                    </span>
                    <span className="text-sm font-semibold tabular-nums">
                      {eur(detail.prix_vente_ht_eur)}
                    </span>
                  </div>
                  <span className="text-sm text-texte-doux">
                    Cout de revient {eur(detail.cout_revient_eur)}
                  </span>
                  {Number(detail.calage_mutualise_eur) > 0 ? (
                    <span className="text-sm">
                      Calage partage avec le lot precedent :{" "}
                      <strong>{eur(detail.calage_mutualise_eur)}</strong>{" "}
                      economises.
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>

          <Alertes alertes={apercu.alertes} />
        </div>
      ) : enCours ? (
        <p className="text-sm text-texte-doux">Calcul du chiffrage…</p>
      ) : null}
    </section>
  );
}
