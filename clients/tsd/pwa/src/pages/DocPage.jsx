import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
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
import { getDocDefinition } from "../config/docDefinitions.js";

const DEFAULT_OPERATION_FORM = { showCost: true, showPrice: true };

function MetaSeparator() {
  return (
    <span aria-hidden="true" className="text-slate-300 dark:text-slate-600">
      •
    </span>
  );
}

function OperationRow({ op, doc, onDelete, onSave, operationForm }) {
  const { t, fmt } = useI18n();
  const { toNumber } = useApp();
  const priceRoundTo = doc?.price_type?.round_to ?? null;
  const currencyCode =
    doc?.currency?.code_chr ||
    doc?.currency?.code ||
    doc?.currency_code ||
    "UZS";
  const formOptions = useMemo(
    () => ({ ...DEFAULT_OPERATION_FORM, ...(operationForm || {}) }),
    [operationForm]
  );
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(() => ({
    quantity: op.quantity != null ? String(op.quantity) : "",
    cost: op.cost != null ? String(op.cost) : "",
    price: op.price != null ? String(op.price) : "",
    description: op.description ?? "",
  }));
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
  const quantityNumber = toNumber(op.quantity ?? 0);
  const costValue = toNumber(op.cost ?? 0);
  const costTotal =
    formOptions.showCost !== false && op.cost != null
      ? costValue * quantityNumber
      : null;
  const priceTotal =
    formOptions.showPrice !== false && op.price != null
      ? priceValue * quantityNumber
      : null;

  const handleFieldChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleQuantityChange = (event) => {
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
      description: form.description || undefined,
    };
    if (formOptions.showCost !== false) {
      const costNumber = toNumber(form.cost);
      if (Number.isFinite(costNumber)) payload.cost = costNumber;
    }
    if (formOptions.showPrice !== false) {
      const priceNumber = toNumber(form.price);
      if (Number.isFinite(priceNumber) && priceNumber > 0) {
        payload.price = priceNumber;
      }
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
          <div className="flex flex-col gap-3 text-sm text-slate-600 dark:text-slate-300">
            <div className="flex flex-wrap items-center gap-2 font-medium">
              <span>
                <strong className="text-slate-900 dark:text-slate-100">
                  {fmt.number(op.quantity)}
                </strong>{" "}
                {unitName}
              </span>
            </div>

            {formOptions.showCost !== false && op.cost != null ? (
              <div className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {t("op.cost") || "Стоимость"}
                </span>
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-sm font-normal text-slate-500 dark:text-slate-400">
                    {fmt.money(costValue, currencyCode, priceRoundTo)}
                    {Number.isFinite(quantityNumber) && quantityNumber > 0
                      ? ` × ${fmt.number(quantityNumber)}`
                      : ""}
                  </span>
                  {Number.isFinite(costTotal) ? (
                    <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {fmt.money(costTotal, currencyCode, priceRoundTo)}
                    </span>
                  ) : (
                    <span className="text-sm font-medium text-slate-600 dark:text-slate-300">
                      {fmt.money(costValue, currencyCode, priceRoundTo)}
                    </span>
                  )}
                </div>
              </div>
            ) : null}

            {formOptions.showPrice !== false ? (
              <div className="flex flex-col gap-1">
                <span className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {t("op.price") || "Цена"}
                </span>
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-sm font-normal text-slate-500 dark:text-slate-400">
                    {fmt.money(priceValue, currencyCode, priceRoundTo)}
                    {Number.isFinite(quantityNumber) && quantityNumber > 0
                      ? ` × ${fmt.number(quantityNumber)}`
                      : ""}
                  </span>
                  {Number.isFinite(priceTotal) ? (
                    <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      {fmt.money(priceTotal, currencyCode, priceRoundTo)}
                    </span>
                  ) : (
                    <span className="text-sm font-medium text-slate-600 dark:text-slate-300">
                      {fmt.money(priceValue, currencyCode, priceRoundTo)}
                    </span>
                  )}
                </div>
              </div>
            ) : null}
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
          {formOptions.showCost !== false ? (
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
          ) : null}
          {formOptions.showPrice !== false ? (
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
          ) : null}
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
              className={buttonClass({ variant: "ghost", size: "sm" })}
              onClick={() => setEditing(false)}
              disabled={saving}
            >
              {t("common.cancel") || "Отмена"}
            </button>
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
          </div>
        </div>
      )}
    </div>
  );
}

