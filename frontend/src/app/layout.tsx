import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FlexoSuite",
  description: "Devis pour imprimeurs flexographiques",
};

// L'ecran est consulte debout devant une presse, souvent sur un telephone :
// le zoom reste autorise (jamais de maximum-scale), et la largeur suit
// l'appareil.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
