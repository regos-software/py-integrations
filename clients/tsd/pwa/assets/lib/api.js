// api.js (token detection + API + SW)

export const CI = (() => {
  const seg = location.pathname.split("/").filter(Boolean);
  const fromPath = seg[0] === "external" ? seg[1] : null;
  return (window.__CI__ || new URLSearchParams(location.search).get("ci") || fromPath || "").trim();
})();

export async function api(action, params = {}) {
  // относительный вызов -> /external/{ci}/external (проксируется в адаптер)
  const res = await fetch("external", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Connected-Integration-Id": CI },
    body: JSON.stringify({ action, params })
  });
  let data = {}; try { data = await res.json(); } catch {}
  return { ok: res.ok, status: res.status, data };
}

export function registerSW() {
  if (!("serviceWorker" in navigator)) return;
  // регистрируем sw относительно текущего /external/{ci}
  const scope = location.pathname.endsWith("/") ? location.pathname : (location.pathname + "/");
  navigator.serviceWorker.register("?pwa=sw", { scope }).catch(() => {});
}
