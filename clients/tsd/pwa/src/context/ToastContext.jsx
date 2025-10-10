import React, { createContext, useCallback, useMemo, useState } from "react";
import { toastClass } from "../lib/ui";

const ToastContext = createContext({
  showToast: () => {},
  hideToast: () => {},
});

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);

  const hideToast = useCallback(() => setToast(null), []);

  const showToast = useCallback((message, options = {}) => {
    if (!message) return;
    const { type = "success", duration = 1800 } = options;
    setToast({ message, type });
    if (duration > 0) {
      window.setTimeout(() => {
        setToast((current) =>
          current && current.message === message ? null : current
        );
      }, duration);
    }
  }, []);

  const value = useMemo(
    () => ({ showToast, hideToast }),
    [showToast, hideToast]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        id="toast"
        className={toastClass(Boolean(toast), toast?.type)}
        role="status"
        aria-live="polite"
      >
        {toast?.message || ""}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
