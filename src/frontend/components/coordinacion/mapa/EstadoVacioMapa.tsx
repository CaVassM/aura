import { MapPinOff } from "lucide-react";

/** Superpuesto al mapa cuando los filtros no dejan ningún servicio. */
export default function EstadoVacioMapa({ onLimpiar }: { onLimpiar: () => void }) {
  return (
    <div className="absolute inset-0 z-30 flex animate-fade-only items-center justify-center bg-co-bg/75 p-6 backdrop-blur-[1px]">
      <div className="flex max-w-sm flex-col items-center gap-2 rounded-lg border border-dashed border-co-teal/50 bg-co-paper p-6 text-center">
        <MapPinOff className="h-6 w-6 text-co-teal" aria-hidden="true" />
        <p className="font-bold text-co-navy">Ningún servicio coincide con los filtros</p>
        <p className="text-sm text-co-ink">
          Con los datos actuales no hay servicios que cumplan todos los criterios (por ejemplo,
          ninguno está en alta demanda). Prueba con otros filtros.
        </p>
        <button
          type="button"
          onClick={onLimpiar}
          className="co-foco mt-1 rounded-md border border-co-teal px-4 py-2 text-sm font-bold text-co-teal hover:bg-co-teal-tint"
        >
          Limpiar filtros
        </button>
      </div>
    </div>
  );
}
