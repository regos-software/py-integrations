// app.js (router + bootstrap) — без статичных import

const rel = (q) => new URL(q, import.meta.url).toString();

// Либы: api, utils, i18n
const apiLib    = await import(rel('?assets=lib/api.js'));     // { CI, api, registerSW }
const utilsLib  = await import(rel('?assets=lib/utils.js'));   // { $, out, tickClock, loadView, esc, fmtMoney, fmtNum, unixToLocal, toNumber }
const i18nLib   = await import(rel('?assets=lib/i18n.js'));    // { initI18n, t, setLocale, getLocale }

// Контекст, который будем передавать во вьюхи
const ctx = {
  ...apiLib,
  ...utilsLib,
  t: i18nLib.t,
  setLocale: i18nLib.setLocale,
  getLocale: i18nLib.getLocale,
};

// --- UI bootstrap ---
ctx.$("title").textContent = "TSD";
ctx.tickClock(); setInterval(ctx.tickClock, 1000);
ctx.registerSW?.();

// Инициализация i18n (выставляем язык из localStorage/браузера)
await i18nLib.initI18n();
const langSelect = ctx.$("lang-select");
if (langSelect) {
  langSelect.value = ctx.getLocale();
  langSelect.addEventListener("change", async () => {
    ctx.setLocale(langSelect.value);
    // Перезапустим OAuth с новым языком
    await reinitOAuth();
    // Перерисуем текущий экран (чтобы тексты обновились)
    router();
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

// --- REGOS OAuth (инициализация/переинициализация) ---
const REGOS_CLIENT_ID   = "your_client_id_here"; // TODO: замените на реальный clientId
const REGOS_REDIRECT_URI = new URL("?assets=oauth/redirect.html", location.href).toString();

async function reinitOAuth() {
  if (!window.RegosOAuthSDK) return;

  try {
    // Если SDK поддерживает destroy — очищаем предыдущую инициализацию
    window.RegosOAuthSDK.destroy?.();
  } catch (_) {}

  // Инициализация с текущим языком
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
    onData: (user, access_token) => {
      // при необходимости можем сохранить токен в ctx
      ctx.currentUser = user || null;
      ctx.accessToken = access_token || null;
    },
    onLogout: () => {
      ctx.currentUser = null;
      ctx.accessToken = null;
    },
    onError: (err) => console.error("[REGOS OAuth] error:", err?.message || err),
  });
}

// Стартуем OAuth (после initI18n, чтобы язык корректно выставился)
await reinitOAuth();

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
