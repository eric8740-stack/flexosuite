// @vitest-environment jsdom
//
// Ce que ces tests verrouillent : le front aiguille sur `code`, JAMAIS sur le
// texte de `detail`, et un 401 ne vaut pas a lui seul « session expiree ».
//
// Ce qu'ils NE prouvent PAS : qu'un ecran reagit correctement a ces erreurs.
// Aucun ecran d'authentification n'est livre, rien n'ecoute encore le signal de
// session. Ces tests couvrent la couche de transport, pas un comportement
// metier - qui n'existe pas.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ErreurApi, SESSION_EXPIREE, lire } from "./client";

/** Fabrique une reponse d'erreur JSON, comme le backend l'enverrait. */
function reponseErreur(statut: number, corps: unknown): Response {
  return new Response(JSON.stringify(corps), {
    status: statut,
    headers: { "Content-Type": "application/json" },
  });
}

function simuler(reponse: Response) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(reponse)),
  );
}

/** Recupere l'ErreurApi d'un appel qui doit echouer, en la TYPANT : sans ca,
 *  `catch (e) => e` rend `unknown` et le type-check du build echoue. Le helper
 *  echoue aussi si l'appel reussit - un test qui ne verifie rien est pire
 *  qu'un test absent. */
async function erreurDe(appel: Promise<unknown>): Promise<ErreurApi> {
  try {
    await appel;
  } catch (e) {
    if (e instanceof ErreurApi) return e;
    throw e;
  }
  throw new Error("L'appel aurait du echouer, il a reussi.");
}

/** Compte les evenements de session expiree emis pendant un appel. */
function compteurSession() {
  const ecouteur = vi.fn();
  window.addEventListener(SESSION_EXPIREE, ecouteur);
  return {
    nombre: () => ecouteur.mock.calls.length,
    detacher: () => window.removeEventListener(SESSION_EXPIREE, ecouteur),
  };
}

let session: ReturnType<typeof compteurSession>;

beforeEach(() => {
  session = compteurSession();
});

afterEach(() => {
  session.detacher();
  vi.unstubAllGlobals();
});

describe("lecture du corps d'erreur", () => {
  it("conserve `code` et `detail` de la forme du contrat v1", async () => {
    simuler(
      reponseErreur(409, {
        code: "installation_requise",
        detail: "Aucun compte n'existe encore.",
      }),
    );

    const erreur = await erreurDe(lire("/matieres"));

    expect(erreur).toBeInstanceOf(ErreurApi);
    expect(erreur.statut).toBe(409);
    expect(erreur.code).toBe("installation_requise");
    expect(erreur.detail).toBe("Aucun compte n'existe encore.");
    // Le message affichable reprend `detail` tel quel : le contrat garantit
    // qu'il est lisible par un deviseur.
    expect(erreur.message).toBe("Aucun compte n'existe encore.");
  });

  it("reste defensif sur une ancienne reponse sans `code`", async () => {
    simuler(reponseErreur(404, { detail: "Matiere introuvable." }));

    const erreur = await erreurDe(lire("/matieres/999"));

    expect(erreur).toBeInstanceOf(ErreurApi);
    expect(erreur.statut).toBe(404);
    // `null` = « on ne sait pas », surtout pas un code devine a partir du statut.
    expect(erreur.code).toBeNull();
    expect(erreur.detail).toBe("Matiere introuvable.");
  });

  it("ignore un `code` absent de la liste du contrat", async () => {
    simuler(reponseErreur(400, { code: "code_invente", detail: "Refus." }));

    const erreur = await erreurDe(lire("/devis/apercu"));

    expect(erreur.code).toBeNull();
    expect(erreur.detail).toBe("Refus.");
  });

  it("rend un message de repli quand le corps n'est pas exploitable", async () => {
    simuler(new Response("<html>502</html>", { status: 502 }));

    const erreur = await erreurDe(lire("/matieres"));

    expect(erreur.code).toBeNull();
    expect(erreur.detail).toBeNull();
    expect(erreur.message).toContain("502");
  });

  it("aplatit le `detail` liste d'une validation 422", async () => {
    simuler(
      reponseErreur(422, {
        code: "payload_invalide",
        detail: [{ msg: "largeur_mm requis" }, { msg: "quantite requise" }],
      }),
    );

    const erreur = await erreurDe(lire("/optimisation/configurations"));

    expect(erreur.code).toBe("payload_invalide");
    expect(erreur.detail).toBe("largeur_mm requis ; quantite requise");
  });
});

describe("les deux 401 ne se traitent pas pareil", () => {
  it("`session_absente` emet le signal de session expiree", async () => {
    simuler(
      reponseErreur(401, {
        code: "session_absente",
        detail: "Votre session a expire.",
      }),
    );

    const erreur = await erreurDe(lire("/devis"));

    expect(erreur.statut).toBe(401);
    expect(erreur.code).toBe("session_absente");
    expect(session.nombre()).toBe(1);
  });

  it("`identifiants_invalides` n'emet AUCUN signal, malgre le meme 401", async () => {
    simuler(
      reponseErreur(401, {
        code: "identifiants_invalides",
        detail: "Identifiant ou mot de passe incorrect.",
      }),
    );

    const erreur = await erreurDe(lire("/auth/moi"));

    expect(erreur.statut).toBe(401);
    expect(erreur.code).toBe("identifiants_invalides");
    // Le cas qui justifie tout ce test : traiter le statut sans le code
    // ejecterait l'utilisateur de l'ecran de connexion a chaque faute de frappe.
    expect(session.nombre()).toBe(0);
  });

  it("un 401 sans `code` n'emet rien non plus", async () => {
    simuler(reponseErreur(401, { detail: "Non autorise." }));

    const erreur = await erreurDe(lire("/devis"));

    expect(erreur.code).toBeNull();
    // On ne devine pas : sans code, on ne sait pas si c'est une session perdue
    // ou un refus d'identifiants. Le silence est la reponse prudente.
    expect(session.nombre()).toBe(0);
  });
});

describe("appels qui reussissent", () => {
  it("rend le corps JSON tel quel", async () => {
    simuler(
      new Response(JSON.stringify({ statut: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(lire("/sante")).resolves.toEqual({ statut: "ok" });
    expect(session.nombre()).toBe(0);
  });

  it("rend `undefined` sur un 204 sans tenter de lire un corps", async () => {
    simuler(new Response(null, { status: 204 }));

    await expect(lire("/devis/1")).resolves.toBeUndefined();
  });
});
