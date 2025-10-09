import React from "react";
import { useI18n } from "../context/I18nContext.jsx";
import { inputClass } from "../lib/ui";

const OPTIONS = [
  { value: "ru", label: "RU" },
  { value: "en", label: "EN" },
  { value: "uz", label: "UZ" },
];

export default function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  return (
    <div className="flex items-center">
      <label className="sr-only" htmlFor="lang-select">
        Language
      </label>
      <select
        id="lang-select"
        className={inputClass(
          "h-10 w-[84px] min-w-[84px] uppercase font-semibold tracking-wide"
        )}
        value={locale}
        onChange={(event) => setLocale(event.target.value)}
        aria-label="Language"
      >
        {OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
