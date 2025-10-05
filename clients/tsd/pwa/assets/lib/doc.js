// views/doc.js — без import; получает ctx
export async function screenDoc(ctx, id) {
  await ctx.loadView("doc");

  // кнопки
  ctx.$("btn-back-docs").onclick = () => { location.hash = "#/docs"; };
  ctx.$("btn-add-op").onclick   = () => { location.hash = `#/doc/${id}/op/new`; };

  // спиннер
  ctx.$("ops-list").innerHTML = `<div class="muted">Загрузка...</div>`;

  // запрашиваем документ (+ возможно операции)
  const { data } = await ctx.api("purchase_get", { doc_id: id });
  const doc = data?.result?.doc || {};
  let ops   = data?.result?.operations;

  // если бек не вернул operations — добираем отдельно
  if (!Array.isArray(ops)) {
    const r2 = await ctx.api("purchase_ops_get", { doc_id: id });
    ops = r2?.data?.result?.items || [];
  }

  // шапка
  ctx.$("doc-title").textContent = `Документ ${doc.code || id}`;
  const status = (doc.performed ? "проведён" : "новый") + (doc.blocked ? " • блок." : "");
  ctx.$("doc-status").textContent = status;

  const meta = [
    ctx.unixToLocal(doc.date),
    doc.partner?.name || "",
    `${Number(doc.amount ?? 0).toLocaleString("ru-RU",{minimumFractionDigits:2,maximumFractionDigits:2})} ${doc.currency?.code_chr ?? "UZS"}`
  ].filter(Boolean).join(" · ");
  ctx.$("doc-meta").textContent = meta;

  // список операций
  const list = ctx.$("ops-list");
  if (!ops?.length) {
    list.innerHTML = `<div class="muted">Операций ещё нет</div>`;
    return;
  }

  list.innerHTML = "";
  ops.forEach(op => {
    const item = op.item || {};
    const barcode = item.base_barcode
      || (item.barcode_list ? String(item.barcode_list).split(",")[0]?.trim() : "");

    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><strong>${ctx.esc(item.name || "")}</strong></div>
          <div class="muted">${ctx.esc(barcode || "")}</div>
        </div>
        <div style="text-align:right">
          <div>${ctx.fmtNum(op.quantity)} шт</div>
          <div class="muted">С/с: ${ctx.fmtMoney(op.cost)} · Цена: ${ctx.fmtMoney(op.price ?? 0)}</div>
        </div>
      </div>`;
    list.appendChild(el);
  });
}