export default function DocPage({ definition: definitionProp }) {
  const { id } = useParams();
  const docIdNumber = Number(id);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { api, unixToLocal, setAppTitle } = useApp();
  const { t, fmt, locale } = useI18n();
  const { showToast } = useToast();

  const typeParam = searchParams.get("type") || undefined;
  const docDefinition = useMemo(
    () => definitionProp || getDocDefinition(typeParam),
    [definitionProp, typeParam]
  );

  const operationForm = useMemo(
    () => ({
      ...DEFAULT_OPERATION_FORM,
      ...(docDefinition?.operation?.form || {}),
      ...(docDefinition?.detail?.operationForm || {}),
    }),
    [docDefinition]
  );

  const [doc, setDoc] = useState(null);
  const [operations, setOperations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionsOpen, setActionsOpen] = useState(false);

  const loadDoc = useCallback(async () => {
    const detail = docDefinition?.detail || {};
    if (!detail.docAction || !detail.operationsAction) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const buildDocPayload = detail.buildDocPayload || ((docId) => docId);
      const buildOpsPayload =
        detail.buildOperationsPayload || ((docId) => docId);
      const transformDoc = detail.transformDoc || ((data) => data);
      const transformOperations =
        detail.transformOperations ||
        ((data) => {
          if (Array.isArray(data)) return data;
          if (Array.isArray(data?.result)) return data.result;
          if (Array.isArray(data?.operations)) return data.operations;
          return [];
        });

      const batchConfig = detail.batch;
      if (batchConfig?.buildRequest) {
        const batchPayload = batchConfig.buildRequest(docIdNumber, {
          buildDocPayload,
          buildOperationsPayload: buildOpsPayload,
          definition: docDefinition,
        });
        const batchAction = batchConfig.action || "batch.run";
        const {
          ok: batchOk,
          status,
          data: batchData,
        } = await api(batchAction, batchPayload);

        if (!batchOk) {
          const description =
            batchData?.description ||
            batchData?.error ||
            "Batch request failed";
          throw new Error(`${description} (${status})`);
        }

        const docKey = batchConfig.docKey || "doc";
        const operationsKey = batchConfig.operationsKey || "operations";
        const findStep = (key) =>
          batchData?.result?.find?.((step) => step?.key === key);

        const docStep = findStep(docKey);
        if (!docStep) {
          throw new Error(`Шаг batch '${docKey}' не найден`);
        }
        if (docStep.response?.ok === false) {
          const description =
            docStep.response?.result?.description ||
            docStep.response?.description ||
            `Batch step '${docKey}' failed`;
          throw new Error(description);
        }

        const opsStep = findStep(operationsKey);
        if (!opsStep) {
          throw new Error(`Шаг batch '${operationsKey}' не найден`);
        }
        if (opsStep.response?.ok === false) {
          const description =
            opsStep.response?.result?.description ||
            opsStep.response?.description ||
            `Batch step '${operationsKey}' failed`;
          throw new Error(description);
        }

        const extractDoc =
          batchConfig.extractDoc ||
          ((response) => {
            if (!response) return null;
            const { result } = response;
            if (Array.isArray(result)) {
              return result[0] ?? null;
            }
            return result ?? null;
          });

        const extractOperations =
          batchConfig.extractOperations || ((response) => response);

        const docData = extractDoc(docStep.response);
        const operationsData = extractOperations(opsStep.response);

        setDoc(transformDoc(docData));
        setOperations(transformOperations(operationsData) || []);
        return;
      }

      const [docResponse, opsResponse] = await Promise.all([
        api(detail.docAction, buildDocPayload(docIdNumber)),
        api(detail.operationsAction, buildOpsPayload(docIdNumber)),
      ]);
      setDoc(transformDoc(docResponse?.data));
      setOperations(transformOperations(opsResponse?.data) || []);
    } catch (err) {
      setError(err);
      setDoc(null);
      setOperations([]);
    } finally {
      setLoading(false);
    }
  }, [api, docDefinition, docIdNumber]);

  useEffect(() => {
    loadDoc();
  }, [loadDoc]);

  const docTitle = useMemo(() => {
    const prefixKey = docDefinition?.labels?.title || "doc.title_prefix";
    const translated = t(prefixKey);
    const prefix =
      translated === prefixKey
        ? docDefinition?.labels?.titleFallback || "Документ"
        : translated;
    return `${prefix} ${doc?.code || id}`;
  }, [doc, docDefinition, id, t]);

  useEffect(() => {
    setAppTitle(docTitle);
  }, [docTitle, locale, setAppTitle]);

  const handleDelete = async (opId) => {
    const question = t("confirm.delete_op") || "Удалить операцию?";
    if (!window.confirm(question)) return;
    const detail = docDefinition?.detail || {};
    const deleteAction = detail.deleteAction;
    if (!deleteAction) {
      showToast(t("not_supported") || "Действие недоступно", {
        type: "error",
      });
      return;
    }

    try {
      const buildDeletePayload =
        detail.buildDeletePayload || ((operationId) => [{ id: operationId }]);
      const handleDeleteResponse =
        detail.handleDeleteResponse ||
        ((data) => data?.row_affected > 0 || data?.result?.row_affected > 0);

      const payload = buildDeletePayload(opId, { docId: docIdNumber, doc });
      const { data } = await api(deleteAction, payload);

      if (handleDeleteResponse(data, { opId, payload, doc })) {
        showToast(t("toast.op_deleted") || "Операция удалена", {
          type: "success",
        });
        await loadDoc();
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
    const detail = docDefinition?.detail || {};
    const editAction = detail.editAction;
    if (!editAction) {
      showToast(t("not_supported") || "Действие недоступно", {
        type: "error",
      });
      return false;
    }

    try {
      const buildEditPayload =
        detail.buildEditPayload ||
        ((operationId, next) => [{ id: operationId, ...next }]);
      const handleEditResponse =
        detail.handleEditResponse ||
        ((data) => data?.row_affected > 0 || data?.result?.row_affected > 0);

      const requestPayload = buildEditPayload(opId, payload, {
        docId: docIdNumber,
        doc,
      });
      const { data } = await api(editAction, requestPayload);
      if (handleEditResponse(data, { opId, payload, doc })) {
        showToast(t("toast.op_updated") || "Операция сохранена", {
          type: "success",
        });
        await loadDoc();
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

  const actionsLabel = useMemo(() => {
    const value = t("doc.actions");
    return value === "doc.actions" ? "Действия" : value;
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
    const roundTo = doc.price_type?.round_to ?? null;
    return [
      doc.date ? unixToLocal(doc.date) : null,
      doc.partner?.name || null,
      fmt.money(doc.amount ?? 0, currency, roundTo),
    ].filter(Boolean);
  }, [doc, fmt, unixToLocal]);

  const partnerLabel = useMemo(() => {
    const detail = docDefinition?.detail || {};
    const key = detail.partnerLabelKey || "doc.partner";
    const translated = t(key);
    if (translated && translated !== key) return translated;
    const fallbackKey = detail.partnerLabelFallback;
    if (fallbackKey) return fallbackKey;
    const generic = t("partner");
    if (generic && generic !== "partner") return generic;
    return "Партнёр";
  }, [docDefinition, t]);

  const goToDocs = useCallback(() => {
    const buildDocsPath =
      docDefinition?.navigation?.buildDocsPath || (() => "/docs");
    navigate(buildDocsPath(doc), { replace: true });
  }, [doc, docDefinition, navigate]);

  const goToNewOperation = useCallback(() => {
    const buildNewOperationPath =
      docDefinition?.navigation?.buildNewOperationPath ||
      ((docId) => `/doc/${docId}/op/new`);
    navigate(buildNewOperationPath(docIdNumber));
  }, [docDefinition, docIdNumber, navigate]);

  const handleOpenActions = useCallback(() => {
    setActionsOpen(true);
  }, []);

  const handleCloseActions = useCallback(() => {
    setActionsOpen(false);
  }, []);

  const handlePerform = useCallback(async () => {
    const detail = docDefinition?.detail || {};
    const action = detail.performAction;
    if (!action) {
      showToast(t("not_supported") || "Действие недоступно", {
        type: "error",
      });
      return;
    }

    const confirmMessage = t("confirm.perform_doc") || "Провести документ?";
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      const payloadBuilder =
        detail.buildPerformPayload || ((docId) => ({ id: docId }));
      const payload = payloadBuilder(doc?.id ?? docIdNumber, { doc });
      const { data } = await api(action, payload);
      const succeeded =
        detail.handlePerformResponse?.(data, { doc }) ??
        data?.result?.success ??
        true;

      if (succeeded) {
        showToast(t("toast.doc_performed") || "Документ проведён", {
          type: "success",
        });
        setActionsOpen(false);
        await loadDoc();
      } else {
        throw new Error(data?.description || "Perform failed");
      }
    } catch (err) {
      showToast(err.message || "Не удалось провести документ", {
        type: "error",
        duration: 2400,
      });
    }
  }, [api, doc, docDefinition, docIdNumber, loadDoc, showToast, t]);

  const handleCancelPerform = useCallback(async () => {
    const detail = docDefinition?.detail || {};
    const action = detail.cancelPerformAction;
    if (!action) {
      showToast(t("not_supported") || "Действие недоступно", {
        type: "error",
      });
      return;
    }

    const confirmMessage =
      t("confirm.cancel_perform_doc") || "Отменить проведение документа?";
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      const payloadBuilder =
        detail.buildCancelPerformPayload || ((docId) => ({ id: docId }));
      const payload = payloadBuilder(doc?.id ?? docIdNumber, { doc });
      const { data } = await api(action, payload);
      const succeeded =
        detail.handleCancelPerformResponse?.(data, { doc }) ??
        data?.result?.success ??
        true;

      if (succeeded) {
        showToast(t("toast.doc_cancelled") || "Проведение отменено", {
          type: "success",
        });
        setActionsOpen(false);
        await loadDoc();
      } else {
        throw new Error(data?.description || "Cancel perform failed");
      }
    } catch (err) {
      showToast(err.message || "Не удалось отменить проведение", {
        type: "error",
        duration: 2400,
      });
    }
  }, [api, doc, docDefinition, docIdNumber, loadDoc, showToast, t]);

  const handleLock = useCallback(async () => {
    const detail = docDefinition?.detail || {};
    const action = detail.lockAction;
    if (!action) {
      showToast(t("not_supported") || "Действие недоступно", {
        type: "error",
      });
      return;
    }

    const confirmMessage = t("confirm.lock_doc") || "Заблокировать документ?";
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      const payloadBuilder =
        detail.buildLockPayload || ((docId) => ({ ids: [docId] }));
      const payload = payloadBuilder(doc?.id ?? docIdNumber, { doc });
      const { data } = await api(action, payload);
      const succeeded =
        detail.handleLockResponse?.(data, { doc }) ??
        data?.result?.success ??
        true;

      if (succeeded) {
        showToast(t("toast.doc_locked") || "Документ заблокирован", {
          type: "success",
        });
        setActionsOpen(false);
        await loadDoc();
      } else {
        throw new Error(data?.description || "Lock failed");
      }
    } catch (err) {
      showToast(err.message || "Не удалось заблокировать документ", {
        type: "error",
        duration: 2400,
      });
    }
  }, [api, doc, docDefinition, docIdNumber, loadDoc, showToast, t]);

  const handleUnlock = useCallback(async () => {
    const detail = docDefinition?.detail || {};
    const action = detail.unlockAction;
    if (!action) {
      showToast(t("not_supported") || "Действие недоступно", {
        type: "error",
      });
      return;
    }

    const confirmMessage =
      t("confirm.unlock_doc") || "Разблокировать документ?";
    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      const payloadBuilder =
        detail.buildUnlockPayload || ((docId) => ({ ids: [docId] }));
      const payload = payloadBuilder(doc?.id ?? docIdNumber, { doc });
      const { data } = await api(action, payload);
      const succeeded =
        detail.handleUnlockResponse?.(data, { doc }) ??
        data?.result?.success ??
        true;

      if (succeeded) {
        showToast(t("toast.doc_unlocked") || "Документ разблокирован", {
          type: "success",
        });
        setActionsOpen(false);
        await loadDoc();
      } else {
        throw new Error(data?.description || "Unlock failed");
      }
    } catch (err) {
      showToast(err.message || "Не удалось разблокировать документ", {
        type: "error",
        duration: 2400,
      });
    }
  }, [api, doc, docDefinition, docIdNumber, loadDoc, showToast, t]);

  const handlePrint = useCallback(() => {
    console.log("[doc-actions] print", {
      id: doc?.id ?? docIdNumber,
      type: docDefinition?.key,
    });
    setActionsOpen(false);
  }, [doc?.id, docDefinition?.key, docIdNumber]);

  if (!docDefinition) {
    return (
      <section className={sectionClass()} id="doc">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
          {t("doc.title_prefix") || "Документ"}
        </h1>
        <div className={mutedTextClass()}>
          {t("doc.not_supported") || "Тип документа не поддерживается"}
        </div>
      </section>
    );
  }

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
        <div className="w-full flex items-center justify-between gap-2">
          <button
            type="button"
            className={buttonClass({ variant: "ghost", size: "sm" })}
            onClick={handleOpenActions}
          >
            {actionsLabel}
          </button>
          <button
            id="btn-add-op"
            type="button"
            className={buttonClass({ variant: "primary", size: "sm" })}
            onClick={goToNewOperation}
            disabled={doc?.performed || doc?.blocked}
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
            {partnerLabel}
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
              doc.currency?.code_chr || doc.currency?.code || "UZS",
              doc.price_type?.round_to ?? null
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
              doc={doc}
              onDelete={handleDelete}
              onSave={handleSave}
              operationForm={operationForm}
            />
          ))
        )}
      </div>

      {actionsOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6"
          role="presentation"
          onClick={handleCloseActions}
        >
          <div
            className={cardClass(
              "relative w-full max-w-sm space-y-4 p-6 shadow-xl"
            )}
            role="dialog"
            aria-modal="true"
            aria-labelledby="doc-actions-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <h2
                id="doc-actions-title"
                className="text-lg font-semibold text-slate-900 dark:text-slate-50"
              >
                {actionsLabel}
              </h2>
              <button
                type="button"
                className={iconButtonClass({ variant: "ghost" })}
                onClick={handleCloseActions}
                aria-label={t("common.close") || "Закрыть"}
                title={t("common.close") || "Закрыть"}
              >
                <i className="fa-solid fa-xmark" aria-hidden="true" />
              </button>
            </div>

            <div className="flex flex-col gap-3">
              {!doc?.performed ? (
                <button
                  type="button"
                  className={buttonClass({ variant: "primary", size: "md" })}
                  onClick={handlePerform}
                >
                  {t("doc.perform") === "doc.perform"
                    ? "Провести"
                    : t("doc.perform") || "Провести"}
                </button>
              ) : null}
              {doc?.performed ? (
                <button
                  type="button"
                  className={buttonClass({ variant: "ghost", size: "md" })}
                  onClick={handleCancelPerform}
                >
                  {t("doc.cancel_perform") === "doc.cancel_perform"
                    ? "Отменить проведение"
                    : t("doc.cancel_perform") || "Отменить проведение"}
                </button>
              ) : null}
              {!doc?.blocked ? (
                <button
                  type="button"
                  className={buttonClass({ variant: "ghost", size: "md" })}
                  onClick={handleLock}
                >
                  {t("doc.lock") === "doc.lock"
                    ? "Заблокировать"
                    : t("doc.lock") || "Заблокировать"}
                </button>
              ) : null}
              {doc?.blocked ? (
                <button
                  type="button"
                  className={buttonClass({ variant: "ghost", size: "md" })}
                  onClick={handleUnlock}
                >
                  {t("doc.unlock") === "doc.unlock"
                    ? "Разблокировать"
                    : t("doc.unlock") || "Разблокировать"}
                </button>
              ) : null}
              <button
                type="button"
                className={buttonClass({ variant: "ghost", size: "md" })}
                onClick={handlePrint}
              >
                {t("doc.print") === "doc.print"
                  ? "Печать"
                  : t("doc.print") || "Печать"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
