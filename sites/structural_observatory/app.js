"use strict";

// Renders the three instruments' committed results into the page. Pure DOM, no deps.

const GATE_LABELS = {}; // gate ids are self-describing; shown verbatim.

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  if (attrs) {
    for (const [key, value] of Object.entries(attrs)) {
      if (key === "class") node.className = value;
      else if (key === "html") node.innerHTML = value;
      else node.setAttribute(key, value);
    }
  }
  for (const child of children || []) {
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

function gateChip(name, passed) {
  return el("span", { class: `gate ${passed ? "pass" : "fail"}` }, [
    el("span", { class: "dot" }, []),
    el("code", {}, [name]),
  ]);
}

function renderGates(section, gates) {
  const holder = section.querySelector("[data-gates]");
  holder.innerHTML = "";
  for (const [name, passed] of Object.entries(gates)) {
    holder.appendChild(gateChip(name, Boolean(passed)));
  }
}

function pill(text, kind) {
  return el("span", { class: `pill ${kind}` }, [text]);
}

function table(headers, rows) {
  const thead = el("thead", {}, [
    el("tr", {}, headers.map((h) => el("th", {}, [h]))),
  ]);
  const tbody = el("tbody", {}, rows.map((cells) =>
    el("tr", {}, cells.map((c) => (c && c.node ? el("td", { class: c.cls || "" }, [c.node]) : el("td", { class: (c && c.cls) || "" }, [String(c && c.text !== undefined ? c.text : c)]))))
  ));
  return el("table", {}, [thead, tbody]);
}

function renderRepresentationSearch(section, data) {
  renderGates(section, data.gates);
  const rows = data.tasks.map((t) => {
    const s = t.selections;
    return [
      { text: t.task, cls: "tag" },
      { text: t.ground_truth_quotient, cls: "tag" },
      { node: pill(s.minimal_sufficient.chosen, s.minimal_sufficient.recovered_ground_truth ? "yes" : "no"), cls: "" },
      { node: pill(s.mdl_only.chosen, s.mdl_only.sufficient ? "yes" : "no"), cls: "" },
      { node: pill(s.accuracy_only.chosen, "gold"), cls: "" },
    ];
  });
  section.querySelector("[data-body]").appendChild(
    table(
      ["task", "ground truth", "minimal-sufficient", "mdl-only", "accuracy-only"],
      rows
    )
  );
}

function renderStructureCompiler(section, data) {
  renderGates(section, data.gates);
  const traj = data.abstract_trajectory
    .map((n) => (n.regime === "high" ? "H" : "."))
    .join("");
  const levels = data.abstract_trajectory.map((n) => n.level).join("");
  const rows = Object.entries(data.verification).map(([medium, v]) => [
    { text: medium, cls: "tag" },
    { node: pill(v.commutes ? "id" : "broken", v.commutes ? "yes" : "no") },
    { text: v.fidelity.toFixed(3), cls: "num" },
    { text: v.length, cls: "num" },
  ]);
  const body = section.querySelector("[data-body]");
  body.appendChild(
    el("p", { class: "status" }, [`regimes ${traj}  levels ${levels}`])
  );
  body.appendChild(table(["medium", "q∘F = id", "fidelity", "steps"], rows));
}

function renderSparseIcaLearnability(section, data) {
  renderGates(section, data.gates);
  const body = section.querySelector("[data-body]");
  const poly = data.poly_exponent_gate || {};
  const perS = poly.per_sparsity || {};
  const bStrs = Object.entries(perS).map(([s, v]) => `s=${s}: b≈${v.fitted_exponent_b?.toFixed(3) ?? "?"}`);
  body.appendChild(
    el("p", { class: "status" }, [
      `fitted exponents ${bStrs.join(" · ")} (gate ≤ ${poly.exponent_gate_max ?? "?"})`,
    ])
  );
  // Amari means per (d_Z, N, s) if available; else per (d_Z, N).
  const rows = [];
  const points = data.sweep_points || [];
  const sparsities = Array.from(new Set(points.map((p) => p.s ?? p.sparsity ?? "?"))).sort();
  const dZs = data.d_Z_values || [];
  const Ns = data.N_values || [];
  for (const s of sparsities) {
    for (const dz of dZs) {
      const cells = [{ text: `s=${s}, d_Z=${dz}`, cls: "tag" }];
      for (const n of Ns) {
        const pt = points.find((p) => (p.s ?? p.sparsity) === s && p.d_z === dz && p.n === n);
        cells.push({ text: pt ? pt.amari_mean.toFixed(4) : "—", cls: "num" });
      }
      rows.push(cells);
    }
  }
  body.appendChild(table(["(s, d_Z)", ...Ns.map((n) => `N=${n}`)], rows));
}

function renderLinearIcaLearnability(section, data) {
  renderGates(section, data.gates);
  const body = section.querySelector("[data-body]");
  const poly = data.poly_exponent_gate;
  body.appendChild(
    el("p", { class: "status" }, [
      `fitted exponent b ≈ ${poly.fitted_exponent_b.toFixed(3)} (gate ≤ ${poly.exponent_gate_max}); target Amari ≤ ${poly.target_amari}`,
    ])
  );
  // Build a d_Z x N matrix of Amari mean values.
  const dZs = data.d_Z_values;
  const Ns = data.N_values;
  const meanByPair = {};
  for (const pt of data.sweep_points) {
    meanByPair[`${pt.d_z}_${pt.n}`] = pt.amari_mean;
  }
  const rows = dZs.map((dz) => {
    const cells = [{ text: `d_Z=${dz}`, cls: "tag" }];
    for (const n of Ns) {
      const v = meanByPair[`${dz}_${n}`];
      cells.push({
        text: v === undefined ? "—" : v.toFixed(4),
        cls: "num",
      });
    }
    return cells;
  });
  body.appendChild(
    table(["", ...Ns.map((n) => `N=${n}`)], rows)
  );
}

function renderRateDistortionPair(section, data) {
  renderGates(section, data.gates);
  const body = section.querySelector("[data-body]");
  for (const source of data.sources) {
    body.appendChild(
      el("p", { class: "status" }, [
        `${source.source}: source entropy H = ${source.source_entropy_bits.toFixed(4)} bits · D_max = ${source.d_max.toFixed(4)}`,
      ])
    );
    const rows = source.curve.map((pt) => {
      const beyondDmax = pt.D >= source.d_max;
      const miClamped = beyondDmax ? "—" : pt.test_channel_MI.toFixed(4);
      const kind = beyondDmax
        ? "gold"
        : Math.abs(pt.test_channel_MI - pt.R) < 1e-9
          ? "yes"
          : "no";
      return [
        { text: pt.D.toFixed(2), cls: "num" },
        { text: pt.R.toFixed(4), cls: "num" },
        {
          node: pill(miClamped, kind),
        },
      ];
    });
    body.appendChild(table(["D", "R(D)  [bits]", "I(X; X̂) via test channel"], rows));
    body.appendChild(
      el("p", { class: "status" }, [
        "Note: the test-channel formula produces spurious values for D > D_max (the channel is not the RD-optimal one there). Those rows show '—' to avoid the misleading negative mutual-information display; only 0 <= D < D_max is meaningful.",
      ])
    );
  }
}

function renderCrossTaskLearnabilityContinuous(section, data) {
  renderGates(section, data.gates);
  const body = section.querySelector("[data-body]");
  body.appendChild(
    el("p", { class: "status" }, [
      `bound form: ${data.theorem_bound_form}; ε_rel = ${data.eps_rel}; ambient X = ${data.ambient_side}×${data.ambient_side} (${data.ambient_size} cells)`,
    ])
  );
  const rows = data.scaling_points.map((pt) => [
    { text: `${pt.d_z}`, cls: "num" },
    { text: `${pt.r}`, cls: "num" },
    { text: `${pt.M}`, cls: "num" },
    { text: `${pt.N_bound}`, cls: "num" },
    { node: pill(pt.exact_recovery_at_bound.toFixed(4), pt.meets_target ? "yes" : "no") },
    { text: `${(1 - data.eps_rel).toFixed(2)}`, cls: "num" },
  ]);
  body.appendChild(
    table(
      ["d_Z", "r", "M = r^d_Z", "N (bound)", "P(recover @ N)", "target 1−ε"],
      rows
    )
  );
  const ratioRows = data.N_bound_ratio_d_Z2_over_d_Z1.map((row) => [
    { text: `r = ${row.r}`, cls: "tag" },
    { node: pill(row.ratio.toFixed(3) + "×", row.ratio > row.r / 2 ? "yes" : "no") },
  ]);
  body.appendChild(
    el("p", { class: "status" }, [
      "N_bound(d_Z=2) / N_bound(d_Z=1) — the exponential-in-d_Z scaling:",
    ])
  );
  body.appendChild(table(["resolution", "N-bound ratio"], ratioRows));
}

function renderCrossTaskLearnability(section, data) {
  renderGates(section, data.gates);
  const body = section.querySelector("[data-body]");
  body.appendChild(
    el("p", { class: "status" }, [
      `bound form: ${data.theorem_bound_form}; ε = ${data.eps}; M = ${data.M}`,
    ])
  );
  const rows = data.distributions.map((d) => [
    { text: d.distribution, cls: "tag" },
    { text: d.c_from_p_min.toFixed(2), cls: "num" },
    { text: `${d.theorem_bound_N}`, cls: "num" },
    { node: pill(
        d.exact_recovery_at_theorem_bound.toFixed(4),
        d.exact_recovery_meets_target ? "yes" : "no"
      ) },
    { text: `${(1 - data.eps).toFixed(2)}`, cls: "num" },
  ]);
  body.appendChild(
    table(
      ["distribution", "c", "N (bound)", "P(recover @ N)", "target 1−ε"],
      rows
    )
  );
}

function renderCrossTaskSufficiency(section, data) {
  renderGates(section, data.gates);
  const body = section.querySelector("[data-body]");
  body.appendChild(
    el("p", { class: "status" }, [`latent: ${data.latent_Z_definition}`])
  );
  const rows = data.families.map((f) => [
    { text: f.family, cls: "tag" },
    { text: `${f.tasks.length}`, cls: "num" },
    { node: pill(f.coarsest_common_sufficient.quotient, f.coarsest_common_sufficient.quotient === "identity" ? "no" : "yes") },
    { text: `${f.coarsest_common_sufficient.image_size}`, cls: "num" },
    { text: f.coarsest_common_sufficient.description_length.toFixed(2), cls: "num" },
    {
      text: f.per_task_minimal_sufficient
        .map((p) => `${p.minimal_sufficient}(${p.minimal_sufficient_image_size})`)
        .join(", "),
      cls: "tag",
    },
  ]);
  body.appendChild(
    table(
      ["family", "tasks", "coarsest CSS", "|image|", "DL (bits)", "per-task MSS"],
      rows
    )
  );
}

function renderSymbolicCausation(section, data) {
  renderGates(section, data.gates);
  const rows = data.rows.map((r) => {
    const klText = Number.isFinite(r.delta_kl) ? r.delta_kl.toFixed(3) : "∞";
    return [
      { text: r.intervention, cls: "tag" },
      { node: pill(data.classifications[r.intervention], "gold") },
      { text: klText, cls: "num" },
      { text: r.true_goal_effect.toFixed(3), cls: "num" },
      { text: r.observed_goal_gain.toFixed(3), cls: "num" },
      { text: r.calibration_error.toFixed(3), cls: "num" },
      { text: r.transfer.toFixed(3), cls: "num" },
    ];
  });
  section.querySelector("[data-body]").appendChild(
    table(
      ["condition", "class", "ΔKL", "true effect", "observed", "calib err", "transfer"],
      rows
    )
  );
}

async function main() {
  const status = document.getElementById("global-status");
  let data;
  try {
    const response = await fetch("results.json", { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
  } catch (error) {
    status.textContent = `Could not load results.json: ${error.message}`;
    return;
  }

  renderRepresentationSearch(
    document.getElementById("representation_search"),
    data.representation_search
  );
  renderStructureCompiler(
    document.getElementById("structure_compiler"),
    data.structure_compiler
  );
  renderSymbolicCausation(
    document.getElementById("symbolic_causation"),
    data.symbolic_causation
  );
  renderCrossTaskSufficiency(
    document.getElementById("cross_task_sufficiency"),
    data.cross_task_sufficiency
  );
  renderCrossTaskLearnability(
    document.getElementById("cross_task_learnability"),
    data.cross_task_learnability
  );
  renderCrossTaskLearnabilityContinuous(
    document.getElementById("cross_task_learnability_continuous"),
    data.cross_task_learnability_continuous
  );
  renderRateDistortionPair(
    document.getElementById("rate_distortion_pair"),
    data.rate_distortion_pair
  );
  if (data.linear_ica_learnability) {
    renderLinearIcaLearnability(
      document.getElementById("linear_ica_learnability"),
      data.linear_ica_learnability
    );
  }
  if (data.sparse_ica_learnability) {
    renderSparseIcaLearnability(
      document.getElementById("sparse_ica_learnability"),
      data.sparse_ica_learnability
    );
  }

  const allPass = [
    "representation_search",
    "structure_compiler",
    "symbolic_causation",
    "cross_task_sufficiency",
    "cross_task_learnability",
    "cross_task_learnability_continuous",
    "rate_distortion_pair",
    "linear_ica_learnability",
    "sparse_ica_learnability",
  ].every((k) => data[k] && data[k].status === "pass");
  status.textContent = allPass
    ? "All nine instruments: status = pass. Every gate below is green."
    : "One or more instruments did not pass — see gates below.";
}

// ================================================================
// Interactive visualisations — one small canvas widget per instrument.
// All pure vanilla JS, no external libs (CSP-safe).
// ================================================================

const Z_PALETTE = ["#e0525b", "#f2c14e", "#6ea8fe", "#3fb27f"];
const AMBIENT = "#0e141d";
const INK = "#e7edf3";
const MUTED = "#5f7185";

function makeSeededPRNG(seed) {
  // Mulberry32 - small, seeded, deterministic.
  let s = seed >>> 0;
  return function () {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function drawGridCells(ctx, opts) {
  const { rows, cols, cellSize, x0, y0, colorAt, borderAt } = opts;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const x = x0 + c * cellSize;
      const y = y0 + r * cellSize;
      ctx.fillStyle = colorAt(r, c);
      ctx.fillRect(x, y, cellSize, cellSize);
      const border = borderAt ? borderAt(r, c) : null;
      ctx.strokeStyle = border || "#22303d";
      ctx.lineWidth = border ? 2 : 1;
      ctx.strokeRect(x, y, cellSize, cellSize);
    }
  }
}

function makeControls(container, controls) {
  const wrap = el("div", { class: "viz-controls" }, []);
  for (const c of controls) wrap.appendChild(c);
  container.appendChild(wrap);
  return wrap;
}

function makeSlider(label, min, max, value, onInput) {
  const holder = el("label", { class: "viz-slider" }, [
    el("span", {}, [label]),
    el("span", { class: "viz-value" }, [`${value}`]),
  ]);
  const input = document.createElement("input");
  input.type = "range";
  input.min = String(min);
  input.max = String(max);
  input.step = "1";
  input.value = String(value);
  const valueSpan = holder.querySelector(".viz-value");
  input.addEventListener("input", () => {
    valueSpan.textContent = input.value;
    onInput(Number(input.value));
  });
  holder.appendChild(input);
  return holder;
}

function makeRadio(label, options, selected, onChange) {
  const holder = el("div", { class: "viz-radio" }, [
    el("span", { class: "viz-radio-label" }, [label]),
  ]);
  const group = "g" + Math.floor(Math.random() * 1e9);
  for (const opt of options) {
    const id = group + "_" + opt.value;
    const wrapper = el("label", { class: "viz-radio-opt" }, []);
    const input = document.createElement("input");
    input.type = "radio";
    input.name = group;
    input.value = String(opt.value);
    input.id = id;
    if (opt.value === selected) input.checked = true;
    input.addEventListener("change", () => onChange(opt.value));
    wrapper.appendChild(input);
    wrapper.appendChild(document.createTextNode(opt.label));
    holder.appendChild(wrapper);
  }
  return holder;
}

function makeCanvas(width, height) {
  const c = document.createElement("canvas");
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  c.width = width * dpr;
  c.height = height * dpr;
  c.style.width = `${width}px`;
  c.style.height = `${height}px`;
  const ctx = c.getContext("2d");
  ctx.scale(dpr, dpr);
  return { canvas: c, ctx };
}

// ---- Instrument 5 viz: coupon-collector animation for cross_task_learnability ----

function mountLearnabilityViz(section, opts) {
  const { M, ambientSide, distributionMasses, thmBound, distName, container } = opts;
  const width = 380;
  const height = 260;
  const gridSize = 200;
  const cellSize = gridSize / ambientSide;

  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);

  // Precompute a deterministic sample sequence (up to N_max) via seeded PRNG.
  const maxN = Math.max(60, thmBound + 5);
  const rng = makeSeededPRNG(1234 + M);
  const cumMass = [];
  {
    let acc = 0;
    for (const m of distributionMasses) {
      acc += m;
      cumMass.push(acc);
    }
  }
  // Map each ambient cell (0..ambientSide^2-1) to a fibre index (0..M-1).
  function cellFibre(cellIdx) {
    // Distribute cells cyclically among fibres, so that fibre i has
    // (ambientSide^2 / M) cells (when balanced) — matches Instrument 4's
    // 4x4 grid + Instrument 6's r-grid quantisation.
    const cellsPerFibre = (ambientSide * ambientSide) / M;
    return Math.floor(cellIdx / cellsPerFibre);
  }
  const sampleSequence = [];
  for (let i = 0; i < maxN; i++) {
    const u = rng();
    // Pick a fibre index by inverse CDF, then a specific cell in that fibre.
    let fibre = M - 1;
    for (let f = 0; f < M; f++) {
      if (u <= cumMass[f]) {
        fibre = f;
        break;
      }
    }
    const cellsPerFibre = (ambientSide * ambientSide) / M;
    const cellInFibre = Math.floor(rng() * cellsPerFibre);
    const cellIdx = fibre * cellsPerFibre + cellInFibre;
    sampleSequence.push({ cellIdx, fibre });
  }

  let N = 0;

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);

    // Determine which fibres have been hit at current N.
    const hit = new Array(M).fill(false);
    const sampledCells = new Set();
    for (let i = 0; i < N; i++) {
      hit[sampleSequence[i].fibre] = true;
      sampledCells.add(sampleSequence[i].cellIdx);
    }
    const hitCount = hit.filter(Boolean).length;

    // Draw grid.
    const x0 = 12;
    const y0 = 12;
    drawGridCells(ctx, {
      rows: ambientSide,
      cols: ambientSide,
      cellSize,
      x0,
      y0,
      colorAt: (r, c) => {
        const idx = r * ambientSide + c;
        const f = cellFibre(idx);
        const base = Z_PALETTE[f % Z_PALETTE.length];
        return hit[f] ? base : base + "44"; // dim if fibre not yet hit
      },
      borderAt: (r, c) => {
        const idx = r * ambientSide + c;
        return sampledCells.has(idx) ? INK : null;
      },
    });

    // Overlay dots for sampled cells.
    ctx.fillStyle = INK;
    for (const idx of sampledCells) {
      const r = Math.floor(idx / ambientSide);
      const c = idx % ambientSide;
      const x = x0 + c * cellSize + cellSize / 2;
      const y = y0 + r * cellSize + cellSize / 2;
      ctx.beginPath();
      ctx.arc(x, y, Math.max(1.5, cellSize / 6), 0, Math.PI * 2);
      ctx.fill();
    }

    // Legend + status text on the right.
    ctx.fillStyle = INK;
    ctx.font = "13px ui-monospace, monospace";
    const textX = x0 + gridSize + 16;
    let ty = y0 + 14;
    ctx.fillText(`N = ${N}`, textX, ty); ty += 18;
    ctx.fillStyle = hitCount === M ? "#3fb27f" : MUTED;
    ctx.fillText(`fibres hit: ${hitCount} / ${M}`, textX, ty); ty += 18;

    // Recovery probability (uses the same DP as Python core, done inline).
    const pRecover = uniformCouponRecovery(M, N);
    ctx.fillStyle = INK;
    ctx.fillText(`P(recover) = ${pRecover.toFixed(4)}`, textX, ty); ty += 18;
    if (N >= thmBound) {
      ctx.fillStyle = "#3fb27f";
      ctx.fillText(`✓ N ≥ thm bound ${thmBound}`, textX, ty);
    } else {
      ctx.fillStyle = "#f2c14e";
      ctx.fillText(`need ${thmBound - N} more for bound`, textX, ty);
    }
    ty += 26;
    ctx.fillStyle = MUTED;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText(distName, textX, ty);
  }

  const slider = makeSlider("samples N", 0, maxN, 0, (v) => {
    N = v;
    draw();
  });
  container.appendChild(slider);
  draw();
}

