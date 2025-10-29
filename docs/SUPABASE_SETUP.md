# Supabase Setup Guide

Complete guide to configuring Supabase for the Person Detection MVP.

## Prerequisites

You already have:
- ✅ Supabase project created (`halloween-pi`)
- ✅ Environment variables configured in `.env`:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `HOSTNAME`

## Setup Steps

### 1. Run Database Migration

1. Go to your Supabase dashboard: https://supabase.com/dashboard/project/halloween-pi
2. Navigate to **SQL Editor** (in left sidebar)
3. Click **New Query**
4. Copy the contents of `supabase_migration.sql` from this repository
5. Paste into the SQL Editor
6. Click **Run** (or press Cmd/Ctrl + Enter)

This migration creates:
- `person_detections` table with proper indexes
- Row Level Security (RLS) policies for public read, service write
- `detection-images` storage bucket (public)
- Storage policies for public read, service upload/delete

### 2. Verify Setup

Run the test suite to verify everything is configured correctly:

```bash
uv run python test_supabase_connection.py
```

Expected output:
```
✅ All environment variables configured
✅ Client initialized successfully
✅ Detection record inserted successfully
✅ Retrieved X recent detections
✅ Image uploaded successfully
✅ Complete workflow successful
✅ All tests passed!
```

### 3. Start Detection System

Once tests pass, run the person detection system:

```bash
uv run python detect_people.py
```

The system will:
- Connect to your DoorBird RTSP stream
- Detect people using YOLOv8
- Save images locally (backup)
- Upload images to Supabase Storage
- Insert detection records to database

## Database Schema

### person_detections Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key, auto-generated |
| `timestamp` | timestamptz | When person was detected (from video) |
| `confidence` | float4 | YOLO confidence score (0.0-1.0) |
| `bounding_box` | jsonb | Box coordinates: `{x1, y1, x2, y2}` |
| `image_url` | text | URL to image in Supabase Storage |
| `device_id` | text | Device identifier (from `HOSTNAME`) |
| `costume_classification` | text | AI costume description (optional) |
| `costume_confidence` | float4 | AI classification confidence (optional) |
| `created_at` | timestamptz | Database insertion timestamp |

### Storage Structure

Images are stored in the `detection-images` bucket with the path:
```
{HOSTNAME}/{timestamp}.jpg

Example: halloween-pi/20241027_183045.jpg
```

Public URL format:
```
https://your-project.supabase.co/storage/v1/object/public/detection-images/{HOSTNAME}/{timestamp}.jpg
```

## Security

### Row Level Security (RLS)

- **Public Read**: Anyone can query detections (for dashboard)
- **Service Write**: Only service role can insert/update records (Raspberry Pi)

### Storage Policies

- **Public Read**: Anyone can view images (for dashboard)
- **Service Upload**: Only service role can upload images (Raspberry Pi)
- **Service Delete**: Only service role can delete images (cleanup)

### Environment Variables

- `NEXT_PUBLIC_*` variables: Safe to expose in frontend (Next.js)
- `SUPABASE_SERVICE_ROLE_KEY`: **NEVER** expose to frontend, only for backend (Raspberry Pi)

## Useful Queries

### View Recent Detections

```sql
select
  timestamp,
  confidence,
  device_id,
  costume_classification,
  image_url
from person_detections
order by timestamp desc
limit 20;
```

### Count Detections by Device

```sql
select
  device_id,
  count(*) as total_detections
from person_detections
group by device_id;
```

### Get Detections from Last Hour

```sql
select *
from person_detections
where timestamp > now() - interval '1 hour'
order by timestamp desc;
```

### Average Confidence Score

```sql
select
  device_id,
  avg(confidence) as avg_confidence,
  count(*) as total
from person_detections
group by device_id;
```

## Monitoring

### Check Database Size

Navigate to: **Settings > Usage** in Supabase dashboard

Monitor:
- Database size
- Storage usage
- API request counts

### Storage Usage

Navigate to: **Storage > detection-images**

You can:
- Browse uploaded images
- Check storage usage
- Manually delete old images if needed

## Troubleshooting

### Test Fails: Permission Denied

**Problem**: `permission denied for table person_detections`

**Solution**:
- Check RLS policies were created
- Verify using `SUPABASE_SERVICE_ROLE_KEY` (not anon key)

### Test Fails: Storage Upload 403

**Problem**: Cannot upload to storage bucket

**Solution**:
- Verify bucket `detection-images` exists and is public
- Check storage policies were created
- Verify using service role key

### Cannot Connect to Supabase

**Problem**: Connection errors

**Solution**:
- Check `NEXT_PUBLIC_SUPABASE_URL` is correct
- Verify network connectivity
- Check Supabase project is not paused

### Images Not Showing in Dashboard

**Problem**: Image URLs work but don't display

**Solution**:
- Verify bucket is public
- Check CORS settings if accessing from web
- Verify image_url format in database

## Next Steps

After setup is complete:

1. ✅ Run `detect_people.py` to start collecting detections
2. Build Next.js dashboard to display detections in real-time
3. Integrate Baseten API for costume classification
4. Update detection records with costume descriptions
5. Test end-to-end flow before Halloween night

## Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Storage Documentation](https://supabase.com/docs/guides/storage)

---

**Last Updated**: October 2024
**For**: Halloween Costume Detector MVP
