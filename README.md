# Ghostbusters — local-first Halloween 2026

Clone the repository, open it with your coding agent, and say:

```sh
git clone https://github.com/alanagoyal/ghostbusters.git
cd ghostbusters
```

> Get Ghostbusters working with my doorbell. It is a <brand/model> on the Wi-Fi network this computer is on.

The default is a private costume gallery on your computer: YOLO detection, local
vision classification, SQLite records, local photos and live updates. No account,
credit card or Docker. The agent follows [the complete local setup runbook](docs/LOCAL_SETUP.md).
You may need to enter your camera login privately, enable local streaming, allow
camera/network access, or choose a device.

**Tested hosts:** Apple M4 Mac mini (16 GB) and M2 MacBook Air (24 GB), Python 3.11. Full local vision uses
Apple's Metal GPU; Linux, Windows and Raspberry Pi full-local inference are not
supported by this release. [Model measurements and limits](docs/LOCAL_BENCHMARK.md).

**Cameras:** DoorBird local API, USB adapter, and discoverable ONVIF/RTSP adapter.
See the runbook for the distinction between implemented and hardware-tested support.
Vendor-cloud-only doorbells need a separate adapter; compatibility is not universal.

```sh
uv sync --frozen --python 3.11 --extra local
uv run --no-sync ghostbusters local setup --brand doorbird
uv run --no-sync ghostbusters local models
uv run --no-sync ghostbusters local build
uv run --no-sync ghostbusters local camera-check --seconds 15
uv run --no-sync ghostbusters local up
uv run --no-sync ghostbusters local link
```

Setup is resumable and emits JSON actions; provide credentials only through a private
file as described in the runbook. `local status` reports health; `local stop` stops
only this install. Photos stay private and unblurred locally, are deleted under the
retention/disk policy, and require the private gallery access link. Costume guesses
can be wrong, and counts represent detections rather than unique visitors.

## Optional cloud version with Stripe Projects

For cloud vision and a private, sign-in-protected gallery, ask your agent to follow
[the Stripe Projects setup guide](docs/STRIPE_PROJECTS.md). The agent provisions
Supabase/OpenRouter and optionally Vercel using their CLIs, imports credentials,
and bootstraps the database. The guide spells out browser approvals and the
Supabase backend-key fallback. Capture still runs on a computer at home.
Use a separate checkout to keep an existing local installation alongside cloud.

**Plan for a few owner steps:**

1. Sign in to Stripe Projects and approve the requested provider association (Supabase in our test).
2. If credentials are missing, approve Supabase CLI access **or** use the existing dashboard key route below. Both are not inherently required.
3. If automatic retrieval is unavailable, supply the new project's Supabase backend secret through a secure form. With your authorization, an agent with access to your signed-in browser can copy an **existing** key directly into secure configuration instead; never put it in chat.

Agents should first reuse credentials returned by provisioning, before requesting
another login. Vercel needed no separate authorization in our test. You still
handle account selection, password/MFA/CAPTCHA challenges and required permission
consent. Camera credentials/streaming permission, a real walkthrough, and a
free-tier capacity or budget decision may also need you. With the private cloud
gallery, you also click an email sign-in link; the agent creates your viewer account
and access list. [Privacy, model selection and migration](docs/CLOUD_PRIVACY.md).

**Verified cloud test:** DoorBird capture → classification → storage → live hosted
gallery worked on October 28, 2026. The test used
`nvidia/nemotron-3.5-super-vl:free` at $0 inference pricing. However, its
[current provider notice](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free)
says not to submit personal data such as faces: **do not use that free endpoint
for real camera footage**. It is not a recommended production default. Choose a
vision endpoint with suitable data-use terms and explicit pricing, or use local
mode. Free inference also has quotas and variable availability.

Existing Baseten/Supabase installs keep their configured behavior.
Manual cloud setup is explicit: `uv run --no-sync ghostbusters setup --provider baseten`.
See [legacy cloud CLI operation](docs/CLI.md).

[Test stills and camera-free verification](backend/tests/fixtures/README.md) · [Contributing](CONTRIBUTING.md) · [Privacy](SECURITY.md)

## License

The combined application is distributed under [AGPL-3.0](LICENSE). Original MIT
notices are preserved in [third-party notices](THIRD_PARTY_NOTICES.md). Hosted forks
must offer corresponding source; set `NEXT_PUBLIC_SOURCE_URL` to the deployed source.
