// Glosario del panel de Coordinación: TODOS los textos de los ⓘ viven aquí.
// Los números (10 %, 50 %, 2 semanas, 42 días, umbrales de nivel, fechas) no se escriben a mano:
// se rellenan con lo que devuelve /api/demo/estado (ver `contextoGlosario`).

import { EstadoDemo } from "./types-coordinacion";
import { num, rangoSinAnio } from "./format";

export type Termino =
  | "citas_agendadas"
  | "espera_media"
  | "ocupacion"
  | "desencuentros"
  | "atendidos_alternativa"
  | "capacidad_semanal"
  | "capacidad_agenda"
  | "libres"
  | "liberados"
  | "reservados"
  | "nivel"
  | "servicio_ideal"
  | "grupo"
  | "franja"
  | "pedidos"
  | "en_su_tipo"
  | "regla_motivo"
  | "regla_afinidad"
  | "regla_aviso"
  | "regla_asistencia"
  | "regla_pesos";

/** Texto del globo ⓘ. Los {marcadores} se rellenan con el contexto. */
export const GLOSARIO: Record<Termino, string> = {
  citas_agendadas:
    "Citas que AURA reservó para los pedidos que llegaron {pedidos}.",
  espera_media:
    "Días entre el pedido y la cita. Se mide igual que en D2, donde la espera media era de {linea_base} días.",
  ocupacion:
    "Qué parte de los cupos que los servicios prestaron a AURA ya está reservada en las próximas {semanas} semanas.",
  desencuentros:
    "Pedidos sin ningún cupo compatible con el horario, canal o distrito del estudiante. Se registran como evidencia para decidir dónde abrir horarios.",
  atendidos_alternativa:
    "Estudiantes que recibieron un servicio relacionado porque el ideal no tenía cupo en su horario. Ej.: consejería → apoyo entre pares.",
  capacidad_semanal: "Cupos que el servicio atiende en una semana, según D6.",
  capacidad_agenda:
    "La capacidad del servicio en las {semanas} semanas de agenda abierta.",
  libres:
    "Lo que queda después de las citas que el servicio ya tenía ({ocupacion_inicial} %).",
  liberados:
    "La parte de los cupos libres que el servicio presta a AURA para autoagendamiento ({fraccion_liberada} %).",
  reservados: "Cupos liberados que AURA ya asignó a un estudiante.",
  nivel:
    "Porcentaje de cupos liberados ya reservados: baja < {baja} %, media {baja}–{alta} %, alta > {alta} %.",
  servicio_ideal:
    "El tipo de servicio que corresponde al motivo del estudiante, según la tabla de Reglas.",
  grupo: "Diurno o nocturno, según la modalidad que declara el estudiante.",
  franja:
    "Días y horas en que el estudiante dijo que podía asistir.",
  // Columnas de la tabla de demanda por tipo (textos propios, no vienen del encargo original).
  pedidos: "Todos los pedidos de ese tipo: los atendidos y los que quedaron sin cupo.",
  en_su_tipo: "Pedidos que se atendieron en el servicio que necesitaban.",
  // Reglas: una frase simple por tarjeta.
  regla_motivo:
    "Cada motivo que cuenta el estudiante se traduce al tipo de servicio que le corresponde.",
  regla_afinidad:
    "Qué tan parecido es un servicio a lo que la persona necesita; si el ideal no tiene cupo, solo se ofrece una alternativa con afinidad suficiente.",
  regla_aviso:
    "Señales de la trayectoria académica que activan un aviso para el equipo de bienestar, nunca para el estudiante.",
  regla_asistencia:
    "Probabilidad de que la persona asista según el canal; el motor prefiere canales donde se asiste más.",
  regla_pesos:
    "Cuánto pesa cada objetivo cuando el motor decide las asignaciones: cobertura, espera, equilibrio, equidad y afinidad.",
};

/** Nombres con que se muestran los términos del embudo y otras columnas. */
export const NOMBRES: Partial<Record<Termino, string>> = {
  capacidad_semanal: "Capacidad semanal (D6)",
  capacidad_agenda: "Capacidad en {semanas} semanas",
  libres: "Libres",
  liberados: "Liberados para AURA",
  reservados: "Reservados por AURA",
};

export interface ContextoGlosario {
  pedidos: string;
  linea_base: string;
  semanas: string;
  ocupacion_inicial: string;
  fraccion_liberada: string;
  baja: string;
  alta: string;
}

/** Contexto del glosario a partir de /api/demo/estado (sin estado, los marcadores quedan en «…»). */
export function contextoGlosario(e: EstadoDemo | null): ContextoGlosario {
  if (!e) {
    return {
      pedidos: "…",
      linea_base: "…",
      semanas: "…",
      ocupacion_inicial: "…",
      fraccion_liberada: "…",
      baja: "…",
      alta: "…",
    };
  }
  return {
    pedidos: rangoSinAnio(e.pedidos_desde, e.pedidos_hasta),
    linea_base: num(e.espera_linea_base_dias, 0),
    semanas: num(e.agenda_abierta_semanas, 0),
    ocupacion_inicial: num(e.ocupacion_inicial_pct, 1),
    fraccion_liberada: num(e.fraccion_liberada_pct, 1),
    baja: num(e.umbrales_nivel.baja_menor_que, 0),
    alta: num(e.umbrales_nivel.alta_mayor_que, 0),
  };
}

function rellenar(plantilla: string, ctx: ContextoGlosario): string {
  return plantilla.replace(/\{(\w+)\}/g, (_, clave: string) =>
    clave in ctx ? ctx[clave as keyof ContextoGlosario] : `{${clave}}`,
  );
}

export function textoGlosario(termino: Termino, ctx: ContextoGlosario): string {
  return rellenar(GLOSARIO[termino], ctx);
}

export function nombreTermino(termino: Termino, ctx: ContextoGlosario): string {
  return rellenar(NOMBRES[termino] ?? termino, ctx);
}
