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

## Documentation

| Document | Contenu |
| --- | --- |
| [`docs/SPEC-METIER.md`](docs/SPEC-METIER.md) | Le cahier de recette : valeurs de référence, paramétrage, formules des 7 postes de coût |
| [`docs/REPRISE.md`](docs/REPRISE.md) | L'état réel du chantier |
| [`docs/PLAN.md`](docs/PLAN.md) | Les lots et leurs critères de sortie |

## Données

Tout ce qui figure dans ce dépôt est **fictif** : aucun nom de client, aucun nom
d'imprimeur, aucune donnée réelle.
