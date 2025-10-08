import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../context/I18nContext.jsx';
import { useToast } from '../context/ToastContext.jsx';
import { useApp } from '../context/AppContext.jsx';

export default function HomePage() {
  const { t, locale } = useI18n();
  const { setAppTitle } = useApp();
  const { showToast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    const raw = t('app.title');
    const title = raw === 'app.title' ? 'TSD' : raw || 'TSD';
    setAppTitle(title);
  }, [locale, setAppTitle, t]);

  const soonLabelRaw = t('soon');
  const soonLabel = soonLabelRaw === 'soon' ? 'Скоро' : soonLabelRaw || 'Скоро';

  const soon = () => showToast(soonLabel, { duration: 1500, type: 'info' });

  return (
    <section className="stack" id="home">
  <h1 id="home-title">{t('main_menu') === 'main_menu' ? 'Главное меню' : t('main_menu') || 'Главное меню'}</h1>
      <div className="stack">
        <button
          id="btn-doc-purchase"
          type="button"
          className="btn block"
          onClick={() => navigate('/docs')}
        >
          <span id="btn-doc-purchase-txt">{t('doc_purchase') === 'doc_purchase' ? 'Поступление от контрагента' : t('doc_purchase') || 'Поступление от контрагента'}</span>
        </button>

        <button
          id="btn-doc-sales"
          type="button"
          className="btn block ghost"
          onClick={soon}
        >
          <div className="row">
            <span id="btn-doc-sales-txt">{t('doc_sales') === 'doc_sales' ? 'Отгрузка контрагенту' : t('doc_sales') || 'Отгрузка контрагенту'}</span>
            <span className="pill" id="pill-sales">{soonLabel}</span>
          </div>
        </button>

        <button
          id="btn-doc-inventory"
          type="button"
          className="btn block ghost"
          onClick={soon}
        >
          <div className="row">
            <span id="btn-doc-inventory-txt">{t('doc_inventory') === 'doc_inventory' ? 'Инвентаризация' : t('doc_inventory') || 'Инвентаризация'}</span>
            <span className="pill" id="pill-inventory">{soonLabel}</span>
          </div>
        </button>
      </div>
    </section>
  );
}
