"use client";

import { ReactNode } from "react";
import { Resumen } from "@/lib/types-coordinacion";
import { num, rangoDel } from "@/lib/format";
import { Termino } from "@/lib/glosario";
import InfoTip from "../InfoTip";
import NumeroAnimado from "../NumeroAnimado";
import { useDemo } from "../DemoProvider";

function Kpi({
  termino,
  etiqueta,
  valor,
  subtitulo,
  tono = "text-co-navy",
}: {
  termino: Termino;
  etiqueta: string;
  valor: ReactNode;
  subtitulo: string;
  tono?: string;
}) {
  return (
    <div className="px-5 py-5 first:pl-0 sm:px-6">
      <p className="flex min-h-[2.1rem] items-start text-[13px] font-bold leading-tight text-co-navy">
        {etiqueta}
        <InfoTip termino={termino} />
      </p>
      <p className={`mt-2 text-[2.6rem] font-extrabold leading-none ${tono}`}>{valor}</p>
      <p className="mt-2 text-[13px] font-medium leading-snug text-co-ink">{subtitulo}</p>
    </div>
  );
}

/** Los KPI en una banda continua con separadores verticales (sin una tarjeta por cifra). */
export default function BandaKpis({ resumen }: { resumen: Resumen }) {
  const { estado } = useDemo();
  const k = resumen.kpis;
  const semanas = estado ? `${estado.agenda_abierta_semanas} semanas` : "agenda abierta";
  return (
    <div className="grid grid-cols-2 divide-co-line sm:divide-x xl:grid-cols-4">
      <Kpi
        termino="citas_agendadas"
        etiqueta="Citas agendadas"
        valor={<NumeroAnimado valor={k.citas_agendadas} />}
        subtitulo={`Pedidos ${rangoDel(resumen.pedidos.desde, resumen.pedidos.hasta)}`}
      />
      <Kpi
        termino="ocupacion"
        etiqueta="Ocupación de cupos liberados"
        valor={<NumeroAnimado valor={k.ocupacion_pct} decimales={1} sufijo="%" />}
        subtitulo={`${num(k.cupos_reservados, 0)} de ${num(k.cupos_liberados, 0)} reservados · ${semanas}`}
      />
      <Kpi
        termino="desencuentros"
        etiqueta="Desencuentros"
        valor={<NumeroAnimado valor={k.desencuentros} />}
        subtitulo="Pedidos sin cupo compatible"
        tono="text-co-coral-ink"
      />
      <Kpi
        termino="atendidos_alternativa"
        etiqueta="Atendidos con alternativa afín"
        valor={<NumeroAnimado valor={k.atendidos_alternativa} />}
        subtitulo="Pedidos desviados a otro tipo"
        tono="text-co-teal"
      />
    </div>
  );
}
