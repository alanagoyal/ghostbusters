"""Small, non-interactive adapter for credentials provisioned by provider CLIs."""

import argparse
import base64
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from uuid import UUID

from dotenv import dotenv_values

from backend.scripts.cli import ROOT, public_key, save_env
from backend.src.camera import camera_source, region_of_interest
from backend.src.clients.vision import validate_openrouter_model


class SetupError(ValueError):
    """Messages contain field names and remedies, never credential values."""


def read_env(path):
    if not path.is_file():
        raise SetupError(
            "Input file missing; finish provisioning or private input first"
        )
    return dict(dotenv_values(path, interpolate=False))


def field(values, *names, required=True):
    found = {values[name] for name in names if values.get(name)}
    if len(found) > 1:
        raise SetupError("Conflicting aliases: " + ", ".join(names))
    if not found:
        if required:
            raise SetupError("Missing " + names[0])
        return None
    value = found.pop()
    if any(c in value for c in "\r\n\x00"):
        raise SetupError("Invalid single-line field: " + names[0])
    return value


def backend_key(value):
    if value.startswith("sb_secret_"):
        return True
    try:
        data = value.split(".")[1]
        return (
            json.loads(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).get(
                "role"
            )
            == "service_role"
        )
    except (ValueError, IndexError, UnicodeError):
        return False


