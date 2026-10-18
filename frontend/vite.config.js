import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Production CSP injected into built index.html only (keeps Vite HMR working in dev).
const CSP =
  "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; " +
  "font-src https://fonts.gstatic.com; img-src 'self' data:; " +
  "connect-src 'self' https://bloom-api.onrender.com;";

/** @type {import('vite').Plugin} */
const cspPlugin = {
  name: "inject-csp",
  apply: "build",
  transformIndexHtml(html) {
    return html.replace(
      "</head>",
      `  <meta http-equiv="Content-Security-Policy" content="${CSP}" />\n  </head>`
    );
  },
};

export default defineConfig({
  plugins: [react(), cspPlugin],
  server: { port: 5173 },
});
