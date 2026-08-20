// Couche d'acces bas niveau au backend FastAPI.
//
// Base VIDE par defaut -> toutes les requetes sont RELATIVES (`/api/...`) et
// resolues par le navigateur contre l'origine de la page. L'appli marche donc a
// l'identique sur localhost et depuis le backend qui sert le front sur le meme
// port (mono-port). AUCUNE URL absolue en dur, nulle part.
//
// `NEXT_PUBLIC_API_URL` ne sert qu'en developpement, quand le front (3000) et
// l'API (8000) ont des origines differentes. Au build du package la variable est
// retiree : la base redevient relative.
//
// ⚠️ En developpement, employer partout le MEME nom d'hote - `localhost`, jamais
// `127.0.0.1`. Le port ne change pas la notion de same-site, l'hote si : melanger
// les deux rend le cookie `SameSite=Strict` cross-site, et la session ne tient
// pas, sans le moindre message d'erreur. Voir `AGENTS.md`.
export const BASE_API = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * Les codes d'erreur de la v1 du contrat. Ils sont **stables** : c'est la seule
 * chose sur laquelle le front a le droit d'aiguiller. Tout ajout passe par le
 * journal des changements de `docs/CONTRAT-API.md`.
 */
export const CODES_ERREUR = [
  "session_absente",
  "identifiants_invalides",
  "installation_requise",
  "installation_deja_faite",
  "calibration_requise",
  "mode_demo_lecture_seule",
  "origine_refusee",
  "introuvable",
  "payload_invalide",
  "regle_metier",
] as const;

export type CodeErreur = (typeof CODES_ERREUR)[number];

/**
 * Emis quand le backend signale une session absente ou expiree, c'est-a-dire
 * sur le code `session_absente` et sur lui seul.
 *
 * ⚠️ PAS sur tous les 401 : `identifiants_invalides` en est un aussi. Un front
 * qui traiterait le statut sans le code ejecterait l'utilisateur de l'ecran de
 * connexion a chaque faute de frappe.
 *
 * ⚠️ Rien ne l'ecoute encore, et c'est VOLONTAIRE : l'ecran de connexion et la
 * gestion de session arrivent avec le lot 2 du backend. Le signal existe pour
 * que le branchement se fasse plus tard en un seul endroit - aucune redirection
 * n'est cablee ici.
 */
export const SESSION_EXPIREE = "flexosuite:session-expiree";

/**
 * Erreur d'appel a l'API, portant les trois informations du contrat v1.
 *
 * - `statut` : le code HTTP.
 * - `code` : l'identifiant STABLE, pour la machine. `null` quand la reponse
 *   n'en porte pas (reponse anterieure a la v1, erreur d'infrastructure, corps
 *   non JSON). Un `null` n'est pas une valeur par defaut a interpreter : c'est
 *   l'aveu qu'on ne sait pas, et l'appelant doit rester prudent.
 * - `detail` : la phrase pour l'humain, affichable telle quelle a un deviseur.
 *   `null` si le backend n'en a pas fourni.
 *
 * ⚠️ Ne JAMAIS aiguiller sur `detail` ni sur `message` : ce sont des textes
 * destines a etre lus, donc reformulables a tout moment. Un aiguillage bati
 * dessus casse en silence a la premiere relecture.
 */
export class ErreurApi extends Error {
  readonly statut: number;
  readonly code: CodeErreur | null;
  readonly detail: string | null;

  constructor(
    statut: number,
    code: CodeErreur | null,
    detail: string | null,
    message: string,
  ) {
    super(message);
    this.name = "ErreurApi";
    this.statut = statut;
    this.code = code;
    this.detail = detail;
  }
}

/** Un code n'est retenu que s'il fait partie de la liste du contrat. Un code
 *  inconnu vaut `null` : mieux vaut ne pas savoir que croire savoir. */
function codeConnu(valeur: unknown): CodeErreur | null {
  return typeof valeur === "string" &&
    (CODES_ERREUR as readonly string[]).includes(valeur)
    ? (valeur as CodeErreur)
    : null;
}

/**
 * Extrait `code` et `detail` du corps d'erreur. Trois formes sont acceptees,
 * parce que les trois existent pour de vrai :
 *   1. `{ "code": "...", "detail": "..." }` - la forme du contrat v1 ;
 *   2. `{ "detail": "..." }` - une reponse anterieure a la v1, ou une
 *      HTTPException FastAPI ecrite avant que les codes n'existent ;
 *   3. `{ "detail": [ { "msg": "..." } ] }` - la validation 422 de FastAPI.
 * Tout le reste (corps vide, HTML d'un proxy, JSON inattendu) rend deux `null`.
 */
async function lireErreur(
  reponse: Response,
): Promise<{ code: CodeErreur | null; detail: string | null }> {
  let donnees: unknown;
  try {
    donnees = await reponse.json();
  } catch {
    return { code: null, detail: null };
  }

  if (typeof donnees !== "object" || donnees === null) {
    return { code: null, detail: null };
  }

  const corps = donnees as { code?: unknown; detail?: unknown };
  const code = codeConnu(corps.code);

  if (typeof corps.detail === "string" && corps.detail) {
    return { code, detail: corps.detail };
  }

  if (Array.isArray(corps.detail)) {
    const messages = corps.detail
      .map((d: { msg?: string }) => d?.msg)
      .filter((m): m is string => typeof m === "string" && m.length > 0);
    if (messages.length) return { code, detail: messages.join(" ; ") };
  }

  return { code, detail: null };
}

async function requete<T>(chemin: string, options?: RequestInit): Promise<T> {
  const reponse = await fetch(`${BASE_API}/api${chemin}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    // Requis par l'authentification par cookie (contrat v1).
    credentials: "include",
    ...options,
  });

  if (reponse.ok) {
    if (reponse.status === 204) return undefined as T;
    return (await reponse.json()) as T;
  }

  const { code, detail } = await lireErreur(reponse);

  // Le signal ne part que sur le code, jamais sur le statut : `session_absente`
  // et `identifiants_invalides` sont tous les deux des 401.
  if (code === "session_absente" && typeof window !== "undefined") {
    window.dispatchEvent(new Event(SESSION_EXPIREE));
  }

  throw new ErreurApi(
    reponse.status,
    code,
    detail,
    // Le message sert a l'AFFICHAGE et a la trace, jamais a l'aiguillage.
    detail ?? `Le serveur a repondu ${reponse.status} sur ${chemin}.`,
  );
}

export function lire<T>(chemin: string): Promise<T> {
  return requete<T>(chemin);
}

export function envoyer<T>(chemin: string, corps: unknown): Promise<T> {
  return requete<T>(chemin, { method: "POST", body: JSON.stringify(corps) });
}
