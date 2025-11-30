"use client";

import { useEffect, useRef, useMemo } from "react";
import Image from "next/image";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Camera } from "lucide-react";
import { toTitleCase } from "@/lib/string-utils";

// Simple blur placeholder for loading state
const shimmerPlaceholder = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgwIiBoZWlnaHQ9IjI0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PC9zdmc+";

// Preload images into browser cache
function useImagePreloader(urls: string[]) {
  useEffect(() => {
    urls.forEach((url) => {
      const img = new window.Image();
      img.src = url;
    });
  }, [urls]);
}

interface PersonDetection {
  id: string;
  timestamp: string;
  confidence: number;
  image_url: string | null;
  costume_classification: string | null;
  costume_description: string | null;
  costume_confidence: number | null;
}

interface PhotoGalleryProps {
  initialDetections: PersonDetection[];
}

export function PhotoGallery({ initialDetections }: PhotoGalleryProps) {
  // Filter to only detections with images, using server-provided data
  const detectionsWithImages = useMemo(
    () => initialDetections.filter((d) => d.image_url),
    [initialDetections]
  );
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Preload visible images (last 10) into browser cache immediately
  const imageUrlsToPreload = useMemo(() => {
    return detectionsWithImages
      .slice(0, 10)
      .map((d) => d.image_url)
      .filter((url): url is string => url !== null);
  }, [detectionsWithImages]);

  useImagePreloader(imageUrlsToPreload);

  // Auto-scroll to the right (most recent photos) whenever detections update
  useEffect(() => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      // Scroll to the far right
      container.scrollLeft = container.scrollWidth - container.clientWidth;
    }
  }, [detectionsWithImages]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Photo Gallery</CardTitle>
            <CardDescription>Detected visitors gallery</CardDescription>
          </div>
          <Badge variant="outline">{detectionsWithImages.length} photos</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollContainerRef}
          className="overflow-x-auto overflow-y-hidden py-4 h-[310px]"
        >
          <div className="flex gap-6 px-2">
            {[...detectionsWithImages].reverse().map((detection, index) => {
              // Alternate slight rotations for polaroid effect
              const rotation = index % 3 === 0 ? -2 : index % 3 === 1 ? 2 : 0;
              // Priority load the last 5 images (most recent, shown on the right)
              const totalImages = detectionsWithImages.length;
              const isPriority = index >= totalImages - 5;

              return (
                <div
                  key={detection.id}
                  className="flex-shrink-0 group"
                  style={{
                    animation: `slideInFromBottom 0.6s ease-out ${
                      index * 50
                    }ms backwards`,
                  }}
                >
                  {/* Polaroid frame */}
                  <div
                    className="bg-white p-3 pb-3 shadow-lg transition-all duration-300 hover:shadow-xl hover:-translate-y-1"
                    style={{
                      width: "180px",
                      transform: `rotate(${rotation}deg)`,
                    }}
                  >
                    {/* Photo */}
                    <div className="relative aspect-[3/4] overflow-hidden bg-gray-100">
                      {detection.image_url && (
                        <Image
                          src={detection.image_url}
                          alt={detection.costume_classification || "Detection"}
                          fill
                          className="object-cover transition-transform duration-500 group-hover:scale-110"
                          sizes="180px"
                          priority={isPriority}
                          placeholder="blur"
                          blurDataURL={shimmerPlaceholder}
                          unoptimized
                        />
                      )}
                    </div>
                    {/* Caption area */}
                    <div className="pt-2 flex items-center justify-between gap-2 min-h-[32px]">
                      <div className="text-xs font-bold text-gray-600 font-mono truncate flex-1">
                        {detection.costume_classification ? toTitleCase(detection.costume_classification) : ""}
                      </div>
                      <div className="text-[10px] text-gray-500 font-mono whitespace-nowrap">
                        {formatTime(detection.timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {detectionsWithImages.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <Camera className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <p>No photos captured yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
