"use client";

import { useEffect, useRef } from "react";
import { getAvisos, urlAvisosStream } from "@/lib/api";
import { AvisoEstudiante } from "@/lib/types";

const SONDEO_MS = 3000;
const ESPERA_FLUJO_MS = 4000;

/**
 * Escucha los avisos en vivo de una persona (p. ej. «tu lote se resolvió»). Empieza desde lo último que ya
 * existe: lo anterior ya está en su conversación o en "Mis citas". `EventSource` reconecta solo; si el flujo no
 * llega (un túnel o proxy que lo corta), el aviso igual llega consultando cada pocos segundos.
 */
export function useAvisos(estudianteId: string, alRecibir: (aviso: AvisoEstudiante) => void) {
  const manejador = useRef(alRecibir);
  manejador.current = alRecibir;

  useEffect(() => {
    let cerrado = false;
    let fuente: EventSource | null = null;
    let ultimo = 0;
    let epoca: string | null = null;
    let sondeo: ReturnType<typeof setInterval> | null = null;
    let espera: ReturnType<typeof setTimeout> | null = null;

    const recibir = (aviso: AvisoEstudiante) => {
      if (aviso.id <= ultimo) return; // el id evita repetirlo si llega por el flujo y por el sondeo
      ultimo = aviso.id;
      manejador.current(aviso);
    };

    const consultar = () =>
      getAvisos(estudianteId, ultimo)
        .then((r) => {
          if (cerrado) return;
          if (epoca !== null && r.epoca !== epoca) ultimo = 0; // la demo se reinició
          epoca = r.epoca;
          r.avisos.forEach(recibir);
        })
        .catch(() => undefined);

    const detenerSondeo = () => {
      if (sondeo) clearInterval(sondeo);
      sondeo = null;
    };
    const iniciarSondeo = () => {
      if (cerrado || sondeo) return;
      consultar();
      sondeo = setInterval(consultar, SONDEO_MS);
    };
    const flujoActivo = () => {
      if (espera) clearTimeout(espera);
      espera = null;
      detenerSondeo();
    };

    const conectar = () => {
      if (cerrado) return;
      fuente = new EventSource(urlAvisosStream(estudianteId, ultimo));
      espera = setTimeout(iniciarSondeo, ESPERA_FLUJO_MS);
      fuente.addEventListener("inicio", (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        epoca = d.epoca ?? epoca;
        if (d.reinicio) ultimo = 0;
        flujoActivo();
      });
      fuente.addEventListener("reinicio", () => {
        ultimo = 0;
      });
      fuente.addEventListener("aviso", (e) => {
        flujoActivo();
        recibir(JSON.parse((e as MessageEvent).data));
      });
      fuente.onerror = () => iniciarSondeo();
    };

    getAvisos(estudianteId, 0)
      .then((r) => {
        ultimo = r.ultimo_id;
        epoca = r.epoca;
      })
      .catch(() => undefined)
      .finally(conectar);

    return () => {
      cerrado = true;
      fuente?.close();
      detenerSondeo();
      if (espera) clearTimeout(espera);
    };
  }, [estudianteId]);
}
