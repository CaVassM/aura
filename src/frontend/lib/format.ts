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

export function num(valor: number, decimales = 1): string {
  return valor.toLocaleString("es-ES", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimales,
  });
}

/** Número con exactamente `decimales` decimales: 0,60 · 1,00. */
export function numFijo(valor: number, decimales: number): string {
  return valor.toLocaleString("es-ES", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
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
