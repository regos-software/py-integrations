import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import useDebouncedValue from "../hooks/useDebouncedValue.js";

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
    <section className="stack" id="docs">
      <div className="row row-start">
        <h1 id="docs-title">{t("docs.title") || "Документы закупки"}</h1>
      </div>

      <form className="input-row" onSubmit={handleSearchSubmit} role="search">
        <input
          id="search-docs"
          type="search"
          value={inputValue}
          placeholder={
            t("docs.search.placeholder") || "Поиск по номеру / поставщику..."
          }
          onChange={(event) => setInputValue(event.target.value)}
        />
        <button
          id="btn-docs-refresh"
          type="button"
          className="btn icon ghost"
          onClick={fetchDocs}
          aria-label={t("docs.refresh") || "Обновить"}
          title={t("docs.refresh") || "Обновить"}
        >
          <i className="fa-solid fa-rotate-right" aria-hidden="true" />
        </button>
      </form>

      <div className="row">
        <span id="page-indicator" className="muted">
          {page} / {totalPages}
        </span>
        <div className="cluster">
          <button
            id="prev-page"
            type="button"
            className="btn small ghost"
            onClick={handlePrev}
            disabled={page <= 1}
          >
            {backLabel}
          </button>
          <button
            id="next-page"
            type="button"
            className="btn small ghost"
            onClick={handleNext}
            disabled={page >= totalPages}
          >
            {nextLabel}
          </button>
        </div>
      </div>

      <div id="docs-list" className="list" aria-live="polite">
        {loading && (
          <div className="muted">{t("common.loading") || "Загрузка..."}</div>
        )}
        {!loading && error && (
          <div className="muted">{String(error.message || error)}</div>
        )}
        {!loading && !error && items.length === 0 && (
          <div className="muted">{nothingLabel}</div>
        )}
        {!loading &&
          !error &&
          items.map((doc) => (
            <button
              key={doc.id}
              type="button"
              className="item"
              onClick={() => navigate(`/doc/${doc.id}`)}
            >
              <div className="row">
                <div className="stack muted">
                  <strong>{doc.code || doc.id}</strong>
                  <span className="muted truncate">
                    {doc.partner?.name || ""}
                  </span>
                </div>
                <div className="stack text-right muted">
                  <span>{unixToLocal(doc.date)}</span>
                  <span>{statusLabel(doc)}</span>
                </div>
              </div>
            </button>
          ))}
      </div>
    </section>
  );
}
