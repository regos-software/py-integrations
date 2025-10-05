// app.js (router + bootstrap) — без статичных import

const rel = (q) => new URL(q, import.meta.url).toString();

// грузим либы динамически, сохраняя /external/{ci}
const apiLib   = await import(rel('?assets=lib/api.js'));   // { CI, api, registerSW }
const utilsLib = await import(rel('?assets=lib/utils.js')); // {$, out, tickClock, loadView, ...}

// контекст, который будем передавать во вьюхи
const ctx = {
  ...apiLib,
  ...utilsLib,
};

// UI bootstrap
ctx.$("title").textContent = "TSD";
ctx.tickClock(); setInterval(ctx.tickClock, 1000);
ctx.registerSW();

// грузим вьюхи динамически
const views = {
  home:   await import(rel('?assets=views/home.js')),   // export screenHome(ctx)
  docs:   await import(rel('?assets=views/docs.js')),   // export screenDocs(ctx, page, q)
  doc:    await import(rel('?assets=views/doc.js')),    // export screenDoc(ctx, id)
  op_new: await import(rel('?assets=views/op_new.js')), // export screenOpNew(ctx, id)
};

// SPA router
async function router() {
  const h = location.hash || "#/home";
  if (h.startsWith("#/docs")) {
    const qs = new URLSearchParams(h.split("?")[1] || "");
    const p = parseInt(qs.get("page") || "1", 10) || 1;
    const q = qs.get("q") || "";
    await views.docs.screenDocs(ctx, p, q);
  } else if (h.startsWith("#/doc/") && h.endsWith("/op/new")) {
    const id = h.split("/")[2];
    await views.op_new.screenOpNew(ctx, id);
  } else if (h.startsWith("#/doc/")) {
    const id = h.split("/")[2];
    await views.doc.screenDoc(ctx, id);
  } else {
    await views.home.screenHome(ctx);
  }
}
window.addEventListener("hashchange", router);
router();

// для отладки
window.__CI__  = apiLib.CI;
window.__out   = utilsLib.out;
