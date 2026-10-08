"use client";

import { ReactNode, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Termino, textoGlosario } from "@/lib/glosario";
import { useDemo } from "./DemoProvider";

interface Posicion {
  x: number;
  y: number;
  abajo: boolean;
}

const ANCHO = 448; // 28 rem: los textos del glosario caben en 2 líneas

/**
 * Círculo con «i» junto a un término. Al pasar el cursor o enfocarlo con el teclado muestra un
 * globo corto con el texto del glosario (lib/glosario.ts). El globo se dibuja en un portal para
 * que no lo recorten las tablas con scroll.
 *
 * El globo solo existe mientras el cursor está sobre la «i» o el foco de teclado está en ella; se
 * cierra también al hacer scroll, redimensionar, hacer clic o mover el cursor a otro lado, para
 * que nunca quede un globo suelto en pantalla.
 */
export default function InfoTip({
  termino,
  texto,
  claro = false,
}: {
  termino?: Termino;
  /** Texto propio; si falta se usa el glosario. */
  texto?: string;
  /** Variante para fondos oscuros. */
  claro?: boolean;
}) {
  const { glosario } = useDemo();
  const contenido = texto ?? (termino ? textoGlosario(termino, glosario) : "");
  const id = useId();
  const boton = useRef<HTMLButtonElement>(null);
  const [pos, setPos] = useState<Posicion | null>(null);
  const origen = useRef<"hover" | "foco" | null>(null);

  function mostrar(desde: "hover" | "foco") {
    const r = boton.current?.getBoundingClientRect();
    if (!r) return;
    const ancho = Math.min(ANCHO, window.innerWidth * 0.8);
    const x = Math.min(Math.max(8, r.left + r.width / 2 - ancho / 2), window.innerWidth - ancho - 8);
    const abajo = r.top < 90; // sin espacio arriba: se muestra debajo
    origen.current = desde;
    setPos({ x, y: abajo ? r.bottom + 8 : r.top - 8, abajo });
  }

  const ocultar = () => {
    origen.current = null;
    setPos(null);
  };

  // Mientras hay globo: se cierra con scroll, resize, clic o si el cursor ya no está sobre la «i».
  useEffect(() => {
    if (!pos) return;
    const alMoverse = (e: PointerEvent) => {
      if (origen.current === "hover" && !boton.current?.contains(e.target as Node)) ocultar();
    };
    window.addEventListener("scroll", ocultar, true);
    window.addEventListener("resize", ocultar);
    window.addEventListener("pointerdown", ocultar, true);
    window.addEventListener("pointermove", alMoverse);
    return () => {
      window.removeEventListener("scroll", ocultar, true);
      window.removeEventListener("resize", ocultar);
      window.removeEventListener("pointerdown", ocultar, true);
      window.removeEventListener("pointermove", alMoverse);
    };
  }, [pos]);

  return (
    <>
      <button
        ref={boton}
        type="button"
        aria-label="Más información"
        aria-describedby={pos ? id : undefined}
        onMouseEnter={() => mostrar("hover")}
        onMouseLeave={() => origen.current === "hover" && ocultar()}
        onFocus={(e) => e.currentTarget.matches(":focus-visible") && mostrar("foco")}
        onBlur={ocultar}
        onKeyDown={(e) => e.key === "Escape" && ocultar()}
        className={`co-foco ml-1.5 inline-flex h-4 w-4 shrink-0 cursor-help items-center justify-center rounded-full border align-middle text-[10px] font-bold leading-none transition-colors ${
          claro
            ? "border-co-bg/70 text-co-bg hover:bg-co-bg hover:text-co-teal-deep focus-visible:bg-co-bg focus-visible:text-co-teal-deep"
            : "border-co-teal/60 text-co-teal hover:bg-co-teal hover:text-white focus-visible:bg-co-teal focus-visible:text-white"
        }`}
      >
        i
      </button>
      {pos &&
        createPortal(
          <div
            id={id}
            role="tooltip"
            style={{
              position: "fixed",
              left: pos.x,
              top: pos.y,
              width: Math.min(ANCHO, window.innerWidth * 0.8),
              transform: pos.abajo ? undefined : "translateY(-100%)",
            }}
            className="pointer-events-none z-[100] rounded-md bg-co-navy px-3 py-2 text-xs font-medium leading-snug text-co-bg shadow-pop"
          >
            {contenido}
          </div>,
          document.body,
        )}
    </>
  );
}

/** Etiqueta con su ⓘ: <ConInfo termino="nivel">Nivel</ConInfo>. */
export function ConInfo({ termino, children }: { termino: Termino; children: ReactNode }) {
  return (
    <span className="inline-flex items-center">
      {children}
      <InfoTip termino={termino} />
    </span>
  );
}
