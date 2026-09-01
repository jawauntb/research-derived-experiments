const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const root = path.join(__dirname, "..");
const { canonicalPayload } = require("../fixture.js");
const worldsData = require("../worlds.json");
const receiptsData = require("../receipts.json");
const { publicPaths, server } = require("../server.js");

let origin;
const serverReady = new Promise((resolve) => server.listen(0, "127.0.0.1", () => {
  origin = `http://127.0.0.1:${server.address().port}`;
  server.unref();
  resolve();
}));

function request(pathname, method = "GET") {
  return serverReady.then(() => new Promise((resolve, reject) => {
    const request = http.request({ hostname: "127.0.0.1", port: server.address().port, path: pathname, method }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks).toString("utf8") }));
    });
    request.on("error", reject);
    request.end();
  }));
}

const tests = [];
function it(name, fn) { tests.push({ name, fn }); }

it("has stable SHA-256 canonical digests for every fixture", () => {
    for (const receipt of receiptsData.receipts) {
      const digest = crypto.createHash("sha256").update(canonicalPayload(receipt)).digest("hex");
      assert.match(receipt.canonical_digest, /^[a-f0-9]{64}$/);
      assert.equal(digest, receipt.canonical_digest, receipt.receipt_id);
    }
});

it("keeps every receipt bound to a registered admitted world", () => {
    const worlds = new Map(worldsData.worlds.map((world) => [world.id, world]));
    for (const receipt of receiptsData.receipts) {
      const world = worlds.get(receipt.world_id);
      assert.ok(world, receipt.receipt_id);
      assert.equal(world.state, "ADMITTED", receipt.receipt_id);
      assert.ok(world.receipt_ids.includes(receipt.receipt_id), receipt.receipt_id);
    }
});

it("publishes only reviewed state and reason for non-admitted worlds", () => {
    const allowed = new Set(["id", "title", "short_title", "modality", "state", "version", "version_label", "description", "capability", "scope", "source_contract", "source_clock", "gate_reason", "receipt_ids", "default_receipt"]);
    for (const world of worldsData.worlds.filter((item) => item.state !== "ADMITTED")) {
      assert.deepEqual(world.receipt_ids, [], world.id);
      assert.equal(world.default_receipt, null, world.id);
      assert.equal(world.description, null, world.id);
      assert.equal(world.capability, null, world.id);
      assert.equal(world.scope, null, world.id);
      for (const key of Object.keys(world)) assert.ok(allowed.has(key), `${world.id}.${key}`);
      assert.ok(world.gate_reason, world.id);
    }
});

it("represents all four outcome states in the admitted trial fixture", () => {
    const outcomes = new Set(receiptsData.receipts.filter((receipt) => receipt.world_id === "clinical_trials_sec").map((receipt) => receipt.outcome));
    assert.deepEqual(outcomes, new Set(["ACCEPTED", "REJECTED", "INCONCLUSIVE", "CHECKER_ERROR"]));
});

it("serves only the explicit GET/HEAD allowlist with restrictive headers", async () => {
    for (const pathname of ["/", "/index.html", "/styles.css", "/app.js", "/fixture.js", "/worlds.json", "/receipts.json", "/assets/mark.svg", "/assets/checkpoint.svg"]) {
      const response = await request(pathname);
      assert.equal(response.status, 200, pathname);
    }
    assert.deepEqual([...publicPaths].sort(), ["app.js", "assets/checkpoint.svg", "assets/mark.svg", "fixture.js", "index.html", "receipts.json", "styles.css", "worlds.json"].sort());
    const response = await request("/");
    assert.match(response.headers["content-security-policy"], /default-src 'none'/);
    assert.match(response.headers["content-security-policy"], /script-src 'self'/);
    assert.equal(response.headers["cache-control"], "no-cache, max-age=0");
    assert.equal(response.headers["x-content-type-options"], "nosniff");
    assert.equal(response.headers["referrer-policy"], "no-referrer");
});

it("handles HEAD without a body and rejects methods, traversal, and unknown files", async () => {
    const head = await request("/index.html", "HEAD");
    assert.equal(head.status, 200);
    assert.equal(head.body, "");
    assert.equal((await request("/index.html", "POST")).status, 405);
    assert.notEqual((await request("/%2e%2e/%2e%2e/etc/passwd")).status, 200);
    assert.notEqual((await request("/%2e%2e/server.js")).status, 200);
    assert.equal((await request("/not-public.txt")).status, 404);
    assert.equal((await request("/%E0%A4%A")).status, 400);
});

it("contains no secrets or person-level Apollo data", () => {
    const sourceFiles = ["index.html", "styles.css", "app.js", "fixture.js", "worlds.json", "receipts.json", "server.js", "railway.json"];
    const source = sourceFiles.map((file) => fs.readFileSync(path.join(root, file), "utf8")).join("\n");
    assert.doesNotMatch(source, /(?:sk|rk|pk)-[A-Za-z0-9_-]{16,}/i);
    assert.doesNotMatch(source, /(?:authorization|bearer|api[_ -]?key)\s*[:=]\s*["'][^"']+/i);
    assert.doesNotMatch(source, /\+?\d{1,3}[-.\s]\(?\d{3}\)?[-.\s]\d{4}/);
    assert.doesNotMatch(source, /linkedin\.com\/(?:in|company)\//i);
    assert.doesNotMatch(source, /apollo[_ -]?(?:id|contact|person|organization)/i);
    const emails = source.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || [];
    assert.deepEqual([...new Set(emails)], ["jawaun.brown95@gmail.com"]);
});

it("renders source-controlled strings through text nodes, not HTML execution", () => {
    const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
    assert.doesNotMatch(app, /\.innerHTML\s*=|insertAdjacentHTML|document\.write|eval\s*\(|new Function/);
    assert.match(app, /textContent/);
    assert.match(app, /createTextNode/);
    const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
    assert.doesNotMatch(html, /on(?:error|load|click)\s*=/i);
    assert.doesNotMatch(html, /javascript:/i);
});

it("has a no-JavaScript default receipt and pilot path", () => {
    const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
    assert.match(html, /<noscript>[\s\S]*Clinical Trials \/ SEC[\s\S]*ACCEPTED[\s\S]*mailto:jawaun\.brown95@gmail\.com/);
    assert.match(html, /mailto:jawaun\.brown95@gmail\.com\?subject=Bio%20Claim%20Firewall%20design%20partner/);
    assert.match(html, /<script src="fixture\.js" defer><\/script>/);
    assert.match(html, /<script src="app\.js" defer><\/script>/);
});

it("updates the claim type when switching evidence worlds", () => {
    const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
    assert.match(app, /open_targets:\s*"TARGET_DISEASE_ASSOCIATION"/);
    assert.match(app, /arc_vcc:\s*"PERTURBATION_DIRECTION"/);
    assert.match(app, /getElementById\("claim-type"\)\.textContent = claimType/);
});

(async () => {
  let failures = 0;
  for (const test of tests) {
    try {
      await test.fn();
      console.log(`ok - ${test.name}`);
    } catch (error) {
      failures += 1;
      console.error(`not ok - ${test.name}`);
      console.error(error.stack || error);
    }
  }
  if (failures) process.exitCode = 1;
})();
