import { Scale } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { coordinacionBrand, coordinacionNav } from "@/components/coordinacion/nav";
import Placeholder from "@/components/ui/Placeholder";

export default function ReglasPage() {
  return (
    <PortalShell
      brandIcon={coordinacionBrand.icon}
      brandIconBg={coordinacionBrand.iconBg}
      brandName={coordinacionBrand.name}
      brandSubtitle={coordinacionBrand.subtitle}
      nav={coordinacionNav}
      activeHref="/coordinacion/reglas"
      exitHref="/"
      exitLabel="Volver a AURA"
      title="Reglas"
      subtitle="Fuera del alcance del Entregable 2"
    >
      <Placeholder
        icon={<Scale />}
        title="Reglas de asignación"
        description="Parámetros del optimizador (prioridad por espera, equidad, umbrales). Se puede construir más adelante si el equipo lo necesita."
      />
    </PortalShell>
  );
}
