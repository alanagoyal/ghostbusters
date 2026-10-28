"""Authorization test on a DISPOSABLE Postgres DB named ghostbusters_privacy_test.

Use normal PG* connection variables. Creates Supabase-shaped fixture schemas;
never run this against a real Supabase project. No cloud services or images used.
"""

import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MEMBER = "00000000-0000-0000-0000-000000000001"
STRANGER = "00000000-0000-0000-0000-000000000002"


def query(sql, ok=True):
    result = subprocess.run(
        ["psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1"],
        input=sql,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if ok and result.returncode:
        raise AssertionError(result.stderr)
    if not ok and not result.returncode:
        raise AssertionError("Expected permission failure")
    return result.stdout.strip()


def as_user(role, uid, sql, ok=True):
    return query(f"set role {role}; set request.jwt.claim.sub='{uid}'; {sql}", ok)


class PrivateGallerySQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("PGDATABASE") != "ghostbusters_privacy_test":
            raise RuntimeError(
                "Requires disposable PGDATABASE=ghostbusters_privacy_test"
            )
        query("""
          create role anon nologin;
          create role authenticated nologin;
          create role service_role nologin bypassrls;
          create schema auth;
          create table auth.users (id uuid primary key);
          create function auth.uid() returns uuid language sql stable as
            $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
            $$;
          grant usage on schema auth to anon, authenticated, service_role;
          create schema storage;
          create table storage.buckets (id text primary key, name text, public boolean);
          create table storage.objects
            (id integer primary key, bucket_id text, name text);
          alter table storage.objects enable row level security;
          grant usage on schema storage to anon, authenticated, service_role;
          grant all on storage.objects to anon, authenticated, service_role;
          create publication supabase_realtime;
        """)
        cls.schema = (ROOT / "backend/migrations/projects_bootstrap.sql").read_text()
        query("begin;" + cls.schema + "commit;")
        query("begin;" + cls.schema + "commit;")  # idempotence
        query(f"""
          insert into auth.users values ('{MEMBER}'), ('{STRANGER}');
          insert into public.gallery_viewers values ('{MEMBER}');
          insert into public.person_detections
            (timestamp, confidence, bounding_box, device_id)
            values (now(), 0.9, '{{}}', 'synthetic');
          insert into storage.objects values (1, 'detection-images', 'synthetic.jpg'),
            (2, 'other-bucket', 'unrelated.jpg');
        """)

    def test_anonymous_denied(self):
        as_user("anon", "", "select * from public.person_detections;", False)
        as_user("anon", "", "select * from public.gallery_viewers;", False)
        self.assertEqual(
            as_user("anon", "", "select count(*) from storage.objects;"), "0"
        )
        self.assertEqual(
            query("select public from storage.buckets where id='detection-images';"),
            "f",
        )

    def test_unlisted_authenticated_denied(self):
        for table in (
            "public.person_detections",
            "public.gallery_viewers",
            "storage.objects",
        ):
            self.assertEqual(
                as_user("authenticated", STRANGER, f"select count(*) from {table};"),
                "0",
            )
        as_user(
            "authenticated",
            STRANGER,
            f"insert into public.gallery_viewers values ('{STRANGER}');",
            False,
        )

    def test_viewer_read_only_and_revocation(self):
        for table in (
            "public.person_detections",
            "public.gallery_viewers",
            "storage.objects",
        ):
            self.assertEqual(
                as_user("authenticated", MEMBER, f"select count(*) from {table};"), "1"
            )
        as_user("authenticated", MEMBER, "delete from public.person_detections;", False)
        as_user(
            "authenticated",
            MEMBER,
            "insert into storage.objects values (3,'detection-images','bad.jpg');",
            False,
        )
        # No delete policy: viewer cannot remove a stored photo.
        self.assertEqual(
            as_user(
                "authenticated",
                MEMBER,
                "with d as (delete from storage.objects returning *) "
                "select count(*) from d;",
            ),
            "0",
        )
        query(f"delete from public.gallery_viewers where user_id='{MEMBER}';")
        self.assertEqual(
            as_user("authenticated", MEMBER, "select count(*) from storage.objects;"),
            "0",
        )
        self.assertEqual(
            as_user(
                "authenticated",
                MEMBER,
                "select count(*) from public.person_detections;",
            ),
            "0",
        )
        query(f"insert into public.gallery_viewers values ('{MEMBER}');")

    def test_service_role_write_and_unknown_policy_rollback(self):
        self.assertEqual(
            as_user(
                "service_role", "", "select count(*) from public.person_detections;"
            ),
            "1",
        )
        as_user(
            "service_role",
            "",
            "insert into storage.objects values (4,'detection-images','backend.jpg'); "
            "delete from storage.objects where id=4;",
        )
        query(
            "create policy unexpected on public.person_detections "
            "for select to anon using (true);"
        )
        query("begin;" + self.schema + "commit;", False)
        self.assertEqual(
            query("select count(*) from pg_policies where policyname='unexpected';"),
            "1",
        )
        query("drop policy unexpected on public.person_detections;")


if __name__ == "__main__":
    unittest.main()
