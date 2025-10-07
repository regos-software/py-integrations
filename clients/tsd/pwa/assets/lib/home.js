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

  // ---- QR со ссылкой на текущую страницу ----
  const urlForQR = location.origin + location.pathname + location.hash;

  // находим или создаём контейнер
  let qrEl = ctx.$("qr-code");
  if (!qrEl) {
    const anchor = ctx.$("doc-types") || document.getElementById("app");
    qrEl = document.createElement("div");
    qrEl.id = "qr-code";
    qrEl.className = "qr";
    // поместим сразу под списком документов
    if (anchor && anchor.insertAdjacentElement) {
      anchor.insertAdjacentElement("afterend", qrEl);
    } else {
      document.body.appendChild(qrEl);
    }
  }

  // очищаем и рисуем
  qrEl.innerHTML = "";
  if (window.QRCode) {
    new QRCode(qrEl, {
      text: urlForQR,
      width: 192,
      height: 192,
      correctLevel: QRCode.CorrectLevel.M,
    });
  } else {
    // запасной вариант (библиотека ещё не подгрузилась)
    qrEl.textContent = urlForQR;
  }

  // доступность
  qrEl.setAttribute("role", "img");
  qrEl.setAttribute("aria-label", "QR для этой страницы");
  qrEl.title = urlForQR;

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
