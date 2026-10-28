# Ghostbusters

An open-source doorbell camera project that detects visitors, guesses their
Halloween costumes, and shows their photos in a live gallery.

I built and run my installation with **Baseten for inference, Supabase for the
database and photo storage, and Vercel for the frontend**. YOLO detection and camera
capture run on a computer at home. That is still my setup: starting my configured
installation runs through Baseten. Adding other setup options has not switched it
to local inference or Stripe Projects.

You can reproduce that stack with your own accounts and keys. I've also added two
agent-guided ways to get started from a prompt: **local setup** and **Stripe
Projects setup**. Both have passed real DoorBird walkthroughs; see the verification
notes below for what was tested and what changed afterward.

## Choose your setup

| Path | Inference | Records, photos and gallery | Start here |
| --- | --- | --- | --- |
| **Original stack — what I run** | Baseten | Supabase + Vercel | [Baseten setup](docs/CLI.md) with your own accounts/keys |
| **Local — no cloud accounts** | Qwen vision model on your Mac | SQLite, local photos and a private local gallery | [Local setup](docs/LOCAL_SETUP.md) |
| **Stripe Projects — agent-provisioned cloud** | OpenRouter | Supabase + optional Vercel, provisioned through provider CLIs | [Stripe Projects setup](docs/STRIPE_PROJECTS.md) |

**Fresh clones default to local setup. Existing configured installations keep their
selected provider.** Use a separate checkout to try another path alongside an
existing installation. In every path, the capture computer stays on the camera's
network; Vercel hosts the frontend, not the camera process.

Clone the repository and open it in your coding agent:

```sh
git clone https://github.com/alanagoyal/ghostbusters.git
cd ghostbusters
```

## Use the original Baseten stack

Create your own Baseten, Supabase and Vercel accounts, supply your keys privately,
and follow [the cloud setup guide](docs/CLI.md), [Supabase setup](docs/SUPABASE_SETUP.md)
and [frontend hosting guide](frontend/SETUP.md). You can ask your agent:

> Set up Ghostbusters using the original Baseten + Supabase + Vercel stack in docs/CLI.md. Use my own accounts and keys. My camera is a <brand/model>. Keep Baseten as the inference provider and tell me when you need secure credential input.

For a new installation, select Baseten explicitly:

```sh
uv sync --frozen --python 3.11
uv run --no-sync ghostbusters setup --provider baseten
```

Once configured, start the backend with:

```sh
uv run --no-sync ghostbusters start --foreground
```

This uses that installation's configured provider, database and camera. **In my
installation, that means Baseten and my existing Supabase project.** Ctrl+C stops
foreground capture. The Vercel frontend is separate; for local frontend development,
run `npm --prefix frontend ci` and `npm --prefix frontend run dev`.

Cloud inference is billed. The original Supabase setup uses public gallery reads
and a public photo bucket; review [privacy and private-gallery migration](docs/CLOUD_PRIVACY.md)
before deploying your own installation. Updating the code does not change existing
hosted access policies.

## Easier path: local setup

> Get Ghostbusters working locally with my doorbell using docs/LOCAL_SETUP.md. It is a <brand/model> on the same network as this computer. Keep inference and photos local.

The agent handles discovery, dependencies, model downloads and the private gallery.
No cloud account, credit card or Docker is needed. You may need to provide your
camera login privately, enable local streaming, grant camera/network permission,
or choose a discovered device. Starting from one prompt still requires these
owner actions when applicable.

**Supported full-local hardware:** Apple Silicon macOS with at least 16 GB RAM and
Python 3.11. Tested on an M4 Mac mini (16 GB) and M2 MacBook Air (24 GB). Linux,
Windows and Raspberry Pi full-local inference are not supported by this release.
See [model measurements](docs/LOCAL_BENCHMARK.md) and the [complete runbook](docs/LOCAL_SETUP.md).

Local photos are private and unblurred, with retention and disk limits. The gallery
requires its private access link. Costume guesses can be wrong; counts are
detections, not unique visitors.

## Easier path: Stripe Projects setup

> Set up Ghostbusters using docs/STRIPE_PROJECTS.md. Use Stripe Projects to provision Supabase and OpenRouter and deploy the gallery to Vercel. My camera is a <brand/model>. Discover it on this network and tell me when I need to approve access or provide a secret privately.

The agent provisions supported resources through Stripe Projects and provider CLIs,
imports credentials, configures the app and bootstraps the database. This path uses
**OpenRouter instead of Baseten** and does not replace my original installation.
New Projects galleries use private photo buckets and an explicit viewer list.

Plan for these owner steps when needed:

1. Sign in to Stripe Projects and approve provider association (Supabase in our test).
2. Approve Supabase CLI access if needed for automatic backend-key retrieval. If retrieval is unavailable, paste the project's backend key into a secure form instead. Both routes are not inherently required.
3. Provide camera access or choose a device, approve any paid model/budget, and do a walkthrough to verify capture.
4. For the private gallery, request and click an email sign-in link. The agent creates your viewer account and access list.

Agents should use provisioned credentials before requesting another login; Vercel
needed no separate login in our test. Computer use can help navigate provider pages,
but tool security rules may require you to approve access or paste credentials
yourself. Never put secrets in chat. The [user and agent runbook](docs/STRIPE_PROJECTS.md)
covers these handoffs, free-tier capacity limits and recovery.

## What we've verified

- **Original Baseten stack:** real DoorBird capture → Baseten classification → photo/record in the existing Supabase project. Reverified October 28, 2026 after rotating the API key; this remains my running configuration.
- **Local setup:** fresh installation on an M2 MacBook Air, camera discovery, local inference and a real-person “No costume” result in the authenticated gallery. [Acceptance evidence](docs/LOCAL_BENCHMARK.md#fresh-install-acceptance).
- **Stripe Projects:** fresh provisioning and a real DoorBird walkthrough through OpenRouter → Supabase → hosted gallery, including an update without reloading, on October 28, 2026. That test preceded the new private-gallery sign-in/signed-link changes; those have automated policy and link tests but still need hosted verification.

The Stripe test used `nvidia/nemotron-3.5-super-vl:free` at $0 token pricing.
Its [provider notice](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free) prohibits
personal data such as faces, identified after that test. The app now blocks that
endpoint for camera use. A suitable replacement must be selected and verified;
the paid replacement checks hit routing/credit blockers. See
[model selection, costs and privacy](docs/CLOUD_PRIVACY.md). Free provisioning does
not guarantee free or available inference.

**Camera support is not universal.** DoorBird, USB and ONVIF/RTSP adapters have
different levels of hardware verification; see [camera support](docs/CAMERAS.md).
Vendor-cloud-only doorbells may need another adapter.

[Test stills and camera-free verification](backend/tests/fixtures/README.md) · [Contributing](CONTRIBUTING.md) · [Privacy](SECURITY.md)

## License

The combined application is distributed under [AGPL-3.0](LICENSE). Original MIT
notices are preserved in [third-party notices](THIRD_PARTY_NOTICES.md). Hosted forks
must offer corresponding source; set `NEXT_PUBLIC_SOURCE_URL` to the deployed source.
