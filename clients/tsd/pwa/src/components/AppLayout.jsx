import React, { useCallback, useEffect, useMemo } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import Clock from "./Clock.jsx";
import InstallButton from "./InstallButton.jsx";
import LanguageSwitcher from "./LanguageSwitcher.jsx";
import NavBackButton from "./NavBackButton.jsx";

export default function AppLayout() {
  const { registerSW } = useApp();
  const { t } = useI18n();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    registerSW();
  }, [registerSW]);

  const { pathname } = location;

  const fallbackPath = useMemo(() => {
    if (pathname.startsWith("/doc/") && pathname.endsWith("/op/new")) {
      return pathname.replace(/\/op\/new\/?$/, "");
    }
    if (pathname.startsWith("/doc/")) {
      return "/docs";
    }
    if (pathname.startsWith("/docs")) {
      return "/home";
    }
    return "/home";
  }, [pathname]);

  const showBack = pathname !== "/home";

  const handleBack = useCallback(() => {
    const canGoBack =
      typeof window !== "undefined" && window.history?.state?.idx > 0;

    if (canGoBack) {
      navigate(-1);
      return;
    }

    if (pathname !== fallbackPath) {
      navigate(fallbackPath, { replace: true });
    } else {
      navigate("/home", { replace: true });
    }
  }, [navigate, pathname, fallbackPath]);

  const backLabelRaw = t("nav.back");
  const backLabel = backLabelRaw === "nav.back" ? "Назад" : backLabelRaw;
  const installLabelRaw = t("install_app");
  const installLabel =
    installLabelRaw === "install_app" ? "Установить" : installLabelRaw;

  return (
    <div className="app-shell">
      <header className="appbar">
        <div className="left">
          {showBack ? (
            <NavBackButton onClick={handleBack} label={backLabel} />
          ) : null}
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
