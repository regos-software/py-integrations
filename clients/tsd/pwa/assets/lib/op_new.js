// views/op_new.js — без import; получает ctx
let mediaStream = null, scanTimer = null, pickedProduct = null;

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");
  pickedProduct = null;

  // --- helpers: UI busy/notify ---
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
  function toast(msg) {
    let t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.style.cssText = "position:fixed;left:50%;bottom:16px;transform:translateX(-50%);max-width:90%;background:#10b981;color:#fff;padding:10px 14px;border-radius:8px;box-shadow:0 4px 14px rgba(0,0,0,.2);z-index:9999;font-size:14px";
      document.body.appendChild(t);
    }
    t.textContent = msg || "";
    t.style.display = "block";
    setTimeout(()=>{ t.style.display = "none"; }, 2000);
  }
  function simulateEnter(el){
    if (!el) return;
    el.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  }

  // --- wire UI ---
  ctx.$("btn-scan").onclick       = startScan;
  ctx.$("btn-close-scan").onclick = stopScan;
  ctx.$("product-query").addEventListener("keydown", (e)=>{
    if (e.key==="Enter"){
      e.preventDefault();
      const q = e.target.value.trim();
      if (q) doProductSearch(q); // поиск запускается только по Enter
    }
  });
  ctx.$("btn-op-cancel").onclick  = ()=>{ location.hash = `#/doc/${id}`; };
  ctx.$("btn-op-save").onclick    = ()=>saveOp(id);

  let detector = null;
  if ("BarcodeDetector" in window) {
    try { detector = new BarcodeDetector({ formats: ["ean_13","ean_8","code_128","upc_a","upc_e","itf"] }); } catch {}
  }

  // --- scan ---
  async function startScan(){
    ctx.$("scanner").classList.remove("hidden");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      mediaStream = stream;
      const video = ctx.$("preview");
      video.srcObject = stream; await video.play().catch(()=>{});
      scanTimer = setInterval(async ()=>{
        try {
          if (!detector) return;
          const track = stream.getVideoTracks()[0];
          const imageCapture = new ImageCapture(track);
          const bitmap = await imageCapture.grabFrame();
          const res = await detector.detect(bitmap);
          if (res && res[0]) {
            const code = res[0].rawValue || res[0].displayValue;
            if (code) {
              // подставляем в оба поля и "жмём" Enter на поле поиска
              const pq = ctx.$("product-query");
              const bc = ctx.$("barcode");
              if (bc) bc.value = code;
              if (pq) { pq.value = code; }
              stopScan();
              simulateEnter(pq); // симулируем Enter
            }
          }
        } catch {}
      }, 500);
    } catch {
      alert("Не удалось открыть камеру. Введите штрих-код вручную.");
      ctx.$("scanner").classList.add("hidden");
    }
  }
  function stopScan(){
    if (scanTimer) { clearInterval(scanTimer); scanTimer=null; }
    if (mediaStream) { mediaStream.getTracks().forEach(t=>t.stop()); mediaStream=null; }
    ctx.$("scanner").classList.add("hidden");
  }

  // --- search & pick ---
  async function doProductSearch(q){
    const box = ctx.$("product-results");
    box.innerHTML = `<div class="muted">Поиск...</div>`;
    const { data } = await ctx.api("product_search", { q, doc_id: id });
    const items = data?.result?.items || [];
    renderResults(items);
  }
  function renderResults(items){
    const box = ctx.$("product-results");
    if (!items.length){ box.innerHTML = `<div class="muted">Ничего не найдено</div>`; return; }
    box.innerHTML = "";
    items.forEach(p=>{
      const el = document.createElement("div");
      el.className = "item";
      const codeOrBarcode = p.base_barcode
        ?? (p.barcode_list ? String(p.barcode_list).split(",")[0]?.trim() : "")
        ?? p.code;
      el.innerHTML = `
        <div class="row">
          <div>
            <div><strong>${ctx.esc(p.name||"")}</strong></div>
            <div class="muted">${ctx.esc(codeOrBarcode||"")}</div>
          </div>
          <button class="btn">Выбрать</button>
        </div>`;
      el.querySelector(".btn").onclick = ()=>pick(p);
      box.appendChild(el);
    });
  }
  function pick(p){
    const barcode = p.base_barcode || (p.barcode_list ? String(p.barcode_list).split(",")[0]?.trim() : "");
    pickedProduct = {
      id: p.id || p.uuid || p.code,
      name: p.name,
      barcode,
      vat_value: p?.vat?.value ?? 0
    };
    ctx.$("product-picked").classList.remove("hidden");
    ctx.$("picked-name").textContent = pickedProduct.name || "—";
    ctx.$("picked-code").textContent = pickedProduct.barcode || "";
    setTimeout(()=>{ ctx.$("qty")?.focus(); }, 0);
  }

  // --- save ---
  async function saveOp(docId){
    if (!pickedProduct) return alert("Выберите товар");
    const qty   = ctx.toNumber(ctx.$("qty").value);
    const cost  = ctx.toNumber(ctx.$("cost").value);
    const price = ctx.toNumber(ctx.$("price").value);
    if (!qty || qty<=0) return alert("Введите количество");

    const vat_value = Number(pickedProduct.vat_value ?? 0);

    const item = {
      document_id: Number(docId),
      item_id: Number(pickedProduct.id),
      quantity: qty,
      cost: cost,
      price: price || undefined,
      vat_value
      // description: можно добавить из отдельного поля при необходимости
    };

    setBusy(true);
    try {
      const { ok, data } = await ctx.api("purchase_ops_add", { items: [item] });
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        toast("Операция добавлена");
        resetForm(); // остаёмся на экране, готовим новую операцию
      } else {
        const msg = data?.description || "Не удалось сохранить операцию";
        alert(msg);
      }
    } catch {
      alert("Ошибка сети при сохранении");
    } finally {
      setBusy(false);
    }
  }

  function resetForm(){
    ["barcode","product-query","qty","cost","price"].forEach(id=>{
      const el = ctx.$(id);
      if (el) el.value = "";
    });
    pickedProduct = null;
    ctx.$("product-picked").classList.add("hidden");
    const box = ctx.$("product-results");
    if (box) box.innerHTML = "";
    ctx.$("product-query")?.focus();
  }
}
