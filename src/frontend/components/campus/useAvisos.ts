"use client";

import { useEffect, useRef } from "react";
import { getAvisos, urlAvisosStream } from "@/lib/api";
import { AvisoEstudiante } from "@/lib/types";

/**
 * Escucha los avisos en vivo de una persona (p. ej. «tu lote se resolvió»). Empieza desde lo último que ya
 * existe: lo anterior ya está en su conversación o en "Mis citas". `EventSource` reconecta solo.
 */
export function useAvisos(estudianteId: string, alRecibir: (aviso: AvisoEstudiante) => void) {
  const manejador = useRef(alRecibir);
  manejador.current = alRecibir;

  useEffect(() => {
    let cerrado = false;
    let fuente: EventSource | null = null;
    let ultimo = 0;

    const conectar = () => {
      if (cerrado) return;
      fuente = new EventSource(urlAvisosStream(estudianteId, ultimo));
      fuente.addEventListener("inicio", (e) => {
        if (JSON.parse((e as MessageEvent).data).reinicio) ultimo = 0;
      });
      fuente.addEventListener("reinicio", () => {
        ultimo = 0;
      });
      fuente.addEventListener("aviso", (e) => {
        const aviso: AvisoEstudiante = JSON.parse((e as MessageEvent).data);
        if (aviso.id <= ultimo) return;
        ultimo = aviso.id;
        manejador.current(aviso);
      });
    };

    getAvisos(estudianteId, 0)
      .then((r) => {
        ultimo = r.ultimo_id;
      })
      .catch(() => undefined)
      .finally(conectar);

    return () => {
      cerrado = true;
      fuente?.close();
    };
  }, [estudianteId]);
}
