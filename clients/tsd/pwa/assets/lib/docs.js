// views/doc.js — без import; получает ctx
export async function screenDoc(ctx, id) {
  await ctx.loadView("doc");

  // локализация кнопок/подписей
  const $spinnerMsg = () => `<div class="muted">${ctx.t("common.loading")}</div>`;
  const $emptyMsg   = () => `<div class="muted">${ctx.t("doc.no_ops") || ctx.t("common.nothing")}</div>`;

  ctx.$("btn-back-docs").textContent = ctx.t("doc.to_list");
  ctx.$("btn-add-op").textContent    = ctx.t("doc.add_op");
  ctx.$("btn-back-docs").onclick = () => { location.hash = "#/docs"; };
  ctx.$("btn-add-op").onclick   = () => { location.hash = `#/doc/${id}/op/new`; };

  // спиннер
  ctx.$("ops-list").innerHTML = $spinnerMsg();

  // документ + операции
  const { data } = await ctx.api("purchase_get", { doc_id: id });
  const doc = data?.result?.doc || {};
  let ops   = data?.result?.operations;

  if (!Array.isArray(ops)) {
    const r2 = await ctx.api("purchase_ops_get", { doc_id: id });
    ops = r2?.data?.result?.items || [];
  }

  // шапка документа
  ctx.$("doc-title").textContent = `${ctx.t("doc.title_prefix") || "Документ"} ${doc.code || id}`;
  const statusStr = `${doc.performed ? ctx.t("docs.status.performed") : ctx.t("docs.status.new")}${
    doc.blocked ? " • " + ctx.t("docs.status.blocked") : ""
  }`;
  ctx.$("doc-status").textContent = statusStr;

  const meta = [
    ctx.unixToLocal(doc.date),
    doc.partner?.name || "",
    `${ctx.fmtNum(doc.amount, { minimumFractionDigits:2, maximumFractionDigits:2 })} ${doc.currency?.code_chr ?? "UZS"}`
  ].filter(Boolean).join(" · ");
  ctx.$("doc-meta").textContent = meta;

  // рендер списка операций
  const list = ctx.$("ops-list");
  if (!ops?.length) { list.innerHTML = $emptyMsg(); return; }

  renderOps(ops);

  // ---------- helpers ----------

  function toast(msg, isError=false){
    let t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.className = "toast";
      document.body.appendChild(t);
    }
    t.classList.toggle("error", !!isError);
    t.textContent = msg || "";
    t.classList.add("show");
    setTimeout(()=>t.classList.remove("show"), 1600);
  }

  function renderOps(items){
    list.innerHTML = "";
    items.forEach(op => list.appendChild(renderOpItem(op)));
  }

  function renderOpItem(op){
    const item = op.item || {};
    const barcode = item.base_barcode
      || (item.barcode_list ? String(item.barcode_list).split(",")[0]?.trim() : "");

    const wrap = document.createElement("div");
    wrap.className = "item";

    // view mode
    const view = document.createElement("div");
    view.className = "row";
    view.innerHTML = `
      <div>
        <div><strong>${ctx.esc(item.name || "")}</strong></div>
        <div class="muted">${ctx.esc(barcode || "")}</div>
      </div>
      <div class="meta">
        <div><strong>${ctx.fmtNum(op.quantity)}</strong> ${ctx.t("unit.pcs") || "шт"}</div>
        <span class="dot"></span>
        <div class="muted">${ctx.t("op.cost")}: ${ctx.fmtMoney(op.cost)}</div>
        <span class="dot"></span>
        <div class="muted">${ctx.t("op.price")}: ${ctx.fmtMoney(op.price ?? 0)}</div>
        <div style="width:8px"></div>
        <button class="btn small ghost op-edit">
          <i class="fa-solid fa-pen"></i> ${ctx.t("op.edit") || "Редактировать"}
        </button>
        <button class="btn small ghost op-del">
          <i class="fa-solid fa-trash"></i> ${ctx.t("op.delete") || "Удалить"}
        </button>
      </div>
    `;

    // edit mode (скрыт)
    const edit = document.createElement("div");
    edit.className = "form-vert hidden";
    edit.innerHTML = `
      <div>
        <label>${ctx.t("op.qty")}</label>
        <input type="number" step="any" inputmode="decimal" class="op-qty" value="${ctx.esc(op.quantity)}" />
      </div>
      <div>
        <label>${ctx.t("op.cost")}</label>
        <input type="number" step="any" inputmode="decimal" class="op-cost" value="${ctx.esc(op.cost)}" />
      </div>
      <div>
        <label>${ctx.t("op.price")}</label>
        <input type="number" step="any" inputmode="decimal" class="op-price" value="${ctx.esc(op.price ?? "")}" />
      </div>
      <div class="page-actions">
        <button class="btn small op-save">${ctx.t("common.save")}</button>
        <button class="btn small ghost op-cancel">${ctx.t("common.cancel")}</button>
      </div>
    `;

    // привязка
    wrap.appendChild(view);
    wrap.appendChild(edit);

    // handlers
    const btnEdit = view.querySelector(".op-edit");
    const btnDel  = view.querySelector(".op-del");
    const btnSave = edit.querySelector(".op-save");
    const btnCancel = edit.querySelector(".op-cancel");

    btnEdit.onclick = () => {
      view.classList.add("hidden");
      edit.classList.remove("hidden");
      edit.querySelector(".op-qty").focus();
    };

    btnCancel.onclick = () => {
      edit.classList.add("hidden");
      view.classList.remove("hidden");
    };

    btnDel.onclick = async () => {
      const q = ctx.t("confirm.delete_op") || "Удалить операцию?";
      if (!confirm(q)) return;
      setBusy(true, [btnEdit, btnDel]);

      try {
        const { ok, data } = await ctx.api("purchase_ops_delete", { items: [{ id: op.id }] });
        const affected = data?.result?.row_affected || 0;
        if (ok && affected > 0) {
          wrap.remove();
          if (!list.children.length) list.innerHTML = $emptyMsg();
          toast(ctx.t("toast.op_deleted") || "Операция удалена");
        } else {
          toast((data?.description || "Не удалось удалить операцию"), true);
        }
      } catch {
        toast("Network error", true);
      } finally {
        setBusy(false, [btnEdit, btnDel]);
      }
    };

    btnSave.onclick = async () => {
      const qty   = ctx.toNumber(edit.querySelector(".op-qty").value);
      const cost  = ctx.toNumber(edit.querySelector(".op-cost").value);
      const price = ctx.toNumber(edit.querySelector(".op-price").value);
      if (!qty || qty <= 0) { alert(ctx.t("op.qty.required")); return; }

      const savingText = ctx.t("op.saving") || "Сохранение...";
      const oldText = btnSave.textContent;
      btnSave.textContent = savingText;
      setBusy(true, [btnSave, btnCancel]);

      try {
        const payload = {
          items: [{
            id: op.id,
            quantity: qty,
            cost: cost,
            // price опционален — не отправляем, если пустой/NaN
            ...(Number.isFinite(price) ? { price } : {})
          }]
        };
        const { ok, data } = await ctx.api("purchase_ops_edit", payload);
        const affected = data?.result?.row_affected || 0;
        if (ok && affected > 0) {
          // обновим локально и перерисуем одну карточку
          op.quantity = qty;
          op.cost = cost;
          if (Number.isFinite(price)) op.price = price; else op.price = undefined;

          // перерисовать view
          view.querySelector(".muted:nth-of-type(1)"); // оставить как есть
          view.querySelector(".meta").children[0].innerHTML = `<strong>${ctx.fmtNum(op.quantity)}</strong> ${ctx.t("unit.pcs") || "шт"}`;
          view.querySelector(".meta").children[2].innerHTML = `${ctx.t("op.cost")}: ${ctx.fmtMoney(op.cost)}`;
          view.querySelector(".meta").children[4].innerHTML = `${ctx.t("op.price")}: ${ctx.fmtMoney(op.price ?? 0)}`;

          edit.classList.add("hidden");
          view.classList.remove("hidden");
          toast(ctx.t("toast.op_updated") || "Операция сохранена");
        } else {
          toast((data?.description || "Не удалось сохранить операцию"), true);
        }
      } catch {
        toast("Network error", true);
      } finally {
        btnSave.textContent = oldText;
        setBusy(false, [btnSave, btnCancel]);
      }
    };

    return wrap;
  }

  function setBusy(b, elements){
    (elements || []).forEach(el => {
      if (!el) return;
      el.disabled = !!b;
    });
  }
}
