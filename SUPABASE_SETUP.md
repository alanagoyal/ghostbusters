# Supabase Setup Guide

Complete guide to configuring Supabase for the Person Detection MVP.

## Overview

This guide walks through setting up:
- Supabase project creation
- Database schema for person detections
- Storage bucket for detection images
- Row Level Security (RLS) policies
- API configuration for Raspberry Pi integration

## 1. Create Supabase Project

### Sign Up / Login
1. Go to [supabase.com](https://supabase.com)
2. Sign up or login with GitHub
3. Click "New Project"

### Project Configuration
- **Organization**: Create new or select existing
- **Project Name**: `halloween-costume-detector`
- **Database Password**: Generate strong password (save it!)
- **Region**: Choose closest to your location
- **Pricing Plan**: Free tier is sufficient for MVP

### Save Project Credentials
After project creation, navigate to **Project Settings > API**:

- **Project URL**: `https://xxxxxxxxxxxxx.supabase.co` → Use for `NEXT_PUBLIC_SUPABASE_URL`
- **anon/public key**: For frontend dashboard (public) → Use for `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **service_role key**: For Raspberry Pi (private, full access) → Use for `SUPABASE_SERVICE_ROLE_KEY`

**IMPORTANT**: Never commit the `service_role` key to Git!

## 2. Database Schema

### Create Person Detections Table

Navigate to **SQL Editor** and run this SQL:

```sql
-- Create person_detections table
create table person_detections (
  id uuid primary key default gen_random_uuid(),
  timestamp timestamptz not null,
  confidence float4 not null,
  bounding_box jsonb not null,
  image_url text,
  device_id text not null,
  costume_classification text,
  costume_confidence float4,
  created_at timestamptz default now()
);

-- Add indexes for performance
create index idx_person_detections_timestamp
  on person_detections(timestamp desc);

create index idx_person_detections_device
  on person_detections(device_id);

create index idx_person_detections_created_at
  on person_detections(created_at desc);

-- Add comment for documentation
comment on table person_detections is
  'Stores person detection events from YOLOv8 with optional costume classification';
```

### Schema Explanation

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key, auto-generated |
| `timestamp` | timestamptz | When person was detected (from video frame) |
| `confidence` | float4 | YOLO confidence score (0.0-1.0) |
| `bounding_box` | jsonb | Box coordinates: `{x1, y1, x2, y2}` |
| `image_url` | text | URL to image in Supabase Storage |
| `device_id` | text | Raspberry Pi identifier (e.g., "halloween-pi") |
| `costume_classification` | text | Costume description from AI (optional) |
| `costume_confidence` | float4 | AI classification confidence (optional) |
| `created_at` | timestamptz | Database insertion timestamp |

## 3. Storage Bucket

### Create Detection Images Bucket

1. Navigate to **Storage** in Supabase dashboard
2. Click **New Bucket**
3. Configure:
   - **Name**: `detection-images`
   - **Public bucket**: ✅ Yes (for public dashboard)
   - **File size limit**: 5 MB (sufficient for images)
   - **Allowed MIME types**: `image/jpeg`, `image/png`

### Storage Policies

Run this SQL to set up storage policies:

```sql
-- Allow public read access to detection images
create policy "Public Access"
  on storage.objects for select
  using ( bucket_id = 'detection-images' );

-- Allow authenticated/service role to upload
create policy "Service Upload"
  on storage.objects for insert
  with check (
    bucket_id = 'detection-images'
    and (auth.role() = 'service_role' or auth.role() = 'authenticated')
  );

-- Allow authenticated/service role to delete
create policy "Service Delete"
  on storage.objects for delete
  using (
    bucket_id = 'detection-images'
    and (auth.role() = 'service_role' or auth.role() = 'authenticated')
  );
```

### File Naming Convention

Images will be stored as: `{device_id}/{timestamp}.jpg`

Example: `halloween-pi/20241027_183045.jpg`

## 4. Row Level Security (RLS)

### Enable RLS

```sql
-- Enable Row Level Security on person_detections
alter table person_detections enable row level security;
```

### Create RLS Policies

```sql
-- Policy 1: Public read access (for dashboard)
create policy "Public Read Access"
  on person_detections for select
  using ( true );

-- Policy 2: Service role can insert (for Raspberry Pi)
create policy "Service Insert Access"
  on person_detections for insert
  with check ( auth.role() = 'service_role' );

-- Policy 3: Service role can update (for adding costume classification)
create policy "Service Update Access"
  on person_detections for update
  using ( auth.role() = 'service_role' );
```

### Verify RLS Policies

```sql
-- Check enabled policies
select
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
from pg_policies
where tablename = 'person_detections';
```

## 5. Environment Configuration

### Update .env File

Add these variables to your `.env` file on the Raspberry Pi:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
DEVICE_ID=halloween-pi
```

**Security Notes:**
- `NEXT_PUBLIC_*` variables are for frontend (Next.js dashboard)
- `SUPABASE_SERVICE_ROLE_KEY` is for Raspberry Pi backend (full access)
- Keep `.env` file in `.gitignore`
- Never commit real credentials to Git

### .env.example Template

The `.env.example` file includes placeholders:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DEVICE_ID=halloween-pi
```

## 6. Testing Setup

### Test Database Connection

Run this SQL in the SQL Editor:

```sql
-- Insert a test detection
insert into person_detections (
  timestamp,
  confidence,
  bounding_box,
  device_id
) values (
  now(),
  0.95,
  '{"x1": 100, "y1": 150, "x2": 300, "y2": 450}'::jsonb,
  'test-device'
);

-- Query recent detections
select
  id,
  timestamp,
  confidence,
  device_id,
  created_at
from person_detections
order by timestamp desc
limit 10;

-- Clean up test data
delete from person_detections where device_id = 'test-device';
```

### Test Storage Upload

Using the Supabase dashboard:

1. Go to **Storage > detection-images**
2. Click **Upload File**
3. Create folder: `test-device`
4. Upload a test image
5. Verify public URL works: `https://xxxxxxxxxxxxx.supabase.co/storage/v1/object/public/detection-images/test-device/test.jpg`

### Test with Python Client

Create a test script to verify Python integration:

```bash
uv run python test_supabase_connection.py
```

Expected output:
```
✅ Connected to Supabase successfully
✅ Test record inserted: <record_id>
✅ Test record retrieved successfully
✅ Test image uploaded successfully
✅ All tests passed!
```

## 7. Monitoring & Maintenance

### View Recent Detections

```sql
select
  timestamp,
  confidence,
  device_id,
  costume_classification,
  image_url,
  created_at
from person_detections
order by timestamp desc
limit 20;
```

### Check Storage Usage

Navigate to: **Project Settings > Usage**
- Monitor storage usage
- Check API request counts
- Review database size

### Cleanup Old Data (Optional)

For Halloween night, you probably want to keep all data. But for testing:

```sql
-- Delete detections older than 7 days
delete from person_detections
where created_at < now() - interval '7 days';
```

## 8. Production Checklist

Before Halloween night:

- [ ] Supabase project created
- [ ] Database table created with indexes
- [ ] Storage bucket configured
- [ ] RLS policies enabled and tested
- [ ] Environment variables set on Raspberry Pi
- [ ] Test detection successfully stored
- [ ] Test image successfully uploaded
- [ ] Public dashboard can read data
- [ ] Monitor setup (optional: set up Supabase alerts)

## Troubleshooting

### Common Issues

**Problem**: `permission denied for table person_detections`
- **Solution**: Check RLS policies, ensure using `service_role` key

**Problem**: Storage upload fails with 403
- **Solution**: Verify storage policies allow service role to insert

**Problem**: Cannot connect to Supabase
- **Solution**: Check network connectivity, verify SUPABASE_URL is correct

**Problem**: Images not appearing in dashboard
- **Solution**: Verify bucket is public, check image_url format

### Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Storage Documentation](https://supabase.com/docs/guides/storage)

## Next Steps

After completing this setup:

1. Install Python Supabase client: `uv add supabase`
2. Update `detect_people.py` to upload detections
3. Create dashboard to display detections in real-time
4. Integrate Baseten API for costume classification
5. Test end-to-end flow before Halloween

---

**Last Updated**: October 2024
**For**: Halloween Costume Detector MVP
