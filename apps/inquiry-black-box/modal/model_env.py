from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

EnvMap = Mapping[str, str | None]

SECRET_ENV_KEYS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "OPENROUTER_API_KEY",
    "VOYAGE_API_KEY",
    "HF_TOKEN",
    "HUGGINGFACE_TOKEN",
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    "INQUIRY_CLOUD_AUTH_SECRET",
    "SYNC_ENCRYPTION_KEY",
    "DATABASE_URL",
    "MODAL_JOB_WEBHOOK_TOKEN",
)

RAILWAY_DEPLOY_ENV_KEYS = (
    "NIXPACKS_NODE_VERSION",
    "INQUIRY_CLOUD_AUTH_SECRET",
    "DATABASE_URL",
    "RAILWAY_PUBLIC_API_URL",
    "SYNC_ENCRYPTION_KEY",
    "MODAL_JOB_WEBHOOK_URL",
    "MODAL_JOB_WEBHOOK_TOKEN",
    "MODAL_JOB_TIMEOUT_MS",
)

MODAL_DEPLOY_ENV_KEYS = (
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    "MODAL_ENVIRONMENT",
    "MODAL_REGION",
    "MODAL_WORKSPACE",
    "MODAL_DEFAULT_GPU",
)

MODEL_ROUTING_ENV_KEYS = (
    "MODEL_PROVIDER",
    "SESSION_SUMMARY_MODEL",
    "EMBEDDING_MODEL",
    "ANTHROPIC_MODEL_JUDGE",
    "ANTHROPIC_MODEL_BULK",
    "GEMINI_MODEL_VIDEO",
    "GEMINI_MODEL_JUDGE",
    "OPENROUTER_BASE_URL",
)

RESEARCH_MODEL_ENV_KEYS = (
    "TRIBE_MODEL_ID",
    "TRIBE_MODEL_REVISION",
    "TRIBE_GIT_REF",
    "VJEPA_MODEL_ID",
    "VJEPA_LARGE_MODEL_ID",
    "INTERNVIDEO_MODEL_ID",
    "QWEN_VL_MODEL_ID",
    "WHISPER_MODEL_ID",
    "FASTER_WHISPER_MODEL_ID",
    "BRAIN2QWERTY_REPO",
    "BRAIN2QWERTY_DATASET_ID",
    "BRAINDECODE_MODEL_ID",
    "BBBD_CACHE_DIR",
    "SCV_OPEN_LLM_MODEL_ID",
    "SCV_OPEN_LLM_ACTIVATION_LAYER",
    "SCV_MODAL_APP_BASE_NAME",
)

DEFAULT_RESEARCH_MODELS = {
    "TRIBE_MODEL_ID": "facebook/tribev2",
    "BRAIN2QWERTY_REPO": "facebookresearch/brain2qwerty",
    "BRAINDECODE_MODEL_ID": "braindecode/cbramod-pretrained",
}


