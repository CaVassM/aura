"use client";

import { useState } from "react";
import { Loader2, RotateCcw } from "lucide-react";
import { useDemo } from "./DemoProvider";

/** Botón discreto: vuelve a sembrar la demo y recarga los datos de todas las pantallas. */
export default function ReiniciarDemo() {
  const { reiniciar } = useDemo();
  const [reiniciando, setReiniciando] = useState(false);
  const [falla, setFalla] = useState(false);

  async function onClick() {
    const ok = window.confirm(
      "Se descartan las citas y desencuentros nuevos y se vuelve a sembrar la demo. ¿Continuar?",
    );
    if (!ok) return;
    setReiniciando(true);
    setFalla(false);
    try {
      await reiniciar();
    } catch {
      setFalla(true);
    } finally {
      setReiniciando(false);
    }
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={reiniciando}
      title={
        falla
          ? "No se pudo reiniciar la demo; revisa el backend"
          : "Vuelve a sembrar la demo y recarga los datos"
      }
      className={`co-foco inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold transition-colors disabled:opacity-60 ${
        falla
          ? "text-co-coral-ink hover:bg-co-coral-tint"
          : "text-co-ink hover:bg-co-teal-tint hover:text-co-navy"
      }`}
    >
      {reiniciando ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
      ) : (
        <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
      )}
      {falla ? "Error al reiniciar" : "Reiniciar demo"}
    </button>
  );
}
