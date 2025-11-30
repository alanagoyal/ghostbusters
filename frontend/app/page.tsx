import { supabase } from "@/lib/supabase";
import { DashboardClient } from "@/components/dashboard/dashboard-client";

// Cache for 5 minutes, revalidate in background
export const revalidate = 300;

// Preload link component for images
function ImagePreloadLinks({ urls }: { urls: string[] }) {
  return (
    <>
      {urls.map((url) => (
        <link key={url} rel="preload" as="image" href={url} />
      ))}
    </>
  );
}

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

async function getInitialDetections(): Promise<PersonDetection[]> {
  // Skip data fetching during build time
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    return [];
  }

  try {
    const { data, error } = await supabase
      .from("person_detections")
      .select("*")
      .order("timestamp", { ascending: false })
      .limit(200);

    if (error) {
      console.error("Error fetching detections:", error);
      return [];
    }

    return data || [];
  } catch (err) {
    console.error("Error fetching detections:", err);
    return [];
  }
}

export default async function Dashboard() {
  const initialDetections = await getInitialDetections();

  // Get the 5 most recent image URLs for preloading (these will be visible first)
  const preloadUrls = initialDetections
    .filter((d) => d.image_url)
    .slice(0, 5)
    .map((d) => d.image_url as string);

  return (
    <>
      <ImagePreloadLinks urls={preloadUrls} />
      <DashboardClient initialDetections={initialDetections} />
    </>
  );
}
