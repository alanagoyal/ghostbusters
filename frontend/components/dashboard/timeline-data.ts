// Noon-to-noon keeps arrivals after midnight at the end of the evening.
// Slots are bounded to a single day, regardless of the years between records.
export function eveningTimeline(detections: Array<{ timestamp: string }>) {
  const counts = new Map<number, Map<number, number>>();
  let first = 95;
  let last = 0;
  for (const detection of detections) {
    const date = new Date(detection.timestamp);
    if (!Number.isFinite(date.getTime())) continue;
    const year = date.getFullYear();
    const slot = Math.floor(((date.getHours() + 12) % 24 * 60 + date.getMinutes()) / 15);
    const series = counts.get(year) ?? new Map<number, number>();
    series.set(slot, (series.get(slot) ?? 0) + 1);
    counts.set(year, series);
    first = Math.min(first, slot);
    last = Math.max(last, slot);
  }
  if (!counts.size) return { slots: [], series: [] };
  first = Math.max(0, first - 1);
  last = Math.min(95, Math.max(last + 1, first + 4));
  const slots = Array.from({ length: last - first + 1 }, (_, i) => {
    const slot = first + i;
    const hour = (Math.floor(slot / 4) + 12) % 24;
    return { slot, label: `${hour % 12 || 12}:${String(slot % 4 * 15).padStart(2, '0')} ${hour >= 12 ? 'PM' : 'AM'}` };
  });
  return { slots, series: [...counts].sort(([a], [b]) => b - a).map(([year, values]) => ({
    year, counts: slots.map(({ slot }) => values.get(slot) ?? 0),
  })) };
}
