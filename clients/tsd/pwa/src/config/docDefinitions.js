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
    buildNewDocPath: () => "/doc/new?type=purchase",
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
  create: {
    addAction: "docs.purchase.add",
    titleKey: "doc.purchase.create.title",
    titleFallback: "Новый документ закупки",
    submitLabelKey: "common.create",
    submitLabelFallback: "Создать",
    successMessageKey: "toast.doc_purchase_created",
    successMessageFallback: "Документ создан",
    initialValues: () => ({
      vat_calculation_type: "No",
    }),
    references: {
      partners: {
        action: "references.partner.get",
        params: {
          deleted_mark: false,
          limit: 200,
          sort_orders: [{ column: "Name", direction: "asc" }],
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? item?.code ?? null;
              if (!id) return null;
              const name =
                item?.name ||
                item?.fullname ||
                item?.Name ||
                item?.FullName ||
                `#${id}`;
              const groupName =
                item?.partner_group?.name ||
                item?.partner_group?.Name ||
                item?.partner_group_name ||
                item?.partnerGroup?.name ||
                item?.partnerGroup?.Name ||
                item?.partnerGroupName ||
                item?.group?.name ||
                item?.group?.Name ||
                item?.group_name ||
                null;
              return {
                value: String(id),
                label: name,
                groupLabel:
                  typeof groupName === "string"
                    ? groupName.trim() || null
                    : null,
                raw: item,
              };
            })
              buildMetaSegments: (doc, helpers) => {
                const { unixToLocal, fmt } = helpers;
                const segments = [];
                if (doc?.date) {
                  segments.push(unixToLocal(doc.date));
                }
                const senderName =
                  doc?.stock_sender?.name ||
                  doc?.stockSender?.name ||
                  doc?.stock_sender_name ||
                  null;
                const receiverName =
                  doc?.stock_receiver?.name ||
                  doc?.stockReceiver?.name ||
                  doc?.stock_receiver_name ||
                  null;
                if (senderName || receiverName) {
                  segments.push(
                    senderName && receiverName
                      ? `${senderName} → ${receiverName}`
                      : senderName || receiverName
                  );
                }
                const partnerName =
                  doc?.partner?.name ||
                  doc?.partner?.Name ||
                  doc?.partner_name ||
                  null;
                if (partnerName) {
                  segments.push(partnerName);
                }
                const currency = doc?.currency?.code_chr || "UZS";
                const roundTo = doc?.price_type?.round_to ?? null;
                if (doc?.amount != null) {
                  const amountNumber = Number(doc.amount);
                  segments.push(fmt.money(amountNumber, currency, roundTo));
                }
                return segments;
              },
              buildPartnerValue: (doc) => {
                const senderName =
                  doc?.stock_sender?.name ||
                  doc?.stockSender?.name ||
                  doc?.stock_sender_name ||
                  null;
                const receiverName =
                  doc?.stock_receiver?.name ||
                  doc?.stockReceiver?.name ||
                  doc?.stock_receiver_name ||
                  null;
                if (senderName || receiverName) {
                  return senderName && receiverName
                    ? `${senderName} → ${receiverName}`
                    : senderName || receiverName;
                }
                return doc?.partner?.name || doc?.partner?.Name || "—";
              },
            .filter(Boolean);
        },
      },
      stocks: {
        action: "references.stock.get",
        params: {
          deleted_mark: false,
          limit: 200,
          sort_orders: [{ column: "Name", direction: "asc" }],
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? item?.code ?? null;
              if (!id) return null;
              const name = item?.name || item?.Name || `#${id}`;
              return {
                value: String(id),
                label: name,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      currencies: {
        action: "references.currency.get",
        params: {
          limit: 200,
          deleted: false,
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? item?.code_num ?? null;
              if (!id) return null;
              const code =
                item?.code_chr ||
                item?.CodeChr ||
                item?.code ||
                item?.Code ||
                `#${id}`;
              const name = item?.name || item?.Name || code;
              const label = `${code}${name ? ` — ${name}` : ""}`.trim();
              return {
                value: String(id),
                label,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      priceTypes: {
        action: "references.price_type.get",
        params: {
          limit: 200,
          sort_orders: [{ column: "Name", direction: "asc" }],
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? null;
              if (!id) return null;
              const name = item?.name || item?.Name || `#${id}`;
              const currencyCode =
                item?.currency?.code_chr ||
                item?.currency?.code ||
                item?.Currency?.code_chr ||
                item?.Currency?.code ||
                null;
              const label = currencyCode ? `${name} (${currencyCode})` : name;
              return {
                value: String(id),
                label,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      users: {
        action: "rbac.user.get",
        params: {
          active: true,
          limit: 200,
        },
        optional: true,
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? null;
              if (!id) return null;
              const name =
                item?.full_name ||
                `${item?.last_name || ""} ${item?.first_name || ""}`.trim() ||
                item?.login ||
                `#${id}`;
              return {
                value: String(id),
                label: name.trim() || `#${id}`,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
    },
    fields: [
      {
        key: "date",
        type: "date",
        required: true,
        labelKey: "doc.date",
        fallbackLabel: "Дата документа",
      },
      {
        key: "partner_id",
        type: "select",
        autocomplete: true,
        required: true,
        referenceKey: "partners",
        autoSelectFirst: true,
        labelKey: "doc.partner",
        fallbackLabel: "Контрагент",
        fallbackType: "number",
      },
      {
        key: "stock_id",
        autocomplete: true,
        type: "select",
        required: true,
        referenceKey: "stocks",
        autoSelectFirst: true,
        labelKey: "doc.stock",
        fallbackLabel: "Склад",
        fallbackType: "number",
      },
      {
        key: "currency_id",
        type: "select",
        required: true,
        referenceKey: "currencies",
        autoSelectFirst: true,
        labelKey: "doc.currency",
        fallbackLabel: "Валюта",
        fallbackType: "number",
      },
      {
        key: "price_type_id",
        type: "select",
        required: false,
        allowEmptyOption: true,
        referenceKey: "priceTypes",
        labelKey: "doc.price_type",
        fallbackLabel: "Тип цены",
      },
      {
        key: "vat_calculation_type",
        type: "select",
        required: false,
        labelKey: "doc.vat_calculation_type",
        fallbackLabel: "Расчёт НДС",
        options: () => [
          { value: "No", label: "Не начислять" },
          { value: "Exclude", label: "В сумме" },
          { value: "Include", label: "Начислить сверху" },
        ],
        defaultValue: "No",
      },
      {
        key: "exchange_rate",
        type: "number",
        required: false,
        step: "0.0001",
        labelKey: "doc.exchange_rate",
        fallbackLabel: "Курс валюты",
      },
      {
        key: "attached_user_id",
        type: "select",
        required: true,
        referenceKey: "users",
        allowEmptyOption: false,
        labelKey: "doc.employee",
        fallbackLabel: "Ответственный",
        fallbackType: "number",
      },
      {
        key: "contract_id",
        type: "number",
        required: false,
        labelKey: "doc.contract",
        fallbackLabel: "Договор",
      },
      {
        key: "description",
        type: "textarea",
        required: false,
        labelKey: "doc.description",
        fallbackLabel: "Комментарий",
      },
    ],
    buildPayload: (form, helpers) => {
      const parseId = (value) => {
        if (value == null || value === "") return null;
        const numeric = Number(value);
        return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
      };

      const dateUnix = helpers.toUnixTime(form.date);
      if (!dateUnix) {
        throw new Error("invalid_date");
      }

      const partnerId = parseId(form.partner_id);
      const stockId = parseId(form.stock_id);
      const currencyId = parseId(form.currency_id);
      const attachedUserId = parseId(form.attached_user_id);

      if (!partnerId || !stockId || !currencyId || !attachedUserId) {
        throw new Error("missing_required");
      }

      const payload = {
        date: dateUnix,
        partner_id: partnerId,
        stock_id: stockId,
        currency_id: currencyId,
        attached_user_id: attachedUserId,
      };

      const priceTypeId = parseId(form.price_type_id);
      if (priceTypeId) payload.price_type_id = priceTypeId;

      const contractId = parseId(form.contract_id);
      if (contractId) payload.contract_id = contractId;

      if (form.vat_calculation_type) {
        payload.vat_calculation_type = form.vat_calculation_type;
      }

      if (form.exchange_rate) {
        const rate = Number(form.exchange_rate);
        if (!Number.isNaN(rate) && rate > 0) {
          payload.exchange_rate = rate;
        }
      }

      if (form.description) {
        const trimmed = form.description.trim();
        if (trimmed) payload.description = trimmed;
      }

      return payload;
    },
    resolveCreatedId: (response) => {
      if (!response) return null;
      const { result } = response;
      if (result?.new_id) return Number(result.new_id);
      if (Array.isArray(result?.ids) && result.ids[0] != null) {
        return Number(result.ids[0]);
      }
      if (result?.id) return Number(result.id);
      if (response?.new_id) return Number(response.new_id);
      return null;
    },
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

        return {
          ...operation,
          quantity: actual,
          cost: null,
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
      showDescription: false,
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
    buildAddPayload: ({ docId, picked, quantity }) => {
      return [
        {
          document_id: docId,
          item_id: Number(picked.id),
          actual_quantity: quantity,
          datetime: Math.floor(Date.now() / 1000),
          update_actual_quantity: false,
        },
      ];
    },
    handleAddResponse: (data) => data?.result?.row_affected > 0,
    form: {
      showCost: false,
      showPrice: false,
      showDescription: false,
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
    buildNewDocPath: () => "/doc/new?type=wholesale",
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
  create: {
    addAction: "docs.wholesale.add",
    titleKey: "doc.wholesale.create.title",
    titleFallback: "Новый документ отгрузки",
    submitLabelKey: "common.create",
    submitLabelFallback: "Создать",
    successMessageKey: "toast.doc_wholesale_created",
    successMessageFallback: "Документ создан",
    initialValues: () => ({
      vat_calculation_type: "No",
    }),
    references: {
      partners: {
        action: "references.partner.get",
        params: {
          deleted_mark: false,
          limit: 200,
          sort_orders: [{ column: "Name", direction: "asc" }],
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? item?.code ?? null;
              if (!id) return null;
              const name =
                item?.name ||
                item?.fullname ||
                item?.Name ||
                item?.FullName ||
                `#${id}`;
              const groupName =
                item?.partner_group?.name ||
                item?.partner_group?.Name ||
                item?.partner_group_name ||
                item?.partnerGroup?.name ||
                item?.partnerGroup?.Name ||
                item?.partnerGroupName ||
                item?.group?.name ||
                item?.group?.Name ||
                item?.group_name ||
                null;
              return {
                value: String(id),
                label: name,
                groupLabel:
                  typeof groupName === "string"
                    ? groupName.trim() || null
                    : null,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      stocks: {
        action: "references.stock.get",
        params: {
          deleted_mark: false,
          limit: 200,
          sort_orders: [{ column: "Name", direction: "asc" }],
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? item?.code ?? null;
              if (!id) return null;
              const name = item?.name || item?.Name || `#${id}`;
              return {
                value: String(id),
                label: name,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      currencies: {
        action: "references.currency.get",
        params: {
          limit: 200,
          deleted: false,
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? item?.code_num ?? null;
              if (!id) return null;
              const code =
                item?.code_chr ||
                item?.CodeChr ||
                item?.code ||
                item?.Code ||
                `#${id}`;
              const name = item?.name || item?.Name || code;
              const label = `${code}${name ? ` — ${name}` : ""}`.trim();
              return {
                value: String(id),
                label,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      priceTypes: {
        action: "references.price_type.get",
        params: {
          limit: 200,
          sort_orders: [{ column: "Name", direction: "asc" }],
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? null;
              if (!id) return null;
              const name = item?.name || item?.Name || `#${id}`;
              const currencyCode =
                item?.currency?.code_chr ||
                item?.currency?.code ||
                item?.Currency?.code_chr ||
                item?.Currency?.code ||
                null;
              const label = currencyCode ? `${name} (${currencyCode})` : name;
              return {
                value: String(id),
                label,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      users: {
        action: "rbac.user.get",
        params: {
          active: true,
          limit: 200,
        },
        optional: true,
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? null;
              if (!id) return null;
              const name =
                item?.full_name ||
                `${item?.last_name || ""} ${item?.first_name || ""}`.trim() ||
                item?.login ||
                `#${id}`;
              return {
                value: String(id),
                label: name.trim() || `#${id}`,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
    },
    fields: [
      {
        key: "date",
        type: "date",
        required: true,
        labelKey: "doc.date",
        fallbackLabel: "Дата документа",
      },
      {
        key: "partner_id",
        type: "select",
        required: true,
        referenceKey: "partners",
        autoSelectFirst: true,
        labelKey: "doc.wholesale.partner",
        fallbackLabel: "Контрагент",
        fallbackType: "number",
      },
      {
        key: "stock_id",
        type: "select",
        required: true,
        referenceKey: "stocks",
        autoSelectFirst: true,
        labelKey: "doc.stock",
        fallbackLabel: "Склад",
        fallbackType: "number",
      },
      {
        key: "currency_id",
        type: "select",
        required: true,
        referenceKey: "currencies",
        autoSelectFirst: true,
        labelKey: "doc.currency",
        fallbackLabel: "Валюта",
        fallbackType: "number",
      },
      {
        key: "price_type_id",
        type: "select",
        required: false,
        allowEmptyOption: true,
        referenceKey: "priceTypes",
        labelKey: "doc.price_type",
        fallbackLabel: "Тип цены",
      },
      {
        key: "vat_calculation_type",
        type: "select",
        required: false,
        labelKey: "doc.vat_calculation_type",
        fallbackLabel: "Расчёт НДС",
        options: () => [
          { value: "No", label: "Не начислять" },
          { value: "Exclude", label: "В сумме" },
          { value: "Include", label: "Начислить сверху" },
        ],
        defaultValue: "No",
      },
      {
        key: "exchange_rate",
        type: "number",
        required: false,
        step: "0.0001",
        labelKey: "doc.exchange_rate",
        fallbackLabel: "Курс валюты",
      },
      {
        key: "attached_user_id",
        type: "select",
        required: false,
        referenceKey: "users",
        allowEmptyOption: true,
        labelKey: "doc.employee",
        fallbackLabel: "Ответственный",
        fallbackType: "number",
      },
      {
        key: "seller_id",
        type: "select",
        required: false,
        referenceKey: "users",
        allowEmptyOption: true,
        labelKey: "doc.wholesale.seller",
        fallbackLabel: "Продавец",
        fallbackType: "number",
      },
      {
        key: "contract_id",
        type: "number",
        required: false,
        labelKey: "doc.contract",
        fallbackLabel: "Договор",
      },
      {
        key: "description",
        type: "textarea",
        required: false,
        labelKey: "doc.description",
        fallbackLabel: "Комментарий",
      },
    ],
    buildPayload: (form, helpers) => {
      const parseId = (value) => {
        if (value == null || value === "") return null;
        const numeric = Number(value);
        return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
      };

      const dateUnix = helpers.toUnixTime(form.date);
      if (!dateUnix) {
        throw new Error("invalid_date");
      }

      const partnerId = parseId(form.partner_id);
      const stockId = parseId(form.stock_id);
      const currencyId = parseId(form.currency_id);

      if (!partnerId || !stockId || !currencyId) {
        throw new Error("missing_required");
      }

      const payload = {
        date: dateUnix,
        partner_id: partnerId,
        stock_id: stockId,
        currency_id: currencyId,
      };

      const priceTypeId = parseId(form.price_type_id);
      if (priceTypeId) payload.price_type_id = priceTypeId;

      const contractId = parseId(form.contract_id);
      if (contractId) payload.contract_id = contractId;

      const attachedUserId = parseId(form.attached_user_id);
      if (attachedUserId) payload.attached_user_id = attachedUserId;

      const sellerId = parseId(form.seller_id);
      if (sellerId) payload.seller_id = sellerId;

      if (form.vat_calculation_type) {
        payload.vat_calculation_type = form.vat_calculation_type;
      }

      if (form.exchange_rate) {
        const rate = Number(form.exchange_rate);
        if (!Number.isNaN(rate) && rate > 0) {
          payload.exchange_rate = rate;
        }
      }

      if (form.description) {
        const trimmed = form.description.trim();
        if (trimmed) payload.description = trimmed;
      }

      return payload;
    },
    resolveCreatedId: (response) => {
      if (!response) return null;
      const { result } = response;
      if (result?.new_id) return Number(result.new_id);
      if (Array.isArray(result?.ids) && result.ids[0] != null) {
        return Number(result.ids[0]);
      }
      if (result?.id) return Number(result.id);
      if (response?.new_id) return Number(response.new_id);
      return null;
    },
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

const movementDefinition = {
  key: "movement",
  labels: {
    title: "docs.movement.title",
    titleFallback: "Перемещения",
    searchPlaceholder: "docs.movement.search.placeholder",
    searchPlaceholderFallback: "Поиск по номеру / складам...",
    refresh: "docs.refresh",
    nothing: "common.nothing",
  },
  navigation: {
    buildDocPath: (doc) => `/doc/${doc.id}?type=movement`,
    buildDocsPath: () => "/docs?type=movement",
    buildNewOperationPath: (docId) => `/doc/${docId}/op/new?type=movement`,
    buildNewDocPath: () => "/doc/new?type=movement",
  },
  list: {
    action: "docs.movement.get",
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
        params.stock_sender_ids = stock_ids;
        params.stock_receiver_ids = stock_ids;
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
      const partnerName =
        doc.partner?.name || doc.partner?.Name || doc.partner_name || "";
      const stockSender =
        doc.stock_sender?.name ||
        doc.stockSender?.name ||
        doc.stock_sender_name ||
        "";
      const stockReceiver =
        doc.stock_receiver?.name ||
        doc.stockReceiver?.name ||
        doc.stock_receiver_name ||
        "";
      const primaryStock =
        stockSender && stockReceiver
          ? `${stockSender} → ${stockReceiver}`
          : stockSender || stockReceiver || doc.stock?.name || "";

      return {
        id: doc.id,
        title: doc.code || doc.id,
        subtitle: partnerName || primaryStock,
        rightTop: doc.date ? unixToLocal(doc.date) : "",
        rightBottom: statusParts.filter(Boolean).join(" • "),
        amountLabel:
          doc.amount != null
            ? fmt.money(doc.amount, currency, doc.price_type?.round_to)
            : undefined,
        stockLabel: primaryStock,
        raw: doc,
      };
    },
  },
  detail: {
    docAction: "docs.movement.get_by_id",
    buildDocPayload: (docId) => docId,
    operationsAction: "docs.movement_operation.get_by_document_id",
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
            path: "DocMovement/Get",
            payload: { ids: [docId] },
          },
          {
            key: "operations",
            path: "MovementOperation/Get",
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
    buildMetaSegments: (doc, helpers) => {
      const { unixToLocal, fmt } = helpers;
      const segments = [];
      if (doc?.date) {
        segments.push(unixToLocal(doc.date));
      }
      const senderName =
        doc?.stock_sender?.name ||
        doc?.stockSender?.name ||
        doc?.stock_sender_name ||
        null;
      const receiverName =
        doc?.stock_receiver?.name ||
        doc?.stockReceiver?.name ||
        doc?.stock_receiver_name ||
        null;
      if (senderName || receiverName) {
        segments.push(
          senderName && receiverName
            ? `${senderName} → ${receiverName}`
            : senderName || receiverName
        );
      }
      const partnerName =
        doc?.partner?.name ||
        doc?.partner?.Name ||
        doc?.partner_name ||
        null;
      if (partnerName) {
        segments.push(partnerName);
      }
      const currency = doc?.currency?.code_chr || "UZS";
      const roundTo = doc?.price_type?.round_to ?? null;
      if (doc?.amount != null) {
        const amountNumber = Number(doc.amount);
        if (Number.isFinite(amountNumber)) {
          segments.push(fmt.money(amountNumber, currency, roundTo));
        }
      }
      return segments;
    },
    buildPartnerValue: (doc) => {
      const senderName =
        doc?.stock_sender?.name ||
        doc?.stockSender?.name ||
        doc?.stock_sender_name ||
        null;
      const receiverName =
        doc?.stock_receiver?.name ||
        doc?.stockReceiver?.name ||
        doc?.stock_receiver_name ||
        null;
      if (senderName || receiverName) {
        return senderName && receiverName
          ? `${senderName} → ${receiverName}`
          : senderName || receiverName;
      }
      return doc?.partner?.name || doc?.partner?.Name || null;
    },
    performAction: "docs.movement.perform",
    cancelPerformAction: "docs.movement.perform_cancel",
    lockAction: "docs.movement.lock",
    unlockAction: "docs.movement.unlock",
    deleteAction: "docs.movement_operation.delete",
    buildDeletePayload: (opId) => [{ id: opId }],
    editAction: "docs.movement_operation.edit",
    buildEditPayload: (opId, payload) => [{ id: opId, ...payload }],
    handleDeleteResponse: (data) => data?.result?.row_affected > 0,
    handleEditResponse: (data) => data?.result?.row_affected > 0,
    operationForm: {
      showCost: false,
      showPrice: false,
    },
    partnerLabelKey: "doc.movement.stocks",
    partnerLabelFallback: "Склады",
  },
  create: {
    addAction: "docs.movement.add",
    titleKey: "doc.movement.create.title",
    titleFallback: "Новое перемещение",
    submitLabelKey: "common.create",
    submitLabelFallback: "Создать",
    successMessageKey: "toast.doc_movement_created",
    successMessageFallback: "Документ создан",
    references: {
      stocks: {
        action: "references.stock.get",
        params: {
          deleted_mark: false,
          limit: 200,
          sort_orders: [{ column: "Name", direction: "asc" }],
        },
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? item?.code ?? null;
              if (!id) return null;
              const name = item?.name || item?.Name || `#${id}`;
              return {
                value: String(id),
                label: name,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
      users: {
        action: "rbac.user.get",
        params: {
          active: true,
          limit: 200,
        },
        optional: true,
        transform: (data = {}) => {
          const list = Array.isArray(data.result) ? data.result : [];
          return list
            .map((item) => {
              const id = item?.id ?? item?.ID ?? null;
              if (!id) return null;
              const name =
                item?.full_name ||
                `${item?.last_name || ""} ${item?.first_name || ""}`.trim() ||
                item?.login ||
                `#${id}`;
              return {
                value: String(id),
                label: name.trim() || `#${id}`,
                raw: item,
              };
            })
            .filter(Boolean);
        },
      },
    },
    fields: [
      {
        key: "date",
        type: "date",
        required: true,
        labelKey: "doc.date",
        fallbackLabel: "Дата документа",
      },
      {
        key: "stock_sender_id",
        type: "select",
        required: true,
        referenceKey: "stocks",
        autoSelectFirst: true,
        labelKey: "doc.movement.stock_sender",
        fallbackLabel: "Склад-отправитель",
        fallbackType: "number",
      },
      {
        key: "stock_receiver_id",
        type: "select",
        required: true,
        referenceKey: "stocks",
        autoSelectFirst: false,
        labelKey: "doc.movement.stock_receiver",
        fallbackLabel: "Склад-получатель",
        fallbackType: "number",
      },
      {
        key: "attached_user_id",
        type: "select",
        required: false,
        referenceKey: "users",
        allowEmptyOption: true,
        labelKey: "doc.employee",
        fallbackLabel: "Ответственный",
        fallbackType: "number",
      },
      {
        key: "description",
        type: "textarea",
        required: false,
        labelKey: "doc.description",
        fallbackLabel: "Комментарий",
      },
    ],
    buildPayload: (form, helpers) => {
      const { toUnixTime } = helpers;

      const parseId = (value) => {
        if (value == null || value === "") return null;
        const numeric = Number(value);
        return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
      };

      const dateUnix = toUnixTime(form.date);
      if (!dateUnix) {
        throw new Error("invalid_date");
      }

      const stockSenderId = parseId(form.stock_sender_id);
      const stockReceiverId = parseId(form.stock_receiver_id);
      if (!stockSenderId || !stockReceiverId) {
        throw new Error("Укажите склады отправителя и получателя");
      }

      const payload = {
        date: dateUnix,
        stock_sender_id: stockSenderId,
        stock_receiver_id: stockReceiverId,
      };

      const attachedId = parseId(form.attached_user_id);
      if (attachedId) {
        payload.attached_user_id = attachedId;
      }

      const description =
        typeof form.description === "string" ? form.description.trim() : "";
      if (description) {
        payload.description = description;
      }

      return payload;
    },
    resolveCreatedId: (response) => {
      if (!response) return null;
      const { result } = response;
      if (result?.new_id != null) return Number(result.new_id);
      if (Array.isArray(result?.ids) && result.ids[0] != null) {
        return Number(result.ids[0]);
      }
      if (result?.id != null) return Number(result.id);
      if (response?.new_id != null) return Number(response.new_id);
      return null;
    },
  },
  operation: {
    titleKey: "op.movement.title",
    titleFallback: "Новая операция перемещения",
    docMetaAction: "docs.movement.get_by_id",
    docMetaPayload: (docId) => docId,
    extractDocContext: (doc = {}) => ({
      stock_id:
        doc?.stock?.id ??
        doc?.stock_sender?.id ??
        doc?.stock_receiver?.id ??
        doc?.stockSender?.id ??
        doc?.stockReceiver?.id ??
        null,
      stock_sender_id:
        doc?.stock_sender?.id ??
        doc?.stockSender?.id ??
        doc?.stock_sender_id ??
        null,
      stock_receiver_id:
        doc?.stock_receiver?.id ??
        doc?.stockReceiver?.id ??
        doc?.stock_receiver_id ??
        null,
    }),
    search: {
      action: "references.item.get_ext",
      buildParams: ({ queryText, docCtx }) => ({
        search: queryText,
        stock_id: docCtx?.stock_sender_id ?? docCtx?.stock_id ?? undefined,
      }),
      normalize: (data = {}) => {
        const items = data.result || [];
        return items
          .map((ext) => {
          const core = ext?.item || {};
          const unit = core?.unit || {};
          const firstBarcode =
            core?.base_barcode ||
            (core?.barcode_list
              ? String(core.barcode_list).split(",")[0]?.trim()
              : "") ||
            core?.code ||
            "";

            const rawId = core.id ?? core.code;
            const id = Number(rawId);
            if (!Number.isFinite(id)) {
              return null;
            }

          return {
            id,
            name: core.name || "—",
            barcode: firstBarcode,
            code: core?.code != null ? String(core.code) : null,
            vat_value: Number(core?.vat?.value ?? 0),
            last_purchase_cost:
              ext?.last_purchase_cost != null
                ? Number(ext.last_purchase_cost)
                : null,
            quantity_common: ext?.quantity?.common ?? null,
            unit: unit?.name || "шт",
            unit_piece: unit?.type === "pcs",
          };
        })
          .filter(Boolean);
      },
    },
    addAction: "docs.movement_operation.add",
    buildAddPayload: ({ docId, picked, quantity, description }) => {
      const qty = Number(quantity);
      if (!Number.isFinite(qty) || qty <= 0) {
        return null;
      }

      const entry = {
        document_id: docId,
        item_id: Number(picked.id),
        quantity: qty,
      };

      if (description) {
        entry.description = description;
      }

      return [entry];
    },
    handleAddResponse: (data) => data?.result?.row_affected > 0,
    form: {
      showCost: false,
      showPrice: false,
      showDescription: true,
    },
  },
};

export const DOC_DEFINITIONS = {
  [purchaseDefinition.key]: purchaseDefinition,
  [inventoryDefinition.key]: inventoryDefinition,
  [movementDefinition.key]: movementDefinition,
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
