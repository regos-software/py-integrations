// app.js (router + bootstrap) — без статичных import и с PWA-кнопкой установки
const rel = (q) => new URL(q, import.meta.url).toString();

// Либы: api, utils, i18n
const apiLib   = await import(rel('?assets=lib/api.js'));   // { CI, api, registerSW }
const utilsLib = await import(rel('?assets=lib/utils.js')); // { $, out, tickClock, loadView, esc, fmtMoney, fmtNum, unixToLocal, toNumber }
const i18nLib  = await import(rel('?assets=lib/i18n.js'));  // { initI18n, t, setLocale, getLocale, fmt }

// Контекст, который будем передавать во вьюхи
// i18n: проксируем функции, чтобы не залипали старые ссылки
const ctx = {
  ...apiLib,
  ...utilsLib,
  t:  (...a) => i18nLib.t(...a),        // ⬅ всегда актуальный переводчик
  fmt:(...a) => i18nLib.fmt(...a),      // ⬅ актуальный форматтер
  setLocale: async (...a) => i18nLib.setLocale(...a),
  getLocale: () => i18nLib.getLocale(),
};

// --- helpers (UI) ---
function setAppTitle(text) {
  try { document.title = text || document.title; } catch {}
  const h = ctx.$("title");
  if (h) h.textContent = text;
}

// Создаём/находим кнопку установки (если её нет в верстке)
function ensureInstallButton() {
  let btn = ctx.$("btn-install");
  if (!btn) {
    const container =
      document.querySelector(".appbar .right") ||
      document.querySelector(".appbar-right") ||
      document.body;

    btn = document.createElement("button");
    btn.id = "btn-install";
    btn.className = "btn small hidden";
    btn.innerHTML = `<i class="fa-solid fa-download"></i> <span id="btn-install-txt"></span>`;
    container.appendChild(btn);
  }
  return btn;
}

// Настраиваем кнопку «Установить» через beforeinstallprompt
function setupInstallCTA() {
  const btn = ensureInstallButton();
  const txt = ctx.$("btn-install-txt");
  if (txt) txt.textContent = ctx.t?.("install_app") || "Установить";

  const hide = () => btn.classList.add("hidden");
  const show = () => btn.classList.remove("hidden");

  const isStandalone =
    window.matchMedia?.("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  if (isStandalone) hide();

  let deferredPrompt = null;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    show();
  });

  btn.addEventListener("click", async () => {
    if (!deferredPrompt) return;
    btn.disabled = true;
    try {
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
    } finally {
      btn.disabled = false;
      hide();
      deferredPrompt = null;
    }
  });

  window.addEventListener("appinstalled", hide);
}

// --- UI bootstrap ---
setAppTitle("TSD"); // первоначальный заголовок до i18n
if (ctx.$("now")) {
  ctx.tickClock();
  setInterval(ctx.tickClock, 1000);
}

// Регистрация Service Worker
if (typeof ctx.registerSW === "function") {
  ctx.registerSW();
} else if ("serviceWorker" in navigator) {
  const scopePath = location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  navigator.serviceWorker
    .register(new URL("?pwa=sw", location.href).toString(), { scope: scopePath })
    .catch(err => console.error("[SW register fallback] failed:", err));
}

// Инициализация i18n
await i18nLib.initI18n();
// a11y: проставим текущий язык на <html>
document.documentElement.lang = ctx.getLocale();

// Локализуем заголовок и кнопку установки
setAppTitle(ctx.t("app.title") || "TSD");
setupInstallCTA();

const langSelect = ctx.$("lang-select");
if (langSelect) {
  langSelect.value = ctx.getLocale();
  langSelect.addEventListener("change", async () => {
    // i18n: обязательно дождаться смены локали (загрузка словаря и обновление биндера t)
    await ctx.setLocale(langSelect.value);
    document.documentElement.lang = ctx.getLocale();

    // Обновим видимые тексты в шапке
    setAppTitle(ctx.t("app.title") || "TSD");
    const installTxt = ctx.$("btn-install-txt");
    if (installTxt) installTxt.textContent = ctx.t?.("install_app") || "Установить";

    // Перерисуем текущий экран (чтобы тексты обновились)
    await router();

    // Если вернёте OAuth — можно передавать актуальную локаль:
    // await reinitOAuth();
  });
}

// Единая кнопка «Назад»
const backBtn = ctx.$("nav-back");
if (backBtn) {
  backBtn.addEventListener("click", () => {
    if (history.length > 1) history.back();
    else location.hash = "#/docs";
  });
}

/* ---------------- REGOS OAuth (временно закомментировано) ----------------
const REGOS_CLIENT_ID    = "your_client_id_here"; // TODO: замените на реальный clientId
const REGOS_REDIRECT_URI = new URL("?assets=oauth/redirect.html", location.href).toString();

async function reinitOAuth() {
  if (!window.RegosOAuthSDK) return;
  try { window.RegosOAuthSDK.destroy?.(); } catch (_) {}
  await window.RegosOAuthSDK.initialize({
    clientId: REGOS_CLIENT_ID,
    redirectUri: REGOS_REDIRECT_URI,
    containerId: "regos-login",
    language: ctx.getLocale(),
    buttonSize: "xs",
    buttonTheme: "light",
    buttonType: "text",
    buttonTextType: "short",
    buttonBorderRadius: 8,
    flow: "auto",
    silent: true,
    debug: false,
    onData: (user, access_token) => { ctx.currentUser = user || null; ctx.accessToken = access_token || null; },
    onLogout: () => { ctx.currentUser = null; ctx.accessToken = null; },
    onError: (err) => console.error("[REGOS OAuth] error:", err?.message || err),
  });
}
// await reinitOAuth();
-------------------------------------------------------------------------- */

// --- Вьюхи грузим динамически ---
const views = {
  home:   await import(rel('?assets=lib/home.js')),   // export screenHome(ctx)
  docs:   await import(rel('?assets=lib/docs.js')),   // export screenDocs(ctx, page, q)
  doc:    await import(rel('?assets=lib/doc.js')),    // export screenDoc(ctx, id)
  op_new: await import(rel('?assets=lib/op_new.js')), // export screenOpNew(ctx, id)
};

// --- SPA router ---
async function router() {
  const h = location.hash || "#/home";
  if (h.startsWith("#/docs")) {
    const qs = new URLSearchParams(h.split("?")[1] || "");
    const p = parseInt(qs.get("page") || "1", 10) || 1;
    const q = qs.get("q") || "";
    await views.docs.screenDocs(ctx, p, q);
  } else if (h.startsWith("#/doc/") && h.endsWith("/op/new")) {
    const id = h.split("/")[2];
    await views.op_new.screenOpNew(ctx, id);
  } else if (h.startsWith("#/doc/")) {
    const id = h.split("/")[2];
    await views.doc.screenDoc(ctx, id);
  } else {
    await views.home.screenHome(ctx);
  }
}
window.addEventListener("hashchange", router);
router();

// Для отладки
window.__CI__  = apiLib.CI;
window.__out   = utilsLib.out;
window.__i18n  = { get: ctx.getLocale, set: ctx.setLocale, t: ctx.t };
