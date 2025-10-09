import { usePWAInstall } from "../hooks/usePWAInstall.js";

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
      className="btn small"
      onClick={handleClick}
    >
      <i className="fa-solid fa-download" aria-hidden="true" />
      <span id="btn-install-txt">{ctaLabel}</span>
    </button>
  );

  if (variant === "floating") {
    return (
      <div className="install-banner" role="dialog" aria-live="polite">
        <div className="install-banner-body">
          <div className="install-banner-text">
            <strong>{heading}</strong>
            {message ? <p>{message}</p> : null}
          </div>
          {button}
        </div>
        <button
          type="button"
          className="install-banner-close"
          onClick={() => onDismiss?.()}
          aria-label={closeLabel}
          title={closeLabel}
        >
          <i className="fa-solid fa-xmark" aria-hidden="true" />
        </button>
      </div>
    );
  }

  return button;
}
