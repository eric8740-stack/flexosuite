// FIXTURES FICTIVES, conformes au contrat v1.
//
// Elles servent a travailler les ecrans pendant que CC1 ecrit les endpoints du
// lot 2. Deux regles absolues :
//   1. AUCUNE donnee reelle d'atelier - ce depot est public. Les valeurs
//      ci-dessous sont fabriquees, comme le « jeu dore » de la spec metier.
//   2. Elles ne s'activent que si `NEXT_PUBLIC_FIXTURES=1`, variable definie
//      dans `.env.development` et JAMAIS au build du package client.

import type {
  ApercuChiffrage,
  Configuration,
  Contexte,
  Matiere,
  Machine,
  OptionFinition,
  ReponseOptimisation,
  ReponseSens,
} from "@/lib/api/types";

export const MODE_FIXTURES = process.env.NEXT_PUBLIC_FIXTURES === "1";

export const matieres: Matiere[] = [
  { id: 12, libelle: "Papier couche demo 80 g" },
  { id: 13, libelle: "Polypropylene blanc demo 50 µ" },
  { id: 14, libelle: "Papier thermique demo 76 g" },
];

export const machines: Machine[] = [
  { id: 3, nom: "Presse Demo A" },
  { id: 4, nom: "Presse Demo B" },
];

export const options: OptionFinition[] = [
  { id: 1, code: "microperfo", libelle: "Microperforation" },
  { id: 2, code: "vernis_selectif", libelle: "Vernis selectif" },
  { id: 3, code: "dorure", libelle: "Dorure a chaud" },
];

const configurations: Configuration[] = [
  {
    id: "cyl12-mach3-3p",
    rang: 1,
    cylindre: { id: 12, developpe_mm: "300.00", nb_dents: 94 },
    machine: { id: 3, nom: "Presse Demo A", laize_utile_mm: "320.00" },
    poses: { laize: 3, developpe: 2, total: 6 },
    intervalles_mm: { laize: "5.00", developpe: "70.00" },
    laizes_mm: { plaque: "310.00", papier: "320.00", chute_par_cote: "5.00" },
    metrage: { nb_tours: 1667, ml_total: 501 },
    rendement_pct: "49.90",
    score: "82.4",
    coefficients: { vitesse: "1.00", gache: "1.00" },
    alertes: [],
  },
  {
    id: "cyl15-mach3-3p",
    rang: 2,
    cylindre: { id: 15, developpe_mm: "254.00", nb_dents: 80 },
    machine: { id: 3, nom: "Presse Demo A", laize_utile_mm: "320.00" },
    poses: { laize: 3, developpe: 3, total: 9 },
    intervalles_mm: { laize: "5.00", developpe: "4.67" },
    laizes_mm: { plaque: "310.00", papier: "320.00", chute_par_cote: "5.00" },
    metrage: { nb_tours: 1112, ml_total: 283 },
    rendement_pct: "94.49",
    score: "76.1",
    coefficients: { vitesse: "0.95", gache: "1.10" },
    alertes: [
      {
        niveau: "attention",
        message:
          "Intervalle en developpe serre (4,67 mm) : verifier la tenue du squelette a l'echenillage.",
      },
    ],
  },
  {
    id: "cyl21-mach4-2p",
    rang: 3,
    cylindre: { id: 21, developpe_mm: "342.90", nb_dents: 108 },
    machine: { id: 4, nom: "Presse Demo B", laize_utile_mm: "250.00" },
    poses: { laize: 2, developpe: 4, total: 8 },
    intervalles_mm: { laize: "12.00", developpe: "5.72" },
    laizes_mm: { plaque: "224.00", papier: "250.00", chute_par_cote: "13.00" },
    metrage: { nb_tours: 1250, ml_total: 429 },
    rendement_pct: "71.11",
    score: "68.9",
    coefficients: { vitesse: "1.00", gache: "1.05" },
    alertes: [
      {
        niveau: "info",
        message:
          "Chute de 13 mm par cote : une laize papier plus etroite ferait gagner de la matiere.",
      },
    ],
  },
];

export const contexte: Contexte = { mode_demo: true };

export const optimisation: ReponseOptimisation = {
  configurations,
  aucun_outil_compatible: false,
  outil_a_fabriquer: null,
  alertes: [
    {
      niveau: "info",
      message:
        "Barèmes non calibrés : les scores sont indicatifs tant que l'atelier n'a pas été calibré.",
    },
  ],
};

