"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { supabase } from "@/lib/supabase";
import { applyDetectionChange, type DetectionChange, type PersonDetection } from "@/lib/detections";
import { galleryImages, privateGallery, publicGalleryImages, type SignedImageCache } from "@/lib/gallery-images";

export function useDetections(initialDetections: PersonDetection[]) {
  const raw = useRef(initialDetections);
  const links = useRef<SignedImageCache>(new Map());
  const [detections, setDetections] = useState(initialDetections);
  const [photos, setPhotos] = useState(() => privateGallery ? [] : publicGalleryImages(initialDetections));
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(privateGallery);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    let generation = 0;
    let fetching = false;
    let reconcileAgain = false;
    let pending: DetectionChange[] = [];
    const animations = new Set<ReturnType<typeof setTimeout>>();
    const publish = async () => {
      const ticket = ++generation;
      setDetections(raw.current);
      const resolved = await galleryImages(raw.current, links.current);
      if (active && ticket === generation) {
        setPhotos(resolved);
        setLoading(false);
      }
    };
    const reconcile = async () => {
      if (!active) return;
      if (fetching) { reconcileAgain = true; return; }
      fetching = true;
      pending = [];
      try {
        const { data, error } = await supabase.from("person_detections").select("*")
          .order("timestamp", { ascending: false }).order("id", { ascending: false }).limit(200);
        if (!active) return;
        if (error) {
          if (privateGallery) { links.current.clear(); raw.current = []; await publish(); }
          return;
        }
        // Events received while the query was in flight win over its older snapshot.
        raw.current = pending.reduce(applyDetectionChange, (data || []) as PersonDetection[]);
        await publish();
      } catch {
        if (active && privateGallery) { links.current.clear(); raw.current = []; await publish(); }
      } finally {
        fetching = false;
        if (active) setLoading(false);
        if (active && reconcileAgain) { reconcileAgain = false; void reconcile(); }
      }
    };
    const channel = supabase.channel("dashboard-detections")
      .on<PersonDetection>("postgres_changes", { event: "*", schema: "public", table: "person_detections" }, payload => {
        if (!active) return;
        const change = payload as DetectionChange;
        if (fetching) pending.push(change);
        if (change.eventType === "INSERT" && change.new.id && !raw.current.some(row => row.id === change.new.id)) {
          const id = change.new.id;
          setNewIds(ids => new Set(ids).add(id));
          const timer = setTimeout(() => {
            animations.delete(timer);
            if (active) setNewIds(ids => { const next = new Set(ids); next.delete(id); return next; });
          }, 250);
          animations.add(timer);
        }
        raw.current = applyDetectionChange(raw.current, change);
        void publish();
      })
      .subscribe(status => {
        if (!active) return;
        setConnected(status === "SUBSCRIBED");
        // Close the server-render-to-subscription gap, and reconcile after reconnects.
        if (status === "SUBSCRIBED") void reconcile();
      });
    if (privateGallery) void reconcile();
    const timer = setInterval(() => { void reconcile(); }, 60_000);
    const onVisible = () => { if (document.visibilityState === "visible") void reconcile(); };
    const onOnline = () => { void reconcile(); };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", onOnline);
    return () => {
      active = false;
      generation++;
      clearInterval(timer);
      animations.forEach(clearTimeout);
      links.current.clear();
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", onOnline);
      void supabase.removeChannel(channel);
    };
  }, []);

  const originalImage = useCallback(async (id: string) => {
    const row = raw.current.find(row => row.id === id);
    if (!row) return null;
    // Full-size originals are authorized and downloaded only when opened.
    const [image] = await galleryImages([row], new Map(), { original: true });
    return image.image_url;
  }, []);

  return { detections, photos, connected, loading, newIds, originalImage };
}
