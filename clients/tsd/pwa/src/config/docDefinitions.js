const DEFAULT_PAGE_SIZE = 20;

const purchaseDefinition = {
  key: "purchase",
  labels: {
    title: "docs.title",
    searchPlaceholder: "docs.search.placeholder",
    refresh: "docs.refresh",
    nothing: "common.nothing",
  },
  navigation: {
    buildDocPath: (doc) => `/doc/${doc.id}`,
    buildDocsPath: () => "/docs",
    buildNewOperationPath: (docId) => `/doc/${docId}/op/new`,
  },
  list: {
    action: "docs.purchase.get",
    pageSize: DEFAULT_PAGE_SIZE,
    buildParams: ({ page, pageSize, search, filters = {} }) => {
      const params = {
        offset: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        sort_orders: [{ column: "date", direction: "desc" }],
      };
      params.performed = false;
      params.deleted_mark = false;

      const {
        performed,
        blocked,
        deleted_mark,
        stock_ids,
        start_date,
        end_date,
      } = filters;

      if (performed === true || performed === false) {
        params.performed = performed;
      } else if (performed == null) {
        delete params.performed;
      }
      if (blocked !== null && blocked !== undefined) {
        params.blocked = blocked;
      }
      if (deleted_mark === true || deleted_mark === false) {
        params.deleted_mark = deleted_mark;
      } else if (deleted_mark == null) {
        delete params.deleted_mark;
      }
      if (Array.isArray(stock_ids) && stock_ids.length > 0) {
        params.stock_ids = stock_ids;
      }
      if (start_date) {
        const parsed = new Date(start_date);
        if (!Number.isNaN(parsed.getTime())) {
          params.start_date = parsed.toISOString();
        }
      }
      if (end_date) {
        const parsed = new Date(end_date);
        if (!Number.isNaN(parsed.getTime())) {
          params.end_date = parsed.toISOString();
        }
      }

      return params;
    },
    transformResponse: (data = {}) => ({
      items: data.result || [],
      total: data.total || 0,
    }),
    mapItem: (doc, helpers) => {
      const { t, unixToLocal, fmt } = helpers;
      const performedRaw = t("docs.status.performed");
      const performedLabel =
        performedRaw === "docs.status.performed" ? "проведён" : performedRaw;
      const newRaw = t("docs.status.new");
      const newLabel = newRaw === "docs.status.new" ? "новый" : newRaw;
      const blockedRaw = t("docs.status.blocked");
      const blockedLabel =
        blockedRaw === "docs.status.blocked" ? "блок." : blockedRaw;

      const statusParts = [doc.performed ? performedLabel : newLabel];
      if (doc.blocked) statusParts.push(blockedLabel);

      const currency = doc.currency?.code_chr || "UZS";
      return {
        id: doc.id,
        title: doc.code || doc.id,
        subtitle: doc.partner?.name || "",
        rightTop: doc.date ? unixToLocal(doc.date) : "",
        rightBottom: statusParts.filter(Boolean).join(" • "),
        amountLabel:
          doc.amount != null
            ? fmt.money(doc.amount, currency, doc.price_type?.round_to)
            : undefined,
        stockLabel: doc.stock?.name || "",
        raw: doc,
      };
    },
  },
  detail: {
    docAction: "docs.purchase.get_by_id",
    buildDocPayload: (docId) => docId,
    operationsAction: "docs.purchase_operation.get_by_document_id",
    buildOperationsPayload: (docId) => docId,
    batch: {
      action: "batch.run",
      docKey: "doc",
      operationsKey: "operations",
      buildRequest: (docId) => ({
        stop_on_error: false,
        requests: [
          {
            key: "doc",
            path: "DocPurchase/Get",
            payload: { ids: [docId] },
          },
          {
            key: "operations",
            path: "PurchaseOperation/Get",
            payload: { document_ids: [docId] },
          },
        ],
      }),
      extractDoc: (response) => {
        if (!response) return null;
        const { result } = response;
        if (Array.isArray(result)) {
          return result[0] ?? null;
        }
        return result ?? null;
      },
      extractOperations: (response) => response?.result ?? [],
    },
    performAction: "docs.purchase.perform",
    cancelPerformAction: "docs.purchase.perform_cancel",
    lockAction: "docs.purchase.lock",
    unlockAction: "docs.purchase.unlock",
    deleteAction: "docs.purchase_operation.delete",
    buildDeletePayload: (opId) => [{ id: opId }],
    editAction: "docs.purchase_operation.edit",
    buildEditPayload: (opId, payload) => [{ id: opId, ...payload }],
    handleDeleteResponse: (data) => data?.result?.row_affected > 0,
    handleEditResponse: (data) => data?.result?.row_affected > 0,
    operationForm: {
      showCost: true,
      showPrice: true,
    },
    partnerLabelKey: "doc.partner",
    partnerLabelFallback: "Поставщик",
  },
  operation: {
    titleKey: "op.title",
    titleFallback: "Новая операция",
    docMetaAction: "docs.purchase.get_by_id",
    docMetaPayload: (docId) => docId,
    extractDocContext: (doc = {}) => ({
      price_type_id: doc?.price_type?.id ?? null,
      doc_currency: doc?.currency?.code_chr ?? null,
      stock_id: doc?.stock?.id ?? null,
      price_type_round_to: doc?.price_type?.round_to ?? null,
    }),
    search: {
      action: "references.item.get_ext",
      buildParams: ({ queryText, docCtx }) => ({
        search: queryText,
        price_type_id: docCtx?.price_type_id ?? undefined,
        stock_id: docCtx?.stock_id ?? undefined,
      }),
      normalize: (data = {}) => {
        const items = data.result || [];
        return items.map((ext) => {
          const core = ext?.item || {};
          const unit = core?.unit || {};
          const firstBarcode =
            core?.base_barcode ||
            (core?.barcode_list
              ? String(core.barcode_list).split(",")[0]?.trim()
              : "") ||
            core?.code ||
            "";

          return {
            id: Number(core.id ?? core.code),
            name: core.name || "—",
            barcode: firstBarcode,
            code: core?.code != null ? String(core.code) : null,
            vat_value: Number(core?.vat?.value ?? 0),
            last_purchase_cost:
              ext?.last_purchase_cost != null
                ? Number(ext.last_purchase_cost)
                : null,
            price: ext?.price != null ? Number(ext.price) : null,
            quantity_common: ext?.quantity?.common ?? null,
            unit: unit?.name || "шт",
            unit_piece: unit?.type === "pcs",
          };
        });
      },
    },
    addAction: "docs.purchase_operation.add",
    buildAddPayload: ({
      docId,
      picked,
      quantity,
      cost,
      price,
      description,
    }) => {
      const payload = [
        {
          document_id: docId,
          item_id: Number(picked.id),
          quantity,
          cost,
          vat_value: Number(picked.vat_value ?? 0),
        },
      ];
      if (price > 0) payload[0].price = price;
      if (description) payload[0].description = description;
      return payload;
    },
    handleAddResponse: (data) => data?.result?.row_affected > 0,
    form: {
      showCost: true,
      showPrice: true,
    },
  },
};

