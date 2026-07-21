"""Deterministic scaffold smoke for the load-bearing prose test.

Runs the rule-based extractor and every ablation kind over the frozen
fixture plans, then writes a byte-stable receipt to
``results/summary.json``. No live provider calls; safe to run in CI.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.load_bearing_prose_test.ablation import ablate_bundle
from experiments.load_bearing_prose_test.claims import digest
from experiments.load_bearing_prose_test.extraction import (
    RuleBasedExtractor,
    default_kappa_vocabulary,
)


PACKAGE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = PACKAGE_DIR / "fixtures"
RESULTS_DIR = PACKAGE_DIR / "results"
DEFAULT_SUMMARY_PATH = RESULTS_DIR / "summary.json"

FIXTURE_FILES: tuple[str, ...] = (
    "artifact_completion_plans.json",
    "recursive_constrained_tool_use_plans.json",
)


def _load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _summarize_family(fixture: dict[str, Any]) -> dict[str, Any]:
    kappa = fixture["kappa"]
    extractor = RuleBasedExtractor(
        kappa=default_kappa_vocabulary(
            capabilities=(
                *kappa.get("required_capabilities", []),
                *kappa.get("forbidden_capabilities", []),
            ),
            artifacts=(kappa["required_artifact"],)
            if "required_artifact" in kappa
            else (),
        )
    )

    plan_rows: list[dict[str, Any]] = []
    for plan in fixture["plans"]:
        bundle = extractor.extract(
            plan_id=plan["plan_id"], plan_text=plan["plan_text"]
        )
        ablations = ablate_bundle(bundle, plan["plan_text"])
        plan_rows.append(
            {
                "plan_id": plan["plan_id"],
                "plan_digest": bundle.plan_digest,
                "claim_count": len(bundle.claims),
                "expected_claim_count": plan["expected_claim_count"],
                "kappa_mentioning_claims": sum(
                    1 for c in bundle.claims if c.mentions_kappa
                ),
                "ablation_count": len(ablations.ablations),
                "bundle_digest": bundle.bundle_digest,
                "ablation_set_digest": digest(ablations.to_dict()),
            }
        )
    return {
        "family": fixture["family"],
        "kappa": kappa,
        "plans": plan_rows,
    }


def build_summary() -> dict[str, Any]:
    """Return the byte-stable summary payload for the scaffold smoke."""

    families = [
        _summarize_family(_load_fixture(FIXTURES_DIR / name))
        for name in FIXTURE_FILES
    ]
    payload = {
        "schema_version": "1.0",
        "run_id": "load_bearing_prose_test_scaffold_2026_07_21",
        "package": "load_bearing_prose_test",
        "extractor": "rule_based_obligation_shape",
        "families": families,
    }
    payload["summary_digest"] = digest(payload)
    return payload


def write_summary(path: Path = DEFAULT_SUMMARY_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_summary(), sort_keys=True, indent=2) + "\n"
    path.write_text(text)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SUMMARY_PATH,
        help="path to write the summary receipt",
    )
    args = parser.parse_args()
    written = write_summary(args.output)
    print(f"wrote {written}")


if __name__ == "__main__":
    main()
