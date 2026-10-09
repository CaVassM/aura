import {
  BookOpen,
  CalendarDays,
  ClipboardCheck,
  Clock,
  GraduationCap,
  Heart,
  Home,
} from "lucide-react";
import { NavItem } from "@/components/PortalShell";

export const campusNav: NavItem[] = [
  { href: "/campus", label: "Inicio", icon: <Home /> },
  { href: "/campus/cursos", label: "Mis cursos", icon: <BookOpen /> },
  {
    href: "/campus/calificaciones",
    label: "Calificaciones",
    icon: <ClipboardCheck />,
  },
  { href: "/campus/calendario", label: "Calendario", icon: <CalendarDays /> },
  { href: "/campus/chat", label: "Bienestar", icon: <Heart /> },
  { href: "/campus/citas", label: "Mis citas", icon: <Clock /> },
];

export const campusBrand = {
  icon: <GraduationCap size={20} className="text-co-teal-deep" />,
  iconBg: "bg-co-bg",
  name: "Universidad Nova",
  subtitle: "Aethera · Campus Virtual",
};
