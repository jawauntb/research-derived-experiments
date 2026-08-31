"""Mirrors MIDAS tests/prompts/test_prompts.py: versioned load + caching,
StrictUndefined on missing template vars, clear_cache(). Requires jinja2
and pyyaml (prompts.py imports both unconditionally, lifted verbatim from
MIDAS — see prompts.py's header); skipped where either is unavailable."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("jinja2")
pytest.importorskip("yaml")

from model_manager.prompts import PromptManager


@pytest.fixture
def temp_prompts_dir(tmp_path):
    v1 = tmp_path / "proposer" / "claim_bundle" / "v1"
    v1.mkdir(parents=True)
    (v1 / "config.yaml").write_text("stop_sequences:\n  - 'END'\n")
    (v1 / "system.j2").write_text("You emit JSON claims only.")
    (v1 / "user.j2").write_text(
        "Question: {{ question }}\n"
        "{% if context_hints is defined %}Hints: {{ context_hints }}{% endif %}"
    )

    minimal = tmp_path / "minimal" / "test" / "v1"
    minimal.mkdir(parents=True)
    (minimal / "config.yaml").write_text("")
    (minimal / "system.j2").write_text("System.")
    (minimal / "user.j2").write_text("User: {{ input }}")

    return tmp_path


@pytest.fixture
def manager(temp_prompts_dir):
    return PromptManager(temp_prompts_dir)


def test_load_valid_prompt_with_config(manager):
    config = manager.load_prompt("proposer/claim_bundle@v1")
    assert config.name == "proposer/claim_bundle"
    assert config.version == "v1"
    assert config.stop_sequences == ["END"]
    assert config.ref == "proposer/claim_bundle@v1"


def test_load_prompt_without_config_file(manager, temp_prompts_dir):
    no_config = temp_prompts_dir / "bare" / "test" / "v1"
    no_config.mkdir(parents=True)
    (no_config / "system.j2").write_text("System.")
    (no_config / "user.j2").write_text("User: {{ input }}")

    config = manager.load_prompt("bare/test@v1")
    assert config.stop_sequences is None


def test_load_prompt_with_empty_config(manager):
    config = manager.load_prompt("minimal/test@v1")
    assert config.stop_sequences is None


def test_load_missing_prompt_raises(manager):
    with pytest.raises(FileNotFoundError, match="Prompt not found"):
        manager.load_prompt("proposer/claim_bundle@v99")


def test_load_missing_system_template_raises(manager, temp_prompts_dir):
    broken = temp_prompts_dir / "broken" / "test" / "v1"
    broken.mkdir(parents=True)
    (broken / "user.j2").write_text("User prompt")

    with pytest.raises(FileNotFoundError, match="Template file not found"):
        manager.load_prompt("broken/test@v1")


def test_invalid_reference_format_raises(manager):
    with pytest.raises(ValueError, match="Invalid prompt reference"):
        manager.load_prompt("proposer/claim_bundle")  # missing @version


def test_render_with_all_variables(manager):
    messages = manager.render(
        "proposer/claim_bundle@v1",
        {"question": "does A regulate B?", "context_hints": {"note": "synthetic"}},
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "does A regulate B?" in messages[1]["content"]


def test_render_missing_required_variable_raises(manager):
    with pytest.raises(ValueError, match="Missing required variable"):
        manager.render("proposer/claim_bundle@v1", {})


def test_caching(manager):
    c1 = manager.load_prompt("proposer/claim_bundle@v1")
    c2 = manager.load_prompt("proposer/claim_bundle@v1")
    assert c1 is c2


def test_clear_cache(manager):
    c1 = manager.load_prompt("proposer/claim_bundle@v1")
    assert "proposer/claim_bundle@v1" in manager._cache

    manager.clear_cache()
    assert manager._cache == {}

    c2 = manager.load_prompt("proposer/claim_bundle@v1")
    assert c1 is not c2
    assert c1.name == c2.name


def test_shipped_proposer_prompt_renders():
    """Sanity check against the actual prompts/ directory shipped in this
    repo, using the {question, evidence_records, context_hints} contract
    the task instructions specify for the proposer."""
    prompts_root = Path(__file__).resolve().parents[2] / "prompts"
    mgr = PromptManager(prompts_root)
    messages = mgr.render(
        "proposer/claim_bundle@v1",
        {
            "question": "does EXAMPLE-GENE-A regulate EXAMPLE-GENE-B?",
            "evidence_records": [
                {"id": "example_source:0001", "observation_type": "interventional"}
            ],
            "context_hints": {"note": "synthetic test fixture"},
        },
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "JSON" in messages[0]["content"]
    assert "example_source:0001" in messages[1]["content"]


def test_shipped_repairer_prompt_renders():
    """Sanity check the repairer prompt against the {failed_claim,
    fault_code, reasons, evidence_records} contract."""
    prompts_root = Path(__file__).resolve().parents[2] / "prompts"
    mgr = PromptManager(prompts_root)
    messages = mgr.render(
        "repairer/claim_repair@v1",
        {
            "failed_claim": {"claim_id": "x", "relation": "causes"},
            "fault_code": "CAUSALITY_OVERCLAIM",
            "reasons": ["observational record cannot license 'causes'"],
            "evidence_records": [{"id": "example_source:0002"}],
        },
    )
    assert len(messages) == 2
    assert "CAUSALITY_OVERCLAIM" in messages[1]["content"]
    assert "observational record cannot license 'causes'" in messages[1]["content"]
