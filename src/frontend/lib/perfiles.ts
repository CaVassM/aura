/**
 * Perfiles de estudiante de la demo (datos simulados de la ciudad ficticia de Aethera).
 *
 * Cada perfil es lo que el portal "ya sabe" de la persona y lo que se manda al backend en cada
 * mensaje del chat: `id` → `estudiante_id`, `distrito` → `distrito`. El distrito es donde la persona
 * vive (D1 `district_id`) y se usa para sus citas presenciales; en la conversación puede cambiarlo
 * ("esta semana estoy por Vector"). El turno de estudio (diurno/nocturno) NO va aquí: el agente lo
 * toma de lo que la persona cuente.
 *
 * Los distritos son los 5 de la red (D6). Los ids `STU_DEMO_###` no chocan con los de los datos
 * (`STU_AE_######`). Todo vive en RAM en el backend: al reiniciarlo se pierden citas y conversaciones.
 */

export type DistritoId =
  | "DIST_GAIA"
  | "DIST_NEBULA"
  | "DIST_VECTOR"
  | "DIST_HORIZON"
  | "DIST_QUANTUM";

export const DISTRITOS: Record<DistritoId, string> = {
  DIST_GAIA: "Gaia",
  DIST_NEBULA: "Nébula",
  DIST_VECTOR: "Vector",
  DIST_HORIZON: "Horizon",
  DIST_QUANTUM: "Quantum",
};

export interface PerfilEstudiante {
  /** Se envía como `estudiante_id`. */
  id: string;
  nombre: string;
  /** Nombre de pila para saludar. */
  corto: string;
  iniciales: string;
  /** Código de la institución (D1 `institution_id`); solo informativo en la demo. */
  institucion: "UNI_NOVA_AETHER";
  /** Se envía como `distrito`. */
  distrito: DistritoId;
  /** Color del avatar (clases completas para que Tailwind las incluya). */
  avatar: string;
}

export const PERFILES: PerfilEstudiante[] = [
  {
    id: "STU_DEMO_001",
    nombre: "Lucía Mendoza",
    corto: "Lucía",
    iniciales: "LM",
    institucion: "UNI_NOVA_AETHER",
    distrito: "DIST_NEBULA",
    avatar: "bg-co-coral-tint text-co-coral-ink",
  },
  {
    id: "STU_DEMO_002",
    nombre: "Mateo Rivas",
    corto: "Mateo",
    iniciales: "MR",
    institucion: "UNI_NOVA_AETHER",
    distrito: "DIST_VECTOR",
    avatar: "bg-co-amber-tint text-co-amber-ink",
  },
  {
    id: "STU_DEMO_003",
    nombre: "Valentina Ortega",
    corto: "Valentina",
    iniciales: "VO",
    institucion: "UNI_NOVA_AETHER",
    distrito: "DIST_GAIA",
    avatar: "bg-co-sage-tint text-co-sage-ink",
  },
  {
    id: "STU_DEMO_004",
    nombre: "Diego Salas",
    corto: "Diego",
    iniciales: "DS",
    institucion: "UNI_NOVA_AETHER",
    distrito: "DIST_HORIZON",
    avatar: "bg-co-teal-tint text-co-teal-dark",
  },
];

export const PERFIL_INICIAL = PERFILES[0];

export const nombreDistrito = (id: string): string =>
  DISTRITOS[id as DistritoId] ?? id.replace("DIST_", "");
