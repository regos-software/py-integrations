import React from "react";
import { iconButtonClass } from "../lib/ui";

export default function NavBackButton({ onClick, label }) {
  if (!onClick) return null;
  return (
    <button
      id="nav-back"
      type="button"
      className={iconButtonClass({ variant: "ghost" })}
      aria-label={label || "Назад"}
      title={label || "Назад"}
      onClick={onClick}
    >
      <i className="fa-solid fa-chevron-left" aria-hidden="true" />
    </button>
  );
}
