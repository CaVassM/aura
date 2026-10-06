import { ServiceOption } from "@/lib/types";

const MODALIDAD_LABEL: Record<ServiceOption["modalidad"], string> = {
  presencial: "Presencial",
  online: "Online",
  telefónico: "Teléfono",
};

export default function ServiceCard({
  service,
  onSelect,
}: {
  service: ServiceOption;
  onSelect: (s: ServiceOption) => void;
}) {
  return (
    <button
      onClick={() => onSelect(service)}
      className="ml-11 w-[calc(100%-2.75rem)] max-w-md rounded-xl border border-aura-border bg-white p-4 text-left shadow-card transition hover:border-aura-teal/40"
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-semibold text-aura-navy">
          {service.nombre}
        </p>
        <span className="shrink-0 rounded-full bg-aura-teal-pale px-2 py-1 text-[11px] font-medium text-aura-teal">
          {MODALIDAD_LABEL[service.modalidad]}
        </span>
      </div>
      <p className="mt-1 text-xs text-aura-gray">{service.descripcion}</p>
      <p className="mt-2 text-xs text-aura-gray">
        Espera estimada:{" "}
        <span className="font-medium text-aura-navy">
          {service.esperaEstimadaDias} día
          {service.esperaEstimadaDias === 1 ? "" : "s"}
        </span>
      </p>
    </button>
  );
}
