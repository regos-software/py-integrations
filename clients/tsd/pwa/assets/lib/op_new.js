// views/op_new.js — без import; получает ctx
let mediaStream = null, scanTimer = null, pickedProduct = null, detector = null;

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");
  pickedProduct = null;

  // ---- helpers ----
  function setBusy(b) {
    const ids = ["btn-scan","btn-close-scan","product-query","barcode","qty","cost","price","btn-op-save","btn-op-cancel"];
    ids.forEach(k => {
      const el = ctx.$(k);
      if (!el) return;
      if ("disabled" in el) el.disabled = b;
    });
    const save = ctx.$("btn-op-save");
    if (save) save.textContent = b ? "Сохранение..." : "Сохранить";
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
  function markInvalid(el, on=true){
    if (!el) return;
    el.style.borderColor = on ? "#ef4444" : "";
    el.style.boxShadow = on ? "0 0 0 2px rgba(239,68,68,.2)" : "";
  }
  function simulateEnter(el){
    if (!el) return;
    el.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  }
  function firstBarcode(p){
    return p?.base_barcode
      ?? (p?.barcode_list ? String(p.barcode_list).split(",")[0]?.trim() : "")
      ?? p?.code ?? "";
  }

  // ---- wire UI ----
  // Поиск строго по Enter (и в штрих-коде, и в поле поиска)
  ctx.$("barcode").addEventListener("keydown", (e)=>{
    if (e.key === "Enter") {
      e.preventDefault();
      const v = e.target.value.trim();
      if (v) doProductSearch(v);
    }
  });
  ctx.$("product-query").addEventListener("keydown", (e)=>{
    if (e.key === "Enter") {
      e.preventDefault();
      const v = e.target.value.trim();
      if (v) doProductSearch(v);
    }
  });

  ctx.$("btn-op-cancel").onclick = ()=>{ location.hash = `#/doc/${id}`; };
  ctx.$("btn-op-save").onclick   = ()=>saveOp(id);

  // Навигация по Enter: qty -> cost -> price -> Сохранить
  ctx.$("qty").addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); ctx.$("cost").focus(); }
  });
  ctx.$("cost").addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); ctx.$("price").focus(); }
  });
  ctx.$("price").addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); saveOp(id); }
  });

  // Сканер
  ctx.$("btn-scan").onclick       = startScan;
  ctx.$("btn-close-scan").onclick = stopScan;

  if ("BarcodeDetector" in window) {
    try { detector = new BarcodeDetector({ formats: ["ean_13","ean_8","code_128","upc_a","upc_e","itf"] }); } catch {}
  }

  // ---- scan ----
  async function startScan(){
    ctx.$("scanner").classList.remove("hidden");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      mediaStream = stream;
      const video = ctx.$("preview");
      video.srcObject = stream;
      await video.play().catch(()=>{});
      // Стратегия: пытаемся детектить видео напрямую; если упало — через bitmap/canvas
      const detectFrame = async () => {
        if (!mediaStream) return;
        try {
          let okCode = null;
          if (detector) {
            try {
              const res = await detector.detect(video);
              if (res && res[0]) okCode = res[0].rawValue || res[0].displayValue || null;
            } catch {
              // fallback через canvas
              try {
                const c = document.createElement("canvas");
                c.width = video.videoWidth || 640; c.height = video.videoHeight || 360;
                const g = c.getContext("2d");
                g.drawImage(video, 0, 0, c.width, c.height);
                const img = c; // HTMLCanvasElement подходит
                const res2 = await detector.detect(img);
                if (res2 && res2[0]) okCode = res2[0].rawValue || res2[0].displayValue || null;
              } catch {}
            }
          }
          if (okCode) {
            const pq = ctx.$("product-query");
            const bc = ctx.$("barcode");
            if (bc) bc.value = okCode;
            if (pq) pq.value = okCode;
            stopScan();
            simulateEnter(pq); // один поток — одно считывание
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
    ctx.$("scanner").classList.add("hidden");
  }

  // ---- search & pick ----
  async function doProductSearch(q){
    const box = ctx.$("product-results");
    box.innerHTML = `<div class="muted">Поиск...</div>`;
    try {
      const { data } = await ctx.api("product_search", { q, doc_id: id });
      const items = data?.result?.items || [];
      renderResults(items);
      // если один — сразу выбрать
      if (items.length === 1) pick(items[0]);
    } catch {
      box.innerHTML = `<div class="muted">Ошибка поиска</div>`;
    }
  }

  function renderResults(items){
    const box = ctx.$("product-results");
    if (!items.length){ box.innerHTML = `<div class="muted">Ничего не найдено</div>`; return; }
    box.innerHTML = "";
    items.forEach(p=>{
      const el = document.createElement("div");
      el.className = "item";
      const codeOrBarcode = firstBarcode(p);
      el.innerHTML = `
        <div class="row">
          <div>
            <div><strong>${ctx.esc(p.name||"Без наименования")}</strong></div>
            <div class="muted">${ctx.esc(codeOrBarcode||"")}</div>
          </div>
          <button class="btn">Выбрать</button>
        </div>`;
      el.querySelector(".btn").onclick = ()=>pick(p);
      box.appendChild(el);
    });
  }

  function pick(p){
    pickedProduct = {
      id: p.id || p.uuid || p.code,
      name: p.name || "—",
      barcode: firstBarcode(p),
      vat_value: p?.vat?.value ?? 0
    };
    ctx.$("product-picked").classList.remove("hidden");
    ctx.$("picked-name").textContent = pickedProduct.name;
    ctx.$("picked-code").textContent = pickedProduct.barcode || "";
    // для скорости сразу в qty
    setTimeout(()=>{ ctx.$("qty")?.focus(); }, 0);
  }

  // ---- save ----
  async function saveOp(docId){
    // валидация
    const qtyEl = ctx.$("qty");
    const costEl = ctx.$("cost");
    const qty   = ctx.toNumber(qtyEl.value);
    const cost  = ctx.toNumber(costEl.value);
    const price = ctx.toNumber(ctx.$("price").value); // опционально

    // сброс подсветки
    markInvalid(qtyEl, false);
    markInvalid(costEl, false);

    if (!pickedProduct) { toast("Сначала выберите товар", false); return; }
    let hasErr = false;
    if (!qty || qty <= 0) { markInvalid(qtyEl, true); hasErr = true; }
    if (!cost || cost <= 0){ markInvalid(costEl, true); hasErr = true; }
    if (hasErr) { toast("Заполните обязательные поля", false); return; }

    const vat_value = Number(pickedProduct.vat_value ?? 0);
    const item = {
      document_id: Number(docId),
      item_id: Number(pickedProduct.id),
      quantity: qty,
      cost: cost,
      vat_value,
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
        const msg = data?.description || "Не удалось сохранить операцию";
        toast(msg, false);
      }
    } catch {
      toast("Ошибка сети при сохранении", false);
    } finally {
      setBusy(false);
    }
  }

  function resetForm(){
    // очистка инпутов
    ["barcode","product-query","qty","cost","price"].forEach(id=>{
      const el = ctx.$(id);
      if (el) { el.value = ""; markInvalid(el,false); }
    });
    // скрыть выбранный товар
    pickedProduct = null;
    ctx.$("product-picked").classList.add("hidden");
    // очистить результаты поиска
    const box = ctx.$("product-results");
    if (box) box.innerHTML = "";
    // фокус обратно на поле штрих-кода — под новый скан
    ctx.$("barcode")?.focus();
  }

  // Стартовый фокус — на штрих-код
  ctx.$("barcode").focus();
}
