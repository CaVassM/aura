"use client";

import Link from "next/link";
import { ReactNode } from "react";

export interface NavItem {
  href: string;
  label: string;
  icon: ReactNode;
}

export interface PortalShellProps {
  brandIcon: ReactNode;
  brandIconBg: string; // clase tailwind, ej. "bg-aura-purple-nav"
  brandName: string;
  brandSubtitle: string;
  nav: NavItem[];
  activeHref: string;
  user?: { name: string; role: string; initials: string };
  sidebarFooter?: ReactNode;
  exitHref: string;
  exitLabel: string;
  title: string;
  subtitle: string;
  topbarRight?: ReactNode;
  children: ReactNode;
}

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
  return (
    <div className="flex min-h-screen bg-aura-bg">
      {/* Sidebar */}
      <aside className="flex w-[280px] shrink-0 flex-col border-r border-aura-border bg-white px-5 py-6">
        <div className="flex items-center gap-3 px-1">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${brandIconBg}`}
          >
            {brandIcon}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold leading-tight text-aura-navy">
              {brandName}
            </p>
            <p className="truncate text-xs leading-tight text-aura-gray">
              {brandSubtitle}
            </p>
          </div>
        </div>

        <nav className="mt-7 flex flex-1 flex-col gap-1">
          {nav.map((item) => {
            const active = item.href === activeHref;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  active
                    ? "bg-aura-purple-nav text-aura-navy"
                    : "text-aura-gray hover:bg-aura-bg hover:text-aura-navy"
                }`}
              >
                <span className="shrink-0 [&>svg]:h-[18px] [&>svg]:w-[18px]">
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-3 pt-4">
          {sidebarFooter}
          {user && (
            <div className="flex items-center gap-2.5 rounded-xl px-1 py-1.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-aura-purple-nav text-xs font-bold text-aura-purple">
                {user.initials}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold leading-tight text-aura-navy">
                  {user.name}
                </p>
                <p className="truncate text-xs leading-tight text-aura-gray">
                  {user.role}
                </p>
              </div>
            </div>
          )}
          <Link
            href={exitHref}
            className="block px-1 text-xs font-medium text-aura-gray hover:text-aura-navy"
          >
            ← {exitLabel}
          </Link>
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-aura-border bg-white px-8 py-5">
          <div className="min-w-0">
            <h1 className="truncate text-lg font-bold text-aura-navy">
              {title}
            </h1>
            <p className="truncate text-sm text-aura-gray">{subtitle}</p>
          </div>
          {topbarRight && (
            <div className="flex shrink-0 items-center gap-3">
              {topbarRight}
            </div>
          )}
        </header>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