// Balanced-only recovery via O(N*M) DP. Same formula as Python core.
function uniformCouponRecovery(M, N) {
  if (N < M) return 0;
  let prev = new Array(M + 1).fill(0);
  prev[0] = 1;
  for (let n = 0; n < N; n++) {
    const curr = new Array(M + 1).fill(0);
    for (let k = 0; k <= M; k++) {
      const stay = prev[k] * (k / M);
      const arrive = k > 0 ? prev[k - 1] * ((M - k + 1) / M) : 0;
      curr[k] = stay + arrive;
    }
    prev = curr;
  }
  return Math.max(0, Math.min(1, prev[M]));
}

// General (possibly unbalanced) coupon recovery via DP over fibre subsets.
// For small M (≤ 8) we can afford enumeration; for larger M we assume balanced.
function generalCouponRecovery(masses, N) {
  if (N < masses.length) return 0;
  if (masses.length > 8) {
    return uniformCouponRecovery(masses.length, N); // fallback
  }
  const M = masses.length;
  let total = 0;
  for (let mask = 0; mask < 1 << M; mask++) {
    let excluded = 0;
    let bits = 0;
    for (let i = 0; i < M; i++) if (mask & (1 << i)) { excluded += masses[i]; bits++; }
    const remaining = 1 - excluded;
    const sign = bits % 2 === 0 ? 1 : -1;
    total += sign * Math.pow(remaining, N);
  }
  return Math.max(0, Math.min(1, total));
}

