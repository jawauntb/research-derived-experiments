#!/usr/bin/env python3
"""One-command reproducer / dispatcher for experiments.

`python scripts/regen.py <name>` reproduces an experiment's committed artifacts
where that is possible on CPU without secrets (deterministic, seeded), and
otherwise prints the documented run command (many sweeps require Modal/GPU or
Doppler-scoped secrets and must be dispatched from an authed machine).

This closes the reproducibility hole flagged by Mo (ICML 2026): a wiped
environment never forces a manual re-run — the reproduce step is one command.

  python scripts/regen.py list          # list experiments + how each reproduces
  python scripts/regen.py <name>         # reproduce <name> (or print its command)
  python scripts/regen.py <name> --deps  # also pip-install the CPU stack first
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CPU_DEPS = ["torch>=2.5,<2.8", "numpy>=1.26,<2.2", "scipy>=1.11,<1.15",
            "gudhi", "matplotlib", "reportlab"]

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
# Flagship paper PDFs (built from committed numbers/data).
PDF_BUILDERS = {
    "commitment_surface": [
        "python scripts/make_commitment_surface_figures.py",
        "python scripts/build_commitment_surface_pdf.py",
    ],
    "symbolic_weakness": ["python scripts/build_weakness_pdf.py"],
}
# After building, copy the rendered PDF to the committed + site-served locations so
# a regen refreshes what readers actually see.
PDF_OUTPUTS = {
    "symbolic_weakness": ["weakness_predicts_ood.pdf"],
    "grid_cell_weakness": [
        "weakness_predicts_topology.pdf",
        "concern_deforms_metric.pdf",
        "reward_deformation_effective_dimension_law.pdf",
    ],
}


def refresh_committed_pdfs(name):
    import shutil
    for fname in PDF_OUTPUTS.get(name, []):
        src = ROOT / "artifacts" / "papers" / fname
        if not src.exists():
            continue
        for dest_dir in (ROOT / "papers" / "pdf",
                         ROOT / "sites" / "reafference_attribution" / "papers"):
            if dest_dir.exists():
                shutil.copy2(src, dest_dir / fname)
                print(f"[regen] refreshed {dest_dir.relative_to(ROOT)}/{fname}")


def load_manifest():
    p = ROOT / "docs" / "verification.json"
    return json.loads(p.read_text()) if p.exists() else {"experiments": []}


def run(cmds):
    for c in cmds:
        print(f"\n$ {c}")
        r = subprocess.run(c, shell=True, cwd=ROOT)
        if r.returncode != 0:
            print(f"[regen] command failed ({r.returncode}); stopping.")
            sys.exit(r.returncode)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    name = args[0]
    do_deps = "--deps" in args

    man = {e["name"]: e for e in load_manifest()["experiments"]}

    if name == "list":
        for n, e in sorted(man.items()):
            how = "local-cpu" if n in LOCAL else ("pdf" if n in PDF_BUILDERS else "documented-command")
            print(f"{n:34s} [{how}]  {e.get('run_command') or ''}")
        return

    if do_deps:
        run([f"{sys.executable} -m pip install --quiet " + " ".join(f'"{d}"' for d in CPU_DEPS)])

    if name in LOCAL:
        print(f"[regen] reproducing {name} locally (CPU, deterministic)")
        run(LOCAL[name] + PDF_BUILDERS.get(name, []))
        refresh_committed_pdfs(name)
    elif name in PDF_BUILDERS:
        print(f"[regen] rebuilding {name} paper PDF from committed numbers")
        run(PDF_BUILDERS[name])
        refresh_committed_pdfs(name)
    elif name in man:
        cmd = man[name].get("run_command")
        print(f"[regen] {name} is not a local CPU reproducer (likely needs Modal/GPU/secrets).")
        print(f"[regen] documented run command:\n    {cmd or '(see README / result reports)'}")
        print("[regen] dispatch it from a Modal/Doppler-authed machine.")
    else:
        print(f"[regen] unknown experiment '{name}'. Try: python scripts/regen.py list")
        sys.exit(1)


if __name__ == "__main__":
    main()
