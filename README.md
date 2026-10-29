# ghostbusters

an open-source doorbell camera project that detects visitors, guesses their
halloween costumes, and shows their photos in a live gallery.

i built it with baseten, supabase and vercel. you can use that stack, run fully
locally on a supported mac, or provision a cloud installation with stripe projects.
in every setup, a computer stays on the camera's network to capture video and run
person detection; vercel hosts only the cloud gallery.

## choose your setup

| path | inference | records, photos and gallery | start here |
| --- | --- | --- | --- |
| **local — no cloud accounts** | qwen vision model on your mac | sqlite, local photos and a private local gallery | [local setup](docs/LOCAL_SETUP.md) |
| **stripe projects — agent-provisioned cloud** | openrouter | supabase + optional vercel | [stripe projects setup](docs/STRIPE_PROJECTS.md) |
| **original stack — what i run** | baseten | supabase + vercel | [cloud setup](docs/CLI.md) with your own accounts/keys |

fresh clones default to local setup. existing configured installations keep their
selected provider. use a separate checkout to try another path alongside one
that's already running.

```sh
git clone https://github.com/alanagoyal/ghostbusters.git
cd ghostbusters
```

open the repository in your coding agent and use one of these prompts:

### local setup

> get ghostbusters working locally with my doorbell using `docs/LOCAL_SETUP.md`. it is a <brand/model> on the same network as this computer. keep inference and photos local.

requires **apple silicon macos, at least 16 gb ram, and python 3.11**. tested on an
m4 mac mini (16 gb) and m2 macbook air (24 gb). linux, windows and raspberry pi
full-local inference are not supported. see [model measurements](docs/LOCAL_BENCHMARK.md).

no cloud account, credit card or docker is needed. the agent handles discovery,
dependencies, model downloads and the gallery. you may need to provide a camera
login privately, enable local streaming, grant permissions, or choose a device.
local photos are **unblurred**, protected by a private access link, with retention
and disk limits.

### stripe projects setup

> set up ghostbusters using `docs/STRIPE_PROJECTS.md`. use stripe projects to provision supabase and openrouter and deploy the gallery to vercel. my camera is a <brand/model>. discover it on this network and tell me when i need to approve access or provide a secret privately.

you may need to approve provider access, supply a backend key securely, and choose
a model and budget. new galleries use private storage and an explicit viewer list;
viewers complete email sign-in. free provisioning does not guarantee free inference.
see the [setup runbook](docs/STRIPE_PROJECTS.md) and [cloud privacy guide](docs/CLOUD_PRIVACY.md).

### original baseten stack

> set up ghostbusters using the original baseten + supabase + vercel stack in `docs/CLI.md`. use my own accounts and keys. my camera is a <brand/model>. keep baseten as the inference provider and tell me when you need secure credential input.

for manual setup, follow [cloud setup](docs/CLI.md), [supabase setup](docs/SUPABASE_SETUP.md)
and [frontend hosting](frontend/SETUP.md). cloud inference is billed. the original
schema uses public gallery reads and a public photo bucket; review the
[private-gallery migration](docs/CLOUD_PRIVACY.md#existing-public-installations)
before deploying your own installation.

## compatibility and verification

camera support is not universal. doorbird has real-hardware verification; usb and
onvif/rtsp support require testing on your device. vendor-cloud-only doorbells may
need another adapter. see [camera support](docs/CAMERAS.md).

- **baseten:** verified real doorbird capture, classification and photo/record storage.
- **local:** verified a fresh mac installation, discovery, local inference and a real-person “no costume” result in the authenticated gallery. see [acceptance evidence](docs/LOCAL_BENCHMARK.md#fresh-install-acceptance).
- **stripe projects:** provisioning and a real doorbird walkthrough reached the hosted gallery with live updates. that test preceded private-gallery sign-in and signed-link changes, which still need hosted verification. the model used is now blocked because its provider prohibits face data; a suitable replacement still needs successful verification.

costume guesses can be wrong, and counts are detections, not unique visitors.
cloud inference receives unblurred person crops; saved cloud scenes blur detected
person regions on a best-effort basis. this is not anonymization. see
[privacy and model restrictions](docs/CLOUD_PRIVACY.md).

[test stills and camera-free verification](backend/tests/fixtures/README.md) · [contributing](CONTRIBUTING.md) · [security](SECURITY.md)

## license

the combined application is distributed under [agpl-3.0](LICENSE). original mit
notices are preserved in [third-party notices](THIRD_PARTY_NOTICES.md). hosted forks
must offer corresponding source; set `NEXT_PUBLIC_SOURCE_URL` to the deployed source.
