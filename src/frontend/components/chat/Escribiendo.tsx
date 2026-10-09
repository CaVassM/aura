import { AvatarAura } from "./ChatBubble";

export default function Escribiendo() {
  return (
    <div className="flex items-center gap-3 animate-fade-only" role="status" aria-label="AURA está escribiendo">
      <AvatarAura pequeno />
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-md border border-co-line bg-white px-4 py-3.5 shadow-card">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 animate-dot rounded-full bg-co-teal"
            style={{ animationDelay: `${i * 160}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
