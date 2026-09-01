(() => {
  "use strict";

  const worldList = document.getElementById("world-list");
  const presetList = document.getElementById("preset-list");
  const catalog = document.getElementById("world-catalog");
  const resultCard = document.getElementById("result-card");
  let worlds = [];
  let receipts = [];
  let selectedWorldId = "clinical_trials_sec";

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
    let claimText;
    if (receipt.world_id === "clinical_trials_sec") claimText = `“The registered trial ${claim.registry_id} was ${claim.asserted_value?.toLowerCase()} as of ${formatDate(claim.as_of)}.”`;
    else if (receipt.world_id === "open_targets") claimText = `“${claim.target_id} has a ${claim.association_type} association with ${claim.disease_id} in release ${claim.release}.”`;
    else claimText = `“Perturbing ${claim.perturbed_gene} ${claim.direction} expression of ${claim.measured_gene} in assay ${claim.assay}.”`;
    document.getElementById("claim-text").textContent = claimText;
    document.getElementById("claim-as-of").textContent = claim.as_of ? `as of ${formatDate(claim.as_of)}` : (claim.release ? `release ${claim.release}` : `assay ${claim.assay}`);
    const fields = document.getElementById("claim-fields");
    fields.replaceChildren(...Object.entries(claim).slice(0, 2).map(([key, value]) => {
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
    document.getElementById("citation").textContent = citation ? `${citation.source} · ${citation.locator}` : "No citation issued for this outcome.";
    document.getElementById("citation-ref").textContent = citation?.reference || "No evidence reference issued.";
    document.getElementById("receipt-json").textContent = JSON.stringify(receipt, null, 2);
    document.getElementById("verified-label").textContent = "checking digest…";
    document.getElementById("fixture-status").classList.remove("bad");
    document.getElementById("fixture-status").textContent = `Fixture loaded locally · canonical receipt digest ${receipt.canonical_digest.slice(0, 8)}…`;
  }

  async function verifyDigest(receipt) {
    const expected = await globalThis.BioFirewallFixture?.digestReceipt(receipt);
    const verified = expected && expected === receipt.canonical_digest;
    const label = document.getElementById("verified-label");
    label.textContent = verified ? "digest verified" : "digest mismatch";
    if (!verified) {
      document.getElementById("fixture-status").classList.add("bad");
      document.getElementById("fixture-status").textContent = "Fixture digest mismatch · no receipt should be trusted.";
    }
  }

  function resultSummary(receipt) {
    if (receipt.outcome === "ACCEPTED") return receipt.evidence?.comparison ? `The cited disclosure matches the frozen record (${receipt.evidence.comparison}).` : "The selected claim matches the frozen evidence record.";
    if (receipt.outcome === "REJECTED") return receipt.evidence?.comparison ? `The selected assertion conflicts with the frozen record (${receipt.evidence.comparison}).` : "The selected assertion exceeds or conflicts with the frozen evidence contract.";
    if (receipt.outcome === "INCONCLUSIVE") return receipt.reason || "The evidence is not answerable, so no verdict is issued.";
    return receipt.error?.message || "The integrity prerequisite failed before a scientific outcome could be issued.";
  }

  function formatDate(value) { const date = new Date(`${value}T00:00:00Z`); return Number.isNaN(date.getTime()) ? text(value) : date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }); }
  function worldMark(id) { return { clinical_trials_sec: "CT", open_targets: "OT", arc_vcc: "AV", neurovault: "NV", flywire_connectome: "FC" }[id] || "·"; }
  function worldClass(id) { return { clinical_trials_sec: "clinical", open_targets: "targets", arc_vcc: "arc", neurovault: "neuro", flywire_connectome: "fly" }[id] || "clinical"; }
  function catalogClass(state) { return state === "ADMITTED" ? "admitted" : state.includes("DEFERRED") ? "deferred" : "withheld"; }
  function displayState(state) { return state.replaceAll("_", " "); }
  function catalogState(state) { return state === "ADMITTED" ? state : state.includes("DEFERRED") ? "DEFERRED" : "WITHHELD"; }
  function outcomeIcon(outcome) { const icon = make("span", `preset-icon ${outcome.toLowerCase().replace("checker_error", "error")}`, { ACCEPTED: "✓", REJECTED: "×", INCONCLUSIVE: "?", CHECKER_ERROR: "!" }[outcome] || "?"); return icon; }

  boot().catch((error) => {
    document.getElementById("fixture-status").classList.add("bad");
    document.getElementById("fixture-status").textContent = `Fixture unavailable · ${error.message}`;
  });
})();
