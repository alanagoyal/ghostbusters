-- Additive only: preserve this installation's existing RLS and bucket visibility.
alter table public.person_detections
  add column if not exists thumbnail_url text,
  add column if not exists image_width integer,
  add column if not exists image_height integer,
  add column if not exists image_placeholder text;
