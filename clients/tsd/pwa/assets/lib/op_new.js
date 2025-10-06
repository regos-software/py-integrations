// views/op_new.js — только ZXing (UMD) + поиск ItemExt
let pickedProduct = null;
let zxingReader = null;
let zxingReady = false;
let zxingControls = null;
let currentDeviceId = null;
let docCtx = { price_type_id: null, stock_id: null };

// overlay для рамки ROI
let overlay = null, og = null;

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");

  // ---- helpers ----
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

  const firstBarcodeFromItem = (core) =>
    core?.base_barcode ??
    (core?.barcode_list ? String(core.barcode_list).split(",")[0]?.trim() : "") ??
    core?.code ?? "";

  // ---- overlay (рамка) ----
  function ensureOverlay(video) {
    if (overlay && og) return;
    overlay = document.createElement("canvas");
    overlay.id = "scan-overlay";
    overlay.style.cssText = "position:absolute;inset:0;pointer-events:none;";
    const parent = video.parentElement || video;
    parent.style.position = parent.style.position || "relative";
    parent.appendChild(overlay);
    og = overlay.getContext("2d");
  }
  function drawROI(video) {
    if (!overlay || !og) return;
    const w = video.videoWidth || video.clientWidth || 640;
    const h = video.videoHeight || video.clientHeight || 360;
    overlay.width = w; overlay.height = h;
    og.clearRect(0,0,w,h);

    const rw = Math.round(w * 0.72);
    const rh = Math.round(h * 0.5);
    const rx = Math.round((w - rw) / 2);
    const ry = Math.round((h - rh) / 2);

    // затемняем фон
    og.fillStyle = "rgba(0,0,0,0.35)";
    og.fillRect(0,0,w,ry);
    og.fillRect(0,ry,rx,rh);
    og.fillRect(rx+rw,ry,w-(rx+rw),rh);
    og.fillRect(0,ry+rh,w,h-(ry+rh));

    // белая рамка
    og.lineWidth = 2;
    og.strokeStyle = "#ffffff";
    og.strokeRect(rx, ry, rw, rh);
  }

  // ---- ZXing загрузка и инициализация ----
  async function ensureZXing() {
    if (zxingReady && zxingReader) return true;

    if (!window.ZXing) {
      await new Promise((resolve) => {
        const s = document.createElement("script");
        s.src = "?assets=lib/zxing.min.js";
        s.async = true;
        s.onload = resolve;
        s.onerror = () => { console.error("[ZXing] load failed"); resolve(); };
        document.head.appendChild(s);
      });
    }
    if (!window.ZXing) return false;

    const ZX = window.ZXing;

    // Берём доступный класс: MultiFormat -> Barcode -> QR
    const ReaderClass =
      ZX.BrowserMultiFormatReader ||
      ZX.BrowserBarcodeReader ||
      ZX.BrowserQRCodeReader;

    if (!ReaderClass) {
      console.error("[ZXing] Browser*Reader not found in UMD");
      return false;
    }

    // Хинты: используем нативный Map (НЕ ZX.Map)
    let reader = null;
    try {
      const hints = new Map();
      if (ZX.DecodeHintType && ZX.BarcodeFormat) {
        const formats = [
          ZX.BarcodeFormat.EAN_13,
          ZX.BarcodeFormat.EAN_8,
          ZX.BarcodeFormat.UPC_A,
          ZX.BarcodeFormat.UPC_E,
          ZX.BarcodeFormat.ITF,
          ZX.BarcodeFormat.CODE_128,
          ZX.BarcodeFormat.CODE_39,
          ZX.BarcodeFormat.CODABAR
        ].filter(Boolean);
        hints.set(ZX.DecodeHintType.POSSIBLE_FORMATS, formats);
      }
      // некоторые версии принимают hints в конструкторе, некоторые — через setHints
      try {
        reader = new ReaderClass(hints);
      } catch {
        reader = new ReaderClass();
        if (typeof reader.setHints === "function") reader.setHints(hints);
      }
    } catch {
      reader = new ReaderClass();
    }

    zxingReader = reader;
    zxingReady  = true;
    return true;
  }

  async function listCameras() {
    // разные версии: listVideoInputDevices или getVideoInputDevices
    const listFn = zxingReader.listVideoInputDevices || zxingReader.getVideoInputDevices;
    if (typeof listFn !== "function") return [];
    try {
      const devices = await listFn.call(zxingReader);
      // Унифицируем к [{deviceId,label}]
      return devices.map(d => ({
        deviceId: d.deviceId || d.id || d.deviceId_,
        label: d.label || ""
      })).filter(d => d.deviceId);
    } catch {
      return [];
    }
  }

  async function pickBackCameraId() {
    const cams = await listCameras();
    if (!cams.length) return null;
    const byLabel = cams.find(c => /back|environment|rear/i.test(c.label));
    return (byLabel || cams[0]).deviceId;
  }

  // ---- контекст документа (price_type_id, stock_id) ----
  const docId = Number(id);
  try {
    const { data } = await ctx.api("purchase_get", { doc_id: docId });
    const doc = data?.result?.doc;
    docCtx.price_type_id = doc?.price_type?.id ?? null;
    docCtx.stock_id      = doc?.stock?.id ?? null;
  } catch { /* необязательно */ }

  // ---- поиск только по Enter (ItemExt[]) ----
  const runSearch = async (q) => {
    const box = ctx.$("product-results");
    box.textContent = ctx.t("searching");
    try {
      const payload = { q, doc_id: docId };
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
      pick(items[0]); // авто-выбор
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

  // ---- кнопки сохранить/отмена ----
  if (ctx.$("btn-op-cancel")) ctx.$("btn-op-cancel").textContent = ctx.t("cancel");
  if (ctx.$("btn-op-save"))   ctx.$("btn-op-save").textContent   = ctx.t("save");

  ctx.$("btn-op-cancel").onclick = ()=>{ location.hash = `#/doc/${id}`; };
  ctx.$("btn-op-save").onclick   = ()=>saveOp(id);

  // ---- быстрые кнопки количества ----
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

  // ---- навигация Enter: qty -> cost -> price -> save ----
  ctx.$("qty").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("cost").focus(); } });
  ctx.$("cost").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("price").focus(); } });
  ctx.$("price").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); saveOp(id); } });

  // ---- кнопки камеры (иконки) ----
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

  btnScan.onclick       = startScan;
  btnClose.onclick      = stopScan;
  document.addEventListener("visibilitychange", () => { if (document.hidden) stopScan(); });
  window.addEventListener("pagehide", stopScan);

  async function startScan() {
    // HTTPS обязателен (кроме localhost)
    const insecure = location.protocol !== "https:" && location.hostname !== "localhost";
    if (insecure) { toast(ctx.t("camera_open_failed"), false); return; }

    // загрузим ZXing
    const ok = await ensureZXing();
    if (!ok) { toast("Не удалось загрузить модуль сканера", false); return; }

    const video = ctx.$("preview");
    const scanner = ctx.$("scanner");
    if (!video || !scanner) { toast(ctx.t("camera_open_failed"), false); return; }

    scanner.classList.remove("hidden");
    try { video.setAttribute("playsinline",""); video.setAttribute("webkit-playsinline",""); video.autoplay = true; video.muted = true; } catch {}

    ensureOverlay(video);

    // выбираем тыловую камеру, если получится
    if (!currentDeviceId) currentDeviceId = await pickBackCameraId();

    // Нормализуем вызов «непрерывного» декодирования в разных версиях библиотеки
    const startContinuous = async (deviceId, elId, onCode, onError) => {
      // текущие версии:
      if (typeof zxingReader.decodeFromVideoDevice === "function") {
        return zxingReader.decodeFromVideoDevice(deviceId, elId, async (result, err, controls) => {
          try { drawROI(video); } catch {}
          if (result && result.text) onCode(result.text, controls);
          else if (err && !(err && err.name === "NotFoundException")) onError?.(err);
        });
      }
      // более старые:
      if (typeof zxingReader.decodeFromInputVideoDevice === "function") {
        return zxingReader.decodeFromInputVideoDevice(deviceId, elId, async (result, err, controls) => {
          try { drawROI(video); } catch {}
          if (result && result.text) onCode(result.text, controls);
          else if (err && !(err && err.name === "NotFoundException")) onError?.(err);
        });
      }
      // fallback: один раз (без непрерывного)
      if (typeof zxingReader.decodeOnceFromVideoDevice === "function") {
        const res = await zxingReader.decodeOnceFromVideoDevice(deviceId, elId);
        onCode(res?.text || "", { stop: () => zxingReader.reset?.() });
        return { stop: () => zxingReader.reset?.() };
      }
      throw new Error("No suitable decode method");
    };

    try {
      // старт
      zxingControls = await startContinuous(currentDeviceId ?? undefined, "preview",
        (code, controls) => {
          // нашли код
          try { navigator.vibrate?.(40); } catch {}
          const pq = ctx.$("product-query"), bc = ctx.$("barcode");
          if (bc) bc.value = code;
          if (pq) pq.value = code;
          stopScan();           // остановим, чтобы не повторялось
          simulateEnter(pq);    // триггерим поиск
        },
        (err) => {
          // консоль для диагностики, но не мешаем UI
          console.debug("[ZXing] scan err:", err?.name || err);
        }
      );

      // включим фонарик, если доступен
      try {
        const ms = video.srcObject;
        const track = ms && ms.getVideoTracks && ms.getVideoTracks()[0];
        const caps = track?.getCapabilities?.() || {};
        if (caps.torch) {
          await track.applyConstraints({ advanced: [{ torch: true }] }).catch(()=>{});
        }
      } catch {}
    } catch (e) {
      console.error("[ZXing] start error:", e);
      stopScan();
      toast(ctx.t("camera_open_failed"), false);
    }
  }

  function stopScan() {
    try { zxingControls?.stop?.(); } catch {}
    try { zxingReader?.reset?.(); } catch {}
    zxingControls = null;

    const video = ctx.$("preview");
    if (video) {
      try { video.pause?.(); } catch {}
      try { video.srcObject = null; } catch {}
    }
    const scanner = ctx.$("scanner");
    if (scanner) scanner.classList.add("hidden");
    if (og && overlay) { og.clearRect(0,0,overlay.width,overlay.height); }
  }

  // ====== принимаем ТОЛЬКО ItemExt ======
  function pick(ext){
    const core = ext?.item || {};
    pickedProduct = {
      id: Number(core.id ?? core.code),
      name: core.name || "—",
      barcode: firstBarcodeFromItem(core),
      vat_value: Number(core?.vat?.value ?? 0),
      last_purchase_cost: ext?.last_purchase_cost ?? null,
      price: ext?.price != null ? Number(ext.price) : null,
      quantity_common: ext?.quantity?.common ?? null,
      image_url: ext?.image_url || core?.image_url || null
    };

    ctx.$("product-picked").classList.remove("hidden");
    ctx.$("picked-name").textContent = pickedProduct.name;
    ctx.$("picked-code").textContent = pickedProduct.barcode || "";

    // подсказки: последняя закупка + цена продажи (если есть)
    const hintBox = ctx.$("cost-suggest");
    hintBox.innerHTML = "";
    const lpc = pickedProduct.last_purchase_cost;
    if (lpc != null) {
      const b = document.createElement("button");
      b.className = "btn secondary";
      b.textContent = ctx.t("last_purchase_cost_hint", { cost: ctx.fmtMoney(lpc) });
      b.onclick = () => {
        ctx.$("cost").value = String(lpc);
        ctx.$("cost").focus();
        ctx.$("cost").select?.();
      };
      hintBox.appendChild(b);
    }
    if (pickedProduct.price != null) {
      const b2 = document.createElement("button");
      b2.className = "btn ghost";
      b2.textContent = `${ctx.t("op.price")}: ${ctx.fmtMoney(pickedProduct.price)}`;
      b2.onclick = () => {
        ctx.$("price").value = String(pickedProduct.price);
        ctx.$("price").focus();
        ctx.$("price").select?.();
      };
      hintBox.appendChild(b2);
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

    if (!pickedProduct || pickedProduct.id == null || Number.isNaN(Number(pickedProduct.id))) {
      toast(ctx.t("select_product_first"), false); return;
    }

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
