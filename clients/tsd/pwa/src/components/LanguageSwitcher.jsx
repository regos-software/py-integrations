import React, { useCallback, useState } from "react";
import { useI18n } from "../context/I18nContext.jsx";
import {
  buttonClass,
  cardClass,
  iconButtonClass,
  mutedTextClass,
} from "../lib/ui";
import { cn } from "../lib/utils";

const OPTIONS = [
  { value: "ru", label: "Русский" },
  { value: "en", label: "English" },
  { value: "uz", label: "Oʻzbekcha" },
];

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();
  const [open, setOpen] = useState(false);

  const handleSelect = useCallback(
    (value) => {
      setLocale(value);
      setOpen(false);
    },
    [setLocale]
  );

  const toggleLabel = t("language.switcher") || "Изменить язык интерфейса";
  const modalTitle = t("language.select_title") || "Выберите язык";

  return (
    <>
      <button
        type="button"
        className={iconButtonClass({ variant: "ghost" })}
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={toggleLabel}
        title={toggleLabel}
      >
        <i className="fa-solid fa-language" aria-hidden="true" />
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6 mt-36"
          role="presentation"
          onClick={() => setOpen(false)}
        >
          <div
            className={cardClass(
              "relative w-full max-w-xs space-y-4 p-6 shadow-xl"
            )}
            role="dialog"
            aria-modal="true"
            aria-labelledby="language-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <h2
                id="language-modal-title"
                className="text-lg font-semibold text-slate-900 dark:text-slate-50"
              >
                {modalTitle}
              </h2>
              <button
                type="button"
                className={iconButtonClass({ variant: "ghost" })}
                onClick={() => setOpen(false)}
                aria-label={t("common.close") || "Закрыть"}
                title={t("common.close") || "Закрыть"}
              >
                <i className="fa-solid fa-xmark" aria-hidden="true" />
              </button>
            </div>
            <p className={mutedTextClass()}>
              {t("language.choose_prompt") || "Выберите язык интерфейса"}
            </p>
            <div className="space-y-2">
              {OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={cn(
                    buttonClass({
                      variant: option.value === locale ? "primary" : "ghost",
                      size: "sm",
                      block: true,
                    }),
                    "justify-start"
                  )}
                  onClick={() => handleSelect(option.value)}
                  aria-current={option.value === locale}
                >
                  <span className="font-semibold">{option.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
