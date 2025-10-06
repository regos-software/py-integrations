// views/op_new.js — без import; получает ctx
let mediaStream = null;
let scanTimer = null;
let detector = null;
let pickedProduct = null;
let currentDeviceId = null;
let docCtx = { price_type_id: null, stock_id: null };

// ZXing fallback
let zxingReader = null;
let zxingReady = false;
let zxingBusy = false;

// overlay для подсветки зоны сканирования и боксов
let overlay = null, og = null; // canvas + 2D context

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");

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
  function firstBarcodeFromItem(item){
    return item?.base_barcode ??
      (item?.barcode_list ? String(item.barcode_list).split(",")[0]?.trim() : "") ??
      item?.code ?? "";
  }

  // overlay helpers
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
  function layoutOverlay(video) {
    const w = video.videoWidth || video.clientWidth || 640;
    const h = video.videoHeight || video.clientHeight || 360;
    overlay.width = w;
    overlay.height = h;
  }
  function roiRect(video) {
    const w = video.videoWidth || 640, h = video.videoHeight || 360;
    const rw = Math.round(w * 0.7);
    const rh = Math.round(h * 0.5);
    const rx = Math.round((w - rw) / 2);
    const ry = Math.round((h - rh) / 2);
    return { rx, ry, rw, rh, w, h };
  }
  function drawROIandBoxes(video, boxes=[]) {
    if (!overlay || !og) return;
    layoutOverlay(video);
    og.clearRect(0,0,overlay.width,overlay.height);

    const { rx, ry, rw, rh } = roiRect(video);

    // затемняем остальной фон
    og.fillStyle = "rgba(0,0,0,0.35)";
    og.fillRect(0,0,overlay.width,ry);
    og.fillRect(0,ry,rx,rh);
    og.fillRect(rx+rw,ry,overlay.width-(rx+rw),rh);
    og.fillRect(0,ry+rh,overlay.width,overlay.height-(ry+rh));

    // рамка ROI
    og.lineWidth = 2;
    og.strokeStyle = "#ffffff";
    og.strokeRect(rx, ry, rw, rh);

    // найденные боксы
    og.strokeStyle = "#00e676";
    og.lineWidth = 3;
    for (const b of boxes) {
      const bb = b?.boundingBox;
      const cp = b?.cornerPoints;
      if (bb && typeof bb.x === "number") {
        og.strokeRect(bb.x + rx, bb.y + ry, bb.width, bb.height);
      } else if (Array.isArray(cp) && cp.length) {
        og.beginPath();
        og.moveTo(cp[0].x + rx, cp[0].y + ry);
        for (let i=1; i<cp.length; i++) og.lineTo(cp[i].x + rx, cp[i].y + ry);
        og.closePath();
        og.stroke();
      }
    }
  }

  // ZXing loader + reader
  async function ensureZXing() {
    if (zxingReady && zxingReader) return true;
    // грузим UMD-скрипт из ассетов
    if (!window.ZXing) {
      await new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = "?assets=lib/zxing.min.js";
        s.async = true;
        s.onload = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
      }).catch(()=>{});
    }
    if (!window.ZXing) return false;

    try {
      const ZX = window.ZXing;
      zxingReader = new ZX.BrowserMultiFormatReader();

      // Подскажем нужные форматы (ускоряет)
      const hints = new ZX.Map();
      const formats = [
        ZX.BarcodeFormat.EAN_13,
        ZX.BarcodeFormat.EAN_8,
        ZX.BarcodeFormat.UPC_A,
        ZX.BarcodeFormat.UPC_E,
        ZX.BarcodeFormat.ITF,
        ZX.BarcodeFormat.CODE_128,
        ZX.BarcodeFormat.CODE_39,
        ZX.BarcodeFormat.CODABAR
      ];
      hints.set(ZX.DecodeHintType.POSSIBLE_FORMATS, formats);
      zxingReader.setHints(hints);
      zxingReady = true;
      return true;
    } catch {
      return false;
    }
  }

  async function decodeWithZXing(canvas) {
    if (!zxingReady || zxingBusy) return null;
    zxingBusy = true;
    try {
      const res = await zxingReader.decodeFromCanvas(canvas).catch(()=>null);
      return res?.text || null;
    } finally {
      zxingBusy = false;
    }
  }

  // ==== подтянем контекст документа ====
  const idNum = Number(id);
  try {
    const { data } = await ctx.api("purchase_get", { doc_id: idNum });
    const doc = data?.result?.doc;
    docCtx.price_type_id = doc?.price_type?.id ?? null;
    docCtx.stock_id      = doc?.stock?.id ?? null;
  } catch { /* не критично */ }

  // ==== поиск по Enter (возвращает только ItemExt) ====
  const runSearch = async (q) => {
    const box = ctx.$("product-results");
    box.textContent = ctx.t("searching");
    try {
      const payload = { q, doc_id: idNum };
      if (docCtx.price_type_id != null) payload.price_type_id = Number(docCtx.price_type_id);
      if (docCtx.stock_id != null)      payload.stock_id      = Number(docCtx.stock_id);

      const { data } = await ctx.api("product_search", payload);
      const items = data?.result?.items || [];   // ItemExt[]
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

  // BarcodeDetector (если доступен) — расширенный список форматов
  if ("BarcodeDetector" in window) {
    try {
      const FORMATS = ["ean_13","ean_8","upc_a","upc_e","itf","code_128","code_39","codabar","qr_code"];
      detector = new BarcodeDetector({ formats: FORMATS });
    } catch {}
  }

  // авто-стоп при сворачивании/уходе
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
    const insecure = location.protocol !== "https:" && location.hostname !== "localhost";
    if (insecure) { toast(ctx.t("camera_open_failed"), false); return; }

    stopScan();
    const scanner = ctx.$("scanner");
    scanner?.classList.remove("hidden");

    const video = ctx.$("preview");
    if (!video) { toast(ctx.t("camera_open_failed"), false); return; }

    try { video.setAttribute("playsinline",""); video.setAttribute("webkit-playsinline",""); video.autoplay = true; video.muted = true; } catch {}

    // 1) пробуем FullHD с environment
    const primaryConstraints = {
      video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
      audio: false
    };

    try {
      let stream = await navigator.mediaDevices.getUserMedia(primaryConstraints).catch(()=>null);
      // 2) fallback: тыловая камера по deviceId
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

      ensureOverlay(video);

      // дождёмся валидных размеров видео
      let guard = 0;
      while ((video.videoWidth|0) < 160 && guard++ < 50) {
        await new Promise(r => setTimeout(r, 50));
      }

      // попытка включить фонарик (если доступен)
      try {
        const [track] = stream.getVideoTracks();
        const caps = track?.getCapabilities?.() || {};
        if (caps.torch) {
          await track.applyConstraints({ advanced: [{ torch: true }] }).catch(()=>{});
        }
      } catch {}

      // канвас для ROI
      const work = document.createElement("canvas");
      const wg = work.getContext("2d", { willReadFrequently: true });

      const detectFrame = async () => {
        if (!mediaStream) return;

        const { rx, ry, rw, rh } = roiRect(video);
        work.width = rw; work.height = rh;
        wg.imageSmoothingEnabled = false;
        // усилим картинку
        wg.filter = "contrast(140%) brightness(115%)";
        wg.drawImage(video, rx, ry, rw, rh, 0, 0, rw, rh);

        let code = null;
        let boxes = [];

        // 1) Нативный детектор
        if (detector) {
          try {
            const result = await detector.detect(work);
            boxes = result || [];
            if (result && result[0]) code = result[0].rawValue || result[0].displayValue || null;
          } catch {}
          // Поворот ROI на 90°
          if (!code) {
            const rot = document.createElement("canvas");
            rot.width = rh; rot.height = rw;
            const rg = rot.getContext("2d");
            rg.translate(rot.width/2, rot.height/2);
            rg.rotate(Math.PI/2);
            rg.drawImage(work, -work.width/2, -work.height/2);
            try {
              const result2 = await detector.detect(rot);
              boxes = result2 || boxes;
              if (result2 && result2[0]) code = result2[0].rawValue || result2[0].displayValue || null;
            } catch {}
          }
        }

        // 2) ZXing fallback
        if (!code) {
          if (!zxingReady) await ensureZXing();
          if (zxingReady) {
            code = await decodeWithZXing(work);
            if (!code) {
              // Попробуем повернуть ROI
              const rot = document.createElement("canvas");
              rot.width = rh; rot.height = rw;
              const rg = rot.getContext("2d");
              rg.translate(rot.width/2, rot.height/2);
              rg.rotate(Math.PI/2);
              rg.drawImage(work, -work.width/2, -work.height/2);
              code = await decodeWithZXing(rot);
            }
          }
        }

        drawROIandBoxes(video, boxes);

        if (code) {
          const pq = ctx.$("product-query"), bc = ctx.$("barcode");
          if (bc) bc.value = code;
          if (pq) pq.value = code;
          try { navigator.vibrate?.(40); } catch {}
          stopScan();
          simulateEnter(pq);
          return;
        }

        scanTimer = setTimeout(() => requestAnimationFrame(detectFrame), 90);
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
    if (og && overlay) { og.clearRect(0,0,overlay.width,overlay.height); }
  }
  function safeStopScan(){ try { stopScan(); } catch {} }

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
