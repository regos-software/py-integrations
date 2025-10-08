import React, { useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import { useI18n } from '../context/I18nContext.jsx';
import Clock from './Clock.jsx';
import InstallButton from './InstallButton.jsx';
import LanguageSwitcher from './LanguageSwitcher.jsx';
import NavBackButton from './NavBackButton.jsx';

export default function AppLayout() {
  const { registerSW } = useApp();
  const { t } = useI18n();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    registerSW();
  }, [registerSW]);

  const showBack = location.pathname !== '/home';

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else if (location.pathname.startsWith('/doc')) {
      navigate('/docs', { replace: true });
    } else {
      navigate('/home', { replace: true });
    }
  };

  const backLabelRaw = t('nav.back');
  const backLabel = backLabelRaw === 'nav.back' ? 'Назад' : backLabelRaw;
  const installLabelRaw = t('install_app');
  const installLabel = installLabelRaw === 'install_app' ? 'Установить' : installLabelRaw;

  return (
    <div className="app-shell">
      <header className="appbar">
        <div className="left">
          {showBack ? <NavBackButton onClick={handleBack} label={backLabel} /> : null}
          <LanguageSwitcher />
        </div>
        <div className="right">
          <Clock />
          <InstallButton label={installLabel} />
          <div id="regos-login" />
        </div>
      </header>
      <main className="container content">
        <div className="card">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
