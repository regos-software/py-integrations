import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  BrowserMultiFormatReader,
  BarcodeFormat,
  DecodeHintType,
} from "@zxing/library";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import { useToast } from "../context/ToastContext.jsx";
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

const QUICK_QTY = [1, 5, 10, 12];

const SEARCH_MODES = {
  SCAN: "scan",
  NAME: "name",
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

function firstBarcode(item) {
  return (
    item?.base_barcode ||
    (item?.barcode_list
      ? String(item.barcode_list).split(",")[0]?.trim()
      : "") ||
    item?.code ||
    ""
  );
}

export default function OpNewPage() {
  const { id } = useParams();
  const docId = Number(id);
  const navigate = useNavigate();
  const { api, toNumber, setAppTitle } = useApp();
  const { t, fmt, locale } = useI18n();
  const { showToast } = useToast();

  const [docCtx, setDocCtx] = useState({ price_type_id: null, stock_id: null });
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
  const videoRef = useRef(null);
  const readerRef = useRef(null);

  useEffect(() => {
    setAppTitle(t("op.title") || "Новая операция");
  }, [locale, setAppTitle, t]);

  useEffect(() => {
    async function loadDocMeta() {
      try {
        const { data: docData } = await api("docs.purchase.get_by_id", id);
        setDocCtx({
          price_type_id: docData?.price_type?.id ?? null,
          stock_id: docData?.stock?.id ?? null,
        });
      } catch (err) {
        console.warn("[op_new] failed to fetch doc context", err);
      }
    }
    loadDocMeta();
  }, [api, docId]);

  const closeResultModal = useCallback(() => {
    setResultModalOpen(false);
    setResultItems([]);
  }, []);

  const handlePickItem = useCallback(
    (item) => {
      setPicked(item);
      closeResultModal();
      setSearchStatus("done");
      window.setTimeout(() => {
        document.getElementById("qty")?.focus();
      }, 0);
    },
    [closeResultModal]
  );

  const runSearch = useCallback(
    async (value, mode = searchMode) => {
      const queryText = value?.trim();
      if (!queryText) return;
      setSearchStatus("loading");
      try {
        const payload = {
          search: queryText,
          price_type_id: docCtx?.price_type_id,
          stock_id: docCtx?.stock_id,
        };

        const { data } = await api("refrences.item.get_ext", payload);
        const rawItems = data?.result || [];
        if (!rawItems.length) {
          setPicked(null);
          closeResultModal();
          setSearchStatus("empty");
          return;
        }

        const normalizedItems = rawItems.map((ext) => {
          const core = ext?.item || {};
          return {
            id: Number(core.id ?? core.code),
            name: core.name || "—",
            barcode: firstBarcode(core),
            vat_value: Number(core?.vat?.value ?? 0),
            last_purchase_cost: ext?.last_purchase_cost ?? null,
            price: ext?.price != null ? Number(ext.price) : null,
            quantity_common: ext?.quantity?.common ?? null,
            unit: core?.unit?.name || "шт",
            unit_piece: core?.unit?.type === "pcs",
          };
        });

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
      }
    },
    [
      api,
      closeResultModal,
      docCtx.price_type_id,
      docCtx.stock_id,
      docId,
      handlePickItem,
      searchMode,
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
    if (searchMode === SEARCH_MODES.SCAN) {
      window.setTimeout(() => document.getElementById("barcode")?.focus(), 0);
    } else {
      stopScan();
      window.setTimeout(
        () => document.getElementById("product-query")?.focus(),
        0
      );
    }
  }, [searchMode, closeResultModal, stopScan]);

  const startScan = async () => {
    if (scanning) return;
    if (searchMode !== SEARCH_MODES.SCAN) return;

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
          runSearch(text, SEARCH_MODES.SCAN);
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
    if (!picked?.id) {
      showToast(t("select_product_first") || "Сначала выберите товар", {
        type: "error",
      });
      return;
    }
    const qtyNumber = toNumber(quantity);
    const costNumber = toNumber(cost);
    if (!qtyNumber || qtyNumber <= 0) {
      showToast(t("fill_required_fields") || "Заполните обязательные поля", {
        type: "error",
      });
      return;
    }

    if (picked?.unit_piece && !Number.isInteger(qtyNumber)) {
      showToast(t("qty.integer_only") || "Количество должно быть целым", {
        type: "error",
      });
      return;
    }

    const payload = {
      items: [
        {
          document_id: docId,
          item_id: Number(picked.id),
          quantity: qtyNumber,
          cost: costNumber,
          vat_value: Number(picked.vat_value ?? 0),
        },
      ],
    };
    const priceNumber = toNumber(price);
    if (priceNumber > 0) payload.items[0].price = priceNumber;
    if (description.trim()) payload.items[0].description = description.trim();

    setSaving(true);
    try {
      const { ok, data } = await api("purchase_ops_add", payload);
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        showToast(t("toast.op_added") || "Операция добавлена", {
          type: "success",
        });
        setQuantity("");
        setCost("");
        setPrice("");
        setBarcodeValue("");
        setQueryValue("");
        setPicked(null);
        setSearchStatus("idle");
        window.setTimeout(() => document.getElementById("barcode")?.focus(), 0);
      } else {
        throw new Error(data?.description || "Save failed");
      }
    } catch (err) {
      showToast(
        err.message || t("save_failed") || "Не удалось сохранить операцию",
        { type: "error", duration: 2400 }
      );
    } finally {
      setSaving(false);
    }
  };

  const descriptionPreview = useMemo(() => {
    if (!description.trim() || !picked) return "";
    return `${t("op.description") || "Описание"}: ${description.trim()}`;
  }, [description, picked, t]);

  const lpcLabel = useMemo(() => {
    if (picked?.last_purchase_cost == null) return null;
    return fmt.money(picked.last_purchase_cost);
  }, [fmt, picked]);

  const priceLabel = useMemo(() => {
    if (picked?.price == null) return null;
    return fmt.money(picked.price);
  }, [fmt, picked]);

  return (
    <section className={sectionClass()} id="op-new">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
        {t("op.title") || "Новая операция"}
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
      </div>

      {searchMode === SEARCH_MODES.SCAN && (
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
              value={barcodeValue}
              placeholder={
                t("op.barcode.placeholder") ||
                "или введите штрих-код и нажмите Enter"
              }
              onChange={(event) => setBarcodeValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  runSearch(barcodeValue, SEARCH_MODES.SCAN);
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
          {searchStatus != "idle" && (
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
                document.getElementById("cost")?.focus();
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
                document.getElementById("price")?.focus();
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
          onClick={() => navigate(`/doc/${docId}`)}
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

      {resultModalOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="search-results-title"
          onClick={handleModalDismiss}
        >
          <div
            className={cardClass(
              "relative w-full max-w-lg space-y-4 shadow-xl"
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
                    <span className={mutedTextClass()}>{item.barcode}</span>
                    {item.price != null ? (
                      <span className={mutedTextClass()}>
                        {fmt.money(item.price)}
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
