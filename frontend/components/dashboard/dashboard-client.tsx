"use client";

import { useEffect, useMemo, useState } from "react";
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

// This year's filter opens with the Halloween 2026 broadcast.
const YEAR_FILTER_OPENS = Date.parse("2026-10-31T15:00:00-07:00");
const UPCOMING_YEAR = 2026;

function useYearFilterOpen() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const wait = YEAR_FILTER_OPENS - Date.now();
    if (wait <= 0) { setOpen(true); return; }
    const timer = setTimeout(() => setOpen(true), wait);
    return () => clearTimeout(timer);
  }, []);
  return open;
}

interface DashboardClientProps {
  initialDetections: PersonDetection[];
}

export function DashboardClient({ initialDetections }: DashboardClientProps) {
  const live = useDetections(initialDetections);
  const { connected: detectorOnline, loading, newIds, originalImage } = live;
  const allDetections = live.detections;
  const allPhotos = live.photos;
  const filterOpen = useYearFilterOpen();
  const [chosenYear, setSelectedYear] = useState<number | null>(null);
  const selectedYear = filterOpen || chosenYear !== UPCOMING_YEAR ? chosenYear : null;
  const years = [...new Set([...allDetections, ...allPhotos].map(row => new Date(row.timestamp).getFullYear()))]
    .filter(Number.isFinite).sort((a, b) => b - a);
  const filterYears = [...new Set([...years, UPCOMING_YEAR])].sort((a, b) => a - b);
  const detections = allDetections.filter(row => selectedYear === null || new Date(row.timestamp).getFullYear() === selectedYear);
  const photos = allPhotos.filter(row => selectedYear === null || new Date(row.timestamp).getFullYear() === selectedYear);

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
      (d) => now >= new Date(d.timestamp).getTime() && now - new Date(d.timestamp).getTime() < oneHour
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
      <GalleryHeader online={detectorOnline} />
      <div className="space-y-8">
        <div id="costume-archive" className="scroll-mt-6">
          <div className="year-filter-row">
            <div className="year-filter" role="group" aria-label="Filter dashboard by year">
              {[null, ...filterYears].map(year => {
                // aria-disabled keeps the button hoverable and focusable so its tooltip shows.
                const locked = !filterOpen && year === UPCOMING_YEAR;
                return <button key={year ?? "all"} type="button" aria-pressed={selectedYear === year}
                  aria-disabled={locked || undefined} title={locked ? "Check back Oct 31, 3pm PT" : undefined}
                  onClick={() => { if (!locked) setSelectedYear(year); }}>
                  {year ?? "All years"}
                </button>;
              })}
            </div>
            {!filterOpen && <span className="year-filter-note">Check back Oct 31, 3pm PT</span>}
          </div>
          <PhotoGallery key={selectedYear ?? "all"} detections={photos} isLoading={loading} newIds={newIds} originalImage={originalImage} />
        </div>

        <div className="summary-strip grid grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Recent Detections"
            value={detections.length}
            description={selectedYear === null ? "Across all years · loaded records" : `${selectedYear} · loaded records`}
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
                  Date.now() >= new Date(d.timestamp).getTime() && Date.now() - new Date(d.timestamp).getTime() < 5 * 60 * 1000
              ).length
            }
            description="Last 5 minutes"
            icon={Activity}
          />
          <ConfidenceMeter detections={detections} />
        </div>

        <div className="analytics-layout">
          <CostumeDistribution costumes={costumeStats.costumes} />
          <ActivityTimeline detections={detections} years={years} />
        </div>
        <LiveFeed detections={detections} limit={8} />
        <About />
      </div>
    </main>
  );
}
