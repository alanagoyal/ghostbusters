import { supabase } from "@/lib/supabase";

export const privateGallery = process.env.NEXT_PUBLIC_GALLERY_ACCESS === "private";

// Only use object names from this project's bucket. Never fetch arbitrary record URLs.
export function objectPath(value: string): string | null {
  if (!value.includes("://")) return value.startsWith("/") || value.includes("..") ? null : value;
  try {
    const url = new URL(value);
    const base = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL || "");
    const prefix = "/storage/v1/object/public/detection-images/";
    if (url.origin !== base.origin || !url.pathname.startsWith(prefix)) return null;
    return decodeURIComponent(url.pathname.slice(prefix.length));
  } catch { return null; }
}

export async function galleryImages<T extends { image_url: string | null }>(rows: T[]): Promise<T[]> {
  if (!privateGallery) return rows;
  return Promise.all(rows.map(async row => {
    const path = row.image_url ? objectPath(row.image_url) : null;
    if (!path) return { ...row, image_url: null };
    const { data, error } = await supabase.storage.from("detection-images").createSignedUrl(path, 120);
    return { ...row, image_url: error ? null : data?.signedUrl ?? null };
  }));
}
