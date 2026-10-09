import { ClipboardCheck } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav } from "@/components/campus/nav";
import Placeholder from "@/components/ui/Placeholder";

export default function CalificacionesPage() {
  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus/calificaciones"
      exitHref="/"
      exitLabel="Salir del campus"
      title="Calificaciones"
      subtitle="Fuera del alcance del Entregable 2"
      topbarRight={<TopbarControls />}
    >
      <Placeholder
        icon={<ClipboardCheck />}
        title="Calificaciones"
        description="Esta sección pertenece al campus virtual general, no a la misión de AURA. Se puede construir más adelante si el equipo lo necesita."
      />
    </PortalShell>
  );
}
