# Cloud setup with Stripe Projects

Choose this when you want cloud vision and a **private, sign-in-protected** gallery.
The capture computer still stays on at home, on the camera's network. It runs
YOLO; OpenRouter classifies crops, Supabase stores photos/events, and an optional
Vercel deployment serves the dashboard. Stripe Projects provisions services; it
is not the camera host or a Ghostbusters subscription/payment integration.

Local mode remains the account-free default: [local setup](LOCAL_SETUP.md).
Use a separate checkout for cloud if you already have a local or Baseten install.
Existing services, credentials and camera settings must be preserved.

## For the user

Open a fresh clone in your coding agent and say:

> Set up Ghostbusters using docs/STRIPE_PROJECTS.md. Use Stripe Projects to
> provision Supabase and OpenRouter, configure and test the app, and deploy the
> gallery to Vercel. My camera is a [brand/model]. Discover it on this network.
> Tell me when I need to approve account access or privately provide a credential.

The agent runs the commands and provisions available provider accounts. You may
need to do these steps; the agent should ask only when a specific step needs you:

| User action | Why / what to provide |
| --- | --- |
| Approve Stripe sign-in in your own browser | Select the intended account. Complete password, CAPTCHA, email verification or MFA there. Use the CLI's current link/code, not an old one. |
| Approve a provider association | Supabase may ask to authorize an organization associated with your Stripe email. The agent supplies the actual link. |
| Supply a backend key if CLI retrieval is unavailable | Open the provisioned Supabase project's **Settings → API Keys**, copy a **secret** (`sb_secret_…`) or legacy **service_role** key into the agent's secure input. A publishable key or database password cannot substitute. Never paste secrets into chat. |
| Supply camera access / choose a device | Ordinary camera login and local-stream permission; you do not need to know its IP. |
| Choose paid usage if needed | Free provisioning does not guarantee free or available inference. Approve a specific model/plan and budget before a paid upgrade. |

Cloud photos and detection metadata require an explicitly approved viewer account.
The agent creates the account; the viewer clicks an email sign-in link. Face blurring
is best-effort; inference receives unblurred crops. See [cloud privacy](CLOUD_PRIVACY.md).
Stop capture after use; stopping does not delete photos or cancel cloud resources.

## For the agent

### 1. Inspect before provisioning

Read AGENTS.md. Check hardware and existing processes/configuration without
printing secrets. Cloud classification avoids the local MLX requirement, but
camera/YOLO operation still needs validation on the target computer; do not
promise Pi/Windows support or universal doorbell compatibility.

Use a fresh checkout when an installation already exists. Do not import prior
account credentials from another user's checkout. Install dependencies with
`uv sync --frozen --python 3.11`. Install `psql` (Postgres client) for bootstrap;
no local Postgres server or Docker is required.

Keep Stripe's generated files in a separate private provisioning directory so
its `.env` synchronization never overwrites the application's `.env`:

```sh
mkdir -p .ghostbusters/provisioning
chmod 700 .ghostbusters/provisioning
cd .ghostbusters/provisioning
stripe --version
stripe plugin install projects
stripe projects --help
stripe projects status --json
```

If Stripe is missing, install its official CLI (`brew install
stripe/stripe-cli/stripe` on macOS, or `npm install -g @stripe/cli`). If the plugin
already exists, check its version/help instead of reinstalling blindly.

For a new project run `stripe projects init`; for an existing association resume
it. Use the normal user-owned CLI session. Don't build a custom auth server,
override HOME, fabricate accounts, or introduce containers to handle sign-in.
Return the current CLI browser handoff to the user and preserve its continuation.
Verify completion with the CLI before proceeding; a screenshot isn't proof.
If access is test-only/ineligible, use the supported account-selection flow
(`stripe projects switch-account`, if listed in installed help). Don't repeat
permission repair indefinitely or activate a payments business to fix Projects.

### Reduce owner handoffs

