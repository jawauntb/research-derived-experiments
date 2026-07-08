#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Sync Inquiry Black Box model/deploy environment keys from Doppler to Railway.

Values are never printed. Each variable is read from Doppler and piped to
Railway with --stdin.

Usage:
  bun run railway:sync-model-env -- \
    --railway-project <project-id-or-name> \
    --railway-service <service-id-or-name> \
    --railway-environment <environment-name>

Options:
  --doppler-project <name>        Defaults to cofounder.
  --doppler-config <name>         Defaults to prd_superoptimizers.
  --railway-project <selector>    Railway project selector.
  --railway-service <selector>    Railway service selector.
  --railway-environment <name>    Railway environment selector.
  --env-file <path>               Secondary dotenv source for keys missing in Doppler.
  --dry-run                       Show key actions without setting values.
  -h, --help                      Show this help.

Environment overrides:
  RAILWAY_BIN=/path/to/railway     Use an installed Railway binary.
  DOPPLER_BIN=/path/to/doppler     Use an installed Doppler binary.
USAGE
}

doppler_project="${DOPPLER_PROJECT:-cofounder}"
doppler_config="${DOPPLER_CONFIG:-prd_superoptimizers}"
railway_project="${RAILWAY_PROJECT:-}"
railway_service="${RAILWAY_SERVICE:-}"
railway_environment="${RAILWAY_ENVIRONMENT:-}"
dry_run=0
env_files=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --doppler-project)
      doppler_project="$2"
      shift 2
      ;;
    --doppler-config)
      doppler_config="$2"
      shift 2
      ;;
    --railway-project)
      railway_project="$2"
      shift 2
      ;;
    --railway-service)
      railway_service="$2"
      shift 2
      ;;
    --railway-environment)
      railway_environment="$2"
      shift 2
      ;;
    --env-file)
      env_files+=("$2")
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$railway_project" || -z "$railway_service" || -z "$railway_environment" ]]; then
  echo "railway project, service, and environment are required" >&2
  usage >&2
  exit 2
fi

doppler_bin="${DOPPLER_BIN:-doppler}"
if [[ -n "${RAILWAY_BIN:-}" ]]; then
  railway_cmd=("$RAILWAY_BIN")
else
  railway_cmd=(npx -y @railway/cli)
fi

railway_flags=(
  --project "$railway_project"
  --service "$railway_service"
  --environment "$railway_environment"
  --skip-deploys
)

source_keys=(
  NIXPACKS_NODE_VERSION
  INQUIRY_CLOUD_AUTH_SECRET
  DATABASE_URL
  RAILWAY_PUBLIC_API_URL
  SYNC_ENCRYPTION_KEY
  MODAL_JOB_WEBHOOK_URL
  MODAL_JOB_WEBHOOK_TOKEN
  MODAL_JOB_TIMEOUT_MS
  MODAL_TOKEN_ID
  MODAL_TOKEN_SECRET
  MODAL_ENVIRONMENT
  MODAL_REGION
  MODAL_WORKSPACE
  MODAL_DEFAULT_GPU
  OPENAI_API_KEY
  ANTHROPIC_API_KEY
  GOOGLE_API_KEY
  OPENROUTER_API_KEY
  OPENROUTER_BASE_URL
  VOYAGE_API_KEY
  HF_TOKEN
  HUGGINGFACE_TOKEN
  MODEL_PROVIDER
  SESSION_SUMMARY_MODEL
  EMBEDDING_MODEL
  ANTHROPIC_MODEL_JUDGE
  ANTHROPIC_MODEL_BULK
  GEMINI_MODEL_VIDEO
  GEMINI_MODEL_JUDGE
  TRIBE_MODEL_ID
  TRIBE_MODEL_REVISION
  TRIBE_GIT_REF
  VJEPA_MODEL_ID
  VJEPA_LARGE_MODEL_ID
  INTERNVIDEO_MODEL_ID
  QWEN_VL_MODEL_ID
  WHISPER_MODEL_ID
  FASTER_WHISPER_MODEL_ID
  BRAIN2QWERTY_REPO
  BRAIN2QWERTY_DATASET_ID
  BRAINDECODE_MODEL_ID
  SCV_OPEN_LLM_MODEL_ID
  SCV_OPEN_LLM_ACTIVATION_LAYER
  SCV_MODAL_APP_BASE_NAME
)

default_values=(
  "NIXPACKS_NODE_VERSION|22"
  "MODEL_PROVIDER|anthropic"
  "EMBEDDING_MODEL|text-embedding-3-small"
  "TRIBE_MODEL_ID|facebook/tribev2"
  "BRAIN2QWERTY_REPO|facebookresearch/brain2qwerty"
  "BRAINDECODE_MODEL_ID|braindecode/cbramod-pretrained"
  "MODAL_DEFAULT_GPU|A10G"
)

derived_values=(
  "SESSION_SUMMARY_MODEL|ANTHROPIC_MODEL_BULK"
)

has_doppler_key() {
  "$doppler_bin" secrets get "$1" \
    --project "$doppler_project" \
    --config "$doppler_config" \
    --plain >/dev/null 2>&1
}

