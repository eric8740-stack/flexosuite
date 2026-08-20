// Couche d'acces bas niveau au backend FastAPI.
//
// Base VIDE par defaut -> toutes les requetes sont RELATIVES (`/api/...`) et
// resolues par le navigateur contre l'origine de la page. L'appli marche donc a
// l'identique sur localhost, sur une IP LAN, et depuis le backend qui sert le
// front sur le meme port (mono-port). AUCUNE URL absolue en dur, nulle part.
//
// `NEXT_PUBLIC_API_URL` ne sert qu'en developpement, quand le front (:3000) et
// l'API (:8000) ont des origines differentes. Au build du package la variable
// est retiree : la base redevient relative.
export const BASE_API = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * Emis quand l'API repond 401 (session absente ou expiree).
 *
 * ⚠️ Rien ne l'ecoute encore, et c'est VOLONTAIRE : l'authentification arrive
 * avec le lot 2 du backend (contrat v1). La gestion de session et la
 * redirection ne seront figees qu'une fois le backend livre. En attendant, le
 * signal existe pour que le branchement se fasse en un seul endroit.
 */
export const SESSION_EXPIREE = "flexosuite:session-expiree";

/** Erreur d'appel portant le statut HTTP, pour que l'appelant puisse aiguiller
 *  (401 session, 409 installation requise) sans reparser un message. */
export class ErreurApi extends Error {
  readonly statut: number;

  constructor(statut: number, message: string) {
    super(message);
    this.name = "ErreurApi";
    this.statut = statut;
  }
}

/**
 * Lit le message clair du backend (`detail`, convention FastAPI et contrat).
 * Le contrat garantit qu'il est affichable tel quel a un deviseur.
 */
async function detailErreur(reponse: Response, repli: string): Promise<string> {
  try {
    const donnees = await reponse.json();
    if (typeof donnees?.detail === "string" && donnees.detail) {
      return donnees.detail;
    }
    if (Array.isArray(donnees?.detail)) {
      const messages = donnees.detail
        .map((d: { msg?: string }) => d?.msg)
        .filter(Boolean);
      if (messages.length) return messages.join(" ; ");
    }
  } catch {
    // reponse non JSON : on garde le message de repli
  }
  return repli;
}

async function requete<T>(chemin: string, options?: RequestInit): Promise<T> {
  const reponse = await fetch(`${BASE_API}/api${chemin}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    // Requis des que l'authentification par cookie arrivera (lot 2).
    credentials: "include",
    ...options,
  });

  if (reponse.status === 401 && typeof window !== "undefined") {
    window.dispatchEvent(new Event(SESSION_EXPIREE));
  }

  if (!reponse.ok) {
    throw new ErreurApi(
      reponse.status,
      await detailErreur(
        reponse,
        `Le serveur a repondu ${reponse.status} sur ${chemin}.`,
      ),
    );
  }

  if (reponse.status === 204) return undefined as T;
  return (await reponse.json()) as T;
}

export function lire<T>(chemin: string): Promise<T> {
  return requete<T>(chemin);
}

export function envoyer<T>(chemin: string, corps: unknown): Promise<T> {
  return requete<T>(chemin, { method: "POST", body: JSON.stringify(corps) });
}
