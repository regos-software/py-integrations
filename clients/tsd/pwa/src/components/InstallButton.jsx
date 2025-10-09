import { usePWAInstall } from "../hooks/usePWAInstall.js";

export default function InstallButton({ label }) {
  const { canInstall, installed, supported, promptInstall } = usePWAInstall();

  if (installed) return null; // already installed
  if (!supported && !canInstall) return null; // no prompt available yet

  const handleClick = async () => {
    const { outcome } = await promptInstall();
    console.log("[pwa] user choice:", outcome);
  };

  return (
    <button
      id="btn-install"
      type="button"
      className="btn small"
      onClick={handleClick}
    >
      <i className="fa-solid fa-download" aria-hidden="true" />
      <span id="btn-install-txt">{label || "Install"}</span>
    </button>
  );
}
