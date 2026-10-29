"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Camera, X } from "lucide-react";
import type { PersonDetection } from "@/lib/detections";
import type { GalleryImage } from "@/lib/gallery-images";
import { toTitleCase } from "@/lib/string-utils";

interface PhotoGalleryProps {
  detections: GalleryImage<PersonDetection>[];
  isLoading: boolean;
  newIds: Set<string>;
  originalImage: (id: string) => Promise<string | null>;
}

export function PhotoGallery({ detections, isLoading, newIds, originalImage }: PhotoGalleryProps) {
  const [filter, setFilter] = useState("");
  const allPhotos = detections.filter(detection => detection.image_url);
  const photos = allPhotos.filter(detection =>
    `${detection.costume_classification || ""} ${detection.costume_description || ""}`.toLowerCase().includes(filter.toLowerCase())
  );
  const [selected, setSelected] = useState<PersonDetection | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const request = useRef(0);
  const scrollContainer = useRef<HTMLDivElement>(null);
  const followNewest = useRef(true);
  const newestId = photos[0]?.id;

  useEffect(() => {
    if (followNewest.current && scrollContainer.current) scrollContainer.current.scrollLeft = 0;
  }, [newestId]);

  useEffect(() => {
    if (selected) dialog.current?.showModal();
    else { dialog.current?.close(); request.current++; setPreview(null); }
  }, [selected]);

  useEffect(() => {
    if (selected && !photos.some(photo => photo.id === selected.id)) setSelected(null);
  }, [photos, selected]);

  useEffect(() => () => { request.current++; }, []);

  const openPhoto = async (photo: PersonDetection) => {
    const ticket = ++request.current;
    setPreview(null);
    setPreviewLoading(true);
    setSelected(photo);
    try {
      const url = await originalImage(photo.id);
      if (request.current === ticket) setPreview(url);
    } catch {
      if (request.current === ticket) setPreview(null);
    } finally {
      if (request.current === ticket) setPreviewLoading(false);
    }
  };

  return (
    <>
      <Card className="archive-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Photo Gallery</CardTitle>
              <CardDescription>Recent photos · select to enlarge</CardDescription>
            </div>
            <Badge variant="outline" className="text-muted-foreground">{photos.length} photos</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <label className="archive-search">
            <span>Search costumes</span>
            <input type="search" value={filter} onChange={event => setFilter(event.target.value)} placeholder="Search costumes…" />
          </label>
          {/* RTL scroll origin puts the newest photos on screen before hydration. */}
          <div ref={scrollContainer} dir="rtl"
            onScroll={event => { followNewest.current = Math.abs(event.currentTarget.scrollLeft) < 80; }}
            className={"overflow-x-auto overflow-y-hidden py-4 " + (photos.length ? "min-h-[280px]" : "")}>
            <div dir="ltr" className="flex w-max min-w-full justify-end gap-4">
              {[...photos].reverse().map((detection, index) => {

                const recent = index >= photos.length - 8;
                const placeholder = detection.image_placeholder;
                const blur = placeholder && placeholder.length <= 2048 && /^data:image\/webp;base64,[A-Za-z0-9+/=]+$/.test(placeholder) ? placeholder : undefined;
                return (
                  <div key={detection.id}
                    className={"flex-shrink-0 group " + (newIds.has(detection.id) ? "motion-safe:animate-[slideInFromBottom_200ms_ease-out]" : "")}>
                    <div className="archive-photo"
                      style={{ width: "200px" }}>
                      <button type="button" onClick={() => { void openPhoto(detection); }}
                        aria-label={"Open " + (detection.costume_classification || "detection") + " photo"}
                        className="block w-full relative aspect-[3/4] overflow-hidden bg-gray-100 cursor-zoom-in focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-current">
                        <Image src={detection.image_url!}
                          unoptimized={detection.image_unoptimized}
                          loading={recent ? "eager" : "lazy"}
                          fetchPriority={detection.id === newestId ? "high" : "auto"}
                          placeholder={blur ? "blur" : "empty"} blurDataURL={blur}
                          referrerPolicy="no-referrer"
                          alt={detection.costume_classification || "Detection"}
                          fill className="object-cover transition-transform duration-500 group-hover:scale-105" sizes="200px" />
                      </button>
                      <div className="pt-2 flex items-center justify-between gap-2 min-h-[32px]">
                        <div className="text-xs text-foreground truncate flex-1">
                          {detection.costume_classification ? toTitleCase(detection.costume_classification) : ""}
                        </div>
                        <time dateTime={detection.timestamp} suppressHydrationWarning className="text-[10px] text-muted-foreground whitespace-nowrap">
                          {new Date(detection.timestamp).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true })}
                        </time>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          {!isLoading && photos.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <Camera className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>{filter ? "No costumes match your search" : "No photos captured yet"}</p>
            </div>
          )}
        </CardContent>
      </Card>
      <dialog ref={dialog} aria-label="Detection photo" onCancel={() => setSelected(null)} onClose={() => setSelected(null)}
        onClick={event => { if (event.target === event.currentTarget) setSelected(null); }}
        className="m-auto max-w-[95vw] max-h-[95vh] rounded-lg bg-background text-foreground p-4 shadow-xl backdrop:bg-black/75">
        <div className="flex items-center justify-between gap-6 mb-3">
          <p>{selected?.costume_classification ? toTitleCase(selected.costume_classification) : "Detection photo"}</p>
          <button type="button" onClick={() => setSelected(null)} aria-label="Close photo" className="p-2"><X className="h-5 w-5" /></button>
        </div>
        {preview ? <Image src={preview} alt={selected?.costume_classification || "Detection"} width={selected?.image_width || 1344}
          height={selected?.image_height || 768} unoptimized referrerPolicy="no-referrer" className="max-h-[80vh] w-auto object-contain" />
          : <p role="status" className="p-12">{previewLoading ? "Loading photo…" : "Photo unavailable"}</p>}
      </dialog>
    </>
  );
}
