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

const DASHBOARD_TITLE = "Ghostbusters";

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

  const handleTitleHover = (e: React.MouseEvent<HTMLHeadingElement>) => {
    const target = e.currentTarget;
    target.classList.add('wiggling');
    setTimeout(() => {
      target.classList.remove('wiggling');
    }, 900);
  };

  return (
    <div className="min-h-screen bg-background pt-10 sm:pt-20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 pb-6 space-y-6">
        <div className="mb-8">
          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <h1
              className="text-4xl sm:text-5xl font-bold tracking-tight bg-gradient-to-r from-zinc-100 via-white to-zinc-100 text-zinc-900 px-6 py-6 shadow-lg relative overflow-hidden w-fit title-banner cursor-default"
              style={{
                boxShadow: '0 4px 12px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.5)',
              }}
              onMouseEnter={handleTitleHover}
            >
              <span className="relative z-10">
                {DASHBOARD_TITLE}
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
            <div className="flex flex-col items-start gap-2 sm:items-end">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <div className={`w-3 h-3 rounded-full ${connected ? "bg-green-500 animate-pulse" : "border-2 border-foreground/70"}`}></div>
                  {connected && <div className="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping opacity-75"></div>}
                </div>
                <span className={`text-sm font-medium ${connected ? "text-green-600" : "text-foreground/80"}`}>{connected ? "Connected" : "Offline"}</span>
              </div>
              {!connected && (
                <p className="max-w-64 text-left sm:text-right text-xs leading-relaxed text-foreground/80">
                  Ghostbusters is currently offline.<br />
                  Check back October 31st at 3pm.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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

        <div className="mt-6">
          <PhotoGallery detections={photos} isLoading={loading} newIds={newIds} originalImage={originalImage} />
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
          <About />
        </div>
      </div>
    </div>
  );
}
