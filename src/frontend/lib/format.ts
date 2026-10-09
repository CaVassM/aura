// Formato de fechas y números para el panel (es-PE). Las fechas llegan como YYYY-MM-DD.

const MESES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

function partes(iso: string) {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return { anio, mes, dia };
}

/** "16 de noviembre" */
export function fechaLarga(iso: string): string {
  const { mes, dia } = partes(iso);
  return `${dia} de ${MESES[mes - 1]}`;
}

/** "16 nov" */
export function fechaCorta(iso: string): string {
  const { mes, dia } = partes(iso);
  return `${dia} ${MESES[mes - 1].slice(0, 3)}`;
}

/** "del 16 al 29 de noviembre de 2026" (o con los dos meses si cambian). */
export function rangoFechas(desde: string, hasta: string): string {
  const a = partes(desde);
  const b = partes(hasta);
  const inicio = a.mes === b.mes ? `${a.dia}` : fechaLarga(desde);
  return `del ${inicio} al ${fechaLarga(hasta)} de ${b.anio}`;
}

/** "16–29 nov" (o "28 nov–3 dic" si cruza de mes). */
export function rangoCorto(desde: string, hasta: string): string {
  const a = partes(desde);
  const b = partes(hasta);
  return a.mes === b.mes
    ? `${a.dia}–${b.dia} ${MESES[b.mes - 1].slice(0, 3)}`
    : `${fechaCorta(desde)}–${fechaCorta(hasta)}`;
}

/** "del 9 al 15 nov" (o "del 28 oct al 3 nov" si cruza de mes). */
export function rangoDel(desde: string, hasta: string): string {
  const a = partes(desde);
  const b = partes(hasta);
  return a.mes === b.mes
    ? `del ${a.dia} al ${b.dia} ${MESES[b.mes - 1].slice(0, 3)}`
    : `del ${fechaCorta(desde)} al ${fechaCorta(hasta)}`;
}

/** "del 9 al 15 de noviembre" (sin año). */
export function rangoSinAnio(desde: string, hasta: string): string {
  const a = partes(desde);
  const b = partes(hasta);
  const inicio = a.mes === b.mes ? `${a.dia}` : fechaLarga(desde);
  return `del ${inicio} al ${fechaLarga(hasta)}`;
}

export function num(valor: number, decimales = 1): string {
  return valor.toLocaleString("es-ES", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimales,
    useGrouping: "always" as never, // 1.036 (es-ES no agrupa los números de 4 cifras)
  });
}

/** Número con exactamente `decimales` decimales: 0,60 · 1,00. */
export function numFijo(valor: number, decimales: number): string {
  return valor.toLocaleString("es-ES", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
    useGrouping: "always" as never,
  });
}

export function pct(valor: number): string {
  return `${num(valor)}%`;
}

/** "DIST_GAIA" → "Gaia" (el id viene de D6; solo se le da formato de lectura). */
export function distritoLabel(id: string): string {
  const base = id.replace(/^DIST_/, "").toLowerCase();
  return base.charAt(0).toUpperCase() + base.slice(1);
}

const DIAS_LARGO = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];

/** Día de la semana de una fecha AAAA-MM-DD ("miércoles"), sin depender de la zona horaria. */
export function diaSemana(iso: string): string {
  const { anio, mes, dia } = partes(iso);
  return DIAS_LARGO[new Date(Date.UTC(anio, mes - 1, dia)).getUTCDay()];
}

/** "miércoles 25 de noviembre" */
export function fechaConDia(iso: string): string {
  return `${diaSemana(iso)} ${fechaLarga(iso)}`;
}

/** Piezas para un bloque de calendario: { dia: "mié", numero: 25, mes: "nov" } */
export function bloqueFecha(iso: string): { dia: string; numero: number; mes: string } {
  const { mes, dia } = partes(iso);
  return { dia: diaSemana(iso).slice(0, 3), numero: dia, mes: MESES[mes - 1].slice(0, 3) };
}

/** "10:00 – 11:00" */
export function rangoHoras(desde: string, hasta: string): string {
  return `${desde} – ${hasta}`;
}

/** "miércoles 25 de noviembre" → "Miércoles 25 de noviembre" (solo la primera letra). */
export function primeraMayuscula(texto: string): string {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}
