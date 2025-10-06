// lib/api.js (token detection + API + SW)

// ---- CI (token) ----
export const CI = (() => {
  const seg = location.pathname.split("/").filter(Boolean);
  const fromPath = seg[0] === "external" ? seg[1] : null;
  return (window.__CI__ || new URLSearchParams(location.search).get("ci") || fromPath || "").trim();
})();

// ---- base path helper: всегда /external/{ci}/ ----
function getBasePath() {
  const seg = location.pathname.split("/").filter(Boolean);
  if (seg[0] === "external" && seg[1]) return `/external/${seg[1]}/`;
  // fallback: текущий путь с завершающим слэшем
  return location.pathname.endsWith("/") ? location.pathname : (location.pathname + "/");
}
const BASE = getBasePath();

// ---- API ----
export async function api(action, params = {}) {
  // гарантированно: /external/{ci}/external
  const url = BASE + "external";
    const res = await fetch(BASE + "external", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, params })
    });
  let data = {}; try { data = await res.json(); } catch {}
  return { ok: res.ok, status: res.status, data };
}

// ---- SW ----
export function registerSW() {
  if (!("serviceWorker" in navigator)) return;
  // sw по /external/{ci}/?pwa=sw, scope = /external/{ci}/
  const swUrl = BASE + "?pwa=sw";
  navigator.serviceWorker.register(swUrl, { scope: BASE }).catch(() => {});
}
