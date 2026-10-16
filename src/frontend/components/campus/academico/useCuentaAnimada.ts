"use client";

import { useEffect, useState } from "react";

/** Sube de 0 a `objetivo` con una curva suave (la cifra «se cuenta» al aparecer). Sin animación si la persona la desactivó. */
export function useCuentaAnimada(objetivo: number, duracionMs = 1000, retrasoMs = 0): number {
  const [valor, setValor] = useState(0);

  useEffect(() => {
    // Si la animación no puede correr (movimiento reducido, pestaña oculta o sin rAF) se muestra el valor final.
    const sinAnimacion =
      typeof window.requestAnimationFrame !== "function" ||
      document.hidden ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (sinAnimacion) {
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
    const terminar = () => {
      window.clearTimeout(arranque);
      cancelAnimationFrame(cuadro);
      setValor(objetivo);
    };
    const seguro = window.setTimeout(terminar, retrasoMs + duracionMs + 300); // rAF no corre en una pestaña oculta
    const alCambiarVisibilidad = () => document.hidden && terminar();
    document.addEventListener("visibilitychange", alCambiarVisibilidad);
    return () => {
      window.clearTimeout(arranque);
      window.clearTimeout(seguro);
      cancelAnimationFrame(cuadro);
      document.removeEventListener("visibilitychange", alCambiarVisibilidad);
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
