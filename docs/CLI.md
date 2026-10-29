# Optional cloud setup and seasonal operation

For agent-provisioned OpenRouter/Supabase and optional Vercel hosting, use
[Stripe Projects setup](STRIPE_PROJECTS.md). Existing Baseten setups remain supported.

New clones default local: follow [LOCAL_SETUP.md](LOCAL_SETUP.md). This page applies
to explicitly selected cloud inference/Supabase installations. Bare `setup` on a
fresh clone uses the local workflow; select a provider explicitly for manual cloud setup.

Run commands from your clone after `uv sync --frozen --python 3.11`.
The CLI supports macOS and Linux. It is currently distributed through the checkout,
not a standalone PyPI installation.

| Command | Behavior |
| --- | --- |
| `uv run --no-sync ghostbusters setup --provider baseten` | Interactive camera, inference, Supabase and dashboard configuration; preserves existing provider, explicitly selects Baseten |
| `uv run --no-sync ghostbusters doctor` | Connection checks; one small billed vision request, no database writes |
| `uv run --no-sync ghostbusters doctor --skip-camera` | Checks cloud/config without opening a camera already in use |
| `uv run --no-sync ghostbusters start` | Starts detector service and enables startup at login (Mac) or boot (Linux) |
| `uv run --no-sync ghostbusters status` | Native service state/PID and log location; does not claim cloud health |
| `uv run --no-sync ghostbusters stop` | Stops service and disables automatic startup |
| `uv run --no-sync ghostbusters start --foreground` | Runs in this terminal; Ctrl+C stops; don't combine with a background service |

## Manual first run

1. Create accounts at [Baseten](https://app.baseten.co) and
   [Supabase](https://supabase.com/dashboard). Create a Supabase project.
2. Run `uv run --no-sync ghostbusters setup --provider baseten` in a terminal. Secret inputs do not echo. Enter keeps existing
   settings/defaults. Ctrl+C cancels before saving. Re-running preserves unrelated
   environment settings and comments. Back up config before changing projects.
3. Run the [Supabase bootstrap](SUPABASE_SETUP.md) and its table grants in SQL Editor. A normal Supabase API key cannot run SQL.
4. Run `doctor`. The selected inference provider receives a generated blank image, not a camera frame.
   Failed checks return exit code 1. Raw SDK errors are suppressed to avoid leaking
   credentials. HTTP failures include a status code: 401/403 usually indicate keys
   or access; 404 may indicate the endpoint or missing schema.
5. Start the dashboard with `cd frontend && npm ci && npm run dev` in another
   terminal. Setup already writes its public config. See [hosting](../frontend/SETUP.md).
6. On Linux install once with `sudo ./setup-service.sh`. On Mac no separate install
   step is needed. Run `start`, then `status`. Check logs if the service exits.
7. Walk in view for several seconds. Confirm a photo and costume label appear at
   `http://localhost:3000/ghostbusters`. This verifies uploads and live delivery,
   which the read-only Supabase doctor checks cannot establish.

## Dashboard running light

Apply `supabase/migrations/20261029020000_detector_heartbeat.sql` once in the
Supabase SQL Editor for existing installs (Projects bootstrap includes it). Deploy
the updated dashboard and use the updated detector checkout. The light is green
only after successful YOLO inference refreshes a heartbeat, including empty scenes.
It polls every 10 seconds and shows gray **Offline** when stopped, unreachable, or
no successful inference has occurred for 45 seconds. A crash or camera failure can
take up to about 55 seconds to appear offline. Missing schema also shows Offline.
Gallery history and its Realtime connection do not affect this indicator.

## Halloween

Run `doctor`, `start`, then do a walk-through before visitors arrive. When finished,
run `stop`. No schedule is created: capture stays stopped until you run `start`.
Mac startup requires user login; it does not bypass FileVault. Keep the computer
powered and network-connected. See [macOS](MACOS_SETUP.md) and [Linux/Pi](DEPLOYMENT.md).

Commands operate on the one native Ghostbusters service per user (Mac) or machine
(Linux). `status`/`stop` do not manage manually launched foreground processes or the
Next.js dashboard. Stop foreground capture with Ctrl+C in its terminal. If moving
checkouts, stop and reinstall the service from the new location.

Stopping capture does not delete gallery history, stop the hosted website, or
cancel cloud resources. Hosted Baseten Model APIs avoid maintaining a dedicated
GPU deployment; any dedicated deployment you create must be managed separately.

## Credentials and settings

Backend credentials live in `.env`; frontend config lives in `frontend/.env.local`.
Both are ignored by Git and written with mode 0600. Only a Supabase publishable or
legacy anon key is accepted for the browser. The backend secret/service-role key
stays on the capture computer. Existing environment variables take precedence over
`.env`, so unset stale shell variables when switching projects.

For compatibility, `SUPABASE_SERVICE_ROLE_KEY` also accepts modern Supabase secret
keys, and `NEXT_PUBLIC_SUPABASE_ANON_KEY` accepts publishable keys. See
[Supabase key types](https://supabase.com/docs/guides/api/api-keys).

Use `.env` to adjust `ROI_*` bounds and advanced model settings. Setup does not
provide a visual ROI editor yet. Camera compatibility still depends on the exact
model/stream; see [camera recipes](CAMERAS.md).
