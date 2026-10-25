# Ghostbusters gallery

The default local gallery is a static Next.js build served by the Python local service. Follow [local setup](../docs/LOCAL_SETUP.md); `ghostbusters local build` installs frontend dependencies and builds it, and `ghostbusters local up` serves its authenticated API, images and live events. It needs no Supabase configuration or separate Next.js server.

Run `npm ci` and `npm run typecheck` here for frontend development. Use the local build command from the repository root to verify the static output.

The existing cloud branch uses Supabase and the `/ghostbusters` base path. Its development and hosting instructions are in [SETUP.md](SETUP.md).
