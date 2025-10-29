import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import { applyManifestOverrides } from "./manifestOverrides";
import { registerSW } from "./registerSW";

const container = document.getElementById("root");
const root = createRoot(container);

root.render(<App />);
applyManifestOverrides()
  .catch(() => undefined)
  .finally(registerSW);
