// Niveles de ocupación. El backend decide el nivel (`nivel`); aquí solo se traduce a color y texto.
// coral = alta demanda, ámbar = media, salvia = baja. Los textos usan las variantes *-ink (AA).
import { Nivel } from "@/lib/types-coordinacion";

export const NIVELES: Nivel[] = ["baja", "media", "alta"];

export const NIVEL_LABEL: Record<Nivel, string> = {
  baja: "Baja",
  media: "Media",
  alta: "Alta",
};

/** Relleno de barras y puntos. */
export const NIVEL_BG: Record<Nivel, string> = {
  baja: "bg-co-sage",
  media: "bg-co-amber",
  alta: "bg-co-coral",
};

/** Relleno de marcadores SVG. */
export const NIVEL_FILL: Record<Nivel, string> = {
  baja: "fill-co-sage",
  media: "fill-co-amber",
  alta: "fill-co-coral",
};

/** Texto del nivel (contraste AA sobre crema). */
export const NIVEL_INK: Record<Nivel, string> = {
  baja: "text-co-sage-ink",
  media: "text-co-amber-ink",
  alta: "text-co-coral-ink",
};

export const NIVEL_TINT: Record<Nivel, string> = {
  baja: "bg-co-sage-tint",
  media: "bg-co-amber-tint",
  alta: "bg-co-coral-tint",
};
