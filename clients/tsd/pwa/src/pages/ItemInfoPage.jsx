import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";
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
  iconButtonClass,
  inputClass,
  labelClass,
  mutedTextClass,
  sectionClass,
} from "../lib/ui";
import { cn } from "../lib/utils";

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

const DEFAULT_LIMIT = 20;
const OPERATION_LIMIT_MIN = 1;
const OPERATION_LIMIT_MAX = 1000;
const SIMILAR_SEARCH_STEP_KEY = "similar_search";
const SIMILAR_EXT_STEP_KEY = "similar_ext";
const DEFAULT_OPERATION_FILTERS = Object.freeze({
  stockId: "all",
  positive: "all",
  docType: "all",
});
const FILTER_POPOVER_WIDTH = 360;
const FILTER_POPOVER_HEIGHT = 320;
const FILTER_POPOVER_MARGIN = 16;
const FILTER_POPOVER_OFFSET = 8;

function normalizeOperationLimit(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return DEFAULT_LIMIT;
  const floored = Math.floor(parsed);
  if (floored < OPERATION_LIMIT_MIN) return OPERATION_LIMIT_MIN;
  if (floored > OPERATION_LIMIT_MAX) return OPERATION_LIMIT_MAX;
  return floored;
}

function normalizeItemExt(ext) {
  if (!ext) return null;
  const core = ext.item || {};
  const unit = core.unit || {};
  const firstBarcode =
    core.base_barcode ||
    (core.barcode_list
      ? String(core.barcode_list)
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean)[0]
      : "") ||
    core.code ||
    "";

  return {
    id: Number(core.id ?? core.code ?? 0) || 0,
    name: core.name || "—",
    barcode: firstBarcode,
    icps: core.icps || null,
    code: core.code != null ? String(core.code) : null,
    articul: core.articul || null,
    color: core.color?.name || null,
    size: core.size?.name || null,
    sizeChart:
      core.sizechart?.name ||
      core.size_chart?.name ||
      core.size_chart_name ||
      core.size?.sizechart?.name ||
      core.size?.size_chart?.name ||
      null,
    unit: unit.name || "шт",
    raw: ext,
  };
}

function normalizeArticulValue(value) {
  if (value == null) return null;
  const stringValue = String(value).trim();
  return stringValue.length > 0 ? stringValue : null;
}

function normalizeNameValue(value) {
  if (value == null) return null;
  const trimmed = String(value).trim();
  if (!trimmed) return null;
  return trimmed.toLocaleLowerCase();
}

function formatFallback(t, key, fallback) {
  const translated = t(key);
  return translated === key ? fallback : translated;
}

