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

/**
 * Número que sube (o baja) suavemente hasta `objetivo`: al cargar y cada vez que cambia.
 * Con movimiento reducido salta directo al valor final.
 */
export function useCountUp(objetivo: number, duracion = 900): number {
  const reducido = useReducedMotion();
  const [valor, setValor] = useState(0);
  const actual = useRef(0);

  useEffect(() => {
    if (reducido) {
      actual.current = objetivo;
      setValor(objetivo);
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
    return () => cancelAnimationFrame(cuadro);
  }, [objetivo, duracion, reducido]);

  return valor;
}
