import { ReactNode } from "react";

/**
 * Pinta el texto del agente con el poco formato que suele traer: **negritas**, viñetas y listas numeradas.
 * Se arma con elementos de React (no con HTML) para que nada del texto se interprete como código.
 */
function enLinea(texto: string, clave: string): ReactNode[] {
  return texto.split(/(\*\*[^*]+\*\*)/g).map((trozo, i) =>
    trozo.startsWith("**") && trozo.endsWith("**") && trozo.length > 4 ? (
      <strong key={`${clave}-${i}`} className="font-bold">
        {trozo.slice(2, -2)}
      </strong>
    ) : (
      <span key={`${clave}-${i}`}>{trozo.replace(/\*(?=\S)|(?<=\S)\*/g, "")}</span>
    ),
  );
}

const VINETA = /^\s*(?:[-*•]|\d+[.)])\s+/;

export default function Texto({ texto }: { texto: string }) {
  const lineas = texto.split("\n");
  const bloques: ReactNode[] = [];
  let lista: string[] = [];

  const cerrarLista = () => {
    if (!lista.length) return;
    const k = bloques.length;
    bloques.push(
      <ul key={`l${k}`} className="my-1.5 space-y-1 pl-1">
        {lista.map((l, i) => (
          <li key={i} className="flex gap-2">
            <span className="mt-[0.55em] h-1.5 w-1.5 shrink-0 rounded-full bg-co-teal" aria-hidden="true" />
            <span>{enLinea(l, `l${k}-${i}`)}</span>
          </li>
        ))}
      </ul>,
    );
    lista = [];
  };

  lineas.forEach((linea, i) => {
    if (VINETA.test(linea)) {
      lista.push(linea.replace(VINETA, ""));
      return;
    }
    cerrarLista();
    if (linea.trim()) bloques.push(<p key={`p${i}`}>{enLinea(linea, `p${i}`)}</p>);
  });
  cerrarLista();

  return <div className="space-y-2">{bloques}</div>;
}

/** Con tarjetas en pantalla, la lista numerada del texto sobra: se conserva solo lo demás. */
export function sinLista(texto: string): string {
  return texto
    .split("\n")
    .filter((l) => !VINETA.test(l))
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
