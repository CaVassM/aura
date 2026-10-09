/** Un color por curso (misma paleta `co.*`), para reconocerlo igual en tarjetas, horario y calendario. Clases completas para Tailwind. */
export interface ColorCurso {
  solido: string;
  tinte: string;
  tinta: string;
  borde: string;
}

export const COLORES_CURSO: ColorCurso[] = [
  { solido: "bg-co-teal", tinte: "bg-co-teal-tint", tinta: "text-co-teal-dark", borde: "border-co-teal" },
  { solido: "bg-co-coral", tinte: "bg-co-coral-tint", tinta: "text-co-coral-ink", borde: "border-co-coral" },
  { solido: "bg-co-amber", tinte: "bg-co-amber-tint", tinta: "text-co-amber-ink", borde: "border-co-amber" },
  { solido: "bg-co-sage", tinte: "bg-co-sage-tint", tinta: "text-co-sage-ink", borde: "border-co-sage" },
  { solido: "bg-co-navy", tinte: "bg-co-line/60", tinta: "text-co-navy", borde: "border-co-navy" },
];

export const colorDeCurso = (indice: number): ColorCurso => COLORES_CURSO[indice % COLORES_CURSO.length];
