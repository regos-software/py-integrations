// views/op_new.js — ZXing (UMD) + поиск ItemExt, иконки-кнопки + корректный overlay

let zxingReader = null;
let zxingControls = null;
let currentDeviceId = null;
let pickedProduct = null;
const docCtx = { price_type_id: null, stock_id: null };

// ==== helpers ====
const once = (fn) => { let done=false; return async (...a)=>{ if(done) return; done=true; return fn(...a); }; };

function toast(msg, ok = true) {
  let t = document.getElementById("toast");
  if (!t) {
    t = document.createElement("div");
    t.id = "toast";
    t.style.cssText = "position:fixed;left:50%;bottom:16px;transform:translateX(-50%);max-width:92%;padding:10px 14px;border-radius:10px;box-shadow:0 6px 16px rgba(0,0,0,.25);z-index:9999;font-size:14px;font-weight:600;color:#fff";
    document.body.appendChild(t);
  }
  t.textContent = msg || "";
  t.style.background = ok ? "#10b981" : "#ef4444";
  t.style.display = "block";
  setTimeout(() => { t.style.display = "none"; }, 1800);
}
function markInvalid(el, on = true) {
  if (!el) return;
  el.style.borderColor = on ? "#ef4444" : "";
  el.style.boxShadow = on ? "0 0 0 2px rgba(239,68,68,.2)" : "";
}
function setBusy(ctx, busy) {
  const ids = ["btn-scan","btn-close-scan","product-query","barcode","qty","cost","price","btn-op-save","btn-op-cancel"];
  ids.forEach(k => { const el = ctx.$(k); if (el && "disabled" in el) el.disabled = busy; });
  const save = ctx.$("btn-op-save");
  if (save) save.textContent = busy ? ctx.t("saving") : ctx.t("save");
}
const firstBarcodeFromItem = (core) =>
  core?.base_barcode ??
  (core?.barcode_list ? String(core.barcode_list).split(",")[0]?.trim() : "") ??
  core?.code ?? "";

// ==== overlay (ROI) ====
let overlay = null, og = null, overlayObserver = null;

function ensureOverlay(video) {
  if (overlay && og) return;

  const parent = video.parentElement || video;
  if (getComputedStyle(parent).position === "static") parent.style.position = "relative";
  parent.style.overflow = "hidden"; // важное: обрезаем, чтобы overlay не вылезал
  // создаём canvas поверх видео
  overlay = document.createElement("canvas");
  overlay.id = "scan-overlay";
  overlay.style.cssText = "position:absolute;inset:0;pointer-events:none;z-index:2;";
  // если у видео скругления — повторим их на оверлее
  try { overlay.style.borderRadius = getComputedStyle(video).borderRadius; } catch {}
  parent.appendChild(overlay);
  og = overlay.getContext("2d");

  // следим за изменением размеров видимой области видео
  overlayObserver = new ResizeObserver(() => layoutOverlay(video, true));
  overlayObserver.observe(parent);
  overlayObserver.observe(video);
}

function layoutOverlay(video, redraw = false) {
  if (!overlay || !og) return;
  const rect = video.getBoundingClientRect();
  const dpr = Math.max(1, window.devicePixelRatio || 1);

  // синхронизируем CSS-размер (визуальный) и пиксельный размер canvas
  overlay.style.width = rect.width + "px";
  overlay.style.height = rect.height + "px";
  const pxW = Math.max(1, Math.floor(rect.width * dpr));
  const pxH = Math.max(1, Math.floor(rect.height * dpr));
  if (overlay.width !== pxW || overlay.height !== pxH) {
    overlay.width = pxW;
    overlay.height = pxH;
  }
  if (redraw) drawROI(video);
}

