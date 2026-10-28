# Security and privacy

Do not post credentials, private images or exploit details in a public issue. Use GitHub **Security → Report a vulnerability** if enabled; otherwise use the maintainer's GitHub profile contact channel. This hobby project has no guaranteed response time.

## Default local installation

Camera credentials, SQLite records and unblurred person crops stay on the computer under `.ghostbusters/`. The server binds to loopback; its API, images and live events require the private gallery token. Treat the full gallery link as a password. Keep runtime files private and out of version control. Photos expire under the configured retention and disk limits; downloaded models are separate from that budget.

Local inference does not upload camera images to a model provider. A browser viewing the gallery receives those images; sharing the gallery allows that viewer to see them. Do not expose it through an unauthenticated proxy or forward camera ports to the internet. Camera-library logs can contain credential-bearing URLs.

## Existing cloud installations

The optional Baseten path sends unblurred person crops to the inference provider. The legacy Supabase gallery and image bucket are publicly readable. The saved full-scene image uses face blurring, which is not guaranteed anonymization. Backend secret/service-role keys must never be put in frontend configuration. Review your capture area, access policies and retention before enabling this path.

## New Stripe Projects cloud installs

New Projects setup uses private buckets, explicit viewer membership, and signed
photo links. Read [cloud privacy](docs/CLOUD_PRIVACY.md) for sign-in, model routing,
revocation, retention and migration. Older public installations require an explicit
migration; updating code does not retroactively protect their hosted resources.
Report security issues privately through GitHub's private vulnerability reporting
when enabled; do not put credentials or private images into public issues.
