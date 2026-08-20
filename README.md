# FlexoSuite

Application de **devis pour imprimeurs flexographiques** — catalogue d'outils,
recherche de format, chiffrage.

Elle s'installe **sur le serveur de l'imprimerie**. Ses tarifs, ses clients et ses
coûts machine ne quittent jamais sa machine : pas de cloud obligatoire, pas de
base de données serveur à installer, un seul processus et un seul port.

> **État : en construction.** Le dépôt ne contient pour l'instant que la
> documentation de reprise et le cahier de recette métier. Voir
> [`docs/REPRISE.md`](docs/REPRISE.md) et [`docs/PLAN.md`](docs/PLAN.md).

## D'où ça vient

L'outil naît de 28 ans passés chez un imprimeur d'étiquettes 100 % flexo —
opérateur, chef d'équipe, puis responsable d'atelier (2014-2024), en appui
technique du deviseur : poses, outils, formats, contraintes machine.

Sa logique centrale est le **« format approchant »** : réutiliser un outil
quasi compatible plutôt que d'en fabriquer un neuf.

## Architecture

- **SQLite** — rien d'autre à installer chez le client.
- **Front Next.js en export statique**, servi par le backend FastAPI :
  un seul processus, un seul port.
- **Runtime Python portable embarqué**, wheels binaires uniquement.
- **Code et données séparés** : les données vivent dans `%ProgramData%\FlexoSuite`,
  hors du dossier de code — une mise à jour ne peut rien détruire.

## Démarrage en développement

En développement **seulement**, le front tourne sur son propre port et parle au
backend sur le sien. Il faut alors **deux** réglages, un de chaque côté. Les
oublier ne donne pas un message clair : le front part en 404, ou le navigateur
bloque les appels sans que le backend voie quoi que ce soit.

### 1. Côté front — recopier le modèle

`frontend/.env.example` est versionné ; le fichier réel ne l'est pas.

```powershell
Copy-Item frontend\.env.example frontend\.env.development
```

Il contient :

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIXTURES=1
```

### 2. Côté backend — autoriser le partage d'origine

```powershell
$env:CORS_ORIGINES="http://localhost:3000"
```

Puis, depuis `backend\` :

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Lancer le front

```powershell
cd frontend
npm run dev
```

### Ce qu'il faut savoir avant de chercher une panne

**Sans `CORS_ORIGINES`, le navigateur bloque les appels — c'est voulu.** Le
partage d'origine n'existe que si on le demande : les deux livrables tournent en
mono-port et n'en ont aucun besoin, et un réglage permissif par défaut finirait
livré chez le client.

> ⚠️ **Employez `localhost` des deux côtés, jamais un mélange.** `127.0.0.1` et
> `localhost` sont deux hôtes **différents** pour la règle *same-site* : les
> mélanger produit une session qui « ne tient pas », **sans le moindre message
> d'erreur**. Le port, lui, n'entre pas dans la définition et n'a donc aucune
> importance.

**Aucun fichier `.env` réel n'est versionné.** Seul `frontend/.env.example`
l'est : le `.gitignore` ignore `.env.*`, puis lève l'exception sur **ce chemin
précis** — pas sur un motif comme `**/.env.example`, qui rendrait versionnable
d'avance un modèle que personne n'a relu. Un futur modèle s'ajoutera ligne
par ligne.

Au build du package, `NEXT_PUBLIC_API_URL` est **retirée** : la base d'API
redevient relative, et le backend sert le front. C'est ce qui rend le mono-port
possible.

## Documentation

| Document | Contenu |
| --- | --- |
| [`docs/SPEC-METIER.md`](docs/SPEC-METIER.md) | Le cahier de recette : valeurs de référence, paramétrage, formules des 7 postes de coût |
| [`docs/REPRISE.md`](docs/REPRISE.md) | L'état réel du chantier |
| [`docs/PLAN.md`](docs/PLAN.md) | Les lots et leurs critères de sortie |

## Données

Tout ce qui figure dans ce dépôt est **fictif** : aucun nom de client, aucun nom
d'imprimeur, aucune donnée réelle.
