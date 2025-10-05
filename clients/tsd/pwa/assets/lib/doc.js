// views/doc.js — без import; получает ctx
export async function screenDoc(ctx, id) {
  await ctx.loadView("doc");

  ctx.$("doc-title").textContent = `Документ ${id}`;
  ctx.$("ops-list").innerHTML = `<div class="muted">Загрузка...</div>`;
  ctx.$("btn-back-docs").onclick = ()=>{ location.hash = "#/docs"; };
  ctx.$("btn-add-op").onclick   = ()=>{ location.hash = `#/doc/${id}/op/new`; };

  const { data } = await ctx.api("purchase_get", { doc_id: id });
  const doc = data?.result?.doc || {};
  const ops = data?.result?.operations || [];

  const status = (doc.performed ? "проведён" : "новый") + (doc.blocked ? " • блок." : "");
  ctx.$("doc-status").textContent = status;

  const meta = [
    ctx.unixToLocal(doc.date),
    doc.partner?.name || "",
    `${Number(doc.amount ?? 0).toLocaleString("ru-RU",{minimumFractionDigits:2,maximumFractionDigits:2})} ${doc.currency?.code_chr ?? "UZS"}`
  ].filter(Boolean).join(" · ");
  ctx.$("doc-meta").textContent = meta;

  const list = ctx.$("ops-list");
  if (!ops?.length) { list.innerHTML = `<div class="muted">Операций ещё нет</div>`; return; }
  list.innerHTML = "";
  ops.forEach(op => {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><strong>${ctx.esc(op.product_name || "")}</strong></div>
          <div class="muted">${ctx.esc(op.barcode || op.product_code || "")}</div>
        </div>
        <div style="text-align:right">
          <div>${ctx.fmtNum(op.qty)} шт</div>
          <div class="muted">С/с: ${ctx.fmtMoney(op.cost)} · Цена: ${ctx.fmtMoney(op.price)}</div>
        </div>
      </div>`;
    list.appendChild(el);
  });
}
