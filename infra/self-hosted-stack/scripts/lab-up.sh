#!/usr/bin/env bash
# Start Solo Empire Docker lab by profile (local only).
# Usage:
#   ./scripts/lab-up.sh core observability
#   ./scripts/lab-up.sh shared-platform
#   ./scripts/lab-up.sh core observability devsecops data
#   ./scripts/lab-up.sh streaming
#   ./scripts/lab-up.sh status
#   ./scripts/lab-up.sh down
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — copying from .env.example (edit secrets before production-like use)."
  cp .env.example .env
fi

usage() {
  cat <<'EOF'
Usage:
  lab-up.sh <profile> [profile...]   Start selected profiles
  lab-up.sh status                   Show this project's containers
  lab-up.sh down                     Stop all known lab profiles
  lab-up.sh config                   Validate compose for selected profiles

  Profiles: shared-platform core observability devsecops data streaming optional
            docker-control docker-admin lab-auto-update
Recommended: shared-platform
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

cmd="$1"
shift || true

profile_args=()
for p in "$@"; do
  profile_args+=(--profile "$p")
done

case "$cmd" in
  status)
    docker compose ps -a
    ;;
  down)
    docker compose \
      --profile core \
      --profile observability \
      --profile devsecops \
      --profile shared-platform \
      --profile data \
      --profile streaming \
      --profile optional \
      --profile docker-control \
      --profile docker-admin \
      --profile lab-auto-update \
      down
    ;;
  config)
    if [[ ${#profile_args[@]} -eq 0 ]]; then
      echo "Pass profiles after config, e.g. lab-up.sh config core observability"
      exit 1
    fi
    docker compose "${profile_args[@]}" config --quiet
    echo "OK: compose config valid"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    # First arg was a profile name
    profiles=("$cmd" "$@")
    profile_args=()
    for p in "${profiles[@]}"; do
      case "$p" in
        shared-platform|core|observability|devsecops|data|streaming|optional|docker-control|docker-admin|lab-auto-update|disabled) ;;
        *)
          echo "Unknown profile: $p"
          usage
          exit 1
          ;;
      esac
      profile_args+=(--profile "$p")
    done
    echo "Starting profiles: ${profiles[*]}"
    docker compose "${profile_args[@]}" up -d
    docker compose "${profile_args[@]}" ps
    ;;
esac
