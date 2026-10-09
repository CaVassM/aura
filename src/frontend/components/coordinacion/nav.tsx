import { AlertTriangle, Layers, Map, Radio, Rows3, Scale, Share2 } from "lucide-react";
import { ReactNode } from "react";

export interface ItemNav {
  href: string;
  label: string;
  icon: ReactNode;
}

export const coordinacionNav: ItemNav[] = [
  { href: "/coordinacion", label: "Resumen", icon: <Share2 className="rotate-90" /> },
  { href: "/coordinacion/en-vivo", label: "En vivo", icon: <Radio /> },
  { href: "/coordinacion/lotes", label: "Lotes", icon: <Layers /> },
  { href: "/coordinacion/mapa", label: "Mapa de servicios", icon: <Map /> },
  { href: "/coordinacion/servicios", label: "Servicios", icon: <Rows3 /> },
  { href: "/coordinacion/desencuentros", label: "Desencuentros", icon: <AlertTriangle /> },
  { href: "/coordinacion/reglas", label: "Reglas", icon: <Scale /> },
];
