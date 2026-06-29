const canvas = document.getElementById("atlas-canvas");
const ctx = canvas.getContext("2d", { alpha: false });

const navEl = document.querySelector(".nav");
const titleEl = document.getElementById("view-title");
const kickerEl = document.getElementById("view-kicker");
const subtitleEl = document.getElementById("view-subtitle");
const thesisEl = document.getElementById("mechanism-thesis");
const metricListEl = document.getElementById("metric-list");
const motionListEl = document.getElementById("motion-list");
const sourceLinksEl = document.getElementById("source-links");
const phaseLabelEl = document.getElementById("phase-label");
const phaseValueEl = document.getElementById("phase-value");
const phaseFillEl = document.getElementById("phase-fill");
const cardsEl = document.getElementById("experiment-cards");
const pauseButton = document.getElementById("pause-button");
const tourButton = document.getElementById("tour-button");
const storyButton = document.getElementById("story-button");
const labelsButton = document.getElementById("labels-button");
const speedRange = document.getElementById("speed-range");
const tourStatusTextEl = document.getElementById("tour-status-text");
const tourFillEl = document.getElementById("tour-fill");

const rootStyles = getComputedStyle(document.documentElement);
const cssColor = (name, fallback) => rootStyles.getPropertyValue(name).trim() || fallback;
const colors = {
  ink: cssColor("--ink", "#f6efe4"),
  muted: cssColor("--muted", "rgba(246, 239, 228, 0.66)"),
  faint: cssColor("--faint", "rgba(246, 239, 228, 0.30)"),
  cyan: cssColor("--cyan", "#5de7ef"),
  amber: cssColor("--amber", "#ffc067"),
  violet: cssColor("--violet", "#b58cff"),
  green: cssColor("--green", "#8ce2a9"),
  rose: cssColor("--rose", "#ff8f9b"),
  blue: cssColor("--blue", "#6fa8ff"),
  dark: cssColor("--stage", "#070a12"),
};

const repoUrl = "https://github.com/jawauntb/research-derived-experiments/blob/main";

const pageList = [
  {
    route: "overview",
    nav: "program",
    draw: drawOverview,
    color: colors.blue,
    kicker: "where the research is now",
    title: "a living map of constraints becoming agency",
    subtitle: "The whole program is shown as a changing mechanism: symmetry pressure becomes active geometry, active geometry becomes concern, concern allocates interventions, and viable bodies consume the resulting syntax.",
    thesis: "This page is the wide shot. It binds 34 papers and 117 public result notes into one live field: outer arcs are research tracks, moving packets are evidence passing gates, and the violet frontier marks places where the current mechanism still has to earn stronger claims.",
    motions: [
      "Outer arcs show papers and result families; inner packets show evidence moving from observation to intervention to body design.",
      "Green/cyan gates are strong mechanisms, amber gates are partial positives, and violet frontier loops mark honest unresolved scaffolds.",
      "The zoom pages remain the detailed mechanisms; this page shows how they currently feed one research program.",
    ],
    sources: [
      { label: "repo overview", href: `${repoUrl}/README.md` },
      { label: "metric stack", href: `${repoUrl}/papers/metric_stack_synthesis/paper.md` },
      { label: "phase 2 handoff", href: `${repoUrl}/docs/phase2_next_breakthrough_handoff.md` },
      { label: "specificity frontier", href: `${repoUrl}/docs/semantic_specificity.md` },
    ],
  },
  {
    route: "phase2",
    nav: "phase 2",
    draw: drawPhase2,
    color: colors.green,
    kicker: "guided story mode",
    title: "phase 2: pixels to bodies",
    subtitle: "A reviewer can watch the current claim unfold: RGB scenes become learned foreground masks, masks become six object slots, slots induce semantic profiles, and transfer gates decide what can become a body contract.",
    thesis: "Phase 2 is the bridge from concerned syntax to viable computational bodies. The newest evidence removes algorithmic connected components from the accepted 2A path: learned object slots recover scenes at 1.000, induce semantic profiles at 1.000, and preserve the held-out transfer gate. The honest frontier is making 2B consume that newest learned-slot contract.",
    motions: [
      "Story mode advances a spotlight from pixels to learned foreground masks to six object slots before semantic-profile induction.",
      "Moving packets are evidence: they only cross the next gate when slot recovery, profile purity, concern, target binding, useful programs, and transfer all survive.",
      "Dim paths are controls and open frontiers, so the viewer sees why reward-only, proxy bodies, supplied labels, and connected-component shortcuts are not the final claim.",
    ],
    sources: [
      { label: "phase 2 start-here", href: `${repoUrl}/docs/phase2_next_phase_research_handoff.md` },
      { label: "learned slots result", href: `${repoUrl}/experiments/concerned_syntax/results/learned_object_slots_modal_2026_06_22.md` },
      { label: "next breakthrough", href: `${repoUrl}/docs/phase2_next_breakthrough_handoff.md` },
      { label: "trajectory", href: `${repoUrl}/docs/phase2_breakthrough_trajectory.md` },
    ],
  },
  {
    route: "reafference",
    nav: "reafference",
    draw: drawReafference,
    color: colors.cyan,
    kicker: "first-order self",
    title: "self dE plus world dE becomes observed dE",
    subtitle: "Agents act, world shocks arrive, and the field must assign the same observed energy change to the right source. The violet error path is the attribution update.",
    thesis: "The first-order self is the part of the sensorimotor field whose changes remain predictable from the agent's own efference copy after world causes are accounted for.",
    motions: [
      "Cyan waves are self-caused action copies expanding from agents.",
      "Amber waves are independent world shocks crossing the same field.",
      "White brightening marks observed dE, and violet marks the residual prediction error used to update the boundary.",
    ],
    sources: [
      { label: "paper", href: `${repoUrl}/papers/first_order_self/paper.md` },
      { label: "browser figure", href: `${repoUrl}/papers/first_order_self/figures/fig4_agents_reafference_plasma.html` },
    ],
  },
  {
    route: "syntax",
    nav: "syntax",
    draw: drawSyntax,
    color: colors.amber,
    kicker: "concerned syntax",
    title: "concern selects which structure becomes usable syntax",
    subtitle: "Raw observations become slots, slots become candidate programs, and concern gates the intervention that actually transfers out of distribution.",
    thesis: "Syntax is treated as causal constituency under pressure: the useful structure is the one that survives intervention, not the one that merely compresses the scene.",
    motions: [
      "Raw pixels stream into semantic slots with confidence bands.",
      "Concern opens a gate only for slots that alter the target outcome.",
      "Candidate programs compete; the selected path lights the intervention transfer.",
    ],
    sources: [
      { label: "experiment", href: `${repoUrl}/experiments/concerned_syntax/README.md` },
      { label: "paper", href: `${repoUrl}/papers/concerned_syntax/paper.md` },
    ],
  },
  {
    route: "bodies",
    nav: "bodies",
    draw: drawBodies,
    color: colors.green,
    kicker: "viable computational bodies",
    title: "modules become a body when viability closes the loop",
    subtitle: "Typed modules assemble, perturbations hit, and the body repairs itself only when the architecture maintains a viability signal through action.",
    thesis: "A computational body is not just a graph of modules; it is a typed control organization that keeps enough of itself viable under perturbation.",
    motions: [
      "Modules dock into sensor, memory, policy, and actuator roles.",
      "A perturbation lowers viability and exposes a broken pathway.",
      "Repair rewires the body through the formal gate, then viability recovers.",
    ],
    sources: [
      { label: "experiment", href: `${repoUrl}/experiments/viable_computational_bodies/README.md` },
      { label: "paper", href: `${repoUrl}/papers/viable_computational_bodies/paper.md` },
    ],
  },
  {
    route: "symmetry",
    nav: "symmetry",
    draw: drawSymmetry,
    color: colors.violet,
    kicker: "weakness and invariance",
    title: "the weaker symmetry-compatible rule wins out of distribution",
    subtitle: "Training data underdetermines the answer. The animation shows candidate hypotheses tying in-sample, then separating when a transformation reveals the invariant.",
    thesis: "Generalization comes from compatible weakness: a rule that respects the symmetry has fewer arbitrary commitments and survives the OOD transformation.",
    motions: [
      "Training examples rotate through a latent symmetry group.",
      "A memorizing rule hugs the seen samples while the weak rule tracks the invariant.",
      "The OOD probe separates apparent fit from preserved structure.",
    ],
    sources: [
      { label: "experiment", href: `${repoUrl}/experiments/symbolic_weakness/README.md` },
      { label: "paper", href: `${repoUrl}/papers/weakness_invariance_neurips/paper.md` },
    ],
  },
  {
    route: "activation",
    nav: "activation",
    draw: drawActivation,
    color: colors.rose,
    kicker: "activation geometry",
    title: "interventions test whether a direction is causal or decorative",
    subtitle: "Layer states form a geometry, probes read candidate directions, and matched controls decide whether steering changes behavior for the right reason.",
    thesis: "A direction is interesting only when activation-space evidence, behavior, and controls agree that the intervention moves the mechanism rather than a surface correlate.",
    motions: [
      "Layer bands carry hidden states toward a candidate direction.",
      "Probe confidence rises only where the direction is stable across controls.",
      "Steering arrows either change behavior or fail against matched nulls.",
    ],
    sources: [
      { label: "experiment", href: `${repoUrl}/experiments/activation_geometry/README.md` },
      { label: "readiness", href: `${repoUrl}/docs/paper_readiness.md` },
    ],
  },
  {
    route: "findings",
    nav: "findings",
    draw: drawFindings,
    color: colors.amber,
    kicker: "results & papers",
    title: "what we found, and the papers",
    subtitle: "Three results turn the program's thesis — adaptive systems rediscover geometry because geometry is the portable language of constraints — into measured claims, from a symbolic separation to a causal warp of a learned spatial map.",
    thesis: "The story in one line: symmetry pressure makes generalization measurable as WEAKNESS; weakness and the toroidal GEOMETRY of a spatial code are the same thing seen two ways; and a goal signal CAUSALLY DEFORMS that geometry — concern reshapes the map. The first two are clean but partly definitional; the third is the non-circular result, an intervention that warps the metric where the reward is.",
    motions: [
      "Paper 1 — weakness predicts out-of-distribution generalization where loss, MDL, flatness and validation do not (cyclic/dihedral 100% vs 0%; neural Pearson r = +0.81).",
      "Paper A — the same scalar tracks the toroidal topology of a learned spatial code (Betti numbers 1,2,1); spectral leg confirmed at rho = +0.89.",
      "Paper B — a reward CAUSALLY deforms the code's induced metric at the rewarded location and tracks it when moved (specificity +0.65 / +1.27; control flat +0.04) — local resolution bought at the cost of global generalization.",
    ],
    sources: [
      { label: "PDF · Paper 1: Weakness Predicts OOD", href: "papers/weakness_predicts_ood.pdf" },
      { label: "PDF · Paper A: Weakness \u2192 Toroidal Topology", href: "papers/weakness_predicts_topology.pdf" },
      { label: "PDF · Paper B: Concern Deforms the Metric", href: "papers/concern_deforms_metric.pdf" },
      { label: "repo", href: "https://github.com/jawauntb/research-derived-experiments" },
    ],
  },
];

