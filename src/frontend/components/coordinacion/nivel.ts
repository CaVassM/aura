// Niveles de ocupación. El backend decide el nivel (`nivel`); aquí solo se traduce a color y texto.
import { Nivel } from "@/lib/types-coordinacion";

export const NIVEL_LABEL: Record<Nivel, string> = {
  baja: "Baja",
  media: "Media",
  alta: "Alta",
};

/** Clases de fondo (barras, puntos de la leyenda). */
export const NIVEL_BG: Record<Nivel, string> = {
  baja: "bg-aura-chart-green",
  media: "bg-aura-chart-yellow",
  alta: "bg-aura-chart-red",
};

/** Clases de relleno para marcadores SVG. */
export const NIVEL_FILL: Record<Nivel, string> = {
  baja: "fill-aura-chart-green",
  media: "fill-aura-chart-yellow",
  alta: "fill-aura-chart-red",
};

export const NIVEL_TAG: Record<Nivel, "green" | "yellow" | "red"> = {
  baja: "green",
  media: "yellow",
  alta: "red",
};

export const NIVELES: Nivel[] = ["baja", "media", "alta"];
