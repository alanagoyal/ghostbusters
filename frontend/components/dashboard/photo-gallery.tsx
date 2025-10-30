"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Camera, X, ChevronLeft, ChevronRight, Info } from "lucide-react";
import { supabase } from "@/lib/supabase";

interface PersonDetection {
  id: string;
  timestamp: string;
  confidence: number;
  image_url: string | null;
  costume_classification: string | null;
  costume_description: string | null;
  costume_confidence: number | null;
}

export function PhotoGallery() {
  const [detections, setDetections] = useState<PersonDetection[]>([]);
  const [selectedPhoto, setSelectedPhoto] = useState<PersonDetection | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [showInfo, setShowInfo] = useState(true);

  useEffect(() => {
    // Fetch initial detections with images
    const fetchDetections = async () => {
      const { data, error } = await supabase
        .from("person_detections")
        .select("*")
        .not("image_url", "is", null)
        .order("timestamp", { ascending: false })
        .limit(24);

      if (data && !error) {
        setDetections(data);
      }
    };

    fetchDetections();

    // Subscribe to real-time updates
    const channel = supabase
      .channel("photo-gallery-updates")
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "person_detections",
        },
        (payload) => {
          const newDetection = payload.new as PersonDetection;
          if (newDetection.image_url) {
            setDetections((prev) => [newDetection, ...prev].slice(0, 24));
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const handlePhotoClick = (detection: PersonDetection) => {
    setSelectedPhoto(detection);
  };

  const handleClose = () => {
    setSelectedPhoto(null);
  };

  const handleNext = () => {
    if (!selectedPhoto) return;
    const currentIndex = detections.findIndex((d) => d.id === selectedPhoto.id);
    const nextIndex = (currentIndex + 1) % detections.length;
    setSelectedPhoto(detections[nextIndex]);
  };

  const handlePrev = () => {
    if (!selectedPhoto) return;
    const currentIndex = detections.findIndex((d) => d.id === selectedPhoto.id);
    const prevIndex = (currentIndex - 1 + detections.length) % detections.length;
    setSelectedPhoto(detections[prevIndex]);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedPhoto) return;
      if (e.key === "Escape") handleClose();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "ArrowLeft") handlePrev();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedPhoto, detections]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Camera className="h-5 w-5" />
                Photo Gallery
              </CardTitle>
              <CardDescription>
                Interactive gallery of detected visitors
              </CardDescription>
            </div>
            <Badge variant="outline">{detections.length} photos</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {detections.map((detection, index) => (
              <div
                key={detection.id}
                className="relative aspect-[3/4] cursor-pointer group overflow-hidden border border-border"
                onClick={() => handlePhotoClick(detection)}
                onMouseEnter={() => setHoveredId(detection.id)}
                onMouseLeave={() => setHoveredId(null)}
                style={{
                  animation: `slideInFromBottom 0.6s ease-out ${index * 50}ms backwards`,
                }}
              >
                {detection.image_url && (
                  <>
                    <Image
                      src={detection.image_url}
                      alt={detection.costume_classification || "Detection"}
                      fill
                      className="object-cover transition-transform duration-500 group-hover:scale-110"
                      sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, (max-width: 1280px) 25vw, 16vw"
                    />
                    <div
                      className={`absolute inset-0 bg-gradient-to-t from-background/90 via-background/20 to-transparent transition-opacity duration-300 ${
                        hoveredId === detection.id ? "opacity-100" : "opacity-0"
                      }`}
                    >
                      <div className="absolute bottom-0 left-0 right-0 p-2 space-y-1">
                        {detection.costume_classification && (
                          <Badge
                            variant="secondary"
                            className="text-[10px] truncate max-w-full"
                          >
                            {detection.costume_classification}
                          </Badge>
                        )}
                        <div className="text-[10px] text-muted-foreground font-mono">
                          {formatTime(detection.timestamp)}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>

          {detections.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <Camera className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p>No photos captured yet</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Fullscreen Modal */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={handleClose}
          style={{ animation: "fadeIn 0.3s ease-out" }}
        >
          {/* Close Button */}
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 p-2 hover:bg-accent/50 transition-colors border border-border z-10"
            aria-label="Close"
          >
            <X className="h-6 w-6" />
          </button>

          {/* Info Toggle */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowInfo(!showInfo);
            }}
            className="absolute top-4 left-4 p-2 hover:bg-accent/50 transition-colors border border-border z-10"
            aria-label="Toggle info"
          >
            <Info className="h-6 w-6" />
          </button>

          {/* Previous Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handlePrev();
            }}
            className="absolute left-4 top-1/2 -translate-y-1/2 p-2 hover:bg-accent/50 transition-colors border border-border hidden sm:block"
            aria-label="Previous"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>

          {/* Next Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleNext();
            }}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-2 hover:bg-accent/50 transition-colors border border-border hidden sm:block"
            aria-label="Next"
          >
            <ChevronRight className="h-6 w-6" />
          </button>

          {/* Image Container */}
          <div
            className="relative max-w-4xl w-full max-h-[80vh] aspect-[3/4] border border-border"
            onClick={(e) => e.stopPropagation()}
          >
            {selectedPhoto.image_url && (
              <Image
                src={selectedPhoto.image_url}
                alt={selectedPhoto.costume_classification || "Detection"}
                fill
                className="object-contain"
                priority
                sizes="(max-width: 1024px) 100vw, 80vw"
              />
            )}

            {/* Info Overlay */}
            {showInfo && (
              <div
                className="absolute bottom-0 left-0 right-0 bg-background/90 backdrop-blur-sm p-4 border-t border-border space-y-2"
                style={{ animation: "slideInFromBottom 0.3s ease-out" }}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {selectedPhoto.costume_classification && (
                      <Badge variant="secondary">
                        {selectedPhoto.costume_classification}
                      </Badge>
                    )}
                    {selectedPhoto.costume_confidence && (
                      <Badge variant="outline">
                        {(selectedPhoto.costume_confidence * 100).toFixed(1)}%
                        confidence
                      </Badge>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground font-mono">
                    {formatTime(selectedPhoto.timestamp)}
                  </div>
                </div>
                {selectedPhoto.costume_description && (
                  <p className="text-sm text-foreground">
                    {selectedPhoto.costume_description}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Navigation Hint */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs text-muted-foreground font-mono opacity-50">
            Use ← → keys to navigate • ESC to close
          </div>
        </div>
      )}
    </>
  );
}
