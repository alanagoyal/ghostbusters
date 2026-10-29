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

- Install commit hooks once per clone with
  `uv tool run --from pre-commit==4.3.0 pre-commit install`.
  This installs commit and pre-push hooks; rerun after hook configuration updates.
  Review and re-stage automatic fixes; never bypass hooks. Use a pull request for
  `main` and wait for all required CI checks before merging or reporting success.
- `uv sync --frozen --python 3.11 --extra local` on supported local Macs;
  omit `--extra local` for existing cloud-only platforms.
- `uv run --no-sync python -m unittest discover -s backend/tests/unit -v`
- Frontend: after committing, run `bash scripts/check_frontend.sh` (Node 22).
  This checks committed types, tests, and the static production build exactly as CI
  does, in isolation. Typecheck or a dev preview alone is not sufficient.
- Production local build: `uv run --no-sync ghostbusters local build`.
- Unit tests are offline. Model fixture verification is explicitly separate and uses
  tracked licensed images in `backend/tests/fixtures/local`. Cloud inference is billed;
  cloud integration tests write records. Use disposable resources for new tests.
- Preserve `.env`, `frontend/.env.local`, camera settings,
  existing services and resources. Local lifecycle tracks only its installation.

## Optional Stripe Projects cloud installation

When the user explicitly selects Stripe Projects/cloud, follow
[docs/STRIPE_PROJECTS.md](docs/STRIPE_PROJECTS.md), including its agent runbook.
Provision supported accounts/resources through Stripe Projects and provider CLIs;
ask the owner only for concrete browser approvals, inaccessible secrets, camera
permission/device selection or a budget decision. Use a separate checkout for an
existing install. Keep Stripe's generated credentials in the ignored provisioning
directory; import via `ghostbusters projects configure`, then apply the rerunnable
schema with `ghostbusters projects bootstrap`. Verify model access, uploads and
Realtime separately from provisioning; do not claim live success from unit tests.

New Projects installs use private buckets and explicit `gallery_viewers` access.
Follow [cloud privacy](docs/CLOUD_PRIVACY.md); never relax bucket/RLS access to fix
sign-in. Create owner access with `projects add-viewer`, configure Auth redirects,
and have the owner complete email sign-in. Require explicit model selection and
keep OpenRouter no-data-collection/ZDR routing enabled. NVIDIA free endpoints and
automatic/free routers are blocked for camera footage. Synthetic success does not
establish provider permission to process faces.
