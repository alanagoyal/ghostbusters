import { supabase } from "@/lib/supabase";

export const privateGallery = process.env.NEXT_PUBLIC_GALLERY_ACCESS === "private";

interface ImageRecord {
  image_url: string | null;
  thumbnail_url?: string | null;
}
export type GalleryImage<T extends ImageRecord> = T & { image_unoptimized: boolean };
export type SignedImageCache = Map<string, { url: string; expiresAt: number }>;
const LINK_TTL = 120;
// The reconciliation timer runs every minute; renew before its next tick.
const REFRESH_MARGIN = 65_000;

// Only use object names from this project's bucket. Never fetch arbitrary record URLs.
export function objectPath(value: string): string | null {
  if (!value.includes("://")) return !value || value.startsWith("/") || value.includes("..") || /[?#\\\x00-\x1f]/.test(value) ? null : value;
  try {
    const url = new URL(value);
    const base = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL || "");
    const prefix = "/storage/v1/object/public/detection-images/";
    if (url.origin !== base.origin || !url.pathname.startsWith(prefix)) return null;
    return objectPath(decodeURIComponent(url.pathname.slice(prefix.length)));
  } catch { return null; }
}

interface ImageOptions { original?: boolean }

function source(row: ImageRecord, options: ImageOptions = {}) {
  const original = row.image_url ? objectPath(row.image_url) : null;
  if (options.original) return { path: original, thumbnail: false };
  // The versioned layout also works with legacy databases before metadata columns exist.
  const inferred = original && /\/gallery-v1\/[a-f0-9]{64}\/original\.jpg$/.test(original)
    ? original.replace(/original\.jpg$/, "thumbnail.webp") : null;
  const thumbnail = row.thumbnail_url ? objectPath(row.thumbnail_url) : inferred;
  return { path: thumbnail || original, thumbnail: !!thumbnail };
}

// Synchronous so public thumbnails are present in the initial server-rendered HTML.
export function publicGalleryImages<T extends ImageRecord>(rows: T[], options: ImageOptions = {}): GalleryImage<T>[] {
  return rows.map(row => {
    const { path, thumbnail } = source(row, options);
    const base = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const url = path && base ? `${new URL(base).origin}/storage/v1/object/public/detection-images/${path.split("/").map(encodeURIComponent).join("/")}` : null;
    return { ...row, image_url: url, image_unoptimized: thumbnail };
  });
}

// The caller owns this cache for one mounted viewer. Never share signed links globally.
export async function galleryImages<T extends ImageRecord>(rows: T[], cache: SignedImageCache = new Map(), options: ImageOptions = {}): Promise<GalleryImage<T>[]> {
  if (!privateGallery) return publicGalleryImages(rows, options);
  const paths = [...new Set(rows.map(row => source(row, options).path).filter((path): path is string => !!path))];
  const now = Date.now();
  const missing = paths.filter(path => (cache.get(path)?.expiresAt ?? 0) - now <= REFRESH_MARGIN);
  for (const path of cache.keys()) if (!paths.includes(path)) cache.delete(path);
  if (missing.length) {
    // One authorization request for the batch, rather than one per photo.
    for (const path of missing) cache.delete(path);
    try {
      const { data, error } = await supabase.storage.from("detection-images").createSignedUrls(missing, LINK_TTL);
      if (!error) for (const item of data || []) {
        if (item.path && missing.includes(item.path) && !item.error && item.signedUrl) {
          cache.set(item.path, { url: item.signedUrl, expiresAt: now + LINK_TTL * 1000 });
        }
      }
    } catch { /* A failed authorization never falls back to a public URL. */ }
  }
  return rows.map(row => {
    const path = source(row, options).path;
    const link = path ? cache.get(path) : undefined;
    return { ...row, image_url: link && link.expiresAt > Date.now() ? link.url : null, image_unoptimized: true };
  });
}
