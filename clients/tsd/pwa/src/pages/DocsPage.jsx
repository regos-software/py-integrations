import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import useDebouncedValue from "../hooks/useDebouncedValue.js";
import {
  buttonClass,
  cardClass,
  iconButtonClass,
  inputClass,
  listClass,
  labelClass,
  mutedTextClass,
  sectionClass,
} from "../lib/ui";
import { cn } from "../lib/utils";
import {
  DEFAULT_PAGE_SIZE,
  getDocDefinition,
} from "../config/docDefinitions.js";

const createDefaultFilters = () => ({
  performed: false,
  blocked: null,
  deleted_mark: false,
  stock_ids: [],
  start_date: "",
  end_date: "",
});

export default function DocsPage({ definition: definitionProp }) {
  const { api, unixToLocal, setAppTitle } = useApp();
  const { t, locale, fmt } = useI18n();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const page = Math.max(
    1,
    Number.parseInt(searchParams.get("page") || "1", 10) || 1
  );
  const query = searchParams.get("q") || "";
  const typeParam = searchParams.get("type") || undefined;

  const docDefinition = useMemo(
    () => definitionProp || getDocDefinition(typeParam),
    [definitionProp, typeParam]
  );

  const pageSize = docDefinition?.list?.pageSize || DEFAULT_PAGE_SIZE;

  const [inputValue, setInputValue] = useState(query);
  const [items, setItems] = useState([]);
  const [totalPages, setTotalPages] = useState(page);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const debouncedSearch = useDebouncedValue(inputValue);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filters, setFilters] = useState(() => createDefaultFilters());
  const [filtersDraft, setFiltersDraft] = useState(() =>
    createDefaultFilters()
  );
  const [stocks, setStocks] = useState([]);
  const [stocksLoading, setStocksLoading] = useState(false);
  const [stocksError, setStocksError] = useState(null);

  useEffect(() => {
    setInputValue(query);
  }, [query]);

  const resetFiltersOnTypeRef = useRef(true);

  useEffect(() => {
    if (!docDefinition?.key) return;
    if (resetFiltersOnTypeRef.current) {
      resetFiltersOnTypeRef.current = false;
      return;
    }
    setFilters(createDefaultFilters());
    setFiltersDraft(createDefaultFilters());
  }, [docDefinition?.key]);

  useEffect(() => {
    const titleKey = docDefinition?.labels?.title || "docs.title";
    const translated = t(titleKey);
    const title =
      translated === titleKey
        ? docDefinition?.labels?.titleFallback || "Документы"
        : translated;
    setAppTitle(`${t("app.title") || "TSD"} • ${title}`);
  }, [docDefinition, locale, setAppTitle, t]);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const searchTerm = debouncedSearch.trim();
      const listDescriptor = docDefinition.list;
      const params = listDescriptor.buildParams({
        page,
        pageSize,
        search: searchTerm,
        filters,
      });
      const { data } = await api(listDescriptor.action, params);
      const { items: rawItems = [], total = 0 } =
        listDescriptor.transformResponse(data) || {};

      const mapped = rawItems.map((doc) =>
        listDescriptor.mapItem(doc, { t, fmt, unixToLocal })
      );

      setItems(mapped);
      setTotalPages(Math.max(1, Math.ceil(total / pageSize)));
    } catch (err) {
      setError(err);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [
    api,
    docDefinition,
    page,
    pageSize,
    debouncedSearch,
    filters,
    fmt,
    t,
    unixToLocal,
  ]);

  const updateSearchParams = useCallback(
    (nextPage, nextQuery = query) => {
      const normalizedQuery = nextQuery.trim();
      if (nextPage === page && normalizedQuery === query.trim()) {
        return;
      }

      const params = new URLSearchParams();
      if (nextPage > 1) params.set("page", String(nextPage));
      if (normalizedQuery) params.set("q", normalizedQuery);
      if (typeParam) params.set("type", typeParam);
      setSearchParams(params, { replace: true });
    },
    [page, query, setSearchParams, typeParam]
  );

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  useEffect(() => {
    const trimmed = debouncedSearch.trim();
    if (trimmed === query) return;
    updateSearchParams(1, trimmed);
  }, [debouncedSearch, query, updateSearchParams]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    updateSearchParams(1, inputValue.trim());
  };

  const handlePrev = () => {
    if (page > 1) updateSearchParams(page - 1, query);
  };

  const handleNext = () => {
    if (page < totalPages) updateSearchParams(page + 1, query);
  };

  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.performed !== false) count += 1;
    if (filters.blocked !== null && filters.blocked !== undefined) count += 1;
    if (filters.deleted_mark !== false) count += 1;
    if (Array.isArray(filters.stock_ids) && filters.stock_ids.length > 0)
      count += 1;
    if (filters.start_date) count += 1;
    if (filters.end_date) count += 1;
    return count;
  }, [filters]);

  const fetchStocks = useCallback(async () => {
    if (stocksLoading || stocks.length > 0) return;
    setStocksLoading(true);
    setStocksError(null);
    try {
      const { data } = await api("references.stock.get", {
        deleted_mark: false,
        sort_orders: [{ column: "Name", direction: "asc" }],
      });
      if (!data) {
        throw new Error(
          data?.error?.message ||
            t("docs.filters.stocks_error") ||
            "Не удалось загрузить склады"
        );
      }
      setStocks(
        data?.result?.map((stock) => ({
          id: Number(stock.id ?? stock.ID ?? stock.code ?? 0),
          name: stock.name || stock.Name || `#${stock.id || stock.ID}`,
        }))
      );
    } catch (err) {
      setStocksError(err);
      setStocks([]);
    } finally {
      setStocksLoading(false);
    }
  }, [api, stocks?.length, stocksLoading, t]);

  const handleOpenFilters = () => {
    setFiltersDraft((prev) => ({
      ...createDefaultFilters(),
      ...filters,
      stock_ids: Array.isArray(filters.stock_ids)
        ? filters.stock_ids.map((id) => Number(id))
        : [],
    }));
    setFiltersOpen(true);
    fetchStocks();
  };

  const handleCloseFilters = () => {
    setFiltersOpen(false);
  };

  const handleDraftChange = (field, value) => {
    setFiltersDraft((prev) => ({ ...prev, [field]: value }));
  };

  const handleDraftSelectTriState = (field) => (event) => {
    const value = event.target.value;
    const nextValue = value === "any" ? null : value === "true" ? true : false;
    handleDraftChange(field, nextValue);
  };

  const handleDraftStockChange = (event) => {
    const selected = Array.from(event.target.selectedOptions || []).map((opt) =>
      Number(opt.value)
    );
    handleDraftChange(
      "stock_ids",
      selected.filter((id) => !Number.isNaN(id))
    );
  };

  const handleFiltersClear = () => {
    const cleared = createDefaultFilters();
    setFiltersDraft(cleared);
  };

  const handleFiltersApply = (event) => {
    if (event) event.preventDefault();
    setFilters((prev) => ({
      ...prev,
      ...filtersDraft,
      stock_ids: Array.isArray(filtersDraft.stock_ids)
        ? filtersDraft.stock_ids.filter((id) => !Number.isNaN(Number(id)))
        : [],
    }));
    setFiltersOpen(false);
    updateSearchParams(1, query);
  };

  const nothingLabel = useMemo(() => {
    const key = docDefinition?.labels?.nothing || "common.nothing";
    const value = t(key);
    return value === key ? "Ничего не найдено" : value;
  }, [docDefinition, t]);
  const backLabel = useMemo(() => {
    const value = t("nav.back");
    return value === "nav.back" ? "Назад" : value;
  }, [t]);
  const nextLabel = useMemo(() => {
    const value = t("nav.next");
    return value === "nav.next" ? "Вперёд" : value;
  }, [t]);

  const filtersTitle = useMemo(() => {
    const key = docDefinition?.labels?.filtersTitle || "docs.filters.title";
    const value = t(key);
    return value === key ? "Фильтры" : value;
  }, [docDefinition, t]);
  const filtersApplyLabel = useMemo(() => {
    const value = t("docs.filters.apply");
    return value === "docs.filters.apply" ? "Применить" : value;
  }, [t]);
  const filtersClearLabel = useMemo(() => {
    const value = t("docs.filters.clear");
    return value === "docs.filters.clear" ? "Сбросить" : value;
  }, [t]);
  const filtersCancelLabel = useMemo(() => {
    const value = t("common.cancel");
    return value === "common.cancel" ? "Отмена" : value;
  }, [t]);

  return (
    <section className={sectionClass()} id="docs">
      <div className="flex items-center gap-3">
        <h1
          className="text-2xl font-semibold text-slate-900 dark:text-slate-50"
          id="docs-title"
        >
          {(() => {
            const key = docDefinition?.labels?.title || "docs.title";
            const value = t(key);
            if (value === key) {
              return (
                docDefinition?.labels?.titleFallback || "Документы закупки"
              );
            }
            return value;
          })()}
        </h1>
      </div>

      <form
        className="flex gap-3 flex-row sm:items-center"
        onSubmit={handleSearchSubmit}
        role="search"
      >
        <input
          id="search-docs"
          type="search"
          value={inputValue}
          placeholder={(() => {
            const key =
              docDefinition?.labels?.searchPlaceholder ||
              "docs.search.placeholder";
            const value = t(key);
            if (value === key) {
              return (
                docDefinition?.labels?.searchPlaceholderFallback ||
                "Поиск по номеру / поставщику..."
              );
            }
            return value;
          })()}
          onChange={(event) => setInputValue(event.target.value)}
          className={inputClass("flex-1")}
        />
        <button
          id="btn-docs-refresh"
          type="button"
          className={iconButtonClass({ variant: "ghost" })}
          onClick={fetchDocs}
          aria-label={(() => {
            const key = docDefinition?.labels?.refresh || "docs.refresh";
            const value = t(key);
            return value === key ? "Обновить" : value;
          })()}
          title={(() => {
            const key = docDefinition?.labels?.refresh || "docs.refresh";
            const value = t(key);
            return value === key ? "Обновить" : value;
          })()}
        >
          <i className="fa-solid fa-rotate-right" aria-hidden="true" />
        </button>
        <button
          id="btn-docs-filters"
          type="button"
          className={buttonClass({
            variant: activeFiltersCount > 0 ? "primary" : "ghost",
            size: "sm",
          })}
          onClick={handleOpenFilters}
        >
          <i className="fa-solid fa-filter" aria-hidden="true" />
          {activeFiltersCount > 0 ? (
            <span className="ml-1 inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-white/80 px-2 text-xs font-semibold text-slate-900">
              {activeFiltersCount}
            </span>
          ) : null}
        </button>
      </form>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <span id="page-indicator" className={mutedTextClass()}>
          {page} / {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <button
            id="prev-page"
            type="button"
            className={buttonClass({ variant: "ghost", size: "sm" })}
            onClick={handlePrev}
            disabled={page <= 1}
          >
            {backLabel}
          </button>
          <button
            id="next-page"
            type="button"
            className={buttonClass({ variant: "ghost", size: "sm" })}
            onClick={handleNext}
            disabled={page >= totalPages}
          >
            {nextLabel}
          </button>
        </div>
      </div>

      <div id="docs-list" className={listClass()} aria-live="polite">
        {loading && (
          <div className={mutedTextClass()}>
            {t("common.loading") || "Загрузка..."}
          </div>
        )}
        {!loading && error && (
          <div className={mutedTextClass()}>
            {String(error.message || error)}
          </div>
        )}
        {!loading && !error && items.length === 0 && (
          <div className={mutedTextClass()}>{nothingLabel}</div>
        )}
        {!loading &&
          !error &&
          items.map((item) => (
            <button
              key={item.id}
              type="button"
              className={cardClass(
                "flex items-start justify-between gap-4 text-left transition hover:-translate-y-0.5 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2"
              )}
              onClick={() => {
                const buildPath =
                  docDefinition?.navigation?.buildDocPath ||
                  ((doc) => `/doc/${doc.id}`);
                navigate(buildPath(item.raw));
              }}
            >
              <div className="flex min-w-0 flex-col gap-1">
                <strong className="text-base font-semibold text-slate-900 dark:text-slate-50">
                  {item.title}
                </strong>
                <span className={cn(mutedTextClass(), "truncate")}>
                  {item.subtitle || ""}
                </span>
                {item.stockLabel ? (
                  <span
                    className={cn(
                      mutedTextClass(),
                      "truncate font-medium text-slate-600 dark:text-slate-200"
                    )}
                    title={item.stockLabel}
                  >
                    {item.stockLabel}
                  </span>
                ) : null}
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1 text-right">
                {item.amountLabel ? (
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {item.amountLabel}
                  </span>
                ) : null}
                <span className={mutedTextClass()}>{item.rightTop}</span>
                <span className={mutedTextClass()}>{item.rightBottom}</span>
              </div>
            </button>
          ))}
      </div>

      {filtersOpen ? (
        <div
          className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-slate-900/70 px-4 py-6"
          role="presentation"
          onClick={handleCloseFilters}
        >
          <div
            className={cardClass(
              "relative mt-6 w-full max-w-lg space-y-5 p-6 shadow-xl"
            )}
            role="dialog"
            aria-modal="true"
            aria-labelledby="docs-filters-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <h2
                id="docs-filters-title"
                className="text-lg font-semibold text-slate-900 dark:text-slate-50"
              >
                {filtersTitle}
              </h2>
              <button
                type="button"
                className={iconButtonClass({ variant: "ghost" })}
                onClick={handleCloseFilters}
                aria-label={filtersCancelLabel}
                title={filtersCancelLabel}
              >
                <i className="fa-solid fa-xmark" aria-hidden="true" />
              </button>
            </div>

            <form className="flex flex-col gap-4" onSubmit={handleFiltersApply}>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-2">
                  <label className={labelClass()} htmlFor="filter-performed">
                    {t("docs.filters.performed") === "docs.filters.performed"
                      ? "Статус проведения"
                      : t("docs.filters.performed")}
                  </label>
                  <select
                    id="filter-performed"
                    className={inputClass()}
                    value={
                      filtersDraft.performed === null ||
                      filtersDraft.performed === undefined
                        ? "any"
                        : filtersDraft.performed
                        ? "true"
                        : "false"
                    }
                    onChange={handleDraftSelectTriState("performed")}
                  >
                    <option value="false">
                      {t("docs.filters.performed.false") ===
                      "docs.filters.performed.false"
                        ? "Только непроведённые"
                        : t("docs.filters.performed.false")}
                    </option>
                    <option value="true">
                      {t("docs.filters.performed.true") ===
                      "docs.filters.performed.true"
                        ? "Только проведённые"
                        : t("docs.filters.performed.true")}
                    </option>
                    <option value="any">
                      {t("docs.filters.any") === "docs.filters.any"
                        ? "Все"
                        : t("docs.filters.any")}
                    </option>
                  </select>
                </div>

                <div className="flex flex-col gap-2">
                  <label className={labelClass()} htmlFor="filter-blocked">
                    {t("docs.filters.blocked") === "docs.filters.blocked"
                      ? "Блокировка"
                      : t("docs.filters.blocked")}
                  </label>
                  <select
                    id="filter-blocked"
                    className={inputClass()}
                    value={
                      filtersDraft.blocked === null ||
                      filtersDraft.blocked === undefined
                        ? "any"
                        : filtersDraft.blocked
                        ? "true"
                        : "false"
                    }
                    onChange={handleDraftSelectTriState("blocked")}
                  >
                    <option value="any">
                      {t("docs.filters.any") === "docs.filters.any"
                        ? "Все"
                        : t("docs.filters.any")}
                    </option>
                    <option value="false">
                      {t("docs.filters.blocked.false") ===
                      "docs.filters.blocked.false"
                        ? "Только неблокированные"
                        : t("docs.filters.blocked.false")}
                    </option>
                    <option value="true">
                      {t("docs.filters.blocked.true") ===
                      "docs.filters.blocked.true"
                        ? "Только блокированные"
                        : t("docs.filters.blocked.true")}
                    </option>
                  </select>
                </div>

                <div className="flex flex-col gap-2">
                  <label className={labelClass()} htmlFor="filter-deleted-mark">
                    {t("docs.filters.deleted_mark") ===
                    "docs.filters.deleted_mark"
                      ? "Удалённые"
                      : t("docs.filters.deleted_mark")}
                  </label>
                  <select
                    id="filter-deleted-mark"
                    className={inputClass()}
                    value={
                      filtersDraft.deleted_mark === null ||
                      filtersDraft.deleted_mark === undefined
                        ? "any"
                        : filtersDraft.deleted_mark
                        ? "true"
                        : "false"
                    }
                    onChange={handleDraftSelectTriState("deleted_mark")}
                  >
                    <option value="false">
                      {t("docs.filters.deleted_mark.false") ===
                      "docs.filters.deleted_mark.false"
                        ? "Без удалённых"
                        : t("docs.filters.deleted_mark.false")}
                    </option>
                    <option value="true">
                      {t("docs.filters.deleted_mark.true") ===
                      "docs.filters.deleted_mark.true"
                        ? "Только удалённые"
                        : t("docs.filters.deleted_mark.true")}
                    </option>
                    <option value="any">
                      {t("docs.filters.any") === "docs.filters.any"
                        ? "Все"
                        : t("docs.filters.any")}
                    </option>
                  </select>
                </div>

                <div className="flex flex-col gap-2">
                  <label className={labelClass()} htmlFor="filter-stock-ids">
                    {t("docs.filters.stocks") === "docs.filters.stocks"
                      ? "Склады"
                      : t("docs.filters.stocks")}
                  </label>
                  <select
                    id="filter-stock-ids"
                    multiple
                    className={inputClass("min-h-[8rem]")}
                    value={filtersDraft.stock_ids.map((id) => String(id))}
                    onChange={handleDraftStockChange}
                    disabled={stocksLoading}
                  >
                    {stocksLoading ? (
                      <option value="loading">
                        {t("common.loading") || "Загрузка..."}
                      </option>
                    ) : stocks.length > 0 ? (
                      stocks.map((stock) => (
                        <option key={stock.id} value={String(stock.id)}>
                          {stock.name || `#${stock.id}`}
                        </option>
                      ))
                    ) : (
                      <option value="empty" disabled>
                        {stocksError
                          ? String(
                              stocksError.message ||
                                t("docs.filters.stocks_error") ||
                                "Не удалось загрузить"
                            )
                          : t("docs.filters.stocks_empty") ===
                            "docs.filters.stocks_empty"
                          ? "Склады не найдены"
                          : t("docs.filters.stocks_empty")}
                      </option>
                    )}
                  </select>
                  {stocksError ? (
                    <span className={mutedTextClass()}>
                      {String(
                        stocksError.message ||
                          t("docs.filters.stocks_error") ||
                          "Не удалось загрузить"
                      )}
                    </span>
                  ) : null}
                  {!stocksLoading && stocks.length === 0 && !stocksError ? (
                    <span className={mutedTextClass()}>
                      {t("docs.filters.stocks_hint") ===
                      "docs.filters.stocks_hint"
                        ? "Выберите склады после загрузки"
                        : t("docs.filters.stocks_hint")}
                    </span>
                  ) : null}
                </div>

                <div className="flex flex-col gap-2">
                  <label className={labelClass()} htmlFor="filter-start-date">
                    {t("docs.filters.start_date") === "docs.filters.start_date"
                      ? "Дата с"
                      : t("docs.filters.start_date")}
                  </label>
                  <input
                    id="filter-start-date"
                    type="date"
                    className={inputClass()}
                    value={filtersDraft.start_date || ""}
                    onChange={(event) =>
                      handleDraftChange("start_date", event.target.value)
                    }
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label className={labelClass()} htmlFor="filter-end-date">
                    {t("docs.filters.end_date") === "docs.filters.end_date"
                      ? "Дата по"
                      : t("docs.filters.end_date")}
                  </label>
                  <input
                    id="filter-end-date"
                    type="date"
                    className={inputClass()}
                    value={filtersDraft.end_date || ""}
                    onChange={(event) =>
                      handleDraftChange("end_date", event.target.value)
                    }
                  />
                </div>
              </div>

              <div className="flex items-center justify-between gap-3">
                <button
                  type="button"
                  className={buttonClass({ variant: "ghost", size: "sm" })}
                  onClick={handleFiltersClear}
                >
                  {filtersClearLabel}
                </button>

                <button
                  type="submit"
                  className={buttonClass({ variant: "primary", size: "sm" })}
                >
                  {filtersApplyLabel}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </section>
  );
}
