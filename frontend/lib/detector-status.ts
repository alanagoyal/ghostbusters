export const DETECTOR_STATUS_PATH = "_system/detector-status.json";
export const DETECTOR_TTL_MS = 90_000;

// Missing, invalid, stale and implausibly future timestamps never mean live.
export function detectorIsOnline(value: unknown, now = Date.now()): boolean {
  if (!value || typeof value !== "object") return false;
  const status = value as Record<string, unknown>;
  if (status.running !== true || typeof status.updated_at !== "string") return false;
  const age = now - Date.parse(status.updated_at);
  return Number.isFinite(age) && age >= -5_000 && age < DETECTOR_TTL_MS;
}
