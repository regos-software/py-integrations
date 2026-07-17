import React, { useEffect, useState } from "react";

function formatTime(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(
    date.getSeconds()
  )}`;
}

export default function Clock() {
  const [time, setTime] = useState(() => formatTime(new Date()));

  useEffect(() => {
    setTime(formatTime(new Date()));
    const id = window.setInterval(() => setTime(formatTime(new Date())), 1000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <span
      id="now"
      className="font-mono text-sm font-semibold text-slate-600 dark:text-slate-300"
      aria-live="polite"
    >
      {time}
    </span>
  );
}
