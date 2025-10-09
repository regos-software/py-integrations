import React, { createContext, useContext, useEffect, useMemo } from "react";
import { CI, api, assetUrl, registerSW } from "../lib/api.js";
import { esc, fmtMoney, fmtNum, toNumber, unixToLocal } from "../lib/utils.js";

const AppContext = createContext(null);

function setAppTitle(text) {
  if (!text) return;
  try {
    document.title = text;
  } catch (err) {
    console.warn("[title] failed to set", err);
  }
}

export function AppProvider({ children }) {
  const value = useMemo(
    () => ({
      ci: CI,
      api,
      assetUrl,
      registerSW,
      fmtMoney,
      fmtNum,
      toNumber,
      unixToLocal,
      esc,
      setAppTitle,
    }),
    []
  );

  useEffect(() => {
    window.__CI__ = CI;
  }, []);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useApp must be used within AppProvider");
  }
  return ctx;
}
