import { ReactNode } from "react";
import CoordinacionShell from "@/components/coordinacion/CoordinacionShell";
import { DemoProvider } from "@/components/coordinacion/DemoProvider";

// Un solo estado de demo y un solo marco (barra lateral + cabecera) para las pantallas de
// Coordinación; al reiniciar la demo, todas recargan sus datos.
export default function CoordinacionLayout({ children }: { children: ReactNode }) {
  return (
    <DemoProvider>
      <CoordinacionShell>{children}</CoordinacionShell>
    </DemoProvider>
  );
}
