import React, {
  createContext,
  useCallback,
  useMemo,
  useState,
  useEffect,
} from "react";
import { toastClass } from "../lib/ui";

const ToastContext = createContext({
  showToast: () => {},
  hideToast: () => {},
});

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const hideToast = useCallback((id) => {
    if (!id) {
      setToasts((prev) => prev.map((toast) => ({ ...toast, dismissed: true })));
      return;
    }
    setToasts((prev) =>
      prev.map((toast) =>
        toast.id === id ? { ...toast, dismissed: true } : toast
      )
    );
  }, []);

  const showToast = useCallback((message, options = {}) => {
    if (!message) return null;
    const { type = "success", duration = 1800 } = options;
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [
      ...prev,
      { id, message, type, duration, dismissed: false },
    ]);
    return id;
  }, []);

  const value = useMemo(
    () => ({ showToast, hideToast }),
    [showToast, hideToast]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-6 left-1/2 z-50 flex w-[min(420px,90vw)] -translate-x-1/2 flex-col items-stretch gap-3">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
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

const TOAST_TRANSITION_DURATION = 220;

function ToastItem({ toast, onRemove }) {
  const { id, message, type, duration, dismissed } = toast;
  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (!dismissed) return undefined;
    setOpen(false);
    const timer = window.setTimeout(
      () => onRemove(id),
      TOAST_TRANSITION_DURATION
    );
    return () => window.clearTimeout(timer);
  }, [dismissed, id, onRemove]);

  useEffect(() => {
    if (dismissed || duration <= 0) return undefined;
    const hideTimer = window.setTimeout(() => setOpen(false), duration);
    const removeTimer = window.setTimeout(
      () => onRemove(id),
      duration + TOAST_TRANSITION_DURATION
    );
    return () => {
      window.clearTimeout(hideTimer);
      window.clearTimeout(removeTimer);
    };
  }, [dismissed, duration, id, onRemove]);

  return (
    <div className={toastClass(open, type)} role="status" aria-live="polite">
      {message}
    </div>
  );
}
