// views/op_new.js — без import; получает ctx
let mediaStream = null;
let scanTimer = null;
let detector = null;
let pickedProduct = null;
let currentDeviceId = null;
let docCtx = { price_type_id: null, stock_id: null };

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");

  // Чистим предыдущее состояние сканера (если вернулись на экран повторно)
  safeStopScan();

  pickedProduct = null;
  docCtx = { price_type_id: null, stock_id: null };

  // ==== helpers ====
  function setBusy(b) {
    const ids = ["btn-scan","btn-close-scan","product-query","barcode","qty","cost","price","btn-op-save","btn-op-cancel"];
    ids.forEach(k => { const el = ctx.$(k); if (el && "disabled" in el) el.disabled = b; });
    const save = ctx.$("btn-op-save");
    if (save) save.textContent = b ? ctx.t("saving") : ctx.t("save");
  }
  function toast(msg, ok = true) {
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
    setTimeout(() => { t.style.display = "none"; }, 2000);
  }
  function markInvalid(el, on = true) {
    if (!el) return;
    el.style.borderColor = on ? "#ef4444" : "";
    el.style.boxShadow   = on ? "0 0 0 2px rgba(239,68,68,.2)" : "";
  }
  function simulateEnter(el){ if (el) el.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true })); }
  const firstBarcode = (p) =>
    p?.base_barcode ??
    (p?.barcode_list ? String(p.barcode_list).split(",")[0]?.trim() : "") ??
    p?.code ?? "";

  // ==== подтянем контекст документа ====
  const idNum = Number(id);
  try {
    const { data } = await ctx.api("purchase_get", { doc_id: idNum });
    const doc = data?.result?.doc;
    docCtx.price_type_id = doc?.price_type?.id ?? null;
    docCtx.stock_id      = doc?.stock?.id ?? null;
  } catch {
    // не критично: поиск просто пойдет без контекстных параметров
  }

  // ==== поиск по Enter ====
  const runSearch = async (q) => {
    const box = ctx.$("product-results");
    box.textContent = ctx.t("searching");
    try {
      const payload = { q, doc_id: idNum };
      if (docCtx.price_type_id != null) payload.price_type_id = Number(docCtx.price_type_id);
      if (docCtx.stock_id != null)      payload.stock_id      = Number(docCtx.stock_id);

      const { data } = await ctx.api("product_search", payload);
      const items = data?.result?.items || [];
      if (!items.length) {
        pickedProduct = null;
        ctx.$("product-picked").classList.add("hidden");
        box.textContent = ctx.t("nothing_found");
        return;
      }
      // Автовыбор первого
      pick(items[0]);
      box.textContent = "";
    } catch {
      box.textContent = ctx.t("search_error");
    }
  };

  ctx.$("barcode").addEventListener("keydown", (e)=>{
    if (e.key === "Enter") { e.preventDefault(); const v = e.target.value.trim(); if (v) runSearch(v); }
  });
  ctx.$("product-query").addEventListener("keydown", (e)=>{
    if (e.key === "Enter") { e.preventDefault(); const v = e.target.value.trim(); if (v) runSearch(v); }
  });

  // ==== кнопки сохранить/отмена ====
  if (ctx.$("btn-op-cancel")) ctx.$("btn-op-cancel").textContent = ctx.t("cancel");
  if (ctx.$("btn-op-save"))   ctx.$("btn-op-save").textContent   = ctx.t("save");

  ctx.$("btn-op-cancel").onclick = ()=>{ location.hash = `#/doc/${id}`; };
  ctx.$("btn-op-save").onclick   = ()=>saveOp(id);

  // ==== быстрые кнопки количества ====
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

  // ==== навигация Enter: qty -> cost -> price -> save ====
  ctx.$("qty").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("cost").focus(); } });
  ctx.$("cost").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("price").focus(); } });
  ctx.$("price").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); saveOp(id); } });

  // ==== Сканер: иконки на кнопках ====
  const btnScan = ctx.$("btn-scan");
  if (btnScan) {
    btnScan.classList.add("btn","icon");
    btnScan.innerHTML = `<i class="fa-solid fa-camera"></i><span class="sr-only">${ctx.esc(ctx.t("op.scan"))}</span>`;
  }
  const btnClose = ctx.$("btn-close-scan");
  if (btnClose) {
    btnClose.classList.add("btn","icon");
    btnClose.innerHTML = `<i class="fa-solid fa-xmark"></i><span class="sr-only">${ctx.esc(ctx.t("cancel"))}</span>`;
  }

  ctx.$("btn-scan").onclick       = startScan;
  ctx.$("btn-close-scan").onclick = stopScan;

  // BarcodeDetector (если доступен)
  if ("BarcodeDetector" in window) {
    try { detector = new BarcodeDetector({ formats: ["ean_13","ean_8","code_128","upc_a","upc_e","itf"] }); } catch {}
  }

  // Авто-стоп при сворачивании/уходе
  document.addEventListener("visibilitychange", () => { if (document.hidden) stopScan(); });
  window.addEventListener("pagehide", stopScan);

  async function pickBackCamera() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cams = devices.filter(d => d.kind === "videoinput");
      const byLabel = cams.find(c => /back|environment/i.test(c.label));
      return (byLabel || cams[0] || null)?.deviceId || null;
    } catch { return null; }
  }

  async function startScan(){
    // Требуется HTTPS (кроме localhost)
    const insecure = location.protocol !== "https:" && location.hostname !== "localhost";
    if (insecure) { toast(ctx.t("camera_open_failed"), false); return; }

    stopScan(); // закрыть предыдущее
    const scanner = ctx.$("scanner");
    if (scanner) scanner.classList.remove("hidden");

    const video = ctx.$("preview");
    if (!video) { toast(ctx.t("camera_open_failed"), false); return; }

    try {
      // атрибуты для iOS Safari
      video.setAttribute("playsinline", "");
      video.setAttribute("webkit-playsinline", "");
      video.autoplay = true;
      video.muted = true;
    } catch {}

    try {
      // 1) с facingMode: environment или сохранённым deviceId
      const primaryConstraints = {
        video: currentDeviceId
          ? { deviceId: { exact: currentDeviceId } }
          : { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      };

      let stream = await navigator.mediaDevices.getUserMedia(primaryConstraints).catch(()=>null);

      // 2) если не удалось — после разрешения выберем тыловую камеру по deviceId
      if (!stream) {
        const backId = await pickBackCamera();
        if (backId) {
          stream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: backId } }, audio: false }).catch(()=>null);
          if (stream) currentDeviceId = backId;
        }
      }

      if (!stream) throw new Error("no-stream");

      mediaStream = stream;
      video.srcObject = stream;
      await video.play().catch(()=>{});

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
          // троттлинг детекции (~12 FPS)
          scanTimer = setTimeout(() => requestAnimationFrame(detectFrame), 80);
        }
      };
      requestAnimationFrame(detectFrame);
    } catch {
      stopScan();
      toast(ctx.t("camera_open_failed"), false);
      ctx.$("barcode").focus();
    }
  }

  function stopScan(){
    if (scanTimer) { clearTimeout(scanTimer); scanTimer = null; }
    if (mediaStream) {
      try { mediaStream.getTracks().forEach(t=>t.stop()); } catch {}
      mediaStream = null;
    }
    const video = ctx.$("preview");
    if (video) {
      try { video.pause?.(); } catch {}
      try { video.srcObject = null; } catch {}
    }
    const scanner = ctx.$("scanner");
    if (scanner) scanner.classList.add("hidden");
  }
  function safeStopScan(){ try { stopScan(); } catch {} }

  function pick(p){
    pickedProduct = {
      id: p.id || p.uuid || p.code,
      name: p.name || "—",
      barcode: firstBarcode(p),
      vat_value: p?.vat?.value ?? 0,
      last_purchase_cost: p?.last_purchase_cost
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
      b.textContent = ctx.t("last_purchase_cost_hint", { cost: ctx.fmtMoney(lpc) });
      b.onclick = () => { ctx.$("cost").value = String(lpc); ctx.$("cost").focus(); ctx.$("cost").select?.(); };
      hintBox.appendChild(b);
    }
    // сразу фокус в qty
    setTimeout(()=>{ ctx.$("qty")?.focus(); }, 0);
  }

  async function saveOp(docId){
    const qtyEl = ctx.$("qty");
    const costEl = ctx.$("cost");
    const qty   = ctx.toNumber(qtyEl.value);
    const cost  = ctx.toNumber(costEl.value);
    const price = ctx.toNumber(ctx.$("price").value);

    markInvalid(qtyEl,false); markInvalid(costEl,false);

    if (!pickedProduct) { toast(ctx.t("select_product_first"), false); return; }
    let hasErr = false;
    if (!qty || qty <= 0) { markInvalid(qtyEl, true); hasErr = true; }
    if (!cost || cost <= 0){ markInvalid(costEl, true); hasErr = true; }
    if (hasErr) { toast(ctx.t("fill_required_fields"), false); return; }

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
        toast(ctx.t("op_added"));
        resetForm();
      } else {
        toast(data?.description || ctx.t("save_failed"), false);
      }
    } catch {
      toast(ctx.t("network_error_save"), false);
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
