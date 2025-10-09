import React from "react";
import { useI18n } from "../context/I18nContext.jsx";

const OPTIONS = [
  { value: "ru", label: "RU" },
  { value: "en", label: "EN" },
  { value: "uz", label: "UZ" },
];

export default function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  return (
    <div className="lang-switcher">
      <label className="sr-only" htmlFor="lang-select">
        Language
      </label>
      <select
        id="lang-select"
        className="lang-select"
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
