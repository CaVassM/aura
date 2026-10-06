import { BookOpen } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav, campusUser } from "@/components/campus/nav";
import Placeholder from "@/components/ui/Placeholder";

export default function CursosPage() {
  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus/cursos"
      user={campusUser}
      exitHref="/"
      exitLabel="Salir del campus"
      title="Mis cursos"
      subtitle="Fuera del alcance del Entregable 2"
      topbarRight={<TopbarControls />}
    >
      <Placeholder
        icon={<BookOpen />}
        title="Mis cursos"
        description="Esta sección pertenece al campus virtual general, no a la misión de AURA. Se puede construir más adelante si el equipo lo necesita."
      />
    </PortalShell>
  );
}