function drawROI(video) {
  if (!overlay || !og) return;

  // берём размеры canvas (они уже учитывают DPR)
  const w = overlay.width;
  const h = overlay.height;

  og.clearRect(0, 0, w, h);

  // прямоугольник интереса: под штрих-код (шире, чем выше)
  const rw = Math.round(w * 0.78);
  const rh = Math.round(h * 0.46);
  const rx = Math.round((w - rw) / 2);
  const ry = Math.round((h - rh) / 2);

  // тень по краям
  og.fillStyle = "rgba(0,0,0,0.35)";
  og.fillRect(0,0,w,ry);
  og.fillRect(0,ry,rx,rh);
  og.fillRect(rx+rw,ry,w-(rx+rw),rh);
  og.fillRect(0,ry+rh,w,h-(ry+rh));

  // белая рамка
  og.lineWidth = 2 * Math.max(1, window.devicePixelRatio || 1);
  og.strokeStyle = "#ffffff";
  og.strokeRect(rx, ry, rw, rh);

  // лёгкие скругления углов
  try {
    const r = 10 * Math.max(1, window.devicePixelRatio || 1);
    og.lineJoin = "round";
    og.lineCap = "round";
    og.beginPath();
    roundedRect(og, rx, ry, rw, rh, r);
    og.stroke();
  } catch {}
}
function roundedRect(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w/2, h/2);
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

// ==== ZXing ====
const loadZXing = once(async () => {
  if (window.ZXing?.BrowserMultiFormatReader) return true;
  await new Promise((resolve) => {
    const s = document.createElement("script");
    s.src = "?assets=lib/zxing.min.js";
    s.async = true;
    s.onload = resolve;
    s.onerror = resolve;
    document.head.appendChild(s);
  });
  return !!window.ZXing?.BrowserMultiFormatReader;
});
async function ensureZXingReader() {
  if (zxingReader) return zxingReader;
  const ok = await loadZXing();
  if (!ok) throw new Error("ZXing UMD не загрузился");
  const ZX = window.ZXing;
  const hints = new Map();
  if (ZX.DecodeHintType && ZX.BarcodeFormat) {
    hints.set(
      ZX.DecodeHintType.POSSIBLE_FORMATS,
      [
        ZX.BarcodeFormat.EAN_13,
        ZX.BarcodeFormat.EAN_8,
        ZX.BarcodeFormat.UPC_A,
        ZX.BarcodeFormat.UPC_E,
        ZX.BarcodeFormat.ITF,
        ZX.BarcodeFormat.CODE_128,
        ZX.BarcodeFormat.CODE_39,
        ZX.BarcodeFormat.CODABAR
      ].filter(Boolean)
    );
  }
  zxingReader = new ZX.BrowserMultiFormatReader(hints);
  return zxingReader;
}
async function listCameras() {
  const r = await ensureZXingReader();
  const list = await r.listVideoInputDevices();
  return (list || [])
    .map(d => ({ deviceId: d.deviceId || d.id, label: d.label || "" }))
    .filter(d => d.deviceId);
}
async function pickBackCameraId() {
  const cams = await listCameras();
  if (!cams.length) return null;
  const back = cams.find(c => /back|environment|rear/i.test(c.label));
  return (back || cams[0]).deviceId;
}

// ==== поиск ItemExt → pick ====
function pick(ctx, ext) {
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

  const hintBox = ctx.$("cost-suggest");
  hintBox.innerHTML = "";
  if (pickedProduct.last_purchase_cost != null) {
    const b = document.createElement("button");
    b.className = "btn secondary";
    b.textContent = ctx.t("last_purchase_cost_hint", { cost: ctx.fmtMoney(pickedProduct.last_purchase_cost) });
    b.onclick = () => { ctx.$("cost").value = String(pickedProduct.last_purchase_cost); ctx.$("cost").focus(); ctx.$("cost").select?.(); };
    hintBox.appendChild(b);
  }
  if (pickedProduct.price != null) {
    const b2 = document.createElement("button");
    b2.className = "btn ghost";
    b2.textContent = `${ctx.t("op.price")}: ${ctx.fmtMoney(pickedProduct.price)}`;
    b2.onclick = () => { ctx.$("price").value = String(pickedProduct.price); ctx.$("price").focus(); ctx.$("price").select?.(); };
    hintBox.appendChild(b2);
  }

  setTimeout(() => ctx.$("qty")?.focus(), 0);
}
async function runSearch(ctx, q, docId) {
  const box = ctx.$("product-results");
  box.textContent = ctx.t("searching");
  try {
    const payload = { q, doc_id: Number(docId) };
    if (docCtx.price_type_id != null) payload.price_type_id = Number(docCtx.price_type_id);
    if (docCtx.stock_id != null) payload.stock_id = Number(docCtx.stock_id);
    const { data } = await ctx.api("product_search", payload);
    const items = data?.result?.items || [];
    if (!items.length) {
      pickedProduct = null;
      ctx.$("product-picked").classList.add("hidden");
      box.textContent = ctx.t("nothing_found");
      return;
    }
    pick(ctx, items[0]);   // авто-выбор первого ItemExt
    box.textContent = "";
  } catch {
    box.textContent = ctx.t("search_error");
  }
}