Before asking for another login, privately inspect the **names** of credentials
returned by provisioning and the supported provider auth methods. Our Vercel
provisioning returned a working token; a separate browser approval was unnecessary.
Supabase provider association and Supabase CLI management login are separate.
The CLI login is optional if the backend key can be obtained another authorized
way. Don't force users through both paths by default.

With explicit owner authorization and an accessible signed-in browser, computer
use may navigate to the exact new project's API Keys page and transfer an existing
backend key directly to the secure credential destination. Keep reveal/copy/paste
out of screenshots, chat, shell history, command arguments and tool output.
Do not claim success until the secure write receipt or file validation confirms it.
If secure transfer isn't supported, use one secure input form, show where it is,
and replace it only after expiry/cancellation. Never ask for secrets in chat.

Computer use can navigate login pages and fill ordinary non-secret fields. It
cannot be promised to bypass owner actions: account selection, MFA/email codes,
CAPTCHA and new access grants remain subject to the browser tool's approval rules.
Pause at new security-sensitive consent and get the owner's confirmation when
required; do not silently self-approve broader access. Creating/rotating keys is
separate from retrieving an existing authorized key. Prefer normal browser login
to a fragile headless CLI-code relay, and never log incremental PTY secret echoes.

Our October 28 test required Stripe login, Supabase provider approval, an attempted
Supabase CLI login (failed HTTP 404), and a secure backend-key fallback. It also
needed an owner decision to pause an older test database at the free-project cap.
The strict fresh-credential test needed isolated CLI storage because the Stripe
plugin hardcoded a global vault path; Docker was a test isolation workaround, not
a normal product prerequisite. Do not impose those test-harness steps on new users.

### 2. Provision with provider CLIs

Read any installed Stripe Projects CLI skill and current command help. Inspect
`stripe projects catalog --json` / `stripe projects search <provider> --json`.
Check status before each add so resuming doesn't create duplicate resources.
Use the returned service/plan parameters; don't assume the current catalog matches
an older guide. The expected services are Supabase project, OpenRouter API, and
optionally Vercel project. Typical supported commands are:

```sh
stripe projects add supabase/project
stripe projects add openrouter/api
stripe projects env --pull
```

If association is needed, use `stripe projects link <provider>` and its returned
handoff. Let the CLI create/link accounts wherever supported. Do not send users
to create every provider account manually. Complete only necessary browser
approval in the user's browser; do not collect their account password.

Use free plans where available, or the user's approved budget. Record project
and resource IDs, chosen plans and pending steps in a credential-free private
installation note. Keep provider CLI output that might contain secrets out of
chat/logs. Never print `.env`, vault contents, or API-key command output.

### 3. Resolve credentials, schema and camera

Stripe owns `.ghostbusters/provisioning/.env`; don't edit it. The adapter accepts
observed aliases: `SUPABASE_PROJECT_URL` / `SUPABASE_URL`,
`SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_ANON_KEY`, and
`OPENROUTER_API_API_KEY` / `OPENROUTER_API_KEY`. Conflicting aliases fail clearly.
Plan-management keys are not inference keys.

First try backend-key retrieval with the existing authorized Supabase CLI:
`--fetch-supabase-keys` invokes `supabase projects api-keys --project-ref … --output
json` with captured output. Install the official Supabase CLI if necessary.
If login is missing, complete `supabase login` via its normal owner authorization.
If it cannot access this project, ask for the exact backend key described above,
securely stored as `SUPABASE_SECRET_KEY` in `.ghostbusters/cloud-secrets.env`
(mode 0600). Do not substitute a publishable key, scrape a session, or make a
second project. Supply that file with `--secrets` instead of the retrieval flag.