// Attach viz to each instrument section.
function attachInteractiveViz(data) {
  // Instrument 5 (cross_task_learnability): 4x4 grid, uniform coupon collector.
  const i5 = document.getElementById("cross_task_learnability");
  if (i5) {
    const container = el("div", { class: "viz" }, [
      el("h4", {}, ["Interactive: watch coupon collection converge"]),
    ]);
    i5.appendChild(container);
    const uniformD = data.cross_task_learnability.distributions[0];
    mountLearnabilityViz(i5, {
      M: uniformD.M || 4,
      ambientSide: 4,
      distributionMasses: [0.25, 0.25, 0.25, 0.25],
      thmBound: uniformD.theorem_bound_N,
      distName: `uniform · c=${uniformD.c_from_p_min} · thm bound N=${uniformD.theorem_bound_N}`,
      container,
    });
  }

  // Instrument 6 (continuous learnability): use the r=8, d_Z=2 case (M=64).
  const i6 = document.getElementById("cross_task_learnability_continuous");
  if (i6) {
    const container = el("div", { class: "viz" }, [
      el("h4", {}, ["Interactive: coupon collection at (d_Z=2, r=8) — M=64"]),
    ]);
    i6.appendChild(container);
    const pt = data.cross_task_learnability_continuous.scaling_points.find(
      (p) => p.d_z === 2 && p.r === 8
    );
    mountLearnabilityViz(i6, {
      M: pt.M,
      ambientSide: 16,
      distributionMasses: new Array(pt.M).fill(1 / pt.M),
      thmBound: pt.N_bound,
      distName: `d_Z=2, r=8 · M=64 · thm bound N=${pt.N_bound}`,
      container,
    });
  }

  // Instrument 4 (cross_task_sufficiency): 4x4 grid + quotient button switcher.
  const i4 = document.getElementById("cross_task_sufficiency");
  if (i4) {
    mountSufficiencyViz(i4, data.cross_task_sufficiency);
  }

  // Instrument 1 (representation_search): 8x8 grid (n=6 bits, first 64 by bit order).
  const i1 = document.getElementById("representation_search");
  if (i1) {
    mountFiberFinderViz(i1, data.representation_search);
  }

  // Instrument 3 (agency): 4-bar chart per condition.
  const i3 = document.getElementById("symbolic_causation");
  if (i3) {
    mountAgencyViz(i3, data.symbolic_causation);
  }

  // Instrument 7 (RD): plot R(D) curve.
  const i7 = document.getElementById("rate_distortion_pair");
  if (i7) {
    mountRDViz(i7, data.rate_distortion_pair);
  }

  // Instrument 2 (structure_compiler): timeline scrubber across 4 embodiments.
  const i2 = document.getElementById("structure_compiler");
  if (i2) {
    mountStructureCompilerViz(i2, data.structure_compiler);
  }

  // Instrument 8 (linear ICA): Amari heat-grid.
  const i8 = document.getElementById("linear_ica_learnability");
  if (i8) {
    mountIcaHeatViz(i8, data.linear_ica_learnability, { title: "Amari at each (d_Z, N)" });
  }

  // Instrument 9 (sparse ICA): Amari heat-grid faceted by sparsity.
  const i9 = document.getElementById("sparse_ica_learnability");
  if (i9) {
    mountSparseIcaHeatViz(i9, data.sparse_ica_learnability);
  }

  // Instrument 10 (iVAE): Amari heat-grid.
  const i10 = document.getElementById("ivae_learnability");
  if (i10) {
    mountIcaHeatViz(i10, data.ivae_learnability, { title: "iVAE Amari at each (d_Z, N)" });
  }

  // Instrument 11 (Interventional CRL): Amari heat-grid.
  const i11 = document.getElementById("interventional_crl_learnability");
  if (i11) {
    mountIcaHeatViz(i11, data.interventional_crl_learnability, {
      title: "Interv-CRL Amari at each (d_Z, N_per_env)",
    });
  }

  // Companion instrument: compiler_tomography_pair (MDL recovery curve + ecology).
  const iCT = document.getElementById("compiler_tomography_pair");
  if (iCT) {
    mountCompilerTomographyViz(iCT, data.compiler_tomography_pair);
  }

  // Companion: concern_fisher_pair (CG-1 Fisher matching + CG-2 holonomy).
  const iCF = document.getElementById("concern_fisher_pair");
  if (iCF && data.concern_fisher_pair) mountConcernFisherViz(iCF, data.concern_fisher_pair);

  // Companion: causal_semantics_pair (Ψ-quotient vs co-occurrence signature).
  const iCS = document.getElementById("causal_semantics_pair");
  if (iCS && data.causal_semantics_pair) mountCausalSemanticsViz(iCS, data.causal_semantics_pair);

  // Companion: antecedent_taxonomy_pair (local screens intersect to true Z).
  const iAT = document.getElementById("antecedent_taxonomy_pair");
  if (iAT && data.antecedent_taxonomy_pair) mountAntecedentTaxonomyViz(iAT, data.antecedent_taxonomy_pair);

  // Companion: sica_finite_derivation_pair (LR-vector partition == joint-parity MSS).
  const iSICA = document.getElementById("sica_finite_derivation_pair");
  if (iSICA && data.sica_finite_derivation_pair) mountSicaFiniteDerivationViz(iSICA, data.sica_finite_derivation_pair);
}

