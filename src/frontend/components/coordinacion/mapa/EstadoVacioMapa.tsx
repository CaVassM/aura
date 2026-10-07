import { MapPinOff } from "lucide-react";

/** Superpuesto al mapa cuando los filtros no dejan ningún servicio. */
export default function EstadoVacioMapa({ onLimpiar }: { onLimpiar: () => void }) {
  return (
    <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/70 p-6 backdrop-blur-[1px]">
      <div className="flex max-w-sm flex-col items-center gap-2 rounded-2xl border border-dashed border-aura-border bg-white p-6 text-center shadow-card">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-aura-purple-nav text-aura-purple">
          <MapPinOff className="h-5 w-5" aria-hidden="true" />
        </div>
        <p className="font-semibold text-aura-navy">
          Ningún servicio coincide con los filtros
        </p>
        <p className="text-sm text-aura-gray">
          Con los datos actuales no hay servicios que cumplan todos los
          criterios (por ejemplo, ninguno está en alta demanda). Prueba con
          otros filtros.
        </p>
        <button
          type="button"
          onClick={onLimpiar}
          className="mt-1 rounded-xl border border-aura-teal px-4 py-2 text-sm font-semibold text-aura-teal hover:bg-aura-teal-pale"
        >
          Limpiar filtros
        </button>
      </div>
    </div>
  );
}
