// views/op_new.js — без import; получает ctx
let mediaStream = null, scanTimer = null, pickedProduct = null, detector = null;

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");
  pickedProduct = null;

  // --- Заголовок + chevron "назад" к документу ---
  // Ищем заголовок в пределах #app: сначала по известным id, затем первый h1
  const appRoot  = ctx.$("app") || document.body;
  const titleEl =
    appRoot?.querySelector("#op-title, #op-new-title, .page-title, h1") || null;

  if (titleEl) {
    // Обёртка-ряд слева направо
    let wrap = titleEl.closest(".row");
    if (!wrap || !wrap.classList.contains("row-start")) {
      const newWrap = document.createElement("div");
      newWrap.className = "row row-start";
      titleEl.parentNode.insertBefore(newWrap, titleEl);
      newWrap.appendChild(titleEl);
      wrap = newWrap;
    }
    // Кнопка назад (создаём один раз)
    let backChevron = appRoot.querySelector("#btn-op-back");
    if (!backChevron) {
      backChevron = document.createElement("button");
      backChevron.id = "btn-op-back";
      backChevron.className = "btn icon clear"; // без рамки
      const backLabel = ctx.t("nav.back") || ctx.t("doc.to_list") || "Назад";
      backChevron.title = backLabel;
      backChevron.setAttribute("aria-label", backLabel);
      backChevron.innerHTML = `<i class="fa-solid fa-chevron-left"></i>`;
      backChevron.onclick = () => {
        stopScan();                   // закрыть камеру, если открыта
        location.hash = `#/doc/${id}`;
      };
      wrap.insertBefore(backChevron, titleEl);
    }
  }

  // ---- helpers ----
  function setBusy(b) {
    const ids = ["btn-scan","btn-close-scan","product-query","barcode","qty","cost","price","btn-op-save","btn-op-cancel"];
    ids.forEach(k => { const el = ctx.$(k); if (el && "disabled" in el) el.disabled = b; });
    const save = ctx.$("btn-op-save"); if (save) save.textContent = b ? "Сохранение..." : "Сохранить";
  }
  function toast(msg, ok=true) {
    let t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.style.cssText = "position:fixed;left:50%;bottom:16px;transform:translateX(-50%);max-width:92%;padding:10px 14px;border-radius:10px;box-shadow:0 6px 16px rgba(0,0,0,.25);z-index:9999;font-size:14px;font-weight:600";
      document.body.appendChild(t);
    }
    t.textContent = msg || "";
    t.style.background = ok ? "#10b981" : "#ef4444";
    t.style.color = "#fff";
    t.style.display = "block";
    setTimeout(()=>{ t.style.display = "none"; }, 2000);
  }
  function markInvalid(el, on=true){ if (!el) return; el.style.borderColor = on ? "#ef4444" : ""; el.style.boxShadow = on ? "0 0 0 2px rgba(239,68,68,.2)" : ""; }
  function simulateEnter(el){ if (el) el.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true })); }
  const firstBarcode = (p) => p?.base_barcode ?? (p?.barcode_list ? String(p.barcode_list).split(",")[0]?.trim() : "") ?? p?.code ?? "";

  // ---- поиск только по Enter ----
  const runSearch = async (q) => {
    const box = ctx.$("product-results");
    box.textContent = "Поиск...";
    try {
      const { data } = await ctx.api("product_search", { q, doc_id: id });
      const items = data?.result?.items || [];
      if (!items.length) {
        pickedProduct = null;
        ctx.$("product-picked").classList.add("hidden");
        box.textContent = "Ничего не найдено";
        return;
      }
      // Автовыбор первого
      pick(items[0]);
      box.textContent = "";
    } catch {
      box.textContent = "Ошибка поиска";
    }
  };

  ctx.$("barcode").addEventListener("keydown", (e)=>{
    if (e.key === "Enter") { e.preventDefault(); const v = e.target.value.trim(); if (v) runSearch(v); }
  });
  ctx.$("product-query").addEventListener("keydown", (e)=>{
    if (e.key === "Enter") { e.preventDefault(); const v = e.target.value.trim(); if (v) runSearch(v); }
  });

  ctx.$("btn-op-cancel").onclick = ()=>{ stopScan(); location.hash = `#/doc/${id}`; };
  ctx.$("btn-op-save").onclick   = ()=>saveOp(id);

  // Быстрые кнопки количества
  ctx.$("qty-quick").addEventListener("click", (e)=>{
    const btn = e.target.closest("button[data-inc]");
    if (!btn) return;
    const inc = Number(btn.dataset.inc || "0");
    const el = ctx.$("qty");
    const val = ctx.toNumber(el.value) || 0;
    el.value = String(val + inc);
    el.focus();
    el.select?.();
  });

  // Навигация по Enter: qty -> cost -> price -> save
  ctx.$("qty").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("cost").focus(); } });
  ctx.$("cost").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("price").focus(); } });
  ctx.$("price").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); saveOp(id); } });

  // Сканер
  ctx.$("btn-scan").onclick       = startScan;
  ctx.$("btn-close-scan").onclick = stopScan;

  if ("BarcodeDetector" in window) {
    try { detector = new BarcodeDetector({ formats: ["ean_13","ean_8","code_128","upc_a","upc_e","itf"] }); } catch {}
  }

  async function startScan(){
    ctx.$("scanner").classList.remove("hidden");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      mediaStream = stream;
      const video = ctx.$("preview");
      video.srcObject = stream; await video.play().catch(()=>{});
      const detectFrame = async () => {
        if (!mediaStream) return;
        try {
          let okCode = null;
          if (detector) {
            try {
              const res = await detector.detect(video);
              if (res && res[0]) okCode = res[0].rawValue || res[0].displayValue || null;
            } catch {
              try {
                const c = document.createElement("canvas");
                c.width = video.videoWidth || 640; c.height = video.videoHeight || 360;
                const g = c.getContext("2d"); g.drawImage(video, 0, 0, c.width, c.height);
                const res2 = await detector.detect(c);
                if (res2 && res2[0]) okCode = res2[0].rawValue || res2[0].displayValue || null;
              } catch {}
            }
          }
          if (okCode) {
            const pq = ctx.$("product-query"), bc = ctx.$("barcode");
            if (bc) bc.value = okCode;
            if (pq) pq.value = okCode;
            stopScan();
            simulateEnter(pq);
            return;
          }
        } finally {
          scanTimer = requestAnimationFrame(detectFrame);
        }
      };
      scanTimer = requestAnimationFrame(detectFrame);
    } catch {
      toast("Не удалось открыть камеру", false);
      ctx.$("scanner").classList.add("hidden");
      ctx.$("barcode").focus();
    }
  }
  function stopScan(){
    if (scanTimer) { cancelAnimationFrame(scanTimer); scanTimer=null; }
    if (mediaStream) { mediaStream.getTracks().forEach(t=>t.stop()); mediaStream=null; }
    const sc = ctx.$("scanner"); if (sc) sc.classList.add("hidden");
  }

  function pick(p){
    pickedProduct = {
      id: p.id || p.uuid || p.code,
      name: p.name || "—",
      barcode: firstBarcode(p),
      vat_value: p?.vat?.value ?? 0,
      last_purchase_cost: p?.last_purchase_cost   // если бэк вернёт — покажем подсказку
    };
    ctx.$("product-picked").classList.remove("hidden");
    ctx.$("picked-name").textContent = pickedProduct.name;
    ctx.$("picked-code").textContent = pickedProduct.barcode || "";

    // подсказка "последняя закупка"
    const hintBox = ctx.$("cost-suggest");
    hintBox.innerHTML = "";
    const lpc = pickedProduct.last_purchase_cost;
    if (lpc != null) {
      const b = document.createElement("button");
      b.className = "btn secondary";
      b.textContent = `С/с из последней закупки: ${ctx.fmtMoney(lpc)}`;
      b.onclick = () => { ctx.$("cost").value = String(lpc); ctx.$("cost").focus(); ctx.$("cost").select?.(); };
      hintBox.appendChild(b);
    }
    // сразу в qty
    setTimeout(()=>{ ctx.$("qty")?.focus(); }, 0);
  }

  async function saveOp(docId){
    const qtyEl = ctx.$("qty");
    const costEl = ctx.$("cost");
    const qty   = ctx.toNumber(qtyEl.value);
    const cost  = ctx.toNumber(costEl.value);
    const price = ctx.toNumber(ctx.$("price").value);

    markInvalid(qtyEl,false); markInvalid(costEl,false);

    if (!pickedProduct) { toast("Сначала выберите товар", false); return; }
    let hasErr = false;
    if (!qty || qty <= 0) { markInvalid(qtyEl, true); hasErr = true; }
    if (!cost || cost <= 0){ markInvalid(costEl, true); hasErr = true; }
    if (hasErr) { toast("Заполните обязательные поля", false); return; }

    const item = {
      document_id: Number(docId),
      item_id: Number(pickedProduct.id),
      quantity: qty,
      cost: cost,
      vat_value: Number(pickedProduct.vat_value ?? 0),
      ...(price ? { price } : {})
    };

    setBusy(true);
    try {
      const { ok, data } = await ctx.api("purchase_ops_add", { items: [item] });
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        toast("Операция добавлена");
        resetForm();
      } else {
        toast(data?.description || "Не удалось сохранить операцию", false);
      }
    } catch {
      toast("Ошибка сети при сохранении", false);
    } finally {
      setBusy(false);
    }
  }

  function resetForm(){
    ["barcode","product-query","qty","cost","price"].forEach(id=>{
      const el = ctx.$(id); if (el){ el.value = ""; markInvalid(el,false); }
    });
    pickedProduct = null;
    ctx.$("product-picked").classList.add("hidden");
    ctx.$("cost-suggest").innerHTML = "";
    ctx.$("product-results").textContent = "";
    ctx.$("barcode")?.focus();
  }

  // стартовый фокус — на штрих-код
  ctx.$("barcode").focus();
}
