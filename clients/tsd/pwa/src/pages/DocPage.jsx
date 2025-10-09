import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import {
  buttonClass,
  cardClass,
  iconButtonClass,
  inputClass,
  labelClass,
  listClass,
  mutedTextClass,
  sectionClass,
} from "../lib/ui";
import { cn } from "../lib/utils";

function MetaSeparator() {
  return (
    <span aria-hidden="true" className="text-slate-300 dark:text-slate-600">
      •
    </span>
  );
}

function OperationRow({ op, onDelete, onSave }) {
  const { t, fmt } = useI18n();
  const { toNumber } = useApp();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    quantity: op.quantity != null ? String(op.quantity) : "",
    cost: op.cost != null ? String(op.cost) : "",
    price: op.price != null ? String(op.price) : "",
    description: op.description ?? "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      quantity: op.quantity != null ? String(op.quantity) : "",
      cost: op.cost != null ? String(op.cost) : "",
      price: op.price != null ? String(op.price) : "",
      description: op.description ?? "",
    });
  }, [op]);

  const item = op.item || {};
  const barcode =
    item.base_barcode ||
    (item.barcode_list
      ? String(item.barcode_list).split(",")[0]?.trim()
      : "") ||
    item.code ||
    "";
  const code = (item.code ?? "").toString().padStart(6, "0");
  const unitName = item.unit?.name;
  const unitPiece = item.unit?.type === "pcs";
  const priceValue = toNumber(op.price ?? 0);

  const handleFieldChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleQuantityChange = (event) => {
    console.log("item", item);
    const nextValue = event.target.value;
    if (unitPiece) {
      if (/^\d*$/.test(nextValue)) {
        setForm((prev) => ({ ...prev, quantity: nextValue }));
      }
      return;
    }
    setForm((prev) => ({ ...prev, quantity: nextValue }));
  };

  const handleSave = async () => {
    if (!form.quantity || toNumber(form.quantity) <= 0) {
      window.alert(t("op.qty.required") || "Введите количество");
      return;
    }

    setSaving(true);
    const payload = {
      quantity: toNumber(form.quantity),
      cost: toNumber(form.cost),
      description: form.description || undefined,
    };
    const priceNumber = toNumber(form.price);
    if (Number.isFinite(priceNumber) && priceNumber > 0) {
      payload.price = priceNumber;
    }

    const ok = await onSave(op.id, payload);
    setSaving(false);
    if (ok) {
      setEditing(false);
    }
  };

  return (
    <div
      className={cardClass(
        "space-y-4 transition hover:-translate-y-0.5 hover:shadow-md"
      )}
    >
      {!editing && (
        <>
          <div className="flex items-start justify-between gap-4">
            <div className="flex min-w-0 flex-col gap-2">
              <strong className="truncate text-base font-semibold text-slate-900 dark:text-slate-50">
                {item.name || ""}
              </strong>
              <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <span className="font-semibold tracking-wide">{code}</span>
                {barcode ? (
                  <>
                    <MetaSeparator />
                    <span className="truncate">{barcode}</span>
                  </>
                ) : null}
                {op.description ? (
                  <>
                    <MetaSeparator />
                    <span className="truncate">{op.description}</span>
                  </>
                ) : null}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className={cn(iconButtonClass({ variant: "ghost" }), "op-edit")}
                onClick={() => setEditing(true)}
                aria-label={t("op.edit") || "Редактировать"}
                title={t("op.edit") || "Редактировать"}
              >
                <i className="fa-solid fa-pen" aria-hidden="true" />
              </button>
              <button
                type="button"
                className={cn(iconButtonClass({ variant: "ghost" }), "op-del")}
                onClick={() => onDelete(op.id)}
                aria-label={t("op.delete") || "Удалить"}
                title={t("op.delete") || "Удалить"}
              >
                <i className="fa-solid fa-trash" aria-hidden="true" />
              </button>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            <span>
              <strong className="text-slate-900 dark:text-slate-100">
                {fmt.number(op.quantity)}
              </strong>{" "}
              {unitName}
            </span>
            <MetaSeparator />
            <span>{fmt.money(op.cost)}</span>
            <MetaSeparator />
            <span>{fmt.money(priceValue)}</span>
          </div>
        </>
      )}

      {editing && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label className={labelClass()} htmlFor={`qty-${op.id}`}>
              {t("op.qty") || "Количество"}
            </label>
            <input
              id={`qty-${op.id}`}
              type="number"
              inputMode={unitPiece ? "numeric" : "decimal"}
              step={unitPiece ? 1 : "0.01"}
              value={form.quantity}
              onChange={handleQuantityChange}
              className={inputClass()}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className={labelClass()} htmlFor={`cost-${op.id}`}>
              {t("op.cost") || "Стоимость"}
            </label>
            <input
              id={`cost-${op.id}`}
              type="number"
              inputMode="decimal"
              value={form.cost}
              onChange={handleFieldChange("cost")}
              className={inputClass()}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className={labelClass()} htmlFor={`price-${op.id}`}>
              {t("op.price") || "Цена"}
            </label>
            <input
              id={`price-${op.id}`}
              type="number"
              inputMode="decimal"
              value={form.price}
              onChange={handleFieldChange("price")}
              className={inputClass()}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className={labelClass()} htmlFor={`description-${op.id}`}>
              {t("op.description") || "Описание"}
            </label>
            <input
              id={`description-${op.id}`}
              type="text"
              value={form.description}
              onChange={handleFieldChange("description")}
              className={inputClass()}
            />
          </div>
          <div className="flex flex-wrap gap-3" id={`op-actions-${op.id}`}>
            <button
              type="button"
              className={buttonClass({ variant: "primary", size: "sm" })}
              onClick={handleSave}
              disabled={saving}
            >
              {saving
                ? t("op.saving") || "Сохранение..."
                : t("common.save") || "Сохранить"}
            </button>
            <button
              type="button"
              className={buttonClass({ variant: "ghost", size: "sm" })}
              onClick={() => setEditing(false)}
              disabled={saving}
            >
              {t("common.cancel") || "Отмена"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DocPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { api, unixToLocal, setAppTitle } = useApp();
  const { t, fmt, locale } = useI18n();
  const { showToast } = useToast();

  const [doc, setDoc] = useState(null);
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchDoc() {
      setLoading(true);
      setError(null);
      try {
        const { data } = await api("purchase_get", { doc_id: id });
        const docData = data?.result?.doc || null;
        const ops = data?.result?.operations || [];
        if (!cancelled) {
          setDoc(docData);
          setOperations(Array.isArray(ops) ? ops : []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
          setDoc(null);
          setOperations([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchDoc();
    return () => {
      cancelled = true;
    };
  }, [api, id]);

  const docTitle = useMemo(() => {
    const prefix = t("doc.title_prefix") || "Документ";
    return `${prefix} ${doc?.code || id}`;
  }, [doc, id, t]);

  useEffect(() => {
    setAppTitle(docTitle);
  }, [docTitle, locale, setAppTitle]);

  const handleDelete = async (opId) => {
    const question = t("confirm.delete_op") || "Удалить операцию?";
    if (!window.confirm(question)) return;
    try {
      const { ok, data } = await api("purchase_ops_delete", {
        items: [{ id: opId }],
      });
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        setOperations((prev) => prev.filter((op) => op.id !== opId));
        showToast(t("toast.op_deleted") || "Операция удалена", {
          type: "success",
        });
      } else {
        throw new Error(data?.description || "Delete failed");
      }
    } catch (err) {
      showToast(err.message || "Не удалось удалить операцию", {
        type: "error",
        duration: 2400,
      });
    }
  };

  const handleSave = async (opId, payload) => {
    try {
      const { ok, data } = await api("purchase_ops_edit", {
        items: [{ id: opId, ...payload }],
      });
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        setOperations((prev) =>
          prev.map((op) => {
            if (op.id !== opId) return op;
            const next = { ...op, ...payload };
            if (!Object.prototype.hasOwnProperty.call(payload, "price")) {
              next.price = op.price;
            }
            if (!Object.prototype.hasOwnProperty.call(payload, "description")) {
              next.description = op.description;
            }
            return next;
          })
        );
        showToast(t("toast.op_updated") || "Операция сохранена", {
          type: "success",
        });
        return true;
      }
      throw new Error(data?.description || "Save failed");
    } catch (err) {
      showToast(err.message || "Не удалось сохранить операцию", {
        type: "error",
        duration: 2400,
      });
      return false;
    }
  };

  const status = useMemo(() => {
    if (!doc) return "";
    const segments = [];
    const performed = t("docs.status.performed");
    const performedLabel =
      performed === "docs.status.performed" ? "проведён" : performed;
    const newLabel = t("docs.status.new");
    const newValue = newLabel === "docs.status.new" ? "новый" : newLabel;
    segments.push(doc.performed ? performedLabel : newValue);
    if (doc.blocked) {
      const blocked = t("docs.status.blocked");
      segments.push(blocked === "docs.status.blocked" ? "блок." : blocked);
    }
    return segments.join(" • ");
  }, [doc, t]);

  const backToDocsLabel = useMemo(() => {
    const preferred = t("docs.back_to_list");
    if (preferred && preferred !== "docs.back_to_list") return preferred;
    const fallback = t("nav.back");
    return fallback === "nav.back" ? "Назад" : fallback;
  }, [t]);

  const addOperationLabel = useMemo(() => {
    const value = t("doc.add_op");
    return value === "doc.add_op" ? "Добавить" : value;
  }, [t]);

  const nothingLabel = useMemo(() => {
    const value = t("doc.no_ops") || t("common.nothing");
    return value || "Операций ещё нет";
  }, [t]);

  const metaSegments = useMemo(() => {
    if (!doc) return [];
    const currency = doc.currency?.code_chr || "UZS";
    return [
      doc.date ? unixToLocal(doc.date) : null,
      doc.partner?.name || null,
      fmt.money(doc.amount ?? 0, currency),
    ].filter(Boolean);
  }, [doc, fmt, unixToLocal]);

  const goToDocs = useCallback(() => {
    navigate("/docs", { replace: true });
  }, [navigate]);

  const goToNewOperation = useCallback(() => {
    navigate(`/doc/${id}/op/new`);
  }, [id, navigate]);

  if (loading) {
    return (
      <section className={sectionClass()} id="doc">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
          {docTitle}
        </h1>
        <div className={mutedTextClass()}>
          {t("common.loading") || "Загрузка..."}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className={sectionClass()} id="doc">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
          {docTitle}
        </h1>
        <div className={mutedTextClass()}>{String(error.message || error)}</div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={buttonClass({ variant: "ghost", size: "sm" })}
            onClick={goToDocs}
          >
            {backToDocsLabel}
          </button>
        </div>
      </section>
    );
  }

  if (!doc) {
    return (
      <section className={sectionClass()} id="doc">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
          {docTitle}
        </h1>
        <div className={mutedTextClass()}>
          {t("common.nothing") || "Ничего не найдено"}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={buttonClass({ variant: "ghost", size: "sm" })}
            onClick={goToDocs}
          >
            {backToDocsLabel}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className={sectionClass()} id="doc">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1
            className="text-2xl font-semibold text-slate-900 dark:text-slate-50"
            id="doc-title"
          >
            {docTitle}
          </h1>
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            {status ? <span id="doc-status">{status}</span> : null}
            {status && metaSegments.length > 0 ? <MetaSeparator /> : null}
            {metaSegments.map((segment, index) => {
              const segmentId =
                index === 0
                  ? "doc-date"
                  : index === 1
                  ? "doc-partner"
                  : index === 2
                  ? "doc-amount"
                  : undefined;
              return (
                <React.Fragment key={`${segment}-${index}`}>
                  {index > 0 && <MetaSeparator />}
                  <span className="truncate" id={segmentId}>
                    {segment}
                  </span>
                </React.Fragment>
              );
            })}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className={buttonClass({ variant: "ghost", size: "sm" })}
            onClick={goToDocs}
          >
            {backToDocsLabel}
          </button>
          <button
            id="btn-add-op"
            type="button"
            className={buttonClass({ variant: "primary", size: "sm" })}
            onClick={goToNewOperation}
          >
            <span>{addOperationLabel}</span>
            <i className="fa-solid fa-plus" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div
        className={cardClass(
          "space-y-2 text-sm text-slate-700 dark:text-slate-200"
        )}
        id="doc-meta"
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-slate-900 dark:text-slate-100">
            {t("doc.partner") === "doc.partner"
              ? t("partner") === "partner"
                ? "Поставщик"
                : t("partner")
              : t("doc.partner")}
          </span>
          <MetaSeparator />
          <span className="truncate">{doc.partner?.name || "—"}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-slate-900 dark:text-slate-100">
            {t("doc.amount") === "doc.amount" ? "Сумма" : t("doc.amount")}
          </span>
          <MetaSeparator />
          <span>
            {fmt.money(
              doc.amount ?? 0,
              doc.currency?.code_chr || doc.currency?.code || "UZS"
            )}
          </span>
        </div>
        {doc.employee?.full_name ? (
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-slate-900 dark:text-slate-100">
              {t("doc.employee") === "doc.employee"
                ? "Ответственный"
                : t("doc.employee")}
            </span>
            <MetaSeparator />
            <span>{doc.employee.full_name}</span>
          </div>
        ) : null}
      </div>

      <div id="ops-list" className={listClass("mt-2")} aria-live="polite">
        {operations.length === 0 ? (
          <div className={cardClass(`${mutedTextClass()} text-center py-6`)}>
            {nothingLabel}
          </div>
        ) : (
          operations.map((operation) => (
            <OperationRow
              key={operation.id}
              op={operation}
              onDelete={handleDelete}
              onSave={handleSave}
            />
          ))
        )}
      </div>
    </section>
  );
}
