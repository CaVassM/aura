import { ReactNode } from "react";

// A diferencia del layout, el template se vuelve a montar al cambiar de sección: fundido suave (solo opacidad: un transform rompería los elementos fixed).
export default function CoordinacionTemplate({ children }: { children: ReactNode }) {
  return <div className="animate-fade-only">{children}</div>;
}
