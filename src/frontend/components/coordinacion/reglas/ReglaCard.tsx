import { ReactNode } from "react";

/** Tarjeta numerada de una regla; muestra «Provisional» según lo que declara el backend. */
export default function ReglaCard({
  numero,
  titulo,
  provisional,
  children,
}: {
  numero: string;
  titulo: string;
  provisional: boolean;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl2 border border-aura-border bg-white p-5 shadow-card sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-aura-teal-pale text-xs font-extrabold text-aura-teal">
            {numero}
          </span>
          <h3 className="font-bold text-aura-navy">{titulo}</h3>
        </div>
        {provisional && (
          <span className="rounded-full border border-aura-tag-red-bg bg-[#FFF2EE] px-2.5 py-1 text-[10px] font-extrabold tracking-wide text-aura-tag-red-text">
            PROVISIONAL
          </span>
        )}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}
