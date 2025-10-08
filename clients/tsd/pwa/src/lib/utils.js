export function esc(value) {
  if (value == null) return '';
  return String(value).replace(/[&<>"']/g, (m) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[m]);
}

export function fmtNum(value, options = {}) {
  const v = Number(value ?? 0);
  if (!Number.isFinite(v)) return '0';
  return v.toLocaleString('ru-RU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options
  });
}

export function fmtMoney(value, locale = 'ru-RU', currency = 'UZS') {
  const v = Number(value ?? 0);
  return v.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    currency,
    style: 'currency'
  });
}

export function toNumber(value) {
  if (value == null || value === '') return 0;
  const normalized = String(value).replace(',', '.');
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function unixToLocal(ts) {
  if (!ts) return '';
  const d = new Date(Number(ts) * 1000);
  const pad = (n) => String(n).padStart(2, '0');
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
