(() => {
  "use strict";

  const worldList = document.getElementById("world-list");
  const presetList = document.getElementById("preset-list");
  const catalog = document.getElementById("world-catalog");
  const resultCard = document.getElementById("result-card");
  let worlds = [];
  let receipts = [];
  let selectedWorldId = "clinical-trials-sec";

  const text = (value) => (value == null ? "" : String(value));
  const make = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = text(content);
    return node;
  };

  async function boot() {
    const [worldResponse, receiptResponse] = await Promise.all([
      fetch("worlds.json", { cache: "no-store" }),
      fetch("receipts.json", { cache: "no-store" }),
    ]);
    if (!worldResponse.ok || !receiptResponse.ok) throw new Error("fixture files unavailable");
    const worldData = await worldResponse.json();
    const receiptData = await receiptResponse.json();
    worlds = Array.isArray(worldData.worlds) ? worldData.worlds : [];
    receipts = Array.isArray(receiptData.receipts) ? receiptData.receipts : [];
    renderWorldPicker();
    renderCatalog();
    selectWorld(selectedWorldId);
    try {
      const liveResponse = await fetch("live_model_receipt.json", { cache: "no-store" });
      if (!liveResponse.ok) throw new Error("live-model receipt unavailable");
      const liveModelReceipt = await liveResponse.json();
      await renderLiveModelProof(liveModelReceipt);
    } catch {
      renderLiveModelUnavailable();
    }
  }

  function renderLiveModelUnavailable() {
    const status = document.getElementById("live-proof-status");
    if (!status) return;
    status.classList.add("bad");
    status.textContent = "Recorded experiment unavailable · the checkpoint fixtures remain usable.";
  }

  async function renderLiveModelProof(liveModelReceipt) {
    const experiment = liveModelReceipt?.experiment;
    const runs = Array.isArray(liveModelReceipt?.runs) ? liveModelReceipt.runs : [];
    if (!experiment || experiment.frozen !== true || experiment.live_endpoint !== false || runs.length !== 3) {
      throw new Error("live-model receipt contract unavailable");
    }
    for (const card of document.querySelectorAll("[data-live-stage]")) {
      const run = runs.find((item) => item.stage === card.dataset.liveStage);
      if (!run) throw new Error("live-model run unavailable");
      card.querySelector(".live-score").textContent = `${run.safe_repetitions}/${run.total_repetitions}`;
      card.querySelector(".live-percent").textContent = `${formatPercent(run.safe_repetitions / run.total_repetitions)}%`;
      const meter = card.querySelector(".proof-meter");
      meter.setAttribute("aria-valuemax", String(run.total_repetitions));
      meter.setAttribute("aria-valuenow", String(run.safe_repetitions));
      meter.querySelector(".proof-fill").style.width = `${formatPercent(run.safe_repetitions / run.total_repetitions)}%`;
    }
    document.getElementById("live-world").textContent = experiment.evidence_world;
    document.getElementById("live-model").textContent = `${providerLabel(experiment.provider)} · ${experiment.model}`;
    document.getElementById("live-shape").textContent = `${experiment.case_count} cases × ${experiment.repetitions} repetitions`;
    const finalRun = runs.find((item) => item.stage === "final_boundary");
    const modelCalls = Number(finalRun?.model_usage?.total_calls);
    const preModelRefusals = Number(experiment.total_repetitions) - modelCalls;
    if (!Number.isInteger(modelCalls) || !Number.isInteger(preModelRefusals) || preModelRefusals < 0) {
      throw new Error("live-model usage contract unavailable");
    }
    document.getElementById("live-calls").textContent = `${modelCalls} of ${experiment.total_repetitions}; ${preModelRefusals} pre-model refusals`;
    document.getElementById("live-receipt-digest").textContent = `${liveModelReceipt.canonical_digest.slice(0, 12)}…`;
    await verifyLiveModelDigest(liveModelReceipt);
  }

  async function verifyLiveModelDigest(liveModelReceipt) {
    const expected = await globalThis.BioFirewallFixture?.digestReceipt(liveModelReceipt);
    const verified = expected && expected === liveModelReceipt.canonical_digest;
    const status = document.getElementById("live-proof-status");
    status.classList.toggle("bad", !verified);
    status.textContent = verified
      ? "Receipt bundle consistent · source runs are pinned by SHA-256."
      : "Receipt bundle mismatch · do not rely on this recorded result.";
  }

  function renderWorldPicker() {
    worldList.replaceChildren();
    for (const world of worlds) {
      const admitted = world.state === "ADMITTED";
      const button = make("button", `world-option${admitted && world.id === selectedWorldId ? " active" : ""}`);
      button.type = "button";
      button.dataset.world = world.id;
      button.setAttribute("aria-pressed", admitted && world.id === selectedWorldId ? "true" : "false");
      if (!admitted) {
        button.disabled = true;
        button.setAttribute("aria-label", `${world.title}: ${displayState(world.state)}; checking unavailable`);
      }
      const mark = make("span", `world-mark ${worldClass(world.id)}`, worldMark(world.id));
      mark.setAttribute("aria-hidden", "true");
      const label = make("span");
      label.append(make("strong", null, world.title));
      label.append(make("small", null, world.short_title || displayState(world.state)));
      const dot = make("span", `state-dot ${admitted ? "admitted" : "not-admitted"}`);
      dot.title = displayState(world.state);
      button.append(mark, label, dot);
      if (admitted) button.addEventListener("click", () => selectWorld(world.id));
      worldList.append(button);
    }
  }

  function renderCatalog() {
    catalog.replaceChildren();
    for (const world of worlds) {
      const card = make("article", `catalog-card ${catalogClass(world.state)}`);
      const top = make("div", "catalog-top");
      const mark = make("span", `world-mark ${worldClass(world.id)}`, worldMark(world.id));
      mark.setAttribute("aria-hidden", "true");
      top.append(mark, make("span", "state-badge", catalogState(world.state)));
      card.append(top, make("h3", null, world.title));
      if (world.state === "ADMITTED") {
        card.append(make("p", null, world.short_title), make("small", null, world.modality));
      } else {
        card.append(make("p", null, "Review in progress"), make("small", null, world.gate_reason || "No public evidence is available."));
      }
      catalog.append(card);
    }
  }

  function selectWorld(worldId) {
    const world = worlds.find((item) => item.id === worldId);
    if (!world || world.state !== "ADMITTED") return;
    selectedWorldId = worldId;
    for (const button of worldList.querySelectorAll(".world-option")) {
      const active = button.dataset.world === worldId;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    }
    const worldReceipts = receipts.filter((receipt) => receipt.world_id === worldId && world.receipt_ids.includes(receipt.receipt_id));
    presetList.replaceChildren();
    for (const receipt of worldReceipts) {
      const button = make("button", "preset");
      button.type = "button";
      button.dataset.receipt = receipt.receipt_id;
      button.setAttribute("aria-pressed", "false");
      button.setAttribute("aria-label", `${receipt.preset_label}; select exact fixture`);
      const icon = outcomeIcon(receipt.outcome);
      icon.setAttribute("aria-hidden", "true");
      const label = make("span");
      const parts = receipt.preset_label.split(" · ");
      label.append(make("strong", null, parts[0]), make("small", null, parts.slice(1).join(" · ")));
      button.append(icon, label);
      button.addEventListener("click", () => selectReceipt(receipt.receipt_id));
      presetList.append(button);
    }
    document.getElementById("selected-world-label").textContent = `${world.title} · ${world.version_label}`;
    selectReceipt(world.default_receipt);
  }

  function selectReceipt(receiptId) {
    const receipt = receipts.find((item) => item.receipt_id === receiptId && item.world_id === selectedWorldId);
    if (!receipt) return;
    for (const button of presetList.querySelectorAll(".preset")) {
      const active = button.dataset.receipt === receiptId;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    }
    renderClaim(receipt);
    renderResult(receipt);
    void verifyDigest(receipt);
  }

  function renderClaim(receipt) {
    const claim = receipt.normalized_claim || {};
    const world = worlds.find((item) => item.id === receipt.world_id);
    const claimType = {
      "clinical-trials-sec": "TRIAL_DISCLOSURE",
      "open-targets": "TARGET_DISEASE_ASSOCIATION",
      "arc-vcc": "PERTURBATION_DIRECTION",
    }[receipt.world_id] || "BOUNDED_CLAIM";
    let claimText;
    if (receipt.world_id === "clinical-trials-sec") claimText = `“The SEC exhibit identifies ${claim.intervention} as trial ${claim.nct_id}, consistent with the registry as of ${formatDate(claim.as_of)}.”`;
    else if (receipt.world_id === "open-targets") claimText = `“${claim.target_id} has a ${claim.evidence_source} association with ${claim.disease_id} in release ${claim.release}.”`;
    else claimText = `“Perturbing ${claim.perturbed_gene} ${claim.direction} expression of ${claim.response_gene} in assay ${claim.assay}.”`;
    document.getElementById("claim-type").textContent = claimType;
    document.getElementById("claim-text").textContent = claimText;
    document.getElementById("claim-as-of").textContent = claim.as_of ? `as of ${formatDate(claim.as_of)}` : (claim.release ? `release ${claim.release}` : `assay ${claim.assay}`);
    const fields = document.getElementById("claim-fields");
    const displayKeys = {
      "clinical-trials-sec": ["nct_id", "sponsor"],
      "open-targets": ["target_id", "disease_id"],
      "arc-vcc": ["perturbed_gene", "response_gene"],
    }[receipt.world_id] || Object.keys(claim).slice(0, 2);
    fields.replaceChildren(...displayKeys.map((key) => [key, claim[key]]).map(([key, value]) => {
      const span = make("span"); span.append(document.createTextNode(`${key}: `), make("b", null, value)); return span;
    }));
    document.getElementById("selected-world-label").textContent = `${world.title} · ${world.version_label}`;
  }

  function renderResult(receipt) {
    const outcome = receipt.outcome.toLowerCase().replace("checker_error", "error");
    resultCard.className = `result-card ${outcome}`;
    const symbols = { accepted: "✓", rejected: "×", inconclusive: "?", error: "!" };
    document.getElementById("result-symbol").textContent = symbols[outcome] || "?";
    document.getElementById("result-title").firstChild.textContent = receipt.outcome;
    document.getElementById("result-summary").textContent = resultSummary(receipt);
    document.getElementById("result-scope").textContent = receipt.scope || receipt.reason || "No scope is available for this fixture.";
    document.getElementById("rule-title").textContent = receipt.winning_rule?.title || "No rule issued";
    document.getElementById("rule-rationale").textContent = receipt.winning_rule?.rationale || receipt.reason || receipt.error?.message || "The checker stopped before rule evaluation.";
    const citation = receipt.citations?.[0];
    const sourceReference = receipt.source_reference;
    document.getElementById("citation").textContent = citation
      ? `${citation.source} · ${citation.locator}`
      : sourceReference
        ? `${sourceReference.label} · ${sourceReference.locator}`
        : "No citation issued for this outcome.";
    document.getElementById("citation-ref").textContent = citation?.reference || sourceReference?.reference || "No evidence reference issued.";
    document.getElementById("receipt-json").textContent = JSON.stringify(receipt, null, 2);
    document.getElementById("verified-label").textContent = "checking bundle consistency…";
    document.getElementById("fixture-status").classList.remove("bad");
    document.getElementById("fixture-status").textContent = `Fixture loaded locally · bundle consistency digest ${receipt.canonical_digest.slice(0, 8)}…`;
  }

  async function verifyDigest(receipt) {
    const expected = await globalThis.BioFirewallFixture?.digestReceipt(receipt);
    const verified = expected && expected === receipt.canonical_digest;
    const label = document.getElementById("verified-label");
    label.textContent = verified ? "bundle consistent" : "bundle mismatch";
    if (!verified) {
      document.getElementById("fixture-status").classList.add("bad");
      document.getElementById("fixture-status").textContent = "Fixture bundle mismatch · consistency check failed; do not rely on this fixture.";
    }
  }

  function resultSummary(receipt) {
    if (receipt.outcome === "ACCEPTED") return receipt.evidence?.comparison ? `The cited disclosure matches the frozen record (${receipt.evidence.comparison}).` : "The selected claim matches the frozen evidence record.";
    if (receipt.outcome === "REJECTED") return receipt.evidence?.comparison ? `The selected assertion conflicts with the frozen record (${receipt.evidence.comparison}).` : "The selected assertion exceeds or conflicts with the frozen evidence contract.";
    if (receipt.outcome === "INCONCLUSIVE") return receipt.reason || "The evidence is not answerable, so no verdict is issued.";
    return receipt.error?.message || "The integrity prerequisite failed before a scientific outcome could be issued.";
  }

  function formatDate(value) { const date = new Date(String(value).includes("T") ? value : `${value}T00:00:00Z`); return Number.isNaN(date.getTime()) ? text(value) : date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }); }
  function formatPercent(value) { const percent = Number(value) * 100; return Number.isInteger(percent) ? String(percent) : percent.toFixed(1); }
  function providerLabel(value) { return value === "openai" ? "OpenAI" : text(value); }
  function worldMark(id) { return { "clinical-trials-sec": "CT", "open-targets": "OT", "arc-vcc": "AV", neurovault: "NV", flywire_connectome: "FC" }[id] || "·"; }
  function worldClass(id) { return { "clinical-trials-sec": "clinical", "open-targets": "targets", "arc-vcc": "arc", neurovault: "neuro", flywire_connectome: "fly" }[id] || "clinical"; }
  function catalogClass(state) { return state === "ADMITTED" ? "admitted" : state.includes("DEFERRED") ? "deferred" : "withheld"; }
  function displayState(state) { return state.replaceAll("_", " "); }
  function catalogState(state) { return state === "ADMITTED" ? state : state.includes("DEFERRED") ? "DEFERRED" : "WITHHELD"; }
  function outcomeIcon(outcome) { const icon = make("span", `preset-icon ${outcome.toLowerCase().replace("checker_error", "error")}`, { ACCEPTED: "✓", REJECTED: "×", INCONCLUSIVE: "?", CHECKER_ERROR: "!" }[outcome] || "?"); return icon; }

  boot().catch(() => {
    document.getElementById("fixture-status").classList.add("bad");
    document.getElementById("fixture-status").textContent = "Fixture unavailable · the static proof bundle did not load.";
    const proofStatus = document.getElementById("live-proof-status");
    if (proofStatus) {
      proofStatus.classList.add("bad");
      proofStatus.textContent = "Recorded experiment unavailable · the public receipt did not load.";
    }
  });
})();
