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

  const allPass = ["representation_search", "structure_compiler", "symbolic_causation"].every(
    (k) => data[k].status === "pass"
  );
  status.textContent = allPass
    ? "All three instruments: status = pass. Every gate below is green."
    : "One or more instruments did not pass — see gates below.";
}

void GATE_LABELS;
document.addEventListener("DOMContentLoaded", main);
