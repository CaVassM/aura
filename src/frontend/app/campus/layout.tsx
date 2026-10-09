import { ReactNode } from "react";
import { PerfilProvider } from "@/components/campus/PerfilProvider";

export default function CampusLayout({ children }: { children: ReactNode }) {
  return <PerfilProvider>{children}</PerfilProvider>;
}