Discover/select the camera using [camera discovery](LOCAL_SETUP.md) and
[adapter recipes](CAMERAS.md). Discovery does not require downloading vision
models or starting local capture. On supported local Macs, install discovery
dependencies with `uv sync --frozen --python 3.11 --extra local` first. On a supported Mac, `ghostbusters local setup
--brand doorbird` provides structured discovery/device selection; use its private
config to obtain the selected address, not a user-supplied assumed IP. Cloud
capture currently uses the legacy USB/RTSP/HTTP reader, so verify the discovered
device supports that stream independently; local DoorBird HTTP success alone
does not prove its RTSP stream works.

The agent writes `.ghostbusters/camera.env` (0600) containing `CAMERA_SOURCE`
(USB index or discovered compatible stream URL), or `DOORBIRD_IP`,
`DOORBIRD_USERNAME`, `DOORBIRD_PASSWORD`. Optional `DEVICE_ID` and `ROI_*` are
accepted. No credentials, URLs or frames in logs/UI. If the camera only supports
an incompatible adapter, report that limitation instead of guessing endpoints.

Choose an explicit currently available OpenRouter model accepting image input.
Inspect the provider's model catalog, pricing, retention/training policies and
input restrictions before sending camera images. Synthetic model success is not
permission to upload faces. The tested `nvidia/nemotron-3.5-super-vl:free` endpoint
has zero token pricing but its [provider notice](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free)
prohibits personal data such as faces; do not select it for real camera capture.
It was used in the October 28 verification, and this limitation was identified
afterward. Future real-camera setup must select a suitable endpoint or local mode. The client requires no-data-collection and ZDR
routing and blocks that free endpoint; [current replacement test results](CLOUD_PRIVACY.md)
are explicit about credit/routing failures. Don't hardcode a free model
from an old test: availability, quota and credit requirements can change.
From the repository root:

```sh
uv run --no-sync ghostbusters projects configure \
  --source .ghostbusters/provisioning/.env \
  --camera-env .ghostbusters/camera.env \
  --model <chosen-vision-model-id> \
  --fetch-supabase-keys
uv run --no-sync ghostbusters projects bootstrap \
  --source .ghostbusters/provisioning/.env
```

Configure validates before writing `.env` and `frontend/.env.local`, with 0600
permissions. It never starts capture. Identical reruns are safe; conflicting
existing app configuration is refused. It imports only runtime fields, not
Stripe keys, database passwords or provider management tokens.

Bootstrap uses `psql`, a transaction, and a rerunnable schema with explicit
grants, viewer-list RLS, Realtime membership and a private image bucket. Use a dedicated new
Ghostbusters database, not an unrelated application's project. It prefers the
**provider-returned** `SUPABASE_POOLER_URL` (including transaction poolers) over
`SUPABASE_DB_URL`, since direct endpoints may require IPv6. `[YOUR-PASSWORD]`
is hydrated with URL-encoded `DB_PASS`, `SUPABASE_DB_PASSWORD`, or
`SUPABASE_DB_PASS`. Do not invent
hostnames/ports. The connection URI is decoded into libpq environment fields (host, port,
database, user and password), with TLS required. Credentials are never placed
in command arguments. No new Python setup dependencies are needed.

### 4. Configure private gallery access

The adapter writes `GALLERY_ACCESS=private` and
`NEXT_PUBLIC_GALLERY_ACCESS=private`. Bootstrap denies anonymous data/photo reads.
Create/reuse the owner's Auth user and grant access (no email is sent by this command):

```sh
uv run --no-sync ghostbusters projects add-viewer --email <owner-email>
```

Set Supabase Auth Site URL and allowed redirect URL to the exact deployed gallery
URL, using authorized provider tools or **Authentication → URL Configuration**.
The user then opens the gallery and requests/clicks an email sign-in link. This is
an additional necessary owner step for private viewing. Check email delivery;
Supabase's default email service may require configured SMTP for non-team viewers.
Do not make the bucket public to work around missing login or SMTP configuration.
See [viewer management and migration](CLOUD_PRIVACY.md) for revocation and existing installs.