export const sens: ReponseSens = {
  sens: [
    { numero: 1, libelle: "0° Exterieur droite avant", rotation_vue_planche: 90, rotation_vue_bobine: 0, face: "exterieur" },
    { numero: 2, libelle: "180° Exterieur gauche avant", rotation_vue_planche: 270, rotation_vue_bobine: 180, face: "exterieur" },
    { numero: 3, libelle: "270° Exterieur pied avant", rotation_vue_planche: 0, rotation_vue_bobine: 270, face: "exterieur" },
    { numero: 4, libelle: "90° Exterieur tete avant", rotation_vue_planche: 180, rotation_vue_bobine: 90, face: "exterieur" },
    { numero: 5, libelle: "0° Interieur droite avant", rotation_vue_planche: 90, rotation_vue_bobine: 0, face: "interieur" },
    { numero: 6, libelle: "180° Interieur gauche avant", rotation_vue_planche: 270, rotation_vue_bobine: 180, face: "interieur" },
    { numero: 7, libelle: "270° Interieur pied avant", rotation_vue_planche: 0, rotation_vue_bobine: 270, face: "interieur" },
    { numero: 8, libelle: "90° Interieur tete avant", rotation_vue_planche: 180, rotation_vue_bobine: 90, face: "interieur" },
  ],
};

/** Apercu de chiffrage : reprend l'exemple du contrat, etendu a un second lot
 *  pour exercer l'affichage du calage mutualise. */
export const apercu: ApercuChiffrage = {
  postes: [
    { numero: 1, libelle: "Matière", montant_eur: "315.00" },
    { numero: 2, libelle: "Encres", montant_eur: "138.60" },
    { numero: 3, libelle: "Outillage / Clichés", montant_eur: "200.00" },
    { numero: 4, libelle: "Mise en route / Calage", montant_eur: "200.00" },
    { numero: 5, libelle: "Roulage", montant_eur: "180.00" },
    { numero: 6, libelle: "Finitions", montant_eur: "232.00" },
    { numero: 7, libelle: "Main d'œuvre opérateur", montant_eur: "156.00" },
  ],
  cout_revient_eur: "1421.60",
  marge_pct: "25.00",
  coefficient: "1.25",
  prix_vente_ht_eur: "1777.00",
  prix_au_mille_eur: "177.70",
  nb_calages: 1,
  details_par_lot: [
    {
      ordre: 0,
      prix_vente_ht_eur: "1777.00",
      cout_revient_eur: "1421.60",
      calage_mutualise_eur: "0.00",
    },
  ],
  alertes: [],
};

/** Deux lots de la meme etiquette : le second partage le calage du premier.
 *  Sert a exercer l'affichage de `calage_mutualise_eur`, que le contrat impose
 *  de montrer parce que c'est un argument commercial. */
export const apercuDeuxLots: ApercuChiffrage = {
  postes: [
    { numero: 1, libelle: "Matière", montant_eur: "472.50" },
    { numero: 2, libelle: "Encres", montant_eur: "207.90" },
    { numero: 3, libelle: "Outillage / Clichés", montant_eur: "200.00" },
    { numero: 4, libelle: "Mise en route / Calage", montant_eur: "200.00" },
    { numero: 5, libelle: "Roulage", montant_eur: "270.00" },
    { numero: 6, libelle: "Finitions", montant_eur: "348.00" },
    { numero: 7, libelle: "Main d'œuvre opérateur", montant_eur: "234.00" },
  ],
  cout_revient_eur: "1932.40",
  marge_pct: "25.00",
  coefficient: "1.25",
  prix_vente_ht_eur: "2415.50",
  prix_au_mille_eur: "161.03",
  nb_calages: 1,
  details_par_lot: [
    {
      ordre: 0,
      prix_vente_ht_eur: "1777.00",
      cout_revient_eur: "1421.60",
      calage_mutualise_eur: "0.00",
    },
    {
      ordre: 1,
      prix_vente_ht_eur: "638.50",
      cout_revient_eur: "510.80",
      calage_mutualise_eur: "200.00",
    },
  ],
  alertes: [
    {
      niveau: "info",
      message:
        "Le second lot partage le calage du premier : 200,00 € de mise en route economises.",
    },
  ],
};
