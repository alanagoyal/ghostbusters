# Dashboard Setup Instructions

## Quick Start

1. **Navigate to the dashboard directory:**
```bash
cd dashboard
```

2. **Add your Supabase credentials:**
   Edit `.env.local` and add your Supabase URL and anon key:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

   You can find these in your Supabase project settings at:
   https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api

3. **Run the development server:**
```bash
npm run dev
```

4. **Open the dashboard:**
   Visit http://localhost:3000 in your browser

## What's Included

- **Real-time detection monitoring:** New detections appear automatically as they're inserted into the database
- **Device tracking:** See which device detected each person
- **Confidence scores:** View detection and costume classification confidence levels
- **Timestamp display:** All detections shown in chronological order

## Testing the Real-time Connection

To verify the real-time updates work:

1. Open the dashboard in your browser
2. Open your Supabase SQL Editor at: https://supabase.com/dashboard/project/YOUR_PROJECT/sql/new
3. Insert a test detection:
```sql
INSERT INTO person_detections (
  timestamp,
  confidence,
  bounding_box,
  device_id,
  image_url
) VALUES (
  NOW(),
  0.95,
  '{"x": 100, "y": 100, "width": 200, "height": 300}'::jsonb,
  'test-device',
  'https://example.com/test.jpg'
);
```
4. The new detection should appear in the dashboard immediately!

## Troubleshooting

**Issue:** Dashboard shows "Loading detections..." forever
- Check that your Supabase credentials in `.env.local` are correct
- Verify your Supabase project is active
- Open browser console (F12) to see any error messages

**Issue:** Real-time updates don't work
- Ensure Realtime is enabled for the `person_detections` table in Supabase
- Go to: Database > Replication > Enable replication for `person_detections`
- Check browser console for connection errors

**Issue:** "Failed to fetch detections" error
- Verify your Supabase anon key has permission to read from `person_detections`
- Check Row Level Security (RLS) policies on the table

## Next Steps

- Add image display for detections
- Implement filtering by device or date range
- Add charts and analytics
- Deploy to production (Vercel, Netlify, etc.)
