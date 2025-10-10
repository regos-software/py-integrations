import { usePWAInstall } from "../hooks/usePWAInstall.js";
import {
  buttonClass,
  cardClass,
  iconButtonClass,
  mutedTextClass,
} from "../lib/ui";
import { cn } from "../lib/utils";

export default function InstallButton({
  label,
  title,
  message,
  variant = "inline",
  onDismiss,
  dismissLabel,
}) {
  const { canInstall, installed, supported, promptInstall } = usePWAInstall();

  if (installed) return null; // already installed
  if (!supported && !canInstall) return null; // no prompt available yet

  const handleClick = async () => {
    const { outcome } = await promptInstall();
    console.log("[pwa] user choice:", outcome);
  };

  const ctaLabel = label || "Install";
  const heading = title || ctaLabel;
  const closeLabel = dismissLabel || "Close";

  const button = (
    <button
      id="btn-install"
      type="button"
      className={buttonClass({ variant: "primary", size: "sm" })}
      onClick={handleClick}
    >
      <i className="fa-solid fa-download" aria-hidden="true" />
      <span id="btn-install-txt">{ctaLabel}</span>
    </button>
  );

  if (variant === "floating") {
    return (
      <div
        className={cardClass(
          "fixed bottom-6 left-1/2 z-40 w-[min(520px,calc(100vw-32px))] -translate-x-1/2 space-y-4 shadow-xl"
        )}
        role="dialog"
        aria-live="polite"
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:gap-6">
          <div className="flex-1 space-y-1">
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              {heading}
            </p>
            {message ? (
              <p className={cn(mutedTextClass(), "leading-relaxed")}>
                {message}
              </p>
            ) : null}
          </div>
          <div className="flex shrink-0 items-center gap-3">
            {button}
            <button
              type="button"
              className={cn(
                iconButtonClass({ variant: "ghost" }),
                "text-slate-500 dark:text-slate-300"
              )}
              onClick={() => onDismiss?.()}
              aria-label={closeLabel}
              title={closeLabel}
            >
              <i className="fa-solid fa-xmark" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return button;
}
