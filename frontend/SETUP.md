# Legacy cloud gallery

For the default private local gallery, use [local setup](../docs/LOCAL_SETUP.md). These instructions apply only to existing Baseten/Supabase installations.

From the repository root, `ghostbusters setup --provider baseten` writes `frontend/.env.local`. It contains only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (publishable or legacy anon key). Do not put backend secret keys in frontend settings. Preserve existing values.

```sh
npm --prefix frontend ci
npm --prefix frontend run typecheck
npm --prefix frontend run dev
```

Open `http://localhost:3000/ghostbusters`. For a production Next.js server, use `npm --prefix frontend run build` then `npm --prefix frontend start`. A hosted deployment needs the same two public settings at build time. Do not set `NEXT_PUBLIC_STORAGE_PROVIDER=local` for the cloud build.

The schema, public SELECT policy and Realtime publication must match [Supabase setup](../docs/SUPABASE_SETUP.md). The gallery is publicly readable by design. Verify real inserts arrive without reloading; a successful page render alone does not verify capture or Realtime.
