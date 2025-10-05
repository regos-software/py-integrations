// app.js (router + bootstrap)
import { CI, registerSW } from "./?assets=lib/api.js";
import { $, out, tickClock } from "./?assets=lib/utils.js";
import { screenHome } from "./?assets=views/home.js";
import { screenDocs } from "./?assets=views/docs.js";
import { screenDoc } from "./?assets=views/doc.js";
import { screenOpNew } from "./?assets=views/op_new.js";

// UI bootstrap
$("title").textContent = "TSD • Закупки";
tickClock(); setInterval(tickClock, 1000);
registerSW();

// SPA router
async function router() {
  const h = location.hash || "#/home";
  if (h.startsWith("#/docs")) {
    const qs = new URLSearchParams(h.split("?")[1] || "");
    const p = parseInt(qs.get("page") || "1", 10) || 1;
    const q = qs.get("q") || "";
    await screenDocs(p, q);
  } else if (h.startsWith("#/doc/") && h.endsWith("/op/new")) {
    const id = h.split("/")[2];
    await screenOpNew(id);
  } else if (h.startsWith("#/doc/")) {
    const id = h.split("/")[2];
    await screenDoc(id);
  } else {
    await screenHome();
  }
}
window.addEventListener("hashchange", router);
router();

// для отладки
window.__CI__ = CI;
window.__out = out;
