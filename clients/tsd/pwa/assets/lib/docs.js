// views/docs.js — без import; получает ctx
let docsPage = 1;
let docsTotalPages = 1;
let docsQuery = "";

// локальная помощница: перевод с запасным значением
function tt(ctx, key, fallback) {
  const s = ctx.t(key);
  return s === key ? (fallback ?? key) : s;
}

export async function screenDocs(ctx, page = 1, queryStr = "") {
  await ctx.loadView("docs");
  docsPage = Math.max(1, page);
  docsQuery = queryStr;

  // --- Заголовок + кнопка Домой слева ---
  const titleEl = ctx.$("docs-title");
  if (titleEl) {
    // обёртка вокруг заголовка (создаём один раз)
    let wrap = titleEl.closest(".row");
    if (!wrap || !wrap.classList.contains("row-start")) {
      // создаём новую обёртку row row-start
      const newWrap = document.createElement("div");
      newWrap.className = "row row-start";
      titleEl.parentNode.insertBefore(newWrap, titleEl);
      newWrap.appendChild(titleEl);
      wrap = newWrap;
    }
    // кнопка Домой (создаём один раз)
    let btnHome = ctx.$("btn-docs-home");
    if (!btnHome) {
      btnHome = document.createElement("button");
      btnHome.id = "btn-docs-home";
      btnHome.className = "icon-btn";
      const homeLabel = tt(ctx, "nav.home", "Главная");
      btnHome.title = homeLabel;
      btnHome.setAttribute("aria-label", homeLabel);
      btnHome.innerHTML = `<i class="fa-solid fa-house"></i>`;
      btnHome.onclick = () => { location.hash = "#/"; };
      wrap.insertBefore(btnHome, titleEl);
    }
  }

  // Заголовки и подписи через i18n
  if (titleEl) titleEl.textContent = ctx.t("docs.title");

  const search = ctx.$("search-docs");
  const btnRefresh = ctx.$("btn-docs-refresh");

  if (search) {
    search.placeholder = ctx.t("docs.search.placeholder");
    search.value = docsQuery;
    // Поиск по Enter
    search.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        docsQuery = e.target.value.trim();
        screenDocs(ctx, 1, docsQuery);
      }
    }, { once: true }); // предотвратить мульти-подписки при повторных рендерах
  }

  if (btnRefresh) {
    const label = ctx.t("docs.refresh");
    btnRefresh.className = "btn icon ghost"; // сделать иконкой
    btnRefresh.innerHTML = `<i class="fa-solid fa-rotate-right"></i>`;
    btnRefresh.title = label;
    btnRefresh.setAttribute("aria-label", label);
    btnRefresh.onclick = () => screenDocs(ctx, docsPage, docsQuery);
  }

  const btnPrev = ctx.$("prev-page");
  const btnNext = ctx.$("next-page");
  if (btnPrev) btnPrev.textContent = tt(ctx, "nav.back", "Назад");
  if (btnNext) btnNext.textContent = tt(ctx, "nav.next", "Вперёд");

  // init UI
  const pageInd = ctx.$("page-indicator");
  if (pageInd) pageInd.textContent = `${docsPage} / ...`;

  const list = ctx.$("docs-list");
  if (list) list.innerHTML = `<div class="muted">${ctx.t("common.loading")}</div>`;

  // handlers пагинации
  if (btnPrev) btnPrev.onclick = () => { if (docsPage > 1) screenDocs(ctx, docsPage - 1, docsQuery); };
  if (btnNext) btnNext.onclick = () => { if (docsPage < docsTotalPages) screenDocs(ctx, docsPage + 1, docsQuery); };

  // запрос
  const pageSize = 20;
  const { data } = await ctx.api("purchase_list", { page: docsPage, page_size: pageSize, query: docsQuery });

  const items = (data?.result?.items) || [];
  const hasMore = items.length === pageSize;
  docsTotalPages = hasMore ? (docsPage + 1) : docsPage;

  if (pageInd) pageInd.textContent = `${docsPage} / ${docsTotalPages}`;
  renderDocsRaw(ctx, items);
}

function renderDocsRaw(ctx, items) {
  const list = ctx.$("docs-list");
  if (!list) return;

  if (!items.length) {
    list.innerHTML = `<div class="muted">${ctx.t("common.nothing")}</div>`;
    return;
  }
  list.innerHTML = "";

  items.forEach((d) => {
    const id = d.id;
    const code = d.code || id;
    const supplier = d.partner?.name ?? "";
    const dateStr = ctx.unixToLocal(d.date);

    const statusKey = d.performed ? "docs.status.performed" : "docs.status.new";
    let status = ctx.t(statusKey);
    if (d.blocked) status += ` • ${ctx.t("docs.status.blocked")}`;

    const amount = new Intl.NumberFormat(ctx.getLocale?.() || "ru", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(Number(d.amount ?? 0));
    const currency = d.currency?.code_chr ?? "UZS";

    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><strong>${ctx.esc(code)}</strong></div>
          <div class="muted">${ctx.esc(supplier)}</div>
        </div>
        <div class="text-right">
          <div class="pill">${ctx.esc(status)}</div>
          <div class="muted mt-4">${ctx.esc(dateStr)}</div>
          <div class="muted mt-4">${amount} ${ctx.esc(currency)}</div>
        </div>
      </div>
    `;
    el.onclick = () => { location.hash = `#/doc/${id}`; };
    list.appendChild(el);
  });
}
