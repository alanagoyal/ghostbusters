import { supabase } from "@/lib/supabase";
import { DashboardClient } from "@/components/dashboard/dashboard-client";

export const revalidate = 60; // Revalidate every 60 seconds

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

  return <DashboardClient initialDetections={initialDetections} />;
}
