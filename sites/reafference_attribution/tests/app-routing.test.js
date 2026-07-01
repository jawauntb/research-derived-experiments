const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const siteRoot = path.join(__dirname, "..");
const appSource = fs.readFileSync(path.join(siteRoot, "app.js"), "utf8");
const routes = ["overview", "phase2", "reafference", "syntax", "bodies", "symmetry", "activation", "findings", "verification"];
const routeLabels = {
  overview: "program",
  phase2: "phase 2",
  reafference: "reafference",
  syntax: "syntax",
  bodies: "bodies",
  symmetry: "symmetry",
  activation: "activation",
  findings: "findings",
  verification: "verification",
};

class Element {
  constructor(tagName, document) {
    this.tagName = tagName.toUpperCase();
    this.document = document;
    this.children = [];
    this.attributes = new Map();
    this.dataset = {};
    this.listeners = {};
    this.style = {};
    this.textContent = "";
    this.className = "";
    this.id = "";
    this.type = "";
    this.href = "";
    this.value = "";
    this.parentElement = null;
  }

  append(...children) {
    for (const child of children) {
      child.parentElement = this;
      this.children.push(child);
    }
  }

  replaceChildren(...children) {
    this.children = [];
    this.append(...children);
  }

  addEventListener(type, handler) {
    this.listeners[type] = handler;
  }

  click() {
    this.listeners.click?.();
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
    if (name === "aria-current") this.ariaCurrent = String(value);
  }

  removeAttribute(name) {
    this.attributes.delete(name);
    if (name === "aria-current") delete this.ariaCurrent;
  }

  getBoundingClientRect() {
    return { width: this.rectWidth || 960, height: this.rectHeight || 600 };
  }

  matches(selector) {
    if (selector === "[data-route]") return Boolean(this.dataset.route);
    if (selector === ".nav-item") return this.className === "nav-item";
    if (selector === ".experiment-card") return this.className === "experiment-card";
    if (selector === ".metric") return this.className === "metric";
    if (selector === ".metric-value") return this.className === "metric-value";
    return false;
  }

  querySelectorAll(selector) {
    const results = [];
    const visit = element => {
      if (element.matches(selector)) results.push(element);
      for (const child of element.children) visit(child);
    };
    visit(this);
    return results;
  }
}

class Document {
  constructor() {
    this.elementsById = new Map();
    this.root = new Element("html", this);
    this.documentElement = { style: {}, scrollWidth: 960 };
  }

  createElement(tagName) {
    return new Element(tagName, this);
  }

  getElementById(id) {
    return this.elementsById.get(id);
  }

  querySelector(selector) {
    if (selector === ".nav") return this.nav;
    if (selector === ".experiment-card[aria-current='page'] strong") {
      const card = this.cards.children.find(child => child.ariaCurrent === "page");
      return card?.children[0] || null;
    }
    if (selector === ".nav-item[aria-current='page']") {
      return this.nav.children.find(child => child.ariaCurrent === "page") || null;
    }
    if (selector === "h1") return this.getElementById("view-title");
    return null;
  }

  querySelectorAll(selector) {
    return this.root.querySelectorAll(selector);
  }
}

