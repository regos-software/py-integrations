import React, { useCallback, useEffect, useState } from 'react';
import { isStandalone } from '../lib/api.js';

export default function InstallButton({ label }) {
  const [promptEvent, setPromptEvent] = useState(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (isStandalone()) return undefined;

    const handler = (event) => {
      event.preventDefault();
      setPromptEvent(event);
      setVisible(true);
    };

    const installed = () => {
      setPromptEvent(null);
      setVisible(false);
    };

    window.addEventListener('beforeinstallprompt', handler);
    window.addEventListener('appinstalled', installed);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      window.removeEventListener('appinstalled', installed);
    };
  }, []);

  const handleClick = useCallback(async () => {
    if (!promptEvent) return;
    setVisible(false);
    promptEvent.prompt();
    try {
      await promptEvent.userChoice;
    } finally {
      setPromptEvent(null);
    }
  }, [promptEvent]);

  if (!visible || isStandalone()) {
    return null;
  }

  return (
    <button
      id="btn-install"
      type="button"
      className="btn small"
      onClick={handleClick}
    >
      <i className="fa-solid fa-download" aria-hidden="true" />
      <span id="btn-install-txt">{label || 'Install'}</span>
    </button>
  );
}
