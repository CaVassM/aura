import { AlertTriangle } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import { coordinacionBrand, coordinacionNav } from "@/components/coordinacion/nav";
import Placeholder from "@/components/ui/Placeholder";

export default function DesencuentrosPage() {
  return (
    <PortalShell
      brandIcon={coordinacionBrand.icon}
      brandIconBg={coordinacionBrand.iconBg}
      brandName={coordinacionBrand.name}
      brandSubtitle={coordinacionBrand.subtitle}
      nav={coordinacionNav}
      activeHref="/coordinacion/desencuentros"
      exitHref="/"
      exitLabel="Volver a AURA"
      title="Desencuentros"
      subtitle="Fuera del alcance del Entregable 2"
    >
      <Placeholder
        icon={<AlertTriangle />}
        title="Desencuentros"
        description="Registro de estudiantes sin horario compatible, para justificar aperturas institucionales. Se puede construir más adelante si el equipo lo necesita."
      />
    </PortalShell>
  );
}
