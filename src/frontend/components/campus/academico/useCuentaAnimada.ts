"use client";

import { useEffect, useState } from "react";

/** Sube de 0 a `objetivo` con una curva suave (la cifra «se cuenta» al aparecer). Sin animación si la persona la desactivó. */
export function useCuentaAnimada(objetivo: number, duracionMs = 1000, retrasoMs = 0): number {
  const [valor, setValor] = useState(0);

  useEffect(() => {
    if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setValor(objetivo);
      return;
    }
    let cuadro = 0;
    let inicio: number | null = null;
    const arranque = window.setTimeout(() => {
      const paso = (t: number) => {
        inicio ??= t;
        const p = Math.min((t - inicio) / duracionMs, 1);
        setValor(objetivo * (1 - Math.pow(1 - p, 3)));
        if (p < 1) cuadro = requestAnimationFrame(paso);
      };
      cuadro = requestAnimationFrame(paso);
    }, retrasoMs);
    return () => {
      window.clearTimeout(arranque);
      cancelAnimationFrame(cuadro);
    };
  }, [objetivo, duracionMs, retrasoMs]);

  return valor;
}

/** `false` el primer cuadro y `true` enseguida: sirve para que una barra o un anillo crezcan con transición CSS. */
export function useListo(retrasoMs = 60): boolean {
  const [listo, setListo] = useState(false);
  useEffect(() => {
    const t = window.setTimeout(() => setListo(true), retrasoMs);
    return () => window.clearTimeout(t);
  }, [retrasoMs]);
  return listo;
}
