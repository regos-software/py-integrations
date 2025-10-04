// токен приходим из window.__CI__ (вставляет backend) или из ?ci=
const CI = window.__CI__ || new URLSearchParams(location.search).get("ci") || "";

const out = (id, value) => {
  const el = document.getElementById(id);
  if (el) el.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
};

// регистрация SW (файл отдаётся по ?pwa=sw, scope = /clients/)
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/clients/tsd?pwa=sw", { scope: "/clients/" })
    .catch(err => console.warn("SW register failed", err));
}

// универсальный вызов backend API
async function callApi(action, params = {}) {
  const res = await fetch("/clients/tsd/external", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Connected-Integration-Id": CI
    },
    body: JSON.stringify({ action, params })
  });
  let data = {};
  try { data = await res.json(); } catch {}
  return { ok: res.ok, status: res.status, data };
}

// Демо UI-логика
window.addEventListener("DOMContentLoaded", () => {
  out("token", CI || "—");

  const pingBtn = document.getElementById("ping");
  if (pingBtn) {
    pingBtn.addEventListener("click", async () => {
      pingBtn.disabled = true;
      const res = await callApi("ping");
      out("out", res);
      pingBtn.disabled = false;
    });
  }

  // пример формы
  const form = document.getElementById("demo-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = form.querySelector("textarea[name=text]")?.value || "";
      const res = await callApi("send", { text });
      out("out", res);
    });
  }
});
