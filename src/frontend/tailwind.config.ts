import type { Config } from "tailwindcss";

// Estos valores salieron de muestrear directamente los píxeles de tus
// 4 capturas de Figma (fondo, botones, tarjetas, tags, barras del gráfico).
// Si algo no calza 100% al comparar lado a lado, es el único archivo
// que necesitas tocar — todo el proyecto usa estos nombres (aura-navy,
// aura-teal, etc.), nunca un hex suelto dentro de un componente.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        aura: {
          bg: "#FAF8F3",        // fondo general (crema cálido)
          surface: "#FFFFFF",   // tarjetas blancas
          navy: "#243442",      // títulos y texto principal
          gray: "#6E7987",      // texto secundario / párrafos
          "gray-light": "#C3C7CC", // etiquetas pequeñas muy suaves

          teal: "#285B63",      // color de marca: botones, íconos, acentos
          "teal-dark": "#1D4046", // hover/pressed del teal
          "teal-pale": "#E7F1EE", // fondo suave con tinte teal (tarjetas)
          "teal-icon-bg": "#C7E6DC", // fondo de cajitas de ícono en teal

          purple: "#6B5E8E",       // acento secundario (equipo de bienestar)
          "purple-pale": "#EFEBF8", // fondo suave con tinte púrpura
          "purple-nav": "#ECE9F2",  // fondo de ítem activo en sidebar

          border: "#E7E2D6",      // borde neutro sobre fondo crema

          "tag-green-bg": "#DFEAE3",
          "tag-green-text": "#3D6B57",
          "tag-purple-bg": "#E7E3F1",
          "tag-purple-text": "#6C5F96",
          "tag-yellow-bg": "#F5E8C9",
          "tag-yellow-text": "#9C7A2E",
          "tag-red-bg": "#F6DAD4",
          "tag-red-text": "#B85C4E",

          "chart-green": "#80AE9B",
          "chart-yellow": "#D9B35C",
          "chart-red": "#C77F73",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(36,52,66,0.04), 0 1px 3px rgba(36,52,66,0.06)",
      },
      borderRadius: {
        xl2: "20px",
      },
    },
  },
  plugins: [],
};
export default config;
