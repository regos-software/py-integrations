// views/home.js — без import; получает ctx
export async function screenHome(ctx) {
  await ctx.loadView("home");
  ctx.$("ci-label").textContent = ctx.CI || "—";
  ctx.$("btn-start").onclick = () => { location.hash = "#/docs"; };
}
