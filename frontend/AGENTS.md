<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

<!-- Ajout FlexoSuite (hors bloc genere) -->

## Les trois interdits de ce depot

Le front est **exporte en statique** (`NEXT_OUTPUT=export`) et servi par le
backend FastAPI sur un seul port. Sont donc interdits, et la CI les refuse :

1. toute route API Next (`src/**/route.ts`) ;
2. tout middleware (`src/middleware.ts`) ;
3. toute server action (`"use server"`).

Chacun des trois casse l'export, donc le package Windows, donc la livraison.

## Base d'API

Tous les appels passent par `src/lib/api/client.ts`. **Aucune URL absolue en
dur** : en developpement `NEXT_PUBLIC_API_URL` pointe le backend sur son port
(`.env.development`), au build du package la variable est absente et la base
redevient relative (meme origine).

## Demarrage en developpement

Deux reglages, un de chaque cote. **Il en faut les deux** : le front doit savoir
ou joindre l'API, et le backend doit autoriser l'origine du front.

### 1. Cote backend, avant de lancer uvicorn (PowerShell)

```powershell
$env:CORS_ORIGINES="http://localhost:3000"
```

Le partage d'origine est **vide par defaut** : le middleware n'est monte que si
des origines sont explicitement listees. C'est voulu — le package Windows et la
demo sont mono-port et n'en ont aucun besoin.

⚠️ **Sans cette variable, le navigateur bloque les appels sans que le backend
ne voie rien passer.** Il n'y a ni 4xx ni 5xx a lire cote serveur : le refus est
pris par le navigateur, sur la base des en-tetes de reponse. Le seul endroit ou
ca se voit est la console du navigateur (`blocked by CORS policy`). Un ecran
vide sans erreur serveur, en developpement, commence par cette verification.

### 2. Cote front, dans `frontend/.env.development`

Ce fichier n'est **pas versionne** : le `.gitignore` de la racine exclut
`.env.*`. Sur un poste neuf, le creer a la main :

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIXTURES=1
```

- `NEXT_PUBLIC_API_URL` : le backend tourne sur son propre port en dev. Sans
  cette ligne, le front appelle `/api` sur son propre port (3000) et recoit
  des 404.
- `NEXT_PUBLIC_FIXTURES` : a 1, les ecrans travaillent sur les fixtures
  fictives de `src/lib/fixtures/` tant que les endpoints du lot 2 n'existent
  pas. Ni l'une ni l'autre variable n'est definie au build du package : le
  chemin des fixtures y est du code mort et la base d'API redevient relative.

### ⚠️ Un seul nom d'hote partout : `localhost`

Dans **tous** les exemples, la ligne de commande, le navigateur et les deux
reglages ci-dessus : **`localhost`, jamais `127.0.0.1`**. Ne pas melanger les
deux, meme le temps d'un essai.

Le **port** ne change pas la notion de *same-site* — `localhost:3000` et
`localhost:8000` sont same-site. L'**hote**, si : `localhost` et `127.0.0.1`
sont deux hotes differents, donc **cross-site**. Le cookie de session etant fige
en `SameSite=Strict` (contrat v1), un melange des deux fait que **la session ne
tient pas** : le cookie est bien pose, il n'est simplement jamais renvoye. Aucun
message d'erreur ne le dit — on voit seulement une reconnexion a chaque appel.

## Erreurs : aiguiller sur `code`, jamais sur `detail`

Le contrat v1 impose `{"code": "...", "detail": "..."}` sur **toute** erreur.
Les deux champs ont deux publics :

- **`code`** est pour la machine. Identifiant stable, c'est le SEUL sur lequel
  le front a le droit d'aiguiller.
- **`detail`** est pour l'humain. Affichable tel quel a un deviseur, et
  **reformulable a tout moment** : un aiguillage bati dessus casse en silence a
  la premiere relecture du texte.

`ErreurApi` (`src/lib/api/client.ts`) porte les trois : `statut`, `code`,
`detail`. Un `code` a `null` signale une reponse qui n'en porte pas encore —
le front reste alors prudent plutot que de deviner.

⚠️ **Deux codes differents partagent le 401** : `session_absente` (rediriger
vers la connexion) et `identifiants_invalides` (rester sur la connexion).
Traiter tout 401 comme une session expiree ejecterait l'utilisateur de l'ecran
de connexion a chaque faute de frappe. Le statut HTTP seul ne suffit donc pas.
