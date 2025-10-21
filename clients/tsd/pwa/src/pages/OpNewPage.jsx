import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  BrowserMultiFormatReader,
  BarcodeFormat,
  DecodeHintType,
} from "@zxing/library";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
import scanSuccessSfx from "../audio/scan_success.mp3";
import scanFailSfx from "../audio/scan_fail.mp3";
import {
  buttonClass,
  cardClass,
  chipClass,
  iconButtonClass,
  inputClass,
  labelClass,
  mutedTextClass,
  sectionClass,
} from "../lib/ui";
import { cn } from "../lib/utils";
import { getDocDefinition } from "../config/docDefinitions.js";

const QUICK_QTY = [1, 5, 10, 12];

const SEARCH_MODES = {
  SCAN: "scan",
  NAME: "name",
  INSANT: "insant",
};

const ZXING_FORMATS = [
  BarcodeFormat.QR_CODE,
  BarcodeFormat.UPC_A,
  BarcodeFormat.UPC_E,
  BarcodeFormat.EAN_8,
  BarcodeFormat.EAN_13,
  BarcodeFormat.ITF,
  BarcodeFormat.PDF_417,
  BarcodeFormat.CODE_39,
  BarcodeFormat.CODE_128,
].filter(Boolean);

const BATCH_SEARCH_STEP_KEY = "search_list";
const BATCH_ADD_STEP_KEY = "add_operation";

const toPascalCase = (value = "") =>
  value
    .split(/[_\s]+/g)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join("");

const resolveBatchPathFromAction = (action) => {
  if (!action || typeof action !== "string") return null;
  const segments = action.split(".").filter(Boolean);
  if (segments.length < 3) return null;
  const resource = toPascalCase(segments[1]);
  const method = toPascalCase(segments[2]);
  if (!resource || !method) return null;
  return `${resource}/${method}`;
};

const createBatchAddPayload = ({ definition, docId, itemPlaceholder }) => {
  if (!definition?.key || !docId || !itemPlaceholder) return null;

  switch (definition.key) {
    case "inventory": {
      return [
        {
          document_id: docId,
          item_id: itemPlaceholder,
          actual_quantity: 1,
          datetime: Math.floor(Date.now() / 1000),
          update_actual_quantity: false,
        },
      ];
    }
    default:
      return null;
  }
};

const normalizeAudioSrc = (src) => {
  if (typeof src !== "string") return src;
  if (src.startsWith("data:application/octet-stream;base64")) {
    return src.replace(
      "data:application/octet-stream;base64",
      "data:audio/mpeg;base64"
    );
  }
  return src;
};

const SCAN_SUCCESS_SRC = normalizeAudioSrc(scanSuccessSfx);
const SCAN_FAIL_SRC = normalizeAudioSrc(scanFailSfx);

