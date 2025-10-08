const CI = (() => {
  const segments = window.location.pathname.split('/').filter(Boolean);
  const fromPath = segments[0] === 'external' ? segments[1] : null;
  return (window.__CI__ || new URLSearchParams(window.location.search).get('ci') || fromPath || '').trim();
})();

function getBasePath() {
  const segments = window.location.pathname.split('/').filter(Boolean);
  if (segments[0] === 'external' && segments[1]) {
    return `/external/${segments[1]}/`;
  }
  return window.location.pathname.endsWith('/') ? window.location.pathname : `${window.location.pathname}/`;
}

const BASE = getBasePath();

export { CI };

export function assetUrl(path) {
  return new URL(`?assets=${path}`, window.location.href).toString();
}

export async function api(action, params = {}) {
  const url = `${BASE}external`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, params })
  });

  let data = {};
  try {
    data = await response.json();
  } catch (err) {
    console.warn('[api] failed to parse json', err);
  }
  return { ok: response.ok, status: response.status, data };
}

export function registerSW() {
  if (!('serviceWorker' in navigator)) return;

  const swUrl = new URL('?pwa=sw', window.location.href).toString();
  navigator.serviceWorker.register(swUrl, { scope: BASE }).catch((err) => {
    console.warn('[sw] register failed', err);
  });
}

export function isStandalone() {
  return (
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  );
}
