#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Dump induced-metric density fields for the Paper B heatmap figure.

Trains one net per condition (control / reward@A / reward@B) and saves the 2-D
metric-density field for each. Run from experiments/grid_cell_weakness/.
"""
import json
import reward_deformation as rd

out = {}
for name, rxy in [("control", None), ("reward_A", (0.3, 0.3)), ("reward_B", (0.7, 0.7))]:
    r = rd.train(20260629, reward_xy=rxy, steps=2500)
    out[name] = dict(density=r["density"].tolist(), side=r["side"], reward_xy=rxy)
    print(name, "done", flush=True)

with open("artifacts/grid_cell_weakness/reward_fields.json", "w") as f:
    json.dump(out, f)
print("WROTE fields", flush=True)
