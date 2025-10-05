// views/op_new.js
import { api } from "./?assets=lib/api.js";
import { loadView, $, esc, fmtNum, fmtMoney, toNumber } from "./?assets=lib/utils.js";

let mediaStream=null, scanTimer=null, pickedProduct=null;

export async function screenOpNew(id) {
  await loadView("op_new");
  pickedProduct = null;

  $("btn-scan").onclick = startScan;
  $("btn-close-scan").onclick = stopScan;
  $("product-query").addEventListener("keydown", (e)=>{ if (e.key==="Enter"){ e.preventDefault(); doProductSearch(e.target.value.trim()); }});
  $("btn-op-cancel").onclick = ()=>{ location.hash = `#/doc/${id}`; };
  $("btn-op-save").onclick = ()=>saveOp(id);

  let detector = null;
  if ("BarcodeDetector" in window) {
    try { detector = new BarcodeDetector({ formats: ["ean_13","ean_8","code_128","upc_a","upc_e","itf"] }); } catch {}
  }

  async function startScan(){
    $("scanner").classList.remove("hidden");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      mediaStream = stream;
      const video = $("preview");
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
              $("barcode").value = code;
              stopScan();
              await onBarcode(code);
            }
          }
        } catch {}
      }, 500);
    } catch { alert("Не удалось открыть камеру. Введите штрих-код вручную."); $("scanner").classList.add("hidden"); }
  }
  function stopScan(){
    if (scanTimer) { clearInterval(scanTimer); scanTimer=null; }
    if (mediaStream) { mediaStream.getTracks().forEach(t=>t.stop()); mediaStream=null; }
    $("scanner").classList.add("hidden");
  }
  async function onBarcode(code){
    $("product-query").value = code;
    await doProductSearch(code, true);
  }

  async function doProductSearch(q, autoPick=false){
    $("product-results").innerHTML = `<div class="muted">Поиск...</div>`;
    const { data } = await api("product_search", { q, doc_id: id });
    const items = data?.result?.items || [];
    renderResults(items, autoPick);
  }
  function renderResults(items, autoPick){
    const box = $("product-results");
    if (!items.length){ box.innerHTML = `<div class="muted">Ничего не найдено</div>`; return; }
    if (autoPick && items.length===1){ return pick(items[0]); }
    box.innerHTML = "";
    items.forEach(p=>{
      const el = document.createElement("div");
      el.className = "item";
      el.innerHTML = `
        <div class="row">
          <div>
            <div><strong>${esc(p.name||"")}</strong></div>
            <div class="muted">${esc(p.code || p.barcode || "")}</div>
          </div>
          <button class="btn">Выбрать</button>
        </div>`;
      el.querySelector(".btn").onclick = ()=>pick(p);
      box.appendChild(el);
    });
  }
  function pick(p){
    pickedProduct = { id: p.id || p.uuid || p.code, name: p.name, barcode: p.barcode || "" };
    $("product-picked").classList.remove("hidden");
    $("picked-name").textContent = pickedProduct.name || "—";
    $("picked-code").textContent = pickedProduct.barcode || "";
  }
  async function saveOp(docId){
    if (!pickedProduct) return alert("Выберите товар");
    const qty = toNumber($("qty").value);
    const cost = toNumber($("cost").value);
    const price = toNumber($("price").value);
    const expdate = $("expdate").value || null;
    if (!qty || qty<=0) return alert("Введите количество");
    const payload = { doc_id: docId, product_id: pickedProduct.id, qty, cost, price, expdate, barcode: $("barcode").value.trim() || pickedProduct.barcode || null };
    const { ok, data } = await api("purchase_add_operation", payload);
    if (ok && data?.result?.status==="ok"){ alert("Операция добавлена"); location.hash = `#/doc/${docId}`; }
    else { alert("Не удалось сохранить операцию"); }
  }
}
