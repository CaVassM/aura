import { ReactNode } from "react";

/** Título de sección con un acento de color (barra) y jerarquía clara; sin caja alrededor. */
export default function Seccion({
  titulo,
  info,
  derecha,
  acento = "bg-co-teal",
  children,
}: {
  titulo: string;
  info?: ReactNode;
  derecha?: ReactNode;
  acento?: string;
  children?: ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 className="flex items-center text-lg font-extrabold tracking-tight text-co-navy">
          <span className={`mr-2.5 h-5 w-1.5 rounded-full ${acento}`} aria-hidden="true" />
          {titulo}
          {info}
        </h2>
        {derecha}
      </div>
      {children}
    </section>
  );
}