const pages = Object.fromEntries(pageList.map(page => [page.route, page]));
const tourStepSeconds = 10.5;
const metricNodes = [];
let metricSignature = "";
let phaseSignature = "";
let frameRequest = 0;
let routeButtons = [];
let reafferenceBasis = null;

const state = {
  route: "overview",
  paused: false,
  showLabels: true,
  storyMode: true,
  tourMode: false,
  tourRouteIndex: 0,
  tourRouteStartedAt: 0,
  tourRouting: false,
  tourExpectedRoute: "",
  speed: 1,
  elapsed: 0,
  lastFrame: 0,
  width: 960,
  height: 600,
  dpr: 1,
  reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
};

const programLayers = [
  {
    label: "weakness selects invariants",
    short: "weakness",
    detail: "shortcut and invariant rules tie in-sample; weakness predicts OOD",
    status: "foundation",
    value: "0.99+ LB",
    color: colors.violet,
    level: 0.70,
  },
  {
    label: "activation geometry frontier",
    short: "activation frontier",
    detail: "directions must survive controls before they count as mechanisms",
    status: "frontier",
    value: "specificity open",
    color: colors.rose,
    level: 0.56,
  },
  {
    label: "self/world attribution",
    short: "self/world",
    detail: "null anchors and current replay turn observed dE into source credit",
    status: "mechanism",
    value: "12/13 current replay",
    color: colors.cyan,
    level: 0.84,
  },
  {
    label: "concerned intervention syntax",
    short: "intervention syntax",
    detail: "agents choose useful program families, targets, and low-cost probes",
    status: "mechanism",
    value: "rich gate 1.00",
    color: colors.amber,
    level: 0.92,
  },
  {
    label: "viable computational bodies",
    short: "viable bodies",
    detail: "body search consumes the syntax contract under formal viability gates",
    status: "mechanism",
    value: "body gate 1.00",
    color: colors.green,
    level: 0.88,
  },
  {
    label: "next combined frontier",
    short: "next frontier",
    detail: "learned object slots, neural modules, and open-ended program discovery",
    status: "open",
    value: "scaffolds visible",
    color: colors.blue,
    level: 0.46,
  },
];

const phase2Steps = [
  {
    label: "RGB pixel scene",
    short: "pixels",
    value: "raw image",
    status: "input",
    color: colors.cyan,
    story: "The scene begins as rendered pixels with a hidden parse; the accepted route does not start from a symbolic answer.",
    detail: "synthetic RGB surface with hidden binding",
  },
  {
    label: "learned foreground",
    short: "mask",
    value: "no CC path",
    status: "learned",
    color: colors.blue,
    story: "A learned foreground pixel model replaces the old algorithmic connected-component extractor on the accepted path.",
    detail: "foreground classifier plus slot-local search",
  },
  {
    label: "six learned slots",
    short: "slots",
    value: "1.000 recovery",
    status: "evidence",
    color: colors.green,
    story: "The learned mask resolves into six canonical object slots; Modal evidence reports slot and scene recovery at 1.000.",
    detail: "slot recovery 1.000 / scene recovery 1.000",
  },
  {
    label: "semantic profiles",
    short: "profiles",
    value: "purity 1.000",
    status: "induced",
    color: colors.violet,
    story: "Anonymous slots induce semantic profiles from intervention success, bound/unbound utility gaps, and action templates.",
    detail: "family, pair, action-template metrics 1.000",
  },
  {
    label: "rich intervention program",
    short: "programs",
    value: "transfer 1.000",
    status: "mechanism",
    color: colors.amber,
    story: "The discovered-profile world model preserves the held-out rich-program transfer gate from learned object slots.",
    detail: "observe, move, ablate, and compose families compete",
  },
  {
    label: "executable body",
    short: "bodies",
    value: "older 2A pass",
    status: "2B bridge",
    color: colors.green,
    story: "Searched executable bodies already consume earlier 2A contracts while reward-only, family-proxy, and target-proxy bodies fail.",
    detail: "module bodies pass label-free transfer gates",
  },
  {
    label: "next frontier",
    short: "frontier",
    value: "newest 2A -> 2B",
    status: "not overclaimed",
    color: colors.rose,
    story: "The next honest step is 2B consumption of the learned-object-slot/discovered-profile contract, then trainable modules and less controlled vision.",
    detail: "not natural-image vision or full slot attention",
  },
];

const storyPlans = {
  overview: programLayers.map(layer => ({
    label: layer.short,
    detail: layer.detail,
    color: layer.color,
  })),
  reafference: [
    { label: "efference copy", detail: "Agents emit self-prediction waves before the field knows what changed.", color: colors.cyan },
    { label: "world shock", detail: "External causes cross the same sensor field and can masquerade as self-change.", color: colors.amber },
    { label: "observed dE", detail: "The bright field is the combined observation that must be explained.", color: colors.green },
    { label: "source credit", detail: "Residual error moves the self/world boundary toward the right cause.", color: colors.violet },
  ],
  syntax: [
    { label: "raw scene", detail: "Observation starts as pixels with many possible compressions.", color: colors.cyan },
    { label: "semantic slots", detail: "Slots become candidates only after they carry stable structure.", color: colors.cyan },
    { label: "concern gate", detail: "Concern opens only where a slot changes the target outcome.", color: colors.amber },
    { label: "program test", detail: "Candidate programs compete by intervention, not by prettier descriptions.", color: colors.violet },
    { label: "OOD transfer", detail: "The selected syntax counts when it transfers beyond the seen scene.", color: colors.green },
  ],
  bodies: [
    { label: "typed modules", detail: "Sensor, memory, policy, and actuator roles assemble into one organization.", color: colors.cyan },
    { label: "viability loop", detail: "The module graph becomes body-like only when viability can be read through action.", color: colors.green },
    { label: "perturbation", detail: "A body claim has to survive damage, not just look organized at rest.", color: colors.rose },
    { label: "repair gate", detail: "Formal checks decide whether repair closes the loop or merely rewires noise.", color: colors.amber },
    { label: "recovered body", detail: "The accepted body is the one whose viability recovers after repair.", color: colors.green },
  ],
  symmetry: [
    { label: "train tie", detail: "Shortcut and invariant rules can look equally good on the seen examples.", color: colors.cyan },
    { label: "transform", detail: "A symmetry transformation exposes which rule carries less arbitrary baggage.", color: colors.violet },
    { label: "OOD probe", detail: "The out-of-distribution gate separates memorized fit from preserved structure.", color: colors.amber },
    { label: "weak rule wins", detail: "The weaker compatible rule survives because it respects the transformation.", color: colors.green },
  ],
  activation: [
    { label: "read state", detail: "Layer states supply a geometry, but geometry alone is not yet a mechanism.", color: colors.cyan },
    { label: "fit probe", detail: "A probe direction becomes interesting only if it is stable across controls.", color: colors.violet },
    { label: "steer", detail: "Intervention asks whether moving the direction changes behavior.", color: colors.amber },
    { label: "control check", detail: "Matched nulls must fail before the direction earns causal credit.", color: colors.rose },
  ],
  findings: [
    { label: "weakness predicts OOD", detail: "Paper 1: symmetry-compatible volume beats loss, MDL and flatness at predicting generalization (r = +0.81).", color: colors.cyan },
    { label: "weakness is geometry", detail: "Paper A: the same scalar tracks a spatial code's toroidal topology; spectral leg confirmed (rho = +0.89).", color: colors.violet },
    { label: "concern deforms it", detail: "Paper B: a reward causally warps the code's induced metric at the goal and tracks it when moved (specificity +1.27, control +0.04).", color: colors.amber },
  ],
};

const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));
const mix = (a, b, t) => a + (b - a) * t;
const ease = t => t * t * (3 - 2 * t);
const wave = t => 0.5 + 0.5 * Math.sin(t);
const cycle = (duration, offset = 0) => ((state.elapsed / duration + offset) % 1 + 1) % 1;
const phaseLabel = (labels, p) => labels[Math.min(labels.length - 1, Math.floor(p * labels.length))];
const hasPage = route => Object.prototype.hasOwnProperty.call(pages, route);
const routeIndex = route => Math.max(0, pageList.findIndex(page => page.route === route));
const storyActive = (index, focusIndex) => !state.storyMode || index === focusIndex;

function storyState(route, p) {
  const plan = storyPlans[route] || [];
  if (!plan.length) return { index: 0, step: null };
  const index = Math.min(plan.length - 1, Math.floor(clamp(p, 0, 0.999) * plan.length));
  return { index, step: plan[index] };
}

function routeFromHash() {
  const route = window.location.hash.replace("#", "");
  return hasPage(route) ? route : "overview";
}

function normalizeRoute() {
  const route = routeFromHash();
  if (window.location.hash !== `#${route}`) {
    window.location.hash = route;
  }
  return route;
}

function resizeCanvas() {
  const rect = canvas.parentElement.getBoundingClientRect();
  state.width = Math.max(1, Math.floor(rect.width));
  state.height = Math.max(1, Math.floor(rect.height));
  state.dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.floor(state.width * state.dpr);
  canvas.height = Math.floor(state.height * state.dpr);
  canvas.style.width = `${state.width}px`;
  canvas.style.height = `${state.height}px`;
  ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
  reafferenceBasis = null;
  scheduleFrame();
}

function setRoute(route) {
  state.route = hasPage(route) ? route : "overview";
  const page = pages[state.route];
  kickerEl.textContent = page.kicker;
  titleEl.textContent = page.title;
  subtitleEl.textContent = page.subtitle;
  thesisEl.textContent = page.thesis;
  motionListEl.replaceChildren(...page.motions.map(text => {
    const item = document.createElement("li");
    item.textContent = text;
    return item;
  }));
  sourceLinksEl.replaceChildren(...page.sources.map(source => {
    const link = document.createElement("a");
    link.href = source.href;
    link.textContent = source.label;
    return link;
  }));

  routeButtons.forEach(button => {
    const active = button.dataset.route === state.route;
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  [...cardsEl.children].forEach(card => {
    const active = card.dataset.route === state.route;
    if (active) card.setAttribute("aria-current", "page");
    else card.removeAttribute("aria-current");
  });
  if (tourStatusTextEl) updateTourStatus();
}

function buildCards() {
  const cards = pageList.map(page => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "experiment-card";
    button.dataset.route = page.route;
    const title = document.createElement("strong");
    title.textContent = page.nav;
    const thesis = document.createElement("span");
    thesis.textContent = page.thesis;
    button.append(title, thesis);
    button.addEventListener("click", () => {
      window.location.hash = page.route;
    });
    return button;
  });
  cardsEl.replaceChildren(...cards);
}

function buildNav() {
  routeButtons = pageList.map(page => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "nav-item";
    button.dataset.route = page.route;
    button.textContent = page.nav;
    button.addEventListener("click", () => {
      window.location.hash = page.route;
    });
    return button;
  });
  navEl.replaceChildren(...routeButtons);
}

