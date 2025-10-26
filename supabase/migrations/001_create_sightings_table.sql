-- Create sightings table for costume detections
-- This table stores each Halloween costume detection with description, confidence, and timestamp

create table if not exists public.sightings (
  id uuid primary key default gen_random_uuid(),
  description text not null,
  confidence numeric check (confidence >= 0 and confidence <= 1),
  timestamp timestamptz default now()
);

-- Create index on timestamp for efficient time-based queries
create index if not exists sightings_timestamp_idx on public.sightings (timestamp desc);

-- Enable Row Level Security
alter table public.sightings enable row level security;

-- RLS Policy: Allow inserts from service role (Pi will use service key)
create policy "Allow service role to insert sightings"
  on public.sightings
  for insert
  to service_role
  with check (true);

-- RLS Policy: Allow authenticated and anon users to read sightings
create policy "Allow public read access to sightings"
  on public.sightings
  for select
  to anon, authenticated
  using (true);

-- Enable Realtime for the sightings table
alter publication supabase_realtime add table public.sightings;

-- Add helpful comment
comment on table public.sightings is 'Stores Halloween costume detections from Raspberry Pi with open-ended descriptions from vision-language model';
