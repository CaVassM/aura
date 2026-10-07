import { ReactNode } from "react";
import { DemoProvider } from "@/components/coordinacion/DemoProvider";

// Un solo estado de demo para las cuatro pantallas de Coordinación: escenario, fechas y
// reinicio. Al reiniciar, todas las pantallas recargan sus datos.
export default function CoordinacionLayout({ children }: { children: ReactNode }) {
  return <DemoProvider>{children}</DemoProvider>;
}
