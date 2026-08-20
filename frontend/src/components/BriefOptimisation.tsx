"use client";

import { useState } from "react";
import { Champ, classesSaisie } from "./Champ";
import { libelleRessource } from "@/lib/format";
import type {
  DemandeOptimisation,
  Machine,
  Matiere,
  OptionFinition,
} from "@/lib/api/types";

/**
 * Le brief client : ce que le deviseur a sous les yeux quand le telephone
 * sonne. Vocabulaire d'atelier (laize, dev, pose), tout en francais.
 */
export function BriefOptimisation({
  matieres,
  machines,
  options,
  enCours,
  onRecherche,
}: {
  matieres: Matiere[];
  machines: Machine[];
  options: OptionFinition[];
  enCours: boolean;
  onRecherche: (demande: DemandeOptimisation) => void;
}) {
  const [largeur, setLargeur] = useState("100");
  const [hauteur, setHauteur] = useState("80");
  const [quantite, setQuantite] = useState("10000");
  const [nbCouleurs, setNbCouleurs] = useState("5");
  const [matiereId, setMatiereId] = useState("");
  const [intervalleDevMin, setIntervalleDevMin] = useState("");
  const [codesRetenus, setCodesRetenus] = useState<string[]>([]);
  const [forcageIntervalleLaize, setForcageIntervalleLaize] = useState("");
  const [forcageNbPosesLaize, setForcageNbPosesLaize] = useState("");
  const [forcageMachineId, setForcageMachineId] = useState("");

  const matiereChoisie = matiereId || (matieres[0] ? String(matieres[0].id) : "");
  const forcageActif =
    forcageIntervalleLaize !== "" ||
    forcageNbPosesLaize !== "" ||
    forcageMachineId !== "";

  function basculerOption(code: string) {
    setCodesRetenus((actuels) =>
      actuels.includes(code)
        ? actuels.filter((c) => c !== code)
        : [...actuels, code],
    );
  }

  function soumettre(evenement: React.FormEvent) {
    evenement.preventDefault();

    const demande: DemandeOptimisation = {
      format: { largeur_mm: Number(largeur), hauteur_mm: Number(hauteur) },
      quantite: Number(quantite),
      nb_couleurs: Number(nbCouleurs),
      matiere_id: Number(matiereChoisie),
    };

    // Les trois blocs facultatifs ne partent que s'ils sont renseignes : un
    // objet vide n'a pas le meme sens qu'un champ absent pour le backend.
    if (intervalleDevMin !== "") {
      demande.contrainte_client = { intervalle_dev_min_mm: intervalleDevMin };
    }
    if (codesRetenus.length > 0) {
      demande.options_codes = codesRetenus;
    }
    if (forcageActif) {
      demande.forcages = {
        intervalle_laize_mm:
          forcageIntervalleLaize === "" ? null : forcageIntervalleLaize,
        nb_poses_laize:
          forcageNbPosesLaize === "" ? null : Number(forcageNbPosesLaize),
        machine_id: forcageMachineId === "" ? null : Number(forcageMachineId),
      };
    }

    onRecherche(demande);
  }

  return (
    <form
      onSubmit={soumettre}
      className="flex flex-col gap-5 rounded-lg border border-bordure bg-surface p-4 sm:p-5"
    >
      <div>
        <h2 className="text-base font-semibold">Le brief</h2>
        <p className="text-sm text-texte-doux">
          Le format de l&apos;etiquette finie, la quantite demandee, la matiere.
        </p>
      </div>

      <fieldset className="flex flex-col gap-4">
        <legend className="sr-only">Format de l&apos;etiquette</legend>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Champ libelle="Largeur en laize (mm)" htmlFor="largeur">
            <input
              id="largeur"
              className={classesSaisie}
              type="number"
              inputMode="decimal"
              min="1"
              step="0.1"
              required
              value={largeur}
              onChange={(e) => setLargeur(e.target.value)}
            />
          </Champ>
          <Champ libelle="Hauteur en dev (mm)" htmlFor="hauteur">
            <input
              id="hauteur"
              className={classesSaisie}
              type="number"
              inputMode="decimal"
              min="1"
              step="0.1"
              required
              value={hauteur}
              onChange={(e) => setHauteur(e.target.value)}
            />
          </Champ>
        </div>
      </fieldset>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Champ libelle="Quantite" htmlFor="quantite">
          <input
            id="quantite"
            className={classesSaisie}
            type="number"
            inputMode="numeric"
            min="1"
            step="1"
            required
            value={quantite}
            onChange={(e) => setQuantite(e.target.value)}
          />
        </Champ>
        <Champ libelle="Nombre de couleurs" htmlFor="nb-couleurs">
          <input
            id="nb-couleurs"
            className={classesSaisie}
            type="number"
            inputMode="numeric"
            min="1"
            max="12"
            step="1"
            required
            value={nbCouleurs}
            onChange={(e) => setNbCouleurs(e.target.value)}
          />
        </Champ>
      </div>

      <Champ libelle="Matiere" htmlFor="matiere">
        <select
          id="matiere"
          className={classesSaisie}
          required
          value={matiereChoisie}
          onChange={(e) => setMatiereId(e.target.value)}
        >
          {matieres.length === 0 ? (
            <option value="">Aucune matiere au referentiel</option>
          ) : null}
          {matieres.map((matiere) => (
            <option key={matiere.id} value={matiere.id}>
              {libelleRessource(matiere, "Matiere")}
            </option>
          ))}
        </select>
      </Champ>

      <Champ
        libelle="Intervalle en dev mini impose par le client (mm)"
        htmlFor="intervalle-dev-min"
        aide="A renseigner si la machine de pose du client exige un ecart minimum entre deux etiquettes. Laisser vide sinon."
      >
        <input
          id="intervalle-dev-min"
          className={classesSaisie}
          type="number"
          inputMode="decimal"
          min="0"
          step="0.1"
          value={intervalleDevMin}
          onChange={(e) => setIntervalleDevMin(e.target.value)}
        />
      </Champ>

      {options.length > 0 ? (
        <fieldset className="flex flex-col gap-2">
          <legend className="text-sm font-medium">Options de finition</legend>
          <div className="flex flex-col gap-1">
            {options.map((option) => (
              <label
                key={option.id}
                className="flex min-h-11 items-center gap-3 rounded-md px-1 text-sm"
              >
                <input
                  type="checkbox"
                  className="size-5"
                  checked={codesRetenus.includes(option.code)}
                  onChange={() => basculerOption(option.code)}
                />
                {libelleRessource(option, "Option")}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}

      <details className="rounded-md border border-bordure">
        <summary className="min-h-11 cursor-pointer list-none px-3 py-3 text-sm font-medium">
          Forcages du deviseur{forcageActif ? " — actifs" : ""}
        </summary>
        <div className="flex flex-col gap-4 border-t border-bordure px-3 py-4">
          <p className="text-xs text-texte-doux">
            Un forcage contourne le plafond d&apos;intervalle en laize : seule la
            faisabilite geometrique reste verifiee. C&apos;est votre decision,
            l&apos;application ne la discute pas.
          </p>
          <Champ libelle="Intervalle en laize impose (mm)" htmlFor="f-intervalle">
            <input
              id="f-intervalle"
              className={classesSaisie}
              type="number"
              inputMode="decimal"
              min="0"
              step="0.1"
              value={forcageIntervalleLaize}
              onChange={(e) => setForcageIntervalleLaize(e.target.value)}
            />
          </Champ>
          <Champ libelle="Nombre de poses en laize impose" htmlFor="f-poses">
            <input
              id="f-poses"
              className={classesSaisie}
              type="number"
              inputMode="numeric"
              min="1"
              step="1"
              value={forcageNbPosesLaize}
              onChange={(e) => setForcageNbPosesLaize(e.target.value)}
            />
          </Champ>
          <Champ libelle="Machine imposee" htmlFor="f-machine">
            <select
              id="f-machine"
              className={classesSaisie}
              value={forcageMachineId}
              onChange={(e) => setForcageMachineId(e.target.value)}
            >
              <option value="">Laisser l&apos;application choisir</option>
              {machines.map((machine) => (
                <option key={machine.id} value={machine.id}>
                  {libelleRessource(machine, "Machine")}
                </option>
              ))}
            </select>
          </Champ>
        </div>
      </details>

      <button
        type="submit"
        disabled={enCours || matieres.length === 0}
        className="min-h-12 rounded-md bg-accent px-4 py-3 text-base font-semibold text-white disabled:opacity-50"
      >
        {enCours ? "Recherche en cours…" : "Chercher les configurations"}
      </button>
    </form>
  );
}
