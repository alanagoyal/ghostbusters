# Existing Supabase installations

New clones use local SQLite and images; no Supabase account is needed. These instructions support the optional [Baseten/cloud path](CLI.md), whose detections and images are public.

1. Create or choose the intended Supabase project. Run `uv run --no-sync ghostbusters setup --provider baseten` to write backend and frontend settings without replacing unrelated configuration.
2. For a **fresh project**, run [supabase_migration.sql](../backend/migrations/supabase_migration.sql) in its SQL Editor. It creates `person_detections`, indexes, RLS policies, Realtime membership and the public `detection-images` bucket. It is not a general rerunnable migration: existing policies or publication membership can cause errors. Do not blindly rerun it on an existing database.
3. Apply these explicit table grants with RLS still enabled:

```sql
grant usage on schema public to anon, authenticated, service_role;
grant select on public.person_detections to anon, authenticated;
grant select, insert, update, delete on public.person_detections to service_role;
```

Ensure `public` is exposed through the Data API. RLS policies and table grants are separate controls; see [Supabase API security](https://supabase.com/docs/guides/api/securing-your-api).

The backend uses `SUPABASE_SERVICE_ROLE_KEY` (also accepts a modern secret key) and `NEXT_PUBLIC_SUPABASE_URL`. The frontend gets only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (publishable or legacy anon key). Never expose a backend key through `NEXT_PUBLIC_*`.

Run `uv run --no-sync ghostbusters doctor --skip-camera` for read checks and a small billed Baseten request. Confirm actual browser updates with a walkthrough before relying on the installation.

The cloud path has no automatic cloud retention policy. Stop capture after use and manage retained records/images explicitly. See [frontend setup](../frontend/SETUP.md).

For the dashboard running light, also apply
[`detector_heartbeat.sql`](../supabase/migrations/20261029020000_detector_heartbeat.sql).
This adds a service-only heartbeat writer and a public aggregate running boolean;
it does not change gallery access policies.
