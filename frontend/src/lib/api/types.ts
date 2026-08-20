// Formes de reponse du backend, tenues par `docs/CONTRAT-API.md` (v1).
//
// Deux conventions du contrat, qui expliquent les types ci-dessous :
//   - les MONTANTS et les DIMENSIONS decimales sont des CHAINES ("1777.00"),
//     jamais des flottants. Le front les AFFICHE, il ne les calcule pas ;
//   - les comptages (poses, tours, metrage) sont des ENTIERS.

/** Message destine au deviseur, affichable tel quel. */
export type Alerte = {
  niveau: "info" | "attention";
  message: string;
};

export type Utilisateur = {
  identifiant: string;
  role: string;
};

/**
 * `GET /api/contexte` — ce que le front doit savoir avant d'afficher quoi que
 * ce soit. Les trois derniers champs arrivent avec le lot 2 : ils sont donc
 * optionnels ici, et leur absence ne doit rien casser.
 */
export type Contexte = {
  mode_demo: boolean;
  installation_faite?: boolean;
  calibration_faite?: boolean;
  utilisateur?: Utilisateur | null;
};

// --- Optimisation de pose ----------------------------------------------------

export type ContrainteClient = {
  intervalle_dev_min_mm?: string;
};

export type Forcages = {
  intervalle_laize_mm: string | null;
  nb_poses_laize: number | null;
  machine_id: number | null;
};

export type DemandeOptimisation = {
  format: { largeur_mm: number; hauteur_mm: number };
  quantite: number;
  nb_couleurs: number;
  matiere_id: number;
  contrainte_client?: ContrainteClient;
  options_codes?: string[];
  forcages?: Forcages;
};

export type Configuration = {
  id: string;
  rang: number;
  cylindre: { id: number; developpe_mm: string; nb_dents: number };
  machine: { id: number; nom: string; laize_utile_mm: string };
  poses: { laize: number; developpe: number; total: number };
  intervalles_mm: { laize: string; developpe: string };
  laizes_mm: { plaque: string; papier: string; chute_par_cote: string };
  /** `ml_total` est un ENTIER de metres, deja arrondi au superieur par le
   *  backend (1667 tours x 300 mm = 500,10 m -> 501). Ne jamais le recalculer. */
  metrage: { nb_tours: number; ml_total: number };
  rendement_pct: string;
  score: string;
  coefficients: { vitesse: string; gache: string };
  alertes: Alerte[];
};

/**
 * Proposition d'outil neuf quand aucun cylindre du parc ne convient.
 *
 * ⚠️ Le contrat v1 dit qu'elle est « chiffree » mais ne fige PAS ses champs, et
 * `docs/SPEC-METIER.md` non plus. Question posee a Eric pour CC1 le 20/08/2026.
 * Type volontairement permissif et rendu defensif (`ProportionOutil`) : le front
 * affiche ce qu'il recoit, il n'invente aucun nom de champ.
 */
export type OutilAFabriquer = Record<string, unknown>;

export type ReponseOptimisation = {
  configurations: Configuration[];
  aucun_outil_compatible: boolean;
  outil_a_fabriquer: OutilAFabriquer | null;
  alertes: Alerte[];
};

// --- Sens d'enroulement ------------------------------------------------------

export type SensEnroulement = {
  numero: number;
  libelle: string;
  /** Vue A, la planche presse. C'est elle que lit le poseur de cliches. */
  rotation_vue_planche: number;
  /** Vue C, la bobine deroulee chez le client. */
  rotation_vue_bobine: number;
  face: "exterieur" | "interieur";
};

export type ReponseSens = { sens: SensEnroulement[] };

// --- Chiffrage ---------------------------------------------------------------

export type ForfaitSousTraitance = {
  libelle: string;
  montant_eur: string;
};

export type LotChiffrage = {
  configuration_id: string;
  matiere_id: number;
  quantite: number;
  nb_couleurs_par_type: { quadri: number; pantone: number };
  changement_outil_cliche: boolean;
  options_codes: string[];
  forfaits_sous_traitance: ForfaitSousTraitance[];
  outil_existant: boolean;
  nb_traces: number;
  forme_speciale: boolean;
};

export type DemandeApercu = {
  lots: LotChiffrage[];
  marge_pct_override: string | null;
};

export type PosteCout = {
  numero: number;
  libelle: string;
  montant_eur: string;
};

export type DetailLot = {
  ordre: number;
  prix_vente_ht_eur: string;
  cout_revient_eur: string;
  /** Ce qu'un lot economise parce qu'il partage le calage du precedent.
   *  Argument commercial : le contrat impose de l'afficher. */
  calage_mutualise_eur: string;
};

export type ApercuChiffrage = {
  postes: PosteCout[];
  cout_revient_eur: string;
  marge_pct: string;
  /** Le coefficient multiplicateur (1.25 pour 25 %). A afficher A COTE du
   *  pourcentage : « 30 % » lu comme un taux de marque coute 9 % au devis. */
  coefficient: string;
  prix_vente_ht_eur: string;
  prix_au_mille_eur: string;
  nb_calages: number;
  details_par_lot: DetailLot[];
  alertes: Alerte[];
};

// --- Referentiels ------------------------------------------------------------
//
// ⚠️ Le contrat v1 (section 5) enumere les champs structurants EN PROSE, sans
// figer les cles JSON. On ne les devine donc pas : ces types se limitent a ce
// que l'ecran d'optimisation CONSOMME reellement, et le libelle est lu de
// maniere defensive (`libelleRessource`). Question posee a Eric pour CC1.

/** Ce dont l'ecran a besoin d'une ressource de referentiel : l'identifiant, et
 *  de quoi l'afficher. Les autres champs existent mais ne sont pas consommes. */
export type RessourceNommee = {
  id: number;
  libelle?: string;
  nom?: string;
};

/** Une matiere, telle que le selecteur du brief en a besoin. */
export type Matiere = RessourceNommee;

/** Une machine, pour le forcage de machine. `nom` est garanti par le contrat :
 *  il figure dans `configuration.machine.nom`. */
export type Machine = RessourceNommee;

/** Une option de finition. `code` est garanti : c'est lui qu'attend le champ
 *  `options_codes` de la demande d'optimisation et des lots de chiffrage. */
export type OptionFinition = RessourceNommee & { code: string };
