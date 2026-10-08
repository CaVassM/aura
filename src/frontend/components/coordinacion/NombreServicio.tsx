import { Nivel } from "@/lib/types-coordinacion";
import { NIVEL_BG, NIVEL_INK, NIVEL_LABEL } from "./nivel";

/**
 * Nombre del servicio (D6) junto con su tipo: nombres como «Espacio Brújula Orientación»
 * pueden confundirse con orientación vocacional, así que el tipo siempre va a la vista.
 */
export default function NombreServicio({
  nombre,
  tipoLabel,
  apilado = false,
}: {
  nombre: string;
  tipoLabel: string;
  apilado?: boolean;
}) {
  return apilado ? (
    <span className="flex flex-col">
      <span className="font-bold text-co-navy">{nombre}</span>
      <span className="text-xs font-semibold text-co-teal">{tipoLabel}</span>
    </span>
  ) : (
    <span>
      <span className="font-bold text-co-navy">{nombre}</span>
      <span className="text-xs font-semibold text-co-teal"> · {tipoLabel}</span>
    </span>
  );
}

/** Nivel como punto de color + palabra (sin cápsula). */
export function NivelTag({ nivel }: { nivel: Nivel }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-bold ${NIVEL_INK[nivel]}`}>
      <span className={`h-2 w-2 rounded-full ${NIVEL_BG[nivel]}`} aria-hidden="true" />
      {NIVEL_LABEL[nivel]}
    </span>
  );
}
