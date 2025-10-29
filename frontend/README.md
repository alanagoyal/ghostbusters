# Person Detection Dashboard

A Next.js dashboard with real-time Supabase integration for monitoring person detections.

## Features

- Real-time updates using Supabase subscriptions
- Displays person detection data from your detection system
- Shows confidence scores, timestamps, device IDs, and costume classifications
- Clean, responsive UI with Tailwind CSS

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
   - Copy `.env.example` to `.env.local`
   - Add your Supabase URL and anon key:
```
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Database Schema

The app expects a `person_detections` table with the following columns:
- `id` (uuid)
- `timestamp` (timestamptz)
- `confidence` (float4)
- `bounding_box` (jsonb)
- `image_url` (text)
- `device_id` (text)
- `costume_classification` (text, nullable)
- `costume_confidence` (float4, nullable)

## Testing Real-time Updates

To test the real-time functionality:

1. Open the dashboard in your browser
2. Insert a new row into the `person_detections` table in Supabase
3. The new detection should appear immediately in the dashboard

## Building for Production

```bash
npm run build
npm start
```
