#!/usr/bin/env bash
# Check committed frontend code in isolation, identically before push and in CI.
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
check_dir=$(mktemp -d "${TMPDIR:-/tmp}/ghostbusters-frontend.XXXXXX")
trap 'rm -rf "$check_dir"' EXIT
git -C "$repo_root" archive "${PRE_COMMIT_TO_REF:-HEAD}" frontend | tar -x -C "$check_dir"

# Exclude installed cloud configuration, ignored .env files, and build output.
for variable in $(compgen -e); do
  case "$variable" in
    NEXT_PUBLIC_*|SUPABASE_*|NODE_ENV) unset "$variable" ;;
  esac
done
export NEXT_PUBLIC_STORAGE_PROVIDER=local
export NEXT_PUBLIC_BASE_PATH=''
export NEXT_TELEMETRY_DISABLED=1

cd "$check_dir/frontend"
npm ci
npm run typecheck
npm test
npm run build
