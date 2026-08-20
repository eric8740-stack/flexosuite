"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Alertes } from "@/components/Alertes";
import { ApercuChiffrage } from "@/components/ApercuChiffrage";
import { BriefOptimisation } from "@/components/BriefOptimisation";
import { CarteConfiguration } from "@/components/CarteConfiguration";
import { ChoixSensEnroulement } from "@/components/SensEnroulement";
import { PropositionOutil } from "@/components/PropositionOutil";
import {
  chargerMachines,
  chargerMatieres,
  chargerOptions,
  chargerSens,
  chercherConfigurations,
} from "@/lib/api";
import { ErreurApi } from "@/lib/api/client";
import type {
  Configuration,
  DemandeOptimisation,
  Machine,
  Matiere,
  OptionFinition,
  ReponseOptimisation,
  SensEnroulement,
} from "@/lib/api/types";

/**
 * L'optimisation de pose est le POINT D'ENTREE UNIQUE de l'application : c'est
 * le coeur du produit, pas un onglet parmi d'autres. Le deviseur arrive ici,
 * saisit son brief, et tout le reste en decoule.
 */
export default function PageOptimisation() {
  const [matieres, setMatieres] = useState<Matiere[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [options, setOptions] = useState<OptionFinition[]>([]);
  const [sens, setSens] = useState<SensEnroulement[]>([]);
  const [erreurReferentiels, setErreurReferentiels] = useState<string | null>(
    null,
  );

  const [demande, setDemande] = useState<DemandeOptimisation | null>(null);
  const [resultat, setResultat] = useState<ReponseOptimisation | null>(null);
  const [rechercheEnCours, setRechercheEnCours] = useState(false);
  const [erreurRecherche, setErreurRecherche] = useState<string | null>(null);

  const [configurationChoisie, setConfigurationChoisie] =
    useState<Configuration | null>(null);
  const [numeroSens, setNumeroSens] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([
      chargerMatieres(),
      chargerMachines(),
      chargerOptions(),
      chargerSens(),
    ])
      .then(([m, ma, o, s]) => {
        setMatieres(m);
        setMachines(ma);
        setOptions(o);
        setSens(s.sens);
      })
      .catch((e: unknown) => {
        // Le message metier d'abord, le detail du serveur ensuite : un
        // deviseur doit comprendre ce qui lui manque avant de lire un statut.
        setErreurReferentiels(
          e instanceof ErreurApi
            ? `Les referentiels n'ont pas pu etre charges. ${e.message}`
            : "Les referentiels n'ont pas pu etre charges.",
        );
      });
  }, []);

  function rechercher(nouvelleDemande: DemandeOptimisation) {
    setDemande(nouvelleDemande);
    setRechercheEnCours(true);
    setErreurRecherche(null);
    setConfigurationChoisie(null);

    chercherConfigurations(nouvelleDemande)
      .then((reponse) => {
        setResultat(reponse);
        // Le tri est deja fait par le backend : on ne re-trie pas, on prend
        // simplement la premiere comme configuration mise en avant.
        setConfigurationChoisie(reponse.configurations[0] ?? null);
      })
      .catch((e: unknown) => {
        setResultat(null);
        setErreurRecherche(
          e instanceof ErreurApi
            ? e.message
            : "La recherche de configurations a echoue.",
        );
      })
      .finally(() => setRechercheEnCours(false));
  }

  return (
    <AppShell>
      {erreurReferentiels ? (
        <p className="rounded-md border border-attention/40 bg-attention-doux px-3 py-2 text-sm">
          {erreurReferentiels}
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] lg:items-start">
        <BriefOptimisation
          matieres={matieres}
          machines={machines}
          options={options}
          enCours={rechercheEnCours}
          onRecherche={rechercher}
        />

        <div className="flex flex-col gap-6">
          {erreurRecherche ? (
            <p className="rounded-md border border-attention/40 bg-attention-doux px-3 py-2 text-sm">
              {erreurRecherche}
            </p>
          ) : null}

          {!resultat && !rechercheEnCours && !erreurRecherche ? (
            <p className="rounded-lg border border-dashed border-bordure p-6 text-sm text-texte-doux">
              Renseignez le brief, puis lancez la recherche : l&apos;application
              cherche dans votre parc les outils qui tiennent ce format.
            </p>
          ) : null}

          {rechercheEnCours ? (
            <p className="text-sm text-texte-doux">
              Recherche des configurations realisables…
            </p>
          ) : null}

          {resultat ? (
            <>
              <Alertes alertes={resultat.alertes} />

              {resultat.aucun_outil_compatible ? (
                resultat.outil_a_fabriquer ? (
                  <PropositionOutil outil={resultat.outil_a_fabriquer} />
                ) : (
                  <p className="rounded-lg border border-bordure bg-surface p-4 text-sm">
                    Aucun outil du parc ne tient ce format.
                  </p>
                )
              ) : null}

              {resultat.configurations.length > 0 ? (
                <section className="flex flex-col gap-3">
                  <div>
                    <h2 className="text-base font-semibold">
                      {resultat.configurations.length === 1
                        ? "Une configuration realisable"
                        : `${resultat.configurations.length} configurations realisables`}
                    </h2>
                    {/* Moins de trois propositions est NORMAL : on ne degrade
                        jamais une contrainte pour remplir la liste. On le dit
                        plutot que de laisser croire a un manque. */}
                    {resultat.configurations.length < 3 ? (
                      <p className="text-sm text-texte-doux">
                        Ce sont les seules qui tiennent vos contraintes. Aucune
                        contrainte n&apos;a ete relachee pour en proposer
                        davantage.
                      </p>
                    ) : null}
                  </div>

                  <div className="flex flex-col gap-4">
                    {resultat.configurations.map((configuration) => (
                      <CarteConfiguration
                        key={configuration.id}
                        configuration={configuration}
                        choisie={configuration.id === configurationChoisie?.id}
                        onChiffrer={setConfigurationChoisie}
                      />
                    ))}
                  </div>
                </section>
              ) : null}

              {configurationChoisie && demande ? (
                <ApercuChiffrage
                  // Changer de configuration doit repartir de lots propres.
                  // La cle de remontage fait ce travail, la ou un effet de
                  // remise a zero provoquerait un rendu en cascade.
                  key={configurationChoisie.id}
                  configuration={configurationChoisie}
                  matiereId={demande.matiere_id}
                  quantite={demande.quantite}
                  nbCouleurs={demande.nb_couleurs}
                  optionsCodes={demande.options_codes ?? []}
                />
              ) : null}
            </>
          ) : null}

          {sens.length > 0 ? (
            <ChoixSensEnroulement
              sens={sens}
              numeroChoisi={numeroSens}
              onChoisir={setNumeroSens}
            />
          ) : null}
        </div>
      </div>
    </AppShell>
  );
}
