# ghostbusters

an open-source doorbell camera project that detects visitors, guesses their
halloween costumes, and shows their photos in a live gallery.

i built and run my installation with **baseten for inference, supabase for the
database and photo storage, and vercel for the frontend**. yolo detection and camera
capture run on a computer at home. that is still my setup: starting my configured
installation runs through baseten. adding other setup options has not switched it
to local inference or stripe projects.

you can reproduce that stack with your own accounts and keys. i've also added two
agent-guided ways to get started from a prompt: **local setup** and **stripe
projects setup**. both have passed real doorbird walkthroughs; see the verification
notes below for what was tested and what changed afterward.

## choose your setup

| path | inference | records, photos and gallery | start here |
| --- | --- | --- | --- |
| **original stack — what i run** | baseten | supabase + vercel | [baseten setup](docs/CLI.md) with your own accounts/keys |
| **local — no cloud accounts** | qwen vision model on your mac | sqlite, local photos and a private local gallery | [local setup](docs/LOCAL_SETUP.md) |
| **stripe projects — agent-provisioned cloud** | openrouter | supabase + optional vercel, provisioned through provider clis | [stripe projects setup](docs/STRIPE_PROJECTS.md) |

**fresh clones default to local setup. existing configured installations keep their
selected provider.** use a separate checkout to try another path alongside an
existing installation. in every path, the capture computer stays on the camera's
network; vercel hosts the frontend, not the camera process.

clone the repository and open it in your coding agent:

```sh
git clone https://github.com/alanagoyal/ghostbusters.git
cd ghostbusters
```

## use the original baseten stack

create your own baseten, supabase and vercel accounts, supply your keys privately,
and follow [the cloud setup guide](docs/CLI.md), [supabase setup](docs/SUPABASE_SETUP.md)
and [frontend hosting guide](frontend/SETUP.md). you can ask your agent:

> set up ghostbusters using the original baseten + supabase + vercel stack in `docs/CLI.md`. use my own accounts and keys. my camera is a <brand/model>. keep baseten as the inference provider and tell me when you need secure credential input.

for a new installation, select baseten explicitly:

```sh
uv sync --frozen --python 3.11
uv run --no-sync ghostbusters setup --provider baseten
```

once configured, start the backend with:

```sh
uv run --no-sync ghostbusters start --foreground
```

this uses that installation's configured provider, database and camera. **in my
installation, that means baseten and my existing supabase project.** ctrl+c stops
foreground capture. the vercel frontend is separate; for local frontend development,
run `npm --prefix frontend ci` and `npm --prefix frontend run dev`.

cloud inference is billed. the original supabase setup uses public gallery reads
and a public photo bucket; review [privacy and private-gallery migration](docs/CLOUD_PRIVACY.md)
before deploying your own installation. updating the code does not change existing
hosted access policies.

## easier path: local setup

> get ghostbusters working locally with my doorbell using `docs/LOCAL_SETUP.md`. it is a <brand/model> on the same network as this computer. keep inference and photos local.

the agent handles discovery, dependencies, model downloads and the private gallery.
no cloud account, credit card or docker is needed. you may need to provide your
camera login privately, enable local streaming, grant camera/network permission,
or choose a discovered device. starting from one prompt still requires these
owner actions when applicable.

**supported full-local hardware:** apple silicon macos with at least 16 gb ram and
python 3.11. tested on an m4 mac mini (16 gb) and m2 macbook air (24 gb). linux,
windows and raspberry pi full-local inference are not supported by this release.
see [model measurements](docs/LOCAL_BENCHMARK.md) and the [complete runbook](docs/LOCAL_SETUP.md).

local photos are private and unblurred, with retention and disk limits. the gallery
requires its private access link. costume guesses can be wrong; counts are
detections, not unique visitors.

## easier path: stripe projects setup

> set up ghostbusters using `docs/STRIPE_PROJECTS.md`. use stripe projects to provision supabase and openrouter and deploy the gallery to vercel. my camera is a <brand/model>. discover it on this network and tell me when i need to approve access or provide a secret privately.

the agent provisions supported resources through stripe projects and provider clis,
imports credentials, configures the app and bootstraps the database. this path uses
**openrouter instead of baseten** and does not replace my original installation.
new projects galleries use private photo buckets and an explicit viewer list.

plan for these owner steps when needed:

1. sign in to stripe projects and approve provider association (supabase in our test).
2. approve supabase cli access if needed for automatic backend-key retrieval. if retrieval is unavailable, paste the project's backend key into a secure form instead. both routes are not inherently required.
3. provide camera access or choose a device, approve any paid model/budget, and do a walkthrough to verify capture.
4. for the private gallery, request and click an email sign-in link. the agent creates your viewer account and access list.

agents should use provisioned credentials before requesting another login; vercel
needed no separate login in our test. computer use can help navigate provider pages,
but tool security rules may require you to approve access or paste credentials
yourself. never put secrets in chat. the [user and agent runbook](docs/STRIPE_PROJECTS.md)
covers these handoffs, free-tier capacity limits and recovery.

## what we've verified

- **original baseten stack:** real doorbird capture → baseten classification → photo/record in the existing supabase project. reverified october 28, 2026 after rotating the api key; this remains my running configuration.
- **local setup:** fresh installation on an m2 macbook air, camera discovery, local inference and a real-person “no costume” result in the authenticated gallery. [acceptance evidence](docs/LOCAL_BENCHMARK.md#fresh-install-acceptance).
- **stripe projects:** fresh provisioning and a real doorbird walkthrough through openrouter → supabase → hosted gallery, including an update without reloading, on october 28, 2026. that test preceded the new private-gallery sign-in/signed-link changes; those have automated policy and link tests but still need hosted verification.

the stripe test used `nvidia/nemotron-3.5-super-vl:free` at $0 token pricing.
its [provider notice](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free) prohibits
personal data such as faces, identified after that test. the app now blocks that
endpoint for camera use. a suitable replacement must be selected and verified;
the paid replacement checks hit routing/credit blockers. see
[model selection, costs and privacy](docs/CLOUD_PRIVACY.md). free provisioning does
not guarantee free or available inference.

**camera support is not universal.** doorbird, usb and onvif/rtsp adapters have
different levels of hardware verification; see [camera support](docs/CAMERAS.md).
vendor-cloud-only doorbells may need another adapter.

[test stills and camera-free verification](backend/tests/fixtures/README.md) · [contributing](CONTRIBUTING.md) · [privacy](SECURITY.md)

## license

the combined application is distributed under [agpl-3.0](LICENSE). original mit
notices are preserved in [third-party notices](THIRD_PARTY_NOTICES.md). hosted forks
must offer corresponding source; set `NEXT_PUBLIC_SOURCE_URL` to the deployed source.
