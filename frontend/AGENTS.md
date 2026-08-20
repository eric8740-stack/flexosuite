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

`.env.development` n'est PAS versionne : le `.gitignore` de la racine exclut
`.env.*`. Sur un poste neuf, le creer a la main dans `frontend/` :

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIXTURES=1
```

- `NEXT_PUBLIC_API_URL` : le backend tourne sur son propre port en dev. Sans
  cette ligne, le front appelle `/api` sur son propre port (:3000) et recoit
  des 404.
- `NEXT_PUBLIC_FIXTURES` : a 1, les ecrans travaillent sur les fixtures
  fictives de `src/lib/fixtures/` tant que les endpoints du lot 2 n'existent
  pas. Ni l'une ni l'autre variable n'est definie au build du package : le
  chemin des fixtures y est du code mort et la base d'API redevient relative.
