// views/home.js — без import; получает ctx
export async function screenHome(ctx) {
  await ctx.loadView("home");

  ctx.$("home-title").textContent              = ctx.t("ready_title");
  ctx.$("token-label").textContent             = ctx.t("current_token");
  ctx.$("ci-label").textContent                = ctx.CI || "—";

  ctx.$("btn-doc-purchase-txt").textContent    = ctx.t("doc_purchase");
  ctx.$("btn-doc-sales-txt").textContent       = ctx.t("doc_sales");
  ctx.$("btn-doc-inventory-txt").textContent   = ctx.t("doc_inventory");
  ctx.$("pill-sales").textContent              = ctx.t("soon");
  ctx.$("pill-inventory").textContent          = ctx.t("soon");

  ctx.$("btn-doc-purchase").onclick = () => { location.hash = "#/docs"; };

  const soon = () => {
    let t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.className = "toast";
      document.body.appendChild(t);
    }
    t.textContent = ctx.t("soon");
    t.classList.add("show");
    setTimeout(()=>t.classList.remove("show"), 1500);
  };
  ctx.$("btn-doc-sales").onclick     = soon;
  ctx.$("btn-doc-inventory").onclick = soon;
}
