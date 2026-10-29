"use client";

import { useMemo } from "react";
import type { PersonDetection } from "@/lib/detections";
import { useDetections } from "@/lib/use-detections";
import { Users, Shirt, Activity } from "lucide-react";
import { truncateString, toTitleCase } from "@/lib/string-utils";
import { StatsCard } from "@/components/dashboard/stats-card";
import { CostumeDistribution } from "@/components/dashboard/costume-distribution";
import { ActivityTimeline } from "@/components/dashboard/activity-timeline";
import { LiveFeed } from "@/components/dashboard/live-feed";
import { ConfidenceMeter } from "@/components/dashboard/confidence-meter";
import { PhotoGallery } from "@/components/dashboard/photo-gallery";
import { About } from "@/components/dashboard/about";

import { GalleryHeader } from "./gallery-header";

interface DashboardClientProps {
  initialDetections: PersonDetection[];
}

export function DashboardClient({ initialDetections }: DashboardClientProps) {
  const { detections, photos, connected, loading, newIds, originalImage } = useDetections(initialDetections);

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
    <main className="observatory">
      <GalleryHeader connected={connected} />
      <div className="space-y-8">
        <div id="costume-archive" className="scroll-mt-6">
          <PhotoGallery detections={photos} isLoading={loading} newIds={newIds} originalImage={originalImage} />
        </div>

        <div className="summary-strip grid grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Recent Detections"
            value={detections.length}
            description="Latest 200 records"
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
            title="Recent Activity"
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

        <div className="analytics-layout">
          <CostumeDistribution costumes={costumeStats.costumes} />
          <ActivityTimeline detections={detections} />
        </div>
        <LiveFeed detections={detections} limit={8} />
        <About />
      </div>
    </main>
  );
}
