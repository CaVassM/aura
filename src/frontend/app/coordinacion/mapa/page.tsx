import { MapPin } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { coordinacionBrand, coordinacionNav } from "@/components/coordinacion/nav";
import Placeholder from "@/components/ui/Placeholder";

export default function MapaPage() {
  return (
    <PortalShell
      brandIcon={coordinacionBrand.icon}
      brandIconBg={coordinacionBrand.iconBg}
      brandName={coordinacionBrand.name}
      brandSubtitle={coordinacionBrand.subtitle}
      nav={coordinacionNav}
      activeHref="/coordinacion/mapa"
      exitHref="/"
      exitLabel="Volver a AURA"
      title="Mapa de servicios"
      subtitle="Fuera del alcance del Entregable 2"
    >
      <Placeholder
        icon={<MapPin />}
        title="Mapa de servicios"
        description="Geolocalización de los servicios de bienestar (dataset D6). Se puede construir más adelante si el equipo lo necesita."
      />
    </PortalShell>
  );
}
