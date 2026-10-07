import { Lightbulb } from "lucide-react";
import { Insight } from "@/lib/types-coordinacion";

/** Hallazgo principal del conjunto filtrado (texto redactado por el backend). */
export default function InsightCard({ insight }: { insight: Insight }) {
  return (
    <div className="flex gap-4 rounded-xl2 border border-aura-tag-red-bg bg-[#FFF9F7] p-5 shadow-card">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-aura-tag-red-bg text-aura-tag-red-text">
        <Lightbulb className="h-5 w-5" aria-hidden="true" />
      </div>
      <div>
        <p className="text-xs font-bold uppercase tracking-wide text-aura-tag-red-text">
          Hallazgo
        </p>
        <p className="mt-1 text-base font-semibold leading-snug text-aura-navy">
          {insight.texto}
        </p>
      </div>
    </div>
  );
}