const inventoryDefinition = {
  key: "inventory",
  labels: {
    title: "docs.inventory.title",
    titleFallback: "Инвентаризации",
    searchPlaceholder: "docs.inventory.search.placeholder",
    searchPlaceholderFallback: "Поиск по номеру / складу...",
    refresh: "docs.refresh",
    nothing: "common.nothing",
    filtersTitle: "docs.filters.title",
  },
  navigation: {
    buildDocPath: (doc) => `/doc/${doc.id}?type=inventory`,
    buildDocsPath: () => "/docs?type=inventory",
    buildNewOperationPath: (docId) => `/doc/${docId}/op/new?type=inventory`,
  },
  list: {
    action: "docs.inventory.get",
    pageSize: DEFAULT_PAGE_SIZE,
    buildParams: ({ page, pageSize, search, filters = {} }) => {
      const normalizeDate = (value) => {
        if (!value) return null;
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) return null;
        return Math.floor(parsed.getTime() / 1000);
      };

      const params = {
        offset: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        sort_orders: [{ column: "OpenDate", direction: "desc" }],
        closed: false,
        deleted_mark: false,
      };

      const {
        performed,
        blocked,
        deleted_mark,
        stock_ids,
        start_date,
        end_date,
      } = filters;

      if (performed === true || performed === false) {
        params.closed = performed;
      } else if (performed == null) {
        delete params.closed;
      }
      if (blocked !== null && blocked !== undefined) {
        params.blocked = blocked;
      }
      if (deleted_mark === true || deleted_mark === false) {
        params.deleted_mark = deleted_mark;
      } else if (deleted_mark == null) {
        delete params.deleted_mark;
      }
      if (Array.isArray(stock_ids) && stock_ids.length > 0) {
        params.stock_ids = stock_ids;
      }

      const startTs = normalizeDate(start_date);
      if (startTs != null) {
        params.start_date = startTs;
      }
      const endTs = normalizeDate(end_date);
      if (endTs != null) {
        params.end_date = endTs;
      }

      return params;
    },
    transformResponse: (data = {}) => ({
      items: data.result || [],
      total: data.total || 0,
    }),
    mapItem: (doc, helpers) => {
      const { t, unixToLocal } = helpers;
      const closedRaw = t("docs.inventory.status.closed");
      const closedLabel =
        closedRaw === "docs.inventory.status.closed" ? "закрыт" : closedRaw;
      const openRaw = t("docs.inventory.status.open");
      const openLabel =
        openRaw === "docs.inventory.status.open" ? "открыт" : openRaw;
      const blockedRaw = t("docs.status.blocked");
      const blockedLabel =
        blockedRaw === "docs.status.blocked" ? "блок." : blockedRaw;

      const compareMap = {
        open_date: t("docs.inventory.compare.open_date"),
        close_date: t("docs.inventory.compare.close_date"),
        operation_date: t("docs.inventory.compare.operation_date"),
      };

      const statusParts = [doc.closed ? closedLabel : openLabel];
      if (doc.blocked) statusParts.push(blockedLabel);
      if (doc.compare_type) {
        const compareLabel = compareMap[doc.compare_type] || doc.compare_type;
        if (compareLabel) statusParts.push(compareLabel);
      }

      return {
        id: doc.id,
        title: doc.code || doc.id,
        subtitle: doc.stock?.name || "",
        rightTop: doc.open_date ? unixToLocal(doc.open_date) : "",
        rightBottom: statusParts.filter(Boolean).join(" • "),
        amountLabel: undefined,
        stockLabel:
          doc.attached_user?.full_name || doc.attached_user?.name || "",
        raw: doc,
      };
    },
  },
  detail: {
    docAction: "docs.inventory.get_by_id",
    buildDocPayload: (docId) => docId,
    operationsAction: "docs.inventory_operation.get",
    buildOperationsPayload: (docId, params = {}) => {
      const searchParam = params.search;
      return {
        document_ids: [docId],
        search:
          searchParam === undefined || searchParam === "" ? null : searchParam,
        limit: params.limit ?? 100,
      };
    },
    batch: {
      action: "batch.run",
      docKey: "doc",
      operationsKey: "operations",
      buildRequest: (docId) => ({
        stop_on_error: false,
        requests: [
          {
            key: "doc",
            path: "DocInventory/Get",
            payload: { ids: [docId] },
          },
          {
            key: "operations",
            path: "InventoryOperation/Get",
            payload: { document_ids: [docId], search: null, limit: 100 },
          },
        ],
      }),
      extractDoc: (response) => {
        if (!response) return null;
        const { result } = response;
        if (Array.isArray(result)) {
          return result[0] ?? null;
        }
        return result ?? null;
      },
      extractOperations: (response) => response?.result ?? [],
    },
    transformDoc: (raw) => {
      if (!raw) return null;
      const doc = { ...raw };
      const performed = Boolean(doc.closed);
      const partnerName =
        doc.attached_user?.full_name ||
        doc.attached_user?.name ||
        doc.attached_user?.login ||
        doc.stock?.name ||
        null;
      const currencyCode =
        doc.price_type?.currency?.code_chr ||
        doc.price_type?.currency?.code ||
        doc.currency?.code_chr ||
        doc.currency?.code ||
        "UZS";

      return {
        ...doc,
        performed,
        date: doc.close_date || doc.open_date || doc.date || null,
        partner: partnerName ? { name: partnerName } : doc.partner ?? null,
        amount:
          doc.amount ??
          doc.total_actual_quantity ??
          doc.total_registered_quantity ??
          0,
        currency: doc.currency ?? { code_chr: currencyCode },
      };
    },
    transformOperations: (response) => {
      const list = Array.isArray(response)
        ? response
        : Array.isArray(response?.result)
        ? response.result
        : [];

      return list.map((operation) => {
        const actual =
          operation.actual_quantity != null
            ? Number(operation.actual_quantity)
            : null;
        const registered =
          operation.registered_quantity != null
            ? Number(operation.registered_quantity)
            : null;
        const diff =
          actual != null && registered != null ? actual - registered : null;
        const diffParts = [];
        if (registered != null) {
          diffParts.push(`Учёт: ${registered}`);
        }
        if (diff != null && diff !== 0) {
          const sign = diff > 0 ? "+" : "";
          diffParts.push(`Δ: ${sign}${diff}`);
        }
        const metaDescription = diffParts.join(" • ");

        return {
          ...operation,
          quantity: actual,
          cost: null,
          description: [operation.description, metaDescription]
            .filter(Boolean)
            .join(" | "),
        };
      });
    },
    performAction: "docs.inventory.perform",
    cancelPerformAction: "docs.inventory.perform_cancel",
    lockAction: "docs.inventory.lock",
    unlockAction: "docs.inventory.unlock",
    deleteAction: "docs.inventory_operation.delete",
    buildDeletePayload: (opId) => [{ id: opId }],
    editAction: "docs.inventory_operation.edit",
    buildEditPayload: (opId, payload) => {
      const entry = {
        id: opId,
        actual_quantity: payload.quantity,
        update_actual_quantity: true,
      };
      if (payload.price != null) {
        entry.price = payload.price;
      }
      return [entry];
    },
    handleDeleteResponse: (data) => data?.result?.row_affected > 0,
    handleEditResponse: (data) => data?.result?.row_affected > 0,
    operationForm: {
      showCost: false,
      showPrice: false,
    },
    partnerLabelKey: "doc.inventory.responsible",
    partnerLabelFallback: "Ответственный",
  },
  operation: {
    titleKey: "op.inventory.title",
    titleFallback: "Новая строка инвентаризации",
    docMetaAction: "docs.inventory.get_by_id",
    docMetaPayload: (docId) => docId,
    extractDocContext: (doc = {}) => ({
      price_type_id: doc?.price_type?.id ?? null,
      doc_currency:
        doc?.price_type?.currency?.code_chr ||
        doc?.price_type?.currency?.code ||
        null,
      stock_id: doc?.stock?.id ?? null,
      price_type_round_to: doc?.price_type?.round_to ?? null,
    }),
    search: {
      action: "references.item.get_ext",
      buildParams: ({ queryText, docCtx }) => ({
        search: queryText,
        price_type_id: docCtx?.price_type_id ?? undefined,
        stock_id: docCtx?.stock_id ?? undefined,
      }),
      normalize: (data = {}) => {
        const items = data.result || [];
        return items.map((ext) => {
          const core = ext?.item || {};
          const unit = core?.unit || {};
          const firstBarcode =
            core?.base_barcode ||
            (core?.barcode_list
              ? String(core.barcode_list).split(",")[0]?.trim()
              : "") ||
            core?.code ||
            "";

          return {
            id: Number(core.id ?? core.code),
            name: core.name || "—",
            barcode: firstBarcode,
            code: core?.code != null ? String(core.code) : null,
            vat_value: Number(core?.vat?.value ?? 0),
            last_purchase_cost:
              ext?.last_purchase_cost != null
                ? Number(ext.last_purchase_cost)
                : null,
            price: ext?.price != null ? Number(ext.price) : null,
            quantity_common: ext?.quantity?.common ?? null,
            unit: unit?.name || "шт",
            unit_piece: unit?.type === "pcs",
          };
        });
      },
    },
    addAction: "docs.inventory_operation.add",
    buildAddPayload: ({ docId, picked, quantity, description }) => {
      return [
        {
          document_id: docId,
          item_id: Number(picked.id),
          actual_quantity: quantity,
          description: description,
          datetime: Math.floor(Date.now() / 1000),
          update_actual_quantity: false,
        },
      ];
    },
    handleAddResponse: (data) => data?.result?.row_affected > 0,
    form: {
      showCost: false,
      showPrice: false,
    },
  },
};

