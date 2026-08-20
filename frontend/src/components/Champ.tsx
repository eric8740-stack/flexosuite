"use client";

import type { ReactNode } from "react";

/**
 * Un champ = un LIBELLE VISIBLE + sa saisie, et l'aide sous le champ plutot
 * qu'en infobulle. Regle du chantier : aucune information ne doit exister
 * uniquement au survol, parce qu'un ecran tactile n'a pas de survol.
 */
export function Champ({
  libelle,
  aide,
  htmlFor,
  children,
}: {
  libelle: string;
  aide?: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-sm font-medium text-texte">
        {libelle}
      </label>
      {children}
      {aide ? <p className="text-xs text-texte-doux">{aide}</p> : null}
    </div>
  );
}

export const classesSaisie =
  "min-h-11 w-full rounded-md border border-bordure bg-white px-3 py-2 text-base text-gray-900 outline-none focus-visible:ring-2 focus-visible:ring-accent";