def fetch_backend_key(url):
    """Use existing Supabase CLI authorization; never print its key-bearing output."""
    host = urlparse(url).hostname or ""
    if not host.endswith(".supabase.co"):
        raise SetupError("Automatic key retrieval requires the provider project URL")
    result = subprocess.run(
        [
            "supabase",
            "projects",
            "api-keys",
            "--project-ref",
            host.split(".")[0],
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode:
        raise SetupError(
            "Supabase CLI cannot retrieve keys; authorize supabase login "
            "or supply SUPABASE_SECRET_KEY privately"
        )
    try:
        keys = json.loads(result.stdout)
        for item in keys:
            key = item.get("api_key", "")
            if backend_key(key):
                return key
    except (ValueError, TypeError, AttributeError):
        pass
    raise SetupError("No backend key returned; supply SUPABASE_SECRET_KEY privately")


def configure(source, camera_file, model, secrets=None, fetch_keys=False, root=ROOT):
    if source.resolve() in {
        (root / ".env").resolve(),
        (root / "frontend/.env.local").resolve(),
    }:
        raise SetupError("Keep provider credentials in a separate provisioning file")
    values = read_env(source)
    if secrets:
        extra = read_env(secrets)
        for key, value in extra.items():
            if values.get(key) and values[key] != value:
                raise SetupError("Conflicting private input: " + key)
        values.update(extra)
    url = field(
        values, "SUPABASE_PROJECT_URL", "SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"
    ).rstrip("/")
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.query
        or parsed.fragment
        or parsed.path
    ):
        raise SetupError("Supabase URL must be an HTTPS origin")
    public = field(
        values,
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_ANON_KEY",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    )
    if not public_key(public):
        raise SetupError("Browser key must be publishable/anon")
    secret = field(
        values, "SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY", required=False
    )
    if not secret and fetch_keys:
        secret = fetch_backend_key(url)
    if not secret or not backend_key(secret):
        raise SetupError(
            "Missing backend key: use --fetch-supabase-keys "
            "or private SUPABASE_SECRET_KEY input"
        )
    try:
        validate_openrouter_model(model)
    except ValueError as error:
        raise SetupError(str(error)) from None
    camera = read_env(camera_file)
    camera = {
        k: v
        for k, v in camera.items()
        if k
        in {
            "CAMERA_SOURCE",
            "DOORBIRD_IP",
            "DOORBIRD_USERNAME",
            "DOORBIRD_PASSWORD",
            "DEVICE_ID",
            "ROI_X_MIN",
            "ROI_X_MAX",
            "ROI_Y_MIN",
            "ROI_Y_MAX",
        }
        and v is not None
    }
    try:
        camera_source(camera)
        region_of_interest(camera)
    except ValueError:
        raise SetupError(
            "Camera configuration incomplete; discover/select device "
            "and supply private camera input"
        ) from None
    backend = {
        **camera,
        "STORAGE_PROVIDER": "supabase",
        "GALLERY_ACCESS": "private",
        "INFERENCE_PROVIDER": "openrouter",
        "OPENROUTER_API_KEY": field(
            values, "OPENROUTER_API_KEY", "OPENROUTER_API_API_KEY"
        ),
        "OPENROUTER_MODEL": model,
        "NEXT_PUBLIC_SUPABASE_URL": url,
        "SUPABASE_SERVICE_ROLE_KEY": secret,
    }
    frontend = {
        "NEXT_PUBLIC_SUPABASE_URL": url,
        "NEXT_PUBLIC_SUPABASE_ANON_KEY": public,
        "NEXT_PUBLIC_STORAGE_PROVIDER": "supabase",
        "NEXT_PUBLIC_GALLERY_ACCESS": "private",
    }
    targets = [(root / ".env", backend), (root / "frontend/.env.local", frontend)]
    # Validate both before writing either. Never silently migrate an existing install.
    for path, desired in targets:
        old = read_env(path) if path.exists() else {}
        if old.get("BASETEN_API_KEY") or old.get("STORAGE_PROVIDER") == "local":
            raise SetupError(
                "Existing installation: use a separate checkout for Projects"
            )
        if any(old.get(k) not in (None, "", v) for k, v in desired.items()):
            raise SetupError(
                "Existing configuration differs; use a separate checkout "
                "or explicitly reconcile it privately"
            )
    for path, desired in targets:
        save_env(path, desired)
    return {
        "status": "configured",
        "next": "bootstrap, then doctor; capture has not started",
    }


def database_url(values):
    # Provider-returned pooler first: direct Supabase endpoints can require IPv6.
    url = field(values, "SUPABASE_POOLER_URL", required=False) or field(
        values, "SUPABASE_DB_URL"
    )
    if "[YOUR-PASSWORD]" in url:
        url = url.replace(
            "[YOUR-PASSWORD]",
            quote(
                field(values, "DB_PASS", "SUPABASE_DB_PASSWORD", "SUPABASE_DB_PASS"),
                safe="",
            ),
        )
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
        raise SetupError("Expected a provider-returned Postgres connection URI")
    return url


def run_sql(source, sql_file=None, statement=None):
    parsed = urlparse(database_url(read_env(source)))
    env = {
        **os.environ,
        # libpq does not expand a connection URI supplied through PGDATABASE.
        # Pass its components via the environment to keep passwords out of argv.
        "PGHOST": parsed.hostname,
        "PGPORT": str(parsed.port or 5432),
        "PGDATABASE": unquote(parsed.path.lstrip("/")),
        "PGUSER": unquote(parsed.username or "postgres"),
        "PGPASSWORD": unquote(parsed.password or ""),
        "PGSSLMODE": "require",
        "PGCONNECT_TIMEOUT": "15",
    }
    result = subprocess.run(
        [
            "psql",
            "-X",
            "--no-password",
            "--set",
            "ON_ERROR_STOP=1",
            "--single-transaction",
            *(["--file", str(sql_file)] if sql_file else []),
        ],
        input=statement,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode:
        raise SetupError(
            "SQL operation failed; verify returned pooler URL/password "
            "and project readiness. Raw database output suppressed"
        )


def bootstrap(source):
    run_sql(source, ROOT / "backend/migrations/projects_bootstrap.sql")
    return {
        "status": "schema_ready",
        "next": "Create owner Auth user and grant-viewer; run doctor",
    }


def grant_viewer(source, user_id, revoke=False):
    # Only a canonical UUID can enter SQL; no email interpolation or arbitrary SQL.
    uid = str(UUID(user_id))
    statement = (
        f"delete from public.gallery_viewers where user_id = '{uid}';"
        if revoke
        else (
            f"insert into public.gallery_viewers (user_id) values ('{uid}') "
            "on conflict do nothing;"
        )
    )
    run_sql(source, statement=statement)
    return {"status": "viewer_revoked" if revoke else "viewer_granted"}


def add_viewer(email, root=ROOT):
    """Create an email-verifiable Auth account and grant access; sends no email.

    The viewer requests a magic link from the gallery to prove mailbox ownership.
    This operator-only command uses the backend secret; browser signup grants nothing.
    """
    from supabase import create_client

    email = email.strip().lower()
    if "@" not in email or any(c.isspace() for c in email):
        raise SetupError("Provide the intended viewer's email address")
    env = read_env(root / ".env")
    if env.get("GALLERY_ACCESS") != "private":
        raise SetupError("Configure the private gallery first")
    try:
        client = create_client(
            env["NEXT_PUBLIC_SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]
        )
        user = None
        # Bounded pagination, preserving existing users and their credentials.
        for page in range(1, 101):
            users = client.auth.admin.list_users(page=page, per_page=100)
            user = next((u for u in users if (u.email or "").lower() == email), None)
            if user or len(users) < 100:
                break
        else:
            raise SetupError(
                "User directory too large; use grant-viewer with the existing user ID"
            )
        if user is None:
            user = client.auth.admin.create_user(
                {"email": email, "email_confirm": False}
            ).user
        if not user:
            raise SetupError("Could not create viewer account")
        client.table("gallery_viewers").upsert({"user_id": str(user.id)}).execute()
    except SetupError:
        raise
    except Exception:
        raise SetupError(
            "Could not grant viewer access; check backend key, Auth and bootstrap. "
            "Safe to retry"
        ) from None
    return {
        "status": "viewer_granted",
        "next": "Open gallery and request an email sign-in link",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser(
        "configure",
        help="Validate provisioned credentials and write app config; no provisioning",
    )
    setup.add_argument("--source", type=Path, required=True)
    setup.add_argument("--camera-env", type=Path, required=True)
    setup.add_argument("--model", required=True)
    setup.add_argument("--secrets", type=Path)
    setup.add_argument("--fetch-supabase-keys", action="store_true")
    sql = commands.add_parser(
        "bootstrap",
        help="Apply rerunnable schema to the selected dedicated Supabase project",
    )
    sql.add_argument("--source", type=Path, required=True)
    viewer = commands.add_parser(
        "grant-viewer",
        help="Allow an existing Supabase Auth user to view the private gallery",
    )
    viewer.add_argument("--source", type=Path, required=True)
    viewer.add_argument("--user-id", required=True)
    viewer.add_argument("--revoke", action="store_true")
    add = commands.add_parser(
        "add-viewer",
        help="Create/reuse a viewer account and allow access; sends no email",
    )
    add.add_argument("--email", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "configure":
            result = configure(
                args.source,
                args.camera_env,
                args.model,
                args.secrets,
                args.fetch_supabase_keys,
            )
        elif args.command == "add-viewer":
            result = add_viewer(args.email)
        elif args.command == "grant-viewer":
            result = grant_viewer(args.source, args.user_id, args.revoke)
        else:
            result = bootstrap(args.source)
        print(json.dumps(result))
        return 0
    except SetupError as error:
        print(json.dumps({"status": "action_required", "action": str(error)}))
    except (OSError, ValueError, subprocess.SubprocessError):
        print(
            json.dumps(
                {
                    "status": "action_required",
                    "action": "Check input files and required CLI availability; "
                    "provider details suppressed",
                }
            )
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
