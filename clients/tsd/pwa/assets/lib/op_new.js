// views/op_new.js — без import; получает ctx
let mediaStream=null, scanTimer=null, pickedProduct=null;

export async function screenOpNew(ctx, id) {
  await ctx.loadView("op_new");
  pickedProduct = null;

  ctx.$("btn-scan").onclick      = startScan;
  ctx.$("btn-close-scan").onclick= stopScan;
  ctx.$("product-query").addEventListener("keydown", (e)=>{ if (e.key==="Enter"){ e.preventDefault(); doProductSearch(e.target.value.trim()); }});
  ctx.$("btn-op-cancel").onclick = ()=>{ location.hash = `#/doc/${id}`; };
  ctx.$("btn-op-save").onclick   = ()=>saveOp(id);

  let detector = null;
  if ("BarcodeDetector" in window) {
    try { detector = new BarcodeDetector({ formats: ["ean_13","ean_8","code_128","upc_a","upc_e","itf"] }); } catch {}
  }

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
    } catch { alert("Не удалось открыть камеру. Введите штрих-код вручную."); ctx.$("scanner").classList.add("hidden"); }
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

  async function doProductSearch(q, autoPick=false){
    ctx.$("product-results").innerHTML = `<div class="muted">Поиск...</div>`;
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
      el.innerHTML = `
        <div class="row">
          <div>
            <div><strong>${ctx.esc(p.name||"")}</strong></div>
            <div class="muted">${ctx.esc(p.code || p.barcode || "")}</div>
          </div>
          <button class="btn">Выбрать</button>
        </div>`;
      el.querySelector(".btn").onclick = ()=>pick(p);
      box.appendChild(el);
    });
  }
  function pick(p){
    pickedProduct = { id: p.id || p.uuid || p.code, name: p.name, barcode: p.barcode || "" };
    ctx.$("product-picked").classList.remove("hidden");
    ctx.$("picked-name").textContent = pickedProduct.name || "—";
    ctx.$("picked-code").textContent = pickedProduct.barcode || "";
  }
  async function saveOp(docId){
    if (!pickedProduct) return alert("Выберите товар");
    const qty = ctx.toNumber(ctx.$("qty").value);
    const cost = ctx.toNumber(ctx.$("cost").value);
    const price = ctx.toNumber(ctx.$("price").value);
    const expdate = ctx.$("expdate").value || null;
    if (!qty || qty<=0) return alert("Введите количество");
    const payload = { doc_id: docId, product_id: pickedProduct.id, qty, cost, price, expdate, barcode: ctx.$("barcode").value.trim() || pickedProduct.barcode || null };
    const { ok, data } = await ctx.api("purchase_add_operation", payload);
    if (ok && data?.result?.status==="ok"){ alert("Операция добавлена"); location.hash = `#/doc/${docId}`; }
    else { alert("Не удалось сохранить операцию"); }
  }
}