function clearCanvas() {
  ctx.fillStyle = colors.dark;
  ctx.fillRect(0, 0, state.width, state.height);
}

function text(label, x, y, size = 13, color = colors.ink, align = "center", weight = "700") {
  if (!state.showLabels) return;
  ctx.save();
  let drawSize = size;
  ctx.font = `${weight} ${drawSize}px "DejaVu Sans Mono", ui-monospace, monospace`;
  let width = ctx.measureText(label).width;
  while (width > state.width - 16 && drawSize > 9) {
    drawSize -= 1;
    ctx.font = `${weight} ${drawSize}px "DejaVu Sans Mono", ui-monospace, monospace`;
    width = ctx.measureText(label).width;
  }
  let safeX = x;
  if (align === "left") safeX = clamp(x, 8, Math.max(8, state.width - width - 8));
  if (align === "right") safeX = clamp(x, Math.min(state.width - 8, width + 8), state.width - 8);
  if (align === "center") safeX = clamp(x, Math.min(state.width / 2, width / 2 + 8), Math.max(state.width / 2, state.width - width / 2 - 8));
  ctx.textAlign = align;
  ctx.textBaseline = "middle";
  ctx.lineJoin = "round";
  ctx.lineWidth = Math.max(3, size * 0.25);
  ctx.strokeStyle = "rgba(5, 7, 12, 0.78)";
  ctx.fillStyle = color;
  ctx.strokeText(label, safeX, y);
  ctx.fillText(label, safeX, y);
  ctx.restore();
}

function wrappedText(label, x, y, maxWidth, lineHeight, size = 12, color = colors.ink, align = "center", weight = "700", maxLines = 2) {
  if (!state.showLabels) return;
  ctx.save();
  ctx.font = `${weight} ${size}px "DejaVu Sans Mono", ui-monospace, monospace`;
  const words = label.split(/\s+/);
  const lines = [];
  let current = "";
  for (const word of words) {
    const trial = current ? `${current} ${word}` : word;
    if (ctx.measureText(trial).width <= maxWidth || !current) {
      current = trial;
      continue;
    }
    lines.push(current);
    current = word;
    if (lines.length === maxLines) break;
  }
  if (current && lines.length < maxLines) lines.push(current);
  if (lines.length === maxLines && words.join(" ").length > lines.join(" ").length) {
    const last = lines[lines.length - 1];
    lines[lines.length - 1] = last.length > 4 ? `${last.slice(0, Math.max(1, last.length - 3))}...` : last;
  }
  const startY = y - ((lines.length - 1) * lineHeight) / 2;
  lines.forEach((lineText, index) => text(lineText, x, startY + index * lineHeight, size, color, align, weight));
  ctx.restore();
}

function drawStoryCue(step, x, y, maxWidth, mapDetail) {
  const compact = state.width < 560;
  const width = Math.min(maxWidth, state.width - 24);
  const height = compact ? 58 : 66;
  const safeY = clamp(y, height / 2 + 12, state.height - height / 2 - 12);
  const activeStep = state.storyMode && step;
  const color = activeStep ? step.color : colors.faint;
  const label = activeStep ? step.label : "map mode";
  const detail = activeStep ? step.detail : mapDetail;
  roundedRect(x - width / 2, safeY - height / 2, width, height, 8, "rgba(8,9,13,0.82)", color);
  text(label, x, safeY - (compact ? 15 : 18), compact ? 10 : 12, activeStep ? color : colors.muted);
  wrappedText(detail, x, safeY + (compact ? 9 : 12), width - 24, compact ? 11 : 13, compact ? 8 : 10, colors.ink, "center", "700", 2);
}

function line(fromX, fromY, toX, toY, color, width = 2, alpha = 1, dash = null) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  if (dash) ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(fromX, fromY);
  ctx.lineTo(toX, toY);
  ctx.stroke();
  ctx.restore();
}

function arrow(fromX, fromY, toX, toY, color, width = 2, alpha = 1, bend = 0) {
  const dx = toX - fromX;
  const dy = toY - fromY;
  const angle = Math.atan2(dy, dx);
  const midX = fromX + dx * 0.5 - dy * bend;
  const midY = fromY + dy * 0.5 + dx * bend;
  const head = Math.max(8, width * 4.2);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(fromX, fromY);
  ctx.quadraticCurveTo(midX, midY, toX, toY);
  ctx.stroke();
  ctx.translate(toX, toY);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-head, -head * 0.44);
  ctx.lineTo(-head * 0.62, 0);
  ctx.lineTo(-head, head * 0.44);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function dot(x, y, radius, color, alpha = 1) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function withAlpha(color, alpha) {
  if (color.startsWith("#") && color.length === 7) {
    const r = Number.parseInt(color.slice(1, 3), 16);
    const g = Number.parseInt(color.slice(3, 5), 16);
    const b = Number.parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  if (color.startsWith("rgb(")) {
    return color.replace("rgb(", "rgba(").replace(")", `, ${alpha})`);
  }
  return color;
}

function halo(x, y, radius, color, alpha = 0.28) {
  const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
  gradient.addColorStop(0, withAlpha(color, alpha));
  gradient.addColorStop(1, withAlpha(color, 0));
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();
}

function roundedRect(x, y, width, height, radius, fill, stroke = "rgba(246,239,228,0.18)") {
  ctx.save();
  ctx.fillStyle = fill;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function metricColor(name) {
  if (/self|slot|probe|weak|viability/i.test(name)) return colors.cyan;
  if (/world|concern|repair|steer/i.test(name)) return colors.amber;
  if (/error|perturb|ood|null/i.test(name)) return colors.violet;
  if (/observed|transfer|invariant|behavior/i.test(name)) return colors.green;
  return colors.blue;
}

function updateMetrics(metrics) {
  const nextSignature = metrics.map(metric => metric.label).join("|");
  if (nextSignature !== metricSignature) {
    metricSignature = nextSignature;
    metricNodes.length = 0;
    metricListEl.replaceChildren(...metrics.map(metric => {
      const row = document.createElement("div");
      const labelRow = document.createElement("div");
      const label = document.createElement("span");
      const value = document.createElement("span");
      const meter = document.createElement("div");
      const fill = document.createElement("span");

      row.className = "metric";
      labelRow.className = "metric-row";
      value.className = "metric-value";
      label.textContent = metric.label;
      meter.className = "meter";
      meter.append(fill);
      labelRow.append(label, value);
      row.append(labelRow, meter);
      metricNodes.push({ fill, value });
      return row;
    }));
  }

  metrics.forEach((metric, index) => {
    const node = metricNodes[index];
    if (!node) return;
    const color = metric.color || metricColor(metric.label);
    const width = `${clamp(metric.amount, 0, 1) * 100}%`;
    if (node.value.textContent !== metric.value) node.value.textContent = metric.value;
    if (node.fill.style.width !== width) node.fill.style.width = width;
    if (node.fill.style.background !== color) node.fill.style.background = color;
  });
}

function updatePhase(label, value, amount) {
  const width = `${clamp(amount, 0, 1) * 100}%`;
  const nextSignature = `${label}|${value}|${width}`;
  if (nextSignature === phaseSignature) return;
  phaseSignature = nextSignature;
  phaseLabelEl.textContent = label;
  phaseValueEl.textContent = value;
  phaseFillEl.style.width = width;
}

const findingsNodes = [
  { key: "weakness", label: "weakness", sub: "predicts OOD", detail: "r = +0.81", color: colors.cyan },
  { key: "geometry", label: "geometry", sub: "toroidal code", detail: "spectral rho +0.89", color: colors.violet },
  { key: "concern", label: "concern", sub: "deforms metric", detail: "specificity +1.27", color: colors.amber },
];

function drawFindings() {
  clearCanvas();
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 26 : 20);
  const { index: focusIndex, step } = storyState("findings", p);
  const vertical = w < 560;
  const n = findingsNodes.length;

  const pts = findingsNodes.map((node, i) => {
    const t = (i + 0.5) / n;
    return vertical
      ? { x: w * 0.42, y: h * (0.16 + 0.68 * t), node, i }
      : { x: w * (0.12 + 0.76 * t), y: h * 0.46, node, i };
  });

  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1];
    line(a.x, a.y, b.x, b.y, withAlpha(colors.faint, 0.5), 1.5, 0.6);
    const fp = (p * 1.0 + i * 0.33) % 1;
    const px = mix(a.x, b.x, fp), py = mix(a.y, b.y, fp);
    dot(px, py, 3.4 + 1.6 * wave(state.elapsed * 2 + i), b.node.color, 0.9);
  }

  pts.forEach(({ x, y, node, i }) => {
    const active = storyActive(i, focusIndex);
    const alpha = active ? 1 : 0.4;
    const r = Math.min(w, h) * (vertical ? 0.085 : 0.072);
    halo(x, y, r * 1.8, node.color, active ? 0.26 : 0.1);
    dot(x, y, r, withAlpha(node.color, active ? 0.9 : 0.4));
    dot(x, y, r * 0.62, colors.dark, 1);
    text(node.label, x, y - 4, vertical ? 13 : 14, withAlpha(colors.ink, alpha), "center", "700");
    text(node.sub, x, y + 12, 10, withAlpha(colors.muted, alpha), "center", "600");
    text(node.detail, x, y + r + 14, 11, withAlpha(node.color, alpha), "center", "700");
  });

  if (state.storyMode) {
    const f = pts[focusIndex];
    drawStoryCue(step, f.x, f.y - Math.min(w, h) * 0.12, w * 0.7, "three papers, one thesis");
  }

  updatePhase(state.storyMode ? "results story" : "results & papers",
    state.storyMode ? step.label : "three papers, one thesis", p);
  updateMetrics([
    { label: "weakness -> OOD", value: "r = +0.81", amount: 0.81, color: colors.cyan },
    { label: "weakness -> torus topology", value: "rho = +0.89", amount: 0.89, color: colors.violet },
    { label: "reward deforms metric", value: "+1.27 (control +0.04)", amount: 0.86, color: colors.amber },
  ]);
}

