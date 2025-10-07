const SUPPORTED = ["ru", "en", "uz"];
const STORAGE_KEY = "tsd_locale";

function normLocale(l) {
  if (!l) return "ru";
  const s = String(l).toLowerCase();
  for (const x of SUPPORTED) if (s === x || s.startsWith(x + "-")) return x;
  return "ru";
}

let locale = "ru";
let messages = {};

async function loadMessages(lc) {
  const url = `?assets=i18n/${lc}.json`;
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`i18n: ${lc} not found`);
  messages = await res.json();
  document.documentElement.lang = lc;
}

export async function initI18n() {
  const urlLc = new URLSearchParams(location.search).get("lang");
  const saved = localStorage.getItem(STORAGE_KEY);
  const nav = (navigator.languages && navigator.languages[0]) || navigator.language || "ru";
  locale = normLocale(urlLc || saved || nav);
  await loadMessages(locale);
}

export function t(key, vars) {
  let s = messages[key] ?? key;
  if (vars && typeof vars === "object") {
    for (const [k, v] of Object.entries(vars)) {
      s = s.replaceAll(`{${k}}`, String(v));
    }
  }
  return s;
}

export function getLocale() { return locale; }

export async function setLocale(next) {
  const lc = normLocale(next);
  if (lc === locale) return;
  await loadMessages(lc);
  locale = lc;
  localStorage.setItem(STORAGE_KEY, lc);
}

export const fmt = {
  money(v, currency = "UZS") {
    return new Intl.NumberFormat(locale, { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(v || 0));
  },
  number(v, opt = {}) {
    return new Intl.NumberFormat(locale, opt).format(Number(v || 0));
  },
  unix(ts) {
    if (!ts) return "";
    return new Intl.DateTimeFormat(locale, { year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit" })
      .format(new Date(Number(ts) * 1000));
  }
};
