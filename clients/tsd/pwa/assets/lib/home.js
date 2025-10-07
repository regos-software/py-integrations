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

  // QR сразу под списком меню (после контейнера кнопок)
  const pageUrl = new URL(location.href, location.origin).toString();

  // пытаемся найти общий контейнер, содержащий все кнопки меню
  const ids = ["btn-doc-purchase", "btn-doc-sales", "btn-doc-inventory"];
  const btns = ids.map(id => ctx.$(id)).filter(Boolean);

  let container = null;
  if (btns.length) {
    let cand = btns[0].parentElement;
    while (cand && !btns.every(b => cand.contains(b))) cand = cand.parentElement;
    container = cand || btns[btns.length - 1].parentElement;
  }
  if (!container) container = ctx.$("home") || document.body;

  // создаём/переиспользуем узел
  let qrWrap = document.getElementById("qr-wrap");
  if (!qrWrap) {
    qrWrap = document.createElement("div");
    qrWrap.id = "qr-wrap";
    qrWrap.style.cssText = [
      "margin-top:16px",
      "display:flex",
      "flex-direction:column",
      "gap:8px",
      "align-items:center"
    ].join(";");

    const cap = document.createElement("div");
    cap.textContent = (ctx.t && (ctx.t("scan_qr_open_here") || "")) || "Сканируйте, чтобы открыть эту страницу";
    cap.style.fontSize = "12px";
    cap.style.opacity = "0.9";
    cap.style.textAlign = "center";
    qrWrap.appendChild(cap);

    const img = document.createElement("img");
    img.id = "qr-img";
    img.alt = "QR";
    img.width = 200;
    img.height = 200;
    img.style.background = "#fff";
    img.style.borderRadius = "6px";
    img.style.padding = "6px";
    img.style.boxShadow = "0 2px 8px rgba(0,0,0,0.1)";
    qrWrap.appendChild(img);

    const link = document.createElement("a");
    link.id = "qr-link";
    link.style.cssText = "max-width:100%;word-break:break-all;text-align:center;text-decoration:underline";
    link.target = "_blank";
    link.rel = "noopener";
    qrWrap.appendChild(link);
  }

  // данные для QR и ссылки
  const qrImg  = qrWrap.querySelector("#qr-img");
  const qrLink = qrWrap.querySelector("#qr-link");
  qrImg.src = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" + encodeURIComponent(pageUrl);
  qrLink.href = pageUrl;
  qrLink.textContent = pageUrl;

  // вставляем сразу после контейнера с меню
  container.insertAdjacentElement("afterend", qrWrap);



}
