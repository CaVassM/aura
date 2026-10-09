"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ChevronLeft, MapPin, PanelRightOpen, RotateCcw, Send, X } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { usePerfil } from "@/components/campus/PerfilProvider";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav } from "@/components/campus/nav";
import ChatBubble, { AvatarAura } from "@/components/chat/ChatBubble";
import { CitaCancelada, CitaConfirmada } from "@/components/chat/CitaConfirmada";
import Escribiendo from "@/components/chat/Escribiendo";
import OpcionCard from "@/components/chat/OpcionCard";
import { ApiError, chatEnviar, chatHistorial, chatReiniciar } from "@/lib/api";
import { fechaConDia } from "@/lib/format";
import { nombreDistrito, PerfilEstudiante } from "@/lib/perfiles";
import { ChatMessage, Opcion } from "@/lib/types";

const uid = () => Math.random().toString(36).slice(2);
const claveSesion = (estudianteId: string) => `aura:chat:${estudianteId}`;

const SUGERENCIAS = [
  "Me está pesando mucho la universidad",
  "¿Qué servicios existen?",
  "Quiero una cita el miércoles por videollamada",
  "¿Qué citas tengo?",
];

function saludo(perfil: PerfilEstudiante): ChatMessage {
  return {
    id: "saludo",
    role: "agent",
    text:
      `Hola, ${perfil.corto}. Soy AURA y te ayudo a encontrar y agendar una cita con bienestar. ` +
      `No atiendo ni diagnostico: te conecto con un servicio disponible.\n\n` +
      `Para las citas presenciales usaré tu distrito, ${nombreDistrito(perfil.distrito)}. ` +
      `Si hoy o esta semana estarás en otro lugar, solo dímelo.\n\n` +
      `¿Qué te gustaría conversar?`,
  };
}

function errorAmable(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.sinConexion) return "No pude conectarme con el servidor de AURA. Revisa que el backend esté encendido e inténtalo de nuevo.";
    if (error.status === 503) return error.detalle || "El asistente no está disponible en este momento. Inténtalo de nuevo en unos minutos.";
    if (error.status === 422) return "No pude entender ese mensaje. ¿Puedes escribirlo de otra forma?";
  }
  return "Tuve un problema para responderte. Inténtalo de nuevo.";
}

