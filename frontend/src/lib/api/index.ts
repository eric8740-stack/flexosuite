// Les appels que les ecrans utilisent. Un seul endroit sait aiguiller vers les
// FIXTURES tant que les endpoints du lot 2 n'existent pas : les composants, eux,
// appellent toujours la meme fonction et n'ont rien a defaire ensuite.

import { lire, envoyer } from "./client";
import type {
  ApercuChiffrage,
  Contexte,
  DemandeApercu,
  DemandeOptimisation,
  Matiere,
  Machine,
  OptionFinition,
  ReponseOptimisation,
  ReponseSens,
} from "./types";
import * as fixtures from "@/lib/fixtures";

export const MODE_FIXTURES = fixtures.MODE_FIXTURES;

/** Petit delai en mode fixtures : sans lui, les etats de chargement ne sont
 *  jamais visibles et on livre des ecrans qui clignotent chez le client. */
function fixture<T>(valeur: T): Promise<T> {
  return new Promise((resoudre) => setTimeout(() => resoudre(valeur), 220));
}

export function chargerContexte(): Promise<Contexte> {
  // `/api/contexte` existe deja (marque ✅ au contrat) : pas de fixture ici,
  // meme en mode fixtures, c'est le seul endpoint de donnees deja livre.
  return lire<Contexte>("/contexte");
}

export function chargerMatieres(): Promise<Matiere[]> {
  if (MODE_FIXTURES) return fixture(fixtures.matieres);
  return lire<Matiere[]>("/matieres");
}

export function chargerMachines(): Promise<Machine[]> {
  if (MODE_FIXTURES) return fixture(fixtures.machines);
  return lire<Machine[]>("/machines");
}

export function chargerOptions(): Promise<OptionFinition[]> {
  if (MODE_FIXTURES) return fixture(fixtures.options);
  return lire<OptionFinition[]>("/options");
}

export function chargerSens(): Promise<ReponseSens> {
  if (MODE_FIXTURES) return fixture(fixtures.sens);
  return lire<ReponseSens>("/sens-enroulement");
}

export function chercherConfigurations(
  demande: DemandeOptimisation,
): Promise<ReponseOptimisation> {
  if (MODE_FIXTURES) return fixture(fixtures.optimisation);
  return envoyer<ReponseOptimisation>("/optimisation/configurations", demande);
}

export function chiffrer(demande: DemandeApercu): Promise<ApercuChiffrage> {
  if (MODE_FIXTURES) {
    return fixture(
      demande.lots.length > 1 ? fixtures.apercuDeuxLots : fixtures.apercu,
    );
  }
  return envoyer<ApercuChiffrage>("/devis/apercu", demande);
}
