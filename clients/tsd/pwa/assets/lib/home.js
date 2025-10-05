// views/home.js
import { loadView, $ } from "./?assets=lib/utils.js";
import { CI } from "./?assets=lib/api.js";

export async function screenHome() {
  await loadView("home");
  $("ci-label").textContent = CI || "—";
  $("btn-start").onclick = () => { location.hash = "#/docs"; };
}
