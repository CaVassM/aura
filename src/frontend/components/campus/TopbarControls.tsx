"use client";

import { Check, ChevronDown, MapPin } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { nombreDistrito } from "@/lib/perfiles";
import { usePerfil } from "./PerfilProvider";

/**
 * Selector de estudiante de la demo: cambia de verdad el `estudiante_id` y el distrito que se envían
 * al backend (cada perfil tiene su propio chat y sus propias citas).
 */
export default function TopbarControls() {
  const { perfil, perfiles, cambiar } = usePerfil();
  const [abierto, setAbierto] = useState(false);
  const caja = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!abierto) return;
    const fuera = (e: MouseEvent) => {
      if (!caja.current?.contains(e.target as Node)) setAbierto(false);
    };
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && setAbierto(false);
    document.addEventListener("mousedown", fuera);
    document.addEventListener("keydown", tecla);
    return () => {
      document.removeEventListener("mousedown", fuera);
      document.removeEventListener("keydown", tecla);
    };
  }, [abierto]);

  return (
    <div ref={caja} className="relative">
      <button
        onClick={() => setAbierto((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={abierto}
        className="co-foco flex items-center gap-2.5 rounded-full border border-co-line bg-white py-1.5 pl-1.5 pr-3 text-sm font-semibold text-co-navy shadow-card transition hover:border-co-teal"
      >
        <span className={`flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-extrabold ${perfil.avatar}`}>
          {perfil.iniciales}
        </span>
        <span className="hidden sm:inline">Demo · {perfil.corto}</span>
        <ChevronDown size={14} className={`text-co-ink transition-transform ${abierto ? "rotate-180" : ""}`} aria-hidden="true" />
      </button>

      {abierto && (
        <ul
          role="listbox"
          aria-label="Estudiante de la demo"
          className="absolute right-0 z-40 mt-2 w-72 origin-top-right animate-rise rounded-2xl border border-co-line bg-co-paper p-1.5 shadow-pop"
        >
          <li className="px-3 pb-1.5 pt-2 text-[11px] font-extrabold uppercase tracking-[0.14em] text-co-teal">
            Ver AURA como…
          </li>
          {perfiles.map((p) => {
            const activo = p.id === perfil.id;
            return (
              <li key={p.id} role="option" aria-selected={activo}>
                <button
                  onClick={() => {
                    cambiar(p.id);
                    setAbierto(false);
                  }}
                  className={`co-foco flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
                    activo ? "bg-co-teal-tint" : "hover:bg-co-bg"
                  }`}
                >
                  <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-extrabold ${p.avatar}`}>
                    {p.iniciales}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-bold text-co-navy">{p.nombre}</span>
                    <span className="flex items-center gap-1 text-xs text-co-ink">
                      <MapPin size={11} aria-hidden="true" />
                      Distrito {nombreDistrito(p.distrito)}
                    </span>
                  </span>
                  {activo && <Check size={16} className="shrink-0 text-co-teal" aria-hidden="true" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
