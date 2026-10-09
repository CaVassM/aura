import {
  Compass,
  HeartHandshake,
  LucideIcon,
  MapPin,
  Phone,
  Users,
  Video,
} from "lucide-react";

/**
 * Cómo se ve cada tipo de servicio y cada canal. Cada tipo tiene su color (misma paleta `co`
 * del panel de Coordinación) para reconocerlo de un vistazo en las tarjetas del chat y en "Mis citas".
 * Las clases van completas para que Tailwind las incluya.
 */
export interface EstiloServicio {
  icono: LucideIcon;
  /** Relleno plano (franja, ícono). */
  solido: string;
  /** Fondo suave. */
  tinte: string;
  /** Texto sobre el tinte (contraste AA). */
  tinta: string;
  /** Borde al pasar el cursor. */
  borde: string;
  /** Degradado del encabezado de la tarjeta. */
  degradado: string;
}

export const SERVICIOS_UI: Record<string, EstiloServicio> = {
  counseling: {
    icono: HeartHandshake,
    solido: "bg-co-teal",
    tinte: "bg-co-teal-tint",
    tinta: "text-co-teal-dark",
    borde: "hover:border-co-teal",
    degradado: "from-co-teal to-co-teal-deep",
  },
  peer_support: {
    icono: Users,
    solido: "bg-co-coral",
    tinte: "bg-co-coral-tint",
    tinta: "text-co-coral-ink",
    borde: "hover:border-co-coral",
    degradado: "from-co-coral to-co-coral-ink",
  },
  career_guidance: {
    icono: Compass,
    solido: "bg-co-amber",
    tinte: "bg-co-amber-tint",
    tinta: "text-co-amber-ink",
    borde: "hover:border-co-amber",
    degradado: "from-co-amber to-co-amber-ink",
  },
};

export const estiloServicio = (tipo: string): EstiloServicio =>
  SERVICIOS_UI[tipo] ?? SERVICIOS_UI.counseling;

export const CANALES_UI: Record<string, { label: string; icono: LucideIcon }> = {
  digital: { label: "Videollamada", icono: Video },
  phone: { label: "Teléfono", icono: Phone },
  in_person: { label: "Presencial", icono: MapPin },
};

export const canalUi = (canal: string) =>
  CANALES_UI[canal] ?? { label: canal, icono: Video };
