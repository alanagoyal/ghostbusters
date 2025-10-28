"use client";

import { useEffect, useState, useMemo } from "react";
import { supabase } from "@/lib/supabase";
import { Users, Shirt, Activity } from "lucide-react";
import { truncateString } from "@/lib/string-utils";
import { StatsCard } from "@/components/dashboard/stats-card";
import { CostumeDistribution } from "@/components/dashboard/costume-distribution";
import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { LiveFeed } from "@/components/dashboard/live-feed";
import { ConfidenceMeter } from "@/components/dashboard/confidence-meter";

interface PersonDetection {
  id: string;
  timestamp: string;
  confidence: number;
  bounding_box: any;
  image_url: string | null;
  device_id: string;
  costume_classification: string | null;
  costume_confidence: number | null;
}

interface DashboardClientProps {
  initialDetections: PersonDetection[];
}

export function DashboardClient({ initialDetections }: DashboardClientProps) {
  const [detections, setDetections] = useState<PersonDetection[]>(initialDetections);

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
    const costumeCounts = new Map<string, number>();
    let totalWithCostume = 0;

    detections.forEach((d) => {
      if (d.costume_classification) {
        const count = costumeCounts.get(d.costume_classification) || 0;
        costumeCounts.set(d.costume_classification, count + 1);
        totalWithCostume++;
      }
    });

    const sorted = Array.from(costumeCounts.entries())
      .map(([name, count]) => ({
        name: truncateString(name, 25),
        count,
        percentage: totalWithCostume > 0 ? (count / totalWithCostume) * 100 : 0,
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
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
            Costume Classifier
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl">
            I hacked my doorbell to detect trick-or-treaters using computer
            vision, classify their costumes with AI, and track the data in
            real-time. The system processes the video feed on a Raspberry Pi 5
            using YOLOv8 to detect people and OpenAI to classify their costumes.
            The results are displayed here.
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
      </div>
    </div>
  );
}