export default function ItemInfoPage() {
  const navigate = useNavigate();
  const { api, setAppTitle } = useApp();
  const { t, fmt, locale } = useI18n();
  const { showToast } = useToast();

  const [searchMode, setSearchMode] = useState(SEARCH_MODES.SCAN);
  const [barcodeValue, setBarcodeValue] = useState("");
  const [queryValue, setQueryValue] = useState("");
  const [searchStatus, setSearchStatus] = useState("idle");
  const [scanning, setScanning] = useState(false);

  const [resultItems, setResultItems] = useState([]);
  const [resultModalOpen, setResultModalOpen] = useState(false);

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({
    stockId: null,
    priceTypeId: null,
    limit: DEFAULT_LIMIT,
  });
  const [settingsDraft, setSettingsDraft] = useState(settings);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [stocks, setStocks] = useState([]);
  const [priceTypes, setPriceTypes] = useState([]);

  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedExt, setSelectedExt] = useState(null);
  const [quantityInfo, setQuantityInfo] = useState([]);
  const [pricesInfo, setPricesInfo] = useState([]);
  const [operations, setOperations] = useState([]);
  const [similarItems, setSimilarItems] = useState([]);
  const [operationFiltersOpen, setOperationFiltersOpen] = useState(false);
  const [operationFiltersAnchor, setOperationFiltersAnchor] = useState(null);
  const [operationFilters, setOperationFilters] = useState(() => ({
    ...DEFAULT_OPERATION_FILTERS,
  }));
  const [operationFiltersDraft, setOperationFiltersDraft] = useState(() => ({
    ...DEFAULT_OPERATION_FILTERS,
  }));
  const [detailsLoading, setDetailsLoading] = useState(false);

  const barcodeInputRef = useRef(null);
  const videoRef = useRef(null);
  const readerRef = useRef(null);
  const filterButtonRef = useRef(null);

  const title = useMemo(() => {
    const translated = t("item_info.title");
    return translated === "item_info.title"
      ? "Информация по номенклатуре"
      : translated;
  }, [t]);

  useEffect(() => {
    setAppTitle(title);
  }, [locale, setAppTitle, title]);

  const focusBarcodeInput = useCallback(() => {
    window.setTimeout(() => {
      barcodeInputRef.current?.focus();
    }, 0);
  }, []);

  useEffect(() => {
    console.log("stocks", stocks, settingsDraft);

    if (stocks.length > 0) {
      setSettingsDraft((prev) => ({
        ...prev,
        stockId: prev.stockId ?? stocks?.[0]?.value,
      }));
      setSettings((prev) => ({
        ...prev,
        stockId: prev.stockId ?? stocks?.[0]?.value,
        limit: normalizeOperationLimit(prev.limit ?? DEFAULT_LIMIT),
      }));
    }
  }, [stocks]);

  useEffect(() => {
    console.log("priceTypes", priceTypes, settingsDraft);
    if (priceTypes.length > 0) {
      setSettingsDraft((prev) => ({
        ...prev,
        priceTypeId: prev.priceTypeId ?? priceTypes?.[0]?.value,
      }));
      setSettings((prev) => ({
        ...prev,
        priceTypeId: prev.priceTypeId ?? priceTypes?.[0]?.value,
        limit: normalizeOperationLimit(prev.limit ?? DEFAULT_LIMIT),
      }));
    }
  }, [priceTypes]);

  useEffect(() => {
    focusBarcodeInput();
  }, [focusBarcodeInput, searchMode]);

  const callApi = useCallback(
    async (action, params, fallbackMessage) => {
      const response = await api(action, params);
      const defaultMessage = formatFallback(
        t,
        "common.error",
        "Ошибка выполнения запроса"
      );

      if (!response.ok) {
        const errMsg =
          response.data?.description ||
          response.data?.detail ||
          fallbackMessage;
        throw new Error(errMsg || defaultMessage);
      }

      const body = response.data;
      if (body && Object.prototype.hasOwnProperty.call(body, "ok")) {
        if (!body.ok) {
          const errMsg = body.description || fallbackMessage;
          throw new Error(errMsg || defaultMessage);
        }
      }
      return body;
    },
    [api, t]
  );

  const loadOptions = useCallback(async () => {
    setOptionsLoading(true);
    try {
      const [stockData, priceTypeData] = await Promise.all([
        callApi(
          "references.stock.get",
          {
            limit: 200,
            deleted_mark: false,
            sort_orders: [{ column: "Name", direction: "asc" }],
          },
          formatFallback(
            t,
            "item_info.stocks_error",
            "Не удалось загрузить склады"
          )
        ),
        callApi(
          "references.price_type.get",
          {},
          formatFallback(
            t,
            "item_info.price_type_error",
            "Не удалось загрузить виды цен"
          )
        ),
      ]);

      const stockOptions = Array.isArray(stockData?.result)
        ? stockData.result.map((stock) => ({
            value: stock.id,
            label: stock.name || `ID ${stock.id}`,
          }))
        : [];
      const priceTypeOptions = Array.isArray(priceTypeData?.result)
        ? priceTypeData.result.map((pt) => ({
            value: pt.id,
            label: pt.name || `ID ${pt.id}`,
          }))
        : [];

      const defaultStockId = stockOptions[0]?.value ?? null;
      const defaultPriceTypeId = priceTypeOptions[0]?.value ?? null;

      setStocks(stockOptions);
      setPriceTypes(priceTypeOptions);

      setSettings((prev) => ({
        stockId: prev.stockId ?? defaultStockId,
        priceTypeId: prev.priceTypeId ?? defaultPriceTypeId,
        limit: normalizeOperationLimit(prev.limit ?? DEFAULT_LIMIT),
      }));
      setSettingsDraft((prev) => ({
        stockId: prev.stockId ?? defaultStockId,
        priceTypeId: prev.priceTypeId ?? defaultPriceTypeId,
        limit: prev.limit ?? DEFAULT_LIMIT,
      }));
    } catch (err) {
      console.warn("[item-info] load options", err);
      showToast(err.message, { type: "error" });
    } finally {
      setOptionsLoading(false);
    }
  }, [callApi, showToast, t]);

  useEffect(() => {
    loadOptions();
  }, [loadOptions]);

  useEffect(() => {
    if (settingsOpen) {
      setSettingsDraft(settings);
    }
  }, [settings, settingsOpen]);

  const getStockFilterValue = useCallback((stock) => {
    if (!stock) return "__none__";
    if (stock.id != null) {
      return `id:${stock.id}`;
    }
    if (stock.name) {
      return `name:${stock.name}`;
    }
    return "__none__";
  }, []);

  const getStockLabel = useCallback(
    (stock) => {
      if (stock?.name) return stock.name;
      if (stock?.id != null) return `ID ${stock.id}`;
      return formatFallback(t, "item_info.stock_unknown", "Склад не указан");
    },
    [t]
  );

  const getDocTypeFilterValue = useCallback((operation) => {
    const object = operation?.document_type;
    if (object?.id != null) {
      return `id:${object.id}`;
    }
    const name = operation?.doc_type_name || object?.name;
    if (name) {
      return `name:${name}`;
    }
    return "__none__";
  }, []);

  const getDocTypeLabel = useCallback(
    (operation) => {
      const object = operation?.document_type;
      const name = operation?.doc_type_name || object?.name;
      if (name) return name;
      if (object?.id != null) return `ID ${object.id}`;
      return formatFallback(
        t,
        "item_info.doc_type_unknown",
        "Тип документа не указан"
      );
    },
    [t]
  );

  const operationStockOptions = useMemo(() => {
    const map = new Map();
    operations.forEach((operation) => {
      const value = getStockFilterValue(operation?.stock);
      const label = getStockLabel(operation?.stock);
      if (!map.has(value)) {
        map.set(value, label);
      }
    });

    return Array.from(map.entries()).map(([value, label]) => ({
      value,
      label,
    }));
  }, [getStockFilterValue, getStockLabel, operations]);

  const operationDocTypeOptions = useMemo(() => {
    const map = new Map();
    operations.forEach((operation) => {
      const value = getDocTypeFilterValue(operation);
      const label = getDocTypeLabel(operation);
      if (!map.has(value)) {
        map.set(value, label);
      }
    });

    return Array.from(map.entries()).map(([value, label]) => ({
      value,
      label,
    }));
  }, [getDocTypeFilterValue, getDocTypeLabel, operations]);

  const filteredOperations = useMemo(() => {
    const { stockId, positive, docType } = operationFilters;

    return operations.filter((operation) => {
      if (stockId !== "all") {
        if (getStockFilterValue(operation?.stock) !== stockId) {
          return false;
        }
      }

      if (positive !== "all") {
        const positiveValue = positive === "true";
        if ((operation?.positive ?? null) !== positiveValue) {
          return false;
        }
      }

      if (docType !== "all") {
        if (getDocTypeFilterValue(operation) !== docType) {
          return false;
        }
      }

      return true;
    });
  }, [
    getDocTypeFilterValue,
    getStockFilterValue,
    operationFilters,
    operations,
  ]);

  const operationFiltersActive =
    operationFilters.stockId !== "all" ||
    operationFilters.positive !== "all" ||
    operationFilters.docType !== "all";

  useEffect(() => {
    setOperationFilters((prev) => {
      let next = prev;
      let modified = false;

      if (
        prev.stockId !== "all" &&
        !operationStockOptions.some((option) => option.value === prev.stockId)
      ) {
        next = { ...next, stockId: "all" };
        modified = true;
      }

      if (
        prev.docType !== "all" &&
        !operationDocTypeOptions.some((option) => option.value === prev.docType)
      ) {
        next = next === prev ? { ...next } : next;
        next.docType = "all";
        modified = true;
      }

      return modified ? next : prev;
    });
  }, [operationDocTypeOptions, operationStockOptions]);

  useEffect(() => {
    if (operationFiltersOpen) {
      setOperationFiltersDraft({ ...operationFilters });
    }
  }, [operationFilters, operationFiltersOpen]);

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
    reader.timeBetweenDecodingAttempts = 75;
    readerRef.current = reader;
    return readerRef.current;
  }, []);

  const stopScan = useCallback(() => {
    setScanning(false);
    if (readerRef.current) {
      readerRef.current.reset();
    }
    if (videoRef.current?.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
  }, []);

  useEffect(() => stopScan, [stopScan]);

  const loadItemDetails = useCallback(
    async (itemInput, overrideSettings) => {
      const itemInfo =
        itemInput && typeof itemInput === "object" ? itemInput : null;
      const itemIdCandidate = itemInfo?.id != null ? itemInfo.id : itemInput;
      const itemIdNumber = Number(itemIdCandidate);

      if (!itemIdNumber || !Number.isFinite(itemIdNumber)) {
        setSelectedExt(null);
        setQuantityInfo([]);
        setPricesInfo([]);
        setOperations([]);
        setSimilarItems([]);
        return;
      }

      const itemName =
        typeof itemInfo?.name === "string" ? itemInfo.name.trim() : "";
      const itemArticulRaw = itemInfo?.articul ?? null;

      const activeSettings = overrideSettings ?? settings;
      const fallbackStockId = stocks[0]?.value ?? null;
      const fallbackPriceTypeId = priceTypes[0]?.value ?? null;

      const stockId =
        activeSettings.stockId != null
          ? Number(activeSettings.stockId)
          : fallbackStockId != null
          ? Number(fallbackStockId)
          : null;
      const priceTypeId =
        activeSettings.priceTypeId != null
          ? Number(activeSettings.priceTypeId)
          : fallbackPriceTypeId != null
          ? Number(fallbackPriceTypeId)
          : null;
      const operationLimit = normalizeOperationLimit(
        activeSettings.limit ?? DEFAULT_LIMIT
      );

      const loadErrorMessage = formatFallback(
        t,
        "item_info.load_error",
        "Не удалось загрузить номенклатуру"
      );
      const quantityErrorMessage = formatFallback(
        t,
        "item_info.quantity_error",
        "Не удалось получить остатки"
      );
      const priceErrorMessage = formatFallback(
        t,
        "item_info.price_error",
        "Не удалось получить цены"
      );
      const operationsErrorMessage = formatFallback(
        t,
        "item_info.operations_error",
        "Не удалось получить операции"
      );
      const similarErrorMessage = formatFallback(
        t,
        "item_info.similar_error",
        "Не удалось получить похожие позиции"
      );

      const similarSearchName =
        itemName || itemInfo?.raw?.item?.name || "${item.result.0.item.name}";

      const requests = [
        {
          key: "item",
          path: "Item/GetExt",
          payload: {
            ids: [itemIdNumber],
            limit: 1,
            ...(stockId ? { stock_id: stockId } : {}),
            ...(priceTypeId ? { price_type_id: priceTypeId } : {}),
          },
        },
        {
          key: SIMILAR_SEARCH_STEP_KEY,
          path: "Item/Search",
          payload: {
            name: similarSearchName,
          },
        },
        {
          key: SIMILAR_EXT_STEP_KEY,
          path: "Item/GetExt",
          payload: {
            ids: `\${${SIMILAR_SEARCH_STEP_KEY}.result}`,
            limit: 100,
            ...(stockId ? { stock_id: stockId } : {}),
            ...(priceTypeId ? { price_type_id: priceTypeId } : {}),
          },
        },
        {
          key: "quantity",
          path: "Item/GetQuantity",
          payload: {
            item_id: itemIdNumber,
          },
        },
        {
          key: "prices",
          path: "ItemPrice/Get",
          payload: {
            item_ids: [itemIdNumber],
          },
        },
        {
          key: "operations",
          path: "ItemOperation/Get",
          payload: {
            item_id: itemIdNumber,
            limit: operationLimit,
          },
        },
      ];

      const batchPayload = {
        stop_on_error: false,
        requests,
      };

      setDetailsLoading(true);
      setSimilarItems([]);
      try {
        const {
          ok: batchOk,
          status,
          data: batchData,
        } = await api("batch.run", batchPayload);

        if (!batchOk) {
          const description =
            batchData?.description || `${loadErrorMessage} (${status})`;
          throw new Error(description || loadErrorMessage);
        }

        if (!batchData?.ok) {
          const description = batchData?.description || loadErrorMessage;
          throw new Error(description || loadErrorMessage);
        }

        const steps = Array.isArray(batchData.result) ? batchData.result : [];
        const findStep = (key) => steps.find((step) => step?.key === key);
        const ensureStep = (key, fallback) => {
          const step = findStep(key);
          if (!step) {
            throw new Error(fallback);
          }
          const response = step.response;
          if (!response || response.ok === false) {
            const description =
              response?.result?.description ||
              response?.description ||
              fallback;
            throw new Error(description || fallback);
          }
          return response;
        };

        const extResponse = ensureStep("item", loadErrorMessage);
        ensureStep(SIMILAR_SEARCH_STEP_KEY, similarErrorMessage);
        const similarExtResponse = ensureStep(
          SIMILAR_EXT_STEP_KEY,
          similarErrorMessage
        );
        const quantityResponse = ensureStep("quantity", quantityErrorMessage);
        const priceResponse = ensureStep("prices", priceErrorMessage);
        const operationsResponse = ensureStep(
          "operations",
          operationsErrorMessage
        );

        const ext = Array.isArray(extResponse?.result)
          ? extResponse.result[0]
          : null;
        setSelectedExt(ext ?? null);
        setQuantityInfo(
          Array.isArray(quantityResponse?.result) ? quantityResponse.result : []
        );
        setPricesInfo(
          Array.isArray(priceResponse?.result) ? priceResponse.result : []
        );
        setOperations(
          Array.isArray(operationsResponse?.result)
            ? operationsResponse.result
            : []
        );

        const targetArticul =
          normalizeArticulValue(itemArticulRaw) ??
          normalizeArticulValue(ext?.item?.articul);
        const targetName =
          normalizeNameValue(itemInfo?.name) ??
          normalizeNameValue(ext?.item?.name);

        let similarList = [];
        if (similarExtResponse && Array.isArray(similarExtResponse.result)) {
          const seenIds = new Set();
          similarList = similarExtResponse.result
            .map((itemExt) => normalizeItemExt(itemExt))
            .filter((similar) => {
              if (!similar || !similar.id) return false;
              if (similar.id === itemIdNumber) return false;

              const articulValue = normalizeArticulValue(similar.articul);
              const similarNameValue = normalizeNameValue(similar.name);

              const matchesArticul =
                targetArticul != null &&
                articulValue != null &&
                articulValue === targetArticul;

              const matchesName =
                targetArticul == null &&
                targetName != null &&
                similarNameValue != null &&
                similarNameValue === targetName;

              if (!matchesArticul && !matchesName) return false;
              if (seenIds.has(similar.id)) return false;
              seenIds.add(similar.id);
              return true;
            });
        }
        setSimilarItems(similarList);
      } catch (err) {
        console.warn("[item-info] load details", err);
        setSimilarItems([]);
        showToast(err.message, { type: "error" });
      } finally {
        setDetailsLoading(false);
      }
    },
    [api, priceTypes, settings, showToast, stocks, t]
  );

  const handlePickItem = useCallback(
    async (item) => {
      if (!item) return;
      setSelectedItem(item);
      setResultModalOpen(false);
      setSearchStatus("done");
      setBarcodeValue("");
      setQueryValue("");
      await loadItemDetails(item, settings);
    },
    [loadItemDetails, settings]
  );

  const resetUI = useCallback(() => {
    setSelectedItem(null);
    setSelectedExt(null);
    setQuantityInfo([]);
    setPricesInfo([]);
    setOperations([]);
    setSimilarItems([]);
  }, []);

  const handlePickSimilarItem = useCallback(
    async (item) => {
      if (typeof window !== "undefined") {
        window.requestAnimationFrame(() => {
          window.scrollTo({ top: 0, behavior: "smooth" });
        });
      }
      resetUI();
      await handlePickItem(item);
    },
    [handlePickItem, resetUI]
  );

  const handleOperationFiltersOpen = useCallback(() => {
    let anchor = null;

    if (typeof window !== "undefined") {
      const button = filterButtonRef.current;
      if (button) {
        const rect = button.getBoundingClientRect();
        const scrollX = window.scrollX ?? window.pageXOffset ?? 0;
        const scrollY = window.scrollY ?? window.pageYOffset ?? 0;
        const viewportWidth =
          window.innerWidth ??
          document.documentElement?.clientWidth ??
          FILTER_POPOVER_WIDTH + FILTER_POPOVER_MARGIN * 2;
        const viewportHeight =
          window.innerHeight ??
          document.documentElement?.clientHeight ??
          FILTER_POPOVER_HEIGHT + FILTER_POPOVER_MARGIN * 2;

        const availableWidth = Math.max(
          240,
          viewportWidth - FILTER_POPOVER_MARGIN * 2
        );
        const popoverWidth = Math.min(FILTER_POPOVER_WIDTH, availableWidth);

        const minLeft = scrollX + FILTER_POPOVER_MARGIN;
        const maxLeft =
          scrollX + viewportWidth - FILTER_POPOVER_MARGIN - popoverWidth;
        let left = scrollX + rect.left;
        left = Math.max(minLeft, Math.min(left, maxLeft));

        const preferredTop = scrollY + rect.bottom + FILTER_POPOVER_OFFSET;
        const maxTop =
          scrollY +
          viewportHeight -
          FILTER_POPOVER_MARGIN -
          FILTER_POPOVER_HEIGHT;

        if (preferredTop <= maxTop) {
          anchor = { top: preferredTop, left, width: popoverWidth };
        } else {
          const topAbove =
            scrollY + rect.top - FILTER_POPOVER_OFFSET - FILTER_POPOVER_HEIGHT;
          const clampedTop = Math.max(
            scrollY + FILTER_POPOVER_MARGIN,
            Math.min(topAbove, maxTop)
          );
          anchor = { top: clampedTop, left, width: popoverWidth };
        }
      }
    }

    setOperationFiltersAnchor(anchor);
    setOperationFiltersOpen(true);
  }, []);

  const handleOperationFiltersChange = useCallback(
    (field) => (event) => {
      const value = event?.target?.value ?? "all";
      setOperationFiltersDraft((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const handleOperationFiltersApply = useCallback(() => {
    setOperationFilters({ ...operationFiltersDraft });
    setOperationFiltersOpen(false);
    setOperationFiltersAnchor(null);
  }, [operationFiltersDraft]);

  const handleOperationFiltersCancel = useCallback(() => {
    setOperationFiltersDraft({ ...operationFilters });
    setOperationFiltersOpen(false);
    setOperationFiltersAnchor(null);
  }, [operationFilters]);

  const handleOperationFiltersReset = useCallback(() => {
    setOperationFiltersDraft({ ...DEFAULT_OPERATION_FILTERS });
  }, []);

  const handleSearch = useCallback(
    async (queryText, mode = SEARCH_MODES.NAME) => {
      const normalized = queryText.trim();
      if (!normalized) {
        setSimilarItems([]);
        if (mode === SEARCH_MODES.SCAN) {
          setBarcodeValue("");
          focusBarcodeInput();
        }
        return;
      }

      setSimilarItems([]);
      setSearchStatus("loading");
      try {
        const fallbackStockId = stocks[0]?.value ?? null;
        const fallbackPriceTypeId = priceTypes[0]?.value ?? null;

        const payload = {
          search: normalized,
          limit: 100,
        };
        const stockId =
          settings.stockId ??
          (fallbackStockId != null ? fallbackStockId : null);
        const priceTypeId =
          settings.priceTypeId ??
          (fallbackPriceTypeId != null ? fallbackPriceTypeId : null);

        if (stockId != null) payload.stock_id = Number(stockId);
        if (priceTypeId != null) payload.price_type_id = Number(priceTypeId);

        console.log("search payload", payload);

        const data = await callApi(
          "references.item.get_ext",
          payload,
          formatFallback(
            t,
            "item_info.search_error",
            "Не удалось выполнить поиск"
          )
        );

        const items = Array.isArray(data?.result) ? data.result : [];
        const normalizedItems = items
          .map((ext) => normalizeItemExt(ext))
          .filter((ext) => ext && ext.id);

        if (normalizedItems.length === 0) {
          setSelectedItem(null);
          setSelectedExt(null);
          setQuantityInfo([]);
          setPricesInfo([]);
          setOperations([]);
          setSimilarItems([]);
          setSearchStatus("empty");
          showToast(formatFallback(t, "common.nothing", "Ничего не найдено"), {
            type: "error",
          });
          return;
        }

        if (normalizedItems.length === 1) {
          await handlePickItem(normalizedItems[0]);
          return;
        }

        setResultItems(normalizedItems);
        setResultModalOpen(true);
        setSearchStatus("multi");
      } catch (err) {
        console.warn("[item-info] search error", err);
        setSearchStatus("error");
        setSimilarItems([]);
        showToast(err.message, { type: "error" });
      } finally {
        if (mode === SEARCH_MODES.SCAN) {
          setBarcodeValue("");
          focusBarcodeInput();
        }
      }
    },
    [
      callApi,
      focusBarcodeInput,
      handlePickItem,
      priceTypes,
      settings.priceTypeId,
      settings.stockId,
      showToast,
      stocks,
      t,
    ]
  );

  const runSearch = useCallback(
    async (value, mode = searchMode) => {
      if (mode === SEARCH_MODES.SCAN) {
        await handleSearch(value, SEARCH_MODES.SCAN);
        return;
      }
      await handleSearch(value, SEARCH_MODES.NAME);
    },
    [handleSearch, searchMode]
  );

  const startScan = useCallback(async () => {
    if (scanning) return;
    if (searchMode !== SEARCH_MODES.SCAN) return;

    try {
      const reader = await ensureReader();
      const constraints = {
        video: { facingMode: { ideal: "environment" } },
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute("playsinline", "true");
        await videoRef.current.play();
      }

      setScanning(true);
      reader.decodeFromVideoDevice(null, videoRef.current, (result, err) => {
        if (result) {
          const text = result.getText();
          stopScan();
          runSearch(text, SEARCH_MODES.SCAN);
        }
        if (
          err &&
          !(err.name === "NotFoundException" || err.name === "NotFoundError")
        ) {
          // swallow non-critical errors
        }
      });
    } catch (err) {
      console.warn("[item-info] start scan", err);
      const messageKey =
        err?.name === "NotAllowedError"
          ? "camera_permission_denied"
          : err?.name === "NotFoundError" ||
            err?.name === "OverconstrainedError"
          ? "camera_not_found"
          : "camera_open_failed";
      showToast(formatFallback(t, messageKey, "Не удалось открыть камеру"), {
        type: "error",
      });
    }
  }, [ensureReader, runSearch, scanning, searchMode, showToast, stopScan, t]);

  const closeResultModal = useCallback(() => {
    setResultModalOpen(false);
    setResultItems([]);
  }, []);

  const handleSettingsApply = useCallback(() => {
    const normalized = {
      stockId:
        settingsDraft.stockId === "" || settingsDraft.stockId == null
          ? null
          : Number(settingsDraft.stockId),
      priceTypeId:
        settingsDraft.priceTypeId === "" || settingsDraft.priceTypeId == null
          ? null
          : Number(settingsDraft.priceTypeId),
      limit: normalizeOperationLimit(settingsDraft.limit ?? DEFAULT_LIMIT),
    };
    setSettings(normalized);
    setSettingsOpen(false);
    if (selectedItem) {
      loadItemDetails(selectedItem, normalized);
    }
  }, [loadItemDetails, selectedItem, settingsDraft]);

  const handleSettingsCancel = useCallback(() => {
    setSettingsDraft(settings);
    setSettingsOpen(false);
  }, [settings]);

  const selectedCore = selectedExt?.item || {};
  const selectedQuantity = selectedExt?.quantity || null;
  const selectedPriceType = selectedExt?.pricetype || null;
  const selectedPrice = selectedExt?.price ?? null;
  const lastPurchaseCost = selectedExt?.last_purchase_cost ?? null;
  const docCurrency =
    selectedPriceType?.currency?.code_chr ||
    selectedPriceType?.currency?.code ||
    "UZS";
  const colorName = selectedCore.color?.name || "—";
  const sizeName = selectedCore.size?.name || "—";
  const producerName = selectedCore.producer?.name || "—";
  const countryName = selectedCore.country?.name || "—";
  const partnerName =
    selectedCore.partner?.name ||
    (selectedCore.partner_id != null ? String(selectedCore.partner_id) : "—");

  return (
    <section className={sectionClass()} id="item-info">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
            {title}
          </h1>
          {selectedItem ? (
            <p className={mutedTextClass()}>
              {formatFallback(
                t,
                "item_info.selected_hint",
                "Выбрана позиция, данные обновлены"
              )}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          className={buttonClass({ variant: "ghost", size: "sm" })}
          onClick={() => navigate(-1)}
        >
          <i className="fa-solid fa-arrow-left" aria-hidden="true" />
          <span className="ml-2">
            {formatFallback(t, "common.back", "Назад")}
          </span>
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className={iconButtonClass({
            variant: searchMode === SEARCH_MODES.SCAN ? "primary" : "ghost",
          })}
          aria-label={formatFallback(t, "op.mode.scan", "Режим сканирования")}
          title={formatFallback(t, "op.mode.scan", "Режим сканирования")}
          onClick={() => {
            setSearchMode(SEARCH_MODES.SCAN);
            stopScan();
            setBarcodeValue("");
            focusBarcodeInput();
          }}
        >
          <i className="fa-solid fa-barcode" aria-hidden="true" />
        </button>
        <button
          type="button"
          className={iconButtonClass({
            variant: searchMode === SEARCH_MODES.NAME ? "primary" : "ghost",
          })}
          aria-label={formatFallback(t, "op.mode.name", "Поиск по названию")}
          title={formatFallback(t, "op.mode.name", "Поиск по названию")}
          onClick={() => {
            setSearchMode(SEARCH_MODES.NAME);
            stopScan();
          }}
        >
          <i className="fa-solid fa-magnifying-glass" aria-hidden="true" />
        </button>
        <button
          type="button"
          className={iconButtonClass({ variant: "secondary" })}
          aria-label={formatFallback(t, "item_info.settings", "Настройки")}
          title={formatFallback(t, "item_info.settings", "Настройки")}
          onClick={() => setSettingsOpen(true)}
        >
          <i className="fa-solid fa-gear" aria-hidden="true" />
        </button>
      </div>

      {[SEARCH_MODES.SCAN].includes(searchMode) ? (
        <>
          <div
            id="scanner"
            className={cn(
              scanning ? "space-y-4" : "hidden",
              cardClass("space-y-4")
            )}
          >
            <video
              id="item-info-preview"
              ref={videoRef}
              playsInline
              className="w-full rounded-xl"
            />
            <div className="flex items-center justify-between gap-3">
              <span className={mutedTextClass()}>
                {formatFallback(
                  t,
                  "scanner.hint",
                  "Наведи камеру на штрих-код"
                )}
              </span>
              <button
                type="button"
                className={iconButtonClass()}
                onClick={stopScan}
                aria-label={formatFallback(t, "common.cancel", "Отмена")}
                title={formatFallback(t, "common.cancel", "Отмена")}
              >
                <i className="fa-solid fa-xmark" aria-hidden="true" />
              </button>
            </div>
          </div>

          <div className="flex flex-row items-center gap-3">
            <input
              id="item-info-barcode"
              ref={barcodeInputRef}
              type="search"
              inputMode="search"
              value={barcodeValue}
              placeholder={formatFallback(
                t,
                "item_info.barcode_placeholder",
                "Введите штрих-код и нажмите Enter"
              )}
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
              type="button"
              className={iconButtonClass()}
              onClick={startScan}
              aria-label={formatFallback(t, "op.scan", "Скан штрих-кода")}
              title={formatFallback(t, "op.scan", "Скан штрих-кода")}
            >
              <i className="fa-solid fa-camera" aria-hidden="true" />
            </button>
          </div>
        </>
      ) : null}

      {searchMode === SEARCH_MODES.NAME ? (
        <div className="space-y-2">
          <div className="flex flex-row items-center gap-3">
            <input
              id="item-info-query"
              type="search"
              value={queryValue}
              placeholder={formatFallback(
                t,
                "item_info.search_placeholder",
                "Наименование / артикул / код"
              )}
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
              type="button"
              className={iconButtonClass()}
              aria-label={formatFallback(t, "common.search", "Поиск")}
              title={formatFallback(t, "common.search", "Поиск")}
              onClick={() => runSearch(queryValue, SEARCH_MODES.NAME)}
            >
              <i className="fa-solid fa-magnifying-glass" aria-hidden="true" />
            </button>
          </div>
          <div className={mutedTextClass()} aria-live="polite">
            {searchStatus === "loading"
              ? formatFallback(t, "searching", "Поиск...")
              : searchStatus === "empty"
              ? formatFallback(t, "common.nothing", "Ничего не найдено")
              : searchStatus === "error"
              ? formatFallback(t, "search_error", "Ошибка поиска")
              : null}
          </div>
        </div>
      ) : null}

      {selectedExt ? (
        <div className={cardClass("space-y-4")} id="item-info-summary">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-50">
              {selectedCore.name || "—"}
            </h2>
            <div className="flex flex-wrap gap-2 text-sm text-slate-600 dark:text-slate-300">
              {selectedCore.code ? (
                <span>
                  {formatFallback(t, "item.code", "Код")}: {selectedCore.code}
                </span>
              ) : null}
              {selectedCore.articul ? (
                <span>
                  {formatFallback(t, "item.articul", "Артикул")}:{" "}
                  {selectedCore.articul}
                </span>
              ) : null}
              {selectedItem?.barcode ? (
                <span>
                  {formatFallback(t, "item.barcode", "Штрихкод")}:{" "}
                  {selectedItem.barcode}
                </span>
              ) : null}
              {selectedItem?.icps ? (
                <span>
                  {formatFallback(t, "item.icps", "ИКПУ")}: {selectedItem.icps}
                </span>
              ) : null}
              <span>
                {formatFallback(t, "item.unit", "Ед.изм.")}:{" "}
                {selectedItem?.unit}
              </span>
            </div>
          </div>

          <div className="grid gap-3 grid-cols-2">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.group", "Группа")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {selectedCore.group?.path || "—"}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.brand", "Бренд")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {selectedCore.brand?.name || "—"}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.department", "Отдел")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {selectedCore.department?.name || "—"}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.updated", "Обновлено")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {selectedCore.last_update
                  ? fmt.unix(selectedCore.last_update)
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.color", "Цвет")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {colorName}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.size", "Размер")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {sizeName}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.producer", "Производитель")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {producerName}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.country", "Страна")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {countryName}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.partner", "Код Контрагента")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {partnerName}
              </p>
            </div>
          </div>

          {selectedQuantity ? (
            <div className="grid gap-3 md:grid-cols-3">
              <div
                className={cardClass(
                  "space-y-1 bg-slate-50/80 dark:bg-slate-900/40"
                )}
                aria-label="quantity-common"
              >
                <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {formatFallback(
                    t,
                    "item_info.quantity_common",
                    "Доступно всего"
                  )}
                </p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {fmt.number(
                    quantityInfo?.reduce(
                      (acc, item) => acc + (item.common ?? 0),
                      0
                    )
                  )}
                </p>
              </div>
              <div
                className={cardClass(
                  "space-y-1 bg-slate-50/80 dark:bg-slate-900/40"
                )}
                aria-label="quantity-allowed"
              >
                <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {formatFallback(
                    t,
                    "item_info.quantity_allowed",
                    "Разрешено к продаже"
                  )}
                </p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {fmt.number(
                    quantityInfo?.reduce(
                      (acc, item) => acc + (item.allowed ?? 0),
                      0
                    ) ?? 0
                  )}
                </p>
              </div>
              <div
                className={cardClass(
                  "space-y-1 bg-slate-50/80 dark:bg-slate-900/40"
                )}
                aria-label="quantity-booked"
              >
                <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {formatFallback(
                    t,
                    "item_info.quantity_booked",
                    "Зарезервировано"
                  )}
                </p>
                <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  {fmt.number(
                    quantityInfo?.reduce(
                      (acc, item) => acc + (item.booked ?? 0),
                      0
                    ) ?? 0
                  )}
                </p>
              </div>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-6">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.current_price", "Текущая цена")}
              </p>
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {fmt.money(
                  selectedPrice,
                  docCurrency,
                  selectedPriceType?.round_to
                )}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.precost", "Себестоимость")}
              </p>
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {fmt.money(lastPurchaseCost, docCurrency)}
              </p>
            </div>
          </div>

          {selectedCore.description ? (
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {formatFallback(t, "item_info.description", "Описание")}
              </p>
              <p className="text-sm text-slate-900 dark:text-slate-100">
                {selectedCore.description}
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      {detailsLoading ? (
        <div
          className={cardClass("text-sm text-slate-600 dark:text-slate-300")}
          aria-live="polite"
        >
          {formatFallback(t, "item_info.refreshing", "Обновляем данные...")}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        <div className={cardClass("space-y-3")} id="item-info-quantity">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
            {formatFallback(t, "item_info.quantity", "Остатки по складам")}
          </h2>
          {quantityInfo.length === 0 ? (
            <p className={mutedTextClass()}>
              {formatFallback(
                t,
                "item_info.quantity_empty",
                "Нет данных об остатках"
              )}
            </p>
          ) : (
            <div className="space-y-2">
              {quantityInfo.map((entry) => (
                <div
                  key={`${entry.stock?.id || "na"}-${
                    entry.stock?.name || "unknown"
                  }`}
                  className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700"
                >
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {entry.stock?.name ||
                      formatFallback(
                        t,
                        "item_info.stock_unknown",
                        "Склад не указан"
                      )}
                  </p>
                  <div className="flex flex-wrap gap-3 text-sm text-slate-600 dark:text-slate-300">
                    <span>
                      {formatFallback(t, "item_info.quantity_common", "Дст")}:{" "}
                      {fmt.number(entry.common ?? 0)}
                    </span>
                    <span>
                      {formatFallback(t, "item_info.quantity_allowed", "Раз")}:{" "}
                      {fmt.number(entry.allowed ?? 0)}
                    </span>
                    <span>
                      {formatFallback(t, "item_info.quantity_booked", "Рез")}:{" "}
                      {fmt.number(entry.booked ?? 0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className={cardClass("space-y-3")} id="item-info-prices">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
            {formatFallback(t, "item_info.prices", "Цены")}
          </h2>
          {pricesInfo.length === 0 ? (
            <p className={mutedTextClass()}>
              {formatFallback(
                t,
                "item_info.prices_empty",
                "Нет данных о ценах"
              )}
            </p>
          ) : (
            <div className="space-y-2">
              {pricesInfo.map((price) => {
                const currencyCode =
                  price.price_type?.currency?.code_chr ||
                  price.price_type?.currency?.code ||
                  docCurrency;
                return (
                  <div
                    key={`${price.item_id}-${price.price_type?.id || "pt"}`}
                    className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {price.price_type?.name ||
                            formatFallback(
                              t,
                              "item_info.price_type_unknown",
                              "Тип цены неизвестен"
                            )}
                        </p>
                        {/* <p className={mutedTextClass()}>
                          {price.price_type?.markup != null
                            ? `${formatFallback(
                                t,
                                "item_info.markup",
                                "Наценка"
                              )}: ${fmt.number(price.price_type.markup, {
                                maximumFractionDigits: 2,
                              })}`
                            : null}{" "}
                          %
                        </p> */}
                      </div>
                      <p className="text-base font-semibold text-slate-900 dark:text-slate-100">
                        {fmt.money(
                          price.value ?? 0,
                          currencyCode,
                          price.price_type?.round_to
                        )}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div
          className={cardClass("space-y-3 xl:col-span-2")}
          id="item-info-operations"
        >
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
            {formatFallback(t, "item_info.operations", "Последние операции")}
          </h2>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className={mutedTextClass()}>
              {formatFallback(
                t,
                "item_info.operations_visible",
                "Показано операций"
              )}
              : {filteredOperations.length} / {operations.length}
            </p>
            <div className="flex items-center gap-2">
              {operationFiltersActive ? (
                <span className="rounded-full bg-slate-900/5 px-2 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-100/10 dark:text-slate-200">
                  {formatFallback(
                    t,
                    "item_info.filters_active",
                    "Фильтры включены"
                  )}
                </span>
              ) : null}
              <button
                type="button"
                ref={filterButtonRef}
                className={iconButtonClass({
                  variant: operationFiltersActive ? "primary" : "ghost",
                })}
                onClick={handleOperationFiltersOpen}
                title={formatFallback(
                  t,
                  "item_info.open_filters",
                  "Настроить фильтры операций"
                )}
              >
                <span className="sr-only">
                  {formatFallback(
                    t,
                    "item_info.open_filters",
                    "Настроить фильтры операций"
                  )}
                </span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="h-5 w-5"
                  aria-hidden="true"
                >
                  <path d="M4 4.75A.75.75 0 0 1 4.75 4h10.5a.75.75 0 0 1 .56 1.242l-3.81 4.51v4.248a.75.75 0 0 1-.326.622l-2.5 1.75A.75.75 0 0 1 8 15.75v-4.998l-3.81-4.51A.75.75 0 0 1 4 4.75Z" />
                </svg>
              </button>
            </div>
          </div>
          {similarItems.length > 0 ? (
            <div
              className={cardClass("space-y-3 xl:col-span-2")}
              id="item-info-similar"
            >
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
                {formatFallback(
                  t,
                  "item_info.similar_items",
                  "Похожие номенклатуры"
                )}
              </h2>
              <div className="grid gap-3 xl:grid-cols-4">
                {similarItems.map((item) => (
                  <button
                    key={`${item.id}-${item.barcode || "similar"}`}
                    type="button"
                    className={cardClass(
                      "w-full text-left transition hover:-translate-y-0.5 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2"
                    )}
                    onClick={() => handlePickSimilarItem(item)}
                  >
                    <div className="flex flex-col gap-1 ">
                      <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                        {item.name || "—"}
                      </span>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                        {item.code ? (
                          <span>
                            {formatFallback(t, "item.code", "Код")}: {item.code}
                          </span>
                        ) : null}
                        {item.articul ? (
                          <span>
                            {formatFallback(t, "item.articul", "Артикул")}:{" "}
                            {item.articul}
                          </span>
                        ) : null}
                        {item.barcode ? <span>{item.barcode}</span> : null}
                        {item.color ? (
                          <span>
                            {formatFallback(t, "item_info.color", "Цвет")}:{" "}
                            {item.color}
                          </span>
                        ) : null}
                        {item.size ? (
                          <span>
                            {formatFallback(t, "item_info.size", "Размер")}:{" "}
                            {item.size}
                          </span>
                        ) : null}
                        {item.sizeChart ? (
                          <span>
                            {formatFallback(
                              t,
                              "item_info.size_chart",
                              "Размерная сетка"
                            )}
                            : {item.sizeChart}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {filteredOperations.length === 0 ? (
            <p className={mutedTextClass()}>
              {operationFiltersActive
                ? formatFallback(
                    t,
                    "item_info.operations_filtered_empty",
                    "Нет операций по выбранным фильтрам"
                  )
                : formatFallback(
                    t,
                    "item_info.operations_empty",
                    "Нет операций"
                  )}
            </p>
          ) : (
            <div className="space-y-2">
              {filteredOperations.map((op, index) => (
                <div
                  key={`${op.document_id || index}-${op.date || "date"}`}
                  className="rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-700"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {op.doc_type_name || op.document_type?.name || "—"}
                      </p>
                      <div className="flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                        {op.doc_code ? <span>{op.doc_code}</span> : null}
                        {op.stock?.name ? <span>• {op.stock.name}</span> : null}
                      </div>
                    </div>
                    <p className="text-sm text-slate-900 dark:text-slate-100">
                      {fmt.unix(op.date)}
                    </p>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-3 text-sm text-slate-600 dark:text-slate-300">
                    <span>
                      {formatFallback(t, "item_info.quantity", "Количество")}:{" "}
                      {fmt.number(op.quantity ?? 0)}
                    </span>
                    {op.price != null ? (
                      <span>
                        {formatFallback(t, "item_info.current_price", "Цена")}:{" "}
                        {fmt.money(op.price ?? 0, docCurrency)}
                      </span>
                    ) : null}
                    {op.positive != null ? (
                      <span>
                        {op.positive
                          ? formatFallback(
                              t,
                              "item_info.operation_income",
                              "Приход"
                            )
                          : formatFallback(
                              t,
                              "item_info.operation_outcome",
                              "Расход"
                            )}
                      </span>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {resultModalOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/70 px-4 py-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="item-info-search-results"
          onClick={closeResultModal}
        >
          <div
            className={cardClass(
              "relative mt-6 w-full max-w-lg space-y-4 shadow-xl"
            )}
            onClick={(event) => event.stopPropagation()}
          >
            <h2
              id="item-info-search-results"
              className="text-lg font-semibold text-slate-900 dark:text-slate-50"
            >
              {formatFallback(
                t,
                "item_info.choose_item",
                "Выберите номенклатуру"
              )}
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
                          {formatFallback(t, "item.code", "Код")}: {item.code}
                        </span>
                      ) : null}
                      {item.barcode ? <span>{item.barcode}</span> : null}
                    </div>
                    {item.articul ? (
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {formatFallback(t, "item.articul", "Артикул")}:{" "}
                        {item.articul}
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
                onClick={closeResultModal}
              >
                {formatFallback(t, "common.cancel", "Отмена")}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {operationFiltersOpen ? (
        <div
          className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="item-info-operations-filter-title"
          onClick={handleOperationFiltersCancel}
        >
          <div
            className={cardClass("absolute space-y-4 shadow-xl")}
            style={{
              top: operationFiltersAnchor?.top ?? "50%",
              left: operationFiltersAnchor?.left ?? "50%",
              width: operationFiltersAnchor?.width
                ? `${operationFiltersAnchor.width}px`
                : "min(360px, calc(100vw - 32px))",
              transform: operationFiltersAnchor
                ? "none"
                : "translate(-50%, -50%)",
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <h2
              id="item-info-operations-filter-title"
              className="text-lg font-semibold text-slate-900 dark:text-slate-50"
            >
              {formatFallback(
                t,
                "item_info.operations_filter_title",
                "Фильтры операций"
              )}
            </h2>

            <div className="space-y-4">
              <div className="space-y-1">
                <label
                  className={labelClass()}
                  htmlFor="item-info-operations-filter-stock"
                >
                  {formatFallback(t, "item_info.filter_stock", "Склад")}
                </label>
                <select
                  id="item-info-operations-filter-stock"
                  className={inputClass()}
                  value={operationFiltersDraft.stockId}
                  onChange={handleOperationFiltersChange("stockId")}
                >
                  <option value="all">
                    {formatFallback(
                      t,
                      "item_info.filter_all_stocks",
                      "Все склады"
                    )}
                  </option>
                  {operationStockOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label
                  className={labelClass()}
                  htmlFor="item-info-operations-filter-positive"
                >
                  {formatFallback(
                    t,
                    "item_info.filter_operation_type",
                    "Тип движения"
                  )}
                </label>
                <select
                  id="item-info-operations-filter-positive"
                  className={inputClass()}
                  value={operationFiltersDraft.positive}
                  onChange={handleOperationFiltersChange("positive")}
                >
                  <option value="all">
                    {formatFallback(
                      t,
                      "item_info.filter_all_movements",
                      "Все операции"
                    )}
                  </option>
                  <option value="true">
                    {formatFallback(t, "item_info.operation_income", "Приход")}
                  </option>
                  <option value="false">
                    {formatFallback(t, "item_info.operation_outcome", "Расход")}
                  </option>
                </select>
              </div>

              <div className="space-y-1">
                <label
                  className={labelClass()}
                  htmlFor="item-info-operations-filter-doc-type"
                >
                  {formatFallback(
                    t,
                    "item_info.filter_doc_type",
                    "Тип документа"
                  )}
                </label>
                <select
                  id="item-info-operations-filter-doc-type"
                  className={inputClass()}
                  value={operationFiltersDraft.docType}
                  onChange={handleOperationFiltersChange("docType")}
                >
                  <option value="all">
                    {formatFallback(
                      t,
                      "item_info.filter_all_doc_types",
                      "Все типы"
                    )}
                  </option>
                  {operationDocTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2 pt-2">
              <button
                type="button"
                className={buttonClass({ variant: "ghost", size: "sm" })}
                onClick={handleOperationFiltersCancel}
              >
                {formatFallback(t, "common.cancel", "Отмена")}
              </button>
              <button
                type="button"
                className={buttonClass({ variant: "secondary", size: "sm" })}
                onClick={handleOperationFiltersReset}
              >
                {formatFallback(t, "item_info.reset_filters", "Сбросить")}
              </button>
              <button
                type="button"
                className={buttonClass({ size: "sm" })}
                onClick={handleOperationFiltersApply}
              >
                {formatFallback(t, "item_info.apply_filters", "Применить")}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {settingsOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/70 px-4 py-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="item-info-settings-title"
          onClick={handleSettingsCancel}
        >
          <div
            className={cardClass(
              "relative mt-12 w-full max-w-md space-y-4 shadow-xl"
            )}
            onClick={(event) => event.stopPropagation()}
          >
            <h2
              id="item-info-settings-title"
              className="text-lg font-semibold text-slate-900 dark:text-slate-50"
            >
              {formatFallback(
                t,
                "item_info.settings_title",
                "Настройки поиска"
              )}
            </h2>
            {optionsLoading ? (
              <p className={mutedTextClass()}>
                {formatFallback(
                  t,
                  "item_info.settings_loading",
                  "Загрузка параметров..."
                )}
              </p>
            ) : null}
            <div className="space-y-4">
              <div className="space-y-2">
                <label
                  className={labelClass()}
                  htmlFor="item-info-settings-stock"
                >
                  {formatFallback(t, "item_info.stock", "Склад")}
                </label>
                <select
                  id="item-info-settings-stock"
                  className={inputClass()}
                  value={settingsDraft.stockId ?? stocks?.[0]?.value ?? ""}
                  onChange={(event) =>
                    setSettingsDraft((prev) => ({
                      ...prev,
                      stockId: event.target.value,
                    }))
                  }
                >
                  {stocks.map((stock) => (
                    <option key={stock.value} value={stock.value}>
                      {stock.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label
                  className={labelClass()}
                  htmlFor="item-info-settings-price-type"
                >
                  {formatFallback(t, "item_info.price_type", "Вид цены")}
                </label>
                <select
                  id="item-info-settings-price-type"
                  className={inputClass()}
                  value={
                    settingsDraft.priceTypeId ?? priceTypes?.[0]?.value ?? ""
                  }
                  onChange={(event) =>
                    setSettingsDraft((prev) => ({
                      ...prev,
                      priceTypeId: event.target.value,
                    }))
                  }
                >
                  {priceTypes.map((pt) => (
                    <option key={pt.value} value={pt.value}>
                      {pt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label
                  className={labelClass()}
                  htmlFor="item-info-settings-limit"
                >
                  {formatFallback(
                    t,
                    "item_info.limit",
                    "Лимит последних операций"
                  )}
                </label>
                <input
                  id="item-info-settings-limit"
                  type="number"
                  min={OPERATION_LIMIT_MIN}
                  max={OPERATION_LIMIT_MAX}
                  step={1}
                  className={inputClass()}
                  value={settingsDraft.limit ?? ""}
                  onChange={(event) =>
                    setSettingsDraft((prev) => ({
                      ...prev,
                      limit:
                        event.target.value === ""
                          ? ""
                          : Number(event.target.value),
                    }))
                  }
                />
                <p className={mutedTextClass()}>
                  {formatFallback(
                    t,
                    "item_info.limit_help",
                    "От 1 до 1000 записей"
                  )}
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                className={buttonClass({ variant: "ghost", size: "sm" })}
                onClick={handleSettingsCancel}
              >
                {formatFallback(t, "common.cancel", "Отмена")}
              </button>
              <button
                type="button"
                className={buttonClass({ variant: "primary", size: "sm" })}
                onClick={handleSettingsApply}
              >
                {formatFallback(t, "common.apply", "Применить")}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
