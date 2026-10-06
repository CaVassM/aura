"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarClock, MessageCircle } from "lucide-react";
import PortalShell from "@/components/PortalShell";
import TopbarControls from "@/components/campus/TopbarControls";
import { campusBrand, campusNav, campusUser } from "@/components/campus/nav";
import Tag from "@/components/ui/Tag";
import { getMyAppointments } from "@/lib/api";
import { Appointment } from "@/lib/types";

export default function MisCitasPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  useEffect(() => {
    setAppointments(getMyAppointments());
  }, []);

  return (
    <PortalShell
      brandIcon={campusBrand.icon}
      brandIconBg={campusBrand.iconBg}
      brandName={campusBrand.name}
      brandSubtitle={campusBrand.subtitle}
      nav={campusNav}
      activeHref="/campus/citas"
      user={campusUser}
      exitHref="/"
      exitLabel="Salir del campus"
      title="Mis citas"
      subtitle="Citas agendadas con servicios de bienestar"
      topbarRight={<TopbarControls />}
    >
      <div className="mx-auto max-w-3xl space-y-3 px-8 py-8">
        {appointments.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-xl2 border border-dashed border-aura-border py-20 text-center">
            <CalendarClock className="text-aura-gray" size={28} />
            <p className="text-sm text-aura-gray">
              Todavía no tienes citas agendadas.
            </p>
            <Link
              href="/campus/chat"
              className="flex items-center gap-2 rounded-full bg-aura-teal px-5 py-2.5 text-sm font-semibold text-white hover:bg-aura-teal-dark"
            >
              <MessageCircle size={16} />
              Hablar con AURA
            </Link>
          </div>
        ) : (
          appointments.map((a) => {
            const d = new Date(a.slot.fechaISO);
            return (
              <div
                key={a.id}
                className="flex items-center justify-between rounded-xl2 border border-aura-border bg-white px-6 py-5 shadow-card"
              >
                <div>
                  <p className="text-sm font-semibold text-aura-navy">
                    {a.serviceName}
                  </p>
                  <p className="mt-1 text-sm text-aura-gray">
                    {d.toLocaleDateString("es-PE", {
                      weekday: "long",
                      day: "numeric",
                      month: "long",
                    })}{" "}
                    ·{" "}
                    {d.toLocaleTimeString("es-PE", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <Tag variant="green">Confirmada</Tag>
              </div>
            );
          })
        )}
      </div>
    </PortalShell>
  );
}
