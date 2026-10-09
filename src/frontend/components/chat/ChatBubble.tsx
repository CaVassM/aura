import { LifeBuoy, Sparkles, TriangleAlert } from "lucide-react";
import { ChatMessage } from "@/lib/types";
import Texto, { sinLista } from "./Texto";

export function AvatarAura({ pequeno = false }: { pequeno?: boolean }) {
  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-co-teal to-co-teal-deep text-white shadow-card ${
        pequeno ? "h-8 w-8" : "h-10 w-10"
      }`}
    >
      <Sparkles size={pequeno ? 15 : 18} aria-hidden="true" />
    </div>
  );
}

export default function ChatBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-rise">
        <div className="max-w-[78%] rounded-2xl rounded-br-md bg-gradient-to-br from-co-teal to-co-teal-dark px-4 py-3 text-sm leading-relaxed text-white shadow-card">
          {message.text}
        </div>
      </div>
    );
  }

  const texto = message.opciones?.length ? sinLista(message.text) || "Encontré estas opciones para ti:" : message.text;

  const variante = message.crisis
    ? "border-co-amber bg-co-amber-tint text-co-navy"
    : message.error
      ? "border-co-coral/40 bg-co-coral-tint text-co-coral-ink"
      : "border-co-line bg-white text-co-navy";

  return (
    <div className="flex items-start gap-3 animate-rise">
      <AvatarAura pequeno />
      <div className={`max-w-[82%] rounded-2xl rounded-tl-md border px-4 py-3 text-sm leading-relaxed shadow-card ${variante}`}>
        {message.crisis && (
          <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-[0.14em] text-co-amber-ink">
            <LifeBuoy size={14} aria-hidden="true" />
            Ayuda inmediata
          </p>
        )}
        {message.error && (
          <p className="mb-1.5 flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-[0.14em]">
            <TriangleAlert size={14} aria-hidden="true" />
            Algo no salió bien
          </p>
        )}
        <Texto texto={texto} />
      </div>
    </div>
  );
}
