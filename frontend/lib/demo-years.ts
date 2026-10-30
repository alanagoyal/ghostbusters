"use client";

import { useEffect, useState } from "react";

const YEAR_MS = 365 * 24 * 60 * 60 * 1000;

// Development-only preview: `?demo=2026` copies some of last year's records forward a year
// so multi-year layouts can be reviewed before new Halloween data exists.
export function useDemoYears<T extends { id: string; timestamp: string }>(rows: T[]): T[] {
  const [enabled, setEnabled] = useState(false);
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") setEnabled(new URLSearchParams(window.location.search).get("demo") === "2026");
  }, []);
  if (!enabled) return rows;
  const copies = rows.filter(row => parseInt(row.id.slice(-1), 16) % 3 === 0).map(row => ({
    ...row,
    id: "demo-" + row.id,
    timestamp: new Date(Date.parse(row.timestamp) + YEAR_MS).toISOString(),
  }));
  return [...copies, ...rows].sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
}
