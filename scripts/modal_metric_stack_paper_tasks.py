#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Run metric-stack paper artifact tasks on Modal L4 workers.

Example:

    uvx --python 3.12 --from modal modal run \
        scripts/modal_metric_stack_paper_tasks.py --mode artifacts

    uvx --python 3.12 --from modal modal run \
        scripts/modal_metric_stack_paper_tasks.py --mode checks
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
REPO_REMOTE = Path("/repo")
PAPER_REL = Path("papers/metric_stack_synthesis/paper.md")
PDF_REL = Path("papers/metric_stack_synthesis/paper.pdf")
FIG2B_REL = Path("papers/metric_stack_synthesis/figures/fig2b_architecture_laws.png")


def _ignore(local_path: Path) -> bool:
    parts = set(local_path.parts)
    ignored_dirs = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".ty",
        ".venv",
        "__pycache__",
        "node_modules",
        "tmp",
    }
    if parts & ignored_dirs:
        return True
    return local_path.suffix in {".pyc", ".DS_Store"}


IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        "markdown-pdf>=1.7,<2",
        "matplotlib>=3.8,<4",
        "numpy>=1.26,<2.2",
        "pytest>=8,<9",
        "ruff>=0.12,<1",
        "scipy>=1.13,<2",
        "torch>=2.5,<2.8",
        "ty",
    )
    .add_local_dir(".", remote_path=str(REPO_REMOTE), copy=True, ignore=_ignore)
)

app = modal.App(name="research-derived-metric-stack-paper-tasks")


def _load_figure_module() -> Any:
    import importlib.util
    import sys

    module_path = REPO_REMOTE / "scripts" / "make_metric_stack_synthesis_figures.py"
    spec = importlib.util.spec_from_file_location("metric_stack_figures", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["metric_stack_figures"] = module
    spec.loader.exec_module(module)
    return module


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=900,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def build_fig2b_png() -> bytes:
    import tempfile

    module = _load_figure_module()
    with tempfile.TemporaryDirectory() as tmp:
        fig_dir = Path(tmp)
        module.FIG_DIR = fig_dir
        module.fig2b_architecture_laws()
        return (fig_dir / FIG2B_REL.name).read_bytes()


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1200,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def build_pdf_and_previews(fig2b_png: bytes, preview_pages: list[int]) -> dict[str, Any]:
    import shutil
    import subprocess
    import tempfile

    import fitz  # PyMuPDF, pulled in by markdown-pdf

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        paper_dir = tmp_root / "paper"
        figures_dir = paper_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        source_paper_dir = REPO_REMOTE / PAPER_REL.parent
        shutil.copy2(source_paper_dir / "paper.md", paper_dir / "paper.md")
        for source_fig in (source_paper_dir / "figures").glob("*"):
            if source_fig.is_file():
                shutil.copy2(source_fig, figures_dir / source_fig.name)
        (figures_dir / FIG2B_REL.name).write_bytes(fig2b_png)

        out_pdf = paper_dir / "paper.pdf"
        subprocess.run(
            [
                "python",
                str(REPO_REMOTE / "scripts" / "render_paper_pdf.py"),
                "--in",
                str(paper_dir / "paper.md"),
                "--out",
                str(out_pdf),
                "--title",
                "The Metric Stack of Concern",
                "--author",
                "Jawaun Brown",
            ],
            check=True,
            cwd=str(REPO_REMOTE),
        )

        pdf_bytes = out_pdf.read_bytes()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        previews: dict[int, bytes] = {}
        for page_idx in preview_pages:
            if 0 <= page_idx < doc.page_count:
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                previews[page_idx] = pix.tobytes("png")
        return {
            "pdf": pdf_bytes,
            "previews": previews,
            "page_count": doc.page_count,
        }


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1800,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def run_remote_checks(candidate_files: list[str]) -> list[dict[str, Any]]:
    import subprocess

    subprocess.run(["git", "init"], cwd=str(REPO_REMOTE), check=True, stdout=subprocess.PIPE)
    subprocess.run(
        ["git", "config", "user.email", "modal-check@example.invalid"],
        cwd=str(REPO_REMOTE),
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Modal Check"],
        cwd=str(REPO_REMOTE),
        check=True,
    )
    existing_files = [
        path
        for path in candidate_files
        if path
        and not path.startswith("tmp/")
        and not path.startswith(".git/")
        and (REPO_REMOTE / path).exists()
    ]
    for start in range(0, len(existing_files), 400):
        batch = existing_files[start : start + 400]
        if batch:
            subprocess.run(["git", "add", "-f", "--", *batch], cwd=str(REPO_REMOTE), check=True)

    commands = [
        ["python", "scripts/publication_guard.py"],
        ["ruff", "check", "."],
        ["ty", "check", "scripts", "experiments", "tests"],
    ]
    results = []
    for command in commands:
        proc = subprocess.run(
            command,
            cwd=str(REPO_REMOTE),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        results.append(
            {
                "command": " ".join(command),
                "returncode": proc.returncode,
                "output": proc.stdout[-12000:],
            }
        )
        if proc.returncode != 0:
            break
    return results


@app.local_entrypoint()
def main(mode: str = "all", preview_pages: str = "0,3,4,5"):
    mode = mode.lower().strip()
    if mode == "all":
        mode = "artifacts"
    if mode not in {"artifacts", "fig2b", "pdf", "checks"}:
        raise SystemExit("mode must be one of: artifacts, fig2b, pdf, checks")

    fig2b_png: bytes | None = None
    if mode in {"artifacts", "fig2b", "pdf"}:
        fig2b_png = build_fig2b_png.remote()
        out_fig = FIG2B_REL
        out_fig.parent.mkdir(parents=True, exist_ok=True)
        out_fig.write_bytes(fig2b_png)
        print(f"[metric-stack-modal] wrote {out_fig} ({out_fig.stat().st_size} bytes)")

    if mode in {"artifacts", "pdf"}:
        assert fig2b_png is not None
        pages = [int(x) for x in preview_pages.split(",") if x.strip()]
        payload = build_pdf_and_previews.remote(fig2b_png, pages)
        out_pdf = PDF_REL
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        out_pdf.write_bytes(payload["pdf"])
        print(
            f"[metric-stack-modal] wrote {out_pdf} "
            f"({out_pdf.stat().st_size} bytes, {payload['page_count']} pages)"
        )
        preview_dir = Path("tmp/pdfs")
        preview_dir.mkdir(parents=True, exist_ok=True)
        for page_idx, png in sorted(payload["previews"].items()):
            preview_path = preview_dir / f"metric_stack_p{int(page_idx) + 1:03d}.png"
            preview_path.write_bytes(png)
            print(f"[metric-stack-modal] wrote {preview_path} ({preview_path.stat().st_size} bytes)")

    if mode == "checks":
        import subprocess

        candidate_proc = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        )
        tracked_proc = subprocess.run(
            ["git", "ls-files"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        )
        candidate_files = sorted(
            {
                line.strip()
                for line in (tracked_proc.stdout + "\n" + candidate_proc.stdout).splitlines()
                if line.strip() and not line.startswith("tmp/")
            }
        )
        failures = []
        for result in run_remote_checks.remote(candidate_files):
            print(f"[metric-stack-modal] $ {result['command']}")
            print(result["output"].rstrip())
            if result["returncode"] != 0:
                failures.append(result)
                break
        if failures:
            raise SystemExit(f"Remote checks failed: {failures[0]['command']}")
