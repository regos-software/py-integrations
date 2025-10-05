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

  // Заголовки и подписи через i18n
  ctx.$("docs-title").textContent = ctx.t("docs.title");
  const search = ctx.$("search-docs");
  if (search) search.placeholder = ctx.t("docs.search.placeholder");
  const btnRefresh = ctx.$("btn-docs-refresh");
  if (btnRefresh) btnRefresh.textContent = ctx.t("docs.refresh");

  const btnPrev = ctx.$("prev-page");
  const btnNext = ctx.$("next-page");
  if (btnPrev) btnPrev.textContent = tt(ctx, "nav.back", "Назад");
  if (btnNext) btnNext.textContent = tt(ctx, "nav.next", "Вперёд");

  // init UI
  ctx.$("page-indicator").textContent = `${docsPage} / ...`;
  ctx.$("docs-list").innerHTML = `<div class="muted">${ctx.t("common.loading")}</div>`;

  // handlers
  btnRefresh.onclick = () => screenDocs(ctx, docsPage, docsQuery);
  search.value = docsQuery;
  search.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      docsQuery = e.target.value.trim();
      screenDocs(ctx, 1, docsQuery);
    }
  });
  btnPrev.onclick = () => { if (docsPage > 1) screenDocs(ctx, docsPage - 1, docsQuery); };
  btnNext.onclick = () => { if (docsPage < docsTotalPages) screenDocs(ctx, docsPage + 1, docsQuery); };

  // запрос
  const pageSize = 20;
  const { data } = await ctx.api("purchase_list", { page: docsPage, page_size: pageSize, query: docsQuery });

  const items = (data?.result?.items) || [];
  const hasMore = items.length === pageSize;
  docsTotalPages = hasMore ? (docsPage + 1) : docsPage;
  ctx.$("page-indicator").textContent = `${docsPage} / ${docsTotalPages}`;

  renderDocsRaw(ctx, items);
}

function renderDocsRaw(ctx, items) {
  const list = ctx.$("docs-list");
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