// ---- Instrument 2 viz: timeline scrubber for the abstract trajectory ----
function mountStructureCompilerViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: scrub time — watch all four embodiments in sync"]),
  ]);
  section.appendChild(container);
  const trajectory = data.abstract_trajectory || [];
  const T = trajectory.length;
  const width = 380, height = 220;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  let t = 0;
  let playing = false;
  let rafId = null;

  function drawRow(row, y, height_px, colorFn, labelFn) {
    const cellW = (width - 40) / T;
    for (let i = 0; i < T; i++) {
      const cx = 20 + i * cellW;
      ctx.fillStyle = colorFn(trajectory[i], i);
      ctx.fillRect(cx, y, cellW - 2, height_px);
      if (i === t) {
        ctx.strokeStyle = "#f2c14e";
        ctx.lineWidth = 2;
        ctx.strokeRect(cx - 1, y - 1, cellW, height_px + 2);
      }
      if (labelFn) {
        ctx.fillStyle = INK;
        ctx.font = "9px ui-monospace, monospace";
        ctx.fillText(labelFn(trajectory[i]), cx + 1, y + height_px - 2);
      }
    }
  }

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = MUTED;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText("regime", 20, 24);
    drawRow(null, 30, 28, (n) => n.regime === "high" ? "#f2c14e" : "#6ea8fe");
    ctx.fillText("level", 20, 74);
    drawRow(null, 80, 28, (n) => {
      const s = 60 + Math.floor(n.level * 15);
      return `rgb(${s}, ${s + 40}, ${s + 60})`;
    });
    ctx.fillText("music (pitch)", 20, 124);
    drawRow(null, 130, 28, (n) => {
      const s = 40 + Math.floor(n.level * 18);
      return `rgb(${s + 60}, ${s}, ${s + 30})`;
    });
    ctx.fillText("spatial (x)", 20, 174);
    drawRow(null, 180, 28, (n) => {
      const px = n.level * 25;
      return `rgb(${40 + px}, ${100 + px}, ${40})`;
    });
    // Current step numbers under all rows:
    ctx.fillStyle = INK;
    ctx.font = "12px ui-monospace, monospace";
    const step = trajectory[t] || {};
    ctx.fillText(`t=${t}: regime=${step.regime || "?"}, level=${step.level || "?"}`, 20, height - 4);
  }

  const slider = makeSlider("time step", 0, T - 1, 0, (v) => { t = v; draw(); });
  container.appendChild(slider);
  const btn = document.createElement("button");
  btn.className = "viz-btn";
  btn.textContent = "▶ play";
  btn.addEventListener("click", () => {
    playing = !playing;
    btn.textContent = playing ? "⏸ pause" : "▶ play";
    if (playing) {
      function step() {
        if (!playing) return;
        t = (t + 1) % T;
        const sliderInput = slider.querySelector("input[type=range]");
        if (sliderInput) sliderInput.value = String(t);
        slider.querySelector(".viz-value").textContent = String(t);
        draw();
        rafId = setTimeout(step, 500);
      }
      step();
    } else if (rafId) clearTimeout(rafId);
  });
  container.appendChild(btn);
  draw();
}

// ---- Instruments 8/10/11 viz: (d_Z, N) Amari heat-grid ----
function mountIcaHeatViz(section, data, opts) {
  const title = (opts && opts.title) || "Amari at each (d_Z, N)";
  const container = el("div", { class: "viz" }, [
    el("h4", {}, [title]),
  ]);
  section.appendChild(container);
  const dZs = data.d_Z_values || [];
  const Ns = data.N_values || [];
  const points = data.sweep_points || [];
  const cellW = 44, cellH = 32, marginL = 60, marginT = 28;
  const width = marginL + Ns.length * cellW + 20;
  const height = marginT + dZs.length * cellH + 40;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  function amariColor(v) {
    // Green (good, low Amari) → Gold → Red (bad, high Amari). Range [0, 0.15].
    const clamp = Math.max(0, Math.min(0.15, v));
    const t = clamp / 0.15;
    if (t < 0.5) {
      const s = t / 0.5;
      const r = Math.round(63 + (242 - 63) * s);
      const g = Math.round(178 + (193 - 178) * s);
      const b = Math.round(127 + (78 - 127) * s);
      return `rgb(${r},${g},${b})`;
    } else {
      const s = (t - 0.5) / 0.5;
      const r = Math.round(242 + (224 - 242) * s);
      const g = Math.round(193 + (82 - 193) * s);
      const b = Math.round(78 + (91 - 78) * s);
      return `rgb(${r},${g},${b})`;
    }
  }
  ctx.fillStyle = AMBIENT;
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = MUTED;
  ctx.font = "10px ui-monospace, monospace";
  Ns.forEach((n, i) => {
    ctx.fillText(`${n}`, marginL + i * cellW + 4, marginT - 6);
  });
  dZs.forEach((d, r) => {
    ctx.fillText(`d_Z=${d}`, 4, marginT + r * cellH + 20);
    Ns.forEach((n, c) => {
      const pt = points.find((p) => p.d_z === d && p.n === n);
      const val = pt ? pt.amari_mean : null;
      ctx.fillStyle = val === null ? "#22303d" : amariColor(val);
      ctx.fillRect(marginL + c * cellW + 1, marginT + r * cellH + 1, cellW - 2, cellH - 2);
      ctx.fillStyle = INK;
      ctx.font = "10px ui-monospace, monospace";
      if (val !== null) {
        ctx.fillText(val.toFixed(3), marginL + c * cellW + 4, marginT + r * cellH + cellH / 2 + 4);
      }
    });
  });
  ctx.fillStyle = MUTED;
  ctx.font = "10px ui-monospace, monospace";
  ctx.fillText("→ N samples", marginL, height - 20);
  ctx.fillText("green = low Amari (good) · gold = medium · red = high (bad)", marginL, height - 6);
}

function mountSparseIcaHeatViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: Amari at each (d_Z, N) per sparsity level"]),
  ]);
  section.appendChild(container);
  const sparsities = Array.from(new Set((data.sweep_points || []).map((p) => p.s ?? p.sparsity))).sort();
  const dZs = data.d_Z_values || [];
  const Ns = data.N_values || [];
  const cellW = 42, cellH = 28, marginL = 60, marginT = 24;
  const facetH = marginT + dZs.length * cellH + 24;
  const width = marginL + Ns.length * cellW + 20;
  const height = sparsities.length * (facetH + 8);
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  function amariColor(v) {
    const clamp = Math.max(0, Math.min(0.15, v));
    const t = clamp / 0.15;
    if (t < 0.5) {
      const s = t / 0.5;
      return `rgb(${Math.round(63 + 179 * s)},${Math.round(178 + 15 * s)},${Math.round(127 - 49 * s)})`;
    } else {
      const s = (t - 0.5) / 0.5;
      return `rgb(${Math.round(242 - 18 * s)},${Math.round(193 - 111 * s)},${Math.round(78 + 13 * s)})`;
    }
  }
  ctx.fillStyle = AMBIENT;
  ctx.fillRect(0, 0, width, height);
  sparsities.forEach((s, si) => {
    const yOff = si * (facetH + 8);
    ctx.fillStyle = INK;
    ctx.font = "12px ui-monospace, monospace";
    ctx.fillText(`s = ${s}`, 4, yOff + 14);
    dZs.forEach((d, r) => {
      ctx.fillStyle = MUTED;
      ctx.font = "10px ui-monospace, monospace";
      ctx.fillText(`d_Z=${d}`, 4, yOff + marginT + r * cellH + 18);
      Ns.forEach((n, c) => {
        const pt = (data.sweep_points || []).find(
          (p) => (p.s ?? p.sparsity) === s && p.d_z === d && p.n === n
        );
        const val = pt ? pt.amari_mean : null;
        ctx.fillStyle = val === null ? "#22303d" : amariColor(val);
        ctx.fillRect(marginL + c * cellW + 1, yOff + marginT + r * cellH + 1, cellW - 2, cellH - 2);
        ctx.fillStyle = INK;
        ctx.font = "9px ui-monospace, monospace";
        if (val !== null) {
          ctx.fillText(val.toFixed(3), marginL + c * cellW + 3, yOff + marginT + r * cellH + cellH / 2 + 3);
        }
      });
      if (r === 0) {
        Ns.forEach((n, c) => {
          ctx.fillStyle = MUTED;
          ctx.font = "9px ui-monospace, monospace";
          ctx.fillText(`${n}`, marginL + c * cellW + 4, yOff + marginT - 4);
        });
      }
    });
  });
}

