"use client";

import { Bell, ChevronDown, SlidersHorizontal } from "lucide-react";

/**
 * Esto es decorativo (igual que en tu Figma): "Escenario de demo" y el
 * selector "A · Lucía" no cambian nada todavía. Si luego quieren que el
 * selector cambie de usuario/escenario de verdad, conviértanlo en un
 * <select> controlado con useState — no hace falta para el Entregable 2.
 */
export default function TopbarControls() {
  return (
    <>
      <button className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-aura-gray hover:bg-aura-bg">
        <SlidersHorizontal size={15} />
        Escenario de demo
      </button>
      <button className="flex items-center gap-1.5 rounded-lg border border-aura-border bg-white px-3 py-1.5 text-sm font-medium text-aura-navy hover:bg-aura-bg">
        A · Lucía
        <ChevronDown size={14} />
      </button>
      <button className="rounded-full p-2 text-aura-gray hover:bg-aura-bg">
        <Bell size={18} />
      </button>
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-aura-purple-nav text-xs font-bold text-aura-purple">
        LM
      </div>
    </>
  );
}
