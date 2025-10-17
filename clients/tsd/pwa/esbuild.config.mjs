import { build, context } from "esbuild";
import { mkdir } from "node:fs/promises";
import { dirname } from "node:path";

const watch = process.argv.includes("--watch");

async function ensureDir(path) {
  try {
    await mkdir(dirname(path), { recursive: true });
  } catch (err) {
    if (err.code !== "EEXIST") throw err;
  }
}

const outFile = "assets/app.js";
await ensureDir(outFile);

const buildOptions = {
  entryPoints: ["src/main.jsx"],
  outfile: outFile,
  bundle: true,
  format: "esm",
  target: ["es2020"],
  jsx: "automatic",
  sourcemap: true,
  minify: !watch,
  define: {
    "process.env.NODE_ENV": JSON.stringify(
      watch ? "development" : "production"
    ),
  },
  loader: {
    ".svg": "dataurl",
    ".mp3": "dataurl",
  },
  logLevel: "info",
};

if (watch) {
  const ctx = await context(buildOptions);
  await ctx.watch();
  console.log("esbuild watching for changes");
} else {
  await build(buildOptions);
  console.log("esbuild build completed");
}
