import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../context/I18nContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { useApp } from "../context/AppContext.jsx";
import { badgeClass, buttonClass, sectionClass } from "../lib/ui";
import { cn } from "../lib/utils";

export default function HomePage() {
  const { t, locale } = useI18n();
  const { setAppTitle } = useApp();
  const { showToast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    const raw = t("app.title");
    const title = raw === "app.title" ? "TSD" : raw || "TSD";
    setAppTitle(title);
  }, [locale, setAppTitle, t]);

  const soonLabelRaw = t("soon");
  const soonLabel = soonLabelRaw === "soon" ? "Скоро" : soonLabelRaw || "Скоро";

  const soon = () => showToast(soonLabel, { duration: 1500, type: "info" });

  return (
    <section className={sectionClass()} id="home">
      <h1
        id="home-title"
        className="text-2xl font-semibold text-slate-900 dark:text-slate-50"
      >
        {t("main_menu") === "main_menu"
          ? "Главное меню"
          : t("main_menu") || "Главное меню"}
      </h1>
      <div className="flex flex-col gap-4">
        <button
          id="btn-doc-purchase"
          type="button"
          className={buttonClass({
            variant: "primary",
            size: "lg",
            block: true,
          })}
          onClick={() => navigate("/docs")}
        >
          <span id="btn-doc-purchase-txt">
            {t("doc_purchase") === "doc_purchase"
              ? "Поступление от контрагента"
              : t("doc_purchase") || "Поступление от контрагента"}
          </span>
        </button>

        {["doc_sales", "doc_inventory"].map((key) => (
          <button
            key={key}
            id={key === "doc_sales" ? "btn-doc-sales" : "btn-doc-inventory"}
            type="button"
            className={buttonClass({
              variant: "ghost",
              size: "lg",
              block: true,
            })}
            onClick={soon}
          >
            <div className="flex w-full items-center justify-between gap-3">
              <span id={`${key}-txt`} className="text-left">
                {t(key) === key
                  ? key === "doc_sales"
                    ? "Отгрузка контрагенту"
                    : "Инвентаризация"
                  : t(key) ||
                    (key === "doc_sales"
                      ? "Отгрузка контрагенту"
                      : "Инвентаризация")}
              </span>
              <span
                className={cn(
                  badgeClass(
                    "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                  ),
                  "uppercase"
                )}
                id={key === "doc_sales" ? "pill-sales" : "pill-inventory"}
              >
                {soonLabel}
              </span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
