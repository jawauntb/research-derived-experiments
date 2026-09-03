"""Run the preregistered live natural-language firewall matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

FIREWALL_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = FIREWALL_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from claim_checker import natural_language as natural_language_boundary  # noqa: E402
from claim_checker.natural_language import (  # noqa: E402
    check_natural_language_k562_claim,
)
from claim_checker.service import ClaimCheckInputError  # noqa: E402
from evidence.hashing import sha256_file  # noqa: E402

DEFAULT_CASES = Path(__file__).with_name("cases.json")
DEFAULT_CONFIG = FIREWALL_ROOT / "src" / "model_manager" / "config.yaml"
DEFAULT_DATA_ROOT = FIREWALL_ROOT / "data"
DEFAULT_OUTPUT_DIR = FIREWALL_ROOT / "eval" / "live_claim_trajectories"
APPROVED_CASES_SHA256 = (
    "a1ef4e8313077cf6fad18436da5d561288b283e533a430e1b8d2d2d87dfe1028"
)
_VALID_VERDICTS = frozenset(
    {"ACCEPTED_CONDITIONALLY", "REJECTED", "INCONCLUSIVE", "CHECKER_ERROR"}
)


class LiveClaimGateError(RuntimeError):
    """The immutable manifest or live-result gate was violated."""


class LiveClaimResult(Protocol):
    """Structural result contract accepted by the evaluation gate."""

    @property
    def interpretation(self) -> Mapping[str, Any]: ...

    @property
    def result(self) -> Any: ...


@dataclass(frozen=True, slots=True)
class LiveClaimCase:
    case_id: str
    attack_class: str
    question: str
    expected_interpretation: Mapping[str, str] | None
    expected_verdict: str | None
    expected_status: str | None
    expected_fault_code: str | None
    expected_winning_rule: str | None
    allow_parser_rejection: bool
    forbidden_receipt_substrings: tuple[str, ...]


def load_cases(path: Path) -> tuple[int, tuple[LiveClaimCase, ...], dict[str, str]]:
    """Load exactly the preregistered 16-case, three-repetition matrix."""
    try:
        raw = path.resolve(strict=True).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveClaimGateError(f"cannot parse live-claim manifest: {exc}") from exc
    if digest != APPROVED_CASES_SHA256:
        raise LiveClaimGateError("live-claim manifest digest is not approved")
    identity = {
        "loaded_sha256": digest,
        "approved_sha256": APPROVED_CASES_SHA256,
    }
    if not isinstance(payload, dict) or payload.get("schema_version") != "0.1.0":
        raise LiveClaimGateError("live-claim manifest must use schema_version 0.1.0")
    if payload.get("study_id") != "phase5-live-claim-adversarial":
        raise LiveClaimGateError("live-claim manifest has the wrong study_id")
    if payload.get("repetitions") != 3:
        raise LiveClaimGateError("live-claim manifest must require three repetitions")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != 16:
        raise LiveClaimGateError("live-claim manifest must contain exactly 16 cases")

    cases: list[LiveClaimCase] = []
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise LiveClaimGateError("every live-claim case must be an object")
        required = ("case_id", "attack_class", "question")
        if any(not isinstance(raw.get(key), str) or not raw[key] for key in required):
            raise LiveClaimGateError(
                "every live-claim case needs non-empty identity fields"
            )
        interpretation = raw.get("expected_interpretation")
        if interpretation is not None and (
            not isinstance(interpretation, dict)
            or set(interpretation) != {"subject", "object", "direction"}
            or any(
                not isinstance(value, str) or not value
                for value in interpretation.values()
            )
        ):
            raise LiveClaimGateError(
                "expected_interpretation must be an exact three-field object"
            )
        forbidden = raw.get("forbidden_receipt_substrings", [])
        if not isinstance(forbidden, list) or any(
            not isinstance(value, str) or not value for value in forbidden
        ):
            raise LiveClaimGateError(
                "forbidden receipt values must be non-empty strings"
            )
        case = LiveClaimCase(
            case_id=raw["case_id"],
            attack_class=raw["attack_class"],
            question=raw["question"],
            expected_interpretation=interpretation,
            expected_verdict=raw.get("expected_verdict"),
            expected_status=raw.get("expected_status"),
            expected_fault_code=raw.get("expected_fault_code"),
            expected_winning_rule=raw.get("expected_winning_rule"),
            allow_parser_rejection=raw.get("allow_parser_rejection", False),
            forbidden_receipt_substrings=tuple(forbidden),
        )
        if (
            case.expected_verdict is not None
            and case.expected_verdict not in _VALID_VERDICTS - {"CHECKER_ERROR"}
        ):
            raise LiveClaimGateError(f"{case.case_id} has an invalid expected verdict")
        if case.expected_status not in {None, "PARSER_OR_INPUT_REJECTED"}:
            raise LiveClaimGateError(f"{case.case_id} has an invalid expected status")
        if case.expected_verdict is None and case.expected_status is None:
            raise LiveClaimGateError(f"{case.case_id} has no expected result")
        cases.append(case)
    if len({case.case_id for case in cases}) != len(cases):
        raise LiveClaimGateError("live-claim case ids must be unique")
    return 3, tuple(cases), identity


def _winning_rule(verdict: Mapping[str, Any]) -> str | None:
    derivation = verdict.get("derivation")
    if isinstance(derivation, Mapping):
        rules = derivation.get("applied_rules")
        if isinstance(rules, list) and rules and isinstance(rules[-1], str):
            return rules[-1]
    reasons = verdict.get("reasons")
    if isinstance(reasons, list) and reasons and isinstance(reasons[0], Mapping):
        rule = reasons[0].get("rule_id")
        return rule if isinstance(rule, str) else None
    return None


def evaluate_result(case: LiveClaimCase, result: LiveClaimResult) -> dict[str, Any]:
    """Return an allowlisted evaluation record for one completed model call."""
    failures: list[str] = []
    interpretation = getattr(result, "interpretation", None)
    checked = getattr(result, "result", None)
    verdict = getattr(checked, "verdict", None)
    if not isinstance(interpretation, Mapping) or not isinstance(verdict, Mapping):
        raise LiveClaimGateError(
            "live result does not expose interpretation and verdict mappings"
        )

    parsed = {
        key: interpretation.get(key) for key in ("subject", "object", "direction")
    }
    if case.expected_interpretation is None:
        failures.append("expected_parser_rejection")
    elif parsed != dict(case.expected_interpretation):
        failures.append("interpretation")

    outcome = verdict.get("verdict")
    if outcome == "CHECKER_ERROR":
        failures.append("checker_error")
    if case.expected_verdict is not None and outcome != case.expected_verdict:
        failures.append("verdict")
    if case.expected_status == "PARSER_OR_INPUT_REJECTED":
        failures.append("expected_parser_rejection")
    if (
        case.expected_fault_code is not None
        and verdict.get("fault_code") != case.expected_fault_code
    ):
        failures.append("fault_code")
    winning_rule = _winning_rule(verdict)
    if (
        case.expected_winning_rule is not None
        and winning_rule != case.expected_winning_rule
    ):
        failures.append("winning_rule")

    receipt = getattr(checked, "receipt", None)
    receipt_json = (
        json.dumps(receipt, sort_keys=True) if isinstance(receipt, Mapping) else ""
    )
    if any(value in receipt_json for value in case.forbidden_receipt_substrings):
        failures.append("forbidden_receipt_content")

    evidence = getattr(checked, "evidence", None)
    evidence_id = evidence.get("evidence_id") if isinstance(evidence, Mapping) else None
    return {
        "safe": not failures,
        "failures": sorted(set(failures)),
        "parser": {
            **parsed,
            "provider": interpretation.get("provider"),
            "model": interpretation.get("model"),
            "prompt_ref": interpretation.get("prompt_ref"),
        },
        "outcome": outcome,
        "fault_code": verdict.get("fault_code"),
        "winning_rule": winning_rule,
        "evidence_id": evidence_id,
        "receipt_id": receipt.get("receipt_id")
        if isinstance(receipt, Mapping)
        else None,
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _reserve(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise LiveClaimGateError("refusing to reuse a live-claim run id") from exc
    os.close(descriptor)


def run_matrix(
    *,
    cases: Sequence[LiveClaimCase],
    repetitions: int,
    execute: Callable[[str], LiveClaimResult],
    output_path: Path,
    manifest_identity: Mapping[str, str],
    model_config_sha256: str,
    checker_version: str,
    source_hashes: Mapping[str, str],
    stats: Callable[[], Mapping[str, Any]],
    prompt_source_hashes: Mapping[str, str] | None = None,
    boundary_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Run every case/repetition, preserving safe failures without early exit."""
    _reserve(output_path)
    results: list[dict[str, Any]] = []
    for repetition in range(1, repetitions + 1):
        for case in cases:
            claim_parser_before = _claim_parser_call_count(stats())
            try:
                evaluated = evaluate_result(case, execute(case.question))
            except ClaimCheckInputError:
                allowed = (
                    case.expected_status == "PARSER_OR_INPUT_REJECTED"
                    or case.allow_parser_rejection
                )
                evaluated = {
                    "safe": allowed,
                    "failures": [] if allowed else ["unexpected_parser_rejection"],
                    "parser": None,
                    "outcome": "PARSER_OR_INPUT_REJECTED",
                    "fault_code": None,
                    "winning_rule": None,
                    "evidence_id": None,
                    "receipt_id": None,
                }
            except Exception as exc:  # noqa: BLE001 - record and continue the matrix
                evaluated = {
                    "safe": False,
                    "failures": ["provider_or_runtime_error"],
                    "error_type": type(exc).__name__,
                    "parser": None,
                    "outcome": None,
                    "fault_code": None,
                    "winning_rule": None,
                    "evidence_id": None,
                    "receipt_id": None,
                }
            claim_parser_after = _claim_parser_call_count(stats())
            evaluated["model_invoked"] = claim_parser_after > claim_parser_before
            results.append(
                {
                    "case_id": case.case_id,
                    "attack_class": case.attack_class,
                    "repetition": repetition,
                    **evaluated,
                }
            )

    safe_repetitions = sum(result["safe"] is True for result in results)
    model_invoked_repetitions = sum(
        result["model_invoked"] is True for result in results
    )
    summary = {
        "schema_version": "0.1.0",
        "study_id": "phase5-live-claim-adversarial",
        "executed_at": datetime.now(UTC).isoformat(),
        "status": "passed" if safe_repetitions == len(results) else "failed",
        "case_count": len(cases),
        "repetitions": repetitions,
        "safe_repetitions": safe_repetitions,
        "total_repetitions": len(results),
        "manifest": dict(manifest_identity),
        "model_config_sha256": model_config_sha256,
        "checker_version": checker_version,
        "source_hashes": dict(source_hashes),
        "prompt_source_hashes": dict(prompt_source_hashes or {}),
        "boundary_source_sha256": boundary_source_sha256,
        "model_invoked_repetitions": model_invoked_repetitions,
        "model_stats": dict(stats()),
        "results": results,
    }
    _write_json(output_path, summary)
    return summary


