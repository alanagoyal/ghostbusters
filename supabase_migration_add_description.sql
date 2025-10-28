-- Migration: Add costume_description column to person_detections table
-- Run this in Supabase SQL Editor if you already have the table created
-- This adds the new costume_description field alongside the existing costume_classification

-- ============================================================================
-- Add costume_description column (if it doesn't exist)
-- ============================================================================

-- Add column to store detailed costume descriptions
alter table person_detections
add column if not exists costume_description text;

-- Add comment to explain the field
comment on column person_detections.costume_description is
  'Detailed costume description from vision model (e.g., "witch with purple hat and black dress")';

-- Note: This migration preserves all existing data
-- The costume_description field will be NULL for existing records
-- New detections will populate both costume_classification and costume_description

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Run this to verify the columns exist:
-- select column_name, data_type, is_nullable
-- from information_schema.columns
-- where table_name = 'person_detections'
-- and column_name like 'costume%'
-- order by column_name;

-- Expected output:
-- costume_classification | text | YES
-- costume_confidence     | real | YES
-- costume_description    | text | YES
