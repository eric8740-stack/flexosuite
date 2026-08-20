// Base d'API : definie en developpement (deux ports), VIDE dans le package
// client (mono-port, meme origine). C'est ce basculement qui permet de
// developper sur deux ports sans casser la livraison.
export const BASE_API = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function appel<T>(chemin: string): Promise<T> {
  const r = await fetch(`${BASE_API}/api${chemin}`);
  if (!r.ok) throw new Error(`Appel ${chemin} en echec : ${r.status}`);
  return (await r.json()) as T;
}
