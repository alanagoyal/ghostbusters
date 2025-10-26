# Supabase Directory

This directory contains SQL migrations and configuration for the Halloween Costume Classifier Supabase database.

## Files

- `migrations/001_create_sightings_table.sql` - Creates the sightings table, RLS policies, and enables Realtime
- `seed.sql` - Optional sample data for testing the dashboard UI

## Quick Start

1. **Create Supabase project** named `halloween-pi` at [supabase.com](https://supabase.com)

2. **Run the migration** in SQL Editor:
   - Copy contents of `migrations/001_create_sightings_table.sql`
   - Paste and run in Supabase dashboard → SQL Editor

3. **Get API credentials** from Settings → API:
   - Copy `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
   - Add to `.env` file in project root

4. **Test the setup**:
   ```bash
   uv run python supabase_client.py
   ```

See [SUPABASE_SETUP.md](../SUPABASE_SETUP.md) for detailed instructions.

## Database Schema

```sql
create table sightings (
  id uuid primary key default gen_random_uuid(),
  description text not null,
  confidence numeric check (confidence >= 0 and confidence <= 1),
  timestamp timestamptz default now()
);
```

## Security

- **Service key** (for Pi): Write access to log detections
- **Anon key** (for Next.js): Read-only access for dashboard
- **RLS enabled**: Automatic access control via policies

## Realtime

The `sightings` table is configured for Realtime updates, allowing the Next.js dashboard to receive live notifications when new costumes are detected.
