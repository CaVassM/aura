import { Insight } from "@/lib/types-coordinacion";

/**
 * Hallazgo principal: siempre sobre el total de desencuentros (sin filtros). Con filtros activos,
 * una línea secundaria dice qué pasa dentro del filtro.
 */
export default function InsightCard({
  insight,
  filtro,
}: {
  insight: Insight;
  filtro?: Insight | null;
}) {
  return (
    <div className="animate-fade-in border-l-4 border-co-coral bg-co-coral-tint px-5 py-4">
      <p className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-co-coral-ink">Hallazgo</p>
      <p className="mt-1 text-lg font-bold leading-snug text-co-navy">{insight.texto}</p>
      {filtro && (
        <p className="mt-2 border-t border-co-coral/30 pt-2 text-sm font-medium leading-snug text-co-navy">
          <span className="font-extrabold text-co-coral-ink">En este filtro:</span> {filtro.texto}
        </p>
      )}
    </div>
  );
}
