// views/docs.js
import { api } from "./?assets=lib/api.js";
import { loadView, $, esc, unixToLocal } from "./?assets=lib/utils.js";

let docsPage = 1;
let docsTotalPages = 1;
let docsQuery = "";

export async function screenDocs(page=1, queryStr="") {
  await loadView("docs");
  docsPage = Math.max(1, page);
  docsQuery = queryStr;

  $("page-indicator").textContent = `${docsPage} / ...`;
  $("docs-list").innerHTML = `<div class="muted">Загрузка...</div>`;

  $("btn-docs-refresh").onclick = ()=>screenDocs(docsPage, docsQuery);
  $("search-docs").value = docsQuery;
  $("search-docs").addEventListener("keydown", e => {
    if (e.key==="Enter"){
      docsQuery=e.target.value.trim();
      screenDocs(1, docsQuery);
    }
  });
  $("prev-page").onclick = ()=> { if (docsPage>1) screenDocs(docsPage-1, docsQuery); };
  $("next-page").onclick = ()=> { if (docsPage<docsTotalPages) screenDocs(docsPage+1, docsQuery); };

  const pageSize = 20;
  const { data } = await api("purchase_list", { page: docsPage, page_size: pageSize, query: docsQuery });

  const items = (data?.result?.items) || [];
  const hasMore = items.length === pageSize;
  docsTotalPages = hasMore ? (docsPage + 1) : docsPage;
  $("page-indicator").textContent = `${docsPage} / ${docsTotalPages}`;

  renderDocsRaw(items);
}

function renderDocsRaw(items){
  const list = $("docs-list");
  if (!items.length) { list.innerHTML = `<div class="muted">Ничего не найдено</div>`; return; }
  list.innerHTML = "";

  items.forEach(d => {
    const id = d.id;
    const code = d.code || id;
    const supplier = d.partner?.name ?? "";
    const dateStr = unixToLocal(d.date);
    const status = (d.performed ? "проведён" : "новый") + (d.blocked ? " • блок." : "");
    const amount = Number(d.amount ?? 0).toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const currency = d.currency?.code_chr ?? "UZS";

    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><strong>${esc(code)}</strong></div>
          <div class="muted">${esc(supplier)}</div>
        </div>
        <div style="text-align:right">
          <div class="pill">${esc(status)}</div>
          <div class="muted" style="margin-top:4px">${esc(dateStr)}</div>
          <div class="muted" style="margin-top:4px">${amount} ${esc(currency)}</div>
        </div>
      </div>`;
    el.onclick = () => { location.hash = `#/doc/${id}`; };
    list.appendChild(el);
  });
}