const wholesaleDefinition = {
  key: "wholesale",
  labels: {
    title: "docs.wholesale.title",
    titleFallback: "Отгрузки контрагентам",
    searchPlaceholder: "docs.wholesale.search.placeholder",
    searchPlaceholderFallback: "Поиск по номеру / клиенту...",
    refresh: "docs.refresh",
    nothing: "common.nothing",
  },
  navigation: {
    buildDocPath: (doc) => `/doc/${doc.id}?type=wholesale`,
    buildDocsPath: () => "/docs?type=wholesale",
    buildNewOperationPath: (docId) => `/doc/${docId}/op/new?type=wholesale`,
  },
  list: {
    action: "docs.wholesale.get",
    pageSize: DEFAULT_PAGE_SIZE,
    buildParams: ({ page, pageSize, search, filters = {} }) => {
      const params = {
        offset: (page - 1) * pageSize,
        limit: pageSize,
        search: search || undefined,
        sort_orders: [{ column: "date", direction: "desc" }],
      };
      params.performed = false;
      params.deleted_mark = false;

      const {
        performed,
        blocked,
        deleted_mark,
        stock_ids,
        start_date,
        end_date,
      } = filters;

      if (performed === true || performed === false) {
        params.performed = performed;
      } else if (performed == null) {
        delete params.performed;
      }
      if (blocked !== null && blocked !== undefined) {
        params.blocked = blocked;
      }
      if (deleted_mark === true || deleted_mark === false) {
        params.deleted_mark = deleted_mark;
      } else if (deleted_mark == null) {
        delete params.deleted_mark;
      }
      if (Array.isArray(stock_ids) && stock_ids.length > 0) {
        params.stock_ids = stock_ids;
      }
      if (start_date) {
        const parsed = new Date(start_date);
        if (!Number.isNaN(parsed.getTime())) {
          params.start_date = parsed.toISOString();
        }
      }
      if (end_date) {
        const parsed = new Date(end_date);
        if (!Number.isNaN(parsed.getTime())) {
          params.end_date = parsed.toISOString();
        }
      }

      return params;
    },
    transformResponse: (data = {}) => ({
      items: data.result || [],
      total: data.total || 0,
    }),
    mapItem: (doc, helpers) => {
      const { t, unixToLocal, fmt } = helpers;
      const performedRaw = t("docs.status.performed");
      const performedLabel =
        performedRaw === "docs.status.performed" ? "проведён" : performedRaw;
      const newRaw = t("docs.status.new");
      const newLabel = newRaw === "docs.status.new" ? "новый" : newRaw;
      const blockedRaw = t("docs.status.blocked");
      const blockedLabel =
        blockedRaw === "docs.status.blocked" ? "блок." : blockedRaw;

      const statusParts = [doc.performed ? performedLabel : newLabel];
      if (doc.blocked) statusParts.push(blockedLabel);

      const currency = doc.currency?.code_chr || "UZS";
      return {
        id: doc.id,
        title: doc.code || doc.id,
        subtitle: doc.partner?.name || "",
        rightTop: doc.date ? unixToLocal(doc.date) : "",
        rightBottom: statusParts.filter(Boolean).join(" • "),
        amountLabel:
          doc.amount != null
            ? fmt.money(doc.amount, currency, doc.price_type?.round_to)
            : undefined,
        stockLabel: doc.stock?.name || "",
        raw: doc,
      };
    },
  },
  detail: {
    docAction: "docs.wholesale.get_by_id",
    buildDocPayload: (docId) => docId,
    operationsAction: "docs.wholesale_operation.get_by_document_id",
    buildOperationsPayload: (docId) => docId,
    batch: {
      action: "batch.run",
      docKey: "doc",
      operationsKey: "operations",
      buildRequest: (docId) => ({
        stop_on_error: false,
        requests: [
          {
            key: "doc",
            path: "DocWholeSale/Get",
            payload: { ids: [docId] },
          },
          {
            key: "operations",
            path: "WholeSaleOperation/Get",
            payload: { document_ids: [docId] },
          },
        ],
      }),
      extractDoc: (response) => {
        if (!response) return null;
        const { result } = response;
        if (Array.isArray(result)) {
          return result[0] ?? null;
        }
        return result ?? null;
      },
      extractOperations: (response) => response?.result ?? [],
    },
    performAction: "docs.wholesale.perform",
    cancelPerformAction: "docs.wholesale.perform_cancel",
    lockAction: "docs.wholesale.lock",
    unlockAction: "docs.wholesale.unlock",
    deleteAction: "docs.wholesale_operation.delete",
    buildDeletePayload: (opId) => [{ id: opId }],
    editAction: "docs.wholesale_operation.edit",
    buildEditPayload: (opId, payload) => [{ id: opId, ...payload }],
    handleDeleteResponse: (data) => data?.result?.row_affected > 0,
    handleEditResponse: (data) => data?.result?.row_affected > 0,
    operationForm: {
      showCost: false,
      showPrice: true,
    },
    partnerLabelKey: "doc.wholesale.partner",
    partnerLabelFallback: "Покупатель",
  },
  operation: {
    titleKey: "op.wholesale.title",
    titleFallback: "Новая отгрузка",
    docMetaAction: "docs.wholesale.get_by_id",
    docMetaPayload: (docId) => docId,
    extractDocContext: (doc = {}) => ({
      price_type_id: doc?.price_type?.id ?? null,
      doc_currency: doc?.currency?.code_chr ?? null,
      stock_id: doc?.stock?.id ?? null,
      price_type_round_to: doc?.price_type?.round_to ?? null,
    }),
    search: {
      action: "references.item.get_ext",
      buildParams: ({ queryText, docCtx }) => ({
        search: queryText,
        price_type_id: docCtx?.price_type_id ?? undefined,
        stock_id: docCtx?.stock_id ?? undefined,
      }),
      normalize: (data = {}) => {
        const items = data.result || [];
        return items.map((ext) => {
          const core = ext?.item || {};
          const unit = core?.unit || {};
          const firstBarcode =
            core?.base_barcode ||
            (core?.barcode_list
              ? String(core.barcode_list).split(",")[0]?.trim()
              : "") ||
            core?.code ||
            "";

          const price = ext?.price != null ? Number(ext.price) : null;
          const basePrice =
            ext?.price2 != null
              ? Number(ext.price2)
              : price != null
              ? price
              : null;

          return {
            id: Number(core.id ?? core.code),
            name: core.name || "—",
            barcode: firstBarcode,
            code: core?.code != null ? String(core.code) : null,
            vat_value: Number(core?.vat?.value ?? 0),
            price,
            price2: basePrice,
            last_purchase_cost:
              ext?.last_purchase_cost != null
                ? Number(ext.last_purchase_cost)
                : null,
            quantity_common: ext?.quantity?.common ?? null,
            unit: unit?.name || "шт",
            unit_piece: unit?.type === "pcs",
          };
        });
      },
    },
    addAction: "docs.wholesale_operation.add",
    buildAddPayload: ({ docId, picked, quantity, price, description }) => {
      const entry = {
        document_id: docId,
        item_id: Number(picked.id),
        quantity,
        vat_value: Number(picked.vat_value ?? 0),
      };
      if (price > 0) entry.price = price;
      if (picked?.price2 != null) entry.price2 = Number(picked.price2);
      if (description) entry.description = description;
      return [entry];
    },
    handleAddResponse: (data) => data?.result?.row_affected > 0,
    form: {
      showCost: false,
      showPrice: true,
    },
    autoFill: {
      priceFromItem: true,
    },
  },
};

export const DOC_DEFINITIONS = {
  [purchaseDefinition.key]: purchaseDefinition,
  [inventoryDefinition.key]: inventoryDefinition,
  [wholesaleDefinition.key]: wholesaleDefinition,
};

export const DEFAULT_DOC_TYPE = purchaseDefinition.key;

export function getDocDefinition(type) {
  if (type && DOC_DEFINITIONS[type]) {
    return DOC_DEFINITIONS[type];
  }
  return DOC_DEFINITIONS[DEFAULT_DOC_TYPE];
}

export function isSupportedDocType(type) {
  return Boolean(type && DOC_DEFINITIONS[type]);
}

export function listDocTypes() {
  return Object.keys(DOC_DEFINITIONS);
}

export { DEFAULT_PAGE_SIZE };
