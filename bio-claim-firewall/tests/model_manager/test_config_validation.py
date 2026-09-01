"""Mirrors MIDAS tests/manager/test_model_manager.py's config-validation
tests; fixtures rewritten for bio-claim-firewall's flat provider-config
shape (model lives on the provider entry, not the task — see
config.yaml / manager.py's module docstring)."""

from __future__ import annotations

import pytest

pytest.importorskip("yaml")

from model_manager.manager import ModelManager


def _write(tmp_path, text):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(text)
    return config_file


def test_config_file_not_found(tmp_path):
    missing = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError, match="Config not found"):
        ModelManager(missing)


def test_config_missing_providers_section(tmp_path):
    cfg = _write(
        tmp_path,
        """
tasks:
  proposer:
    provider: fake_provider
""",
    )
    with pytest.raises(ValueError, match="Config missing 'providers'"):
        ModelManager(cfg)


def test_config_missing_tasks_section(tmp_path):
    cfg = _write(
        tmp_path,
        """
providers:
  fake_provider:
    type: fake
    model: fake-model
""",
    )
    with pytest.raises(ValueError, match="Config missing 'tasks'"):
        ModelManager(cfg)


def test_provider_missing_type(tmp_path):
    cfg = _write(
        tmp_path,
        """
providers:
  fake_provider:
    model: fake-model

tasks:
  proposer:
    provider: fake_provider
""",
    )
    with pytest.raises(ValueError, match="Provider 'fake_provider' missing type"):
        ModelManager(cfg)


def test_task_missing_provider(tmp_path):
    cfg = _write(
        tmp_path,
        """
providers:
  fake_provider:
    type: fake
    model: fake-model

tasks:
  proposer:
    prompt_ref: proposer/claim_bundle@v1
""",
    )
    with pytest.raises(ValueError, match="Task 'proposer' missing provider"):
        ModelManager(cfg)


def test_task_unknown_provider(tmp_path):
    """A task referencing a provider name that's simply not declared."""
    cfg = _write(
        tmp_path,
        """
providers:
  fake_provider:
    type: fake
    model: fake-model

tasks:
  proposer:
    provider: unknown_provider
""",
    )
    with pytest.raises(
        ValueError,
        match="Task 'proposer' references unknown provider 'unknown_provider'",
    ):
        ModelManager(cfg)


def test_task_undefined_provider_ref_no_providers_declared(tmp_path):
    """An 'undefined provider ref' variant: providers section exists but
    is simply empty, still must raise on the task's dangling reference."""
    cfg = _write(
        tmp_path,
        """
providers: {}

tasks:
  proposer:
    provider: openai_gpt4o_mini
""",
    )
    with pytest.raises(
        ValueError,
        match="Task 'proposer' references unknown provider 'openai_gpt4o_mini'",
    ):
        ModelManager(cfg)


def test_valid_config_loads(config_path):
    mgr = ModelManager(config_path)
    assert mgr.config_path == config_path
    assert "providers" in mgr.config
    assert "tasks" in mgr.config
    assert mgr.config["tasks"]["proposer"]["provider"] == "fake_provider"
    assert mgr._providers == {}
    assert mgr._stats == {}


def test_real_config_yaml_is_valid():
    """The actual config.yaml shipped with this package must itself pass
    validation (providers declared, tasks resolve to real providers)."""
    from pathlib import Path

    real_config = (
        Path(__file__).resolve().parents[2] / "src" / "model_manager" / "config.yaml"
    )
    mgr = ModelManager(real_config)
    assert set(mgr.config["tasks"]) == {"claim_parser", "proposer", "repairer"}
    for task_name, task_cfg in mgr.config["tasks"].items():
        assert task_cfg["provider"] in mgr.config["providers"]
    assert "checker" not in mgr.config["tasks"]
