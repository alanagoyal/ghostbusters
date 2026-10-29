# Contributing

Focused fixes and reproducible camera setup reports are welcome. Read [AGENTS.md](AGENTS.md) and [local setup](docs/LOCAL_SETUP.md) first. Open an issue before a large integration.

## Checks

Install both Git hooks once per clone (linked worktrees share the hooks).
Rerun this after pulling changes to hook installation settings:

```sh
uv tool run --from pre-commit==4.3.0 pre-commit install
```

Each commit runs Ruff on staged Python files, fixes imports and formats code.
If a hook changes a file, review and stage the changes, then commit again.
Remaining lint errors must be fixed before committing. Existing hooks are retained
by pre-commit's default migration mode. Keep the Ruff hook version aligned with
`uv.lock`. Hooks must be installed again for each new clone; they are not installed
automatically by Git. Do not bypass them with `--no-verify` or `SKIP`.

Each push runs frontend types, tests, and the local static production build using
`bash scripts/check_frontend.sh`, the same command CI runs. It checks the pushed
commit in a temporary directory without changing dev-server output, dependencies,
or local environment files. Run it manually after committing; it checks `HEAD`,
not uncommitted edits. Use Node 22 and npm. The build needs no camera or cloud access.
Dynamic routes must enumerate their exportable pages with `generateStaticParams`;
a working dev preview or passing TypeScript check does not establish exportability.

Bring `main` into existing feature branches to pick up hook/config changes. Hooks
are local safeguards, not a guarantee that every push from every clone is checked.

Pull requests into `main` must pass all three Offline checks jobs: `checks`,
`private-gallery-policies`, and `secret-history`. Local hooks catch Python style
errors early; CI also verifies tests, types, builds, database policies and secrets.

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