function drawOverview() {
  clearCanvas();
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 30 : 24);
  const { index: focusIndex, step } = storyState("overview", p);

  if (w < 560) drawProgramMobile(w, h, p, focusIndex);
  else drawProgramDesktop(w, h, p, focusIndex);

  updatePhase(state.storyMode ? "program story" : "program synthesis", state.storyMode ? step.label : "map mode: all tracks", p);
  updateMetrics([
    { label: "paper corpus", value: "34 papers", amount: 1, color: colors.green },
    { label: "public result notes", value: "117 reports", amount: 0.92, color: colors.cyan },
    { label: "open frontiers", value: "kept visible", amount: 0.46 + 0.12 * wave(state.elapsed * 0.7), color: colors.violet },
  ]);
}

function drawProgramField(nodes, p) {
  const cell = clamp(Math.floor(state.width / 34), 9, 22);
  for (let y = 0; y < state.height; y += cell) {
    for (let x = 0; x < state.width; x += cell) {
      let chosen = nodes[0];
      let intensity = 0;
      nodes.forEach((node, index) => {
        const dx = (x + cell / 2 - node.x) / state.width;
        const dy = (y + cell / 2 - node.y) / state.height;
        const ridge = Math.sin(dx * 18 + dy * 22 + state.elapsed * 0.9 + index) * 0.08;
        const force = Math.exp(-((dx * dx + dy * dy) / (0.018 + node.layer.level * 0.012))) * (0.52 + ridge);
        if (force > intensity) {
          intensity = force;
          chosen = node;
        }
      });
      const alpha = clamp(0.04 + intensity * 0.36 + 0.05 * wave(p * Math.PI * 2 + x * 0.02 + y * 0.018), 0.04, 0.42);
      ctx.fillStyle = withAlpha(chosen.layer.color, alpha);
      ctx.fillRect(x, y, cell + 0.5, cell + 0.5);
    }
  }
}

function drawProgramDesktop(w, h, p, focusIndex) {
  const cx = w * 0.5;
  const cy = h * 0.51;
  const radius = Math.min(w, h) * 0.34;
  const nodes = programLayers.map((layer, index) => {
    const angle = -Math.PI / 2 + index * (Math.PI * 2 / programLayers.length) + Math.sin(state.elapsed * 0.12) * 0.08;
    return {
      layer,
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius * 0.72,
      index,
    };
  });

  drawProgramField(nodes, p);

  [0.36, 0.58, 0.82].forEach((scale, index) => {
    ctx.save();
    ctx.strokeStyle = index === 2 ? withAlpha(colors.violet, 0.32) : "rgba(246,239,228,0.14)";
    ctx.lineWidth = index === 2 ? 2 : 1;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * scale, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  });

  roundedRect(cx - w * 0.20, cy - h * 0.14, w * 0.40, h * 0.28, 8, "rgba(8,9,13,0.74)", "rgba(246,239,228,0.22)");
  text("constraint -> concern -> intervention", cx, cy - 44, 16, colors.ink);
  text("evidence packets cross gates", cx, cy - 12, 13, colors.cyan);
  text("frontiers stay visible", cx, cy + 18, 13, colors.violet);
  text("zoom pages explain each mechanism", cx, cy + 48, 12, colors.muted);

  nodes.forEach(node => {
    const next = nodes[(node.index + 1) % nodes.length];
    const pulse = (p * programLayers.length + node.index * 0.28) % 1;
    const active = storyActive(node.index, focusIndex);
    line(node.x, node.y, next.x, next.y, node.layer.color, active ? 3.2 : 1.5, active ? 0.72 : 0.28);
    arrow(node.x, node.y, cx, cy, node.layer.color, active ? 3 : 1.8, active ? 0.82 : 0.34, 0.07);
    dot(mix(node.x, cx, pulse), mix(node.y, cy, pulse), active ? 6 : 4, node.layer.color, 0.92);
    halo(node.x, node.y, (active ? 82 : 54) + 18 * wave(state.elapsed * 1.2 + node.index), node.layer.color, active ? 0.24 : 0.12);
    roundedRect(node.x - 92, node.y - 34, 184, 68, 8, active ? "rgba(12,15,24,0.92)" : "rgba(12,15,24,0.78)", node.layer.color);
    text(node.layer.status, node.x, node.y - 18, 10, node.layer.color);
    text(node.layer.label, node.x, node.y + 2, 12, colors.ink);
    text(node.layer.value, node.x, node.y + 22, 10, colors.muted);
  });

  for (let i = 0; i < 28; i++) {
    const a = i * 0.54 + state.elapsed * 0.22;
    const rr = radius * (0.24 + (i % 7) * 0.095);
    const color = programLayers[i % programLayers.length].color;
    dot(cx + Math.cos(a) * rr, cy + Math.sin(a * 1.28) * rr * 0.62, 1.6 + (i % 3), color, 0.36);
  }

  drawStoryCue(storyPlans.overview[focusIndex], cx, h - 96, Math.min(w * 0.72, 680), "All research tracks stay visible so reviewers can compare the program at once.");
}

function drawProgramMobile(w, h, p, focusIndex) {
  const top = 50;
  const bottom = h - 66;
  const spineX = w * 0.18;
  const boxX = w * 0.34;
  const boxWidth = Math.max(158, w - boxX - 12);
  const nodes = programLayers.map((layer, index) => ({
    layer,
    index,
    x: spineX,
    y: mix(top, bottom, index / (programLayers.length - 1)),
  }));

  drawProgramField(nodes, p);
  line(spineX, top - 18, spineX, bottom + 18, colors.faint, 2, 0.4, [4, 10]);
  text("whole program", w * 0.5, 24, 13, colors.ink);

  nodes.forEach(node => {
    const active = storyActive(node.index, focusIndex);
    const packet = (p * programLayers.length + node.index * 0.23) % 1;
    const next = nodes[Math.min(nodes.length - 1, node.index + 1)];
    if (next !== node) {
      dot(spineX, mix(node.y, next.y, packet), active ? 5 : 3.5, node.layer.color, 0.8);
    }
    halo(node.x, node.y, active ? 58 : 38, node.layer.color, active ? 0.22 : 0.10);
    dot(node.x, node.y, active ? 8 : 5, node.layer.color, 0.9);
    line(node.x + 10, node.y, boxX - 8, node.y, node.layer.color, active ? 3 : 1.4, active ? 0.72 : 0.32);
    roundedRect(boxX, node.y - 28, boxWidth, 56, 8, active ? "rgba(12,15,24,0.92)" : "rgba(12,15,24,0.78)", node.layer.color);
    text(node.layer.short, boxX + boxWidth * 0.5, node.y - 9, active ? 11 : 10, colors.ink);
    text(node.layer.value, boxX + boxWidth * 0.5, node.y + 10, 9, node.layer.color);
  });

  drawStoryCue(storyPlans.overview[focusIndex], w * 0.5, h - 96, w - 24, "All tracks remain live in map mode.");
}

function drawPhase2() {
  clearCanvas();
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 28 : 20);
  const focusIndex = Math.floor(p * phase2Steps.length) % phase2Steps.length;
  const focus = phase2Steps[focusIndex];

  if (w < 760) drawPhase2Mobile(w, h, p, focusIndex);
  else drawPhase2Desktop(w, h, p, focusIndex);

  updatePhase("phase 2 bridge", `${focus.status}: ${focus.label}`, p);
  updateMetrics([
    { label: "learned slot bridge", value: "1.000 recovery", amount: 1, color: colors.green },
    { label: "profile transfer gate", value: "1.000 pass", amount: 1, color: colors.amber },
    { label: "newest 2B link", value: "frontier", amount: 0.42 + 0.14 * wave(state.elapsed * 0.8), color: colors.rose },
  ]);
}

function drawPhase2Field(nodes, focusIndex) {
  const cell = clamp(Math.floor(state.width / 42), 8, 18);
  for (let y = 0; y < state.height; y += cell) {
    for (let x = 0; x < state.width; x += cell) {
      let strongest = 0;
      let color = colors.cyan;
      nodes.forEach((node, index) => {
        const dx = (x + cell * 0.5 - node.x) / state.width;
        const dy = (y + cell * 0.5 - node.y) / state.height;
        const gate = index === focusIndex ? 1.15 : 0.72;
        const force = Math.exp(-(dx * dx + dy * dy) / 0.018) * gate;
        if (force > strongest) {
          strongest = force;
          color = node.step.color;
        }
      });
      const ripple = 0.04 * wave(x * 0.024 + y * 0.018 + state.elapsed * 1.1);
      ctx.fillStyle = withAlpha(color, clamp(0.035 + strongest * 0.24 + ripple, 0.03, 0.34));
      ctx.fillRect(x, y, cell + 0.5, cell + 0.5);
    }
  }
}

function drawPhase2Pixels(x, y, width, height, active) {
  const cols = 5;
  const rows = 4;
  const gap = 3;
  const cell = Math.min((width - gap * (cols - 1)) / cols, (height - gap * (rows - 1)) / rows);
  const colorsByRole = [colors.cyan, colors.amber, colors.green, colors.violet, colors.rose];
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const index = (row * cols + col) % colorsByRole.length;
      const pulse = active ? wave(state.elapsed * 2.2 + row + col) : 0.34;
      ctx.fillStyle = withAlpha(colorsByRole[index], 0.24 + pulse * 0.46);
      ctx.fillRect(x + col * (cell + gap), y + row * (cell + gap), cell, cell);
    }
  }
}

function drawPhase2Mask(x, y, width, height, active) {
  const cols = 6;
  const rows = 4;
  const gap = 2;
  const cell = Math.min((width - gap * (cols - 1)) / cols, (height - gap * (rows - 1)) / rows);
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const foreground = (row === 1 && col > 0 && col < 5) || (row === 2 && col > 1 && col < 5) || (row === 3 && col === 3);
      const pulse = active ? wave(state.elapsed * 2.4 + row * 0.8 + col) : 0.30;
      ctx.fillStyle = foreground ? withAlpha(colors.blue, 0.34 + pulse * 0.48) : "rgba(246,239,228,0.07)";
      ctx.fillRect(x + col * (cell + gap), y + row * (cell + gap), cell, cell);
    }
  }
  line(x + width * 0.12, y + height + 8, x + width * 0.88, y + height + 8, active ? colors.blue : colors.faint, 4, active ? 0.72 : 0.32);
}

