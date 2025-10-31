"use client";

import { useEffect, useState, useMemo } from "react";
import Image from "next/image";
import { supabase } from "@/lib/supabase";
import { Users, Shirt, Activity } from "lucide-react";
import { truncateString, toTitleCase } from "@/lib/string-utils";
import { StatsCard } from "@/components/dashboard/stats-card";
import { CostumeDistribution } from "@/components/dashboard/costume-distribution";
import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { LiveFeed } from "@/components/dashboard/live-feed";
import { ConfidenceMeter } from "@/components/dashboard/confidence-meter";
import { PhotoGallery } from "@/components/dashboard/photo-gallery";

const DASHBOARD_TITLE = "Ghostbusters";
const DASHBOARD_DESCRIPTION =
  "This is a live feed from my front door in Noe Valley that identifies the costumes of trick-or-treaters in real time. The video stream is sent over RTSP to a Raspberry Pi, which runs YOLOv8 to detect people. The frames are then classified for costumes using Baseten, the detections are stored in Supabase using real-time listeners, and this dashboard displays the results as they happen.";

interface PersonDetection {
  id: string;
  timestamp: string;
  confidence: number;
  bounding_box: any;
  image_url: string | null;
  device_id: string;
  costume_classification: string | null;
  costume_confidence: number | null;
  costume_description: string | null;
}

interface DashboardClientProps {
  initialDetections: PersonDetection[];
}

export function DashboardClient({ initialDetections }: DashboardClientProps) {
  const [detections, setDetections] =
    useState<PersonDetection[]>(initialDetections);

  // Subscribe to real-time updates
  useEffect(() => {
    const channel = supabase
      .channel("person_detections")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "person_detections" },
        (payload) => {
          const newDetection = payload.new as PersonDetection;
          setDetections((prev) => [newDetection, ...prev.slice(0, 199)]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  // Calculate costume statistics
  const costumeStats = useMemo(() => {
    const costumeCounts = new Map<
      string,
      { count: number; descriptions: string[] }
    >();
    let totalWithCostume = 0;

    detections.forEach((d) => {
      if (d.costume_classification) {
        const existing = costumeCounts.get(d.costume_classification);
        if (existing) {
          existing.count++;
          if (
            d.costume_description &&
            !existing.descriptions.includes(d.costume_description)
          ) {
            existing.descriptions.push(d.costume_description);
          }
        } else {
          costumeCounts.set(d.costume_classification, {
            count: 1,
            descriptions: d.costume_description ? [d.costume_description] : [],
          });
        }
        totalWithCostume++;
      }
    });

    const sorted = Array.from(costumeCounts.entries())
      .map(([name, data]) => ({
        name: truncateString(toTitleCase(name), 25),
        fullName: name,
        count: data.count,
        descriptions: data.descriptions,
        percentage:
          totalWithCostume > 0 ? (data.count / totalWithCostume) * 100 : 0,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    return { costumes: sorted, uniqueCostumes: costumeCounts.size };
  }, [detections]);

  // Calculate activity trend (last hour vs previous hour)
  const activityTrend = useMemo(() => {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;
    const lastHour = detections.filter(
      (d) => now - new Date(d.timestamp).getTime() < oneHour
    ).length;
    const prevHour = detections.filter((d) => {
      const time = now - new Date(d.timestamp).getTime();
      return time >= oneHour && time < oneHour * 2;
    }).length;

    if (prevHour === 0) return 0;
    return ((lastHour - prevHour) / prevHour) * 100;
  }, [detections]);

  return (
    <div className="min-h-screen bg-background pt-10 sm:pt-20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 pb-6 space-y-6">
        <div className="space-y-3 sm:space-y-4">
          <div className="flex items-center justify-between gap-4">
            <h1
              className="text-4xl sm:text-5xl font-bold tracking-tight bg-gradient-to-r from-zinc-100 via-white to-zinc-100 text-zinc-900 px-10 py-5 shadow-lg relative overflow-hidden max-w-xl"
              style={{
                transform: 'rotate(-2deg)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.5)',
              }}
            >
              <span className="relative z-10 flex items-center gap-3">
                <Image
                  src="/detective-icon.png"
                  alt="Detective"
                  width={48}
                  height={48}
                  className="w-10 h-10 sm:w-12 sm:h-12"
                />
                <span>Ghost<span className="italic">busters</span></span>
              </span>
              {/* Gauze texture overlay */}
              <div
                className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage: `repeating-linear-gradient(
                    90deg,
                    transparent,
                    transparent 2px,
                    rgba(0,0,0,0.05) 2px,
                    rgba(0,0,0,0.05) 4px
                  ),
                  repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 2px,
                    rgba(0,0,0,0.05) 2px,
                    rgba(0,0,0,0.05) 4px
                  )`
                }}
              />
              {/* Torn edges effect */}
              <div
                className="absolute left-0 top-0 bottom-0 w-1 bg-zinc-200"
                style={{
                  clipPath: 'polygon(0 0, 100% 5%, 100% 15%, 0 10%, 0 20%, 100% 25%, 100% 35%, 0 30%, 0 40%, 100% 45%, 100% 55%, 0 50%, 0 60%, 100% 65%, 100% 75%, 0 70%, 0 80%, 100% 85%, 100% 95%, 0 90%, 0 100%)'
                }}
              />
              <div
                className="absolute right-0 top-0 bottom-0 w-1 bg-zinc-200"
                style={{
                  clipPath: 'polygon(0 5%, 100% 0, 100% 10%, 0 15%, 0 25%, 100% 20%, 100% 30%, 0 35%, 0 45%, 100% 40%, 100% 50%, 0 55%, 0 65%, 100% 60%, 100% 70%, 0 75%, 0 85%, 100% 80%, 100% 90%, 0 95%, 0 100%, 100% 100%)'
                }}
              />
            </h1>
            <div className="flex items-center gap-2">
              <div className="relative">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <div className="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping opacity-75"></div>
              </div>
              <span className="text-sm font-medium text-green-600">LIVE</span>
            </div>
          </div>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl">
            {DASHBOARD_DESCRIPTION}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Total Visitors"
            value={detections.length}
            description="All-time trick-or-treaters"
            icon={Users}
            trend={{
              value: activityTrend,
              label: "from last hour",
            }}
          />
          <StatsCard
            title="Unique Costumes"
            value={costumeStats.uniqueCostumes}
            description="Different costume types"
            icon={Shirt}
          />
          <StatsCard
            title="Active Now"
            value={
              detections.filter(
                (d) =>
                  Date.now() - new Date(d.timestamp).getTime() < 5 * 60 * 1000
              ).length
            }
            description="Last 5 minutes"
            icon={Activity}
          />
          <ConfidenceMeter detections={detections} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <CostumeDistribution costumes={costumeStats.costumes} />
          </div>
          <div className="lg:col-span-1">
            <LiveFeed detections={detections} limit={8} />
          </div>
        </div>

        <div className="mt-6">
          <ActivityTimeline detections={detections} />
        </div>

        <div className="mt-6">
          <PhotoGallery />
        </div>
      </div>
    </div>
  );
}
