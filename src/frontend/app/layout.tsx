import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

// La tipografía de tu Figma se ve como una geométrica redondeada tipo
// Plus Jakarta Sans / Inter. Si tu Figma usa otra fuente puntual, solo
// cambia el nombre importado arriba y abajo — el resto del proyecto no
// se entera, porque todos los componentes heredan font-sans.
const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "AURA — Tu bienestar, más cerca",
  description:
    "Agendamiento conversacional para servicios de bienestar estudiantil",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className={`${jakarta.variable} font-sans text-aura-navy antialiased`}>
        {children}
      </body>
    </html>
  );
}