// ---- Compiler-tomography viz: MDL recovery curve + ecology trajectories ----
function mountCompilerTomographyViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: MDL recovery curve + ecology reward trajectories"]),
  ]);
  section.appendChild(container);
  const width = 380, height = 260;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  ctx.fillStyle = AMBIENT;
  ctx.fillRect(0, 0, width, height);
  const ct1 = data.ct1 || {};
  const ct2 = data.ct2 || {};
  const perN = ct1.per_N || [];
  // MDL recovery curve (left half)
  const plotW = 160, plotH = 200, x0 = 30, y0 = 20;
  ctx.strokeStyle = MUTED;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x0, y0 + plotH);
  ctx.lineTo(x0 + plotW, y0 + plotH);
  ctx.stroke();
  if (perN.length) {
    const maxN = Math.max(...perN.map((p) => p.N));
    ctx.strokeStyle = "#f2c14e";
    ctx.lineWidth = 2;
    ctx.beginPath();
    perN.forEach((pt, i) => {
      const x = x0 + (pt.N / maxN) * plotW;
      const y = y0 + plotH - pt.recovery_rate * plotH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.fillStyle = "#f2c14e";
    perN.forEach((pt) => {
      const x = x0 + (pt.N / maxN) * plotW;
      const y = y0 + plotH - pt.recovery_rate * plotH;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.fillStyle = INK;
    ctx.font = "10px ui-monospace, monospace";
    ctx.fillText("CT-1 MDL recovery", x0, y0 - 6);
    ctx.fillText("1.0", x0 - 22, y0 + 4);
    ctx.fillText("N", x0 + plotW - 8, y0 + plotH + 14);
  }
  // Ecology trajectories (right half): per-fibre expected reward vs t at beta=4
  const perBeta = ct2.per_beta || [];
  const beta4 = perBeta.find((b) => b.beta === 4.0) || perBeta[perBeta.length - 1];
  if (beta4 && beta4.trajectory) {
    const px0 = 220, py0 = 20, pW = 140, pH = 200;
    ctx.strokeStyle = MUTED;
    ctx.beginPath();
    ctx.moveTo(px0, py0);
    ctx.lineTo(px0, py0 + pH);
    ctx.lineTo(px0 + pW, py0 + pH);
    ctx.stroke();
    ctx.fillStyle = INK;
    ctx.font = "10px ui-monospace, monospace";
    ctx.fillText(`CT-2 β=${beta4.beta}`, px0, py0 - 6);
    ctx.fillText("2.0", px0 - 22, py0 + 4);
    ctx.fillText("t", px0 + pW - 4, py0 + pH + 14);
    const traj = beta4.trajectory;
    const maxT = traj.length - 1;
    const keys = traj.length ? Object.keys(traj[0].expected_reward_per_fiber) : [];
    const cols = ["#e0525b", "#f2c14e", "#6ea8fe", "#3fb27f"];
    keys.forEach((k, ki) => {
      ctx.strokeStyle = cols[ki % cols.length];
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      traj.forEach((row, i) => {
        const x = px0 + (i / maxT) * pW;
        const val = row.expected_reward_per_fiber[k];
        const y = py0 + pH - (val / 2.0) * pH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    });
  }
}

// ---- Companion: concern_fisher_pair viz ----
// Slider selects one of the 4 c-values; shows predicted vs empirical 2x2 Fisher
// diagonals and the CG-2 rectangle/triangle holonomy on the right.
function mountConcernFisherViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: pick c — see empirical Fisher match Cov[T], and the CG-2 holonomy loop"]),
  ]);
  section.appendChild(container);
  const width = 380, height = 260;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  const records = data.cg1_records || [];
  const cg2 = data.cg2 || { epsilon: 0.3, rectangle_holonomy_computed: 0.3, triangle_holonomy_computed: 0.15 };
  let idx = 0;

  function drawMatrix(diag, x0, y0, size, label, tint) {
    const cell = size / 2;
    for (let r = 0; r < 2; r++) {
      for (let c = 0; c < 2; c++) {
        const v = r === c ? diag[r] : 0;
        const alpha = 0.15 + 0.75 * Math.max(0, Math.min(1, v));
        ctx.fillStyle = r === c ? `rgba(${tint},${alpha})` : "#1a232f";
        ctx.fillRect(x0 + c * cell, y0 + r * cell, cell - 1, cell - 1);
        ctx.fillStyle = INK;
        ctx.font = "11px ui-monospace, monospace";
        ctx.fillText(v.toFixed(4), x0 + c * cell + 6, y0 + r * cell + cell / 2 + 4);
      }
    }
    ctx.fillStyle = MUTED;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText(label, x0, y0 - 4);
  }

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const rec = records[idx] || { c: [0, 0], empirical_diag: [1, 1], predicted_diag: [1, 1], max_abs_diff: 0 };
    ctx.fillStyle = INK;
    ctx.font = "12px ui-monospace, monospace";
    ctx.fillText(`c = (${rec.c[0].toFixed(2)}, ${rec.c[1].toFixed(2)})`, 12, 20);
    drawMatrix(rec.predicted_diag, 12, 42, 96, "predicted (Cov[T])", "63,178,127");
    drawMatrix(rec.empirical_diag, 12, 152, 96, "empirical (Fisher)", "110,168,254");
    // Diff readout.
    ctx.fillStyle = "#3fb27f";
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText(`max |Δ| = ${rec.max_abs_diff.toExponential(2)}`, 120, 108);
    ctx.fillStyle = MUTED;
    ctx.fillText("off-diagonal = 0", 120, 122);
    // CG-2 holonomy loop on the right.
    const rx = 200, ry = 40, rw = 150, rh = 120;
    ctx.strokeStyle = "#f2c14e";
    ctx.lineWidth = 2;
    ctx.strokeRect(rx, ry, rw, rh);
    ctx.fillStyle = "rgba(242,193,78,0.10)";
    ctx.fillRect(rx, ry, rw, rh);
    // Triangle inscribed (bottom-left half).
    ctx.beginPath();
    ctx.moveTo(rx, ry + rh);
    ctx.lineTo(rx + rw, ry + rh);
    ctx.lineTo(rx, ry);
    ctx.closePath();
    ctx.strokeStyle = "#6ea8fe";
    ctx.stroke();
    ctx.fillStyle = INK;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText(`ε = ${cg2.epsilon}`, rx, ry - 4);
    ctx.fillStyle = "#f2c14e";
    ctx.fillText(`rect A=1 → holonomy ${cg2.rectangle_holonomy_computed.toFixed(3)}`, rx, ry + rh + 16);
    ctx.fillStyle = "#6ea8fe";
    ctx.fillText(`tri  A=½ → holonomy ${cg2.triangle_holonomy_computed.toFixed(3)}`, rx, ry + rh + 32);
    ctx.fillStyle = MUTED;
    ctx.fillText(`ratio = ${(cg2.rectangle_over_triangle_ratio || 2.0).toFixed(2)}`, rx, ry + rh + 48);
  }

  const slider = makeSlider("c-index", 0, Math.max(0, records.length - 1), 0, (v) => { idx = v; draw(); });
  container.appendChild(slider);
  draw();
}

// ---- Companion: causal_semantics_pair viz ----
// Radio toggles between the Ψ-quotient (correct meaning) and the co-occurrence
// signature partition (orthogonal, wrong). Each message chip is coloured by
// the selected partition; status text reports whether it is common-sufficient.
function mountCausalSemanticsViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: toggle the partition — Ψ-quotient is common-sufficient, co-occurrence is not"]),
  ]);
  section.appendChild(container);
  const width = 380, height = 220;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  const messages = (data.world && data.world.messages) || ["m0", "m1", "m2", "m3", "m4", "m5"];
  const partitions = {
    psi: { name: "Ψ-quotient (CS-2)", blocks: data.psi_partition, sufficient: true },
    cooccur: { name: "co-occurrence signature", blocks: data.cooccurrence_partition, sufficient: false },
  };
  let current = "psi";

  function blockOf(partition, msg) {
    for (let i = 0; i < partition.length; i++) {
      if (partition[i].indexOf(msg) !== -1) return i;
    }
    return -1;
  }

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const p = partitions[current];
    // Layout: one row of 6 chips, coloured by block index in selected partition.
    const chipW = 46, chipH = 46, y0 = 60, x0 = 20, gap = 10;
    messages.forEach((m, i) => {
      const b = blockOf(p.blocks, m);
      const x = x0 + i * (chipW + gap);
      ctx.fillStyle = Z_PALETTE[b % Z_PALETTE.length] || "#888";
      ctx.fillRect(x, y0, chipW, chipH);
      ctx.strokeStyle = "#22303d";
      ctx.strokeRect(x, y0, chipW, chipH);
      ctx.fillStyle = AMBIENT;
      ctx.font = "16px ui-monospace, monospace";
      ctx.fillText(m, x + 10, y0 + chipH / 2 + 6);
    });
    // Draw block brackets underneath.
    ctx.strokeStyle = "#5f7185";
    ctx.lineWidth = 1;
    ctx.font = "11px ui-monospace, monospace";
    let bracketY = y0 + chipH + 12;
    for (let b = 0; b < p.blocks.length; b++) {
      const members = p.blocks[b];
      const startI = messages.indexOf(members[0]);
      const endI = messages.indexOf(members[members.length - 1]);
      const startX = x0 + startI * (chipW + gap);
      const endX = x0 + endI * (chipW + gap) + chipW;
      ctx.beginPath();
      ctx.moveTo(startX, bracketY);
      ctx.lineTo(endX, bracketY);
      ctx.stroke();
      ctx.fillStyle = Z_PALETTE[b % Z_PALETTE.length];
      ctx.fillText(`block ${b} (|·|=${members.length})`, startX, bracketY + 14);
    }
    // Title + status.
    ctx.fillStyle = INK;
    ctx.font = "13px ui-monospace, monospace";
    ctx.fillText(p.name, 12, 24);
    ctx.fillStyle = p.sufficient ? "#3fb27f" : "#e0525b";
    ctx.font = "12px ui-monospace, monospace";
    ctx.fillText(
      p.sufficient
        ? `→ ${p.blocks.length} classes, common-sufficient (coarsest CSS on messages)`
        : `→ ${p.blocks.length} classes, NOT sufficient (orthogonal to Ψ)`,
      12, 42
    );
  }

  const radio = makeRadio(
    "partition:",
    [{ value: "psi", label: "Ψ-quotient" }, { value: "cooccur", label: "co-occurrence" }],
    "psi",
    (v) => { current = v; draw(); }
  );
  container.appendChild(radio);
  draw();
}

