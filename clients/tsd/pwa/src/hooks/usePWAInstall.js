// src/usePWAInstall.ts
import { useEffect, useMemo, useState } from "react";

export function usePWAInstall() {
  const [deferred, setDeferred] = useState(null);
  const [installed, setInstalled] = useState(false);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(display-mode: standalone)");
    const updateInstalled = () =>
      setInstalled(media.matches || window.navigator.standalone === true);
    updateInstalled();
    const cb = () => updateInstalled();
    media.addEventListener?.("change", cb);
    window.addEventListener("appinstalled", updateInstalled);
    return () => {
      media.removeEventListener?.("change", cb);
      window.removeEventListener("appinstalled", updateInstalled);
    };
  }, []);

  useEffect(() => {
    const onBIP = (e) => {
      // Chromium fires this when the app is installable
      e.preventDefault();
      setDeferred(e);
      setSupported(true);
    };
    window.addEventListener("beforeinstallprompt", onBIP);
    return () => window.removeEventListener("beforeinstallprompt", onBIP);
  }, []);

  const canInstall = useMemo(
    () => !!deferred && !installed,
    [deferred, installed]
  );

  async function promptInstall() {
    if (!deferred) return { outcome: "dismissed" };
    // Must be called in a real user gesture (e.g., onClick)
    await deferred.prompt();
    const choice = await deferred.userChoice;
    // After prompting once, Chromium invalidates the event
    setDeferred(null);
    return choice; // { outcome: 'accepted' | 'dismissed', platform: 'web' }
  }

  return { canInstall, installed, supported, promptInstall };
}
