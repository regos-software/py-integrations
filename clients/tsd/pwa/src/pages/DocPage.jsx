import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { useToast } from '../context/ToastContext.jsx';

function OperationRow({ op, onDelete, onSave }) {
  const { t, fmt } = useI18n();
  const { toNumber } = useApp();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    quantity: op.quantity,
    cost: op.cost,
    price: op.price ?? '',
    description: op.description ?? ''
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      quantity: op.quantity,
      cost: op.cost,
      price: op.price ?? '',
      description: op.description ?? ''
    });
  }, [op]);

  const item = op.item || {};
  const barcode = item.base_barcode || (item.barcode_list ? String(item.barcode_list).split(',')[0]?.trim() : '');
  const code = (item.code ?? '').toString().padStart(6, '0');
  const unitName = item.unit?.name || t('unit.pcs') || 'шт';

  const handleFieldChange = (field) => (event) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleSave = async () => {
    if (!form.quantity || toNumber(form.quantity) <= 0) {
      window.alert(t('op.qty.required') || 'Введите количество');
      return;
    }

    setSaving(true);
    const payload = {
      quantity: toNumber(form.quantity),
      cost: toNumber(form.cost),
      description: form.description || undefined
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
    <div className="item compact" key={op.id}>
      <div className={`row top${editing ? ' hidden' : ''}`}>
        <div className="info">
          <strong className="name">{item.name || ''}</strong>
          <div className="sub">
            <span className="muted text-small code">{code}</span>
            <span className="dot" />
            <span className="muted text-small barcode">{barcode}</span>
            {op.description ? (
              <>
                <span className="dot" />
                <span className="muted text-small description">{op.description}</span>
              </>
            ) : null}
          </div>
        </div>
        <div className="actions">
          <button
            type="button"
            className="btn icon clear op-edit"
            onClick={() => setEditing(true)}
            aria-label={t('op.edit') || 'Редактировать'}
            title={t('op.edit') || 'Редактировать'}
          >
            <i className="fa-solid fa-pen" aria-hidden="true" />
          </button>
          <button
            type="button"
            className="btn icon clear op-del"
            onClick={() => onDelete(op.id)}
            aria-label={t('op.delete') || 'Удалить'}
            title={t('op.delete') || 'Удалить'}
          >
            <i className="fa-solid fa-trash" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className={`meta bottom${editing ? ' hidden' : ''}`}>
        <span className="qty"><strong>{fmt.number(op.quantity)}</strong> {unitName}</span>
        <span className="dot" />
        <span className="cost">{fmt.money(op.cost)}</span>
        <span className="dot" />
        <span className="price">{fmt.money(op.price ?? 0)}</span>
      </div>

      {editing && (
        <div className="form-vert">
          <div>
            <label htmlFor={`qty-${op.id}`}>{t('op.qty') || 'Количество'}</label>
            <input
              id={`qty-${op.id}`}
              type="number"
              inputMode="decimal"
              value={form.quantity}
              onChange={handleFieldChange('quantity')}
            />
          </div>
          <div>
            <label htmlFor={`cost-${op.id}`}>{t('op.cost') || 'Стоимость'}</label>
            <input
              id={`cost-${op.id}`}
              type="number"
              inputMode="decimal"
              value={form.cost}
              onChange={handleFieldChange('cost')}
            />
          </div>
          <div>
            <label htmlFor={`price-${op.id}`}>{t('op.price') || 'Цена'}</label>
            <input
              id={`price-${op.id}`}
              type="number"
              inputMode="decimal"
              value={form.price}
              onChange={handleFieldChange('price')}
            />
          </div>
          <div>
            <label htmlFor={`description-${op.id}`}>{t('op.description') || 'Описание'}</label>
            <input
              id={`description-${op.id}`}
              type="text"
              value={form.description}
              onChange={handleFieldChange('description')}
            />
          </div>
          <div className="page-actions">
            <button
              type="button"
              className="btn small"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? (t('op.saving') || 'Сохранение...') : (t('common.save') || 'Сохранить')}
            </button>
            <button
              type="button"
              className="btn small ghost"
              onClick={() => setEditing(false)}
              disabled={saving}
            >
              {t('common.cancel') || 'Отмена'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DocPage() {
  const { id } = useParams();
  const { api, unixToLocal, setAppTitle } = useApp();
  const { t, locale, fmt } = useI18n();
  const { showToast } = useToast();
  const navigate = useNavigate();

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
        const { data } = await api('purchase_get', { doc_id: id });
        const docData = data?.result?.doc || {};
        let ops = data?.result?.operations;
        if (!Array.isArray(ops)) {
          const opsResponse = await api('purchase_ops_get', { doc_id: id });
          ops = opsResponse?.data?.result?.items || [];
        }
        if (!cancelled) {
          setDoc(docData);
          setOperations(ops);
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

  useEffect(() => {
    const prefix = t('doc.title_prefix') || 'Документ';
    const code = doc?.code || id;
    setAppTitle(`${prefix} ${code}`);
  }, [doc, id, locale, setAppTitle, t]);

  const handleDelete = async (opId) => {
    const question = t('confirm.delete_op') || 'Удалить операцию?';
    if (!window.confirm(question)) return;
    try {
      const { ok, data } = await api('purchase_ops_delete', { items: [{ id: opId }] });
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        setOperations((prev) => prev.filter((op) => op.id !== opId));
        showToast(t('toast.op_deleted') || 'Операция удалена', { type: 'success' });
      } else {
        throw new Error(data?.description || 'Delete failed');
      }
    } catch (err) {
      showToast(err.message || 'Не удалось удалить операцию', { type: 'error', duration: 2400 });
    }
  };

  const handleSave = async (opId, payload) => {
    try {
      const { ok, data } = await api('purchase_ops_edit', { items: [{ id: opId, ...payload }] });
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        setOperations((prev) => prev.map((op) => {
          if (op.id !== opId) return op;
          const next = { ...op, ...payload };
          if (!Object.prototype.hasOwnProperty.call(payload, 'price')) {
            next.price = op.price;
          }
          if (!Object.prototype.hasOwnProperty.call(payload, 'description')) {
            next.description = op.description;
          }
          return next;
        }));
        showToast(t('toast.op_updated') || 'Операция сохранена', { type: 'success' });
        return true;
      }
      throw new Error(data?.description || 'Save failed');
    } catch (err) {
      showToast(err.message || 'Не удалось сохранить операцию', { type: 'error', duration: 2400 });
      return false;
    }
  };

  const status = useMemo(() => {
    if (!doc) return '';
    const segments = [];
    const performed = t('docs.status.performed');
    const performedLabel = performed === 'docs.status.performed' ? 'проведён' : performed;
    const newLabel = t('docs.status.new');
    const newValue = newLabel === 'docs.status.new' ? 'новый' : newLabel;
    segments.push(doc.performed ? performedLabel : newValue);
    if (doc.blocked) {
      const blocked = t('docs.status.blocked');
      segments.push(blocked === 'docs.status.blocked' ? 'блок.' : blocked);
    }
    return segments.join(' • ');
  }, [doc, t]);

  if (loading) {
    return <div className="muted">{t('common.loading') || 'Загрузка...'}</div>;
  }

  if (error) {
    return <div className="muted">{String(error.message || error)}</div>;
  }

  if (!doc) {
    return <div className="muted">{t('common.nothing') || 'Ничего не найдено'}</div>;
  }

  const metaParts = [
    unixToLocal(doc.date),
    doc.partner?.name,
    fmt.money(doc.amount ?? 0, doc.currency?.code_chr ?? 'UZS')
  ].filter(Boolean).join(' · ');

  return (
    <section className="stack" id="doc">
      <div className="row row-start">
        <h1 id="doc-title">{(t('doc.title_prefix') || 'Документ')} {doc.code || id}</h1>
      </div>
      <div className="row">
        <div className="stack">
          <span id="doc-status" className="muted">{status}</span>
          <span id="doc-meta" className="muted">{metaParts}</span>
        </div>
        <button
          id="btn-add-op"
          type="button"
          className="btn small"
          onClick={() => navigate(`/doc/${id}/op/new`)}
        >
          {t('doc.add_op') || 'Добавить'}
        </button>
      </div>

      <div id="ops-list" className="list" aria-live="polite">
        {operations.length === 0 ? (
          <div className="muted">{t('doc.no_ops') || t('common.nothing') || 'Операций ещё нет'}</div>
        ) : (
          operations.map((operation) => (
            <OperationRow key={operation.id} op={operation} onDelete={handleDelete} onSave={handleSave} />
          ))
        )}
      </div>
    </section>
  );
}
