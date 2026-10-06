"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ChevronLeft, PanelRightOpen, Send, Sparkles, X } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav, campusUser } from "@/components/campus/nav";
import ChatBubble from "@/components/chat/ChatBubble";
import ServiceCard from "@/components/chat/ServiceCard";
import TimeSlotPicker from "@/components/chat/TimeSlotPicker";
import { bookAppointment, getAvailableSlots, sendMessage } from "@/lib/api";
import { ChatMessage, ServiceOption, TimeSlot } from "@/lib/types";

const uid = () => Math.random().toString(36).slice(2);

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: uid(),
      role: "agent",
      text: "Hola, Lucía. Soy AURA. Te ayudo a encontrar y agendar una cita con bienestar. No atiendo ni diagnostico: te conecto con un servicio disponible. ¿Qué te gustaría conversar?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [services, setServices] = useState<ServiceOption[] | null>(null);
  const [selectedService, setSelectedService] = useState<ServiceOption | null>(
    null
  );
  const [slots, setSlots] = useState<TimeSlot[] | null>(null);
  const [showInfo, setShowInfo] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, services, slots]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { id: uid(), role: "user", text }]);
    setInput("");
    setLoading(true);
    setServices(null);

    const res = await sendMessage(text);
    setMessages((m) => [...m, { id: uid(), role: "agent", text: res.reply }]);
    if (res.services) setServices(res.services);
    setLoading(false);
  }

  async function handleSelectService(service: ServiceOption) {
    setSelectedService(service);
    setServices(null);
    setLoading(true);
    const availableSlots = await getAvailableSlots(service.id);
    setSlots(availableSlots);
    setLoading(false);
  }

  async function handleSelectSlot(slot: TimeSlot) {
    if (!selectedService) return;
    setSlots(null);
    setLoading(true);
    await bookAppointment(selectedService, slot);

    const fecha = new Date(slot.fechaISO).toLocaleDateString("es-PE", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
    const hora = new Date(slot.fechaISO).toLocaleTimeString("es-PE", {
      hour: "2-digit",
      minute: "2-digit",
    });

    setMessages((m) => [
      ...m,
      {
        id: uid(),
        role: "agent",
        text: `Listo — tu cita de ${selectedService.nombre} quedó confirmada para el ${fecha} a las ${hora}. Te llegará un recordatorio antes. Puedes verla en "Mis citas".`,
      },
    ]);
    setSelectedService(null);
    setLoading(false);
  }

  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus/chat"
      user={campusUser}
      exitHref="/"
      exitLabel="Salir del campus"
      title="Conversar con AURA"
      subtitle="Encuentra una cita según tus preferencias"
      topbarRight={
        <>
          <button
            onClick={() => setShowInfo(true)}
            className="flex items-center gap-1.5 rounded-lg border border-aura-border bg-white px-3 py-1.5 text-sm font-medium text-aura-navy hover:bg-aura-bg"
          >
            <PanelRightOpen size={15} />
            ¿Cómo decide AURA?
          </button>
          <TopbarControls />
        </>
      }
    >
      <div className="mx-auto flex h-[calc(100vh-89px)] max-w-3xl flex-col px-8 py-6">
        <div className="flex min-h-0 flex-1 flex-col rounded-xl2 border border-aura-border bg-white shadow-card">
          {/* Header interno del chat */}
          <div className="flex items-center gap-3 border-b border-aura-border px-6 py-4">
            <Link
              href="/campus"
              className="rounded-lg p-1.5 text-aura-gray hover:bg-aura-bg"
            >
              <ChevronLeft size={18} />
            </Link>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-aura-teal text-white">
              <Sparkles size={16} />
            </div>
            <div>
              <p className="text-sm font-bold text-aura-navy">AURA</p>
              <p className="flex items-center gap-1.5 text-xs text-aura-gray">
                <span className="h-1.5 w-1.5 rounded-full bg-aura-teal" />
                Asistente de agenda
              </p>
            </div>
          </div>

          {/* Mensajes */}
          <div
            ref={scrollRef}
            className="flex-1 space-y-3 overflow-y-auto px-6 py-6"
          >
            {messages.map((m) => (
              <ChatBubble key={m.id} message={m} />
            ))}

            {services && (
              <div className="space-y-2 pt-1">
                {services.map((s) => (
                  <ServiceCard
                    key={s.id}
                    service={s}
                    onSelect={handleSelectService}
                  />
                ))}
              </div>
            )}

            {slots && (
              <div className="space-y-2 pt-1">
                <p className="ml-11 text-xs font-medium text-aura-gray">
                  Elige un horario para {selectedService?.nombre}:
                </p>
                <TimeSlotPicker slots={slots} onSelect={handleSelectSlot} />
              </div>
            )}

            {loading && (
              <div className="ml-11 text-xs text-aura-gray">
                AURA está escribiendo…
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-aura-border px-6 py-4">
            <div className="flex items-center gap-2 rounded-full border border-aura-border bg-aura-bg px-4 py-1">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Escribe cómo te sientes…"
                className="flex-1 bg-transparent py-2.5 text-sm text-aura-navy outline-none placeholder:text-aura-gray"
              />
              <button
                onClick={handleSend}
                disabled={loading}
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-aura-teal text-white transition hover:bg-aura-teal-dark disabled:opacity-50"
              >
                <Send size={15} />
              </button>
            </div>
            <p className="mt-3 text-center text-xs text-aura-gray">
              AURA te ayuda a agendar; no diagnostica ni reemplaza atención
              profesional.
            </p>
          </div>
        </div>
      </div>

      {/* Modal "¿Cómo decide AURA?" */}
      {showInfo && (
        <div
          className="fixed inset-0 z-10 flex items-center justify-center bg-aura-navy/30 px-6"
          onClick={() => setShowInfo(false)}
        >
          <div
            className="w-full max-w-sm rounded-xl2 bg-white p-6 shadow-card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <p className="text-base font-bold text-aura-navy">
                ¿Cómo decide AURA?
              </p>
              <button
                onClick={() => setShowInfo(false)}
                className="text-aura-gray hover:text-aura-navy"
              >
                <X size={18} />
              </button>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-aura-gray">
              AURA lee lo que escribes para identificar qué tipo de apoyo
              buscas, consulta la disponibilidad real de la red de bienestar y
              ordena las opciones priorizando menor espera y compatibilidad de
              horario. No analiza tu historial académico ni diagnostica: solo
              coordina el acceso a un servicio humano.
            </p>
          </div>
        </div>
      )}
    </PortalShell>
  );
}
