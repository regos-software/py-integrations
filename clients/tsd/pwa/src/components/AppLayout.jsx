import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext.jsx";
import { useI18n } from "../context/I18nContext.jsx";
import Clock from "./Clock.jsx";
import InstallButton from "./InstallButton.jsx";
import LanguageSwitcher from "./LanguageSwitcher.jsx";
import NavBackButton from "./NavBackButton.jsx";
import QRCode from "qrcode";

export default function AppLayout() {
  const { registerSW } = useApp();
  const { t } = useI18n();
  const location = useLocation();
  const navigate = useNavigate();
  const [qrOpen, setQrOpen] = useState(false);
  const [qrGenerating, setQrGenerating] = useState(false);
  const [qrImage, setQrImage] = useState("");
  const [qrError, setQrError] = useState(null);
  const [qrCopied, setQrCopied] = useState(false);

  useEffect(() => {
    registerSW();
  }, [registerSW]);

  const { pathname, search = "", hash = "" } = location;

  const currentUrl = useMemo(() => {
    const suffix = `${pathname}${search || ""}${hash || ""}`;
    if (typeof window === "undefined" || !window.location?.origin) {
      return suffix;
    }
    return `${window.location.origin}${suffix}`;
  }, [hash, pathname, search]);

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

  const handleCloseQr = useCallback(() => {
    setQrOpen(false);
  }, []);

  useEffect(() => {
    if (!qrOpen) {
      setQrGenerating(false);
      setQrImage("");
      setQrError(null);
      setQrCopied(false);
    }
  }, [qrOpen]);

  const handleOpenQr = useCallback(async () => {
    setQrOpen(true);
    setQrGenerating(true);
    setQrError(null);
    try {
      const dataUrl = await QRCode.toDataURL(currentUrl, {
        width: 280,
        margin: 1,
        errorCorrectionLevel: "M",
        color: { dark: "#111827", light: "#ffffff" },
      });
      setQrImage(dataUrl);
    } catch (err) {
      console.error("[qr] generate error", err);
      const fallback =
        t("qr.generate_failed") || "Не удалось создать QR-код для страницы";
      setQrError(fallback);
    } finally {
      setQrGenerating(false);
    }
  }, [currentUrl, t]);

  const handleCopyLink = useCallback(async () => {
    if (!navigator?.clipboard?.writeText) {
      setQrError(
        t("qr.copy_not_supported") || "Копирование ссылки не поддерживается"
      );
      return;
    }
    try {
      await navigator.clipboard.writeText(currentUrl);
      setQrCopied(true);
      window.setTimeout(() => setQrCopied(false), 1600);
    } catch (err) {
      console.error("[qr] copy error", err);
      setQrError(t("qr.copy_failed") || "Не удалось скопировать ссылку");
    }
  }, [currentUrl, t]);

  return (
    <div className="app-shell">
      <header className="appbar">
        <div className="left">
          {showBack ? (
            <NavBackButton onClick={handleBack} label={backLabel} />
          ) : null}
          <LanguageSwitcher />
          <button
            type="button"
            className="btn icon"
            onClick={handleOpenQr}
            aria-label={
              t("qr.share_button") || "Показать QR-код текущей страницы"
            }
            title={t("qr.share_button") || "Показать QR-код текущей страницы"}
          >
            <i className="fa-solid fa-qrcode" aria-hidden="true" />
          </button>
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
      {qrOpen ? (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={handleCloseQr}
        >
          <div
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="qr-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="row qr-modal-header">
              <h2 id="qr-modal-title">
                {t("qr.share_title") || "Сканируйте на другом устройстве"}
              </h2>
              <button
                type="button"
                className="btn icon"
                onClick={handleCloseQr}
                aria-label={t("common.close") || "Закрыть"}
                title={t("common.close") || "Закрыть"}
              >
                <i className="fa-solid fa-xmark" aria-hidden="true" />
              </button>
            </div>
            <div className="qr-modal-body">
              {qrGenerating ? (
                <p className="muted">
                  {t("qr.generating") || "Готовим QR-код..."}
                </p>
              ) : qrError ? (
                <p className="modal-error">{qrError}</p>
              ) : (
                <img
                  src={qrImage}
                  alt={
                    t("qr.image_alt") ||
                    "QR-код для открытия этой страницы на другом устройстве"
                  }
                />
              )}
            </div>
            <p className="qr-url" aria-live="polite">
              {currentUrl}
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="btn secondary"
                onClick={handleCopyLink}
                disabled={qrGenerating}
              >
                {qrCopied
                  ? t("qr.copied") || "Ссылка скопирована"
                  : t("qr.copy") || "Скопировать ссылку"}
              </button>
              <button
                type="button"
                className="btn ghost"
                onClick={handleCloseQr}
              >
                {t("common.close") || "Закрыть"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