// ==== сканер ====
async function startScan(ctx) {
  const insecure = location.protocol !== "https:" && location.hostname !== "localhost";
  if (insecure) { toast(ctx.t("camera_open_failed"), false); return; }

  const video = ctx.$("preview");
  const scanner = ctx.$("scanner");
  if (!video || !scanner) { toast(ctx.t("camera_open_failed"), false); return; }

  try {
    const reader = await ensureZXingReader();

    scanner.classList.remove("hidden");
    video.setAttribute("playsinline",""); video.autoplay = true; video.muted = true;

    ensureOverlay(video);
    layoutOverlay(video, true);

    if (!currentDeviceId) currentDeviceId = await pickBackCameraId();

    // Учитываем изменение реальных метаданных видео (размер кадра)
    const onMeta = () => { layoutOverlay(video, true); };
    video.removeEventListener("loadedmetadata", onMeta);
    video.addEventListener("loadedmetadata", onMeta, { once: true });

    zxingControls = await reader.decodeFromVideoDevice(currentDeviceId ?? undefined, "preview", (result, err) => {
      layoutOverlay(video, true);
      if (result?.text) {
        try { navigator.vibrate?.(35); } catch {}
        const code = result.text;
        const pq = ctx.$("product-query"), bc = ctx.$("barcode");
        if (bc) bc.value = code;
        if (pq) pq.value = code;
        stopScan(ctx);
        runSearch(ctx, code, ctx.__docId);
      } else if (err && err.name !== "NotFoundException") {
        console.debug("[ZXing]", err?.name || err);
      }
    });

    // фонарик, если доступен
    try {
      const ms = video.srcObject;
      const track = ms && ms.getVideoTracks && ms.getVideoTracks()[0];
      const caps = track?.getCapabilities?.() || {};
      if (caps.torch) await track.applyConstraints({ advanced: [{ torch: true }] }).catch(()=>{});
    } catch {}
  } catch (e) {
    console.error("[ZXing] start error:", e);
    stopScan(ctx);
    toast(ctx.t("camera_open_failed"), false);
  }
}

function stopScan(ctx) {
  try { zxingControls?.stop?.(); } catch {}
  try { zxingReader?.reset?.(); } catch {}
  zxingControls = null;

  const video = ctx.$("preview");
  if (video) { try { video.pause?.(); } catch {} try { video.srcObject = null; } catch {} }

  // спрячем сканер и очистим overlay
  ctx.$("scanner")?.classList.add("hidden");
  if (og && overlay) og.clearRect(0,0,overlay.width,overlay.height);

  // отписка ResizeObserver (чтобы overlay не «жил» дальше)
  try { overlayObserver?.disconnect?.(); } catch {}
  overlayObserver = null;
}

