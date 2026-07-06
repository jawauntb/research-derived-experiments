#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render world-responds paper artifacts on Modal L4 workers."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
REPO_REMOTE = Path("/repo")
PAPER_REL = Path("papers/world_responds/paper.md")
PDF_REL = Path("papers/world_responds/paper.pdf")
FIG5_REL = Path("papers/world_responds/figures/fig5_reengagement_floor.png")


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
    return bool(parts & ignored_dirs) or local_path.suffix in {".pyc", ".DS_Store"}


IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "markdown-pdf>=1.7,<2",
        "matplotlib>=3.8,<4",
        "numpy>=1.26,<2.2",
    )
    .add_local_dir(".", remote_path=str(REPO_REMOTE), copy=True, ignore=_ignore)
)

app = modal.App(name="research-derived-world-responds-paper-tasks")


def _load_figure_module() -> Any:
    import importlib.util
    import sys

    module_path = REPO_REMOTE / "scripts" / "make_world_responds_figures.py"
    spec = importlib.util.spec_from_file_location("world_responds_figures", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["world_responds_figures"] = module
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
def build_reengagement_png() -> bytes:
    import tempfile

    module = _load_figure_module()
    with tempfile.TemporaryDirectory() as tmp:
        fig_dir = Path(tmp)
        module.FIG_DIR = fig_dir
        module.fig5_reengagement_floor()
        return (fig_dir / FIG5_REL.name).read_bytes()


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1200,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def build_pdf_and_previews(reengagement_png: bytes, preview_pages: list[int]) -> dict[str, Any]:
    import shutil
    import subprocess
    import tempfile

    import fitz

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        paper_dir = tmp_root / "paper"
        figures_dir = paper_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        source_paper_dir = REPO_REMOTE / PAPER_REL.parent
        shutil.copy2(source_paper_dir / "paper.md", paper_dir / "paper.md")
        if (source_paper_dir / "figures").exists():
            for source_fig in (source_paper_dir / "figures").glob("*"):
                if source_fig.is_file():
                    shutil.copy2(source_fig, figures_dir / source_fig.name)
        (figures_dir / FIG5_REL.name).write_bytes(reengagement_png)

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
                "When the World Responds",
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
                pix = doc.load_page(page_idx).get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                previews[page_idx] = pix.tobytes("png")
        return {"pdf": pdf_bytes, "previews": previews, "page_count": doc.page_count}


@app.local_entrypoint()
def main(preview_pages: str = "0,4,5,6"):
    reengagement_png = build_reengagement_png.remote()
    FIG5_REL.parent.mkdir(parents=True, exist_ok=True)
    FIG5_REL.write_bytes(reengagement_png)
    print(f"[world-responds-modal] wrote {FIG5_REL} ({FIG5_REL.stat().st_size} bytes)")

    pages = [int(x) for x in preview_pages.split(",") if x.strip()]
    payload = build_pdf_and_previews.remote(reengagement_png, pages)
    PDF_REL.parent.mkdir(parents=True, exist_ok=True)
    PDF_REL.write_bytes(payload["pdf"])
    print(
        f"[world-responds-modal] wrote {PDF_REL} "
        f"({PDF_REL.stat().st_size} bytes, {payload['page_count']} pages)"
    )

    preview_dir = Path("tmp/pdfs")
    preview_dir.mkdir(parents=True, exist_ok=True)
    for page_idx, png in sorted(payload["previews"].items()):
        preview_path = preview_dir / f"world_responds_p{int(page_idx) + 1:03d}.png"
        preview_path.write_bytes(png)
        print(f"[world-responds-modal] wrote {preview_path} ({preview_path.stat().st_size} bytes)")
