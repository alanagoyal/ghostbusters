// Public display text, fixed at build time. These values do not configure detection.
export const galleryCopy = {
  subtitle: process.env.NEXT_PUBLIC_GALLERY_SUBTITLE || "A live feed of trick-or-treaters’ costumes.",
  offlineMessage: process.env.NEXT_PUBLIC_GALLERY_OFFLINE_MESSAGE || "",
  steps: [
    ["Capture", process.env.NEXT_PUBLIC_GALLERY_CAPTURE_TEXT || "A compatible camera streams video to a computer on the same network."],
    ["Detect", process.env.NEXT_PUBLIC_GALLERY_DETECT_TEXT || "YOLO finds people and candidate costumes in sampled frames."],
    ["Filter", process.env.NEXT_PUBLIC_GALLERY_FILTER_TEXT || "The capture settings control confidence, the detection region and the delay between photos."],
    ["Classify", process.env.NEXT_PUBLIC_GALLERY_CLASSIFY_TEXT || "The configured vision model receives a crop and returns a costume guess, confidence and description."],
    ["Publish", process.env.NEXT_PUBLIC_GALLERY_PUBLISH_TEXT || "Detected person regions are blurred before cloud photos are saved to Supabase. Live updates add new records to this page."],
  ],
};
