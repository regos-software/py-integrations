import { cn } from "./utils";

const BUTTON_VARIANTS = {
  primary:
    "bg-slate-900 text-white hover:bg-slate-800 focus-visible:ring-slate-500 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white/90",
  secondary:
    "bg-slate-100 text-slate-900 hover:bg-slate-200 focus-visible:ring-slate-500 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700",
  ghost:
    "border border-slate-300 text-slate-700 hover:bg-slate-100 focus-visible:ring-slate-400 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700",
  danger:
    "bg-rose-600 text-white hover:bg-rose-500 focus-visible:ring-rose-400",
  subtle:
    "bg-slate-50 text-slate-700 hover:bg-slate-100 focus-visible:ring-slate-400 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
};

const BUTTON_SIZES = {
  md: "px-4 py-2 text-sm",
  sm: "px-3 py-2 text-sm",
  lg: "px-5 py-3 text-base",
  icon: "h-10 w-10 p-0",
};

const BUTTON_BASE =
  "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent disabled:cursor-not-allowed disabled:opacity-50";

export function buttonClass({
  variant = "primary",
  size = "md",
  block = false,
} = {}) {
  const variantClass = BUTTON_VARIANTS[variant] ?? BUTTON_VARIANTS.primary;
  const sizeClass = BUTTON_SIZES[size] ?? BUTTON_SIZES.md;
  return cn(BUTTON_BASE, variantClass, sizeClass, block && "w-full");
}

export function iconButtonClass({ variant = "ghost" } = {}) {
  return buttonClass({ variant, size: "icon" });
}

export function mutedTextClass() {
  return "text-sm text-slate-500 dark:text-slate-400";
}

export function cardClass(extra) {
  return cn(
    "rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm backdrop-blur dark:border-slate-700 dark:bg-slate-800/80 sm:p-6",
    extra
  );
}

export function sectionClass(extra) {
  return cn("flex flex-col gap-6", extra);
}

export function listClass(extra) {
  return cn("flex flex-col gap-4", extra);
}

export function inputClass(extra) {
  return cn(
    "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100",
    extra
  );
}

export function labelClass(extra) {
  return cn("text-sm font-medium text-slate-700 dark:text-slate-100", extra);
}

export function badgeClass(extra) {
  return cn(
    "inline-flex items-center rounded-full border border-slate-300 bg-slate-100 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200",
    extra
  );
}

export function chipClass(extra) {
  return cn(
    "inline-flex items-center justify-center rounded-full border border-slate-300 bg-slate-50 px-3 py-1 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
    extra
  );
}

export function toastClass(open, type = "success") {
  const palette =
    type === "error"
      ? "bg-rose-600 text-white"
      : type === "info"
      ? "bg-blue-600 text-white"
      : "bg-emerald-600 text-white";
  return cn(
    "pointer-events-auto w-full rounded-xl px-4 py-3 text-sm font-medium shadow-lg transition duration-200",
    palette,
    open ? "opacity-100 translate-y-0" : "translate-y-2 opacity-0"
  );
}