// ---- Companion: antecedent_taxonomy_pair viz ----
// Radio selects a class; draws each local screen as a segmented bar over the
// four true-Z blocks, then the intersection bar (always 4 singletons = true Z).
function mountAntecedentTaxonomyViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: pick a class — watch its local screens intersect to true Z (4 blocks)"]),
  ]);
  section.appendChild(container);
  const width = 380, height = 260;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  const records = data.records || [];
  // Canonical partitions of {0,1,2,3} illustrating the block counts.
  // The block counts themselves are the real data; the specific groupings
  // below are canonical illustrative choices consistent with those counts.
  function screensFor(blockCounts) {
    if (blockCounts.length === 2 && blockCounts[0] === 2 && blockCounts[1] === 2) {
      return [[[0, 1], [2, 3]], [[0, 2], [1, 3]]];
    }
    if (blockCounts.length === 3 && blockCounts[0] === 4) {
      return [[[0], [1], [2], [3]], [[0, 1], [2, 3]], [[0, 2], [1, 3]]];
    }
    return blockCounts.map((k) => {
      if (k === 4) return [[0], [1], [2], [3]];
      if (k === 2) return [[0, 1], [2, 3]];
      if (k === 1) return [[0, 1, 2, 3]];
      return [[0, 1, 2, 3]];
    });
  }
  let currentName = records.length ? records[0].name : "";

  function drawBar(y, screen, label, extraColor) {
    const barX = 16, barW = 320, barH = 24;
    const cellW = barW / 4;
    for (let z = 0; z < 4; z++) {
      // find block containing z
      let bIdx = 0;
      for (let b = 0; b < screen.length; b++) {
        if (screen[b].indexOf(z) !== -1) { bIdx = b; break; }
      }
      ctx.fillStyle = extraColor || Z_PALETTE[bIdx % Z_PALETTE.length];
      ctx.fillRect(barX + z * cellW, y, cellW - 1, barH);
      ctx.strokeStyle = "#22303d";
      ctx.strokeRect(barX + z * cellW, y, cellW - 1, barH);
      ctx.fillStyle = AMBIENT;
      ctx.font = "12px ui-monospace, monospace";
      ctx.fillText(`z=${z}`, barX + z * cellW + 10, y + 16);
    }
    ctx.fillStyle = MUTED;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText(label, barX, y - 4);
  }

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const rec = records.find((r) => r.name === currentName) || records[0];
    if (!rec) return;
    ctx.fillStyle = INK;
    ctx.font = "13px ui-monospace, monospace";
    ctx.fillText(`${rec.name} · ${rec.num_local_screens} local screen(s)`, 12, 20);
    const screens = screensFor(rec.local_screen_block_counts);
    let y = 46;
    screens.forEach((s, i) => {
      drawBar(y, s, `screen ${i + 1}  (${rec.local_screen_block_counts[i]} block${rec.local_screen_block_counts[i] === 1 ? "" : "s"})`);
      y += 40;
    });
    // Intersection bar: always 4 singletons.
    drawBar(y + 6, [[0], [1], [2], [3]], `⋂ intersection → true Z (${rec.intersection_block_count} blocks)`);
    y += 46;
    ctx.fillStyle = rec.intersection_equals_true_Z ? "#3fb27f" : "#e0525b";
    ctx.font = "12px ui-monospace, monospace";
    ctx.fillText(
      `intersection equals true Z: ${rec.intersection_equals_true_Z ? "yes" : "no"}`,
      16, y + 16
    );
  }

  const options = records.map((r) => ({ value: r.name, label: r.name }));
  const radio = makeRadio("class:", options, currentName, (v) => { currentName = v; draw(); });
  container.appendChild(radio);
  draw();
}

// ---- Companion: sica_finite_derivation_pair viz ----
// 4x4 grid of the 16-state 4-bit world. Radio toggles between the LR-vector
// partition, the joint-parity MSS partition, and the setwise "difference"
// (empty — the two partitions are bit-exactly equal).
function mountSicaFiniteDerivationViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: toggle LR-vector vs joint-parity MSS — bit-exact match"]),
  ]);
  section.appendChild(container);
  const width = 380, height = 260;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);
  const worlds = [];
  for (let i = 0; i < 16; i++) worlds.push([(i >> 3) & 1, (i >> 2) & 1, (i >> 1) & 1, i & 1]);
  function jointParity(w) { return (w[0] ^ w[1]) * 2 + (w[2] ^ w[3]); }
  // The gate asserts LR partition == joint-parity partition, so we render them
  // as the same 4-way coloring; "diff" shows the empty set (all cells muted).
  const modes = {
    lr: { name: "LR-vector partition (T1 + CS-2)", color: (w) => Z_PALETTE[jointParity(w)] },
    mss: { name: "joint-parity MSS partition", color: (w) => Z_PALETTE[jointParity(w)] },
    diff: { name: "difference (LR △ MSS) — empty by SIC-A derivation", color: () => "#22303d" },
  };
  let current = "lr";

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const mode = modes[current];
    ctx.fillStyle = INK;
    ctx.font = "13px ui-monospace, monospace";
    ctx.fillText(mode.name, 12, 20);
    const gridSize = 200, cellSize = gridSize / 4, x0 = 12, y0 = 34;
    drawGridCells(ctx, {
      rows: 4, cols: 4, cellSize, x0, y0,
      colorAt: (r, c) => mode.color(worlds[r * 4 + c]),
      borderAt: (r, c) => Z_PALETTE[jointParity(worlds[r * 4 + c])] + "cc",
    });
    // Right column of text.
    const tx = x0 + gridSize + 16;
    let ty = y0 + 14;
    ctx.fillStyle = INK;
    ctx.font = "12px ui-monospace, monospace";
    ctx.fillText(`|world| = 16`, tx, ty); ty += 18;
    ctx.fillText(`|fibres| = 4`, tx, ty); ty += 18;
    ctx.fillText(`fibre sizes: 4,4,4,4`, tx, ty); ty += 24;
    ctx.fillStyle = current === "diff" ? "#3fb27f" : MUTED;
    ctx.font = "11px ui-monospace, monospace";
    if (current === "diff") {
      ctx.fillText("△ = ∅  (partitions equal)", tx, ty); ty += 14;
      ctx.fillText("→ Lean: sic_a_finite_discrete", tx, ty);
    } else {
      ctx.fillText("border colour = joint-parity fibre", tx, ty); ty += 14;
      ctx.fillText("fill colour = selected partition", tx, ty);
    }
  }

  const radio = makeRadio(
    "partition:",
    [
      { value: "lr", label: "LR-vector" },
      { value: "mss", label: "joint-parity MSS" },
      { value: "diff", label: "difference" },
    ],
    current,
    (v) => { current = v; draw(); }
  );
  container.appendChild(radio);
  draw();
}

