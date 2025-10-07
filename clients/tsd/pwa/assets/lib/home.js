// lib/home.js — без import; получает ctx
export async function screenHome(ctx) {
  await ctx.loadView("home");

  // заголовок
  ctx.$("home-title").textContent = ctx.t("main_menu");

  // подписи кнопок
  ctx.$("btn-doc-purchase-txt").textContent  = ctx.t("doc_purchase");
  ctx.$("btn-doc-sales-txt").textContent     = ctx.t("doc_sales");
  ctx.$("btn-doc-inventory-txt").textContent = ctx.t("doc_inventory");

  // бейджи "скоро"
  const soonTxt = ctx.t("soon");
  ctx.$("pill-sales").textContent     = soonTxt;
  ctx.$("pill-inventory").textContent = soonTxt;

  // действия
  ctx.$("btn-doc-purchase").onclick = () => { location.hash = "#/docs"; };

  const soon = () => {
    let t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.className = "toast";
      document.body.appendChild(t);
    }
    t.textContent = soonTxt;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 1500);
  };
  ctx.$("btn-doc-sales").onclick     = soon;
  ctx.$("btn-doc-inventory").onclick = soon;

const qrEl = ctx.$("qr-code");
if (qrEl) {
  const QR = globalThis.QRCode; 
  qrEl.innerHTML = "";
  if (QR) {
    new QR(qrEl, {
      text: location.href,
      width: 160,
      height: 160,
      correctLevel: QR.CorrectLevel.M
    });
  } else {
    // Fallback на случай, если CDN не загрузился
    const img = new Image();
    img.width = 160; img.height = 160;
    img.alt = "QR";
    img.src = "https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=" + encodeURIComponent(location.href);
    qrEl.replaceChildren(img);
  }
}

  
}