read_env_file_key() {
  python3 - "$1" "${env_files[@]}" <<'PY'
from __future__ import annotations

import sys

key = sys.argv[1]
paths = sys.argv[2:]

for path in paths:
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        continue

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].strip()
        if "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if value:
            print(value, end="")
            raise SystemExit(0)

raise SystemExit(1)
PY
}

has_env_file_key() {
  [[ "${#env_files[@]}" -gt 0 ]] && read_env_file_key "$1" >/dev/null 2>&1
}

allow_env_file_fallback() {
  case "$1" in
    OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY|OPENROUTER_API_KEY|OPENROUTER_BASE_URL|VOYAGE_API_KEY|HF_TOKEN|HUGGINGFACE_TOKEN)
      return 0
      ;;
    MODEL_PROVIDER|SESSION_SUMMARY_MODEL|EMBEDDING_MODEL|ANTHROPIC_MODEL_JUDGE|ANTHROPIC_MODEL_BULK|GEMINI_MODEL_VIDEO|GEMINI_MODEL_JUDGE)
      return 0
      ;;
    TRIBE_MODEL_ID|TRIBE_MODEL_REVISION|TRIBE_GIT_REF|VJEPA_MODEL_ID|VJEPA_LARGE_MODEL_ID|INTERNVIDEO_MODEL_ID|QWEN_VL_MODEL_ID|WHISPER_MODEL_ID|FASTER_WHISPER_MODEL_ID)
      return 0
      ;;
    BRAIN2QWERTY_REPO|BRAIN2QWERTY_DATASET_ID|BRAINDECODE_MODEL_ID|SCV_OPEN_LLM_MODEL_ID|SCV_OPEN_LLM_ACTIVATION_LAYER|SCV_MODAL_APP_BASE_NAME)
      return 0
      ;;
    MODAL_WORKSPACE|MODAL_DEFAULT_GPU)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

set_railway_key_from_doppler() {
  local source_key="$1"
  local target_key="$2"

  if [[ "$dry_run" -eq 1 ]]; then
    echo "would set $target_key from Doppler $source_key"
    return
  fi

  "$doppler_bin" secrets get "$source_key" \
    --project "$doppler_project" \
    --config "$doppler_config" \
    --plain |
    "${railway_cmd[@]}" variable set "$target_key" --stdin "${railway_flags[@]}" >/dev/null
  echo "set $target_key from Doppler $source_key"
}

set_railway_key_from_env_file() {
  local source_key="$1"
  local target_key="$2"

  if [[ "$dry_run" -eq 1 ]]; then
    echo "would set $target_key from env file $source_key"
    return
  fi

  read_env_file_key "$source_key" |
    "${railway_cmd[@]}" variable set "$target_key" --stdin "${railway_flags[@]}" >/dev/null
  echo "set $target_key from env file $source_key"
}

set_railway_key_literal() {
  local key="$1"
  local value="$2"

  if [[ "$dry_run" -eq 1 ]]; then
    echo "would set default $key"
    return
  fi

  printf '%s' "$value" | "${railway_cmd[@]}" variable set "$key" --stdin "${railway_flags[@]}" >/dev/null
  echo "set default $key"
}

echo "syncing keys from Doppler $doppler_project/$doppler_config to Railway $railway_project/$railway_service/$railway_environment"

for key in "${source_keys[@]}"; do
  if has_doppler_key "$key"; then
    set_railway_key_from_doppler "$key" "$key"
  elif allow_env_file_fallback "$key" && has_env_file_key "$key"; then
    set_railway_key_from_env_file "$key" "$key"
  else
    echo "missing in configured sources: $key"
  fi
done

if has_doppler_key HF_TOKEN && ! has_doppler_key HUGGINGFACE_TOKEN && ! has_env_file_key HUGGINGFACE_TOKEN; then
  set_railway_key_from_doppler HF_TOKEN HUGGINGFACE_TOKEN
elif has_env_file_key HF_TOKEN && ! has_env_file_key HUGGINGFACE_TOKEN; then
  set_railway_key_from_env_file HF_TOKEN HUGGINGFACE_TOKEN
fi

for entry in "${default_values[@]}"; do
  key="${entry%%|*}"
  value="${entry#*|}"
  if has_doppler_key "$key"; then
    echo "default skipped, Doppler owns: $key"
  elif has_env_file_key "$key"; then
    echo "default skipped, env file owns: $key"
  else
    set_railway_key_literal "$key" "$value"
  fi
done

for entry in "${derived_values[@]}"; do
  target_key="${entry%%|*}"
  source_key="${entry#*|}"
  if has_doppler_key "$target_key" || has_env_file_key "$target_key"; then
    echo "derived value skipped, source already owns: $target_key"
  elif has_doppler_key "$source_key"; then
    set_railway_key_from_doppler "$source_key" "$target_key"
  elif has_env_file_key "$source_key"; then
    set_railway_key_from_env_file "$source_key" "$target_key"
  else
    echo "derived value missing source: $target_key from $source_key"
  fi
done

echo "sync complete"
