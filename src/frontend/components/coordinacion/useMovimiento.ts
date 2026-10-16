"use client";

import { useEffect, useRef, useState } from "react";

/** true si la persona pidió menos movimiento (prefers-reduced-motion). */
export function useReducedMotion(): boolean {
  const [reducido, setReducido] = useState(false);
  useEffect(() => {
    const consulta = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducido(consulta.matches);
    const alCambiar = (e: MediaQueryListEvent) => setReducido(e.matches);
    consulta.addEventListener("change", alCambiar);
    return () => consulta.removeEventListener("change", alCambiar);
  }, []);
  return reducido;
}

/** ¿Puede correr una animación con requestAnimationFrame? No en una pestaña oculta ni sin rAF. */
export function puedeAnimar(): boolean {
  return typeof requestAnimationFrame === "function" && typeof document !== "undefined" && !document.hidden;
}

/**
 * Número que sube (o baja) suavemente hasta `objetivo`: al cargar y cada vez que cambia.
 *
 * El valor final SIEMPRE llega a mostrarse: con movimiento reducido, con la pestaña oculta o sin requestAnimationFrame
 * salta directo al final; y un temporizador de seguridad lo fija si la animación no avanzó (el navegador no ejecuta rAF en
 * una pestaña en segundo plano, y el contador se quedaría en 0).
 */
export function useCountUp(objetivo: number, duracion = 900): number {
  const reducido = useReducedMotion();
  const [valor, setValor] = useState(0);
  const actual = useRef(0);

  useEffect(() => {
    const fijar = () => {
      actual.current = objetivo;
      setValor(objetivo);
    };
    if (reducido || !puedeAnimar()) {
      fijar();
      return;
    }
    const desde = actual.current;
    const inicio = performance.now();
    let cuadro = 0;
    const paso = (ahora: number) => {
      const progreso = Math.min(1, (ahora - inicio) / duracion);
      const suave = 1 - Math.pow(1 - progreso, 3); // ease-out cúbico
      actual.current = desde + (objetivo - desde) * suave;
      setValor(actual.current);
      if (progreso < 1) cuadro = requestAnimationFrame(paso);
    };
    cuadro = requestAnimationFrame(paso);
    const terminar = () => {
      cancelAnimationFrame(cuadro);
      fijar();
    };
    const seguro = window.setTimeout(terminar, duracion + 300);
    const alCambiarVisibilidad = () => document.hidden && terminar();
    document.addEventListener("visibilitychange", alCambiarVisibilidad);
    return () => {
      cancelAnimationFrame(cuadro);
      window.clearTimeout(seguro);
      document.removeEventListener("visibilitychange", alCambiarVisibilidad);
    };
  }, [objetivo, duracion, reducido]);

  return valor;
}