// ==== сохранение операции ====
async function saveOp(ctx, docId) {
  const qtyEl = ctx.$("qty");
  const costEl = ctx.$("cost");
  const priceEl = ctx.$("price");
  const qty = ctx.toNumber(qtyEl.value);
  const cost = ctx.toNumber(costEl.value);
  const price = ctx.toNumber(priceEl.value);

  markInvalid(qtyEl,false); markInvalid(costEl,false);

  if (!pickedProduct?.id) { toast(ctx.t("select_product_first"), false); return; }
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

  setBusy(ctx, true);
  try {
    const { ok, data } = await ctx.api("purchase_ops_add", { items: [item] });
    const affected = data?.result?.row_affected || 0;
    if (ok && affected > 0) {
      toast(ctx.t("op_added"));
      resetForm(ctx);
    } else {
      toast(data?.description || ctx.t("save_failed"), false);
    }
  } catch {
    toast(ctx.t("network_error_save"), false);
  } finally {
    setBusy(ctx, false);
  }
}
function resetForm(ctx) {
  ["barcode","product-query","qty","cost","price"].forEach(id=>{
    const el = ctx.$(id); if (el){ el.value = ""; markInvalid(el,false); }
  });
  pickedProduct = null;
  ctx.$("product-picked")?.classList.add("hidden");
  ctx.$("cost-suggest").innerHTML = "";
  ctx.$("product-results").textContent = "";
  ctx.$("barcode")?.focus();
}

// ==== экран ====
export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");
  ctx.__docId = Number(id);

  // подтянуть контекст документа (price_type_id, stock_id)
  try {
    const { data } = await ctx.api("purchase_get", { doc_id: ctx.__docId });
    const doc = data?.result?.doc;
    docCtx.price_type_id = doc?.price_type?.id ?? null;
    docCtx.stock_id = doc?.stock?.id ?? null;
  } catch {}

  // кнопки сканера — иконки вместо текста
  const btnScan  = ctx.$("btn-scan");
  const btnClose = ctx.$("btn-close-scan");
  if (btnScan) {
    btnScan.classList.add("btn", "icon");
    btnScan.setAttribute("aria-label", ctx.t("op.scan"));
    btnScan.innerHTML = `<i class="fa-solid fa-camera"></i>`;
    btnScan.onclick = () => startScan(ctx);
  }
  if (btnClose) {
    btnClose.classList.add("btn", "icon");
    btnClose.setAttribute("aria-label", ctx.t("cancel"));
    btnClose.innerHTML = `<i class="fa-solid fa-xmark"></i>`;
    btnClose.onclick = () => stopScan(ctx);
  }

  // поиск по Enter
  const enterSearch = (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const v = e.target.value.trim();
    if (v) runSearch(ctx, v, ctx.__docId);
  };
  ctx.$("barcode")?.addEventListener("keydown", enterSearch);
  ctx.$("product-query")?.addEventListener("keydown", enterSearch);

  // быстрые + навигация Enter
  ctx.$("qty-quick")?.addEventListener("click", (e)=>{
    const btn = e.target.closest("button[data-inc]");
    if (!btn) return;
    const inc = Number(btn.dataset.inc || "0");
    const el = ctx.$("qty");
    const val = ctx.toNumber(el.value) || 0;
    el.value = String(val + inc);
    el.focus(); el.select?.();
  });
  ctx.$("qty")  ?.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("cost") ?.focus(); } });
  ctx.$("cost") ?.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); ctx.$("price")?.focus(); } });
  ctx.$("price")?.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); saveOp(ctx, ctx.__docId); } });

  // сохранить/отмена
  ctx.$("btn-op-cancel")?.addEventListener("click", () => { location.hash = `#/doc/${id}`; });
  ctx.$("btn-op-save")  ?.addEventListener("click", () => saveOp(ctx, ctx.__docId));

  // корректное завершение сканера
  document.addEventListener("visibilitychange", () => { if (document.hidden) stopScan(ctx); });
  window.addEventListener("pagehide", () => stopScan(ctx));
  window.addEventListener("resize", () => {
    const video = ctx.$("preview");
    if (video && !ctx.$("scanner")?.classList.contains("hidden")) layoutOverlay(video, true);
  });

  // стартовый фокус — на штрих-код
  ctx.$("barcode")?.focus();
}
