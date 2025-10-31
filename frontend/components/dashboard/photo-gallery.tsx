"use client";

import { useState, useEffect } from "react";
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
  const [hoveredId, setHoveredId] = useState<string | null>(null);

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
        <div className="overflow-x-auto overflow-y-hidden">
          <div className="flex gap-3 pb-2">
            {detections.map((detection, index) => (
              <div
                key={detection.id}
                className="relative aspect-[3/4] group overflow-hidden border border-border flex-shrink-0"
                style={{
                  width: "180px",
                  animation: `slideInFromBottom 0.6s ease-out ${
                    index * 50
                  }ms backwards`,
                }}
                onMouseEnter={() => setHoveredId(detection.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                {detection.image_url && (
                  <>
                    <Image
                      src={detection.image_url}
                      alt={detection.costume_classification || "Detection"}
                      fill
                      className="object-cover transition-transform duration-500 group-hover:scale-110"
                      sizes="180px"
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
