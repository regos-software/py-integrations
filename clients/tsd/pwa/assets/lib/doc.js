// lib/doc.js — без import; получает ctx
export async function screenDoc(ctx, id) {
  await ctx.loadView("doc");

  // локализация кнопок/подписей
  const $spinnerMsg = () => `<div class="muted">${ctx.t("common.loading")}</div>`;
  const $emptyMsg   = () => `<div class="muted">${ctx.t("doc.no_ops") || ctx.t("common.nothing")}</div>`;

  // кнопки действия (старую кнопку "к списку" прячем — используем chevron возле заголовка)
  const oldBackBtn = ctx.$("btn-back-docs");
  if (oldBackBtn) oldBackBtn.classList.add("hidden");
  const addOpBtn = ctx.$("btn-add-op");
  if (addOpBtn) {
    addOpBtn.textContent = ctx.t("doc.add_op");
    addOpBtn.onclick = () => { location.hash = `#/doc/${id}/op/new`; };
  }

  // шапка документа: заголовок + chevron "назад к списку" слева от него
  const titleEl = ctx.$("doc-title");
  if (titleEl) {
    // обёртка вокруг заголовка (ставим row row-start, чтобы элементы шли слева направо)
    let wrap = titleEl.closest(".row");
    if (!wrap || !wrap.classList.contains("row-start")) {
      const newWrap = document.createElement("div");
      newWrap.className = "row row-start";
      titleEl.parentNode.insertBefore(newWrap, titleEl);
      newWrap.appendChild(titleEl);
      wrap = newWrap;
    }
    // создаём chevron один раз
    let backChevron = ctx.$("btn-doc-back");
    if (!backChevron) {
      backChevron = document.createElement("button");
      backChevron.id = "btn-doc-back";
      backChevron.className = "btn icon clear"; // без рамки
      const backLabel = ctx.t("doc.to_list") || ctx.t("nav.back") || "Назад";
      backChevron.title = backLabel;
      backChevron.setAttribute("aria-label", backLabel);
      backChevron.innerHTML = `<i class="fa-solid fa-chevron-left"></i>`;
      backChevron.onclick = () => { location.hash = "#/docs"; };
      wrap.insertBefore(backChevron, titleEl);
    }
  }

  // спиннер
  const list = ctx.$("ops-list");
  list.innerHTML = $spinnerMsg();

  // документ + операции
  const { data } = await ctx.api("purchase_get", { doc_id: id });
  const doc = data?.result?.doc || {};
  let ops   = data?.result?.operations;

  if (!Array.isArray(ops)) {
    const r2 = await ctx.api("purchase_ops_get", { doc_id: id });
    ops = r2?.data?.result?.items || [];
  }

  // шапка документа — тексты
  if (titleEl) titleEl.textContent = `${ctx.t("doc.title_prefix") || "Документ"} ${doc.code || id}`;
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
    const code = (item.code ?? "").toString().padStart(6, "0"); // лидирующие нули

    const wrap = document.createElement("div");
    wrap.className = "item compact";

    // view mode (две строки: верх — имя + справа иконки; под ним — код+штрихкод; ещё ниже — количество и цены)
    const view = document.createElement("div");
    view.innerHTML = `
      <div class="row compact top">
        <div class="info">
          <strong class="name">${ctx.esc(item.name || "")}</strong>
          <div class="sub">
            <span class="muted text-small code">${ctx.esc(code)}</span>
            <span class="dot"></span>
            <span class="muted text-small barcode">${ctx.esc(barcode || "")}</span>
          </div>
        </div>
        <div class="op-actions">
          <button class="btn icon small ghost op-edit"
                  aria-label="${ctx.t("op.edit") || "Редактировать"}"
                  title="${ctx.t("op.edit") || "Редактировать"}">
            <i class="fa-solid fa-pen"></i>
          </button>
          <button class="btn icon small ghost op-del"
                  aria-label="${ctx.t("op.delete") || "Удалить"}"
                  title="${ctx.t("op.delete") || "Удалить"}">
            <i class="fa-solid fa-trash"></i>
          </button>
        </div>
      </div>

      <div class="meta compact bottom">
        <span class="qty"><strong>${ctx.fmtNum(op.quantity)}</strong> ${ctx.t("unit.pcs") || "шт"}</span>
        <span class="dot"></span>
        <span class="cost">${ctx.fmtMoney(op.cost)}</span>
        <span class="dot"></span>
        <span class="price">${ctx.fmtMoney(op.price ?? 0)}</span>
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
          // обновим локально и перерисуем видимые фрагменты
          op.quantity = qty;
          op.cost = cost;
          if (Number.isFinite(price)) op.price = price; else op.price = undefined;

          // точечно обновляем нижнюю строку (кол-во и цены)
          const metaEl = wrap.querySelector(".meta.bottom");
          metaEl.querySelector(".qty").innerHTML   = `<strong>${ctx.fmtNum(op.quantity)}</strong> ${ctx.t("unit.pcs") || "шт"}`;
          metaEl.querySelector(".cost").textContent  = ctx.fmtMoney(op.cost);
          metaEl.querySelector(".price").textContent = ctx.fmtMoney(op.price ?? 0);

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

