#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal-side BBBD preparation: download missing experiments + unzip in place.

The BBBD corpus is 26.97 GB (five per-experiment archives on Zenodo record
19241964). Local disk is tight — we upload the two zips we already have
(`experiment1.zip`, `experiment4.zip`) to the ``bbbd-cache`` Volume from the
laptop, then run this Modal job to:

  1. Download any missing experiment zips directly from Zenodo (fast — Modal
     has plenty of egress and no laptop-disk pressure).
  2. Unzip each archive into ``/data/bbbd/experiment<N>/``.
  3. Delete the zip after successful extraction to keep the Volume lean.
  4. Verify `participants.tsv` is present in each experiment root.

Run with:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            coherence-testbench/modal_jobs/prepare_bbbd.py

Add ``--experiments 2,3,5`` (etc.) to restrict the set. Defaults to all 5.
"""

from __future__ import annotations

import importlib
from typing import Any

modal = importlib.import_module("modal")


IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl", "unzip")
    .pip_install("requests>=2.32", "tqdm>=4.66")
)

app = modal.App(name="coherence-testbench-bbbd-prep")

bbbd_volume = modal.Volume.from_name("bbbd-cache", create_if_missing=True)
BBBD_MOUNT = "/data/bbbd"

ZENODO_RECORD = "19241964"
EXPERIMENT_ARCHIVES = {
    1: "experiment1.zip",
    2: "experiment2.zip",
    3: "experiment3.zip",
    4: "experiment4.zip",
    5: "experiment5.zip",
}


def _zenodo_url(experiment: int) -> str:
    fname = EXPERIMENT_ARCHIVES[experiment]
    return f"https://zenodo.org/api/records/{ZENODO_RECORD}/files/{fname}/content"


@app.function(
    image=IMAGE,
    timeout=6 * 60 * 60,       # some zips are ~8 GB
    cpu=4,
    memory=8 * 1024,
    volumes={BBBD_MOUNT: bbbd_volume},
)
def prepare_experiment(arg: dict[str, Any]) -> dict[str, Any]:
    """Ensure ``/data/bbbd/experiment<N>/`` is downloaded + unpacked."""
    import os
    import shutil
    import subprocess
    from pathlib import Path

    experiment = int(arg["experiment"])
    force = bool(arg.get("force", False))

    root = Path(BBBD_MOUNT)
    root.mkdir(parents=True, exist_ok=True)
    exp_root = root / f"experiment{experiment}"
    zip_path = root / EXPERIMENT_ARCHIVES[experiment]
    marker = exp_root / ".unpacked"

    if marker.exists() and not force:
        return {"experiment": experiment, "state": "already_unpacked",
                "path": str(exp_root)}

    if not zip_path.exists():
        # Download directly from Zenodo — server-side; laptop stays clean.
        url = _zenodo_url(experiment)
        subprocess.run(
            ["curl", "-L", "--fail", "--retry", "3", "--retry-delay", "5",
             "-o", str(zip_path), url],
            check=True,
        )

    exp_root.mkdir(parents=True, exist_ok=True)
    # Unzip in place. `-o` overwrites without prompting; the marker check
    # above prevents this from accidentally re-running on a good tree.
    subprocess.run(
        ["unzip", "-q", "-o", str(zip_path), "-d", str(exp_root)],
        check=True,
    )
    participants = exp_root / "participants.tsv"
    if not participants.exists():
        # Some zips nest under an internal prefix; flatten one level if so.
        candidates = list(exp_root.glob("*/participants.tsv"))
        if candidates:
            inner = candidates[0].parent
            for item in inner.iterdir():
                shutil.move(str(item), str(exp_root / item.name))
            inner.rmdir()
            participants = exp_root / "participants.tsv"

    if not participants.exists():
        raise RuntimeError(
            f"experiment{experiment}: unpacked but participants.tsv missing "
            f"at {participants}. Layout may have changed on Zenodo."
        )

    # Reclaim Volume space now that the tree is on disk.
    os.remove(zip_path)
    marker.write_text("unpacked-ok\n")
    bbbd_volume.commit()

    subject_count = sum(1 for _ in exp_root.glob("sub-*") if _.is_dir())
    return {
        "experiment": experiment,
        "state": "unpacked",
        "path": str(exp_root),
        "n_subjects": subject_count,
    }


@app.local_entrypoint()
def main(experiments: str = "1,2,3,4,5", force: bool = False) -> None:
    """Fan out one worker per experiment."""
    wanted = [int(x) for x in experiments.split(",") if x.strip()]
    args_list = [{"experiment": e, "force": force} for e in wanted]
    for result in prepare_experiment.map(args_list):
        print(result)
