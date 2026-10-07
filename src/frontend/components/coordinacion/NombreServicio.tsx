import { Nivel } from "@/lib/types-coordinacion";
import Tag from "@/components/ui/Tag";
import { NIVEL_LABEL, NIVEL_TAG } from "./nivel";

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
  return (
    <span
      className={
        apilado
          ? "flex flex-col items-start gap-1"
          : "inline-flex flex-wrap items-center gap-x-2 gap-y-1"
      }
    >
      <span className="font-semibold text-aura-navy">{nombre}</span>
      <span className="rounded-md bg-aura-teal-pale px-1.5 py-0.5 text-[11px] font-semibold text-aura-teal">
        {tipoLabel}
      </span>
    </span>
  );
}

export function NivelTag({ nivel }: { nivel: Nivel }) {
  return <Tag variant={NIVEL_TAG[nivel]}>{NIVEL_LABEL[nivel]}</Tag>;
}