function drawPhase2Slots(x, y, active, compact = false) {
  if (compact) {
    for (let index = 0; index < 6; index++) {
      const col = index % 3;
      const row = Math.floor(index / 3);
      const sx = x - 22 + col * 22;
      const sy = y - 11 + row * 22;
      halo(sx, sy, active ? 13 : 9, colors.green, active ? 0.16 : 0.08);
      dot(sx, sy, active ? 4.4 : 3.2, index % 2 ? colors.green : colors.cyan, 0.88);
    }
    return;
  }

  const labels = ["slot recovery", "scene recovery", "center error"];
  labels.forEach((label, index) => {
    const yy = y + index * 19;
    const color = index === 2 ? colors.blue : colors.green;
    const amount = index === 2 ? 0.42 : 0.96;
    line(x, yy, x + 88 * (active ? amount + 0.04 * wave(state.elapsed + index) : amount * 0.72), yy, color, 7, 0.72);
    text(index === 2 ? "err .019" : label.replace(" recovery", " 1.000"), x + 98, yy, 9, colors.muted, "left", "600");
  });
}

function drawPhase2Profiles(x, y, active, compact = false) {
  const labels = compact ? ["fam", "pair", "act", "pur"] : ["family", "pair", "action", "purity"];
  labels.forEach((label, index) => {
    const angle = -Math.PI / 2 + index * (Math.PI * 2 / labels.length);
    const px = x + Math.cos(angle) * (compact ? 24 : 32);
    const py = y + Math.sin(angle) * (compact ? 18 : 24);
    roundedRect(px - (compact ? 14 : 22), py - 10, compact ? 28 : 44, 20, 6, "rgba(12,15,24,0.86)", active ? colors.violet : "rgba(181,140,255,0.38)");
    text(label, px, py, compact ? 7 : 8, active ? colors.violet : colors.muted);
  });
  dot(x, y, active ? 5 : 3.5, colors.ink, 0.88);
}

function drawPhase2Program(x, y, active) {
  ["observe", "move", "ablate", "compose"].forEach((label, index) => {
    const yy = y + index * 17;
    const selected = active && index === Math.floor(cycle(4, index * 0.03) * 4);
    text(label, x, yy, selected ? 10 : 9, selected ? colors.amber : colors.muted);
  });
}

function drawPhase2Body(x, y, active, compact = false) {
  const moduleWidth = compact ? 22 : 40;
  const moduleHeight = compact ? 15 : 24;
  const modules = compact
    ? [
        [x - 18, y - 11, colors.cyan],
        [x + 15, y - 11, colors.blue],
        [x - 10, y + 14, colors.amber],
        [x + 20, y + 13, colors.green],
      ]
    : [
        [x - 36, y - 20, colors.cyan],
        [x + 34, y - 20, colors.blue],
        [x - 22, y + 28, colors.amber],
        [x + 44, y + 26, colors.green],
      ];
  modules.forEach(([mx, my, color], index) => {
    const activeRadius = compact ? 2.6 + wave(state.elapsed + index) * 0.9 : 3.8 + wave(state.elapsed + index) * 1.8;
    const idleRadius = compact ? 2.3 : 3.2;
    roundedRect(mx - moduleWidth / 2, my - moduleHeight / 2, moduleWidth, moduleHeight, 5, "rgba(12,15,24,0.82)", color);
    dot(mx, my, active ? activeRadius : idleRadius, color, 0.9);
  });
  for (let i = 0; i < modules.length; i++) {
    const a = modules[i];
    const b = modules[(i + 1) % modules.length];
    line(a[0], a[1], b[0], b[1], active ? colors.green : colors.faint, 1.4, active ? 0.62 : 0.32);
  }
}

function drawPhase2Glyph(step, x, y, active, compact = false) {
  if (step.short === "pixels") {
    drawPhase2Pixels(x - (compact ? 25 : 42), y - (compact ? 18 : 28), compact ? 50 : 84, compact ? 36 : 56, active);
    return;
  }
  if (step.short === "mask") {
    drawPhase2Mask(x - (compact ? 27 : 42), y - (compact ? 18 : 28), compact ? 54 : 84, compact ? 34 : 54, active);
    return;
  }
  if (step.short === "slots") {
    if (compact) drawPhase2Slots(x, y, active, true);
    else drawPhase2Slots(x - 54, y - 19, active);
    return;
  }
  if (step.short === "profiles") {
    drawPhase2Profiles(x, y, active, compact);
    return;
  }
  if (step.short === "programs") {
    drawPhase2Program(x, y - (compact ? 20 : 25), active);
    return;
  }
  if (step.short === "bodies") {
    drawPhase2Body(x, y, active, compact);
    return;
  }
  halo(x, y, active ? 60 : 42, colors.rose, active ? 0.22 : 0.10);
  line(x - 44, y + 20, x + 44, y - 20, colors.rose, 2, active ? 0.72 : 0.36, [4, 8]);
  line(x - 44, y - 20, x + 44, y + 20, colors.blue, 2, active ? 0.62 : 0.28, [4, 8]);
  text("open", x, y, 11, colors.rose);
}

function phase2PathPoint(nodes, progress) {
  const scaled = clamp(progress, 0, 0.999) * (nodes.length - 1);
  const index = Math.floor(scaled);
  const local = scaled - index;
  const a = nodes[index];
  const b = nodes[index + 1] || nodes[index];
  return { x: mix(a.x, b.x, ease(local)), y: mix(a.y, b.y, ease(local)), color: b.step.color };
}

function drawPhase2Desktop(w, h, p, focusIndex) {
  const cardW = clamp(w / (phase2Steps.length + 2.2), 108, 136);
  const cardH = 112;
  const nodes = phase2Steps.map((step, index) => ({
    step,
    index,
    x: mix(w * 0.08, w * 0.92, index / (phase2Steps.length - 1)),
    y: h * (index % 2 ? 0.57 : 0.37),
  }));
  drawPhase2Field(nodes, focusIndex);

  text(state.storyMode ? "story follows learned slots -> profiles -> transfer" : "map mode keeps every gate visible", w * 0.5, h * 0.08, 14, colors.ink);
  nodes.forEach((node, index) => {
    const active = state.storyMode ? index === focusIndex : true;
    const next = nodes[index + 1];
    if (next) {
      arrow(node.x + cardW * 0.48, node.y, next.x - cardW * 0.48, next.y, next.step.color, active || index + 1 === focusIndex ? 2.8 : 1.6, active ? 0.72 : 0.34, index % 2 ? -0.05 : 0.05);
      const packet = (p * phase2Steps.length + index * 0.31) % 1;
      if (packet < 1) {
        dot(mix(node.x + cardW * 0.48, next.x - cardW * 0.48, ease(packet)), mix(node.y, next.y, ease(packet)), active ? 5.5 : 3.5, next.step.color, 0.86);
      }
    }

    halo(node.x, node.y, active ? 88 : 58, node.step.color, active ? 0.23 : 0.10);
    roundedRect(node.x - cardW / 2, node.y - cardH / 2, cardW, cardH, 8, active ? "rgba(12,15,24,0.92)" : "rgba(12,15,24,0.72)", node.step.color);
    drawPhase2Glyph(node.step, node.x, node.y - 7, active);
    text(node.step.short, node.x, node.y + 34, active ? 11 : 10, colors.ink);
    text(node.step.value, node.x, node.y + 50, 8, node.step.color);
  });

  const controlY = h * 0.80;
  const failX = w * 0.13;
  const frontierX = w * 0.87;
  roundedRect(failX - 92, controlY - 32, 184, 64, 8, "rgba(255,143,155,0.05)", "rgba(255,143,155,0.36)");
  text("controls fail", failX, controlY - 8, 12, colors.rose);
  text("reward / proxy / supplied-label shortcuts", failX, controlY + 13, 9, colors.muted);
  roundedRect(frontierX - 98, controlY - 32, 196, 64, 8, "rgba(111,168,255,0.05)", "rgba(111,168,255,0.38)");
  text("frontier remains", frontierX, controlY - 8, 12, colors.blue);
  text("2B consumes newest slot contract", frontierX, controlY + 13, 9, colors.muted);
  line(failX + 102, controlY, frontierX - 108, controlY, colors.faint, 1.4, 0.34, [5, 9]);

  if (state.storyMode) {
    const focus = phase2Steps[focusIndex];
    const point = phase2PathPoint(nodes, p);
    halo(point.x, point.y, 44, point.color, 0.24);
    dot(point.x, point.y, 7, point.color, 0.95);
    roundedRect(w * 0.25, h * 0.86, w * 0.50, h * 0.10, 8, "rgba(8,9,13,0.80)", focus.color);
    wrappedText(focus.story, w * 0.50, h * 0.91, w * 0.45, 15, 11, colors.ink, "center", "700", 2);
  }
}

function drawPhase2Mobile(w, h, p, focusIndex) {
  const top = 44;
  const bottom = h - 92;
  const spineX = w * 0.18;
  const boxH = h < 380 ? 34 : 40;
  const nodes = phase2Steps.map((step, index) => ({
    step,
    index,
    x: spineX,
    y: mix(top, bottom, index / (phase2Steps.length - 1)),
  }));
  drawPhase2Field(nodes, focusIndex);
  line(spineX, top - 18, spineX, bottom + 18, colors.faint, 2, 0.42, [4, 9]);
  text("phase 2 story", w * 0.54, 24, 13, colors.ink);

  nodes.forEach((node, index) => {
    const active = state.storyMode ? index === focusIndex : true;
    const boxX = w * 0.31;
    const boxW = w - boxX - 12;
    halo(node.x, node.y, active ? 44 : 28, node.step.color, active ? 0.22 : 0.10);
    dot(node.x, node.y, active ? 7 : 5, node.step.color, 0.9);
    line(node.x + 10, node.y, boxX - 8, node.y, node.step.color, active ? 2.6 : 1.2, active ? 0.72 : 0.30);
    roundedRect(boxX, node.y - boxH / 2, boxW, boxH, 8, active ? "rgba(12,15,24,0.92)" : "rgba(12,15,24,0.74)", node.step.color);
    text(node.step.short, boxX + boxW * 0.38, node.y - (boxH > 36 ? 7 : 6), active ? 10 : 9, colors.ink);
    text(node.step.value, boxX + boxW * 0.38, node.y + (boxH > 36 ? 9 : 7), 8, node.step.color);
    drawPhase2Glyph(node.step, boxX + boxW - 32, node.y, active, true);
  });

  const point = phase2PathPoint(nodes, p);
  dot(point.x, point.y, 4.5, point.color, 0.9);
  const focus = phase2Steps[focusIndex];
  roundedRect(12, h - 78, w - 24, 60, 8, "rgba(8,9,13,0.82)", focus.color);
  wrappedText(focus.story, w * 0.5, h - 52, w - 44, 12, 9, colors.ink, "center", "700", 2);
  text(focus.detail, w * 0.5, h - 32, 8, colors.muted);
}

const agents = [
  { name: "agent A", x: 0.28, y: 0.38, phase: 0.05 },
  { name: "agent B", x: 0.66, y: 0.58, phase: 1.9 },
  { name: "agent C", x: 0.78, y: 0.28, phase: 3.2 },
];

