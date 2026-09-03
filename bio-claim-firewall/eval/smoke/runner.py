"""Run the preregistered Phase 5 live-model smoke study.

The runner deliberately calls only the untrusted proposer and the deterministic
verifier.  ``max_repair_attempts=0`` prevents repair calls from confounding this
first integration test while retaining the existing append-only trajectory format.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_FIREWALL_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _FIREWALL_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


_REQUIRED_SOURCES = (
    "hgnc.2026_pilot",
    "ncbitaxon.2026_pilot",
    "cellontology.2026_pilot",
    "cellline.2026_pilot",
    "reactome.2026_pilot",
    "perturbseq.replogle_2022",
)
_VALID_VERDICTS = frozenset(
    {"ACCEPTED_CONDITIONALLY", "REJECTED", "INCONCLUSIVE", "CHECKER_ERROR"}
)
_DEFAULT_DATA_ROOT = _FIREWALL_ROOT / "data"
_DEFAULT_CONFIG = _FIREWALL_ROOT / "src" / "model_manager" / "config.yaml"
_DEFAULT_QUESTIONS = Path(__file__).with_name("questions.json")
_DEFAULT_OUTPUT_DIR = _FIREWALL_ROOT / "eval" / "smoke_trajectories"
# This digest freezes the exact five-question preregistration.  A caller may
# place an identical copy elsewhere, but may not silently substitute cases.
_APPROVED_QUESTIONS_SHA256 = (
    "1fcb624198bb00a1f3c8b7cbddba4932ff4a63345b5d83acd378e12a423f13b7"
)


class SmokeGateError(RuntimeError):
    """A fatal preregistered smoke-study gate did not pass."""


@dataclass(frozen=True, slots=True)
class SmokeCase:
    case_id: str
    question: str
    subject_id: str
    object_id: str
    effect_sign: str


def _questions_manifest_identity(path: Path) -> dict[str, str]:
    """Verify and describe the immutable five-case study manifest."""
    try:
        resolved_path = path.resolve(strict=True)
        digest = hashlib.sha256(resolved_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise SmokeGateError(f"cannot read smoke manifest {path}: {exc}") from exc

    if digest != _APPROVED_QUESTIONS_SHA256:
        raise SmokeGateError(
            "smoke manifest digest does not match the approved bundled questions.json"
        )
    return {
        "approved_path": str(_DEFAULT_QUESTIONS.resolve()),
        "approved_sha256": _APPROVED_QUESTIONS_SHA256,
        "loaded_path": str(resolved_path),
        "loaded_sha256": digest,
    }


def load_cases(path: Path) -> tuple[SmokeCase, ...]:
    """Load exactly five hand-authored cases from the frozen study manifest."""
    _questions_manifest_identity(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SmokeGateError(f"cannot load smoke manifest {path}: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("schema_version") != "0.1.0":
        raise SmokeGateError(
            "smoke manifest must be a schema_version 0.1.0 JSON object"
        )
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != 5:
        raise SmokeGateError("smoke manifest must contain exactly five cases")

    cases: list[SmokeCase] = []
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict) or not isinstance(
            raw_case.get("selector"), dict
        ):
            raise SmokeGateError(
                "each smoke case must contain an object-valued selector"
            )
        selector = raw_case["selector"]
        fields = {
            "case_id": raw_case.get("case_id"),
            "question": raw_case.get("question"),
            "subject_id": selector.get("subject_id"),
            "object_id": selector.get("object_id"),
            "effect_sign": selector.get("effect_sign"),
        }
        if not all(isinstance(value, str) and value for value in fields.values()):
            raise SmokeGateError(
                "each smoke case must use non-empty string identifiers and question"
            )
        if fields["effect_sign"] not in {"positive", "negative"}:
            raise SmokeGateError(
                "each smoke case effect_sign must be positive or negative"
            )
        cases.append(SmokeCase(**fields))

    if len({case.case_id for case in cases}) != len(cases):
        raise SmokeGateError("smoke case ids must be unique")
    return tuple(cases)


def _missing_data_sources(data_root: Path) -> list[str]:
    missing: list[str] = []
    for source in _REQUIRED_SOURCES:
        has_manifest = any(
            (data_root / "manifests" / f"{source}.{suffix}").is_file()
            for suffix in ("json", "yaml")
        )
        has_snapshot = (data_root / "ontology_snapshots" / source).is_dir() or (
            data_root / "evidence_records" / source / "records.jsonl"
        ).is_file()
        if not (has_manifest and has_snapshot):
            missing.append(source)
    return missing


def _provider_preflight(
    config_path: Path,
    environ: Mapping[str, str],
    *,
    task_name: str = "proposer",
) -> list[str]:
    errors: list[str] = []
    if not config_path.is_file():
        return [f"model config does not exist: {config_path}"]
    if importlib.util.find_spec("yaml") is None:
        return ["missing optional dependency PyYAML; rerun with --with pyyaml"]

    import yaml  # ty: ignore[unresolved-import]  # Optional runtime dependency.

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        task = config["tasks"][task_name]
        provider = config["providers"][task["provider"]]
        provider_type = provider["type"]
    except (KeyError, OSError, TypeError, yaml.YAMLError) as exc:
        return [f"cannot read {task_name} provider from {config_path}: {exc}"]

    required_packages = {"jinja2", "pydantic"}
    if provider_type == "openai_sdk":
        # Keep this in lockstep with ``OpenAIProvider``'s guarded import.
        # Checking only the SDK lets preflight report ready even though the
        # first provider initialization must fail before an API request.
        required_packages.update({"openai", "httpx", "tenacity", "truststore"})
    elif provider_type == "ollama":
        # ``OllamaProvider`` has the same guarded-import boundary for its
        # transport and retry dependencies.
        required_packages.update({"ollama", "httpx", "tenacity"})
    else:
        errors.append(f"unsupported smoke-study provider type: {provider_type!r}")

    for package in sorted(required_packages):
        if importlib.util.find_spec(package) is None:
            errors.append(f"missing optional dependency {package}")

    api_key_env = provider.get("api_key_env")
    if isinstance(api_key_env, str) and not environ.get(api_key_env):
        errors.append(f"configured provider credential is absent: {api_key_env}")
    return errors


def preflight(
    *,
    data_root: Path,
    config_path: Path,
    environ: Mapping[str, str] | None = None,
    task_name: str = "proposer",
) -> list[str]:
    """Return every missing local prerequisite without making a network call."""
    errors = _provider_preflight(
        config_path,
        os.environ if environ is None else environ,
        task_name=task_name,
    )
    missing_sources = _missing_data_sources(data_root)
    if missing_sources:
        errors.append("missing frozen pilot sources: " + ", ".join(missing_sources))
        return errors

    try:
        from evidence import load_bundle

        load_bundle(data_root)
    except Exception as exc:  # noqa: BLE001 - loader owns all hash failures
        errors.append(f"frozen pilot snapshot did not load hash-verified: {exc}")
    return errors


def evidence_for_case(bundle: Any, case: SmokeCase) -> dict[str, Any]:
    """Resolve one real, uniquely selected Replogle record for a smoke case."""
    matches = [
        record
        for record in bundle.ledger.list_by(case.subject_id, case.object_id)
        if record.get("effect", {}).get("sign") == case.effect_sign
    ]
    if len(matches) != 1:
        raise SmokeGateError(
            f"{case.case_id} selector must resolve exactly one frozen evidence record; got {len(matches)}"
        )
    return matches[0]


def assert_verdict_gates(bundle: Any, verdicts: Sequence[dict[str, Any]]) -> None:
    """Apply the operational smoke gates to deterministic verifier output."""
    if not verdicts:
        raise SmokeGateError("a smoke case produced no verifier verdict")
    for verdict in verdicts:
        if not isinstance(verdict, dict):
            raise SmokeGateError("verifier returned a non-object verdict")
        kind = verdict.get("verdict")
        if kind not in _VALID_VERDICTS:
            raise SmokeGateError(f"verifier returned an unknown verdict: {kind!r}")
        if kind == "CHECKER_ERROR":
            raise SmokeGateError(
                f"verifier CHECKER_ERROR: {verdict.get('checker_error')!r}"
            )
        if kind == "ACCEPTED_CONDITIONALLY":
            derivation = verdict.get("derivation")
            if not isinstance(derivation, dict):
                raise SmokeGateError("accepted claim is missing its derivation")
            evidence_ids = derivation.get("evidence_ids")
            if not isinstance(evidence_ids, list) or not evidence_ids:
                raise SmokeGateError(
                    "accepted claim derivation must cite at least one evidence id"
                )
            for evidence_id in evidence_ids:
                if not isinstance(evidence_id, str) or not evidence_id:
                    raise SmokeGateError(
                        "accepted claim derivation has an invalid evidence id"
                    )
                try:
                    bundle.ledger.get(evidence_id)
                except Exception as exc:
                    raise SmokeGateError(
                        f"accepted claim derivation cites unresolved evidence id: {evidence_id!r}"
                    ) from exc


def _trajectory_for_result(trajectory_path: Path, trajectory_id: str) -> dict[str, Any]:
    """Read the one durable trajectory that belongs to a smoke-case result."""
    try:
        lines = trajectory_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SmokeGateError(
            f"missing trajectory receipt for {trajectory_id}: {exc}"
        ) from exc

    matching: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SmokeGateError(f"malformed trajectory receipt: {exc}") from exc
        if isinstance(record, dict) and record.get("trajectory_id") == trajectory_id:
            matching.append(record)
    if len(matching) != 1:
        raise SmokeGateError(
            f"expected one durable trajectory receipt for {trajectory_id}; got {len(matching)}"
        )
    return matching[0]


def assert_schema_valid_proposed_claims(trajectory: Mapping[str, Any]) -> None:
    """Require every model-proposed claim in a case receipt to satisfy the full schema."""
    attempts = trajectory.get("attempts")
    if not isinstance(attempts, list):
        raise SmokeGateError("trajectory receipt must contain an attempts list")

    proposed_claims: list[dict[str, Any]] = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            raise SmokeGateError("trajectory receipt contains a non-object attempt")
        if attempt.get("stage") == "propose":
            claim = attempt.get("proposed_claim")
            if not isinstance(claim, dict):
                raise SmokeGateError(
                    "trajectory proposer attempt is missing its claim object"
                )
            proposed_claims.append(claim)
    if not proposed_claims:
        raise SmokeGateError("smoke case has no durable proposed claims to validate")

    from verifier.schema import load_claim_schema, validate_claim

    schema = load_claim_schema(_FIREWALL_ROOT / "spec")
    for claim in proposed_claims:
        failure = validate_claim(claim, schema)
        if failure is not None:
            raise SmokeGateError(
                "model proposed a claim that is not schema-valid: "
                f"{failure.field_path or '<root>'} ({failure.constraint_kind})"
            )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _source_manifest_hashes(bundle: Any) -> dict[str, str]:
    """Return the complete six-source snapshot identity required by the study."""
    manifests = getattr(bundle, "manifests", None)
    if not isinstance(manifests, Mapping):
        raise SmokeGateError("loaded pilot bundle does not expose source manifests")

    expected_sources = set(_REQUIRED_SOURCES)
    actual_sources = set(manifests)
    if actual_sources != expected_sources:
        missing = sorted(expected_sources - actual_sources)
        unexpected = sorted(
            repr(source) for source in actual_sources - expected_sources
        )
        raise SmokeGateError(
            "loaded pilot bundle manifest sources differ from the preregistered six: "
            f"missing={missing}, unexpected={unexpected}"
        )

    hashes: dict[str, str] = {}
    for source in _REQUIRED_SOURCES:
        manifest = manifests.get(source)
        sha256 = getattr(manifest, "sha256", None)
        if not isinstance(sha256, str) or len(sha256) != 64:
            raise SmokeGateError(
                f"loaded pilot bundle is missing a valid manifest hash for {source}"
            )
        hashes[source] = sha256
    return hashes


def _reservation_path(trajectory_path: Path, summary_path: Path) -> Path:
    trajectory_path = trajectory_path.resolve()
    summary_path = summary_path.resolve()
    expected_summary = trajectory_path.with_suffix(".summary.json")
    if summary_path != expected_summary:
        raise SmokeGateError(
            "trajectory and summary paths must share one run id and output directory"
        )
    # The ignored summary artifact is the reservation itself.  This avoids
    # creating a third, untracked lock-file type while preserving the same
    # run-id after a process dies between model calls and final summary.
    return summary_path


def _reserve_run(trajectory_path: Path, summary_path: Path) -> Path:
    """Atomically reserve one run-id before either receipt artifact can be written."""
    reservation_path = _reservation_path(trajectory_path, summary_path)
    trajectory_path.parent.mkdir(parents=True, exist_ok=True)
    if trajectory_path.exists():
        raise SmokeGateError("refusing to mix runs: choose an unused run id")

    try:
        descriptor = os.open(
            str(reservation_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
        )
    except FileExistsError as exc:
        raise SmokeGateError("refusing to mix runs: choose an unused run id") from exc
    try:
        os.write(
            descriptor, b'{"status":"reserved","study_id":"phase5-live-model-smoke"}\n'
        )
    finally:
        os.close(descriptor)

    # A normal runner always reserves before writing.  Rechecking closes the
    # remaining race with an older/manual writer that did not follow that
    # contract.  Preserve this reservation if that race occurs: it prevents
    # a later run from mixing a fresh summary with the manual trajectory.
    if trajectory_path.exists():
        raise SmokeGateError("refusing to mix runs: choose an unused run id")
    return reservation_path


def _summary_base(
    *,
    cases: Sequence[SmokeCase],
    data_root: Path,
    config_path: Path,
    questions_path: Path,
    checker_version: str,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "study_id": "phase5-live-model-smoke",
        "executed_at": datetime.now(UTC).isoformat(),
        "case_ids": [case.case_id for case in cases],
        "data_root": str(data_root),
        "model_config": str(config_path),
        "model_config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "questions_manifest": _questions_manifest_identity(questions_path),
        "checker_version": checker_version,
    }


def run_smoke(
    *,
    data_root: Path,
    config_path: Path,
    cases: Sequence[SmokeCase],
    trajectory_path: Path,
    summary_path: Path,
    checker_version: str,
    questions_path: Path = _DEFAULT_QUESTIONS,
) -> dict[str, Any]:
    """Execute five proposer-to-verifier cases and write durable local receipts."""
    _reserve_run(trajectory_path, summary_path)
    from evidence import load_bundle
    from model_manager import ModelManager
    from orchestrator import Orchestrator, OrchestratorConfig
    from proposer import Proposer
    from repairer import Repairer
    from verifier.config import VerifierConfig

    bundle = load_bundle(data_root)
    manager = ModelManager(config_path)
    orchestrator = Orchestrator(
        Proposer(manager),
        Repairer(manager),
        VerifierConfig(checker_version=checker_version),
        bundle,
        OrchestratorConfig(max_repair_attempts=0, trajectory_path=trajectory_path),
    )
    summary = _summary_base(
        cases=cases,
        data_root=data_root,
        config_path=config_path,
        questions_path=questions_path,
        checker_version=checker_version,
    )
    summary["snapshot_hashes"] = bundle.ledger.snapshot_hashes()
    summary["source_manifest_hashes"] = _source_manifest_hashes(bundle)
    completed: list[dict[str, Any]] = []

    try:
        for case in cases:
            evidence = evidence_for_case(bundle, case)
            result = orchestrator.run(case.question, [evidence])
            trajectory = _trajectory_for_result(trajectory_path, result.trajectory_id)
            assert_schema_valid_proposed_claims(trajectory)
            assert_verdict_gates(bundle, result.final_verdicts)
            completed.append(
                {
                    "case_id": case.case_id,
                    "trajectory_id": result.trajectory_id,
                    "status": result.status,
                    "attempts": result.attempts,
                    "evidence_id": evidence["evidence_id"],
                    "verdicts": [
                        verdict["verdict"] for verdict in result.final_verdicts
                    ],
                }
            )
    except Exception as exc:
        summary.update({"status": "failed", "cases": completed, "error": str(exc)})
        _write_json(summary_path, summary)
        raise

    summary.update({"status": "passed", "cases": completed})
    _write_json(summary_path, summary)
    return summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=_DEFAULT_DATA_ROOT)
    parser.add_argument("--model-config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--questions", type=Path, default=_DEFAULT_QUESTIONS)
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--checker-version", default="0.1.0")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="validate prerequisites without calling a provider",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    cases = load_cases(args.questions)
    errors = preflight(data_root=args.data_root, config_path=args.model_config)
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2
    if args.preflight:
        print(
            json.dumps(
                {"status": "ready", "case_ids": [case.case_id for case in cases]}
            )
        )
        return 0

    trajectory_path = args.output_dir / f"{args.run_id}.jsonl"
    summary_path = args.output_dir / f"{args.run_id}.summary.json"
    summary = run_smoke(
        data_root=args.data_root,
        config_path=args.model_config,
        cases=cases,
        trajectory_path=trajectory_path,
        summary_path=summary_path,
        questions_path=args.questions,
        checker_version=args.checker_version,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0
