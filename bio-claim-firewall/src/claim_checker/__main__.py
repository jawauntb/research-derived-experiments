"""Check one structured claim against an explicitly selected evidence world."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from evidence import load_bundle
from model_manager import ModelManager
from worlds import WORLD_REGISTRY

from .natural_language import (
    NaturalLanguageClaimCheckResult,
    check_natural_language_claim,
    check_natural_language_k562_claim,
)
from .service import (
    ClaimCheckInputError,
    ClaimCheckResult,
    check_claim,
    check_k562_claim,
)

_FIREWALL_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DATA_ROOT = _FIREWALL_ROOT / "data"


class _ClaimCheckerArgumentParser(argparse.ArgumentParser):
    """Preserve a JSON error contract when ``--json`` was requested."""

    def __init__(self, *args, json_mode: bool = False, **kwargs) -> None:
        self._json_mode = json_mode
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> NoReturn:
        if getattr(self, "_json_mode", False):
            print(_error_output(json_mode=True, kind="input_error", message=message))
            raise SystemExit(2)
        super().error(message)


def _parser(*, json_mode: bool = False) -> argparse.ArgumentParser:
    parser = _ClaimCheckerArgumentParser(description=__doc__, json_mode=json_mode)
    parser.add_argument(
        "subject", nargs="?", help="Perturbed gene symbol or HGNC CURIE"
    )
    parser.add_argument("object", nargs="?", help="Measured gene symbol or HGNC CURIE")
    parser.add_argument("direction", nargs="?", choices=("increases", "decreases"))
    parser.add_argument(
        "--claim",
        help="One natural-language K562 gene-effect question; parsed by an untrusted LLM.",
    )
    parser.add_argument(
        "--claim-json",
        help="One structured claim encoded as a JSON object; requires an explicit world.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Exact fixture file or directory for the explicitly selected world.",
    )
    parser.add_argument("--data-root", type=Path, default=_DEFAULT_DATA_ROOT)
    parser.add_argument("--world-id", help="Registered evidence-world id.")
    parser.add_argument(
        "--world-version", help="Exact version of the registered evidence world."
    )
    parser.add_argument(
        "--checker-version",
        help="Explicit checker build label; defaults to the selected adapter's build.",
    )
    parser.add_argument(
        "--model-config",
        type=Path,
        default=_FIREWALL_ROOT / "src" / "model_manager" / "config.yaml",
        help="Versioned local routing config for the untrusted parser.",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser


def format_result(result: ClaimCheckResult) -> str:
    """Render a concise local explanation without recasting the verdict."""
    verdict = result.verdict
    receipt = result.receipt if isinstance(result.receipt, dict) else {}
    canonical = (
        receipt.get("canonical_payload", {}) if isinstance(receipt, dict) else {}
    )
    world_id = canonical.get("world_id") or verdict.get("world_id")
    if isinstance(world_id, str) and world_id != "replogle-k562":
        outcome = (
            canonical.get("outcome")
            or verdict.get("outcome")
            or verdict.get("verdict", "CHECKER_ERROR")
        )
        if outcome == "ACCEPTED_CONDITIONALLY":
            outcome = "ACCEPTED"
        world_version = canonical.get("world_version") or verdict.get("world_version")
        lines = [f"Verdict: {outcome}", f"World: {world_id} / {world_version}"]
        if result.claim is not None:
            lines.append(
                "Claim: " + json.dumps(result.claim, ensure_ascii=False, sort_keys=True)
            )
        winning = canonical.get("winning_rule") or verdict.get("winning_rule")
        if isinstance(winning, dict):
            winning = winning.get("id")
        if winning:
            lines.append(f"Winning rule: {winning}")
        citations = canonical.get("citations") or verdict.get("citations") or []
        if isinstance(citations, list) and citations:
            lines.append(f"Citations: {', '.join(str(item) for item in citations)}")
        world_digest = canonical.get("world_digest")
        if world_digest:
            lines.append(f"World digest: {world_digest}")
        reason = (
            canonical.get("message")
            or canonical.get("reason")
            or verdict.get("message")
            or verdict.get("reason")
        )
        if reason:
            lines.append(f"Reason: {reason}")
        return "\n".join(lines)

    lines = [f"Verdict: {verdict['verdict']}"]
    if verdict["verdict"] == "CHECKER_ERROR":
        checker_error = verdict.get("checker_error")
        if isinstance(checker_error, dict):
            lines.append(
                "Checker error: "
                f"{checker_error.get('stage', 'unknown stage')} — "
                f"{checker_error.get('message', 'no diagnostic message')}"
            )
        else:
            lines.append("Checker error: no diagnostic details were returned")
        return "\n".join(lines)
    if result.claim is None:
        lines.append(f"Reason: {verdict.get('reason', 'no reason supplied')}")
        return "\n".join(lines)

    claim = result.claim
    lines.append(
        "Claim: "
        f"{claim['subject']['label']} {claim['relation']} {claim['object']['label']} "
        "in frozen K562 CRISPRi evidence"
    )
    evidence = result.evidence
    if evidence is None:
        lines.append("Checker error: no evidence summary was returned")
        return "\n".join(lines)
    significance = evidence.get("significance")
    significance_text = (
        f"significance {significance}"
        if significance is not None
        else "significance not reported"
    )
    lines.append(
        f"Evidence: {evidence['evidence_id']} ({evidence['effect_sign']}; "
        f"magnitude {evidence.get('magnitude')} {evidence.get('magnitude_scale')}; "
        f"{significance_text})"
    )
    if evidence["citation"]:
        lines.append(f"Citation: {evidence['citation']}")
    derivation = verdict.get("derivation")
    if isinstance(derivation, dict):
        applied_rules = derivation.get("applied_rules")
        if isinstance(applied_rules, list) and applied_rules:
            lines.append(f"Winning rule: {applied_rules[-1]}")
        conditions = derivation.get("conditions")
        if isinstance(conditions, list) and conditions:
            lines.append(
                f"Scope: {'; '.join(str(condition) for condition in conditions)}"
            )
    for reason in verdict.get("reasons", []):
        if isinstance(reason, dict):
            rule_id = reason.get("rule_id")
            message = reason.get("message")
            if rule_id or message:
                lines.append(f"Rule: {rule_id or 'n/a'} — {message or 'no message'}")
                break
    return "\n".join(lines)


def format_natural_language_result(result: NaturalLanguageClaimCheckResult) -> str:
    """Render the untrusted extraction separately from the verified outcome."""
    parsed = result.interpretation
    return "\n".join(
        (
            f"Question (untrusted): {parsed['question']!r}",
            (
                "LLM interpretation (untrusted): "
                f"{parsed['subject']} {parsed['direction']} {parsed['object']}"
            ),
            f"Parser: {parsed['provider']} / {parsed['model']} / {parsed['prompt_ref']}",
            format_result(result.result),
        )
    )


def _result_verdict(result: ClaimCheckResult | NaturalLanguageClaimCheckResult) -> str:
    """Return the deterministic verdict without interpreting it."""
    checked_result = (
        result.result if isinstance(result, NaturalLanguageClaimCheckResult) else result
    )
    return str(checked_result.verdict.get("verdict", "CHECKER_ERROR"))


def _error_output(*, json_mode: bool, kind: str, message: str) -> str:
    """Keep the documented JSON mode machine-readable on expected failures."""
    if json_mode:
        return json.dumps({"error": {"kind": kind, "message": message}}, sort_keys=True)
    label = "Input error" if kind == "input_error" else "Checker unavailable"
    return f"{label}: {message}"


def _parse_claim_json(value: str, parser: argparse.ArgumentParser) -> dict[str, object]:
    """Parse a closed structured claim without accepting arrays or scalars."""
    try:
        claim = json.loads(value)
    except json.JSONDecodeError as exc:
        parser.error(f"--claim-json must be valid JSON: {exc.msg}")
    if not isinstance(claim, dict):
        parser.error("--claim-json must encode a JSON object")
    return claim


def _default_checker_version(adapter: str) -> str:
    """Use the build label owned by each registered adapter."""
    if adapter == "clinical_trials":
        from worlds.clinical_trials.adapter import CHECKER_VERSION

        return CHECKER_VERSION
    if adapter == "open_targets":
        from worlds.open_targets.adapter import CHECKER_VERSION

        return CHECKER_VERSION
    return "0.1.0"


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser(json_mode="--json" in (sys.argv[1:] if argv is None else argv))
    args = parser.parse_args(argv)
    positional_values = (args.subject, args.object, args.direction)
    has_positionals = any(value is not None for value in positional_values)
    selected_inputs = sum(
        (args.claim is not None, args.claim_json is not None, has_positionals)
    )
    if args.claim is not None and has_positionals:
        parser.error("--claim cannot be combined with subject, object, or direction")
    if selected_inputs > 1:
        parser.error(
            "--claim, --claim-json, and SUBJECT OBJECT DIRECTION are mutually exclusive"
        )
    if has_positionals and any(value is None for value in positional_values):
        parser.error("provide all of SUBJECT OBJECT DIRECTION")
    explicit_world = args.world_id is not None or args.world_version is not None
    if explicit_world and (args.world_id is None or args.world_version is None):
        parser.error("--world-id and --world-version must be provided together")
    if explicit_world and args.fixture is None:
        parser.error("--fixture is required for an explicitly selected world")
    if not explicit_world and args.fixture is not None:
        parser.error("--fixture requires --world-id and --world-version")
    if not explicit_world and args.claim_json is not None:
        parser.error("--claim-json requires --world-id, --world-version, and --fixture")
    if selected_inputs == 0:
        if explicit_world:
            parser.error("provide SUBJECT OBJECT DIRECTION, --claim, or --claim-json")
        parser.error("provide SUBJECT OBJECT DIRECTION, or use --claim")
    structured_claim = (
        _parse_claim_json(args.claim_json, parser)
        if args.claim_json is not None
        else None
    )
    try:
        if explicit_world:
            world = WORLD_REGISTRY.resolve(args.world_id or "", args.world_version)
            checker_version = args.checker_version or _default_checker_version(
                world.adapter
            )
            fixture: object
            if world.adapter == "k562":
                fixture = load_bundle(
                    args.fixture, allowed_sources=world.source_allowlist
                )
            else:
                fixture = args.fixture
            if args.claim is not None:
                if "check_natural_language" not in world.capabilities:
                    raise ClaimCheckInputError(
                        f"world {world.world_key} does not support natural-language claims"
                    )
                result = check_natural_language_claim(
                    fixture,
                    world.world_id,
                    world.version,
                    args.claim,
                    ModelManager(args.model_config),
                    checker_version=checker_version,
                )
            elif structured_claim is not None:
                result = check_claim(
                    fixture,
                    world.world_id,
                    world.version,
                    structured_claim,
                    checker_version=checker_version,
                )
            else:
                if world.adapter != "k562":
                    raise ClaimCheckInputError(
                        f"world {world.world_key} requires --claim-json"
                    )
                result = check_claim(
                    fixture,
                    world.world_id,
                    world.version,
                    {
                        "subject": args.subject,
                        "object": args.object,
                        "direction": args.direction,
                    },
                    checker_version=checker_version,
                )
        else:
            checker_version = args.checker_version or "0.1.0"
            bundle = load_bundle(args.data_root)
            if args.claim is not None:
                result = check_natural_language_k562_claim(
                    bundle,
                    args.claim,
                    ModelManager(args.model_config),
                    checker_version=checker_version,
                )
            else:
                result = check_k562_claim(
                    bundle,
                    args.subject,
                    args.object,
                    args.direction,
                    checker_version=checker_version,
                )
    except ClaimCheckInputError as exc:
        print(_error_output(json_mode=args.json, kind="input_error", message=str(exc)))
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI boundary must fail closed
        print(
            _error_output(
                json_mode=args.json, kind="checker_unavailable", message=str(exc)
            )
        )
        return 3

    if args.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    elif isinstance(result, NaturalLanguageClaimCheckResult):
        print(format_natural_language_result(result))
    else:
        print(format_result(result))
    return 4 if _result_verdict(result) == "CHECKER_ERROR" else 0


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
