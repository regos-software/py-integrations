import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useI18n } from "../context/I18nContext.jsx";
import {
  buttonClass,
  cardClass,
  iconButtonClass,
  mutedTextClass,
} from "../lib/ui";
import { cn } from "../lib/utils";
import Clock from "./Clock.jsx";
import InstallButton from "./InstallButton.jsx";
import LanguageSwitcher from "./LanguageSwitcher.jsx";
import NavBackButton from "./NavBackButton.jsx";
import QRCode from "qrcode";

export default function AppLayout() {
  const { t } = useI18n();
  const location = useLocation();
  const navigate = useNavigate();
  const [qrOpen, setQrOpen] = useState(false);
  const [qrGenerating, setQrGenerating] = useState(false);
  const [qrImage, setQrImage] = useState("");
  const [qrError, setQrError] = useState(null);
  const [qrCopied, setQrCopied] = useState(false);
  const [installDismissed, setInstallDismissed] = useState(false);
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") return "light";
    const stored = window.localStorage.getItem("tsd-theme");
    if (stored === "dark" || stored === "light") return stored;
    if (window.matchMedia?.("(prefers-color-scheme: dark)")?.matches) {
      return "dark";
    }
    return "light";
  });

  const { pathname, search = "", hash = "" } = location;

  const currentUrl = useMemo(() => {
    if (typeof window !== "undefined" && window.location?.href) {
      return window.location.href;
    }
    return `${pathname}${search || ""}${hash || ""}`;
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
  const installHintRaw = t("install.banner_hint");
  const installHint =
    installHintRaw === "install.banner_hint"
      ? "Install the app for quick access"
      : installHintRaw;
  const closeLabelRaw = t("common.close");
  const closeLabel =
    closeLabelRaw === "common.close" ? "Закрыть" : closeLabelRaw;
  const isDark = theme === "dark";
  const themeToggleLabel = isDark
    ? t("theme.switch_to_light") || "Переключить на светлую тему"
    : t("theme.switch_to_dark") || "Переключить на тёмную тему";

  const handleCloseQr = useCallback(() => {
    setQrOpen(false);
  }, []);

  const handleToggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("tsd-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!qrOpen) {
      setQrGenerating(false);
      setQrImage("");
      setQrError(null);
      setQrCopied(false);
    }
  }, [qrOpen]);

  useEffect(() => {
    setInstallDismissed(false);
  }, [pathname]);

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
    <div className="relative min-h-screen bg-slate-100 text-slate-900 transition dark:bg-slate-900 dark:text-slate-100">
      <header className="sticky top-0 z-40 mx-auto mt-4 flex w-full max-w-5xl items-center justify-between gap-3 rounded-3xl border border-slate-200 bg-white/85 px-4 py-3 shadow-sm backdrop-blur dark:border-slate-700 dark:bg-slate-900/80 sm:px-6">
        <div className="flex items-center gap-3">
          {showBack ? (
            <NavBackButton onClick={handleBack} label={backLabel} />
          ) : null}
          <LanguageSwitcher />
          <button
            type="button"
            className={iconButtonClass({ variant: "ghost" })}
            onClick={handleToggleTheme}
            aria-label={themeToggleLabel}
            title={themeToggleLabel}
          >
            <i
              className={cn("fa-solid", isDark ? "fa-sun" : "fa-moon")}
              aria-hidden="true"
            />
          </button>
          <button
            type="button"
            className={iconButtonClass({ variant: "ghost" })}
            onClick={handleOpenQr}
            aria-label={
              t("qr.share_button") || "Показать QR-код текущей страницы"
            }
            title={t("qr.share_button") || "Показать QR-код текущей страницы"}
          >
            <i className="fa-solid fa-qrcode" aria-hidden="true" />
          </button>
        </div>
        <div className="flex items-center gap-3">
          <Clock />
          <div id="regos-login" className="hidden md:block" />
        </div>
      </header>
      <main className="mx-auto mt-6 w-full max-w-5xl px-4 pb-32 sm:px-6">
        <div className={cardClass("min-h-[60vh]")}>
          <Outlet />
        </div>
      </main>
      {installDismissed ? null : (
        <InstallButton
          label={installLabel}
          title={installLabel}
          message={installHint}
          variant="floating"
          dismissLabel={closeLabel}
          onDismiss={() => setInstallDismissed(true)}
        />
      )}
      {qrOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6"
          role="presentation"
          onClick={handleCloseQr}
        >
          <div
            className={cardClass(
              "relative w-full max-w-sm space-y-5 p-6 shadow-xl"
            )}
            role="dialog"
            aria-modal="true"
            aria-labelledby="qr-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <h2
                id="qr-modal-title"
                className="text-lg font-semibold text-slate-900 dark:text-slate-50"
              >
                {t("qr.share_title") || "Сканируйте на другом устройстве"}
              </h2>
              <button
                type="button"
                className={iconButtonClass({ variant: "ghost" })}
                onClick={handleCloseQr}
                aria-label={closeLabel}
                title={closeLabel}
              >
                <i className="fa-solid fa-xmark" aria-hidden="true" />
              </button>
            </div>
            <div className="flex min-h-[220px] items-center justify-center overflow-hidden rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 dark:border-slate-600 dark:bg-slate-800">
              {qrGenerating ? (
                <p className={mutedTextClass()}>
                  {t("qr.generating") || "Готовим QR-код..."}
                </p>
              ) : qrError ? (
                <p className="text-sm font-medium text-rose-500">{qrError}</p>
              ) : (
                <img
                  src={qrImage}
                  alt={
                    t("qr.image_alt") ||
                    "QR-код для открытия этой страницы на другом устройстве"
                  }
                  className="h-auto w-full"
                />
              )}
            </div>
            <p
              className={cn(mutedTextClass(), "break-words text-center")}
              aria-live="polite"
            >
              {currentUrl}
            </p>
            <button
              type="button"
              className={cn(
                buttonClass({ variant: "primary", size: "sm", block: true }),
                "justify-center"
              )}
              onClick={handleCopyLink}
              disabled={qrGenerating}
            >
              <i className="fa-solid fa-copy" aria-hidden="true" />
              <span>
                {qrCopied
                  ? t("qr.copied") || "Ссылка скопирована"
                  : t("qr.copy") || "Скопировать ссылку"}
              </span>
            </button>
            <button
              type="button"
              className={cn(
                buttonClass({ variant: "ghost", size: "sm", block: true }),
                "justify-center"
              )}
              onClick={handleCloseQr}
            >
              {closeLabel}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