export default function ChatPage() {
  const { perfil } = usePerfil();
  const [mensajes, setMensajes] = useState<ChatMessage[]>([saludo(perfil)]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [entrada, setEntrada] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [recuperando, setRecuperando] = useState(true);
  const [verInfo, setVerInfo] = useState(false);
  const fin = useRef<HTMLDivElement>(null);
  const campo = useRef<HTMLInputElement>(null);

  // Cada estudiante tiene su propia conversación: al cambiar de perfil se recupera la suya.
  useEffect(() => {
    let vigente = true;
    setMensajes([saludo(perfil)]);
    setSessionId(null);
    setEnviando(false);
    setRecuperando(true);

    let guardada: string | null = null;
    try {
      guardada = window.sessionStorage.getItem(claveSesion(perfil.id));
    } catch {
      /* sin almacenamiento */
    }
    if (!guardada) {
      setRecuperando(false);
      return;
    }
    chatHistorial(guardada, perfil.id)
      .then((h) => {
        if (!vigente) return;
        setSessionId(guardada);
        setMensajes([
          saludo(perfil),
          ...h.mensajes.map<ChatMessage>((m) => ({ id: uid(), role: m.rol, text: m.texto })),
        ]);
      })
      .catch(() => {
        // La sesión ya no existe (p. ej. se reinició el backend, que guarda todo en RAM): se empieza de cero.
        try {
          window.sessionStorage.removeItem(claveSesion(perfil.id));
        } catch {
          /* ignorar */
        }
      })
      .finally(() => vigente && setRecuperando(false));
    return () => {
      vigente = false;
    };
  }, [perfil]);

  useEffect(() => {
    fin.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes, enviando]);

  const guardarSesion = useCallback(
    (id: string | null) => {
      setSessionId(id);
      try {
        if (id) window.sessionStorage.setItem(claveSesion(perfil.id), id);
        else window.sessionStorage.removeItem(claveSesion(perfil.id));
      } catch {
        /* ignorar */
      }
    },
    [perfil.id],
  );

  const enviar = useCallback(
    async (texto: string, opcionElegida?: string) => {
      const limpio = texto.trim();
      if (!limpio || enviando) return;
      setMensajes((m) => [
        ...m.map((x) => (opcionElegida && x.opciones ? { ...x, elegida: opcionElegida } : x)),
        { id: uid(), role: "user", text: limpio },
      ]);
      setEntrada("");
      setEnviando(true);

      const intentar = (sesion: string | null) =>
        chatEnviar({ mensaje: limpio, estudiante_id: perfil.id, session_id: sesion, distrito: perfil.distrito });

      try {
        let res;
        try {
          res = await intentar(sessionId);
        } catch (error) {
          // La conversación guardada ya no existe en el servidor: se reintenta como conversación nueva.
          if (sessionId && error instanceof ApiError && error.status === 404) res = await intentar(null);
          else throw error;
        }
        guardarSesion(res.session_id);
        setMensajes((m) => [
          ...m,
          {
            id: uid(),
            role: "agent",
            text: res.respuesta,
            opciones: res.opciones.length ? res.opciones : undefined,
            cita: res.cita ?? undefined,
            citaCancelada: res.cita_cancelada ?? undefined,
            desencuentro: res.desencuentro_registrado || undefined,
            crisis: res.alerta_crisis || undefined,
          },
        ]);
      } catch (error) {
        setMensajes((m) => [...m, { id: uid(), role: "agent", text: errorAmable(error), error: true }]);
      } finally {
        setEnviando(false);
        campo.current?.focus();
      }
    },
    [enviando, perfil, sessionId, guardarSesion],
  );

  const elegir = (o: Opcion, numero: number) =>
    enviar(
      `Quiero la opción ${numero}: ${o.servicio_nombre}, ${fechaConDia(o.fecha)}, ${o.hora_inicio}`,
      o.opcion_id,
    );

  const nuevaConversacion = async () => {
    if (sessionId) chatReiniciar(sessionId, perfil.id).catch(() => undefined);
    guardarSesion(null);
    setMensajes([saludo(perfil)]);
    campo.current?.focus();
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    enviar(entrada);
  };

  // Solo la lista de opciones más reciente se puede elegir, y únicamente si no se reservó después.
  const ultimaConOpciones = [...mensajes].reverse().find((m) => m.opciones)?.id;
  const indiceUltima = mensajes.findIndex((m) => m.id === ultimaConOpciones);
  const reservadaDespues = mensajes.slice(indiceUltima + 1).some((m) => m.cita);
  const soloSaludo = mensajes.length === 1;

  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus/chat"
      exitHref="/"
      exitLabel="Salir del campus"
      title="Conversar con AURA"
      subtitle="Encuentra una cita según tus preferencias"
      topbarRight={
        <>
          <button
            onClick={() => setVerInfo(true)}
            className="co-foco hidden items-center gap-1.5 rounded-full border border-co-line bg-white px-3.5 py-1.5 text-sm font-semibold text-co-navy transition hover:border-co-teal sm:flex"
          >
            <PanelRightOpen size={15} aria-hidden="true" />
            ¿Cómo decide AURA?
          </button>
          <TopbarControls />
        </>
      }
    >
      <div className="chat-lienzo h-full px-4 py-5 lg:px-8">
        <div className="mx-auto flex h-full max-w-3xl flex-col overflow-hidden rounded-3xl border border-co-line bg-co-paper/80 shadow-pop backdrop-blur">
          {/* Cabecera del chat */}
          <div className="flex items-center gap-3 border-b border-co-line px-5 py-3.5">
            <Link
              href="/campus"
              aria-label="Volver al inicio"
              className="co-foco rounded-lg p-1.5 text-co-ink transition hover:bg-co-bg"
            >
              <ChevronLeft size={18} aria-hidden="true" />
            </Link>
            <div className="animate-breathe">
              <AvatarAura />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-extrabold text-co-navy">AURA</p>
              <p className="flex items-center gap-1.5 text-xs font-semibold text-co-ink">
                <span className="h-1.5 w-1.5 rounded-full bg-co-sage" aria-hidden="true" />
                Asistente de agenda
              </p>
            </div>
            <span
              className="hidden items-center gap-1 rounded-full bg-co-teal-tint px-3 py-1 text-xs font-bold text-co-teal-dark sm:inline-flex"
              title="AURA usa el distrito de tu perfil para las citas presenciales. Puedes cambiarlo conversando."
            >
              <MapPin size={12} aria-hidden="true" />
              {nombreDistrito(perfil.distrito)}
            </span>
            <button
              onClick={nuevaConversacion}
              disabled={enviando || soloSaludo}
              className="co-foco flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold text-co-ink transition hover:bg-co-bg disabled:opacity-40"
            >
              <RotateCcw size={13} aria-hidden="true" />
              <span className="hidden sm:inline">Nueva conversación</span>
            </button>
          </div>

          {/* Mensajes */}
          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-6" aria-live="polite">
            {recuperando ? (
              <div className="flex justify-center py-10 text-sm font-semibold text-co-ink">Recuperando tu conversación…</div>
            ) : (
              mensajes.map((m) => {
                const activas = m.id === ultimaConOpciones && !reservadaDespues;
                return (
                  <div key={m.id} className="space-y-3">
                    <ChatBubble message={m} />

                    {m.opciones && (
                      <div className="ml-0 max-w-xl space-y-2.5 sm:ml-11">
                        {m.opciones.map((o, i) => (
                          <OpcionCard
                            key={o.opcion_id}
                            opcion={o}
                            numero={i + 1}
                            indice={i}
                            activa={activas && !enviando}
                            elegida={m.elegida === o.opcion_id}
                            onElegir={elegir}
                          />
                        ))}
                        {activas && (
                          <p className="text-xs font-semibold text-co-ink">
                            Toca la que prefieras o escríbeme cuál. Todavía no se reserva nada.
                          </p>
                        )}
                      </div>
                    )}

                    {m.cita && (
                      <div className="ml-0 max-w-xl sm:ml-11">
                        <CitaConfirmada cita={m.cita} />
                      </div>
                    )}
                    {m.citaCancelada && (
                      <div className="ml-0 max-w-xl sm:ml-11">
                        <CitaCancelada cita={m.citaCancelada} />
                      </div>
                    )}
                    {m.desencuentro && (
                      <p className="inline-block rounded-md bg-co-amber-tint sm:ml-11 px-3 py-1.5 text-xs font-bold text-co-amber-ink animate-rise">
                        Avisé al equipo de coordinación que faltan horarios como el que buscas.
                      </p>
                    )}
                  </div>
                );
              })
            )}

            {soloSaludo && !recuperando && !enviando && (
              <div className="ml-0 flex max-w-xl flex-wrap gap-2 animate-fade-in sm:ml-11">
                {SUGERENCIAS.map((s, i) => (
                  <button
                    key={s}
                    onClick={() => enviar(s)}
                    style={{ animationDelay: `${i * 70}ms` }}
                    className="co-foco animate-rise rounded-full border border-co-line bg-white px-3.5 py-2 text-xs font-bold text-co-teal-dark shadow-card transition hover:-translate-y-0.5 hover:border-co-teal hover:bg-co-teal-tint"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {enviando && <Escribiendo />}
            <div ref={fin} />
          </div>

          {/* Entrada */}
          <div className="border-t border-co-line bg-white/70 px-5 py-4">
            <form
              onSubmit={onSubmit}
              className="flex items-center gap-2 rounded-full border border-co-line bg-white py-1 pl-5 pr-1.5 shadow-card transition focus-within:border-co-teal focus-within:ring-2 focus-within:ring-co-teal/20"
            >
              <input
                ref={campo}
                value={entrada}
                onChange={(e) => setEntrada(e.target.value)}
                disabled={recuperando}
                maxLength={2000}
                placeholder="Cuéntame cómo te sientes o qué necesitas…"
                aria-label="Escribe tu mensaje"
                className="min-w-0 flex-1 bg-transparent py-2.5 text-sm text-co-navy outline-none placeholder:text-co-ink/70"
              />
              <button
                type="submit"
                disabled={enviando || recuperando || !entrada.trim()}
                aria-label="Enviar"
                className="co-foco flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-co-teal to-co-teal-deep text-white transition hover:scale-105 hover:shadow-lift disabled:scale-100 disabled:opacity-40 disabled:shadow-none"
              >
                <Send size={16} aria-hidden="true" />
              </button>
            </form>
            <p className="mt-2.5 text-center text-xs text-co-ink">
              AURA te ayuda a agendar; no diagnostica ni reemplaza atención profesional.
            </p>
          </div>
        </div>
      </div>

      {verInfo && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-co-teal-deep/50 px-6 backdrop-blur-sm animate-fade-only"
          onClick={() => setVerInfo(false)}
          role="dialog"
          aria-modal="true"
          aria-label="¿Cómo decide AURA?"
        >
          <div
            className="w-full max-w-md rounded-3xl bg-co-paper p-7 shadow-pop animate-rise"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <p className="text-lg font-extrabold text-co-navy">¿Cómo decide AURA?</p>
              <button
                onClick={() => setVerInfo(false)}
                aria-label="Cerrar"
                className="co-foco rounded-lg p-1 text-co-ink transition hover:bg-co-bg hover:text-co-navy"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-co-ink">
              AURA lee lo que escribes para entender qué apoyo buscas, consulta la disponibilidad real de la red de
              bienestar y te propone las mejores opciones según tus días, tu horario, el canal y la espera.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-co-ink">
              Para las citas presenciales usa el distrito de tu perfil, y puedes cambiarlo conversando. No analiza tu
              historial académico ni diagnostica: solo coordina el acceso a un servicio. Nunca reserva sin que tú elijas.
            </p>
          </div>
        </div>
      )}
    </PortalShell>
  );
}
