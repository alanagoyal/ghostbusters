-- Dedicated Ghostbusters Projects database. Apply transactionally.
-- Existing installations must explicitly opt into this private-gallery migration.
set local search_path = public;

create table if not exists public.person_detections (
  id uuid primary key default gen_random_uuid(),
  timestamp timestamptz not null,
  confidence float4 not null,
  bounding_box jsonb not null,
  image_url text,
  device_id text not null,
  costume_classification text,
  costume_description text,
  costume_confidence float4,
  created_at timestamptz default now()
);
alter table public.person_detections
  add column if not exists thumbnail_url text,
  add column if not exists image_width integer,
  add column if not exists image_height integer,
  add column if not exists image_placeholder text;

create index if not exists idx_person_detections_timestamp
  on public.person_detections(timestamp desc);
create index if not exists idx_person_detections_device
  on public.person_detections(device_id);

-- Membership is granted by an operator, never by signup or user_metadata.
create table if not exists public.gallery_viewers (
  user_id uuid primary key references auth.users(id) on delete cascade
);
alter table public.gallery_viewers enable row level security;
alter table public.person_detections enable row level security;

revoke all on public.gallery_viewers from public, anon, authenticated;
grant select on public.gallery_viewers to authenticated;
grant all on public.gallery_viewers to service_role;
revoke all on public.person_detections from public, anon, authenticated;
grant select on public.person_detections to authenticated;
grant select, insert, update, delete on public.person_detections to service_role;
grant usage on schema public to authenticated, service_role;

-- Remove the known policies from the previous public Projects schema.
drop policy if exists "Public Read Access" on public.person_detections;
drop policy if exists "Service Insert Access" on public.person_detections;
drop policy if exists "Service Update Access" on public.person_detections;
drop policy if exists "Ghostbusters membership" on public.gallery_viewers;
create policy "Ghostbusters membership" on public.gallery_viewers
  for select to authenticated using (user_id = (select auth.uid()));
drop policy if exists "Ghostbusters viewer read" on public.person_detections;
create policy "Ghostbusters viewer read" on public.person_detections
  for select to authenticated using (
    exists (select 1 from public.gallery_viewers where user_id = (select auth.uid()))
  );

insert into storage.buckets (id, name, public)
values ('detection-images', 'detection-images', false)
on conflict (id) do update set public = false;
-- These legacy policies were scoped only to detection-images.
drop policy if exists "Public Access" on storage.objects;
drop policy if exists "Service Upload" on storage.objects;
drop policy if exists "Service Delete" on storage.objects;
drop policy if exists "Ghostbusters photo read" on storage.objects;
create policy "Ghostbusters photo read" on storage.objects
  for select to authenticated using (
    bucket_id = 'detection-images' and
    exists (select 1 from public.gallery_viewers where user_id = (select auth.uid()))
  );
-- Service-role access bypasses RLS; no browser upload/write policy is granted.

-- Refuse unknown permissive policies instead of silently claiming privacy.
-- Dedicated projects only: review custom storage policies before migrating.
do $$ begin
  if exists (
    select 1 from pg_policies where
      (schemaname = 'public' and tablename = 'person_detections'
        and policyname <> 'Ghostbusters viewer read') or
      (schemaname = 'public' and tablename = 'gallery_viewers'
        and policyname <> 'Ghostbusters membership') or
      (schemaname = 'storage' and tablename = 'objects'
        and policyname <> 'Ghostbusters photo read')
  ) then
    raise exception 'Unexpected existing policies; review this dedicated project before applying';
  end if;
  if not exists (
    select 1 from pg_publication_tables where pubname = 'supabase_realtime'
      and schemaname = 'public' and tablename = 'person_detections'
  ) then
    alter publication supabase_realtime add table public.person_detections;
  end if;
end $$;
