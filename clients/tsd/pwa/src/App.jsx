import React from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/AppLayout.jsx";
import HomePage from "./pages/HomePage.jsx";
import DocsPage from "./pages/DocsPage.jsx";
import DocPage from "./pages/DocPage.jsx";
import OpNewPage from "./pages/OpNewPage.jsx";
import { AppProvider } from "./context/AppContext.jsx";
import { I18nProvider } from "./context/I18nContext.jsx";
import { ToastProvider } from "./context/ToastContext.jsx";

function Router() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/docs" element={<DocsPage />} />
          <Route path="/doc/:id" element={<DocPage />} />
          <Route path="/doc/:id/op/new" element={<OpNewPage />} />
          <Route path="*" element={<Navigate to="/home" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default function App() {
  return (
    <AppProvider>
      <I18nProvider>
        <ToastProvider>
          <Router />
        </ToastProvider>
      </I18nProvider>
    </AppProvider>
  );
}