const worldSources = [
  { x: 0.14, y: 0.78, phase: 2.4 },
  { x: 0.88, y: 0.76, phase: 5.3 },
];

function buildReafferenceBasis(cell) {
  const cols = Math.ceil(state.width / cell);
  const rows = Math.ceil(state.height / cell);
  const count = cols * rows;
  const basis = {
    cell,
    cols,
    rows,
    xs: new Float32Array(count),
    ys: new Float32Array(count),
    selfBase: new Float32Array(count),
    worldBase: new Float32Array(count),
    observedBase: new Float32Array(count),
    agentDistances: agents.map(() => new Float32Array(count)),
    sourceDistances: worldSources.map(() => new Float32Array(count)),
  };

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const index = row * cols + col;
      const nx = (col * cell + cell / 2) / state.width;
      const ny = 1 - (row * cell + cell / 2) / state.height;
      basis.xs[index] = col * cell;
      basis.ys[index] = row * cell;

      agents.forEach((agent, agentIndex) => {
        const d = Math.hypot(nx - agent.x, ny - agent.y);
        basis.agentDistances[agentIndex][index] = d;
        basis.selfBase[index] += Math.exp(-(d * d) / 0.026) * 0.48;
        basis.observedBase[index] += Math.exp(-(d * d) / 0.006) * 0.34;
      });

      worldSources.forEach((source, sourceIndex) => {
        const d = Math.hypot(nx - source.x, ny - source.y);
        basis.sourceDistances[sourceIndex][index] = d;
        basis.worldBase[index] += Math.exp(-(d * d) / 0.028) * 0.46;
      });
    }
  }

  return basis;
}

function fieldAt(index, basis, p) {
  let self = basis.selfBase[index];
  let world = basis.worldBase[index];
  let observed = basis.observedBase[index];
  const nx = (basis.xs[index] + basis.cell / 2) / state.width;
  const ny = 1 - (basis.ys[index] + basis.cell / 2) / state.height;
  const selfRadius = 0.04 + 0.42 * p;
  const worldRadius = 0.03 + 0.58 * ((p + 0.28) % 1);

  basis.agentDistances.forEach(distances => {
    const d = distances[index];
    self += Math.exp(-((d - selfRadius) ** 2) / 0.0014) * (p < 0.45 ? 1.1 : 0.4);
  });

  basis.sourceDistances.forEach(distances => {
    const d = distances[index];
    world += Math.exp(-((d - worldRadius) ** 2) / 0.0018) * (p > 0.18 && p < 0.72 ? 1.22 : 0.25);
  });

  observed += Math.min(1.2, self * 0.72 + world * 0.76) * (p > 0.38 ? 0.7 : 0.42);
  const errorWave = (ny - 0.44) - 0.12 * Math.sin(nx * 8.2 + p * 6.2);
  const error = Math.exp(-(errorWave * errorWave) / 0.0022) * (p > 0.63 ? 0.86 : 0.18);

  return { self: clamp(self, 0, 1), world: clamp(world, 0, 1), observed: clamp(observed, 0, 1), error: clamp(error, 0, 1) };
}

function drawReafference() {
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 8.5 : 7);
  const { index: focusIndex, step } = storyState("reafference", p);
  const compact = Math.min(w, h) < 600;
  const cell = Math.max(8, Math.floor(Math.min(w, h) / 82));
  if (!reafferenceBasis || reafferenceBasis.cell !== cell) {
    reafferenceBasis = buildReafferenceBasis(cell);
  }
  clearCanvas();

  for (let row = 0; row < reafferenceBasis.rows; row++) {
    for (let col = 0; col < reafferenceBasis.cols; col++) {
      const index = row * reafferenceBasis.cols + col;
      const x = reafferenceBasis.xs[index];
      const y = reafferenceBasis.ys[index];
      const f = fieldAt(index, reafferenceBasis, p);
      const texture = 0.90 + 0.10 * Math.sin(x * 0.034 + y * 0.027 + state.elapsed);
      const r = clamp(7 + f.world * 178 + f.observed * 176 + f.error * 118, 0, 255) * texture;
      const g = clamp(12 + f.self * 210 + f.world * 104 + f.observed * 192 + f.error * 68, 0, 255) * texture;
      const b = clamp(30 + f.self * 220 + f.observed * 172 + f.error * 230, 0, 255) * texture;
      ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.fillRect(x, y, cell + 1, cell + 1);
    }
  }

  agents.forEach((agent, index) => {
    const x = agent.x * w;
    const y = (1 - agent.y) * h;
    const active = !state.storyMode || focusIndex === 0 || focusIndex === 2 || focusIndex === 3;
    halo(x, y, Math.min(w, h) * (0.08 + 0.035 * wave(state.elapsed * 2 + agent.phase)), "rgb(93,231,239)", active ? 0.22 : 0.10);
    dot(x, y, 9, colors.ink);
    dot(x, y, active ? 4 : 3, colors.cyan, active ? 1 : 0.58);
    const sx = x + Math.cos(state.elapsed * 1.8 + agent.phase) * 38;
    const sy = y + Math.sin(state.elapsed * 1.8 + agent.phase) * 26;
    dot(sx, sy, 5, colors.cyan);
    arrow(x - 48, y + 8, x + 52, y - 8, colors.cyan, 2.2, 0.8, -0.08);
    arrow(x + 48, y - 12, x - 44, y + 14, colors.ink, 1.6, 0.58, -0.05);
    const labelX = compact || index !== 0 ? x : x + 82;
    const labelY = compact ? y + (agent.y > 0.50 ? -34 : 34) : (index === 0 ? y - 62 : y + 44);
    text(agent.name, labelX, labelY, compact ? 11 : 13, colors.ink, compact || index !== 0 ? "center" : "left");
  });

  worldSources.forEach((source, index) => {
    const x = source.x * w;
    const y = (1 - source.y) * h;
    const pulse = (p + index * 0.2) % 1;
    const active = !state.storyMode || focusIndex === 1 || focusIndex === 2;
    halo(x, y, 38 + 90 * pulse, "rgb(255,192,103)", (active ? 0.24 : 0.10) * (1 - pulse * 0.45));
    dot(x, y, active ? 7 : 5, colors.amber, active ? 1 : 0.58);
    if (!compact) text("world shock", x, y - 34, 12, colors.amber);
    agents.forEach(agent => {
      const ax = agent.x * w;
      const ay = (1 - agent.y) * h;
      arrow(x, y, ax, ay, colors.amber, 1.5, active ? 0.22 : 0.10, 0.08);
      dot(mix(x, ax, pulse), mix(y, ay, pulse), 4, colors.ink, active ? 0.65 : 0.30);
    });
  });

  const errorActive = !state.storyMode || focusIndex === 3;
  arrow(w * 0.36, h * 0.34, w * 0.61, h * 0.52, colors.violet, 3, (errorActive ? 0.65 : 0.24) + 0.3 * wave(state.elapsed * 2.1), 0.16);
  if (!compact) {
    text("prediction error updates boundary", w * 0.48, h * 0.30, 13, colors.violet);
    text("observed dE", w * 0.67, h * 0.47, 12, colors.ink);
    text("self copy", w * 0.24, h * 0.51, 12, colors.cyan);
  }

  drawStoryCue(step, w * 0.5, h - 96, compact ? w - 24 : Math.min(w * 0.66, 650), "Self, world, observed energy, and residual error are all visible together.");

  const phaseNames = storyPlans.reafference.map(item => item.label);
  updatePhase(state.storyMode ? "reafference story" : "reafference cycle", state.storyMode ? step.label : phaseLabel(phaseNames, p), p);
  updateMetrics([
    { label: "self dE", value: `${Math.round((0.46 + wave(p * Math.PI * 2) * 0.46) * 100)}%`, amount: 0.46 + wave(p * Math.PI * 2) * 0.46, color: colors.cyan },
    { label: "world dE", value: `${Math.round((0.24 + wave(p * Math.PI * 2 + 1.5) * 0.58) * 100)}%`, amount: 0.24 + wave(p * Math.PI * 2 + 1.5) * 0.58, color: colors.amber },
    { label: "prediction error", value: `${Math.round((p > 0.62 ? 0.78 : 0.28) * 100)}%`, amount: p > 0.62 ? 0.78 : 0.28, color: colors.violet },
  ]);
}

function drawSyntax() {
  clearCanvas();
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 10 : 8);
  const { index: focusIndex, step } = storyState("syntax", p);
  const left = w * 0.08;
  const top = h * 0.16;
  const grid = Math.min(w, h) * 0.30;
  const cell = grid / 6;

  roundedRect(left - 18, top - 18, grid + 36, grid + 36, 8, "rgba(246,239,228,0.04)", "rgba(246,239,228,0.20)");
  for (let row = 0; row < 6; row++) {
    for (let col = 0; col < 6; col++) {
      const active = (row === 1 && col > 1 && col < 5) || (col === 2 && row > 1 && row < 5) || (row === 4 && col === 4);
      const concern = active && wave(state.elapsed * 2 + row + col) > 0.34;
      ctx.fillStyle = concern ? colors.amber : active ? "rgba(93,231,239,0.55)" : "rgba(246,239,228,0.08)";
      ctx.fillRect(left + col * cell + 2, top + row * cell + 2, cell - 4, cell - 4);
    }
  }
  text("raw scene", left + grid * 0.5, top - 36, 13, colors.muted);

  const slotX = w * 0.44;
  const slotYs = [h * 0.24, h * 0.39, h * 0.54, h * 0.69];
  slotYs.forEach((y, index) => {
    const amount = clamp((p - index * 0.08) * 1.7, 0, 1);
    const active = storyActive(index === 1 ? 2 : 1, focusIndex);
    roundedRect(slotX - 72, y - 22, 144, 44, 8, active ? "rgba(12,15,24,0.88)" : "rgba(12,15,24,0.62)", index === 1 ? colors.amber : colors.cyan);
    line(slotX - 58, y + 13, slotX - 58 + 116 * amount, y + 13, index === 1 ? colors.amber : colors.cyan, 5, active ? 0.8 : 0.32);
    text(["shape slot", "concern slot", "relation slot", "policy slot"][index], slotX, y - 3, 12, colors.ink);
    arrow(left + grid + 22, top + grid * (0.24 + index * 0.15), slotX - 76, y, index === 1 ? colors.amber : colors.cyan, 1.7, active ? 0.45 : 0.18, 0.08);
  });

  const programX = w * 0.70;
  const programY = h * 0.42;
  const programActive = storyActive(3, focusIndex);
  roundedRect(programX - 88, programY - 90, 176, 180, 8, programActive ? "rgba(181,140,255,0.08)" : "rgba(181,140,255,0.035)", "rgba(181,140,255,0.45)");
  ["if concern", "bind slot", "test cause", "intervene"].forEach((label, index) => {
    const y = programY - 58 + index * 38;
    text(label, programX, y, 12, programActive && index === Math.floor(p * 4) ? colors.violet : colors.muted);
    if (index < 3) line(programX, y + 12, programX, y + 24, colors.violet, 1.2, programActive ? 0.42 : 0.18);
  });

  slotYs.forEach((y, index) => arrow(slotX + 76, y, programX - 92, programY - 50 + index * 32, index === 1 ? colors.amber : colors.cyan, 1.6, programActive ? 0.42 : 0.18, -0.05));
  const targetX = w * 0.88;
  const targetY = h * 0.42;
  const transferActive = storyActive(4, focusIndex);
  arrow(programX + 92, programY, targetX - 32, targetY, colors.green, 3, transferActive ? 0.72 : 0.24, 0.05);
  halo(targetX, targetY, 62 + 20 * wave(state.elapsed * 2.5), "rgb(140,226,169)", transferActive ? 0.20 : 0.08);
  dot(targetX, targetY, transferActive ? 12 : 9, colors.green, transferActive ? 1 : 0.58);
  text("OOD transfer", targetX, targetY + 42, 13, colors.green);
  drawStoryCue(step, w * 0.52, h - 96, Math.min(w * 0.76, 720), "Raw scene, slots, gate, program, and transfer remain visible together.");

  updatePhase(state.storyMode ? "syntax story" : "syntax loop", state.storyMode ? step.label : phaseLabel(storyPlans.syntax.map(item => item.label), p), p);
  updateMetrics([
    { label: "slot confidence", value: `${Math.round((0.42 + 0.50 * ease(p)) * 100)}%`, amount: 0.42 + 0.50 * ease(p), color: colors.cyan },
    { label: "concern gate", value: p > 0.32 && p < 0.78 ? "open" : "testing", amount: p > 0.32 && p < 0.78 ? 0.86 : 0.36, color: colors.amber },
    { label: "transfer signal", value: `${Math.round((p > 0.58 ? 0.80 : 0.28) * 100)}%`, amount: p > 0.58 ? 0.80 : 0.28, color: colors.green },
  ]);
}