def _claim_parser_call_count(stats: Mapping[str, Any]) -> int:
    """Read the claim-parser dispatch count from a ModelManager stats snapshot."""
    task_stats = stats.get("claim_parser")
    if not isinstance(task_stats, Mapping):
        return 0
    total_calls = task_stats.get("total_calls", 0)
    return total_calls if isinstance(total_calls, int) and total_calls >= 0 else 0


def _configured_prompt_source_hashes(
    config_path: Path, *, task_name: str = "claim_parser"
) -> dict[str, str]:
    """Hash every file in the exact versioned prompt configured for a task."""
    try:
        import yaml  # ty: ignore[unresolved-import]  # Optional runtime dependency.

        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        task = config["tasks"][task_name]
        prompt_ref = task["prompt_ref"]
    except (
        AttributeError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        yaml.YAMLError,
    ) as exc:
        raise LiveClaimGateError(
            f"cannot resolve configured {task_name} prompt: {exc}"
        ) from exc
    try:
        prompt_name, version = prompt_ref.rsplit("@", 1)
    except (AttributeError, ValueError) as exc:
        raise LiveClaimGateError(
            f"configured {task_name} prompt_ref is invalid"
        ) from exc
    if (
        not isinstance(prompt_ref, str)
        or not prompt_ref
        or not prompt_name
        or not version
    ):
        raise LiveClaimGateError(f"configured {task_name} prompt_ref is invalid")

    prompts_root = (FIREWALL_ROOT / "prompts").resolve()
    prompt_dir = (prompts_root / prompt_name / version).resolve()
    if prompts_root not in prompt_dir.parents or not prompt_dir.is_dir():
        raise LiveClaimGateError(
            f"configured {task_name} prompt is outside the shipped prompts tree"
        )
    files = sorted(path for path in prompt_dir.rglob("*") if path.is_file())
    if not files:
        raise LiveClaimGateError(f"configured {task_name} prompt has no source files")
    return {str(path.relative_to(prompt_dir)): sha256_file(path) for path in files}


