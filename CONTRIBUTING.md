# Contributing

Focused fixes and reproducible camera setup reports are welcome. Read [AGENTS.md](AGENTS.md) and [local setup](docs/LOCAL_SETUP.md) first. Open an issue before a large integration.

## Checks

On an Apple Silicon Mac with 16 GB RAM, use Python 3.11:

```sh
uv sync --frozen --python 3.11 --extra local
uv run --no-sync python -m unittest discover -s backend/tests/unit -v
uv run --no-sync ruff check backend/src/local backend/src/camera.py backend/scripts/check_camera.py backend/scripts/cli.py backend/scripts/service_runner.py backend/scripts/projects.py backend/src/clients/vision.py scripts/setup_macos_service.py backend/tests/unit backend/tests/local_e2e.py
npm --prefix frontend ci
npm --prefix frontend run typecheck
npm --prefix frontend run test:privacy
uv run --no-sync ghostbusters local build
```

On Linux CI or a cloud-only installation, omit `--extra local`; unit tests do not need Metal, cameras or downloaded models. On a local installation, retain `--extra local` when syncing and use `--no-sync` when running commands so uv does not remove optional runtime packages.

The [licensed fixture test](backend/tests/fixtures/README.md) exercises real local inference separately. Keep CI offline: no camera credentials, paid inference or database writes. The optional Supabase integration script writes records; use a disposable project.

## Pull requests

Describe the behavior change and verification. For camera support, include model, firmware, OS, transport and whether a real detection was tested. Document failures as well as successes. Redact credentials, addresses, tokens and private footage.

Keep runtime files, model weights and private camera images out of commits. Include source, author, license and modifications for every public fixture. Third-party images retain their own licenses; new contributions use the combined application's AGPL-3.0 license; original MIT notices are retained. See [third-party notices](THIRD_PARTY_NOTICES.md).

The private-gallery SQL test runs against a disposable local PostgreSQL 17 database
named `ghostbusters_privacy_test` using normal `PG*` connection settings. It creates
Supabase-shaped schemas and roles; **never run it against a real project**:
`python3 backend/tests/integration/private_gallery_sql.py -v`. CI supplies a fresh
Postgres service. This verifies database policy semantics, not hosted Auth email,
Storage signing or Realtime transport. Test those separately before a cloud launch.
CI also scans full Git history for secrets; do not suppress a real credential
finding until it has been revoked and its remediation reviewed.
