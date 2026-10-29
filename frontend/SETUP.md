# Cloud gallery

For the default private local gallery, use [local setup](../docs/LOCAL_SETUP.md). These instructions apply to Baseten/Supabase and [Stripe Projects](../docs/STRIPE_PROJECTS.md) installations.

From the repository root, `ghostbusters setup --provider baseten` writes `frontend/.env.local`. It contains only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (publishable or legacy anon key). Do not put backend secret keys in frontend settings. Preserve existing values.

```sh
npm --prefix frontend ci
npm --prefix frontend run typecheck
npm --prefix frontend run dev
```

Open `http://localhost:3000/ghostbusters`. For a production Next.js server, use `npm --prefix frontend run build` then `npm --prefix frontend start`. A hosted deployment needs the same two public settings at build time. Do not set `NEXT_PUBLIC_STORAGE_PROVIDER=local` for the cloud build.

The public gallery renders its initial photos on the server. One shared client
subscription applies live row changes to photos, statistics and the feed;
reconnects and minute-long reconciliation repair missed events. New captures
serve prebuilt thumbnails directly from Storage. See [gallery thumbnails](../docs/CLOUD_PRIVACY.md#gallery-thumbnails)
to backfill existing records. Run `npm test` for gallery state and image-access tests.

For legacy Baseten installations, the schema, public SELECT policy and Realtime publication must match [Supabase setup](../docs/SUPABASE_SETUP.md). The gallery is publicly readable by design. Verify real inserts arrive without reloading; a successful page render alone does not verify capture or Realtime.

## Private Stripe Projects gallery

New Projects installations are private by default. Build with
`NEXT_PUBLIC_GALLERY_ACCESS=private` and the project's public URL/key. Use the
[Projects bootstrap and viewer setup](../docs/STRIPE_PROJECTS.md) instead of the
legacy public schema. Set the exact deployed gallery URL in Supabase Auth redirect
configuration. Only listed viewers can sign photo links; browser signup grants no
access. Signed links expire after two minutes and refresh while the page is open.
Set `NEXT_PUBLIC_SOURCE_URL` to the corresponding deployed source for AGPL users.
Never copy backend secrets into a frontend build.
