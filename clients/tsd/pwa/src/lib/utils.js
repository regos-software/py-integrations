export function toNumber(value) {
  if (value == null || value === "") return 0;
  const normalized = String(value).replace(",", ".");
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function unixToLocal(ts) {
  if (!ts) return "";
  const d = new Date(Number(ts) * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

export function cn(...classes) {
  return classes.flat().filter(Boolean).join(" ");
}

export function decimalPlacesFromRoundTo(roundTo) {
  if (roundTo == null) return 0;

  if (typeof roundTo === "number") {
    if (!Number.isFinite(roundTo) || roundTo === 0) {
      return 0;
    }
  }

  const raw = String(roundTo).trim();
  if (!raw) return 0;

  const normalized = raw.replace(",", ".");

  const numeric = Number(normalized);
  if (!Number.isFinite(numeric) || numeric === 0) {
    return 0;
  }

  const absolute = Math.abs(numeric);
  if (Number.isInteger(absolute)) {
    return 0;
  }

  if (normalized.toLowerCase().includes("e")) {
    const parts = absolute.toString().split(".");
    return parts[1] ? parts[1].replace(/0+$/, "").length : 0;
  }

  const [, fraction = ""] = normalized.split(".");
  const trimmed = fraction.replace(/0+$/, "");
  return trimmed.length;
}
