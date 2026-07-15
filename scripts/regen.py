#!/usr/bin/env python3
"""One-command reproducer / dispatcher for experiments.

`python scripts/regen.py <name>` reproduces an experiment's committed artifacts
where that is possible on CPU without secrets (deterministic, seeded), and
otherwise prints the documented run command (many sweeps require Modal/GPU or
Doppler-scoped secrets and must be dispatched from an authed machine).

Allowlisted clean-clone recipes (`bayesian_voi`, `mathematical_claims`) execute
structured argv from the package manifest without a shell, optionally verifying
fresh creation against committed oracles in an isolated checkout.

  python scripts/regen.py list
  python scripts/regen.py <name>
  python scripts/regen.py <name> --deps
  python scripts/regen.py verify-clean-clone
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CPU_DEPS = [
    "torch>=2.5,<2.8",
    "numpy>=1.26,<2.2",
    "scipy>=1.11,<1.15",
    "gudhi",
    "matplotlib",
    "reportlab",
]

# Local, CPU-only, deterministic reproducers. Each value is a list of commands
# (run from repo root). Everything else prints its documented run command.
LOCAL = {
    "grid_cell_weakness": [
        "python experiments/grid_cell_weakness/pilot.py",
        "python experiments/grid_cell_weakness/run_local.py --seeds 2 --steps 4000",
        "python experiments/grid_cell_weakness/reward_deformation.py --seeds 3 --steps 2500",
        "cd experiments/grid_cell_weakness && python dump_fields.py && python dump_manifold.py",
        "python scripts/build_gridcell_pdf.py",
        "python scripts/build_paperB_pdf.py",
        "python scripts/build_effective_dimension_pdf.py",
    ],
    "weakness_temporal": [
        "python experiments/weakness_temporal/temporal.py --n-models 240",
    ],
    "world_responds": [
        "python3 -m experiments.world_responds.suite_c_factorial_ablation",
    ],
}
PDF_BUILDERS = {
    "commitment_surface": [
        "python scripts/make_commitment_surface_figures.py",
        "python scripts/build_commitment_surface_pdf.py",
    ],
    "symbolic_weakness": ["python scripts/build_weakness_pdf.py"],
}
PDF_OUTPUTS = {
    "symbolic_weakness": ["weakness_predicts_ood.pdf"],
    "grid_cell_weakness": [
        "weakness_predicts_topology.pdf",
        "concern_deforms_metric.pdf",
        "reward_deformation_effective_dimension_law.pdf",
    ],
}

# Exact first clean-clone allowlist (R15). Output paths are repo-relative.
CLEAN_CLONE_ALLOWLIST: dict[str, str] = {
    "bayesian_voi": "experiments/bayesian_voi/results/bayesian_voi_summary.json",
    "mathematical_claims": (
        "experiments/mathematical_claims/results/mathematical_claims_summary.json"
    ),
}


def refresh_committed_pdfs(name: str) -> None:
    for fname in PDF_OUTPUTS.get(name, []):
        src = ROOT / "artifacts" / "papers" / fname
        if not src.exists():
            continue
        for dest_dir in (
            ROOT / "papers" / "pdf",
            ROOT / "sites" / "reafference_attribution" / "papers",
        ):
            if dest_dir.exists():
                shutil.copy2(src, dest_dir / fname)
                print(f"[regen] refreshed {dest_dir.relative_to(ROOT)}/{fname}")


def load_manifest() -> dict[str, Any]:
    path = ROOT / "docs" / "verification.json"
    return json.loads(path.read_text()) if path.exists() else {"experiments": []}


def run_shell_commands(cmds: list[str]) -> None:
    for command in cmds:
        print(f"\n$ {command}")
        completed = subprocess.run(command, shell=True, cwd=ROOT, check=False)
        if completed.returncode != 0:
            print(f"[regen] command failed ({completed.returncode}); stopping.")
            raise SystemExit(completed.returncode)


def load_structured_recipe(package: str, *, root: Path = ROOT) -> tuple[list[str], str]:
    """Return (argv, output_relpath) for an allowlisted clean-clone package."""

    if package not in CLEAN_CLONE_ALLOWLIST:
        raise ValueError(f"package is not in the clean-clone allowlist: {package}")
    output_rel = CLEAN_CLONE_ALLOWLIST[package]
    registry = json.loads((root / "docs" / "experiment_contract_registry.json").read_text())
    record = next(
        (
            item
            for item in registry["packages"]
            if isinstance(item, dict) and item.get("package") == package
        ),
        None,
    )
    if not isinstance(record, dict) or record.get("coverage_mode") != "structured_manifest":
        raise ValueError(f"clean-clone package lacks structured coverage: {package}")
    manifest_rel = record.get("manifest_path")
    if not isinstance(manifest_rel, str):
        raise ValueError(f"structured package is missing manifest_path: {package}")
    manifest = json.loads((root / manifest_rel).read_text())
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError(f"manifest runtime missing for {package}")
    execution_class = runtime.get("execution_class")
    if execution_class != "local_cpu":
        raise ValueError(
            f"clean-clone recipe must be local_cpu, found {execution_class}: {package}"
        )
    command = runtime.get("command")
    if not isinstance(command, list) or not command or any(
        not isinstance(part, str) or not part for part in command
    ):
        raise ValueError(f"manifest runtime.command must be a non-empty argv list: {package}")
    if any(";" in part or "|" in part or "&&" in part for part in command):
        raise ValueError(f"manifest runtime.command looks shell-interpolated: {package}")
    return list(command), output_rel


def materialize_clean_checkout(root: Path, dest: Path) -> None:
    """Extract tracked HEAD files into dest (no ignored workstation artifacts)."""

    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(root), "archive", "--format=tar", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
    )
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
        tar.extractall(dest)


def verify_clean_clone_package(package: str, *, root: Path = ROOT) -> None:
    argv, output_rel = load_structured_recipe(package, root=root)
    oracle_path = root / output_rel
    if not oracle_path.is_file():
        raise ValueError(f"committed oracle missing: {output_rel}")
    oracle_bytes = oracle_path.read_bytes()

    with TemporaryDirectory(prefix=f"regen-{package}-") as tmp:
        checkout = Path(tmp) / "checkout"
        materialize_clean_checkout(root, checkout)
        target = checkout / output_rel
        if target.exists():
            target.unlink()
        print(f"[regen] clean-clone verify {package}: {' '.join(argv)}")
        completed = subprocess.run(
            argv,
            cwd=checkout,
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(
                f"[regen] clean-clone recipe failed ({completed.returncode}): {package}"
            )
        if not target.is_file():
            raise SystemExit(
                f"[regen] clean-clone did not newly create output: {output_rel}"
            )
        actual = target.read_bytes()
        if actual != oracle_bytes:
            raise SystemExit(
                f"[regen] clean-clone byte mismatch for {output_rel} "
                f"(oracle={len(oracle_bytes)} actual={len(actual)})"
            )
    print(f"[regen] clean-clone PASS: {package} -> {output_rel}")


def run_structured_local(package: str, *, root: Path = ROOT) -> None:
    argv, output_rel = load_structured_recipe(package, root=root)
    print(f"[regen] reproducing {package} via structured argv (no shell)")
    print(f"$ {' '.join(argv)}")
    completed = subprocess.run(argv, cwd=root, shell=False, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"[regen] command failed ({completed.returncode}); stopping.")
    if not (root / output_rel).is_file():
        raise SystemExit(f"[regen] expected output missing after run: {output_rel}")


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    name = args[0]
    do_deps = "--deps" in args
    verify = "--verify-clean-clone" in args or name == "verify-clean-clone"

    man = {entry["name"]: entry for entry in load_manifest()["experiments"]}

    if name == "list":
        for package_name, entry in sorted(man.items()):
            if package_name in CLEAN_CLONE_ALLOWLIST:
                how = "clean-clone-argv"
            elif package_name in LOCAL:
                how = "local-cpu"
            elif package_name in PDF_BUILDERS:
                how = "pdf"
            else:
                how = "documented-command"
            print(f"{package_name:34s} [{how}]  {entry.get('run_command') or ''}")
        return

    if do_deps:
        run_shell_commands(
            [
                f"{sys.executable} -m pip install --quiet "
                + " ".join(f'"{dep}"' for dep in CPU_DEPS)
            ]
        )

    if name == "verify-clean-clone":
        for package in sorted(CLEAN_CLONE_ALLOWLIST):
            verify_clean_clone_package(package, root=ROOT)
        return

    if verify:
        if name not in CLEAN_CLONE_ALLOWLIST:
            raise SystemExit(
                f"[regen] --verify-clean-clone only supports "
                f"{sorted(CLEAN_CLONE_ALLOWLIST)}"
            )
        verify_clean_clone_package(name, root=ROOT)
        return

    if name in CLEAN_CLONE_ALLOWLIST:
        run_structured_local(name, root=ROOT)
        return

    if name in LOCAL:
        print(f"[regen] reproducing {name} locally (CPU, deterministic)")
        run_shell_commands(LOCAL[name] + PDF_BUILDERS.get(name, []))
        refresh_committed_pdfs(name)
    elif name in PDF_BUILDERS:
        print(f"[regen] rebuilding {name} paper PDF from committed numbers")
        run_shell_commands(PDF_BUILDERS[name])
        refresh_committed_pdfs(name)
    elif name in man:
        command = man[name].get("run_command")
        print(
            f"[regen] {name} is not a local CPU reproducer "
            "(likely needs Modal/GPU/secrets)."
        )
        print(f"[regen] documented run command:\n    {command or '(see README / result reports)'}")
        print("[regen] inspect only; this dispatcher does not launch Modal.")
    else:
        print(f"[regen] unknown experiment '{name}'. Try: python scripts/regen.py list")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
