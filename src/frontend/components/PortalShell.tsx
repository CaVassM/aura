"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { usePerfil } from "@/components/campus/PerfilProvider";

export interface NavItem {
  href: string;
  label: string;
  icon: ReactNode;
}

export interface PortalShellProps {
  brandIcon: ReactNode;
  brandIconBg: string; // clase tailwind, ej. "bg-co-bg"
  brandName: string;
  brandSubtitle: string;
  nav: NavItem[];
  activeHref: string;
  /** Si no se pasa, se usa el estudiante activo del selector de la demo. */
  user?: { name: string; role: string; initials: string; avatar?: string };
  sidebarFooter?: ReactNode;
  exitHref: string;
  exitLabel: string;
  title: string;
  subtitle: ReactNode;
  topbarRight?: ReactNode;
  children: ReactNode;
}

/**
 * Marco del campus del estudiante. Misma familia visual que el panel de Coordinación (barra lateral en
 * teal profundo, crema, acento ámbar) para que las dos vistas se sientan un solo producto.
 */
export default function PortalShell({
  brandIcon,
  brandIconBg,
  brandName,
  brandSubtitle,
  nav,
  activeHref,
  user,
  sidebarFooter,
  exitHref,
  exitLabel,
  title,
  subtitle,
  topbarRight,
  children,
}: PortalShellProps) {
  const { usuario } = usePerfil();
  const persona = user ?? usuario;

  return (
    <div className="flex h-screen overflow-hidden bg-co-bg text-co-navy">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col overflow-y-auto bg-co-teal-deep px-4 py-6 text-co-bg lg:flex">
        <div className="flex items-center gap-3 px-2">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${brandIconBg}`}>
            {brandIcon}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-extrabold leading-tight">{brandName}</p>
            <p className="truncate text-xs leading-tight text-co-bg/80">{brandSubtitle}</p>
          </div>
        </div>

        <nav className="mt-8 flex flex-1 flex-col gap-1" aria-label="Campus">
          {nav.map((item) => {
            const activo = item.href === activeHref;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={activo ? "page" : undefined}
                className={`co-foco relative flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-semibold transition-colors ${
                  activo ? "bg-white/10 text-white" : "text-co-bg/80 hover:bg-white/5 hover:text-white"
                }`}
              >
                {activo && <span className="absolute inset-y-2 left-0 w-1 rounded-r bg-co-amber" aria-hidden="true" />}
                <span className="shrink-0 [&>svg]:h-[18px] [&>svg]:w-[18px]">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-4 pt-6">
          {sidebarFooter}
          <div className="flex items-center gap-3 rounded-xl bg-white/5 px-3 py-2.5">
            <div
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-extrabold ${
                persona.avatar ?? "bg-co-teal-tint text-co-teal-dark"
              }`}
            >
              {persona.initials}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold leading-tight text-white">{persona.name}</p>
              <p className="truncate text-xs leading-tight text-co-bg/80">{persona.role}</p>
            </div>
          </div>
          <Link href={exitHref} className="co-foco block px-1 text-xs font-semibold text-co-bg/80 hover:text-white">
            ← {exitLabel}
          </Link>
        </div>
      </aside>

      <div className="flex h-screen min-w-0 flex-1 flex-col lg:pl-64">
        <header className="relative z-20 flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-b border-co-line bg-co-bg/80 px-6 py-4 backdrop-blur lg:px-10">
          <div className="min-w-0">
            <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-teal">Campus</p>
            <h1 className="truncate text-xl font-extrabold leading-tight text-co-navy">{title}</h1>
            <div className="text-sm leading-snug text-co-ink">{subtitle}</div>
          </div>
          {topbarRight && <div className="flex shrink-0 items-center gap-3">{topbarRight}</div>}
        </header>

        {/* Navegación compacta cuando no cabe la barra lateral */}
        <nav className="flex gap-1 overflow-x-auto border-b border-co-line px-4 py-2 lg:hidden" aria-label="Campus">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`co-foco whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-semibold ${
                item.href === activeHref ? "bg-co-teal text-white" : "text-co-ink"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
