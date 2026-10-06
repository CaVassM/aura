import { AlertTriangle, MapPin, Scale, Share2 } from "lucide-react";
import { NavItem } from "@/components/PortalShell";

export const coordinacionNav: NavItem[] = [
  {
    href: "/coordinacion",
    label: "Resumen",
    icon: <Share2 className="rotate-90" />,
  },
  { href: "/coordinacion/mapa", label: "Mapa de servicios", icon: <MapPin /> },
  {
    href: "/coordinacion/desencuentros",
    label: "Desencuentros",
    icon: <AlertTriangle />,
  },
  { href: "/coordinacion/reglas", label: "Reglas", icon: <Scale /> },
];

export const coordinacionBrand = {
  icon: <Share2 size={18} className="text-white" />,
  iconBg: "bg-aura-navy",
  name: "Red de Bienestar",
  subtitle: "Aethera · Coordinación",
};
