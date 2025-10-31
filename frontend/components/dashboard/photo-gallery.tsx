"use client";

import { useState, useEffect, useRef } from "react";
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
import { supabase } from "@/lib/supabase";
import { toTitleCase } from "@/lib/string-utils";

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
  const scrollContainerRef = useRef<HTMLDivElement>(null);

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

  // Auto-scroll to the right (most recent photos) whenever detections update
  useEffect(() => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      // Scroll to the far right
      container.scrollLeft = container.scrollWidth - container.clientWidth;
    }
  }, [detections]);

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
          <Badge variant="outline">{detections.length} photos</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollContainerRef}
          className="overflow-x-auto overflow-y-hidden py-4"
        >
          <div className="flex gap-6 px-2">
            {[...detections].reverse().map((detection, index) => {
              // Alternate slight rotations for polaroid effect
              const rotation = index % 3 === 0 ? -2 : index % 3 === 1 ? 2 : 0;

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
                        />
                      )}
                    </div>
                    {/* Caption area */}
                    <div className="pt-2 flex items-center justify-between gap-2 min-h-[32px]">
                      <div className="text-[10px] text-gray-600 font-mono truncate flex-1">
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

        {detections.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <Camera className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <p>No photos captured yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
