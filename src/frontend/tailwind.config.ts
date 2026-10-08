import type { Config } from "tailwindcss";

// `aura.*` es la paleta del campus del estudiante (no se toca).
// `co.*` es la paleta del panel de Coordinación: crema cálido, teal profundo y navy para el
// texto; coral = alta demanda y desencuentros, ámbar = media, salvia = baja.
// Contraste mínimo AA: los textos usan navy / ink / *-ink sobre crema o sobre sus tintes; los
// colores planos (coral, ámbar, salvia) son para rellenos y barras, no para texto pequeño.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        aura: {
          bg: "#FAF8F3",
          surface: "#FFFFFF",
          navy: "#243442",
          gray: "#6E7987",
          "gray-light": "#C3C7CC",

          teal: "#285B63",
          "teal-dark": "#1D4046",
          "teal-pale": "#E7F1EE",
          "teal-icon-bg": "#C7E6DC",

          purple: "#6B5E8E",
          "purple-pale": "#EFEBF8",
          "purple-nav": "#ECE9F2",

          border: "#E7E2D6",

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
        co: {
          bg: "#F6F3EE", // fondo crema
          paper: "#FFFCF7", // superficie cálida (drawer, tooltips)
          line: "#E0D6C5", // hairline cálido
          navy: "#1D2E3C", // texto principal
          ink: "#3F5160", // texto secundario (AA sobre crema)
          teal: "#1B5E66", // primario
          "teal-dark": "#12444B",
          "teal-deep": "#0F3B42", // fondo de la barra lateral y la tarjeta héroe
          "teal-tint": "#DCEBE8",
          coral: "#D9573D", // alta demanda, desencuentros
          "coral-ink": "#A33B26",
          "coral-tint": "#FBE3DB",
          amber: "#E2A22F", // media
          "amber-ink": "#7E5300",
          "amber-tint": "#F8E9C6",
          sage: "#5C9C84", // baja
          "sage-ink": "#285F49",
          "sage-tint": "#DDEDE4",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(36,52,66,0.04), 0 1px 3px rgba(36,52,66,0.06)",
        pop: "0 8px 24px rgba(29,46,60,0.14)",
        drawer: "-12px 0 32px rgba(29,46,60,0.16)",
      },
      borderRadius: {
        xl2: "20px",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-only": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(28px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "slide-out-right": {
          "0%": { opacity: "1", transform: "translateX(0)" },
          "100%": { opacity: "0", transform: "translateX(28px)" },
        },
        "grow-x": {
          "0%": { transform: "scaleX(0)" },
          "100%": { transform: "scaleX(1)" },
        },
        "pop-in": {
          "0%": { opacity: "0", transform: "scale(0.5)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        halo: {
          "0%": { opacity: "0.55", transform: "scale(1)" },
          "100%": { opacity: "0", transform: "scale(2.1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 450ms cubic-bezier(0.22, 1, 0.36, 1) both",
        "fade-only": "fade-only 200ms ease-out both",
        "slide-in-right": "slide-in-right 380ms cubic-bezier(0.22, 1, 0.36, 1) both",
        "slide-out-right": "slide-out-right 220ms ease-in both",
        "grow-x": "grow-x 700ms cubic-bezier(0.22, 1, 0.36, 1) both",
        "pop-in": "pop-in 480ms cubic-bezier(0.34, 1.56, 0.64, 1) both",
        halo: "halo 2.4s ease-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