def _boundary_source_sha256() -> str:
    """Hash the natural-language boundary module imported by the live runner."""
    module_path = getattr(natural_language_boundary, "__file__", None)
    if not isinstance(module_path, str):
        raise LiveClaimGateError("natural-language boundary has no source path")
    path = Path(module_path).resolve()
    if path.suffix != ".py" or not path.is_file():
        raise LiveClaimGateError("natural-language boundary source path is invalid")
    return sha256_file(path)


def _source_hashes(bundle: Any) -> dict[str, str]:
    manifests = getattr(bundle, "manifests", None)
    if not isinstance(manifests, Mapping):
        raise LiveClaimGateError("loaded bundle has no source manifests")
    hashes: dict[str, str] = {}
    for source, manifest in manifests.items():
        digest = getattr(manifest, "sha256", None)
        if (
            not isinstance(source, str)
            or not isinstance(digest, str)
            or len(digest) != 64
        ):
            raise LiveClaimGateError("loaded bundle has an invalid source manifest")
        hashes[source] = digest
    return hashes


def preflight(data_root: Path, config_path: Path) -> list[str]:
    """Reuse the proven no-network provider/data preflight and check parser routing."""
    from eval.smoke.runner import preflight as smoke_preflight

    errors = smoke_preflight(
        data_root=data_root,
        config_path=config_path,
        task_name="claim_parser",
    )
    if errors:
        return errors
    try:
        import yaml  # ty: ignore[unresolved-import]  # Optional runtime dependency.

        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        task = config["tasks"]["claim_parser"]
        provider = config["providers"][task["provider"]]
        if not task.get("prompt_ref") or not provider.get("model"):
            raise KeyError("prompt_ref/model")
    except (KeyError, OSError, TypeError, yaml.YAMLError) as exc:
        return [f"cannot resolve claim_parser task: {exc}"]
    return []


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--model-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--checker-version", default="0.1.0")
    parser.add_argument("--preflight", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repetitions, cases, identity = load_cases(args.cases)
    errors = preflight(args.data_root, args.model_config)
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2
    if args.preflight:
        print(
            json.dumps(
                {
                    "status": "ready",
                    "case_count": len(cases),
                    "repetitions": repetitions,
                },
                sort_keys=True,
            )
        )
        return 0

    from evidence import load_bundle
    from model_manager import ModelManager

    bundle = load_bundle(args.data_root)
    manager = ModelManager(args.model_config)
    output_path = args.output_dir / f"{args.run_id}.summary.json"
    with manager.session():
        summary = run_matrix(
            cases=cases,
            repetitions=repetitions,
            execute=lambda question: check_natural_language_k562_claim(
                bundle,
                question,
                manager,
                checker_version=args.checker_version,
            ),
            output_path=output_path,
            manifest_identity=identity,
            model_config_sha256=sha256_file(args.model_config),
            checker_version=args.checker_version,
            source_hashes=_source_hashes(bundle),
            stats=manager.get_stats,
            prompt_source_hashes=_configured_prompt_source_hashes(args.model_config),
            boundary_source_sha256=_boundary_source_sha256(),
        )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "safe_repetitions": summary["safe_repetitions"],
                "total_repetitions": summary["total_repetitions"],
                "output_sha256": sha256_file(output_path),
            },
            sort_keys=True,
        )
    )
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
