import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
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

const DEFAULT_OPERATION_FORM = {
  showCost: true,
  showPrice: true,
  showDescription: true,
};

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

  const metrics = useMemo(() => {
    const conciseQuantity = Number.isFinite(quantityNumber)
      ? fmt.number(quantityNumber)
      : "—";
    const quantityDisplay = `${conciseQuantity}${
      unitName ? ` ${unitName}` : ""
    }`.trim();

    const showCost = formOptions.showCost !== false && op.cost != null;
    const showPrice = formOptions.showPrice !== false && op.price != null;

    const costUnit = showCost
      ? fmt.money(costValue, currencyCode, priceRoundTo)
      : "—";
    const costTotalNumber =
      showCost && Number.isFinite(quantityNumber)
        ? costValue * quantityNumber
        : null;
    const costTotalDisplay = showCost
      ? Number.isFinite(costTotalNumber)
        ? fmt.money(costTotalNumber, currencyCode, priceRoundTo)
        : fmt.money(costValue, currencyCode, priceRoundTo)
      : "—";

    const priceUnit = showPrice
      ? fmt.money(priceValue, currencyCode, priceRoundTo)
      : "—";
    const priceTotalNumber =
      showPrice && Number.isFinite(quantityNumber)
        ? priceValue * quantityNumber
        : null;
    const priceTotalDisplay = showPrice
      ? Number.isFinite(priceTotalNumber)
        ? fmt.money(priceTotalNumber, currencyCode, priceRoundTo)
        : fmt.money(priceValue, currencyCode, priceRoundTo)
      : "—";

    return [
      {
        key: "quantity",
        value: quantityDisplay || "—",
        accent: false,
        title: t("op.qty") || "Количество",
      },
      {
        key: "cost",
        value: costUnit,
        accent: false,
        title: t("op.cost") || "Стоимость",
      },
      {
        key: "cost-total",
        value: costTotalDisplay,
        accent: true,
        title: t("op.cost_total") || "Сумма по себестоимости",
      },
      {
        key: "price",
        value: priceUnit,
        accent: false,
        title: t("op.price") || "Цена",
      },
      {
        key: "price-total",
        value: priceTotalDisplay,
        accent: true,
        title: t("op.price_total") || "Сумма по цене",
      },
    ];
  }, [
    currencyCode,
    fmt,
    formOptions.showCost,
    formOptions.showPrice,
    costValue,
    op.cost,
    op.price,
    priceRoundTo,
    priceValue,
    quantityNumber,
    t,
    unitName,
  ]);

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
    };
    if (formOptions.showDescription !== false) {
      const trimmedDescription = form.description?.trim();
      payload.description = trimmedDescription || undefined;
    }
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
        "space-y-3 transition hover:-translate-y-0.5 hover:shadow-md"
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
          <div className="grid grid-cols-5 items-center gap-2 text-[0.75rem] leading-tight">
            {metrics.map((metric) => (
              <div
                key={metric.key}
                title={metric.title}
                className={cn(
                  "flex min-w-0 items-center justify-end rounded-sm px-2 py-0.5",
                  metric.accent && metric.value !== "—"
                    ? "bg-slate-100 font-semibold text-slate-900 dark:bg-slate-800 dark:text-slate-100"
                    : "text-slate-600 dark:text-slate-300"
                )}
              >
                <span className="truncate">{metric.value}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {editing && (
        <div className="flex flex-col gap-3">
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
          {formOptions.showDescription !== false ? (
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
          ) : null}
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
  const operationSearchRef = useRef("");
  const [operationSearch, setOperationSearch] = useState("");

  useEffect(() => {
    operationSearchRef.current = "";
    setOperationSearch("");
  }, [docDefinition?.key, docIdNumber]);

  const loadDoc = useCallback(
    async (options = {}) => {
      const detail = docDefinition?.detail || {};
      if (!detail.docAction || !detail.operationsAction) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const requestedSearch =
          typeof options.search === "string"
            ? options.search.trim()
            : operationSearchRef.current;
        const searchValue = requestedSearch || "";
        if (Object.prototype.hasOwnProperty.call(options, "search")) {
          operationSearchRef.current = searchValue;
        }
        const buildDocPayload = detail.buildDocPayload || ((docId) => docId);
        const buildOpsPayload =
          detail.buildOperationsPayload ||
          ((docId, params) => {
            if (docDefinition?.key === "inventory") {
              return {
                document_ids: [docId],
                search: params?.search || undefined,
                limit: params?.limit ?? 100,
              };
            }
            return docId;
          });
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
        const shouldUseBatch =
          Boolean(batchConfig?.buildRequest) && searchValue.length === 0;

        const mergeInventorySearch = (payload) => {
          if (docDefinition?.key !== "inventory") {
            return payload;
          }
          if (searchValue.length === 0) {
            return payload;
          }

          const base =
            payload && typeof payload === "object" && !Array.isArray(payload)
              ? { ...payload }
              : { document_ids: [docIdNumber] };

          if (
            !Array.isArray(base.document_ids) ||
            base.document_ids.length === 0
          ) {
            base.document_ids = [docIdNumber];
          }

          base.search = searchValue;

          if (!Object.prototype.hasOwnProperty.call(base, "limit")) {
            base.limit = 100;
          }

          return base;
        };

        if (shouldUseBatch) {
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

        const operationsPayloadBase = buildOpsPayload(docIdNumber, {
          search: searchValue || undefined,
        });
        const operationsPayload = mergeInventorySearch(operationsPayloadBase);

        const [docResponse, opsResponse] = await Promise.all([
          api(detail.docAction, buildDocPayload(docIdNumber)),
          api(detail.operationsAction, operationsPayload),
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
    },
    [api, docDefinition, docIdNumber]
  );

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

  const actionButtons = useMemo(() => {
    const detail = docDefinition?.detail || {};
    const isInventory = docDefinition?.key === "inventory";

    const performLabel = () => {
      if (isInventory) {
        const value = t("doc.inventory.close");
        return value === "doc.inventory.close" ? "Закрыть" : value;
      }
      const value = t("doc.perform");
      return value === "doc.perform" ? "Провести" : value || "Провести";
    };

    const cancelLabel = () => {
      if (isInventory) {
        const value = t("doc.inventory.open");
        return value === "doc.inventory.open" ? "Открыть" : value;
      }
      const value = t("doc.cancel_perform");
      return value === "doc.cancel_perform"
        ? "Отменить проведение"
        : value || "Отменить проведение";
    };

    const lockLabel = () => {
      const value = t("doc.lock");
      return value === "doc.lock" ? "Заблокировать" : value;
    };

    const unlockLabel = () => {
      const value = t("doc.unlock");
      return value === "doc.unlock" ? "Разблокировать" : value;
    };

    const results = [];

    if (detail.performAction) {
      results.push({
        key: "perform",
        visible: !doc?.performed,
        onClick: handlePerform,
        variant: "primary",
        label: performLabel(),
      });
    }

    if (detail.cancelPerformAction) {
      results.push({
        key: "cancel-perform",
        visible: Boolean(doc?.performed),
        onClick: handleCancelPerform,
        variant: "ghost",
        label: cancelLabel(),
      });
    }

    if (detail.lockAction) {
      results.push({
        key: "lock",
        visible: !doc?.blocked,
        onClick: handleLock,
        variant: "ghost",
        label: lockLabel(),
      });
    }

    if (detail.unlockAction) {
      results.push({
        key: "unlock",
        visible: Boolean(doc?.blocked),
        onClick: handleUnlock,
        variant: "ghost",
        label: unlockLabel(),
      });
    }

    results.push({
      key: "print",
      visible: true,
      onClick: handlePrint,
      variant: "ghost",
      label:
        t("doc.print") === "doc.print" ? "Печать" : t("doc.print") || "Печать",
    });

    return results.filter((action) => action.visible);
  }, [
    doc?.blocked,
    doc?.performed,
    docDefinition,
    handleCancelPerform,
    handleLock,
    handlePerform,
    handlePrint,
    handleUnlock,
    t,
  ]);

  const nothingLabel = useMemo(() => {
    const value = t("doc.no_ops") || t("common.nothing");
    return value || "Операций ещё нет";
  }, [t]);

  const metaSegments = useMemo(() => {
    if (!doc) return [];
    const builder = docDefinition?.detail?.buildMetaSegments;
    if (typeof builder === "function") {
      try {
        const built = builder(doc, { fmt, unixToLocal, t });
        if (Array.isArray(built)) {
          return built.filter(Boolean);
        }
      } catch (err) {
        console.warn("[doc_page] meta builder failed", err);
      }
    }
    const currency = doc.currency?.code_chr || "UZS";
    const roundTo = doc.price_type?.round_to ?? null;
    return [
      doc.date ? unixToLocal(doc.date) : null,
      doc.partner?.name || null,
      fmt.money(doc.amount ?? 0, currency, roundTo),
    ].filter(Boolean);
  }, [doc, docDefinition, fmt, t, unixToLocal]);

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

  const partnerValue = useMemo(() => {
    if (!doc) return "—";
    const detail = docDefinition?.detail || {};
    if (typeof detail.buildPartnerValue === "function") {
      try {
        const value = detail.buildPartnerValue(doc);
        if (value !== undefined && value !== null && value !== "") {
          return value;
        }
      } catch (err) {
        console.warn("[doc_page] partner builder failed", err);
      }
    }
    return doc.partner?.name || "—";
  }, [doc, docDefinition]);

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

  const operationSearchPlaceholder = useMemo(() => {
    const detailKey = docDefinition?.detail?.operationSearchPlaceholder;
    if (detailKey) {
      const translated = t(detailKey);
      if (translated && translated !== detailKey) {
        return translated;
      }
    }
    const labelKey = docDefinition?.labels?.operationSearchPlaceholder;
    if (labelKey) {
      const translated = t(labelKey);
      if (translated && translated !== labelKey) {
        return translated;
      }
    }
    const fallbackKey = "doc.inventory.operations.search";
    const fallback = t(fallbackKey);
    if (fallback && fallback !== fallbackKey) {
      return fallback;
    }
    return "Поиск по операциям";
  }, [docDefinition, t]);

  const handleOperationSearchChange = useCallback((event) => {
    setOperationSearch(event.target.value);
  }, []);

  const handleOperationSearchSubmit = useCallback(() => {
    const trimmed = operationSearch.trim();
    operationSearchRef.current = trimmed;
    setOperationSearch(trimmed);
    loadDoc({ search: trimmed });
  }, [loadDoc, operationSearch]);

  const handleOperationSearchKeyDown = useCallback(
    (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        handleOperationSearchSubmit();
      }
    },
    [handleOperationSearchSubmit]
  );

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
        {docDefinition?.key === "inventory" ? (
          <div className="mt-2 w-full flex items-center gap-2">
            <input
              type="search"
              value={operationSearch}
              onChange={handleOperationSearchChange}
              onKeyDown={handleOperationSearchKeyDown}
              placeholder={operationSearchPlaceholder}
              className={inputClass("flex-1")}
              aria-label={operationSearchPlaceholder}
            />
            <button
              type="button"
              className={iconButtonClass({ variant: "secondary" })}
              onClick={handleOperationSearchSubmit}
              aria-label={t("common.search") || "Поиск"}
              title={t("common.search") || "Поиск"}
            >
              <i className="fa-solid fa-magnifying-glass" aria-hidden="true" />
            </button>
          </div>
        ) : null}
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
          <span className="truncate">{partnerValue}</span>
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
              {actionButtons.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  className={buttonClass({
                    variant: action.variant,
                    size: "md",
                  })}
                  onClick={action.onClick}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