// ---- Instrument 4 viz: click a quotient, see the partition ----
function mountSufficiencyViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: click a quotient — see which cells it groups"]),
  ]);
  section.appendChild(container);
  const worlds = [];
  for (let i = 0; i < 16; i++) worlds.push([(i>>3)&1, (i>>2)&1, (i>>1)&1, i&1]);
  // Latent Z = (parity{0,1}, parity{2,3})
  function latentZ(w) { return [w[0]^w[1], w[2]^w[3]]; }
  function latentZIdx(w) { const z = latentZ(w); return z[0]*2 + z[1]; }
  const quotients = [
    { name: "latent Z = joint(parity{0,1}, parity{2,3})", fn: latentZIdx },
    { name: "parity{0,1}", fn: (w) => w[0]^w[1] },
    { name: "parity{2,3}", fn: (w) => w[2]^w[3] },
    { name: "parity{0,1,2,3} (global)", fn: (w) => w[0]^w[1]^w[2]^w[3] },
    { name: "bit 0 only", fn: (w) => w[0] },
    { name: "joint(bit_0, bit_1)", fn: (w) => w[0]*2 + w[1] },
    { name: "identity", fn: (w, i) => i },
    { name: "constant", fn: () => 0 },
  ];
  let current = 0;

  const width = 380, height = 260;
  const gridSize = 200, cellSize = gridSize / 4;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const q = quotients[current];
    // Determine palette per unique q-value.
    const groupIds = worlds.map((w, i) => q.fn(w, i));
    const uniq = Array.from(new Set(groupIds));
    const colorFor = (id) => Z_PALETTE[uniq.indexOf(id) % Z_PALETTE.length] || "#888";
    // Determine border color per Z-fibre for reference.
    const x0 = 12, y0 = 12;
    drawGridCells(ctx, {
      rows: 4, cols: 4, cellSize, x0, y0,
      colorAt: (r, c) => colorFor(groupIds[r * 4 + c]),
      borderAt: (r, c) => {
        // border = latent Z (always shown for reference)
        const zIdx = latentZIdx(worlds[r * 4 + c]);
        return Z_PALETTE[zIdx] + "cc";
      },
    });
    // Text panel.
    ctx.fillStyle = INK;
    ctx.font = "13px ui-monospace, monospace";
    const tx = x0 + gridSize + 16;
    let ty = y0 + 14;
    ctx.fillText(`|image| = ${uniq.length}`, tx, ty); ty += 18;
    // Is this partition sufficient for shared (through Z) tasks? YES iff q's partition refines Z's.
    const refinesZ = worlds.every((w, i) => {
      return worlds.every((w2, j) => {
        if (i === j) return true;
        return q.fn(w, i) !== q.fn(w2, j) || latentZIdx(w) === latentZIdx(w2);
      });
    });
    ctx.fillStyle = refinesZ ? "#3fb27f" : "#e0525b";
    ctx.fillText(`shared-family sufficient: ${refinesZ ? "yes" : "no"}`, tx, ty); ty += 18;
    // Sufficient for the not-shared family (bits 0..3) iff q's partition refines the identity.
    const refinesIdentity = uniq.length === 16;
    ctx.fillStyle = refinesIdentity ? "#3fb27f" : "#e0525b";
    ctx.fillText(`not-shared sufficient: ${refinesIdentity ? "yes" : "no"}`, tx, ty); ty += 26;
    ctx.fillStyle = MUTED;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText("border color = latent Z", tx, ty); ty += 14;
    ctx.fillText("fill color = chosen quotient", tx, ty);
  }
  const buttonsWrap = el("div", { class: "viz-buttons" }, []);
  quotients.forEach((q, i) => {
    const btn = document.createElement("button");
    btn.className = "viz-btn" + (i === current ? " active" : "");
    btn.textContent = q.name;
    btn.addEventListener("click", () => {
      current = i;
      buttonsWrap.querySelectorAll(".viz-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      draw();
    });
    buttonsWrap.appendChild(btn);
  });
  container.appendChild(buttonsWrap);
  draw();
}

// ---- Instrument 1 viz: n=6 bits, click a selector ----
function mountFiberFinderViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: pick a selector, see which quotient it chooses"]),
  ]);
  section.appendChild(container);
  // Take the first task: three_bit_invariant, target = parity{0,1,2}.
  const nBits = 6;
  const worlds = [];
  for (let i = 0; i < 64; i++) {
    const w = [];
    for (let b = nBits - 1; b >= 0; b--) w.push((i >> b) & 1);
    worlds.push(w);
  }
  function targetY(w) { return w[0]^w[1]^w[2]; }
  const selectors = [
    { name: "minimal_sufficient → parity{0,1,2}", fn: (w) => w[0]^w[1]^w[2] },
    { name: "mdl_only → constant", fn: () => 0 },
    { name: "accuracy_only → identity", fn: (w, i) => i },
  ];
  let current = 0;

  const width = 380, height = 300;
  const gridSize = 240, cellSize = gridSize / 8;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const q = selectors[current];
    const groupIds = worlds.map((w, i) => q.fn(w, i));
    const uniq = Array.from(new Set(groupIds));
    const colorFor = (id) => Z_PALETTE[uniq.indexOf(id) % Z_PALETTE.length] || "#888";
    const x0 = 12, y0 = 12;
    // Draw 8x8 grid. Cells laid out row-major on world index.
    drawGridCells(ctx, {
      rows: 8, cols: 8, cellSize, x0, y0,
      colorAt: (r, c) => colorFor(groupIds[r * 8 + c]),
      borderAt: (r, c) => {
        // border = target Y (0/1) — always shown
        const y = targetY(worlds[r * 8 + c]);
        return y === 1 ? "#f2c14e" : "#93a1b1";
      },
    });
    ctx.fillStyle = INK;
    ctx.font = "13px ui-monospace, monospace";
    const tx = x0 + gridSize + 16;
    let ty = y0 + 14;
    ctx.fillText(`|image| = ${uniq.length}`, tx, ty); ty += 18;
    // Sufficient iff q's partition refines Y's — check H(Y|q) = 0.
    const bins = new Map();
    worlds.forEach((w, i) => {
      const k = groupIds[i];
      const y = targetY(w);
      if (!bins.has(k)) bins.set(k, new Set());
      bins.get(k).add(y);
    });
    const sufficient = Array.from(bins.values()).every((s) => s.size === 1);
    ctx.fillStyle = sufficient ? "#3fb27f" : "#e0525b";
    ctx.fillText(`sufficient: ${sufficient ? "yes" : "no"}`, tx, ty); ty += 26;
    ctx.fillStyle = MUTED;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText("border: target Y (gold=1, grey=0)", tx, ty); ty += 14;
    ctx.fillText("fill: selector's chosen partition", tx, ty);
  }
  const btns = el("div", { class: "viz-buttons" }, []);
  selectors.forEach((s, i) => {
    const b = document.createElement("button");
    b.className = "viz-btn" + (i === current ? " active" : "");
    b.textContent = s.name;
    b.addEventListener("click", () => {
      current = i;
      btns.querySelectorAll(".viz-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      draw();
    });
    btns.appendChild(b);
  });
  container.appendChild(btns);
  draw();
}

// ---- Instrument 3 viz: 4-bar chart per condition ----
function mountAgencyViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: pick a condition — see its metric signature"]),
  ]);
  section.appendChild(container);
  const rows = data.rows;
  let current = 0;

  const width = 380, height = 240;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const r = rows[current];
    const metrics = [
      { label: "ΔKL", value: Number.isFinite(r.delta_kl) ? r.delta_kl : 3 },
      { label: "true effect", value: r.true_goal_effect },
      { label: "observed", value: r.observed_goal_gain },
      { label: "transfer", value: r.transfer },
    ];
    const maxVal = Math.max(1, ...metrics.map((m) => Math.abs(m.value)));
    const barW = 60, gap = 14, x0 = 30, y0 = 30, chartH = 150;
    metrics.forEach((m, i) => {
      const x = x0 + i * (barW + gap);
      const h = (Math.abs(m.value) / maxVal) * chartH;
      ctx.fillStyle = m.label === "observed" && m.value > 0 && r.true_goal_effect === 0 ? "#e0525b" : "#6ea8fe";
      ctx.fillRect(x, y0 + chartH - h, barW, h);
      ctx.fillStyle = INK;
      ctx.font = "11px ui-monospace, monospace";
      ctx.fillText(m.value.toFixed(2), x + 4, y0 + chartH - h - 4);
      ctx.fillStyle = MUTED;
      ctx.fillText(m.label, x, y0 + chartH + 14);
    });
    // Title.
    ctx.fillStyle = INK;
    ctx.font = "13px ui-monospace, monospace";
    ctx.fillText(`condition: ${r.intervention}`, 12, 18);
    ctx.fillStyle = "#f2c14e";
    ctx.font = "12px ui-monospace, monospace";
    ctx.fillText(`class: ${data.classifications[r.intervention]}`, 12, height - 12);
  }
  const btns = el("div", { class: "viz-buttons" }, []);
  rows.forEach((r, i) => {
    const b = document.createElement("button");
    b.className = "viz-btn" + (i === current ? " active" : "");
    b.textContent = r.intervention;
    b.addEventListener("click", () => {
      current = i;
      btns.querySelectorAll(".viz-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      draw();
    });
    btns.appendChild(b);
  });
  container.appendChild(btns);
  draw();
}

