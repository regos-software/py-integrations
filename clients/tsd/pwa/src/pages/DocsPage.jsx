import React, { useCallback, useEffect, useMemo, useState } from "react";
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
  mutedTextClass,
  sectionClass,
} from "../lib/ui";
import { cn } from "../lib/utils";

const PAGE_SIZE = 20;

export default function DocsPage() {
  const { api, unixToLocal, setAppTitle } = useApp();
  const { t, locale } = useI18n();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const page = Math.max(
    1,
    Number.parseInt(searchParams.get("page") || "1", 10) || 1
  );
  const query = searchParams.get("q") || "";

  const [inputValue, setInputValue] = useState(query);
  const [items, setItems] = useState([]);
  const [totalPages, setTotalPages] = useState(page);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const debouncedSearch = useDebouncedValue(inputValue);

  useEffect(() => {
    setInputValue(query);
  }, [query]);

  useEffect(() => {
    const title = t("docs.title") || "Документы закупки";
    setAppTitle(`${t("app.title") || "TSD"} • ${title}`);
  }, [locale, setAppTitle, t]);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const searchTerm = debouncedSearch.trim();
      const { data } = await api("purchase_list", {
        page,
        page_size: PAGE_SIZE,
        query: searchTerm,
      });
      const received = data?.result?.items || [];
      const total = data?.result?.total;
      setItems(received);
      if (typeof total === "number") {
        setTotalPages(Math.max(1, Math.ceil(total / PAGE_SIZE)));
      } else {
        const hasMore = received.length === PAGE_SIZE;
        setTotalPages(hasMore ? page + 1 : page);
      }
    } catch (err) {
      setError(err);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [api, page, debouncedSearch]);

  const updateSearchParams = useCallback(
    (nextPage, nextQuery = query) => {
      const normalizedQuery = nextQuery.trim();
      if (nextPage === page && normalizedQuery === query.trim()) {
        return;
      }

      const params = new URLSearchParams();
      if (nextPage > 1) params.set("page", String(nextPage));
      if (normalizedQuery) params.set("q", normalizedQuery);
      setSearchParams(params, { replace: true });
    },
    [page, query, setSearchParams]
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

  const statusLabel = useCallback(
    (doc) => {
      const normalize = (key, fallback) => {
        const value = t(key);
        return value === key ? fallback : value;
      };
      const parts = [];
      parts.push(
        doc.performed
          ? normalize("docs.status.performed", "проведён")
          : normalize("docs.status.new", "новый")
      );
      if (doc.blocked) parts.push(normalize("docs.status.blocked", "блок."));
      return parts.filter(Boolean).join(" • ");
    },
    [t]
  );

  const nothingLabel = useMemo(
    () => t("common.nothing") || "Ничего не найдено",
    [t]
  );
  const backLabel = useMemo(() => {
    const value = t("nav.back");
    return value === "nav.back" ? "Назад" : value;
  }, [t]);
  const nextLabel = useMemo(() => {
    const value = t("nav.next");
    return value === "nav.next" ? "Вперёд" : value;
  }, [t]);

  return (
    <section className={sectionClass()} id="docs">
      <div className="flex items-center gap-3">
        <h1
          className="text-2xl font-semibold text-slate-900 dark:text-slate-50"
          id="docs-title"
        >
          {t("docs.title") || "Документы закупки"}
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
          placeholder={
            t("docs.search.placeholder") || "Поиск по номеру / поставщику..."
          }
          onChange={(event) => setInputValue(event.target.value)}
          className={inputClass("flex-1")}
        />
        <button
          id="btn-docs-refresh"
          type="button"
          className={iconButtonClass({ variant: "ghost" })}
          onClick={fetchDocs}
          aria-label={t("docs.refresh") || "Обновить"}
          title={t("docs.refresh") || "Обновить"}
        >
          <i className="fa-solid fa-rotate-right" aria-hidden="true" />
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
          items.map((doc) => (
            <button
              key={doc.id}
              type="button"
              className={cardClass(
                "flex items-start justify-between gap-4 text-left transition hover:-translate-y-0.5 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2"
              )}
              onClick={() => navigate(`/doc/${doc.id}`)}
            >
              <div className="flex min-w-0 flex-col gap-1">
                <strong className="text-base font-semibold text-slate-900 dark:text-slate-50">
                  {doc.code || doc.id}
                </strong>
                <span className={cn(mutedTextClass(), "truncate")}>
                  {doc.partner?.name || ""}
                </span>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1 text-right">
                <span className={mutedTextClass()}>
                  {unixToLocal(doc.date)}
                </span>
                <span className={mutedTextClass()}>{statusLabel(doc)}</span>
              </div>
            </button>
          ))}
      </div>
    </section>
  );
}
