import React from "react";

export default function NavBackButton({ onClick, label }) {
  if (!onClick) return null;
  return (
    <button
      id="nav-back"
      type="button"
      className="btn icon clear"
      aria-label={label || "Назад"}
      title={label || "Назад"}
      onClick={onClick}
    >
      <i className="fa-solid fa-chevron-left" aria-hidden="true" />
    </button>
  );
}