function drawBodies() {
  clearCanvas();
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 11 : 9);
  const { index: focusIndex, step } = storyState("bodies", p);
  const modules = [
    { label: "sensor", color: colors.cyan, x: 0.13, y: 0.22, tx: 0.39, ty: 0.30 },
    { label: "memory", color: colors.blue, x: 0.15, y: 0.47, tx: 0.50, ty: 0.28 },
    { label: "policy", color: colors.violet, x: 0.13, y: 0.72, tx: 0.53, ty: 0.55 },
    { label: "actuator", color: colors.amber, x: 0.84, y: 0.72, tx: 0.66, ty: 0.68 },
  ];
  const dock = ease(clamp(p * 1.8, 0, 1));
  const perturb = p > 0.42 && p < 0.66 ? Math.sin(((p - 0.42) / 0.24) * Math.PI) : 0;
  const repair = p > 0.60 ? ease((p - 0.60) / 0.40) : 0;

  roundedRect(w * 0.31, h * 0.18, w * 0.44, h * 0.60, 8, "rgba(246,239,228,0.035)", "rgba(246,239,228,0.20)");
  text("typed architecture body", w * 0.53, h * 0.15, 14, colors.ink);

  modules.forEach(module => {
    const active = storyActive(0, focusIndex) || storyActive(1, focusIndex) || storyActive(4, focusIndex);
    const x = mix(module.x * w, module.tx * w, dock);
    const y = mix(module.y * h, module.ty * h, dock);
    roundedRect(x - 54, y - 24, 108, 48, 8, active ? "rgba(12,15,24,0.88)" : "rgba(12,15,24,0.62)", module.color);
    text(module.label, x, y, 12, colors.ink);
  });

  const bodyPoints = modules.map(module => ({ x: mix(module.x * w, module.tx * w, dock), y: mix(module.y * h, module.ty * h, dock), color: module.color }));
  for (let i = 0; i < bodyPoints.length; i++) {
    const a = bodyPoints[i];
    const b = bodyPoints[(i + 1) % bodyPoints.length];
    const active = storyActive(1, focusIndex) || storyActive(3, focusIndex) || storyActive(4, focusIndex);
    arrow(a.x, a.y, b.x, b.y, repair > 0.45 ? colors.green : colors.faint, 2.1, active ? 0.5 + repair * 0.35 : 0.22, 0.04);
  }

  if (perturb > 0) {
    for (let i = 0; i < 4; i++) {
      const radius = 40 + i * 34 + perturb * 46;
      ctx.save();
      ctx.globalAlpha = (1 - i * 0.18) * (storyActive(2, focusIndex) ? 0.35 : 0.14);
      ctx.strokeStyle = colors.rose;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(w * 0.54, h * 0.46, radius, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
    text("perturbation", w * 0.54, h * 0.44, 13, storyActive(2, focusIndex) ? colors.rose : colors.muted);
  }

  const gateX = w * 0.82;
  const gateY = h * 0.29;
  const gateActive = storyActive(3, focusIndex) || storyActive(4, focusIndex);
  roundedRect(gateX - 72, gateY - 44, 144, 88, 8, gateActive ? "rgba(140,226,169,0.07)" : "rgba(140,226,169,0.035)", "rgba(140,226,169,0.42)");
  text("formal gate", gateX, gateY - 12, 13, colors.green);
  text(repair > 0.45 ? "passes repair" : "checking types", gateX, gateY + 14, 11, repair > 0.45 ? colors.green : colors.muted);
  arrow(w * 0.70, h * 0.50, gateX - 76, gateY, colors.green, 2, gateActive ? 0.52 : 0.18, -0.10);
  arrow(gateX, gateY + 48, w * 0.60, h * 0.70, colors.green, 2.4, gateActive ? repair : repair * 0.35, -0.18);

  const viability = clamp(0.82 - perturb * 0.42 + repair * 0.36, 0, 1);
  roundedRect(w * 0.08, h * 0.84, w * 0.84, 34, 8, "rgba(246,239,228,0.04)", "rgba(246,239,228,0.18)");
  line(w * 0.10, h * 0.84 + 17, w * 0.10 + w * 0.80 * viability, h * 0.84 + 17, viability > 0.70 ? colors.green : colors.amber, 13, 0.9);
  text("viability", w * 0.10, h * 0.81, 13, colors.muted, "left");
  text(`${Math.round(viability * 100)}%`, w * 0.91, h * 0.81, 13, colors.ink, "right");
  drawStoryCue(step, w * 0.5, h * 0.68, Math.min(w * 0.76, 720), "Modules, perturbation, repair, and viability remain visible together.");

  updatePhase(state.storyMode ? "body story" : "body loop", state.storyMode ? step.label : phaseLabel(storyPlans.bodies.map(item => item.label), p), p);
  updateMetrics([
    { label: "viability", value: `${Math.round(viability * 100)}%`, amount: viability, color: colors.green },
    { label: "perturbation load", value: `${Math.round(perturb * 100)}%`, amount: perturb, color: colors.rose },
    { label: "repair closure", value: `${Math.round(repair * 100)}%`, amount: repair, color: colors.amber },
  ]);
}

function drawSymmetry() {
  clearCanvas();
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 10 : 8);
  const { index: focusIndex, step } = storyState("symmetry", p);
  const cx = w * 0.34;
  const cy = h * 0.50;
  const r = Math.min(w, h) * 0.23;
  const angle = p * Math.PI * 2;

  ctx.save();
  ctx.strokeStyle = "rgba(246,239,228,0.18)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
  text("latent symmetry group", cx, cy - r - 30, 13, colors.muted);

  const base = [
    [0.00, 0.72],
    [1.26, 0.62],
    [2.51, 0.86],
    [3.77, 0.54],
    [5.03, 0.80],
  ];
  base.forEach(([a, scale], index) => {
    const trainX = cx + Math.cos(a) * r * scale;
    const trainY = cy + Math.sin(a) * r * scale;
    const testX = cx + Math.cos(a + angle) * r * scale;
    const testY = cy + Math.sin(a + angle) * r * scale;
    const transformActive = storyActive(1, focusIndex) || storyActive(2, focusIndex);
    line(trainX, trainY, testX, testY, colors.faint, 1, transformActive ? 0.28 : 0.12);
    dot(trainX, trainY, 5, colors.cyan, storyActive(0, focusIndex) ? 0.92 : 0.55);
    dot(testX, testY, 4.5, index % 2 ? colors.amber : colors.green, transformActive ? 0.82 : 0.42);
  });

  const ruleX = w * 0.70;
  const weakY = h * 0.34;
  const memY = h * 0.62;
  const weakActive = storyActive(3, focusIndex) || storyActive(2, focusIndex);
  const memActive = !state.storyMode || focusIndex < 3;
  roundedRect(ruleX - 104, weakY - 48, 208, 96, 8, weakActive ? "rgba(140,226,169,0.06)" : "rgba(140,226,169,0.025)", "rgba(140,226,169,0.45)");
  roundedRect(ruleX - 104, memY - 48, 208, 96, 8, memActive ? "rgba(255,143,155,0.05)" : "rgba(255,143,155,0.025)", "rgba(255,143,155,0.42)");
  text("weak compatible rule", ruleX, weakY - 14, 13, colors.green);
  text("preserves transform", ruleX, weakY + 13, 11, colors.muted);
  text("memorizing rule", ruleX, memY - 14, 13, colors.rose);
  text("fits train only", ruleX, memY + 13, 11, colors.muted);

  arrow(cx + r + 24, cy - 42, ruleX - 108, weakY, colors.green, 2.4, weakActive ? 0.72 : 0.24, -0.06);
  arrow(cx + r + 24, cy + 42, ruleX - 108, memY, colors.rose, 2.0, memActive ? 0.46 : 0.18, 0.05);
  const ood = ease(clamp((p - 0.48) / 0.32, 0, 1));
  line(ruleX - 82, weakY + 34, ruleX - 82 + 164 * (0.72 + ood * 0.20), weakY + 34, colors.green, 8, 0.85);
  line(ruleX - 82, memY + 34, ruleX - 82 + 164 * (0.76 - ood * 0.42), memY + 34, colors.rose, 8, 0.85);
  text("OOD gate", ruleX, h * 0.82, 13, colors.amber);
  arrow(ruleX, memY + 60, ruleX, h * 0.79, colors.amber, 2, storyActive(2, focusIndex) ? 0.46 : 0.20, 0.10);
  arrow(ruleX, weakY + 60, ruleX, h * 0.79, colors.green, 2.2, weakActive ? 0.62 : 0.22, -0.10);
  drawStoryCue(step, w * 0.5, h * 0.68, Math.min(w * 0.74, 690), "Training examples, transformed probes, and competing rules remain visible together.");

  updatePhase(state.storyMode ? "symmetry story" : "symmetry loop", state.storyMode ? step.label : phaseLabel(storyPlans.symmetry.map(item => item.label), p), p);
  updateMetrics([
    { label: "invariant preservation", value: `${Math.round((0.70 + ood * 0.22) * 100)}%`, amount: 0.70 + ood * 0.22, color: colors.green },
    { label: "memorizer OOD fit", value: `${Math.round((0.76 - ood * 0.42) * 100)}%`, amount: 0.76 - ood * 0.42, color: colors.rose },
    { label: "symmetry pressure", value: `${Math.round((0.46 + wave(angle) * 0.44) * 100)}%`, amount: 0.46 + wave(angle) * 0.44, color: colors.violet },
  ]);
}

