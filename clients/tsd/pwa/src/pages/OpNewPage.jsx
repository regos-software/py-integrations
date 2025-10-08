import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { BrowserMultiFormatReader, BarcodeFormat } from '@zxing/browser';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import { useToast } from '../context/ToastContext.jsx';

const ZXING_FORMATS = [
  BarcodeFormat.EAN_13,
  BarcodeFormat.EAN_8,
  BarcodeFormat.UPC_A,
  BarcodeFormat.UPC_E,
  BarcodeFormat.ITF,
  BarcodeFormat.CODE_128,
  BarcodeFormat.CODE_39,
  BarcodeFormat.CODABAR
].filter(Boolean);

const QUICK_QTY = [1, 5, 10, 12];

function firstBarcode(item) {
  return (
    item?.base_barcode ||
    (item?.barcode_list ? String(item.barcode_list).split(',')[0]?.trim() : '') ||
    item?.code ||
    ''
  );
}

async function listVideoDevices(reader) {
  const devices = await reader.listVideoInputDevices();
  return (devices || []).map((device) => ({
    deviceId: device.deviceId || device.id,
    label: device.label || ''
  })).filter((device) => device.deviceId);
}

function pickCamera(devices) {
  const prefer = [/macro|tele|zoom|close/i, /back|environment|rear/i];
  for (const pattern of prefer) {
    const match = devices.find((device) => pattern.test(device.label));
    if (match) return match.deviceId;
  }
  return devices[0]?.deviceId ?? null;
}

