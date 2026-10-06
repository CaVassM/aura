import { TimeSlot } from "@/lib/types";

export default function TimeSlotPicker({
  slots,
  onSelect,
}: {
  slots: TimeSlot[];
  onSelect: (s: TimeSlot) => void;
}) {
  return (
    <div className="ml-11 grid max-w-md grid-cols-2 gap-2">
      {slots.map((slot) => {
        const d = new Date(slot.fechaISO);
        return (
          <button
            key={slot.id}
            disabled={!slot.disponible}
            onClick={() => onSelect(slot)}
            className="rounded-lg border border-aura-border bg-white px-3 py-2 text-xs font-medium text-aura-navy shadow-card transition hover:border-aura-teal hover:bg-aura-teal-pale disabled:opacity-40"
          >
            {d.toLocaleDateString("es-PE", {
              weekday: "short",
              day: "numeric",
              month: "short",
            })}
            <br />
            {d.toLocaleTimeString("es-PE", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </button>
        );
      })}
    </div>
  );
}