export default function OpNewPage({ definition: definitionProp }) {
  const { id } = useParams();
  const docId = Number(id);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { api, toNumber, setAppTitle } = useApp();
  const { t, fmt, locale } = useI18n();
  const { showToast } = useToast();

  const typeParam = searchParams.get("type") || undefined;
  const docDefinition = useMemo(
    () => definitionProp || getDocDefinition(typeParam),
    [definitionProp, typeParam]
  );

  const buildDocPath = useMemo(
    () =>
      docDefinition?.navigation?.buildDocPath || ((doc) => `/doc/${doc.id}`),
    [docDefinition]
  );

  const formOptions = docDefinition?.operation?.form || {};
  const showCostField = formOptions.showCost !== false;
  const showPriceField = formOptions.showPrice !== false;
  const autoFill = docDefinition?.operation?.autoFill || {};

  const initialDocContext = useMemo(
    () => ({
      price_type_id: null,
      stock_id: null,
      ...(docDefinition?.operation?.initialContext || {}),
    }),
    [docDefinition]
  );

  const [docCtx, setDocCtx] = useState(initialDocContext);
  const [barcodeValue, setBarcodeValue] = useState("");
  const [queryValue, setQueryValue] = useState("");
  const [quantity, setQuantity] = useState("");
  const [cost, setCost] = useState("");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");
  const [searchStatus, setSearchStatus] = useState("idle");
  const [picked, setPicked] = useState(null);
  const [saving, setSaving] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [searchMode, setSearchMode] = useState(SEARCH_MODES.SCAN);
  const [resultModalOpen, setResultModalOpen] = useState(false);
  const [resultItems, setResultItems] = useState([]);
  const priceRoundTo = docCtx?.price_type_round_to ?? null;
  const docCurrency = docCtx?.doc_currency ?? null;

  const videoRef = useRef(null);
  const readerRef = useRef(null);
  const barcodeInputRef = useRef(null);
  const successSoundRef = useRef(null);
  const failSoundRef = useRef(null);
  const instantQueueRef = useRef([]);
  const instantProcessingRef = useRef(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof Audio === "undefined") return;

    const successAudio = new Audio();
    successAudio.src = SCAN_SUCCESS_SRC;
    successAudio.preload = "auto";
    successAudio.load();
    successSoundRef.current = successAudio;

    const failAudio = new Audio();
    failAudio.src = SCAN_FAIL_SRC;
    failAudio.preload = "auto";
    failAudio.load();
    failSoundRef.current = failAudio;

    return () => {
      successAudio.pause();
      successAudio.src = "";
      failAudio.pause();
      failAudio.src = "";
    };
  }, []);

  const focusBarcodeInput = useCallback(() => {
    window.setTimeout(() => {
      barcodeInputRef.current?.focus();
    }, 0);
  }, []);

  const playSound = useCallback((soundRef) => {
    const audio = soundRef.current;
    if (!audio) return;
    try {
      audio.pause();
      if (audio.readyState < 2) {
        audio.load();
      }
      audio.currentTime = 0;
      const playPromise = audio.play();
      if (playPromise && typeof playPromise.catch === "function") {
        playPromise.catch((err) =>
          console.warn("[op_new] failed to play sound", err)
        );
      }
    } catch (err) {
      console.warn("[op_new] failed to play sound", err);
    }
  }, []);

  const playSuccessSound = useCallback(() => {
    playSound(successSoundRef);
  }, [playSound]);

  const playFailSound = useCallback(() => {
    playSound(failSoundRef);
  }, [playSound]);

  useEffect(() => {
    setDocCtx(initialDocContext);
  }, [initialDocContext]);

  const operationTitle = useMemo(() => {
    const key = docDefinition?.operation?.titleKey || "op.title";
    const translated = t(key);
    if (translated === key) {
      return docDefinition?.operation?.titleFallback || "Новая операция";
    }
    return translated;
  }, [docDefinition, t]);

  useEffect(() => {
    setAppTitle(operationTitle);
  }, [operationTitle, locale, setAppTitle]);

  useEffect(() => {
    const metaAction = docDefinition?.operation?.docMetaAction;
    if (!metaAction) return;

    let cancelled = false;
    async function loadDocMeta() {
      try {
        const buildPayload =
          docDefinition?.operation?.docMetaPayload || ((value) => value);
        const payload = buildPayload(docId);
        const { data } = await api(metaAction, payload);
        if (cancelled) return;
        const extractor =
          docDefinition?.operation?.extractDocContext || (() => ({}));
        const context = extractor(data) || {};
        setDocCtx((prev) => ({ ...prev, ...context }));
      } catch (err) {
        console.warn("[op_new] failed to fetch doc context", err);
      }
    }

    loadDocMeta();
    return () => {
      cancelled = true;
    };
  }, [api, docDefinition, docId]);

  const closeResultModal = useCallback(() => {
    setResultModalOpen(false);
    setResultItems([]);
  }, []);

  const handlePickItem = useCallback(
    (item) => {
      setPicked(item);
      closeResultModal();
      if (autoFill.priceFromItem && showPriceField && item?.price != null) {
        setPrice(String(item.price));
      }
      if (
        autoFill.costFromItem &&
        showCostField &&
        item?.last_purchase_cost != null
      ) {
        setCost(String(item.last_purchase_cost));
      }
      setSearchStatus("done");
      window.setTimeout(() => {
        document.getElementById("qty")?.focus();
      }, 0);
    },
    [
      autoFill.costFromItem,
      autoFill.priceFromItem,
      closeResultModal,
      showCostField,
      showPriceField,
    ]
  );

  const resetFormState = useCallback(() => {
    setQuantity("");
    if (showCostField) setCost("");
    if (showPriceField) setPrice("");
    setBarcodeValue("");
    setQueryValue("");
    setPicked(null);
    setSearchStatus("idle");
    setResultModalOpen(false);
    setResultItems([]);
    focusBarcodeInput();
  }, [
    focusBarcodeInput,
    setResultModalOpen,
    setResultItems,
    showCostField,
    showPriceField,
  ]);

  const performAddOperation = useCallback(
    async ({
      pickedItem,
      quantityValue,
      costValue,
      priceValue,
      descriptionValue = "",
      resetForm = true,
      suppressSuccessToast = false,
      onSuccess,
      onFailure,
    }) => {
      if (!pickedItem?.id) {
        showToast(t("select_product_first") || "Сначала выберите товар", {
          type: "error",
        });
        onFailure?.();
        return false;
      }

      const qtyNumber = toNumber(quantityValue);
      if (!qtyNumber || qtyNumber <= 0) {
        showToast(t("fill_required_fields") || "Заполните обязательные поля", {
          type: "error",
        });
        onFailure?.();
        return false;
      }

      if (pickedItem?.unit_piece && !Number.isInteger(qtyNumber)) {
        showToast(t("qty.integer_only") || "Количество должно быть целым", {
          type: "error",
        });
        onFailure?.();
        return false;
      }

      const costNumber =
        showCostField &&
        costValue !== undefined &&
        costValue !== null &&
        costValue !== ""
          ? toNumber(costValue)
          : undefined;
      const priceNumber =
        showPriceField &&
        priceValue !== undefined &&
        priceValue !== null &&
        priceValue !== ""
          ? toNumber(priceValue)
          : undefined;
      const trimmedDescription =
        typeof descriptionValue === "string" ? descriptionValue.trim() : "";

      const buildPayload =
        docDefinition?.operation?.buildAddPayload || (() => null);
      const payload = buildPayload({
        docId,
        picked: pickedItem,
        quantity: qtyNumber,
        cost: costNumber,
        price: priceNumber,
        description: trimmedDescription,
        docCtx,
      });

      if (!payload) {
        showToast(t("save_failed") || "Не удалось сохранить операцию", {
          type: "error",
        });
        onFailure?.();
        return false;
      }

      setSaving(true);
      try {
        const addAction = docDefinition?.operation?.addAction;
        if (!addAction) {
          throw new Error("Operation add action is not configured");
        }
        const { data } = await api(addAction, payload);
        const handleAddResponse =
          docDefinition?.operation?.handleAddResponse ||
          ((response) => response?.result?.row_affected > 0);

        if (handleAddResponse(data, { docCtx, picked: pickedItem, payload })) {
          if (!suppressSuccessToast) {
            showToast(t("toast.op_added") || "Операция добавлена", {
              type: "success",
            });
          }
          if (resetForm) {
            resetFormState();
          }
          onSuccess?.();
          return true;
        }

        throw new Error(data?.description || "Save failed");
      } catch (err) {
        showToast(
          err.message || t("save_failed") || "Не удалось сохранить операцию",
          { type: "error", duration: 2400 }
        );
        onFailure?.();
        return false;
      } finally {
        setSaving(false);
      }
    },
    [
      api,
      docCtx,
      docDefinition,
      resetFormState,
      showCostField,
      showPriceField,
      showToast,
      t,
      toNumber,
    ]
  );

  const handleInstantSearch = useCallback(
    async (queryText) => {
      if (docDefinition?.key !== "inventory") {
        const searchDescriptor = docDefinition?.operation?.search;
        if (!searchDescriptor?.action || !searchDescriptor?.buildParams) {
          console.warn("[op_new] search not configured for doc type");
          showToast(
            t("search_not_configured") ||
              "Поиск для данного документа не настроен",
            { type: "error" }
          );
          playFailSound();
          setSearchStatus("error");
          focusBarcodeInput();
          return;
        }

        closeResultModal();
        setPicked(null);
        setSearchStatus("loading");

        try {
          const params = searchDescriptor.buildParams({
            queryText,
            docCtx,
            docId,
            mode: SEARCH_MODES.INSANT,
          });

          const { data } = await api(searchDescriptor.action, params);
          const normalize = searchDescriptor.normalize || (() => []);
          const normalizedItems = normalize(data, {
            docCtx,
            queryText,
            mode: SEARCH_MODES.INSANT,
            docId,
          });

          if (!Array.isArray(normalizedItems) || normalizedItems.length === 0) {
            setSearchStatus("empty");
            showToast(t("common.nothing") || "Ничего не найдено", {
              type: "error",
            });
            playFailSound();
            return;
          }

          if (normalizedItems.length > 1) {
            setSearchStatus("multi");
            showToast(
              t("op.search.choose_prompt") ||
                "Найдено несколько результатов, уточните запрос",
              { type: "error" }
            );
            playFailSound();
            return;
          }

          const item = normalizedItems[0];
          const costFromItem =
            autoFill.costFromItem &&
            showCostField &&
            item?.last_purchase_cost != null
              ? item.last_purchase_cost
              : undefined;
          const priceFromItem =
            autoFill.priceFromItem && showPriceField && item?.price != null
              ? item.price
              : undefined;

          const success = await performAddOperation({
            pickedItem: item,
            quantityValue: 1,
            costValue: costFromItem,
            priceValue: priceFromItem,
            descriptionValue: "",
            resetForm: false,
            onSuccess: playSuccessSound,
            onFailure: playFailSound,
          });

          setSearchStatus(success ? "done" : "error");
        } catch (err) {
          console.warn("[search] instant error", err);
          setSearchStatus("error");
          showToast(t("search_error") || "Ошибка поиска", {
            type: "error",
          });
          playFailSound();
        } finally {
          focusBarcodeInput();
        }
        return;
      }

      const addPath = resolveBatchPathFromAction(
        docDefinition?.operation?.addAction
      );
      const addPayload = createBatchAddPayload({
        definition: docDefinition,
        docId,
        itemPlaceholder: `\${${BATCH_SEARCH_STEP_KEY}.result.0}`,
      });

      if (!addPath || !addPayload) {
        console.warn("[op_new] instant batch not configured for doc type");
        showToast(
          t("instant.batch_not_supported") ||
            "Мгновенный режим для этого документа пока недоступен",
          { type: "error" }
        );
        playFailSound();
        setSearchStatus("error");
        focusBarcodeInput();
        return;
      }

      const batchPayload = {
        stop_on_error: true,
        requests: [
          {
            key: BATCH_SEARCH_STEP_KEY,
            path: "Item/Search",
            payload: {
              barcode: queryText,
              limit: 1,
            },
          },
          {
            key: BATCH_ADD_STEP_KEY,
            path: addPath,
            payload: addPayload,
          },
        ],
      };

      closeResultModal();
      setPicked(null);
      setSearchStatus("loading");

      try {
        const { data } = await api("batch.run", batchPayload);
        let errored = false;

        if (!data?.ok || data.result.some((r) => !r.response?.ok)) {
          errored = true;
        }
        if (errored) {
          const description =
            searchResponse?.result?.description ||
            t("common.nothing") ||
            "Ошибка выполнения";
          setSearchStatus("error");
          showToast(description, { type: "error" });
          playFailSound();
          return;
        }

        showToast(t("toast.op_added") || "Операция добавлена", {
          type: "success",
        });
        playSuccessSound();
        setSearchStatus("done");
      } catch (err) {
        console.warn("[op_new] instant batch error", err);
        showToast(
          err?.message || t("save_failed") || "Не удалось выполнить операцию",
          { type: "error" }
        );
        playFailSound();
        setSearchStatus("error");
      } finally {
        focusBarcodeInput();
      }
    },
    [
      api,
      autoFill,
      closeResultModal,
      docCtx,
      docDefinition,
      docId,
      focusBarcodeInput,
      performAddOperation,
      playFailSound,
      playSuccessSound,
      setPicked,
      setSearchStatus,
      showCostField,
      showPriceField,
      showToast,
      t,
    ]
  );

  const processInstantQueue = useCallback(async () => {
    if (instantProcessingRef.current) return;
    instantProcessingRef.current = true;
    try {
      while (instantQueueRef.current.length > 0) {
        const nextBarcode = instantQueueRef.current.shift();
        // eslint-disable-next-line no-await-in-loop
        await handleInstantSearch(nextBarcode);
      }
    } finally {
      instantProcessingRef.current = false;
    }
  }, [handleInstantSearch]);

  const enqueueInstantSearch = useCallback(
    (queryText) => {
      const normalized = queryText?.trim();
      if (!normalized) {
        setBarcodeValue("");
        focusBarcodeInput();
        return;
      }

      instantQueueRef.current.push(normalized);
      setBarcodeValue("");
      setSearchStatus("loading");
      focusBarcodeInput();
      void processInstantQueue();
    },
    [focusBarcodeInput, processInstantQueue, setBarcodeValue, setSearchStatus]
  );

  const runSearch = useCallback(
    async (value, mode = searchMode) => {
      const queryText = value?.trim();
      if (!queryText) {
        if (mode === SEARCH_MODES.INSANT) {
          setBarcodeValue("");
          focusBarcodeInput();
        }
        return;
      }
      if (mode === SEARCH_MODES.INSANT) {
        enqueueInstantSearch(queryText);
        return;
      }
      const searchDescriptor = docDefinition?.operation?.search;
      if (!searchDescriptor?.action || !searchDescriptor?.buildParams) {
        console.warn("[op_new] search not configured for doc type");
        return;
      }
      setSearchStatus("loading");
      try {
        const params = searchDescriptor.buildParams({
          queryText,
          docCtx,
          docId,
          mode,
        });

        const { data } = await api(searchDescriptor.action, params);
        const normalize = searchDescriptor.normalize || (() => []);
        const normalizedItems = normalize(data, {
          docCtx,
          queryText,
          mode,
          docId,
        });

        if (!Array.isArray(normalizedItems) || normalizedItems.length === 0) {
          setPicked(null);
          closeResultModal();
          setSearchStatus("empty");
          if (mode === SEARCH_MODES.INSANT) {
            playFailSound();
            setBarcodeValue("");
            focusBarcodeInput();
          }
          return;
        }

        if (mode === SEARCH_MODES.NAME && normalizedItems.length > 1) {
          setResultItems(normalizedItems);
          setResultModalOpen(true);
          setSearchStatus("multi");
          return;
        }

        handlePickItem(normalizedItems[0]);
      } catch (err) {
        console.warn("[search] error", err);
        setPicked(null);
        closeResultModal();
        setSearchStatus("error");
        if (mode === SEARCH_MODES.INSANT) {
          playFailSound();
          setBarcodeValue("");
          focusBarcodeInput();
        }
      }
    },
    [
      api,
      closeResultModal,
      docDefinition,
      docCtx,
      docId,
      focusBarcodeInput,
      enqueueInstantSearch,
      handlePickItem,
      playFailSound,
      searchMode,
      setBarcodeValue,
    ]
  );

  const ensureReader = useCallback(async () => {
    if (readerRef.current) return readerRef.current;

    const hints = new Map();
    if (DecodeHintType?.POSSIBLE_FORMATS) {
      hints.set(DecodeHintType.POSSIBLE_FORMATS, ZXING_FORMATS);
    }
    if (DecodeHintType?.TRY_HARDER) {
      hints.set(DecodeHintType.TRY_HARDER, true);
    }
    if (DecodeHintType?.ALSO_INVERTED) {
      hints.set(DecodeHintType.ALSO_INVERTED, true);
    }

    const reader = new BrowserMultiFormatReader(hints, 200);
    reader.timeBetweenDecodingAttempts = 50;
    readerRef.current = reader;
    return readerRef.current;
  }, []);

  const stopScan = useCallback(() => {
    setScanning(false);
    if (readerRef.current) {
      console.log("Stopping scanner...");

      readerRef.current.reset();
    }
    if (videoRef.current?.srcObject) {
      console.log("Stopping video stream...");

      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    console.log("Scanner stopped.");

    setScanning(false);
  }, []);

  const handleModalDismiss = useCallback(() => {
    closeResultModal();
    setSearchStatus("idle");
  }, [closeResultModal]);

  useEffect(() => {
    setSearchStatus("idle");
    closeResultModal();
    if (searchMode === SEARCH_MODES.NAME) {
      stopScan();
      window.setTimeout(
        () => document.getElementById("product-query")?.focus(),
        0
      );
      return;
    }

    focusBarcodeInput();
  }, [searchMode, closeResultModal, stopScan, focusBarcodeInput]);

  const startScan = async () => {
    if (scanning) return;
    if (
      searchMode !== SEARCH_MODES.SCAN &&
      searchMode !== SEARCH_MODES.INSANT
    ) {
      return;
    }

    try {
      const reader = await ensureReader();
      console.log("reader", reader);

      const constraints = {
        video: { facingMode: { ideal: "environment" } },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute("playsinline", "true");
        await videoRef.current.play();
      }

      console.log("Video started, starting scan...");

      setScanning(true);

      reader.decodeFromVideoDevice(null, videoRef.current, (result, err) => {
        console.log("scan result", { result, err });
        if (result) {
          const text = result.getText();
          stopScan();
          runSearch(text, searchMode);
        }
        if (
          err &&
          !(err.name === "Камера не найдена" || err.name === "NotFoundError")
        ) {
          // console.error(err);
        }
      });
    } catch (err) {
      console.error("[scan] start error", err);
      const messageKey =
        err?.name === "NotAllowedError"
          ? "camera_permission_denied"
          : err?.name === "NotFoundError" ||
            err?.name === "OverconstrainedError"
          ? "camera_not_found"
          : "camera_open_failed";
      showToast(t(messageKey) || "Не удалось открыть камеру", {
        type: "error",
      });
    }
  };

  const handleSubmit = async () => {
    await performAddOperation({
      pickedItem: picked,
      quantityValue: quantity,
      costValue: cost,
      priceValue: price,
      descriptionValue: description,
      resetForm: true,
    });
  };

  const descriptionPreview = useMemo(() => {
    if (!description.trim() || !picked) return "";
    return `${t("op.description") || "Описание"}: ${description.trim()}`;
  }, [description, picked, t]);

  const lpcLabel = useMemo(() => {
    if (!showCostField || picked?.last_purchase_cost == null) return null;
    return fmt.money(picked.last_purchase_cost, docCurrency, priceRoundTo);
  }, [fmt, picked, priceRoundTo, showCostField]);

  const priceLabel = useMemo(() => {
    if (!showPriceField || picked?.price == null) return null;
    return fmt.money(picked.price, docCurrency, priceRoundTo);
  }, [fmt, picked, priceRoundTo, showPriceField]);

  if (!docDefinition) {
    return (
      <section className={sectionClass()} id="op-new">
        <h1 className="text-xs font-semibold text-slate-900 dark:text-slate-50">
          {operationTitle}
        </h1>
        <p className={mutedTextClass()}>
          {t("doc.not_supported") || "Тип документа не поддерживается"}
        </p>
      </section>
    );
  }

  return (
    <section className={sectionClass()} id="op-new">
      <h1 className="text-xs font-semibold text-slate-900 dark:text-slate-50">
        {operationTitle}
      </h1>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className={iconButtonClass({
            variant: searchMode === SEARCH_MODES.SCAN ? "primary" : "ghost",
          })}
          onClick={() => setSearchMode(SEARCH_MODES.SCAN)}
          aria-label={t("op.mode.scan") || "Режим сканирования"}
          title={t("op.mode.scan") || "Режим сканирования"}
        >
          <i className="fa-solid fa-barcode" aria-hidden="true" />
        </button>
        <button
          type="button"
          className={iconButtonClass({
            variant: searchMode === SEARCH_MODES.NAME ? "primary" : "ghost",
          })}
          onClick={() => setSearchMode(SEARCH_MODES.NAME)}
          aria-label={t("op.mode.name") || "Поиск по названию"}
          title={t("op.mode.name") || "Поиск по названию"}
        >
          <i className="fa-solid fa-magnifying-glass" aria-hidden="true" />
        </button>
        <button
          type="button"
          className={iconButtonClass({
            variant: searchMode === SEARCH_MODES.INSANT ? "primary" : "ghost",
          })}
          onClick={() => setSearchMode(SEARCH_MODES.INSANT)}
          aria-label={t("op.mode.insant") || "Мгновенное добавление"}
          title={t("op.mode.insant") || "Мгновенное добавление"}
        >
          <i className="fa-solid fa-bolt" aria-hidden="true" />
        </button>
      </div>

      {[SEARCH_MODES.SCAN, SEARCH_MODES.INSANT].includes(searchMode) && (
        <>
          <div
            id="scanner"
            className={cn(
              scanning ? "space-y-4" : "hidden",
              cardClass("space-y-4")
            )}
          >
            <video
              id="preview"
              ref={videoRef}
              playsInline
              className="w-full rounded-xl"
            />
            <div className="flex items-center justify-between gap-3">
              <span className={mutedTextClass()}>
                {t("scanner.hint") || "Наведи камеру на штрих-код"}
              </span>
              <button
                id="btn-close-scan"
                type="button"
                className={iconButtonClass()}
                onClick={stopScan}
                aria-label={t("common.cancel") || "Отмена"}
                title={t("common.cancel") || "Отмена"}
              >
                <i className="fa-solid fa-xmark" aria-hidden="true" />
              </button>
            </div>
          </div>

          <div className="flex gap-3 flex-row items-center">
            <input
              id="barcode"
              type="search"
              inputMode="search"
              ref={barcodeInputRef}
              value={barcodeValue}
              placeholder={
                t("op.barcode.placeholder") ||
                "или введите штрих-код и нажмите Enter"
              }
              onChange={(event) => setBarcodeValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  runSearch(barcodeValue, searchMode);
                }
              }}
              className={inputClass("flex-1")}
            />
            <button
              id="btn-scan"
              type="button"
              className={iconButtonClass()}
              onClick={startScan}
              aria-label={t("op.scan") || "Скан штрих-кода"}
              title={t("op.scan") || "Скан штрих-кода"}
            >
              <i className="fa-solid fa-camera" aria-hidden="true" />
            </button>
          </div>
        </>
      )}

      {searchMode === SEARCH_MODES.NAME && (
        <>
          <div className="flex gap-3 flex-row items-center">
            <input
              id="product-query"
              type="search"
              value={queryValue}
              placeholder={
                t("op.search.placeholder") || "Наименование / артикул"
              }
              onChange={(event) => setQueryValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  runSearch(queryValue, SEARCH_MODES.NAME);
                }
              }}
              className={inputClass("flex-1")}
            />
            <button
              aria-label={t("common.search")}
              title={t("common.search")}
              type="button"
              className={iconButtonClass()}
              onClick={() => runSearch(queryValue, SEARCH_MODES.NAME)}
            >
              <i className="fa-solid fa-magnifying-glass" aria-hidden="true" />
            </button>
          </div>
          {!["idle", "done"].includes(searchStatus) && (
            <div
              id="product-results"
              className={mutedTextClass()}
              aria-live="polite"
            >
              {searchStatus === "loading" && (t("searching") || "Поиск...")}
              {searchStatus === "empty" &&
                (t("common.nothing") || "Ничего не найдено")}
              {searchStatus === "error" &&
                (t("search_error") || "Ошибка поиска")}
              {searchStatus === "multi" &&
                (t("op.search.choose_prompt") ||
                  "Найдено несколько результатов, выберите из списка")}
            </div>
          )}
        </>
      )}

      {picked && (
        <div id="product-picked" className={cardClass("space-y-2")}>
          <strong
            id="picked-name"
            className="text-lg font-semibold text-slate-900 dark:text-slate-50"
          >
            {picked.name}
          </strong>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span id="picked-code" className={mutedTextClass()}>
              {picked.barcode}
            </span>
            {picked.quantity_common != null && (
              <span className={mutedTextClass()}>
                {fmt.number(picked.quantity_common)} {picked.unit}
              </span>
            )}
          </div>
          {descriptionPreview && (
            <div id="picked-desc" className={mutedTextClass()}>
              {descriptionPreview}
            </div>
          )}
        </div>
      )}

      {searchMode !== SEARCH_MODES.INSANT && (
        <>
          <div className={cardClass("space-y-4")}>
            <div className="space-y-2">
              <label className={labelClass()} htmlFor="qty">
                {t("op.qty") || "Количество"}
                <span className={cn(mutedTextClass(), "ml-1")}>*</span>
              </label>
              <input
                id="qty"
                type="number"
                inputMode={picked?.unit_piece ? "numeric" : "decimal"}
                step={picked?.unit_piece ? 1 : "0.01"}
                value={quantity}
                onChange={(event) => {
                  const nextValue = event.target.value;
                  if (picked?.unit_piece) {
                    if (/^\d*$/.test(nextValue)) {
                      setQuantity(nextValue);
                    }
                    return;
                  }
                  setQuantity(nextValue);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    if (showCostField) {
                      document.getElementById("cost")?.focus();
                    } else if (showPriceField) {
                      document.getElementById("price")?.focus();
                    } else {
                      handleSubmit();
                    }
                  }
                }}
                className={inputClass()}
              />
              <div className="flex flex-wrap gap-2" id="qty-quick">
                {QUICK_QTY.map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={chipClass()}
                    data-inc={value}
                    onClick={() =>
                      setQuantity((prev) => {
                        const base = toNumber(prev);
                        if (picked?.unit_piece) {
                          const normalized = Number.isFinite(base)
                            ? Math.trunc(base)
                            : 0;
                          return String(normalized + value);
                        }
                        return String(base + value);
                      })
                    }
                  >
                    +{value}
                  </button>
                ))}
              </div>
            </div>

            {showCostField && (
              <div className="space-y-2">
                <label className={labelClass()} htmlFor="cost">
                  {t("op.cost") || "Стоимость"}
                </label>
                <input
                  id="cost"
                  type="number"
                  inputMode="decimal"
                  value={cost}
                  onChange={(event) => setCost(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      if (showPriceField) {
                        document.getElementById("price")?.focus();
                      } else {
                        handleSubmit();
                      }
                    }
                  }}
                  className={inputClass()}
                />
                {lpcLabel && (
                  <div className="flex flex-wrap gap-2" id="cost-hint-wrap">
                    <button
                      type="button"
                      id="cost-hint"
                      className={chipClass()}
                      onClick={() => setCost(String(picked.last_purchase_cost))}
                    >
                      {lpcLabel}
                    </button>
                  </div>
                )}
              </div>
            )}

            {showPriceField && (
              <div className="space-y-2">
                <label className={labelClass()} htmlFor="price">
                  {t("op.price") || "Цена"}
                </label>
                <input
                  id="price"
                  type="number"
                  inputMode="decimal"
                  value={price}
                  onChange={(event) => setPrice(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      handleSubmit();
                    }
                  }}
                  className={inputClass()}
                />
                {priceLabel && (
                  <div className="flex flex-wrap gap-2" id="price-hint-wrap">
                    <button
                      type="button"
                      id="price-hint"
                      className={chipClass()}
                      onClick={() => setPrice(String(picked.price))}
                    >
                      {priceLabel}
                    </button>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-2">
              <label className={labelClass()} htmlFor="description">
                {t("op.description") || "Описание"}
              </label>
              <input
                id="description"
                type="text"
                value={description}
                placeholder={
                  t("op.description.placeholder") ||
                  "Комментарий к операции (необяз.)"
                }
                onChange={(event) => setDescription(event.target.value)}
                className={inputClass()}
              />
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-3">
            <button
              id="btn-op-cancel"
              type="button"
              className={buttonClass({ variant: "ghost", size: "sm" })}
              onClick={() => navigate(buildDocPath({ id: docId }))}
              disabled={saving}
            >
              {t("common.cancel") || "Отмена"}
            </button>
            <button
              id="btn-op-save"
              type="button"
              className={buttonClass({ variant: "primary", size: "sm" })}
              onClick={handleSubmit}
              disabled={saving}
            >
              {saving
                ? t("op.saving") || "Сохранение..."
                : t("common.save") || "Сохранить"}
            </button>
          </div>
        </>
      )}

      {resultModalOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/70 px-4 py-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="search-results-title"
          onClick={handleModalDismiss}
        >
          <div
            className={cardClass(
              "relative mt-6 w-full max-w-lg space-y-4 shadow-xl"
            )}
            onClick={(event) => event.stopPropagation()}
          >
            <h2
              id="search-results-title"
              className="text-lg font-semibold text-slate-900 dark:text-slate-50"
            >
              {t("op.search.choose_prompt") || "Выберите товар"}
            </h2>
            <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
              {resultItems.map((item) => (
                <button
                  key={`${item.id}-${item.barcode}`}
                  type="button"
                  className={cardClass(
                    "w-full text-left transition hover:-translate-y-0.5 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2"
                  )}
                  onClick={() => handlePickItem(item)}
                >
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                      {item.name}
                    </span>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      {item.code ? (
                        <span>
                          {(t("item.code") === "item.code"
                            ? "Код"
                            : t("item.code")) + ": "}
                          <span className="font-medium text-slate-700 dark:text-slate-200">
                            {item.code}
                          </span>
                        </span>
                      ) : null}
                      {item.code && item.barcode ? <span>•</span> : null}
                      {item.barcode ? <span>{item.barcode}</span> : null}
                    </div>
                    {item.last_purchase_cost != null ? (
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {(t("op.last_purchase_cost") === "op.last_purchase_cost"
                          ? "Последняя закуп"
                          : t("op.last_purchase_cost")) + ": "}
                        <span className="font-medium text-slate-700 dark:text-slate-200">
                          {fmt.money(
                            item.last_purchase_cost,
                            docCurrency,
                            priceRoundTo
                          )}
                        </span>
                      </span>
                    ) : null}
                    {item.price != null ? (
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {(t("op.price") === "op.price"
                          ? "Цена"
                          : t("op.price")) + ": "}
                        <span className="font-medium text-slate-700 dark:text-slate-200">
                          {fmt.money(item.price, docCurrency, priceRoundTo)}
                        </span>
                      </span>
                    ) : null}
                  </div>
                </button>
              ))}
            </div>
            <div className="flex justify-end">
              <button
                type="button"
                className={buttonClass({ variant: "ghost", size: "sm" })}
                onClick={handleModalDismiss}
              >
                {t("common.cancel") || "Отмена"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
