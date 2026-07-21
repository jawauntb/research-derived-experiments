(() => {
  const scenarioSelect = document.getElementById("scenario-select");
  const actionButtons = document.getElementById("action-buttons");
  const scenarioBlurb = document.getElementById("scenario-blurb");
  const comparePanel = document.getElementById("compare-panel");
  const runBtn = document.getElementById("run-btn");

  let catalog = null;
  let selectedAction = null;

  async function boot() {
    const response = await fetch("scenarios.json", { cache: "no-store" });
    catalog = await response.json();
    hydrateResearch(catalog);
    for (const scenario of catalog.scenarios) {
      const option = document.createElement("option");
      option.value = scenario.id;
      option.textContent = scenario.title;
      scenarioSelect.appendChild(option);
    }
    scenarioSelect.addEventListener("change", () => renderScenario());
    runBtn.addEventListener("click", runBoth);
    renderScenario();
  }

  function hydrateResearch(data) {
    document.getElementById("stat-delta").textContent = data.research.delta_ct;
    document.getElementById("stat-n").textContent =
      `${data.research.d2_episodes} / ${data.research.d3_episodes}`;
    document.getElementById("stat-ci").textContent = data.research.ci;
    document.getElementById("stat-models").textContent = data.research.models.join(" · ");
    document.getElementById("claim-box").textContent = data.product.claim;
    document.getElementById("kill-note").textContent = data.research.kill_note;
  }

  function currentScenario() {
    return catalog.scenarios.find((item) => item.id === scenarioSelect.value);
  }

  function selectedMode() {
    const checked = document.querySelector('input[name="mode"]:checked');
    return checked ? checked.value : "soft_prompt";
  }

  function renderScenario() {
    const scenario = currentScenario();
    scenarioBlurb.textContent = scenario.blurb;
    actionButtons.replaceChildren();
    selectedAction = scenario.default_action;
    for (const [key, spec] of Object.entries(scenario.actions)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chip";
      button.textContent = spec.label;
      button.dataset.action = key;
      button.setAttribute("aria-pressed", key === selectedAction ? "true" : "false");
      button.addEventListener("click", () => {
        selectedAction = key;
        for (const node of actionButtons.querySelectorAll(".chip")) {
          node.setAttribute("aria-pressed", node.dataset.action === key ? "true" : "false");
        }
      });
      actionButtons.appendChild(button);
    }
    comparePanel.hidden = true;
  }

  function renderResult(rootId, result) {
    const root = document.getElementById(rootId);
    const metrics = root.querySelector(".metrics");
    const receipt = root.querySelector(".receipt");
    const rows = [
      ["joint_success", result.scores.joint_success],
      ["task_success", result.scores.task_success],
      ["violation", result.scores.violation],
      ["false_completion", result.scores.false_completion],
      ["enforcement_applied", result.evidence.enforcement_applied],
      ["repair_applied", result.evidence.repair_applied],
    ];
    metrics.replaceChildren(
      ...rows.map(([name, value]) => {
        const row = document.createElement("div");
        row.className = "metric";
        const label = document.createElement("span");
        label.textContent = name;
        const val = document.createElement("span");
        val.className = value ? "pass" : "fail";
        val.textContent = String(value);
        row.append(label, val);
        return row;
      }),
    );
    receipt.textContent = JSON.stringify(
      {
        mode: result.mode,
        condition: result.condition,
        provider_action: result.provider_action,
        applied_action: result.evidence.action,
        capability_used: result.evidence.capability_used,
        policy_digest: result.policy_digest,
        workspace_digest: result.evidence.workspace_digest,
        scores: result.scores,
      },
      null,
      2,
    );
  }

  function runBoth() {
    const scenario = currentScenario();
    const soft = runEpisode({
      scenario,
      mode: "soft_prompt",
      actionKey: selectedAction,
    });
    const guarded = runEpisode({
      scenario,
      mode: "external_guards",
      actionKey: selectedAction,
    });
    // Highlight selected mode by running its path too (same data as compare).
    void selectedMode();
    renderResult("result-soft", soft);
    renderResult("result-guard", guarded);
    comparePanel.hidden = false;
    comparePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  boot().catch((error) => {
    scenarioBlurb.textContent = `Failed to load scenarios: ${error.message}`;
  });
})();