export default function OpNewPage() {
  const { id } = useParams();
  const docId = Number(id);
  const navigate = useNavigate();
  const { api, toNumber, setAppTitle } = useApp();
  const { t, fmt, locale } = useI18n();
  const { showToast } = useToast();

  const [docCtx, setDocCtx] = useState({ price_type_id: null, stock_id: null });
  const [barcodeValue, setBarcodeValue] = useState('');
  const [queryValue, setQueryValue] = useState('');
  const [quantity, setQuantity] = useState('');
  const [cost, setCost] = useState('');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');
  const [searchStatus, setSearchStatus] = useState('idle');
  const [picked, setPicked] = useState(null);
  const [saving, setSaving] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [currentDeviceId, setCurrentDeviceId] = useState(null);

  const videoRef = useRef(null);
  const readerRef = useRef(null);
  const controlsRef = useRef(null);

  useEffect(() => {
    setAppTitle(t('op.title') || 'Новая операция');
  }, [locale, setAppTitle, t]);

  useEffect(() => {
    async function loadDocMeta() {
      try {
        const { data } = await api('purchase_get', { doc_id: docId });
        const doc = data?.result?.doc;
        setDocCtx({
          price_type_id: doc?.price_type?.id ?? null,
          stock_id: doc?.stock?.id ?? null
        });
      } catch (err) {
        console.warn('[op_new] failed to fetch doc context', err);
      }
    }
    loadDocMeta();
  }, [api, docId]);

  const runSearch = useCallback(async (value) => {
    const queryText = value?.trim();
    if (!queryText) return;
    setSearchStatus('loading');
    try {
      const payload = { q: queryText, doc_id: docId };
      if (docCtx.price_type_id != null) payload.price_type_id = Number(docCtx.price_type_id);
      if (docCtx.stock_id != null) payload.stock_id = Number(docCtx.stock_id);
      const { data } = await api('product_search', payload);
      const items = data?.result?.items || [];
      if (!items.length) {
        setPicked(null);
        setSearchStatus('empty');
        return;
      }
      const ext = items[0];
      const core = ext?.item || {};
      setPicked({
        id: Number(core.id ?? core.code),
        name: core.name || '—',
        barcode: firstBarcode(core),
        vat_value: Number(core?.vat?.value ?? 0),
        last_purchase_cost: ext?.last_purchase_cost ?? null,
        price: ext?.price != null ? Number(ext.price) : null,
        quantity_common: ext?.quantity?.common ?? null,
        unit: core?.unit?.name || 'шт'
      });
      setSearchStatus('done');
      window.setTimeout(() => {
        document.getElementById('qty')?.focus();
      }, 0);
    } catch (err) {
      console.warn('[search] error', err);
      setPicked(null);
      setSearchStatus('error');
    }
  }, [api, docCtx.price_type_id, docCtx.stock_id, docId]);

  const ensureReader = useCallback(async () => {
    if (readerRef.current) return readerRef.current;
    const hints = new Map();
    // if (DecodeHintType.POSSIBLE_FORMATS) {
    //   hints.set(DecodeHintType.POSSIBLE_FORMATS, ZXING_FORMATS);
    // }
    readerRef.current = new BrowserMultiFormatReader(hints, {
      delayBetweenScanAttempts: 250
    });
    return readerRef.current;
  }, []);

  const stopScan = useCallback(() => {
    setScanning(false);
    try {
      controlsRef.current?.stop?.();
      controlsRef.current = null;
    } catch (err) {
      console.warn('[scan] stop error', err);
    }
    try {
      readerRef.current?.reset?.();
    } catch (err) {
      console.warn('[scan] reset error', err);
    }
    const video = videoRef.current;
    if (video) {
      try { video.pause?.(); } catch {}
      try { video.srcObject = null; } catch {}
    }
  }, []);

  useEffect(() => {
    const visibilityHandler = () => {
      if (document.hidden) stopScan();
    };
    document.addEventListener('visibilitychange', visibilityHandler);
    window.addEventListener('pagehide', stopScan);
    return () => {
      document.removeEventListener('visibilitychange', visibilityHandler);
      window.removeEventListener('pagehide', stopScan);
      stopScan();
    };
  }, [stopScan]);

  useEffect(() => {
    document.getElementById('barcode')?.focus();
  }, []);

  const startScan = useCallback(async () => {
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
      showToast(t('camera_open_failed') || 'Не удалось открыть камеру', { type: 'error' });
      return;
    }

    try {
      const reader = await ensureReader();
      const devices = await listVideoDevices(reader);
      if (!devices.length) {
        showToast(t('camera_open_failed') || 'Не удалось открыть камеру', { type: 'error' });
        return;
      }
      const selectedDeviceId = currentDeviceId || pickCamera(devices) || devices[0].deviceId;
      setCurrentDeviceId(selectedDeviceId);

      const controls = await reader.decodeFromVideoDevice(selectedDeviceId, videoRef.current, (result, err) => {
        if (result?.text) {
          const code = result.text;
          setBarcodeValue(code);
          setQueryValue(code);
          stopScan();
          runSearch(code);
          try { navigator.vibrate?.(35); } catch {}
        } else if (err && err.name !== 'NotFoundException') {
          console.debug('[ZXing]', err?.name || err);
        }
      });

      controlsRef.current = controls;
      setScanning(true);
    } catch (err) {
      console.error('[scan] start error', err);
      showToast(t('camera_open_failed') || 'Не удалось открыть камеру', { type: 'error' });
      stopScan();
    }
  }, [currentDeviceId, ensureReader, runSearch, showToast, stopScan, t]);

  const handleSubmit = async () => {
    if (!picked?.id) {
      showToast(t('select_product_first') || 'Сначала выберите товар', { type: 'error' });
      return;
    }
    const qtyNumber = toNumber(quantity);
    const costNumber = toNumber(cost);
    if (!qtyNumber || qtyNumber <= 0 || !costNumber || costNumber <= 0) {
      showToast(t('fill_required_fields') || 'Заполните обязательные поля', { type: 'error' });
      return;
    }

    const payload = {
      items: [{
        document_id: docId,
        item_id: Number(picked.id),
        quantity: qtyNumber,
        cost: costNumber,
        vat_value: Number(picked.vat_value ?? 0)
      }]
    };
    const priceNumber = toNumber(price);
    if (priceNumber > 0) payload.items[0].price = priceNumber;
    if (description.trim()) payload.items[0].description = description.trim();

    setSaving(true);
    try {
      const { ok, data } = await api('purchase_ops_add', payload);
      const affected = data?.result?.row_affected || 0;
      if (ok && affected > 0) {
        showToast(t('toast.op_added') || 'Операция добавлена', { type: 'success' });
        setQuantity('');
        setCost('');
        setPrice('');
        setBarcodeValue('');
        setQueryValue('');
        setPicked(null);
        setSearchStatus('idle');
        window.setTimeout(() => document.getElementById('barcode')?.focus(), 0);
      } else {
        throw new Error(data?.description || 'Save failed');
      }
    } catch (err) {
      showToast(err.message || t('save_failed') || 'Не удалось сохранить операцию', { type: 'error', duration: 2400 });
    } finally {
      setSaving(false);
    }
  };

  const descriptionPreview = useMemo(() => {
    if (!description.trim() || !picked) return '';
    return `${t('op.description') || 'Описание'}: ${description.trim()}`;
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
    <section className="stack" id="op-new">
      <h1>{t('op.title') || 'Новая операция'}</h1>

      <div id="scanner" className={`stack${scanning ? '' : ' hidden'}`}>
        <video id="preview" ref={videoRef} playsInline autoPlay muted />
        <div className="row">
          <span className="muted">{t('scanner.hint') || 'Наведи камеру на штрих-код'}</span>
          <button
            id="btn-close-scan"
            type="button"
            className="btn icon"
            onClick={stopScan}
            aria-label={t('common.cancel') || 'Отмена'}
            title={t('common.cancel') || 'Отмена'}
          >
            <i className="fa-solid fa-xmark" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="input-row">
        <label htmlFor="barcode" className="sr-only">{t('op.scan') || 'Штрих-код'}</label>
        <input
          id="barcode"
          type="search"
          inputMode="search"
          value={barcodeValue}
          placeholder={t('op.barcode.placeholder') || 'или введите штрих-код и нажмите Enter'}
          onChange={(event) => setBarcodeValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              runSearch(barcodeValue);
            }
          }}
        />
        <button
          id="btn-scan"
          type="button"
          className="btn icon"
          onClick={startScan}
          aria-label={t('op.scan') || 'Скан штрих-кода'}
          title={t('op.scan') || 'Скан штрих-кода'}
        >
          <i className="fa-solid fa-camera" aria-hidden="true" />
        </button>
      </div>

      <div className="stack">
        <label htmlFor="product-query">{t('op.search.label') || 'Поиск товара'}</label>
        <input
          id="product-query"
          type="search"
          value={queryValue}
          placeholder={t('op.search.placeholder') || 'Наименование / артикул'}
          onChange={(event) => setQueryValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              runSearch(queryValue);
            }
          }}
          onSearch={(event) => runSearch(event.target.value)}
        />
        <div id="product-results" className="muted" aria-live="polite">
          {searchStatus === 'loading' && (t('searching') || 'Поиск...')}
          {searchStatus === 'empty' && (t('common.nothing') || 'Ничего не найдено')}
          {searchStatus === 'error' && (t('search_error') || 'Ошибка поиска')}
        </div>
      </div>

      {picked && (
        <div id="product-picked" className="stack">
          <strong id="picked-name">{picked.name}</strong>
          <div className="muted">
            <span id="picked-code">{picked.barcode}</span>
            {picked.quantity_common != null && (
              <>
                <span className="dot" />
                <span>{fmt.number(picked.quantity_common)} {t('unit.pcs') || 'шт'}</span>
              </>
            )}
          </div>
          {descriptionPreview && (
            <div id="picked-desc" className="muted">{descriptionPreview}</div>
          )}
        </div>
      )}

      <div className="stack">
        <label htmlFor="qty">{(t('op.qty') || 'Количество')} <span className="muted">*</span></label>
        <input
          id="qty"
          type="number"
          inputMode="decimal"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              document.getElementById('cost')?.focus();
            }
          }}
        />
        <div className="qty-quick" id="qty-quick">
          {QUICK_QTY.map((value) => (
            <button
              key={value}
              type="button"
              className="chip"
              data-inc={value}
              onClick={() => setQuantity((prev) => String(toNumber(prev) + value))}
            >
              +{value}
            </button>
          ))}
        </div>
      </div>

      <div className="stack">
        <label htmlFor="cost">{(t('op.cost') || 'Стоимость')} <span className="muted">*</span></label>
        <input
          id="cost"
          type="number"
          inputMode="decimal"
          value={cost}
          onChange={(event) => setCost(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              document.getElementById('price')?.focus();
            }
          }}
        />
        {lpcLabel && (
          <button
            type="button"
            id="cost-hint"
            className="btn secondary"
            onClick={() => setCost(String(picked.last_purchase_cost))}
          >
            {lpcLabel}
          </button>
        )}
      </div>

      <div className="stack">
        <label htmlFor="price">{t('op.price') || 'Цена'}</label>
        <input
          id="price"
          type="number"
          inputMode="decimal"
          value={price}
          onChange={(event) => setPrice(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              handleSubmit();
            }
          }}
        />
        {priceLabel && (
          <button
            type="button"
            id="price-hint"
            className="btn secondary"
            onClick={() => setPrice(String(picked.price))}
          >
            {priceLabel}
          </button>
        )}
      </div>

      <div className="stack">
        <label htmlFor="description">{t('op.description') || 'Описание'}</label>
        <input
          id="description"
          type="text"
          value={description}
          placeholder={t('op.description.placeholder') || 'Комментарий к операции (необяз.)'}
          onChange={(event) => setDescription(event.target.value)}
        />
      </div>

      <div className="page-actions">
        <button
          id="btn-op-save"
          type="button"
          className="btn small"
          onClick={handleSubmit}
          disabled={saving}
        >
          {saving ? (t('op.saving') || 'Сохранение...') : (t('common.save') || 'Сохранить')}
        </button>
        <button
          id="btn-op-cancel"
          type="button"
          className="btn small ghost"
          onClick={() => navigate(`/doc/${docId}`)}
          disabled={saving}
        >
          {t('common.cancel') || 'Отмена'}
        </button>
      </div>
    </section>
  );
}
