# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md).
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

import yaml


CONFIG_DIR = Path(__file__).parent
DEFAULT_PROFILE = "local"
PROFILE_CONFIGS: Mapping[str, str] = {
    "local": "config.yaml",
    "hosted-openai": "config.hosted-openai.yaml",
}


def resolve_config_path() -> Path:
    explicit_path = os.getenv("MIDAS_CONFIG_PATH")
    if explicit_path:
        path = Path(explicit_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    profile = os.getenv("MODEL_CONFIG_PROFILE", DEFAULT_PROFILE)
    try:
        filename = PROFILE_CONFIGS[profile]
    except KeyError as exc:
        valid = ", ".join(sorted(PROFILE_CONFIGS))
        raise ValueError(
            f"Unknown MODEL_CONFIG_PROFILE '{profile}'. Expected one of: {valid}."
        ) from exc

    return CONFIG_DIR / filename


def validate_config_environment(config_path: Path) -> None:
    if not config_path.exists():
        raise FileNotFoundError(f"Model config not found: {config_path}")

    with config_path.open() as f:
        config = yaml.safe_load(f) or {}

    providers = config.get("providers", {})
    tasks = config.get("tasks", {})
    active_provider_names = {
        task_cfg.get("provider")
        for task_cfg in tasks.values()
        if isinstance(task_cfg, dict)
    }

    openai_tasks = [
        task_name
        for task_name, task_cfg in tasks.items()
        if isinstance(task_cfg, dict)
        and task_cfg.get("provider") == "openai"
    ]
    openai_settings = providers.get("openai", {}).get("settings", {})
    openai_key = openai_settings.get("api_key") or os.getenv("OPENAI_API_KEY")
    if "openai" in active_provider_names and not openai_key:
        task_list = ", ".join(sorted(openai_tasks))
        raise RuntimeError(
            "OPENAI_API_KEY is required because the selected model config "
            f"uses provider 'openai' for tasks: {task_list}."
        )


# ---------------------------------------------------------------------------
# MODEL-MANAGER-DECISION: `ProfileConfig` does not exist in upstream MIDAS
# src/config/profiles.py (lifted verbatim above, byte-for-byte identical
# except for this addition and the header comment). The Phase 4a task spec
# requires `model_manager/__init__.py` to export a `ProfileConfig` symbol,
# but upstream profiles.py only exposes free functions + module-level
# constants. Rather than rename anything in the verbatim body above, we add
# the minimal wrapper the export contract needs.
# ---------------------------------------------------------------------------
from dataclasses import dataclass  # noqa: E402


@dataclass(frozen=True)
class ProfileConfig:
    """Which named profile is active and the config path it resolves to."""

    profile: str
    config_path: Path


def resolve_profile_config() -> ProfileConfig:
    """Resolve the active profile name and its config path as one object."""
    profile = os.getenv("MODEL_CONFIG_PROFILE", DEFAULT_PROFILE)
    return ProfileConfig(profile=profile, config_path=resolve_config_path())
