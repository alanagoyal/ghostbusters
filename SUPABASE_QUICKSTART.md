# Supabase Quick Start Guide

Since you already have Supabase credentials in your `.env`, here's a quick guide to get person detection working with your existing setup.

## Your Existing Environment Variables

You already have these configured:
```bash
NEXT_PUBLIC_SUPABASE_URL=xxx
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
HOSTNAME=xxx  # You already have this too!
```

**No additional environment variables needed!** The code automatically uses your existing `HOSTNAME` variable to identify the device.

## Quick Setup Steps

### 1. Create Database Table (2 minutes)

Go to your Supabase project → **SQL Editor** and run:

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
create index idx_person_detections_timestamp on person_detections(timestamp desc);
create index idx_person_detections_device on person_detections(device_id);
create index idx_person_detections_created_at on person_detections(created_at desc);

-- Enable Row Level Security
alter table person_detections enable row level security;

-- Allow public reads (for dashboard)
create policy "Public Read Access"
  on person_detections for select
  using ( true );

-- Allow service role to insert/update (for Raspberry Pi)
create policy "Service Insert Access"
  on person_detections for insert
  with check ( auth.role() = 'service_role' );

create policy "Service Update Access"
  on person_detections for update
  using ( auth.role() = 'service_role' );
```

### 2. Create Storage Bucket (1 minute)

1. Go to **Storage** in Supabase dashboard
2. Click **New Bucket**
3. Name: `detection-images`
4. **Make it public** ✅
5. Create

Then add storage policies in **SQL Editor**:

```sql
-- Allow public read access to detection images
create policy "Public Access"
  on storage.objects for select
  using ( bucket_id = 'detection-images' );

-- Allow service role to upload
create policy "Service Upload"
  on storage.objects for insert
  with check (
    bucket_id = 'detection-images'
    and auth.role() = 'service_role'
  );
```

### 3. Test the Connection (30 seconds)

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

### 4. Run Person Detection (Ready to go!)

```bash
uv run python detect_people.py
```

You should see:
```
🚀 Starting person detection system...
🤖 Loading YOLOv8n model...
✅ Model loaded!
✅ Connected to Supabase (Device: halloween-pi)
✅ Connected to RTSP stream!
👁️  Watching for people...
```

When a person is detected:
```
👤 Person detected! (#1)
   Saved locally: detection_20241027_183045.jpg
✅ Detection saved to Supabase (ID: xxx-xxx-xxx)
   Image URL: https://your-project.supabase.co/storage/v1/object/public/detection-images/halloween-pi/20241027_183045.jpg
```

## How It Works

The system now:
1. **Detects people** using YOLOv8 on your DoorBird stream
2. **Saves images locally** (backup)
3. **Uploads to Supabase Storage** (for dashboard)
4. **Inserts detection record** to database with:
   - Timestamp
   - Confidence score
   - Bounding box coordinates
   - Image URL
   - Device ID

## Next Steps

After detections are flowing:
1. Build Next.js dashboard to display detections in real-time
2. Add Baseten API integration for costume classification
3. Update records with costume descriptions

## Troubleshooting

**If test fails**: Check that `DEVICE_ID=halloween-pi` is in your `.env`

**If upload fails**: Verify storage bucket is named `detection-images` and is public

**If insert fails**: Check RLS policies are created correctly

**Need more details?** See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for comprehensive guide

## Database Schema Reference

Quick reference for queries:

```sql
-- View recent detections
select timestamp, confidence, device_id, image_url
from person_detections
order by timestamp desc
limit 20;

-- Count detections by device
select device_id, count(*) as total_detections
from person_detections
group by device_id;

-- Get detections from last hour
select *
from person_detections
where timestamp > now() - interval '1 hour'
order by timestamp desc;
```

---

You're all set! The system is ready to detect trick-or-treaters on Halloween night! 🎃
