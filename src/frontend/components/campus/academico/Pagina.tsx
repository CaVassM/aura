"use client";

import { ReactNode } from "react";
import PortalShell from "@/components/PortalShell";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav } from "@/components/campus/nav";

/** Marco común de las páginas académicas del campus (mismo lienzo que el chat y «Mis citas»). */
export default function Pagina({
  href,
  titulo,
  subtitulo,
  ancho = "max-w-5xl",
  children,
}: {
  href: string;
  titulo: string;
  subtitulo: ReactNode;
  ancho?: string;
  children: ReactNode;
}) {
  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref={href}
      exitHref="/"
      exitLabel="Salir del campus"
      title={titulo}
      subtitle={subtitulo}
      topbarRight={<TopbarControls />}
    >
      <div className="chat-lienzo min-h-full px-4 py-8 lg:px-8">
        <div className={`mx-auto ${ancho} space-y-6`}>{children}</div>
      </div>
    </PortalShell>
  );
}

export function Esqueleto({ bloques = [140, 220, 220] }: { bloques?: number[] }) {
  return (
    <div className="space-y-4" aria-hidden="true">
      {bloques.map((alto, i) => (
        <div key={i} style={{ height: alto }} className="animate-pulse rounded-3xl border border-co-line bg-white/70" />
      ))}
    </div>
  );
}
