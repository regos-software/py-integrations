import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../context/I18nContext.jsx";
import { useApp } from "../context/AppContext.jsx";
import { buttonClass, sectionClass } from "../lib/ui";

export default function HomePage() {
  const { t, locale } = useI18n();
  const { setAppTitle } = useApp();
  const navigate = useNavigate();

  useEffect(() => {
    const raw = t("app.title");
    const title = raw === "app.title" ? "TSD" : raw || "TSD";
    setAppTitle(title);
  }, [locale, setAppTitle, t]);

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
          id="btn-item-info"
          type="button"
          className={buttonClass({
            variant: "primary",
            size: "lg",
            block: true,
          })}
          onClick={() => navigate("/item-info")}
        >
          <span id="btn-item-info-txt">
            {t("item_info.menu") === "item_info.menu"
              ? "Информация по номенклатуре"
              : t("item_info.menu") || "Информация по номенклатуре"}
          </span>
        </button>
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

        <button
          id="btn-doc-movement"
          type="button"
          className={buttonClass({
            variant: "primary",
            size: "lg",
            block: true,
          })}
          onClick={() => navigate("/docs?type=movement")}
        >
          <span id="btn-doc-movement-txt">
            {t("doc_movement") === "doc_movement"
              ? "Перемещение между складами"
              : t("doc_movement") || "Перемещение между складами"}
          </span>
        </button>

        <button
          id="btn-doc-wholesale"
          type="button"
          className={buttonClass({
            variant: "primary",
            size: "lg",
            block: true,
          })}
          onClick={() => navigate("/docs?type=wholesale")}
        >
          <span id="btn-doc-wholesale-txt">
            {t("doc_wholesale") === "doc_wholesale"
              ? "Отгрузка контрагенту"
              : t("doc_wholesale") || "Отгрузка контрагенту"}
          </span>
        </button>

        <button
          id="btn-doc-inventory"
          type="button"
          className={buttonClass({
            variant: "primary",
            size: "lg",
            block: true,
          })}
          onClick={() => navigate("/docs?type=inventory")}
        >
          <span id="doc_inventory-txt">
            {t("doc_inventory") === "doc_inventory"
              ? "Инвентаризация"
              : t("doc_inventory") || "Инвентаризация"}
          </span>
        </button>
      </div>
    </section>
  );
}
