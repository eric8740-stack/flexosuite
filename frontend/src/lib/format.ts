// Formatage a l'affichage. Regle du contrat : les montants arrivent en CHAINE
// et le front NE CALCULE RIEN. On se contente donc de rendre lisible - separer
// les milliers, poser l'unite - jamais d'arrondir ni de convertir.

const NOMBRE_FR = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 3 });

/** "1777.00" -> "1 777,00 €". Une chaine non numerique est rendue telle quelle
 *  plutot que masquee : mieux vaut une valeur etrange visible qu'un trou. */
export function eur(montant: string): string {
  const n = Number(montant);
  if (!Number.isFinite(n)) return montant;
  return `${n.toLocaleString("fr-FR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} €`;
}

/** "300.00" -> "300 mm" ; "5.50" -> "5,5 mm". */
export function mm(valeur: string): string {
  const n = Number(valeur);
  if (!Number.isFinite(n)) return valeur;
  return `${NOMBRE_FR.format(n)} mm`;
}

/** Entier deja calcule par le backend (tours, metrage, poses). */
export function entier(valeur: number): string {
  return valeur.toLocaleString("fr-FR");
}

/** "49.90" -> "49,9 %". */
export function pourcent(valeur: string): string {
  const n = Number(valeur);
  if (!Number.isFinite(n)) return valeur;
  return `${NOMBRE_FR.format(n)} %`;
}

/** "1.00" -> "1,00" (coefficients de vitesse, gache, multiplicateur de marge). */
export function coefficient(valeur: string): string {
  const n = Number(valeur);
  if (!Number.isFinite(n)) return valeur;
  return n.toLocaleString("fr-FR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

/** Libelle d'une ressource de referentiel, sans supposer la cle exacte.
 *  Voir l'avertissement en tete de la section « Referentiels » des types. */
export function libelleRessource(
  ressource: { id: number; libelle?: string; nom?: string },
  defaut: string,
): string {
  return ressource.libelle ?? ressource.nom ?? `${defaut} n° ${ressource.id}`;
}
