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
    action: "docs.purchase.get_raw",
    pageSize: DEFAULT_PAGE_SIZE,
    buildParams: ({ page, pageSize, search }) => ({
      offset: (page - 1) * pageSize,
      limit: pageSize,
      search: search || undefined,
      performed: false,
      deleted_mark: false,
      sort_orders: [{ column: "date", direction: "desc" }],
    }),
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
        raw: doc,
      };
    },
  },
  detail: {
    docAction: "docs.purchase.get_by_id",
    buildDocPayload: (docId) => docId,
    operationsAction: "docs.purchase_operation.get_by_document_id",
    buildOperationsPayload: (docId) => docId,
    deleteAction: "docs.purchase_operation.delete_raw",
    buildDeletePayload: (opId) => [{ id: opId }],
    editAction: "docs.purchase_operation.edit_raw",
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
      action: "refrences.item.get_ext_raw",
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
    addAction: "docs.purchase_operation.add_raw",
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
    action: "docs.wholesale.get_raw",
    pageSize: DEFAULT_PAGE_SIZE,
    buildParams: ({ page, pageSize, search }) => ({
      offset: (page - 1) * pageSize,
      limit: pageSize,
      search: search || undefined,
      performed: false,
      deleted_mark: false,
      sort_orders: [{ column: "date", direction: "desc" }],
    }),
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
        raw: doc,
      };
    },
  },
  detail: {
    docAction: "docs.wholesale.get_by_id",
    buildDocPayload: (docId) => docId,
    operationsAction: "docs.wholesale_operation.get_by_document_id",
    buildOperationsPayload: (docId) => docId,
    deleteAction: "docs.wholesale_operation.delete_raw",
    buildDeletePayload: (opId) => [{ id: opId }],
    editAction: "docs.wholesale_operation.edit_raw",
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
      action: "refrences.item.get_ext_raw",
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
            vat_value: Number(core?.vat?.value ?? 0),
            price,
            price2: basePrice,
            quantity_common: ext?.quantity?.common ?? null,
            unit: unit?.name || "шт",
            unit_piece: unit?.type === "pcs",
          };
        });
      },
    },
    addAction: "docs.wholesale_operation.add_raw",
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
