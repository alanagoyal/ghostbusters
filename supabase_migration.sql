-- Halloween Person Detection Database Migration
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/halloween-pi/sql

-- ============================================================================
-- 1. Create person_detections table
-- ============================================================================

create table if not exists person_detections (
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

comment on table person_detections is
  'Stores person detection events from YOLOv8 with optional costume classification';

-- ============================================================================
-- 2. Create indexes for performance
-- ============================================================================

create index if not exists idx_person_detections_timestamp
  on person_detections(timestamp desc);

create index if not exists idx_person_detections_device
  on person_detections(device_id);

create index if not exists idx_person_detections_created_at
  on person_detections(created_at desc);

-- ============================================================================
-- 3. Enable Row Level Security (RLS)
-- ============================================================================

alter table person_detections enable row level security;

-- ============================================================================
-- 4. Create RLS Policies
-- ============================================================================

-- Allow public read access (for dashboard)
create policy "Public Read Access"
  on person_detections for select
  using ( true );

-- Allow service role to insert (for Raspberry Pi)
create policy "Service Insert Access"
  on person_detections for insert
  with check ( auth.role() = 'service_role' );

-- Allow service role to update (for adding costume classification later)
create policy "Service Update Access"
  on person_detections for update
  using ( auth.role() = 'service_role' );

-- ============================================================================
-- 5. Create storage bucket for detection images
-- ============================================================================

insert into storage.buckets (id, name, public)
values ('detection-images', 'detection-images', true)
on conflict (id) do nothing;

-- ============================================================================
-- 6. Create storage policies
-- ============================================================================

-- Allow public read access to detection images
create policy "Public Access"
  on storage.objects for select
  using ( bucket_id = 'detection-images' );

-- Allow service role to upload images
create policy "Service Upload"
  on storage.objects for insert
  with check (
    bucket_id = 'detection-images'
    and auth.role() = 'service_role'
  );

-- Allow service role to delete images (for cleanup if needed)
create policy "Service Delete"
  on storage.objects for delete
  using (
    bucket_id = 'detection-images'
    and auth.role() = 'service_role'
  );
