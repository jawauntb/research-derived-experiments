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
    const rows = source.curve.map((pt) => [
      { text: pt.D.toFixed(2), cls: "num" },
      { text: pt.R.toFixed(4), cls: "num" },
      {
        node: pill(
          pt.test_channel_MI.toFixed(4),
          pt.D < source.d_max && Math.abs(pt.test_channel_MI - pt.R) < 1e-9 ? "yes" : (pt.D >= source.d_max ? "gold" : "no")
        ),
      },
    ]);
    body.appendChild(table(["D", "R(D)  [bits]", "I(X; X̂) via test channel"], rows));
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
    // Test channel MI dots (should overlap R(D) in achievable regime)
    ctx.fillStyle = "#f2c14e";
    src.curve.forEach((pt) => {
      const x = x0 + (pt.D / dMax) * plotW;
      const y = y0 + plotH - (pt.test_channel_MI / rMax) * plotH;
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

void GATE_LABELS;
document.addEventListener("DOMContentLoaded", async () => {
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