function drawActivation() {
  clearCanvas();
  const w = state.width;
  const h = state.height;
  const p = cycle(state.storyMode ? 9.5 : 7.5);
  const { index: focusIndex, step } = storyState("activation", p);
  const left = w * 0.10;
  const right = w * 0.78;
  const rows = 7;

  for (let i = 0; i < rows; i++) {
    const y = h * (0.18 + i * 0.10);
    const active = Math.max(0, 1 - Math.abs(i - (1.5 + p * 5)) / 2.2);
    const storyAlpha = storyActive(0, focusIndex) || storyActive(1, focusIndex) ? 1 : 0.42;
    line(left, y, right, y, active > 0.35 ? colors.cyan : "rgba(246,239,228,0.16)", 4 + active * 7, (0.35 + active * 0.45) * storyAlpha);
    text(`layer ${i + 1}`, left - 20, y, 11, colors.muted, "right");
    for (let j = 0; j < 10; j++) {
      const x = mix(left + 22, right - 20, j / 9);
      dot(x, y + Math.sin(state.elapsed * 1.1 + j + i) * 8 * active, 2.2 + active * 2.2, active > 0.45 ? colors.cyan : colors.faint, 0.7);
    }
  }

  const probeX = w * 0.45;
  const probeY = h * 0.48;
  const steerX = w * 0.84;
  const steerY = h * 0.34;
  const probeActive = storyActive(1, focusIndex);
  roundedRect(probeX - 82, probeY - 46, 164, 92, 8, probeActive ? "rgba(181,140,255,0.07)" : "rgba(181,140,255,0.035)", "rgba(181,140,255,0.46)");
  text("probe direction", probeX, probeY - 13, 13, colors.violet);
  text("stable across controls", probeX, probeY + 14, 11, colors.muted);
  const steerActive = storyActive(2, focusIndex);
  arrow(probeX + 84, probeY, steerX - 46, steerY, colors.amber, 2.8, steerActive ? 0.68 : 0.26, -0.08);
  roundedRect(steerX - 48, steerY - 42, 96, 84, 8, steerActive ? "rgba(255,192,103,0.08)" : "rgba(255,192,103,0.035)", "rgba(255,192,103,0.48)");
  text("steer", steerX, steerY - 6, 13, colors.amber);
  text("behavior", steerX, steerY + 19, 11, colors.ink);

  const nullX = w * 0.84;
  const nullY = h * 0.68;
  const nullActive = storyActive(3, focusIndex);
  roundedRect(nullX - 58, nullY - 42, 116, 84, 8, nullActive ? "rgba(255,143,155,0.05)" : "rgba(255,143,155,0.025)", "rgba(255,143,155,0.42)");
  text("matched null", nullX, nullY - 8, 13, colors.rose);
  text("should fail", nullX, nullY + 18, 11, colors.muted);
  arrow(probeX + 84, probeY + 18, nullX - 62, nullY, colors.rose, 2, nullActive ? 0.38 : 0.16, 0.10);

  const behaviorProgress = clamp((p - 0.45) / 0.35, 0, 1);
  const behavior = p > 0.45 ? ease(behaviorProgress) : 0.18 + wave(state.elapsed * 1.7) * 0.14;
  const nullScore = 0.22 + wave(state.elapsed * 2.3 + 1.2) * 0.08;
  line(steerX - 30, steerY + 54, steerX - 30 + 62 * behavior, steerY + 54, colors.green, 8, 0.9);
  line(nullX - 35, nullY + 54, nullX - 35 + 70 * nullScore, nullY + 54, colors.rose, 8, 0.85);
  drawStoryCue(step, w * 0.50, h - 96, Math.min(w * 0.76, 720), "Layer state, probe, steering, and matched null stay visible together.");

  updatePhase(state.storyMode ? "activation story" : "activation loop", state.storyMode ? step.label : phaseLabel(storyPlans.activation.map(item => item.label), p), p);
  updateMetrics([
    { label: "probe stability", value: `${Math.round((0.52 + wave(p * Math.PI * 2) * 0.34) * 100)}%`, amount: 0.52 + wave(p * Math.PI * 2) * 0.34, color: colors.violet },
    { label: "behavior shift", value: `${Math.round(behavior * 100)}%`, amount: behavior, color: colors.green },
    { label: "matched null shift", value: `${Math.round(nullScore * 100)}%`, amount: nullScore, color: colors.rose },
  ]);
}

function drawCurrentView() {
  pages[state.route].draw();
}

function scheduleFrame() {
  if (!frameRequest) frameRequest = requestAnimationFrame(frame);
}

function updateMotionControls() {
  pauseButton.disabled = state.reducedMotion;
  pauseButton.textContent = state.reducedMotion ? "reduced motion" : state.paused ? "play" : "pause";
  pauseButton.setAttribute(
    "aria-label",
    state.reducedMotion ? "Animation disabled by reduced motion preference" : state.paused ? "Play animation" : "Pause animation",
  );
}

function updateStoryControls() {
  storyButton.textContent = state.storyMode ? "story on" : "story off";
  storyButton.setAttribute("aria-label", state.storyMode ? "Turn story mode off" : "Turn story mode on");
}

function tourProgress() {
  if (!state.tourMode) return 0;
  return clamp((state.elapsed - state.tourRouteStartedAt) / tourStepSeconds, 0, 1);
}

function updateTourStatus() {
  const index = state.tourMode ? state.tourRouteIndex : routeIndex(state.route);
  const page = pageList[index] || pageList[0];
  let label = `manual · ${page.nav}`;
  if (!state.reducedMotion && state.tourMode) {
    label = `tour ${index + 1}/${pageList.length} · ${page.nav}`;
  }
  tourStatusTextEl.textContent = label;
  tourFillEl.style.width = state.tourMode ? `${tourProgress() * 100}%` : `${((index + 1) / pageList.length) * 100}%`;
  tourFillEl.style.background = page.color;
}

function updateTourControls() {
  if (state.reducedMotion) {
    state.tourMode = false;
    state.tourRouting = false;
    state.tourExpectedRoute = "";
    tourButton.disabled = true;
    tourButton.textContent = "tour disabled";
    tourButton.setAttribute("aria-label", "Reviewer tour disabled by reduced motion preference");
  } else {
    tourButton.disabled = false;
    tourButton.textContent = state.tourMode ? "tour on" : "tour off";
    tourButton.setAttribute("aria-label", state.tourMode ? "Stop reviewer tour" : "Start reviewer tour");
  }
  updateTourStatus();
}

function activateTourRoute(index) {
  const nextIndex = (index + pageList.length) % pageList.length;
  const route = pageList[nextIndex].route;
  state.tourRouteIndex = nextIndex;
  if (routeFromHash() !== route) {
    state.tourRouting = true;
    state.tourExpectedRoute = route;
    window.location.hash = route;
  }
  setRoute(route);
}

function startReviewerTour() {
  if (state.reducedMotion) return;
  state.tourMode = true;
  state.paused = false;
  state.tourRouteIndex = routeIndex(state.route);
  state.tourRouteStartedAt = state.elapsed;
  updateMotionControls();
  updateTourControls();
  activateTourRoute(state.tourRouteIndex);
  state.lastFrame = 0;
  scheduleFrame();
}

function stopReviewerTour() {
  state.tourMode = false;
  state.tourRouting = false;
  state.tourExpectedRoute = "";
  updateTourControls();
}

function advanceReviewerTour() {
  if (!state.tourMode || state.reducedMotion) return;
  let nextIndex = state.tourRouteIndex;
  while (state.elapsed - state.tourRouteStartedAt >= tourStepSeconds) {
    state.tourRouteStartedAt += tourStepSeconds;
    nextIndex = (nextIndex + 1) % pageList.length;
  }
  if (nextIndex !== state.tourRouteIndex) activateTourRoute(nextIndex);
  else updateTourStatus();
}

function frame(now) {
  frameRequest = 0;
  const seconds = now / 1000;
  const delta = state.lastFrame ? seconds - state.lastFrame : 0;
  state.lastFrame = seconds;
  const animating = !state.paused && !state.reducedMotion;
  if (animating) {
    state.elapsed += delta * state.speed;
    advanceReviewerTour();
  }
  drawCurrentView();
  if (animating) scheduleFrame();
}

buildNav();
buildCards();
setRoute(normalizeRoute());
resizeCanvas();
window.addEventListener("resize", resizeCanvas);
window.addEventListener("hashchange", () => {
  const route = normalizeRoute();
  const fromTour = state.tourRouting && route === state.tourExpectedRoute;
  state.tourRouting = false;
  state.tourExpectedRoute = "";
  setRoute(route);
  if (state.tourMode && !fromTour) stopReviewerTour();
  scheduleFrame();
});
pauseButton.addEventListener("click", () => {
  if (state.reducedMotion) return;
  state.paused = !state.paused;
  updateMotionControls();
  state.lastFrame = 0;
  scheduleFrame();
});
tourButton.addEventListener("click", () => {
  if (state.tourMode) stopReviewerTour();
  else startReviewerTour();
  scheduleFrame();
});
labelsButton.addEventListener("click", () => {
  state.showLabels = !state.showLabels;
  labelsButton.textContent = state.showLabels ? "labels on" : "labels off";
  scheduleFrame();
});
storyButton.addEventListener("click", () => {
  state.storyMode = !state.storyMode;
  updateStoryControls();
  scheduleFrame();
});
speedRange.addEventListener("input", () => {
  state.speed = Number(speedRange.value);
});
window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", event => {
  state.reducedMotion = event.matches;
  state.lastFrame = 0;
  updateMotionControls();
  updateTourControls();
  scheduleFrame();
});
updateMotionControls();
updateStoryControls();
updateTourControls();
scheduleFrame();
