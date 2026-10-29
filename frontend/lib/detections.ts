export interface PersonDetection {
  id: string;
  timestamp: string;
  confidence: number;
  bounding_box: unknown;
  image_url: string | null;
  thumbnail_url?: string | null;
  image_width?: number | null;
  image_height?: number | null;
  image_placeholder?: string | null;
  device_id: string;
  costume_classification: string | null;
  costume_confidence: number | null;
  costume_description: string | null;
}

export interface DetectionChange {
  eventType: "INSERT" | "UPDATE" | "DELETE";
  new: Partial<PersonDetection>;
  old: Partial<PersonDetection>;
}

// Merge partial updates, retain ordering, and bound the shared dashboard snapshot.
export function applyDetectionChange(rows: PersonDetection[], change: DetectionChange): PersonDetection[] {
  const id = change.eventType === "DELETE" ? change.old.id : change.new.id;
  if (!id) return rows;
  if (change.eventType === "DELETE") return rows.filter(row => row.id !== id);
  const previous = rows.find(row => row.id === id);
  const next = { ...previous, ...change.new } as PersonDetection;
  if (!next.timestamp) return rows;
  return [...rows.filter(row => row.id !== id), next]
    .sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp) || b.id.localeCompare(a.id))
    .slice(0, 200);
}
