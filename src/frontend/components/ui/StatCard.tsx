import Tag from "./Tag";

export default function StatCard({
  label,
  value,
  tagText,
  tagVariant,
}: {
  label: string;
  value: string;
  tagText: string;
  tagVariant: "green" | "purple" | "yellow" | "red";
}) {
  return (
    <div className="rounded-2xl border border-aura-border bg-white p-5 shadow-card">
      <p className="text-sm text-aura-gray-light">{label}</p>
      <p className="mt-2 text-3xl font-bold text-aura-navy">{value}</p>
      <div className="mt-3">
        <Tag variant={tagVariant}>{tagText}</Tag>
      </div>
    </div>
  );
}
