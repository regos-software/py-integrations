// utils.js (DOM, render, views loader, format)
const viewCache = new Map();

export const $ = (id) => document.getElementById(id);
export const appRoot = () => $("app");

export const out = (v) => { $("out").textContent = typeof v === "string" ? v : JSON.stringify(v, null, 2); };

export async function loadView(name) {
  // относительный запрос -> /external/{ci}?assets=views/NAME.html
  if (!viewCache.has(name)) {
    const r = await fetch(`?assets=views/${name}.html`);
    if (!r.ok) throw new Error(`view ${name} failed`);
    viewCache.set(name, await r.text());
  }
  appRoot().innerHTML = viewCache.get(name);
}

export function esc(s){ return (s==null?"":String(s)).replace(/[&<>"']/g, m=>({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[m])); }
export function fmtNum(n){ return (n==null||isNaN(n))?"0":String(n); }
export function fmtMoney(n){ const v = Number(n||0); return v.toLocaleString("ru-RU",{minimumFractionDigits:2, maximumFractionDigits:2}); }
export function toNumber(v){ const s=String(v||"").replace(",","."); const n=parseFloat(s); return isNaN(n)?0:n; }
export function unixToLocal(ts){
  if(!ts) return "";
  const d = new Date(ts * 1000);
  const p = n => String(n).padStart(2,"0");
  return `${p(d.getDate())}.${p(d.getMonth()+1)}.${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
export function tickClock(){
  const d = new Date(), p=n=>String(n).padStart(2,"0");
  const lbl = $("now");
  if (lbl) lbl.textContent = `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}