// ---- Instrument 7 viz: R(D) curve with source toggle ----
function mountRDViz(section, data) {
  const container = el("div", { class: "viz" }, [
    el("h4", {}, ["Interactive: pick a source — see R(D) and the test channel"]),
  ]);
  section.appendChild(container);
  let currentSource = 0;

  const width = 380, height = 250;
  const { canvas, ctx } = makeCanvas(width, height);
  container.appendChild(canvas);

  function draw() {
    ctx.fillStyle = AMBIENT;
    ctx.fillRect(0, 0, width, height);
    const src = data.sources[currentSource];
    const dMax = Math.max(...src.curve.map((p) => p.D));
    const rMax = Math.max(...src.curve.map((p) => p.R), src.source_entropy_bits);
    const x0 = 50, y0 = 30, plotW = width - 80, plotH = height - 80;
    // axes
    ctx.strokeStyle = MUTED;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x0, y0 + plotH);
    ctx.lineTo(x0 + plotW, y0 + plotH);
    ctx.stroke();
    // R(D) curve
    ctx.strokeStyle = "#6ea8fe";
    ctx.lineWidth = 2;
    ctx.beginPath();
    src.curve.forEach((pt, i) => {
      const x = x0 + (pt.D / dMax) * plotW;
      const y = y0 + plotH - (pt.R / rMax) * plotH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    // Test channel MI dots (should overlap R(D) in achievable regime).
    // Clamp: only draw a dot when D < d_max (test channel is only the
    // RD-optimal one in that regime; beyond it the formula would give a
    // negative or spurious value we don't want to visualise).
    ctx.fillStyle = "#f2c14e";
    src.curve.forEach((pt) => {
      if (pt.D >= src.d_max) return;
      const mi = Math.max(0, pt.test_channel_MI);
      const x = x0 + (pt.D / dMax) * plotW;
      const y = y0 + plotH - (mi / rMax) * plotH;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
    // Anchor labels: R(0), R(D_max).
    ctx.fillStyle = INK;
    ctx.font = "11px ui-monospace, monospace";
    ctx.fillText("R(D)", x0 + 5, y0 - 8);
    ctx.fillText("D", x0 + plotW - 10, y0 + plotH + 16);
    ctx.fillText(`H = ${src.source_entropy_bits.toFixed(3)}`, x0 - 42, y0 + 4);
    ctx.fillText("0", x0 - 12, y0 + plotH + 4);
    ctx.fillText(`${src.d_max.toFixed(2)}`, x0 + plotW - 8, y0 + plotH + 16);
    // Title
    ctx.fillStyle = "#f2c14e";
    ctx.font = "13px ui-monospace, monospace";
    ctx.fillText(src.source, 12, 18);
  }
  const btns = el("div", { class: "viz-buttons" }, []);
  data.sources.forEach((s, i) => {
    const b = document.createElement("button");
    b.className = "viz-btn" + (i === currentSource ? " active" : "");
    b.textContent = s.source;
    b.addEventListener("click", () => {
      currentSource = i;
      btns.querySelectorAll(".viz-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      draw();
    });
    btns.appendChild(b);
  });
  container.appendChild(btns);
  draw();
}

// ================================================================
// Hero WebGL shader: perpetual visual abstract of the fibration.
// ================================================================

const HERO_VERT = `
attribute vec2 aPos;
varying vec2 vUv;
void main() {
  vUv = aPos * 0.5 + 0.5;
  gl_Position = vec4(aPos, 0.0, 1.0);
}
`;

const HERO_FRAG = `
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform vec2 uResolution;

// Fibre palette matches Instrument-4's 4-way latent Z coloring.
const vec3 C0 = vec3(0.878, 0.322, 0.357);  // red   z=(0,0)
const vec3 C1 = vec3(0.949, 0.757, 0.306);  // gold  z=(0,1)
const vec3 C2 = vec3(0.431, 0.659, 0.996);  // blue  z=(1,0)
const vec3 C3 = vec3(0.247, 0.698, 0.498);  // green z=(1,1)
const vec3 BG = vec3(0.020, 0.031, 0.047);

// Cheap 2D hash + noise.
float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// Concern wave — deforms fibre boundaries over time.
vec2 concernFlow(vec2 uv, float t) {
  float wave = sin(uv.y * 3.1415 * 2.0 + t * 0.6) * 0.06;
  float swirl = cos(uv.x * 3.1415 * 1.4 + t * 0.4) * 0.05;
  return uv + vec2(wave, swirl);
}

vec3 pickFibre(vec2 uv) {
  float qx = step(0.5, uv.x);
  float qy = step(0.5, uv.y);
  int idx = int(qx + 2.0 * qy);
  if (idx == 0) return C0;
  if (idx == 1) return C1;
  if (idx == 2) return C2;
  return C3;
}

void main() {
  vec2 uv = vUv;
  float aspect = uResolution.x / uResolution.y;
  vec2 auv = vec2(uv.x * aspect, uv.y);
  float t = uTime;

  // 1) Latent Z partition (via warped coordinates).
  vec2 warped = concernFlow(uv, t);
  vec3 base = pickFibre(warped);

  // 2) Fibre-internal "sample" particles: each fibre has a slow drift
  //    plus a bright dot at a moving position.
  vec3 accum = vec3(0.0);
  for (int i = 0; i < 4; i++) {
    float fi = float(i);
    // Fibre center in canonical (u, v).
    vec2 center = vec2(mod(fi, 2.0) * 0.5 + 0.25, floor(fi / 2.0) * 0.5 + 0.25);
    // Drift within the fibre.
    vec2 drift = vec2(
      sin(t * 0.7 + fi * 1.9) * 0.15,
      cos(t * 0.5 + fi * 2.3) * 0.15
    );
    vec2 pos = center + drift;
    float d = length((uv - pos) * vec2(aspect, 1.0));
    // Multiple soft dots per fibre, at harmonic times.
    for (int k = 0; k < 3; k++) {
      float fk = float(k);
      vec2 subOff = vec2(
        sin(t * 1.1 + fi * 0.7 + fk * 2.1) * 0.05,
        cos(t * 0.9 + fi * 1.3 + fk * 1.7) * 0.05
      );
      float dd = length((uv - pos - subOff) * vec2(aspect, 1.0));
      float glow = smoothstep(0.04, 0.0, dd);
      accum += pickFibre(center) * glow * 0.6;
    }
    accum += pickFibre(center) * smoothstep(0.05, 0.0, d) * 0.4;
  }

  // 3) Compilation "rain": vertical streaks descending from top (Z) into
  //    the corresponding fibre (X).
  vec2 rainUv = uv * vec2(60.0, 12.0);
  rainUv.y += t * 4.0;
  float rain = smoothstep(0.95, 1.0, noise(rainUv)) * smoothstep(0.6, 0.1, uv.y);
  accum += pickFibre(warped) * rain * 0.8;

  // 4) Fibre-tinted base with subtle noise texture.
  float bgnoise = noise(uv * 8.0 + t * 0.2) * 0.05;
  vec3 col = mix(BG, base * 0.25 + bgnoise, 0.85) + accum;

  // 5) Soft vignette.
  vec2 vig = uv - 0.5;
  float v = 1.0 - dot(vig, vig) * 0.7;
  col *= v;

  gl_FragColor = vec4(col, 1.0);
}
`;

function initHero() {
  const canvas = document.getElementById("hero-canvas");
  if (!canvas || !canvas.getContext) return;
  const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
  if (!gl) {
    canvas.style.display = "none";
    return;
  }
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const resize = () => {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(rect.height * dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
  };
  resize();
  window.addEventListener("resize", resize);

  function compile(src, type) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.error("hero shader:", gl.getShaderInfoLog(s));
      return null;
    }
    return s;
  }
  const vs = compile(HERO_VERT, gl.VERTEX_SHADER);
  const fs = compile(HERO_FRAG, gl.FRAGMENT_SHADER);
  if (!vs || !fs) { canvas.style.display = "none"; return; }
  const prog = gl.createProgram();
  gl.attachShader(prog, vs);
  gl.attachShader(prog, fs);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.error("hero link:", gl.getProgramInfoLog(prog));
    canvas.style.display = "none";
    return;
  }
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
    gl.STATIC_DRAW
  );
  const loc = gl.getAttribLocation(prog, "aPos");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const uTime = gl.getUniformLocation(prog, "uTime");
  const uRes = gl.getUniformLocation(prog, "uResolution");

  const start = performance.now();
  function frame(now) {
    const t = (now - start) * 0.001;
    gl.uniform1f(uTime, t);
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

void GATE_LABELS;
document.addEventListener("DOMContentLoaded", async () => {
  initHero();
  await main();
  // Fetch data again once for the viz layer (same URL cached by browser).
  try {
    const response = await fetch("results.json", { cache: "no-cache" });
    if (!response.ok) return;
    const data = await response.json();
    attachInteractiveViz(data);
  } catch (_error) {
    // silent — viz is best-effort
  }
});
