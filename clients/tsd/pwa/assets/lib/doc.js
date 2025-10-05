// views/doc.js
import { api } from "./?assets=lib/api.js";
import { loadView, $, esc, fmtNum, fmtMoney, unixToLocal } from "./?assets=lib/utils.js";

export async function screenDoc(id) {
  await loadView("doc");

  $("doc-title").textContent = `Документ ${id}`;
  $("ops-list").innerHTML = `<div class="muted">Загрузка...</div>`;
  $("btn-back-docs").onclick = ()=>{ location.hash = "#/docs"; };
  $("btn-add-op").onclick = ()=>{ location.hash = `#/doc/${id}/op/new`; };

  const { data } = await api("purchase_get", { doc_id: id });
  const doc = data?.result?.doc || {};
  const ops = data?.result?.operations || [];

  const status = (doc.performed ? "проведён" : "новый") + (doc.blocked ? " • блок." : "");
  $("doc-status").textContent = status;

  const meta = [
    unixToLocal(doc.date),
    doc.partner?.name || "",
    `${Number(doc.amount ?? 0).toLocaleString("ru-RU",{minimumFractionDigits:2,maximumFractionDigits:2})} ${doc.currency?.code_chr ?? "UZS"}`
  ].filter(Boolean).join(" · ");
  $("doc-meta").textContent = meta;

  const list = $("ops-list");
  if (!ops?.length) { list.innerHTML = `<div class="muted">Операций ещё нет</div>`; return; }
  list.innerHTML = "";
  ops.forEach(op => {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><strong>${esc(op.product_name || "")}</strong></div>
          <div class="muted">${esc(op.barcode || op.product_code || "")}</div>
        </div>
        <div style="text-align:right">
          <div>${fmtNum(op.qty)} шт</div>
          <div class="muted">С/с: ${fmtMoney(op.cost)} · Цена: ${fmtMoney(op.price)}</div>
        </div>
      </div>`;
    list.appendChild(el);
  });
}