function makeContext(options = {}) {
  const document = new Document();
  const ids = [
    "view-title",
    "view-kicker",
    "view-subtitle",
    "mechanism-thesis",
    "metric-list",
    "motion-list",
    "source-links",
    "phase-label",
    "phase-value",
    "phase-fill",
    "experiment-cards",
    "pause-button",
    "tour-button",
    "story-button",
    "labels-button",
    "speed-range",
    "tour-status-text",
    "tour-fill",
  ];

  const body = new Element("body", document);
  document.root.append(body);

  const nav = new Element("nav", document);
  nav.className = "nav";
  document.nav = nav;
  body.append(nav);

  const stage = new Element("div", document);
  stage.className = "visual-stage";
  stage.rectWidth = options.stageWidth || 960;
  stage.rectHeight = options.stageHeight || 600;
  const canvas = new Element("canvas", document);
  canvas.id = "atlas-canvas";
  canvas.parentElement = stage;
  const drawnText = [];
  canvas.getContext = () => ({
    arc() {},
    beginPath() {},
    closePath() {},
    createRadialGradient: () => ({ addColorStop() {} }),
    fill() {},
    fillRect() {},
    fillText(label) {
      drawnText.push(String(label));
    },
    lineTo() {},
    measureText: text => ({ width: String(text).length * 8 }),
    moveTo() {},
    quadraticCurveTo() {},
    restore() {},
    rotate() {},
    roundRect() {},
    save() {},
    setLineDash() {},
    setTransform() {},
    stroke() {},
    strokeText() {},
    translate() {},
  });
  document.elementsById.set(canvas.id, canvas);
  stage.append(canvas);
  body.append(stage);

  for (const id of ids) {
    const element = new Element(id === "motion-list" ? "ul" : "div", document);
    element.id = id;
    document.elementsById.set(id, element);
    if (id === "experiment-cards") document.cards = element;
    body.append(element);
  }

  document.getElementById("speed-range").value = "1";

  const listeners = {};
  const window = {
    devicePixelRatio: 1,
    innerWidth: 960,
    location: { hash: "" },
    addEventListener(type, handler) {
      listeners[type] = handler;
    },
    matchMedia: () => ({ matches: Boolean(options.reducedMotion), addEventListener() {} }),
  };

  const context = {
    document,
    getComputedStyle: () => ({ getPropertyValue: () => "" }),
    Math,
    requestAnimationFrame: handler => {
      context.lastFrame = handler;
      return 1;
    },
    window,
    drawnText,
  };
  vm.createContext(context);
  vm.runInContext(appSource, context, { filename: "app.js" });
  context.fireHash = hash => {
    window.location.hash = hash;
    listeners.hashchange();
    context.lastFrame?.(1200);
  };
  return context;
}

test("atlas routes, cards, and inherited-key hashes stay in sync", () => {
  const context = makeContext();
  const { document } = context;

  assert.equal(document.nav.children.length, routes.length);
  assert.equal(document.cards.children.length, routes.length);

  for (const route of routes) {
    context.fireHash(`#${route}`);
    assert.equal(document.querySelector(".nav-item[aria-current='page']").textContent, routeLabels[route]);
    assert.equal(document.querySelector(".experiment-card[aria-current='page'] strong").textContent, routeLabels[route]);
    assert.ok(document.getElementById("view-title").textContent.length > 0);
    assert.equal(document.querySelectorAll(".metric").length, 3);
    for (const value of document.querySelectorAll(".metric-value").map(node => node.textContent)) {
      const percent = Number(value.replace("%", ""));
      if (!Number.isNaN(percent)) assert.ok(percent >= 0 && percent <= 100, `${route}: ${value}`);
    }
  }

  for (const badHash of ["#missing", "#constructor", "#toString", "#__proto__"]) {
    context.fireHash(badHash);
    assert.equal(context.window.location.hash, "overview");
    assert.equal(document.querySelector(".nav-item[aria-current='page']").textContent, "program");
    assert.match(document.getElementById("view-title").textContent, /living map/);
  }
});

test("combined program view exposes corpus and frontier context", () => {
  const context = makeContext();
  const { document } = context;
  context.fireHash("#overview");
  const metricValues = document.querySelectorAll(".metric-value").map(node => node.textContent);
  assert.deepEqual(metricValues, ["34 papers", "117 reports", "kept visible"]);
  assert.match(document.getElementById("mechanism-thesis").textContent, /34 papers and 117 public result notes/);
});

test("phase 2 guide exposes story contract and controls", () => {
  const context = makeContext();
  const { document } = context;
  context.fireHash("#phase2");
  const metricValues = document.querySelectorAll(".metric-value").map(node => node.textContent);
  assert.deepEqual(metricValues, ["1.000 recovery", "1.000 pass", "frontier"]);
  assert.match(document.getElementById("view-title").textContent, /phase 2: pixels to bodies/);
  assert.match(document.getElementById("mechanism-thesis").textContent, /removes algorithmic connected components/);
  assert.ok(context.drawnText.includes("story follows learned slots -> profiles -> transfer"));
  assert.ok(context.drawnText.includes("1.000 recovery"));

  const storyButton = document.getElementById("story-button");
  assert.equal(storyButton.textContent, "story on");
  storyButton.click();
  assert.equal(storyButton.textContent, "story off");
  assert.equal(storyButton.attributes.get("aria-label"), "Turn story mode on");
});

