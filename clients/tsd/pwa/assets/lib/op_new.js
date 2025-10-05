// views/op_new.js — без import; получает ctx
let mediaStream = null, scanTimer = null, pickedProduct = null;

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");
  pickedProduct = null;

  // --- helpers: UI busy/notify ---
  function setBusy(b) {
    const ids = ["btn-scan","btn-close-scan","product-query","barcode","qty","cost","price","expdate","btn-op-save","btn-op-cancel"];
    ids.forEach(k => {
      const el = ctx.$(k);
      if (!el) return;
      if ("disabled" in el) el.disabled = b;
    });
    const save = ctx.$("btn-op-save");
    if (save) save.textContent = b ? "Сохранение..." : "Сохранить";
  }
  function toast(msg) {
    // простой тост без зависимостей
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

  // --- wire UI ---
  ctx.$("btn-scan").onclick       = startScan;
  ctx.$("btn-close-scan").onclick = stopScan;
  ctx.$("product-query").addEventListener("keydown", (e)=>{
    if (e.key==="Enter"){
      e.preventDefault();
      doProductSearch(e.target.value.trim());
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
              ctx.$("barcode").value = code;
              stopScan();
              await onBarcode(code);
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
  async function onBarcode(code){
    ctx.$("product-query").value = code;
    await doProductSearch(code, true);
  }

  // --- search & pick ---
  async function doProductSearch(q, autoPick=false){
    const box = ctx.$("product-results");
    box.innerHTML = `<div class="muted">Поиск...</div>`;
    const { data } = await ctx.api("product_search", { q, doc_id: id });
    const items = data?.result?.items || [];
    renderResults(items, autoPick);
  }
  function renderResults(items, autoPick){
    const box = ctx.$("product-results");
    if (!items.length){ box.innerHTML = `<div class="muted">Ничего не найдено</div>`; return; }
    if (autoPick && items.length===1){ return pick(items[0]); }
    box.innerHTML = "";
    items.forEach(p=>{
      const el = document.createElement("div");
      el.className = "item";
      const codeOrBarcode = p.code ?? p.base_barcode ?? (p.barcode_list ? String(p.barcode_list).split(",")[0]?.trim() : "");
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
    // сохраняем всё, что может пригодиться при добавлении (в т.ч. vat)
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
    // фокус на количество для быстрого ввода
    setTimeout(()=>{ ctx.$("qty")?.focus(); }, 0);
  }

  // --- save ---
  async function saveOp(docId){
    if (!pickedProduct) return alert("Выберите товар");
    const qty   = ctx.toNumber(ctx.$("qty").value);
    const cost  = ctx.toNumber(ctx.$("cost").value);
    const price = ctx.toNumber(ctx.$("price").value);
    if (!qty || qty<=0) return alert("Введите количество");

    // минимальный VAT: берём из товара, иначе 0
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
        // подготовить форму для следующей операции
        resetForm();
      } else {
        const msg = data?.description || "Не удалось сохранить операцию";
        alert(msg);
      }
    } catch (e) {
      alert("Ошибка сети при сохранении");
    } finally {
      setBusy(false);
    }
  }

  function resetForm(){
    // очистка инпутов
    ["barcode","product-query","qty","cost","price","expdate"].forEach(id=>{
      const el = ctx.$(id);
      if (el) el.value = "";
    });
    // скрыть выбранный товар
    pickedProduct = null;
    ctx.$("product-picked").classList.add("hidden");
    // очистить результаты поиска
    const box = ctx.$("product-results");
    if (box) box.innerHTML = "";
    // фокус на поиск
    ctx.$("product-query")?.focus();
  }
}
