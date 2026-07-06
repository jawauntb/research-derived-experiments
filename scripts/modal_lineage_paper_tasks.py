#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render lineage paper PDFs on Modal L4 workers.

Example:

    uvx --python 3.12 --from modal modal run \
        scripts/modal_lineage_paper_tasks.py --papers current_error_calibration,vector_first_order_self,scale_normalized_vprobe
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
REPO_REMOTE = Path("/repo")
PAPER_DIRS = {
    "current_error_calibration": Path("papers/current_error_calibration"),
    "vector_first_order_self": Path("papers/vector_first_order_self"),
    "scale_normalized_vprobe": Path("papers/scale_normalized_vprobe"),
    "architecture_laws_machine_agency": Path("papers/architecture_laws_machine_agency"),
}
PAPER_TITLES = {
    "current_error_calibration": "Current-Error Calibration for Identifying Interventions",
    "vector_first_order_self": "Vector First-Order Self",
    "scale_normalized_vprobe": "Scale-Normalized Probe Calibration",
    "architecture_laws_machine_agency": "Architecture Laws for Machine Agency",
}


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
    .pip_install("markdown-pdf>=1.7,<2")
    .add_local_dir(".", remote_path=str(REPO_REMOTE), copy=True, ignore=_ignore)
)

app = modal.App(name="research-derived-lineage-paper-tasks")


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=1800,
    cpu=4,
    memory=8192,
    single_use_containers=True,
)
def build_pdfs(paper_names: list[str], preview_pages: list[int]) -> dict[str, Any]:
    import subprocess
    import tempfile

    import fitz  # pulled in by markdown-pdf

    payload: dict[str, Any] = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        for name in paper_names:
            rel_dir = PAPER_DIRS[name]
            in_path = REPO_REMOTE / rel_dir / "paper.md"
            out_pdf = tmp_root / f"{name}.pdf"
            subprocess.run(
                [
                    "python",
                    str(REPO_REMOTE / "scripts" / "render_paper_pdf.py"),
                    "--in",
                    str(in_path),
                    "--out",
                    str(out_pdf),
                    "--title",
                    PAPER_TITLES[name],
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
            payload[name] = {
                "pdf": pdf_bytes,
                "page_count": doc.page_count,
                "previews": previews,
            }
    return payload


@app.local_entrypoint()
def main(
    papers: str = "current_error_calibration,vector_first_order_self,scale_normalized_vprobe",
    preview_pages: str = "0,2,5",
) -> None:
    paper_names = [name.strip() for name in papers.split(",") if name.strip()]
    unknown = [name for name in paper_names if name not in PAPER_DIRS]
    if unknown:
        raise SystemExit(f"unknown paper names: {', '.join(unknown)}")
    pages = [int(x) for x in preview_pages.split(",") if x.strip()]
    payload = build_pdfs.remote(paper_names, pages)
    preview_dir = Path("tmp/pdfs")
    preview_dir.mkdir(parents=True, exist_ok=True)
    for name in paper_names:
        rel_dir = PAPER_DIRS[name]
        pdf_path = rel_dir / "paper.pdf"
        pdf_path.write_bytes(payload[name]["pdf"])
        print(
            f"[lineage-modal] wrote {pdf_path} "
            f"({pdf_path.stat().st_size} bytes, {payload[name]['page_count']} pages)"
        )
        for page_idx, png in sorted(payload[name]["previews"].items()):
            preview_path = preview_dir / f"{name}_p{int(page_idx) + 1:03d}.png"
            preview_path.write_bytes(png)
            print(f"[lineage-modal] wrote {preview_path} ({preview_path.stat().st_size} bytes)")
