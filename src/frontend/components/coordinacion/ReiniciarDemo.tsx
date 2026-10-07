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
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition disabled:opacity-60 ${
        falla
          ? "border-aura-tag-red-bg text-aura-tag-red-text"
          : "border-aura-border text-aura-gray hover:text-aura-navy"
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
