/** Barra horizontal que crece desde 0 (con retraso opcional para escalonar) y se ajusta al cambiar el valor. */
export default function Barra({
  pct,
  color = "bg-co-teal",
  retraso = 0,
  alto = "h-2",
  pista = "bg-co-line/70",
  etiqueta,
}: {
  pct: number;
  color?: string;
  retraso?: number;
  alto?: string;
  pista?: string;
  etiqueta?: string;
}) {
  return (
    <div
      className={`${alto} w-full overflow-hidden rounded-full ${pista}`}
      role={etiqueta ? "img" : undefined}
      aria-label={etiqueta}
    >
      <div
        className={`h-full origin-left rounded-full animate-grow-x transition-[width] duration-500 ease-out ${color}`}
        style={{
          width: `${Math.min(100, Math.max(0, pct))}%`,
          animationDelay: `${retraso}ms`,
        }}
      />
    </div>
  );
}
