import { ReactNode } from "react";
import { ActividadProvider } from "@/components/coordinacion/ActividadProvider";
import CoordinacionShell from "@/components/coordinacion/CoordinacionShell";
import { DemoProvider } from "@/components/coordinacion/DemoProvider";

// Un solo estado de demo y un solo marco (barra lateral + cabecera) para las pantallas de
// Coordinación; al reiniciar la demo, todas recargan sus datos, y la actividad en vivo (citas nuevas)
// llega por un flujo en tiempo real que también las refresca.
export default function CoordinacionLayout({ children }: { children: ReactNode }) {
  return (
    <DemoProvider>
      <ActividadProvider>
        <CoordinacionShell>{children}</CoordinacionShell>
      </ActividadProvider>
    </DemoProvider>
  );
}
