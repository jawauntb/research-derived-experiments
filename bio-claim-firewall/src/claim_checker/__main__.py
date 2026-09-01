"""Check one narrow K562 perturbation-effect claim against frozen evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, Sequence

from evidence import load_bundle
from model_manager import ModelManager

from .natural_language import (
    NaturalLanguageClaimCheckResult,
    check_natural_language_k562_claim,
)
from .service import ClaimCheckInputError, ClaimCheckResult, check_k562_claim


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
    parser.add_argument("--data-root", type=Path, default=_DEFAULT_DATA_ROOT)
    parser.add_argument("--checker-version", default="0.1.0")
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
            "LLM interpretation (untrusted): "
            f"{parsed['subject']} {parsed['direction']} {parsed['object']}",
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser(json_mode="--json" in (sys.argv[1:] if argv is None else argv))
    args = parser.parse_args(argv)
    positional_values = (args.subject, args.object, args.direction)
    if args.claim is not None and any(value is not None for value in positional_values):
        parser.error("--claim cannot be combined with subject, object, or direction")
    if args.claim is None and any(value is None for value in positional_values):
        parser.error("provide SUBJECT OBJECT DIRECTION, or use --claim")
    try:
        bundle = load_bundle(args.data_root)
        if args.claim is not None:
            result = check_natural_language_k562_claim(
                bundle,
                args.claim,
                ModelManager(args.model_config),
                checker_version=args.checker_version,
            )
        else:
            result = check_k562_claim(
                bundle,
                args.subject,
                args.object,
                args.direction,
                checker_version=args.checker_version,
            )
    except ClaimCheckInputError as exc:
        print(_error_output(json_mode=args.json, kind="input_error", message=str(exc)))
        return 2
    except Exception as exc:
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
