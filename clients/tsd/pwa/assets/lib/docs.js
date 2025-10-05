// views/docs.js — без import; получает ctx
let docsPage = 1;
let docsTotalPages = 1;
let docsQuery = "";

export async function screenDocs(ctx, page=1, queryStr="") {
  await ctx.loadView("docs");
  docsPage = Math.max(1, page);
  docsQuery = queryStr;

  ctx.$("page-indicator").textContent = `${docsPage} / ...`;
  ctx.$("docs-list").innerHTML = `<div class="muted">Загрузка...</div>`;

  ctx.$("btn-docs-refresh").onclick = ()=>screenDocs(ctx, docsPage, docsQuery);
  ctx.$("search-docs").value = docsQuery;
  ctx.$("search-docs").addEventListener("keydown", e => {
    if (e.key==="Enter"){
      docsQuery=e.target.value.trim();
      screenDocs(ctx, 1, docsQuery);
    }
  });
  ctx.$("prev-page").onclick = ()=> { if (docsPage>1) screenDocs(ctx, docsPage-1, docsQuery); };
  ctx.$("next-page").onclick = ()=> { if (docsPage<docsTotalPages) screenDocs(ctx, docsPage+1, docsQuery); };

  const pageSize = 20;
  const { data } = await ctx.api("purchase_list", { page: docsPage, page_size: pageSize, query: docsQuery });

  const items = (data?.result?.items) || [];
  const hasMore = items.length === pageSize;
  docsTotalPages = hasMore ? (docsPage + 1) : docsPage;
  ctx.$("page-indicator").textContent = `${docsPage} / ${docsTotalPages}`;

  renderDocsRaw(ctx, items);
}

function renderDocsRaw(ctx, items){
  const list = ctx.$("docs-list");
  if (!items.length) { list.innerHTML = `<div class="muted">Ничего не найдено</div>`; return; }
  list.innerHTML = "";

  items.forEach(d => {
    const id = d.id;
    const code = d.code || id;
    const supplier = d.partner?.name ?? "";
    const dateStr = ctx.unixToLocal(d.date);
    const status = (d.performed ? "проведён" : "новый") + (d.blocked ? " • блок." : "");
    const amount = Number(d.amount ?? 0).toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const currency = d.currency?.code_chr ?? "UZS";

    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><strong>${ctx.esc(code)}</strong></div>
          <div class="muted">${ctx.esc(supplier)}</div>
        </div>
        <div style="text-align:right">
          <div class="pill">${ctx.esc(status)}</div>
          <div class="muted" style="margin-top:4px">${ctx.esc(dateStr)}</div>
          <div class="muted" style="margin-top:4px">${amount} ${ctx.esc(currency)}</div>
        </div>
      </div>`;
    el.onclick = () => { location.hash = `#/doc/${id}`; };
    list.appendChild(el);
  });
}
