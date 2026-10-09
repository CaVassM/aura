import { ArrowRight, Layers } from "lucide-react";
import { LoteOferta } from "@/lib/types";

/**
 * Se muestra cuando todo lo compatible está en servicios en modo lote (ocupación alta): en vez de opciones para
 * elegir, se ofrece entrar al lote, que asigna en conjunto y se cierra solo.
 */
export default function LoteOfertaCard({
  oferta,
  activa,
  onEntrar,
  onCambiar,
  conOpciones = false,
}: {
  oferta: LoteOferta;
  activa: boolean;
  onEntrar: () => void;
  onCambiar: () => void;
  /** El lote se ofrece junto a opciones de otro servicio compatible (el que la persona quiere está en lote). */
  conOpciones?: boolean;
}) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-co-amber/50 bg-gradient-to-br from-co-amber-tint to-co-paper p-5 shadow-card animate-rise transition ${
        activa ? "" : "opacity-60 saturate-50"
      }`}
    >
      <span className="absolute inset-y-0 left-0 w-1.5 bg-co-amber" aria-hidden="true" />
      <div className="flex items-start gap-3 pl-1">
        <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-co-amber text-white">
          <Layers size={18} aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-co-amber-ink">
            {conOpciones ? "¿Prefieres ese servicio?" : "Servicios muy ocupados"}
          </p>
          <p className="mt-0.5 text-sm font-bold leading-snug text-co-navy">
            {oferta.servicios.length ? oferta.servicios.join(" · ") : "Los servicios compatibles"} superan el {Math.round(oferta.umbral_pct)} % de
            ocupación.
          </p>
          <p className="mt-1.5 text-xs font-medium leading-relaxed text-co-ink">
            Sus cupos se reparten en un <strong className="font-extrabold">lote</strong>: un grupo de solicitudes se asigna en
            conjunto y el lote se cierra solo en {oferta.ventana_s} segundos (o al juntar {oferta.tamano_maximo}). El día y la hora los
            decide el lote{oferta.pendientes > 0 ? `; ya hay ${oferta.pendientes} esperando` : ""}.
          </p>
        </div>
      </div>
      {activa && (
        <div className="mt-4 flex flex-wrap items-center gap-2 pl-1">
          <button
            type="button"
            onClick={onEntrar}
            className="co-foco inline-flex items-center gap-1.5 rounded-full bg-gradient-to-br from-co-teal to-co-teal-deep px-5 py-2.5 text-sm font-bold text-white shadow-card transition hover:-translate-y-0.5 hover:shadow-lift"
          >
            Entrar al lote
            <ArrowRight size={14} aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={onCambiar}
            className="co-foco rounded-full border border-co-line bg-white px-4 py-2.5 text-sm font-bold text-co-ink transition hover:border-co-teal hover:text-co-navy"
          >
            {conOpciones ? "Me quedo con las opciones de arriba" : "Prefiero cambiar mis horarios"}
          </button>
        </div>
      )}
    </div>
  );
}