### 5. Verify, deploy, then start

```sh
uv run --no-sync ghostbusters doctor --skip-camera
npm --prefix frontend ci
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Doctor makes one small potentially billed vision request with a synthetic blank
image, then checks backend database reads, denied anonymous reads and private bucket access. A 402 means account
creation did not establish model credit/access; a 429 means quota/rate limits.
Resolve the chosen model or budget explicitly. Don't silently switch to paid
inference. Read checks do not verify upload, classification quality or Realtime.

For a hosted gallery, provision the Vercel service with Stripe Projects if
available, then use the Vercel CLI to link **frontend/** to that exact project.
Inspect `vercel link --help`, `vercel env add --help` and `vercel deploy --help`.
Set these production/build variables using private file/stdin input:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (publishable/anon only)
- `NEXT_PUBLIC_STORAGE_PROVIDER=supabase`
- `NEXT_PUBLIC_GALLERY_ACCESS=private`
- `NEXT_PUBLIC_SOURCE_URL` (the corresponding source for this deployed version)

Deploy with the Vercel CLI from frontend (`vercel deploy --prod` after linking
and setting variables); record its actual returned URL and open its `/ghostbusters` gallery path. Never upload backend
`.env`, camera credentials, Supabase secret key or OpenRouter key to frontend.
See [frontend setup](../frontend/SETUP.md) for local dashboard operation.

Run `ghostbusters doctor` with capture stopped to test a camera frame. Then
`ghostbusters start --foreground` for the first supervised session. Keep the
computer on the home network; Vercel does not run camera capture. Ctrl+C stops
foreground capture. Install background capture with `ghostbusters start` only
after verification and after checking no existing Ghostbusters service owns it.

For disposable test resources, verify a synthetic classification, storage upload,
insert, denied anonymous reads, approved-viewer reads and browser Realtime update, then remove the exact test rows
and objects. Finally ask the owner to walk through the camera view and verify
classification/photo arrival without reloading. Report each result separately;
provisioned, synthetic-tested and real-camera-tested are different milestones.
Offline unit tests never establish a live cloud or camera result. Test an unlisted
signed-in account too: authentication alone must not reveal rows or issue photo links.

### Recovery and cleanup

Resume the same project and pending step. Re-pull credentials before importing
when provisioning completes. Never rerun account signup because an approval
expired; issue one fresh handoff for the same account when necessary. Use the
provider CLI to inspect resource state before retrying a timed-out creation.

`ghostbusters stop` stops background capture, not hosting/billing/data. To remove
cloud resources, review the recorded inventory with the owner and use the
provider CLI or supported Stripe Projects removal command for those exact IDs.
Remove plaintext credential files only after the resources/config are no longer
needed; never delete existing installations as cleanup for a new attempt.

## Evidence and references

The October 2026 earlier onboarding test eventually verified OpenRouter inference,
Supabase uploads/inserts/public reads and browser Realtime using synthetic data.
The October 28 fresh test also verified a real DoorBird no-costume person
through the deployed gallery without reload. It took 100.5 minutes including
owner waits; this is not a measured unattended setup time. That test predated the
private-gallery changes; it does not verify the new hosted Auth/signed-link flow. Its two bootstrap
fixes (SUPABASE_DB_PASS and libpq environment components) are included.

The earlier blockers motivated this adapter: alias mismatches, missing backend key,
IPv6-only direct database connectivity, inference credit/quota failures and
repeated browser authorization. This new implementation has offline regression
coverage; it still requires live verification on each new account/camera.

Current provider references (checked October 27, 2026):
[Stripe Projects](https://docs.stripe.com/projects),
[Supabase integration](https://supabase.com/docs/guides/integrations/stripe-projects),
[Supabase CLI key retrieval](https://supabase.com/docs/reference/cli/supabase-projects-api-keys),
[OpenRouter API](https://openrouter.ai/docs/api-reference/overview).
