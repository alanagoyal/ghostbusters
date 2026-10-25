# Working on Ghostbusters

## Setup and operation

New clones are **local-first, account-free**. Follow [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md).
Check hardware before downloads: full local vision currently targets Apple Silicon
macOS with 16 GB RAM and Python 3.11. Do not promise Raspberry Pi/Windows/Linux
local inference, universal doorbell compatibility, or a verified real-person pipeline
without evidence. Owner input should be ordinary camera login/streaming permission
or device choice, never an assumed known IP. Use product discovery/adapters and
structured setup outputs. Keep camera credentials/URLs/frames out of logs and UI.

Preserve existing configuration and running services. Existing Baseten installs stay
on Baseten unless explicitly switched. For existing cloud installs follow
[docs/CLI.md](docs/CLI.md) and the Baseten/Supabase guides.
Never commit credentials, runtime files, models or private camera images.

## Development

- `uv sync --frozen --python 3.11 --extra local` on supported local Macs;
  omit `--extra local` for existing cloud-only platforms.
- `uv run --no-sync python -m unittest discover -s backend/tests/unit -v`
- Frontend: `npm --prefix frontend ci`, `npm --prefix frontend run typecheck`.
- Production local build: `uv run --no-sync ghostbusters local build`.
- Unit tests are offline. Model fixture verification is explicitly separate and uses
  tracked licensed images in `backend/tests/fixtures/local`. Cloud inference is billed;
  cloud integration tests write records. Use disposable resources for new tests.
- Preserve `.env`, `frontend/.env.local`, camera settings,
  existing services and resources. Local lifecycle tracks only its installation.
