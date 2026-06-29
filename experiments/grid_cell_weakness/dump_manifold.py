#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Dump binned population vectors (the manifold) for control vs reward, for a
PCA-3D manifold visualization in Paper B."""
import json
import numpy as np
import reward_deformation as rd

out = {}
for name, rxy in [("control", None), ("reward_A", (0.3, 0.3))]:
    r = rd.train(20260629, reward_xy=rxy, steps=2500)
    out[name] = dict(pop=r["pop"].tolist(), density=r["density"].tolist(),
                     side=r["side"], reward_xy=rxy)
    print(name, "done", flush=True)

with open("artifacts/grid_cell_weakness/reward_manifold.json", "w") as f:
    json.dump(out, f)
print("WROTE manifold", flush=True)
