import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { useApp } from './AppContext.jsx';

const SUPPORTED = ['ru', 'en', 'uz'];
const STORAGE_KEY = 'tsd_locale';

function normLocale(locale) {
  if (!locale) return 'ru';
  const lower = String(locale).toLowerCase();
  const direct = SUPPORTED.find((lang) => lower === lang || lower.startsWith(`${lang}-`));
  return direct || 'ru';
}

function resolveInitialLocale() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get('lang');
  const stored = window.localStorage.getItem(STORAGE_KEY);
  const nav = (navigator.languages && navigator.languages[0]) || navigator.language || 'ru';
  return normLocale(fromQuery || stored || nav);
}

async function fetchMessages(assetUrl, locale) {
  const url = assetUrl(`i18n/${locale}.json`);
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) {
    throw new Error(`i18n: unable to load ${locale}`);
  }
  return res.json();
}

const I18nContext = createContext({
  locale: 'ru',
  t: (key) => key,
  setLocale: async () => {},
  fmt: {
    money: (v) => v,
    number: (v) => v,
    unix: (ts) => ts
  }
});

export function I18nProvider({ children }) {
  const { assetUrl, setAppTitle } = useApp();
  const [locale, setLocale] = useState(() => resolveInitialLocale());
  const [messages, setMessages] = useState({});
  const [ready, setReady] = useState(false);

  const load = useCallback(async (lc) => {
    const normalized = normLocale(lc);
    const loaded = await fetchMessages(assetUrl, normalized);
    setMessages(loaded);
    setLocale(normalized);
    document.documentElement.lang = normalized;
    window.localStorage.setItem(STORAGE_KEY, normalized);
    const title = loaded['app.title'] || 'TSD';
    setAppTitle(title);
    document.dispatchEvent(new CustomEvent('i18n:change'));
  }, [assetUrl, setAppTitle]);

  useEffect(() => {
    load(locale).finally(() => setReady(true));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const translate = useCallback((key, vars) => {
    const template = messages[key];
    if (!template) return key;
    if (!vars) return template;
    return Object.entries(vars).reduce(
      (acc, [k, v]) => acc.replaceAll(`{${k}}`, String(v)),
      template
    );
  }, [messages]);

  const fmt = useMemo(() => ({
    money(value, currency = 'UZS') {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency,
        maximumFractionDigits: 2,
        minimumFractionDigits: 2
      }).format(Number(value || 0));
    },
    number(value, options = {}) {
      return new Intl.NumberFormat(locale, options).format(Number(value || 0));
    },
    unix(ts) {
      if (!ts) return '';
      return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }).format(new Date(Number(ts) * 1000));
    }
  }), [locale]);

  const value = useMemo(() => ({
    locale,
    t: translate,
    setLocale: load,
    fmt
  }), [fmt, load, locale, translate]);

  if (!ready) {
    return null;
  }

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = React.useContext(I18nContext);
  if (!ctx) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return ctx;
}
