import {
  ArrowUpRight,
  CalendarCheck,
  Heart,
  HeartHandshake,
  ShieldCheck,
  Sparkles,
  User,
} from "lucide-react";
import Link from "next/link";

const FEATURES = [
  { icon: <CalendarCheck size={16} />, label: "A tu horario" },
  { icon: <Heart size={16} />, label: "A tu ritmo" },
  { icon: <ShieldCheck size={16} />, label: "Tú decides" },
];

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center gap-14 px-6 py-16 lg:flex-row lg:items-center">
      {/* Columna izquierda */}
      <div className="flex-1">
        <span className="inline-flex items-center gap-2 rounded-full border border-aura-border bg-white px-4 py-2 text-xs font-semibold text-aura-navy">
          <Sparkles size={14} className="text-aura-teal" />
          Bienestar universitario conectado
        </span>

        <h1 className="mt-6 text-5xl font-extrabold leading-[1.08] tracking-tight text-aura-navy sm:text-6xl">
          Tu bienestar,
          <br />
          <span className="text-aura-teal">más cerca.</span>
        </h1>

        <p className="mt-6 max-w-md text-lg leading-relaxed text-aura-gray">
          Un punto de encuentro para acceder a los servicios de bienestar de
          tu ciudad universitaria, de forma simple y oportuna.
        </p>

        <div className="mt-8 flex flex-wrap gap-x-8 gap-y-3 border-t border-aura-border pt-6">
          {FEATURES.map((f) => (
            <span
              key={f.label}
              className="flex items-center gap-2 text-sm font-medium text-aura-gray"
            >
              {f.icon}
              {f.label}
            </span>
          ))}
        </div>
      </div>

      {/* Columna derecha: tarjetas de entrada */}
      <div className="flex w-full max-w-md flex-col gap-5">
        <div className="rounded-xl2 border border-aura-teal/15 bg-aura-teal-pale p-7">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-aura-teal-icon-bg text-aura-teal">
            <User size={22} />
          </div>
          <p className="mt-4 text-xs font-bold tracking-wide text-aura-teal">
            CAMPUS VIRTUAL
          </p>
          <p className="mt-1.5 text-2xl font-bold text-aura-navy">
            Entrar como estudiante
          </p>
          <p className="mt-2 text-sm leading-relaxed text-aura-gray">
            Explora opciones de apoyo y encuentra una cita según lo que
            necesitas.
          </p>
          <Link
            href="/campus"
            className="mt-5 flex items-center justify-center gap-2 rounded-full bg-aura-teal px-5 py-3 text-sm font-semibold text-white transition hover:bg-aura-teal-dark"
          >
            Ingresar al campus
            <ArrowUpRight size={16} />
          </Link>
        </div>

        <div className="rounded-xl2 border border-aura-border bg-white p-7">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-aura-purple-pale text-aura-purple">
            <HeartHandshake size={22} />
          </div>
          <p className="mt-4 text-xs font-bold tracking-wide text-aura-teal">
            COORDINACIÓN DE RED
          </p>
          <p className="mt-1.5 text-2xl font-bold text-aura-navy">
            Entrar como equipo de bienestar
          </p>
          <p className="mt-2 text-sm leading-relaxed text-aura-gray">
            Observa la disponibilidad y el funcionamiento de la red de
            servicios.
          </p>
          <Link
            href="/coordinacion"
            className="mt-5 flex items-center justify-center gap-2 rounded-full border border-aura-border bg-white px-5 py-3 text-sm font-semibold text-aura-navy transition hover:bg-aura-bg"
          >
            Abrir panel
            <ArrowUpRight size={16} />
          </Link>
        </div>
      </div>
    </main>
  );
}
