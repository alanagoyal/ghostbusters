# Private cloud gallery and model selection

New Stripe Projects installs use a **private** `detection-images` bucket and
private detection records. Only Supabase Auth users in `public.gallery_viewers`
can read them. Signup alone never grants access; browser clients cannot write
photos/events or add viewers. The backend secret stays on the capture computer.

The frontend batch-signs photo links for 120 seconds and reconciles every minute,
reusing links within one mounted viewer until renewal is needed. Link caches are
discarded on sign-out/unmount and are never shared across viewers.
Links are bearer credentials: anyone holding a still-valid link can view that
photo. Revoking membership immediately blocks new database reads and new links;
previously issued links may remain valid until expiry. A viewer can save copies.
The UI clears revoked access on its next membership check (within a minute while
active). Signed links bypass Next.js image optimization to avoid a public cache.
New private variants use zero browser cache TTL so cached responses do not extend
access; public legacy variants use a one-hour TTL.

## Gallery thumbnails

Cloud capture generates a 360-pixel WebP thumbnail from the saved, already
privacy-processed scene, plus a tiny blur placeholder. It uploads the thumbnail
and original before inserting a detection. Immutable `gallery-v1/<digest>/` object
paths identify the exact bytes; retries never replace another image. Gallery
cards request thumbnails directly and request originals only when opened.

The additive migration in `supabase/migrations/*_gallery_thumbnails.sql` adds
nullable thumbnail, dimension and placeholder fields without changing policies
or bucket visibility. Updated private bootstrap and legacy setup SQL include the
same columns. Existing schemas work without this migration: the frontend derives
the thumbnail path from the versioned original path, and the backend omits only
unavailable metadata columns. Blur placeholders and recorded dimensions become
available once the migration is applied.

To upgrade existing records using the configured backend account:

```sh
uv run --no-sync python -m backend.scripts.gallery --dry-run
uv run --no-sync python -m backend.scripts.gallery --limit 200
```

Backfill is bounded and rerunnable. It downloads only this project's bucket
objects into memory, preserves the old objects, and updates a row only if its
image reference has not changed concurrently. Output contains counts, never
photo URLs or image data. It does not invoke a model or write test detections.
When deleting a detection, delete its thumbnail and original along with any
legacy object retained by backfill. Shared scene objects may serve several
person records, so check remaining references before deletion.

## Owner and viewers

After bootstrap, the agent can create/reuse the owner's Auth account and grant
access without sending email:

```sh
uv run --no-sync ghostbusters projects add-viewer --email owner@example.com
```

This command uses the locally configured backend secret. It does not change an
existing account's password or verify mailbox ownership. The viewer opens the
gallery, requests a sign-in link, and clicks the email to prove ownership.
Configure Supabase Auth's Site URL and allowed redirect URLs to the exact gallery
URL (including `/ghostbusters`). Use the authorized Management API/CLI if available,
otherwise the project's **Authentication → URL Configuration** dashboard. Do not
use wildcard production redirects. Supabase's default mail service restricts
recipients/rate; configure your own SMTP service for other viewers if required.

For an existing Auth user, grant or revoke by ID:

```sh
uv run --no-sync ghostbusters projects grant-viewer \
  --source .ghostbusters/provisioning/.env --user-id <auth-user-uuid>
# Add --revoke to remove access. Retain the account and stored photos.
```

## Existing public installations

Existing Baseten and previously configured cloud installations keep their current
behavior. Updating code alone does **not** make their existing bucket private.
For a dedicated Ghostbusters project, stop capture, preserve configuration, apply
`projects bootstrap`, explicitly set backend `GALLERY_ACCESS=private` and frontend
`NEXT_PUBLIC_GALLERY_ACCESS=private`, grant viewers, configure Auth redirects, then
rebuild/redeploy the frontend. The adapter refuses conflicting existing settings;
reconcile those fields deliberately. Legacy public image URLs in records are
converted to object paths for signing only when they match the same project/bucket.

Bootstrap is transactional and repeatable. It removes the known old public
policies and refuses unknown policies rather than silently claiming privacy.
Review custom policies before migrating; do not apply it to a shared database.
Previously public photos may already have been downloaded or cached. Privacy
changes cannot revoke those copies. Verify anonymous reads fail, an unlisted
account sees nothing, and an approved viewer sees a synthetic image and live update
before restarting camera capture. Hosted services paused for testing remain paused
until explicitly resumed.

## Cloud inference

Cloud classification sends an **unblurred person crop** to the selected endpoint.
The saved scene is blurred on a best-effort basis; that is not anonymization.
Local mode avoids the model upload. Review your capture area and provider terms.

The application requires an explicit OpenRouter model and sends
`provider: {data_collection: "deny", zdr: true}` on every OpenRouter request,
including doctor. Routing fails if no eligible endpoint exists; it never retries
with relaxed privacy. These flags express provider routing constraints, not a
blanket legal/privacy guarantee. OpenRouter's policy includes legal/abuse exceptions;
review [ZDR](https://openrouter.ai/docs/guides/features/zdr) and
[data collection](https://openrouter.ai/docs/guides/privacy/data-collection).
Do not enable provider prompt/completion logging or opt into training.

**Do not use NVIDIA free trial endpoints for camera images.** The
[Nemotron free endpoint notice](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free)
prohibits personal data such as faces. The original October 28 walkthrough used
this endpoint before the restriction was identified. Runtime setup now rejects
NVIDIA `:free` models and automatic/free routers. Blocking known unsuitable models
does not certify other models: review the chosen endpoint's terms and image support.

Synthetic checks on October 28, 2026 (no camera images, no new credits purchased):

| Candidate | Result with required privacy routing |
| --- | --- |
| `google/gemini-2.5-flash` | HTTP 404; no usable route in this test |
| `openai/gpt-4.1-mini` | HTTP 402; this account requires credits before inference |

Neither check produced a successful paid classification. Do not claim a verified
replacement model yet. The GPT-4.1 mini catalog quoted $0.40/M input tokens and
$1.60/M output tokens; actual cost depends on image tokenization and routing.
Check the [current catalog](https://openrouter.ai/openai/gpt-4.1-mini), account
credit and terms, get a budget, and verify a synthetic classification first.
Free provider plans are separate from inference credit and provider hosting quotas.

## Retention and deletion

Cloud capture currently has no automatic cloud retention scheduler. Stop capture
when finished; delete both the database row and its corresponding storage object
using the authorized backend/provider tools when no longer needed. Deleting only
a row leaves the object behind. Keep a resource inventory and use it for shutdown;
stopping capture does not pause hosting, cancel billing, or delete cloud data.
