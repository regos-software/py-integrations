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

  // QR со ссылкой на текущую страницу
  const qrEl = ctx.$("qr-code");
  if (qrEl && window.QRCode) {
    // на случай повторного входа на screen: очищаем контейнер
    qrEl.innerHTML = "";

    new QRCode(qrEl, {
      text: location.href,                // текущий адрес, включая hash
      width: 192,
      height: 192,
      correctLevel: QRCode.CorrectLevel.M
    });

    // доступность и подсказка
    qrEl.setAttribute("role", "img");
    qrEl.setAttribute("aria-label", "QR для этой страницы");
    qrEl.title = location.href;
  }

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
 
}