test("story mode changes every visualization route", () => {
  const expectations = {
    overview: "weakness",
    reafference: "efference copy",
    syntax: "raw scene",
    bodies: "typed modules",
    symmetry: "train tie",
    activation: "read state",
  };

  for (const [route, storyCue] of Object.entries(expectations)) {
    const context = makeContext();
    const { document } = context;
    context.drawnText.length = 0;
    context.fireHash(`#${route}`);
    assert.ok(context.drawnText.includes(storyCue), `${route} should draw its story cue`);

    document.getElementById("story-button").click();
    context.drawnText.length = 0;
    context.lastFrame?.(2400);
    assert.ok(context.drawnText.includes("map mode"), `${route} should draw map mode after story is off`);
  }
});

test("reviewer tour advances routes and manual navigation stops it", () => {
  const context = makeContext();
  const { document, window } = context;
  const tourButton = document.getElementById("tour-button");
  const tourStatus = document.getElementById("tour-status-text");
  const tourFill = document.getElementById("tour-fill");

  assert.equal(tourButton.textContent, "tour off");
  assert.equal(tourStatus.textContent, "manual · program");

  tourButton.click();
  assert.equal(tourButton.textContent, "tour on");
  assert.equal(tourStatus.textContent, "tour 1/9 · program");

  context.lastFrame?.(1000);
  context.lastFrame?.(11500);
  assert.equal(document.querySelector(".nav-item[aria-current='page']").textContent, "phase 2");
  assert.equal(tourStatus.textContent, "tour 2/9 · phase 2");
  assert.equal(window.location.hash, "phase2");
  assert.equal(tourFill.style.width, "0%");

  context.fireHash("#syntax");
  assert.equal(tourButton.textContent, "tour off");
  assert.equal(tourStatus.textContent, "manual · syntax");
  assert.equal(document.querySelector(".nav-item[aria-current='page']").textContent, "syntax");
});

test("clicking generated cards updates the route", () => {
  const context = makeContext();
  const { document, window } = context;

  for (const card of document.cards.children) {
    card.click();
    assert.equal(window.location.hash, card.dataset.route);
  }
});

test("narrow stages use measured canvas size without overflow", () => {
  for (const width of [320, 375, 390]) {
    const context = makeContext({ stageWidth: width, stageHeight: 500 });
    const canvas = context.document.getElementById("atlas-canvas");
    assert.equal(canvas.style.width, `${width}px`);
    assert.equal(canvas.width, width);
  }
});

test("narrow reafference canvas suppresses dense annotation labels", () => {
  const compact = makeContext({ stageWidth: 390, stageHeight: 430 });
  compact.drawnText.length = 0;
  compact.fireHash("#reafference");
  assert.ok(compact.drawnText.includes("agent A"));
  assert.ok(!compact.drawnText.includes("world shock"));
  assert.ok(!compact.drawnText.includes("prediction error updates boundary"));
  assert.ok(!compact.drawnText.includes("observed dE"));
  assert.ok(!compact.drawnText.includes("self copy"));

  const desktop = makeContext({ stageWidth: 960, stageHeight: 600 });
  desktop.drawnText.length = 0;
  desktop.fireHash("#reafference");
  assert.ok(desktop.drawnText.includes("world shock"));
  assert.ok(desktop.drawnText.includes("prediction error updates boundary"));
  assert.ok(desktop.drawnText.includes("observed dE"));
  assert.ok(desktop.drawnText.includes("self copy"));
});

test("reduced motion renders once with truthful controls", () => {
  const context = makeContext({ reducedMotion: true });
  const pause = context.document.getElementById("pause-button");
  const tour = context.document.getElementById("tour-button");
  assert.equal(pause.disabled, true);
  assert.equal(pause.textContent, "reduced motion");
  assert.equal(pause.attributes.get("aria-label"), "Animation disabled by reduced motion preference");
  assert.equal(tour.disabled, true);
  assert.equal(tour.textContent, "tour disabled");
  assert.equal(tour.attributes.get("aria-label"), "Reviewer tour disabled by reduced motion preference");
});
