"use client";

import { ReactNode } from "react";
import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import { API_BASE_URL, ApiError } from "@/lib/api";

/** Cargando datos del backend. */
export function EstadoCarga({ texto = "Cargando datos…" }: { texto?: string }) {
  return (
    <div
      role="status"
      className="flex items-center justify-center gap-3 px-8 py-16 text-sm text-aura-gray"
    >
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      {texto}
    </div>
  );
}

/** El backend no respondió o devolvió un error: mensaje claro y reintento. */
export function EstadoError({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const sinConexion = error instanceof ApiError && error.sinConexion;
  const mensaje =
    error instanceof Error ? error.message : "Ocurrió un error inesperado.";
  return (
    <div
      role="alert"
      className="mx-auto my-10 flex max-w-xl flex-col items-center gap-3 rounded-2xl border border-aura-tag-red-bg bg-white px-8 py-10 text-center shadow-card"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-aura-tag-red-bg text-aura-tag-red-text">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
      </div>
      <p className="text-base font-semibold text-aura-navy">
        {sinConexion
          ? "No se pudo conectar con el backend"
          : "No se pudieron cargar los datos"}
      </p>
      <p className="text-sm text-aura-gray">{mensaje}</p>
      {sinConexion && (
        <p className="text-xs leading-relaxed text-aura-gray">
          Revisa que el backend esté corriendo (
          <code className="rounded bg-aura-bg px-1">
            uvicorn app.main:app --port 8080
          </code>
          ) y que <code className="rounded bg-aura-bg px-1">NEXT_PUBLIC_API_URL</code>{" "}
          apunte a {API_BASE_URL}.
        </p>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 rounded-xl bg-aura-teal px-4 py-2 text-sm font-semibold text-white hover:bg-aura-teal-dark"
        >
          Reintentar
        </button>
      )}
    </div>
  );
}

/** Sin resultados para el filtro actual (no una tabla en blanco). */
export function EstadoVacio({
  titulo,
  descripcion,
  accion,
}: {
  titulo: string;
  descripcion: string;
  accion?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-8 py-14 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-aura-purple-nav text-aura-purple">
        <Inbox className="h-5 w-5" aria-hidden="true" />
      </div>
      <p className="text-base font-semibold text-aura-navy">{titulo}</p>
      <p className="max-w-md text-sm text-aura-gray">{descripcion}</p>
      {accion && <div className="mt-2">{accion}</div>}
    </div>
  );
}
