import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import {
  DEFAULT_DOC_TYPE,
  getDocDefinition,
} from "../config/docDefinitions.js";
import {
  buttonClass,
  cardClass,
  inputClass,
  labelClass,
  mutedTextClass,
  sectionClass,
} from "../lib/ui";
import { cn } from "../lib/utils";

const REQUIRED_FALLBACK = "Поле обязательно";
const REFERENCE_FALLBACK_MESSAGE =
  "Справочник недоступен, введите идентификатор вручную";

function getLocalizedText(t, key, fallback) {
  if (!key) return fallback;
  const value = t(key);
  return value === key ? fallback : value;
}

function toDateInputValue(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function dateStringToUnix(value) {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return Math.floor(parsed.getTime() / 1000);
}

function defaultTransformOptions(data = {}) {
  const list = Array.isArray(data.result) ? data.result : [];
  return list
    .map((item) => {
      const id = item?.id ?? item?.ID ?? item?.code ?? item?.Code ?? null;
      if (!id) return null;
      const label =
        item?.label ||
        item?.name ||
        item?.Name ||
        item?.fullname ||
        item?.FullName ||
        `#${id}`;
      return {
        value: String(id),
        label,
        raw: item,
      };
    })
    .filter(Boolean);
}

function initializeForm(createConfig, helpers) {
  if (!createConfig) return {};
  const fields = Array.isArray(createConfig.fields) ? createConfig.fields : [];
  const defaultsSource =
    typeof createConfig.initialValues === "function"
      ? createConfig.initialValues(helpers)
      : createConfig.initialValues || {};
  const defaults = defaultsSource || {};
  const base = {};
  const today = helpers?.formatDateInput
    ? helpers.formatDateInput(new Date())
    : toDateInputValue(new Date());

  fields.forEach((field) => {
    let value;
    if (Object.prototype.hasOwnProperty.call(defaults, field.key)) {
      value = defaults[field.key];
    } else if (field.type === "date") {
      value = today;
    } else if (field.defaultValue !== undefined) {
      value =
        typeof field.defaultValue === "function"
          ? field.defaultValue(helpers)
          : field.defaultValue;
    } else {
      value = "";
    }
    base[field.key] =
      value === null || value === undefined ? "" : String(value);
  });

  return base;
}

function extractCreatedId(response) {
  if (!response) return null;
  const { result } = response;
  if (result?.new_id != null) return Number(result.new_id);
  if (Array.isArray(result?.ids) && result.ids[0] != null) {
    return Number(result.ids[0]);
  }
  if (result?.id != null) return Number(result.id);
  if (response?.new_id != null) return Number(response.new_id);
  return null;
}

export default function DocNewPage({ definition: definitionProp }) {
  const { api, setAppTitle, toNumber } = useApp();
  const { t, locale } = useI18n();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const typeParam = searchParams.get("type") || DEFAULT_DOC_TYPE;

  const docDefinition = useMemo(() => {
    if (definitionProp) return definitionProp;
    return getDocDefinition(typeParam);
  }, [definitionProp, typeParam]);

  const createConfig = docDefinition?.create ?? null;

  const initialForm = useMemo(
    () => initializeForm(createConfig, { formatDateInput: toDateInputValue }),
    [createConfig]
  );

  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState({});
  const [references, setReferences] = useState({});
  const [referencesLoading, setReferencesLoading] = useState(false);
  const [referencesError, setReferencesError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(initialForm);
    setFieldErrors({});
  }, [initialForm]);

  const docsPath = useMemo(() => {
    const builder = docDefinition?.navigation?.buildDocsPath;
    return typeof builder === "function" ? builder() : "/docs";
  }, [docDefinition]);

  const buildDocPath = useMemo(
    () =>
      docDefinition?.navigation?.buildDocPath || ((doc) => `/doc/${doc.id}`),
    [docDefinition]
  );

  const backLabel = useMemo(
    () => getLocalizedText(t, "nav.back", "Назад"),
    [t]
  );

  const cancelLabel = useMemo(
    () => getLocalizedText(t, "common.cancel", "Отмена"),
    [t]
  );

  const savingLabel = useMemo(
    () => getLocalizedText(t, "common.saving", "Сохранение..."),
    [t]
  );

  const submitLabel = useMemo(() => {
    if (!createConfig) return getLocalizedText(t, "common.create", "Создать");
    return getLocalizedText(
      t,
      createConfig.submitLabelKey,
      createConfig.submitLabelFallback ||
        getLocalizedText(t, "common.create", "Создать")
    );
  }, [createConfig, t]);

  const title = useMemo(() => {
    if (!createConfig) return null;
    const fallbackTitle =
      getLocalizedText(t, docDefinition?.labels?.title, "Новый документ") ||
      "Новый документ";
    return getLocalizedText(
      t,
      createConfig.titleKey,
      createConfig.titleFallback || fallbackTitle
    );
  }, [createConfig, docDefinition, t]);

  useEffect(() => {
    if (title) {
      setAppTitle(title);
    }
  }, [locale, setAppTitle, title]);

  const handleGoBack = useCallback(() => {
    navigate(docsPath);
  }, [docsPath, navigate]);

  useEffect(() => {
    let cancelled = false;
    const refsConfig = createConfig?.references;
    if (!createConfig || !refsConfig || Object.keys(refsConfig).length === 0) {
      setReferences({});
      setReferencesError(null);
      setReferencesLoading(false);
      return () => {
        cancelled = true;
      };
    }

    async function load() {
      setReferencesLoading(true);
      setReferencesError(null);
      const next = {};
      const errors = [];

      await Promise.all(
        Object.entries(refsConfig).map(async ([key, descriptor]) => {
          if (!descriptor) {
            next[key] = [];
            return;
          }

          if (!descriptor.action) {
            next[key] = Array.isArray(descriptor.options)
              ? descriptor.options
              : [];
            return;
          }

          try {
            const { data } = await api(
              descriptor.action,
              descriptor.params || {}
            );
            const transform =
              typeof descriptor.transform === "function"
                ? descriptor.transform
                : defaultTransformOptions;
            const rawOptions = transform(data);
            const normalized = Array.isArray(rawOptions) ? rawOptions : [];
            next[key] = normalized
              .map((option) => {
                if (!option) return null;
                if (option.value == null) {
                  const rawId =
                    option.id ??
                    option.ID ??
                    option.code ??
                    option.Code ??
                    null;
                  if (rawId == null) return null;
                  const label =
                    option.label ||
                    option.name ||
                    option.Name ||
                    option.full_name ||
                    option.FullName ||
                    `#${rawId}`;
                  return {
                    value: String(rawId),
                    label,
                    raw: option.raw ?? option,
                  };
                }
                return {
                  value: String(option.value),
                  label:
                    option.label ||
                    option.name ||
                    option.Name ||
                    String(option.value),
                  raw: option.raw ?? option,
                };
              })
              .filter(Boolean);
          } catch (err) {
            console.warn("[doc_new] reference fetch failed", key, err);
            if (!descriptor.optional) {
              errors.push(err);
            }
            next[key] = [];
          }
        })
      );

      if (cancelled) return;
      setReferences(next);
      setReferencesError(errors[0] || null);
      setReferencesLoading(false);
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [api, createConfig]);

  useEffect(() => {
    if (!createConfig) return;
    setForm((prev) => {
      const next = { ...prev };
      let changed = false;
      const fields = Array.isArray(createConfig.fields)
        ? createConfig.fields
        : [];

      fields.forEach((field) => {
        if (field.type !== "select" || !field.autoSelectFirst) return;
        if (next[field.key]) return;

        let options = [];
        if (field.referenceKey) {
          options = references[field.referenceKey] || [];
        } else if (typeof field.options === "function") {
          const customOptions = field.options({
            t,
            locale,
            references,
            docDefinition,
          });
          if (Array.isArray(customOptions)) {
            options = customOptions
              .map((option) => {
                if (!option) return null;
                const optionValue = option.value ?? option.id;
                if (optionValue == null) return null;
                const label =
                  option.label ||
                  option.name ||
                  option.Name ||
                  String(optionValue);
                return {
                  value: String(optionValue),
                  label,
                  raw: option.raw ?? option,
                };
              })
              .filter(Boolean);
          }
        }

        if (Array.isArray(options) && options.length > 0) {
          const first = options[0];
          if (first?.value) {
            next[field.key] = String(first.value);
            changed = true;
          }
        }
      });

      return changed ? next : prev;
    });
  }, [createConfig, docDefinition, locale, references, t]);

  const handleFieldChange = useCallback((key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const handleSubmit = useCallback(
    async (event) => {
      if (event) event.preventDefault();
      if (!createConfig) return;

      const fields = Array.isArray(createConfig.fields)
        ? createConfig.fields
        : [];
      const errors = {};

      fields.forEach((field) => {
        const value = form[field.key];
        if (field.required && (value === undefined || value === "")) {
          errors[field.key] = getLocalizedText(
            t,
            "validation.required",
            REQUIRED_FALLBACK
          );
          return;
        }
        if (field.type === "date" && value) {
          const unix = dateStringToUnix(value);
          if (!unix) {
            errors[field.key] = getLocalizedText(
              t,
              "validation.invalid_date",
              "Некорректная дата"
            );
          }
        }
      });

      if (Object.keys(errors).length > 0) {
        setFieldErrors(errors);
        return;
      }

      setFieldErrors({});

      if (!createConfig.addAction) {
        showToast(
          getLocalizedText(t, "save_failed", "Не удалось создать документ"),
          { type: "error" }
        );
        return;
      }

      let payload;
      try {
        payload = createConfig.buildPayload(form, {
          toUnixTime: dateStringToUnix,
          toNumber,
          references,
        });
      } catch (err) {
        console.warn("[doc_new] payload build failed", err);
        const message =
          err?.message ||
          getLocalizedText(t, "save_failed", "Не удалось подготовить данные");
        showToast(message, { type: "error" });
        return;
      }

      if (!payload) {
        showToast(
          getLocalizedText(t, "save_failed", "Не удалось подготовить данные"),
          { type: "error" }
        );
        return;
      }

      setSaving(true);
      try {
        const { data } = await api(createConfig.addAction, payload);
        if (!data || data.ok === false) {
          const description =
            data?.description ||
            data?.result?.description ||
            data?.result?.error ||
            getLocalizedText(t, "save_failed", "Не удалось создать документ");
          showToast(description, { type: "error" });
          return;
        }

        const successMessage = getLocalizedText(
          t,
          createConfig.successMessageKey,
          createConfig.successMessageFallback || "Документ создан"
        );
        showToast(successMessage, { type: "success" });

        const newId = createConfig.resolveCreatedId
          ? createConfig.resolveCreatedId(data)
          : extractCreatedId(data);
        if (newId) {
          navigate(buildDocPath({ id: newId }), { replace: true });
        } else {
          navigate(docsPath, { replace: true });
        }
      } catch (err) {
        console.warn("[doc_new] submit error", err);
        showToast(
          err?.message ||
            getLocalizedText(t, "save_failed", "Не удалось создать документ"),
          { type: "error" }
        );
      } finally {
        setSaving(false);
      }
    },
    [
      api,
      buildDocPath,
      createConfig,
      docsPath,
      form,
      navigate,
      references,
      showToast,
      t,
      toNumber,
    ]
  );

  const referenceFallbackText = useMemo(
    () =>
      getLocalizedText(t, "doc.reference_fallback", REFERENCE_FALLBACK_MESSAGE),
    [t]
  );

  const renderField = useCallback(
    (field) => {
      const fieldId = `field-${field.key}`;
      const value = form[field.key] ?? "";
      const disabled = saving || field.disabled;
      const selectDisabled = disabled || referencesLoading;

      if (field.type === "textarea") {
        return (
          <textarea
            id={fieldId}
            value={value}
            onChange={(event) =>
              handleFieldChange(field.key, event.target.value)
            }
            className={inputClass("min-h-[6rem]")}
            placeholder={getLocalizedText(
              t,
              field.placeholderKey,
              field.placeholderFallback || ""
            )}
            disabled={disabled}
          />
        );
      }

      if (field.type === "date") {
        return (
          <input
            id={fieldId}
            type="date"
            value={value}
            onChange={(event) =>
              handleFieldChange(field.key, event.target.value)
            }
            className={inputClass()}
            disabled={disabled}
          />
        );
      }

      if (field.type === "number") {
        return (
          <input
            id={fieldId}
            type="number"
            inputMode={field.step ? "decimal" : "numeric"}
            step={field.step || "any"}
            value={value}
            onChange={(event) =>
              handleFieldChange(field.key, event.target.value)
            }
            className={inputClass()}
            placeholder={getLocalizedText(
              t,
              field.placeholderKey,
              field.placeholderFallback || ""
            )}
            disabled={disabled}
          />
        );
      }

      if (field.type === "select") {
        let options = [];
        if (typeof field.options === "function") {
          const customOptions = field.options({
            t,
            locale,
            references,
            docDefinition,
          });
          if (Array.isArray(customOptions)) {
            options = customOptions
              .map((option) => {
                if (!option) return null;
                const optionValue = option.value ?? option.id;
                if (optionValue == null) return null;
                const label =
                  option.label ||
                  option.name ||
                  option.Name ||
                  String(optionValue);
                return {
                  value: String(optionValue),
                  label,
                  raw: option.raw ?? option,
                };
              })
              .filter(Boolean);
          }
        } else if (field.referenceKey) {
          options = references[field.referenceKey] || [];
        }

        const hasOptions = Array.isArray(options) && options.length > 0;

        if (hasOptions) {
          const includeEmptyOption =
            field.allowEmptyOption !== false &&
            (!field.required || field.allowEmptyOption);
          return (
            <select
              id={fieldId}
              value={value}
              onChange={(event) =>
                handleFieldChange(field.key, event.target.value)
              }
              className={inputClass()}
              disabled={selectDisabled}
            >
              {includeEmptyOption ? (
                <option value="">
                  {getLocalizedText(t, "common.not_selected", "Не выбрано")}
                </option>
              ) : null}
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          );
        }

        if (field.fallbackType === "number" || field.fallbackType === "text") {
          const type = field.fallbackType === "number" ? "number" : "text";
          const inputMode =
            field.fallbackType === "number" ? "numeric" : undefined;
          return (
            <>
              <input
                id={fieldId}
                type={type}
                inputMode={inputMode}
                value={value}
                onChange={(event) =>
                  handleFieldChange(field.key, event.target.value)
                }
                className={inputClass()}
                placeholder={getLocalizedText(
                  t,
                  field.placeholderKey,
                  field.placeholderFallback || ""
                )}
                disabled={disabled}
              />
              <p className={cn(mutedTextClass(), "text-xs")}>
                {referenceFallbackText}
              </p>
            </>
          );
        }

        return (
          <select id={fieldId} disabled value="" className={inputClass()}>
            <option value="">
              {getLocalizedText(t, "common.nothing", "Нет данных")}
            </option>
          </select>
        );
      }

      return (
        <input
          id={fieldId}
          type="text"
          value={value}
          onChange={(event) => handleFieldChange(field.key, event.target.value)}
          className={inputClass()}
          placeholder={getLocalizedText(
            t,
            field.placeholderKey,
            field.placeholderFallback || ""
          )}
          disabled={disabled}
        />
      );
    },
    [
      docDefinition,
      form,
      handleFieldChange,
      locale,
      referenceFallbackText,
      references,
      referencesLoading,
      saving,
      t,
    ]
  );

  if (!docDefinition) {
    return (
      <section className={sectionClass()} id="doc-new">
        <div className={cardClass("space-y-4 p-6")}>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-50">
            {getLocalizedText(
              t,
              "doc.not_supported",
              "Тип документа не поддерживается"
            )}
          </h1>
          <div className="flex justify-end">
            <button
              type="button"
              className={buttonClass({ variant: "ghost", size: "sm" })}
              onClick={handleGoBack}
            >
              {backLabel}
            </button>
          </div>
        </div>
      </section>
    );
  }

  if (!createConfig) {
    return (
      <section className={sectionClass()} id="doc-new">
        <div className={cardClass("space-y-4 p-6")}>
          <p className={mutedTextClass()}>
            {getLocalizedText(
              t,
              "doc.create_not_supported",
              "Создание документа для этого типа недоступно"
            )}
          </p>
          <div className="flex justify-end">
            <button
              type="button"
              className={buttonClass({ variant: "ghost", size: "sm" })}
              onClick={handleGoBack}
            >
              {backLabel}
            </button>
          </div>
        </div>
      </section>
    );
  }

  const fields = Array.isArray(createConfig.fields) ? createConfig.fields : [];
  const formDescription = createConfig.descriptionKey
    ? getLocalizedText(
        t,
        createConfig.descriptionKey,
        createConfig.descriptionFallback || ""
      )
    : createConfig.descriptionFallback || "";
  const loadingText = getLocalizedText(t, "common.loading", "Загрузка...");
  const referencesFailedText = getLocalizedText(
    t,
    "doc.references_failed",
    "Не удалось загрузить справочники"
  );

  return (
    <section className={sectionClass()} id="doc-new">
      <form className="space-y-6" onSubmit={handleSubmit}>
        <div className={cardClass("space-y-6 p-6")}>
          <div className="space-y-2">
            <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-50">
              {title ||
                getLocalizedText(t, "doc.create_title", "Новый документ")}
            </h1>
            {formDescription ? (
              <p className={mutedTextClass()}>{formDescription}</p>
            ) : null}
          </div>

          {referencesLoading ? (
            <p className={mutedTextClass()}>{loadingText}</p>
          ) : null}

          {!referencesLoading && referencesError ? (
            <p className="text-sm text-red-600 dark:text-red-400">
              {referencesError?.message || referencesFailedText}
            </p>
          ) : null}

          <div className="space-y-4">
            {fields.map((field) => {
              const fieldId = `field-${field.key}`;
              const labelText = getLocalizedText(
                t,
                field.labelKey,
                field.fallbackLabel || field.key
              );
              const description = getLocalizedText(
                t,
                field.descriptionKey,
                field.descriptionFallback || ""
              );
              const errorText = fieldErrors[field.key];

              return (
                <div key={field.key} className="space-y-1">
                  <label
                    className={cn(
                      labelClass(),
                      field.required
                        ? "after:ml-1 after:text-red-500 after:content-['*']"
                        : null
                    )}
                    htmlFor={fieldId}
                  >
                    {labelText}
                  </label>
                  {description ? (
                    <p className={cn(mutedTextClass(), "text-xs")}>
                      {description}
                    </p>
                  ) : null}
                  {renderField(field)}
                  {errorText ? (
                    <p className="text-sm text-red-600 dark:text-red-400">
                      {errorText}
                    </p>
                  ) : null}
                </div>
              );
            })}
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              className={buttonClass({ variant: "ghost" })}
              onClick={handleGoBack}
              disabled={saving}
            >
              {cancelLabel}
            </button>
            <button
              type="submit"
              className={buttonClass({ variant: "primary" })}
              disabled={saving || referencesLoading}
            >
              {saving ? savingLabel : submitLabel}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
