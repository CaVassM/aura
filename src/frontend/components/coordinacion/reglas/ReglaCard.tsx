import { ReactNode } from "react";
import { Termino } from "@/lib/glosario";
import { ConInfo } from "../InfoTip";

/**
 * Bloque numerado de una regla, separado por una línea (no una caja). Muestra «Provisional» según
 * lo que declara el backend y un ⓘ con una frase simple.
 */
export default function ReglaCard({
  numero,
  titulo,
  termino,
  provisional,
  children,
}: {
  numero: string;
  titulo: string;
  termino: Termino;
  provisional: boolean;
  children: ReactNode;
}) {
  return (
    <section className="animate-fade-in border-t-2 border-co-navy/80 pt-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="flex items-center gap-3 text-lg font-extrabold text-co-navy">
          <span className="tabular text-2xl font-extrabold text-co-teal">{numero}</span>
          <ConInfo termino={termino}>{titulo}</ConInfo>
        </h2>
        {provisional && (
          <span className="rounded bg-co-amber-tint px-2 py-1 text-[11px] font-extrabold uppercase tracking-wide text-co-amber-ink">
            Provisional
          </span>
        )}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}