def resolve_model_environment(env: EnvMap | None = None) -> dict[str, Any]:
    source = env or os.environ
    hf_token_key = first_configured_key(source, ("HF_TOKEN", "HUGGINGFACE_TOKEN"))

    return {
        "version": "model_env@0.1.0",
        "routing": {
            "provider": first_value(source, ("MODEL_PROVIDER",), "auto"),
            "session_summary_model": first_value(source, ("SESSION_SUMMARY_MODEL",)),
            "embedding_model": first_value(source, ("EMBEDDING_MODEL",)),
        },
        "providers": {
            "openai": provider_status(source, ("OPENAI_API_KEY",)),
            "anthropic": provider_status(
                source,
                ("ANTHROPIC_API_KEY",),
                model_keys=("ANTHROPIC_MODEL_BULK", "ANTHROPIC_MODEL_JUDGE"),
            ),
            "google": provider_status(
                source,
                ("GOOGLE_API_KEY",),
                model_keys=("GEMINI_MODEL_VIDEO", "GEMINI_MODEL_JUDGE"),
            ),
            "openrouter": provider_status(
                source,
                ("OPENROUTER_API_KEY",),
                extra_config_keys=("OPENROUTER_BASE_URL",),
            ),
            "voyage": provider_status(source, ("VOYAGE_API_KEY",)),
            "huggingface": provider_status(source, ("HF_TOKEN", "HUGGINGFACE_TOKEN")),
        },
        "research_models": {
            "tribe": {
                "model_id": first_value(source, ("TRIBE_MODEL_ID",), DEFAULT_RESEARCH_MODELS["TRIBE_MODEL_ID"]),
                "revision_configured": configured(source, "TRIBE_MODEL_REVISION"),
                "git_ref_configured": configured(source, "TRIBE_GIT_REF"),
                "huggingface_token_key": hf_token_key,
            },
            "brain2qwerty": {
                "repo": first_value(source, ("BRAIN2QWERTY_REPO",), DEFAULT_RESEARCH_MODELS["BRAIN2QWERTY_REPO"]),
                "dataset_configured": configured(source, "BRAIN2QWERTY_DATASET_ID"),
                "huggingface_token_key": hf_token_key,
                "license_gate": "research-only until data/model license allows product use",
            },
            "braindecode": {
                "model_id": first_value(
                    source,
                    ("BRAINDECODE_MODEL_ID",),
                    DEFAULT_RESEARCH_MODELS["BRAINDECODE_MODEL_ID"],
                ),
                "huggingface_token_key": hf_token_key,
            },
            "bbbd": {
                "cache_dir_configured": configured(source, "BBBD_CACHE_DIR"),
            },
            "video_audio": model_id_status(
                source,
                (
                    "VJEPA_MODEL_ID",
                    "VJEPA_LARGE_MODEL_ID",
                    "INTERNVIDEO_MODEL_ID",
                    "QWEN_VL_MODEL_ID",
                    "WHISPER_MODEL_ID",
                    "FASTER_WHISPER_MODEL_ID",
                ),
            ),
            "social_cohesion_vectors": model_id_status(
                source,
                (
                    "SCV_OPEN_LLM_MODEL_ID",
                    "SCV_OPEN_LLM_ACTIVATION_LAYER",
                    "SCV_MODAL_APP_BASE_NAME",
                ),
            ),
        },
        "deploy": {
            "railway": {
                "configured_keys": configured_keys(source, RAILWAY_DEPLOY_ENV_KEYS),
                "missing_keys": missing_keys(source, RAILWAY_DEPLOY_ENV_KEYS),
            },
            "modal": {
                "configured_keys": configured_keys(source, MODAL_DEPLOY_ENV_KEYS),
                "missing_keys": missing_keys(source, MODAL_DEPLOY_ENV_KEYS),
            },
        },
        "configured_known_keys": configured_keys(
            source,
            (
                *SECRET_ENV_KEYS,
                *RAILWAY_DEPLOY_ENV_KEYS,
                *MODAL_DEPLOY_ENV_KEYS,
                *MODEL_ROUTING_ENV_KEYS,
                *RESEARCH_MODEL_ENV_KEYS,
            ),
        ),
    }


def provider_status(
    env: EnvMap,
    secret_keys: Sequence[str],
    *,
    model_keys: Sequence[str] = (),
    extra_config_keys: Sequence[str] = (),
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "configured": any(configured(env, key) for key in (*secret_keys, *extra_config_keys)),
        "configured_secret_keys": configured_keys(env, secret_keys),
    }
    models = model_id_status(env, model_keys)
    if models:
        status["models"] = models
    extra = configured_keys(env, extra_config_keys)
    if extra:
        status["configured_extra_keys"] = extra
    return status


def model_id_status(env: EnvMap, keys: Sequence[str]) -> dict[str, str]:
    models: dict[str, str] = {}
    for key in keys:
        value = clean_value(env.get(key))
        if value:
            models[key] = value
    return models


def configured(env: EnvMap, key: str) -> bool:
    return clean_value(env.get(key)) is not None


def configured_keys(env: EnvMap, keys: Sequence[str]) -> list[str]:
    return sorted({key for key in keys if configured(env, key)})


def missing_keys(env: EnvMap, keys: Sequence[str]) -> list[str]:
    return sorted({key for key in keys if not configured(env, key)})


def first_configured_key(env: EnvMap, keys: Sequence[str]) -> str | None:
    for key in keys:
        if configured(env, key):
            return key
    return None


def first_value(env: EnvMap, keys: Sequence[str], default: str | None = None) -> str | None:
    for key in keys:
        value = clean_value(env.get(key))
        if value:
            return value
    return default


def clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
