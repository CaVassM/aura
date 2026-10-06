const VARIANTS = {
  green: "bg-aura-tag-green-bg text-aura-tag-green-text",
  purple: "bg-aura-tag-purple-bg text-aura-tag-purple-text",
  yellow: "bg-aura-tag-yellow-bg text-aura-tag-yellow-text",
  red: "bg-aura-tag-red-bg text-aura-tag-red-text",
} as const;

export default function Tag({
  children,
  variant,
}: {
  children: React.ReactNode;
  variant: keyof typeof VARIANTS;
}) {
  return (
    <span
      className={`inline-block rounded-md px-2 py-1 text-xs font-medium ${VARIANTS[variant]}`}
    >
      {children}
    </span>
  );
}
