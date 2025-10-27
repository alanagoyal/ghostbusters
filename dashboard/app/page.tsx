"use client";

import { useEffect, useState, useMemo } from "react";
import { supabase } from "@/lib/supabase";
import { Users, Shirt, Activity, TrendingUp } from "lucide-react";
import { truncateString } from "@/lib/string-utils";
import { StatsCard } from "@/components/dashboard/stats-card";
import { CostumeDistribution } from "@/components/dashboard/costume-distribution";
import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { LiveFeed } from "@/components/dashboard/live-feed";
import { ConfidenceMeter } from "@/components/dashboard/confidence-meter";

export const dynamic = "force-dynamic";

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

export default function Dashboard() {
  const [detections, setDetections] = useState<PersonDetection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial detections
  useEffect(() => {
    async function fetchDetections() {
      try {
        const { data, error } = await supabase
          .from("person_detections")
          .select("*")
          .order("timestamp", { ascending: false })
          .limit(200);

        if (error) throw error;
        setDetections(data || []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch detections"
        );
      } finally {
        setLoading(false);
      }
    }

    fetchDetections();
  }, []);

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
        name: truncateString(name, 40),
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

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto pt-20 space-y-6">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">
            Costume Classifier
          </h1>
          <p className="max-w-2xl text-muted-foreground text-sm">
            I hacked my doorbell to detect trick-or-treaters using computer
            vision, classify their costumes with AI, and track the data in
            real-time. The system processes the video feed on a Raspberry Pi 5
            using YOLOv8 to detect people and OpenAI to classify their costumes.
            The results are displayed here.
          </p>
        </div>

        {error && (
          <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-lg">
            Error: {error}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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

        <div className="grid gap-4 md:grid-cols-3">
          <CostumeDistribution costumes={costumeStats.costumes} />
          <LiveFeed detections={detections} limit={8} />
        </div>

        <div className="grid gap-4">
          <ActivityTimeline detections={detections} />
        </div>
      </div>
    </div>
  );
}
