const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const childProcess = require("node:child_process");
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
    assert.deepEqual(
      new Set(worldsData.worlds.filter((world) => world.state === "ADMITTED").map((world) => world.id)),
      new Set(["clinical-trials-sec", "open-targets", "arc-vcc"]),
    );
    for (const receipt of receiptsData.receipts) {
      const world = worlds.get(receipt.world_id);
      assert.ok(world, receipt.receipt_id);
      assert.equal(world.state, "ADMITTED", receipt.receipt_id);
      assert.ok(world.receipt_ids.includes(receipt.receipt_id), receipt.receipt_id);
    }
});

it("is generated from the passing readiness artifact and is not stale", () => {
    assert.equal(worldsData.generated_from, "bio-claim-firewall/experiments/evidence_worlds/results/pilot_readiness.json");
    assert.equal(receiptsData.generated_from, worldsData.generated_from);
    const result = childProcess.spawnSync("python3", [path.join(root, "export_real_receipts.py"), "--check"], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr || result.stdout);
});

it("publishes real admitted identifiers without demo placeholders", () => {
    const serialized = JSON.stringify({ worldsData, receiptsData });
    for (const expected of ["NCT06260774", "ENSG00000141510", "MONDO_0018875", "STAT1", "TAGLN"]) assert.match(serialized, new RegExp(expected));
    assert.doesNotMatch(serialized, /NCT00000001|GENE_A|GENE_B|fixture:\/\/|demo-2026/i);
    for (const receipt of receiptsData.receipts) {
      assert.match(receipt.engine_receipt_id, /^[a-f0-9]{64}$/);
      if (receipt.outcome === "CHECKER_ERROR") {
        assert.equal(receipt.world_digest, null);
        assert.match(receipt.selected_world_context_digest, /^[a-f0-9]{64}$/);
      } else {
        assert.match(receipt.world_digest, /^[a-f0-9]{64}$/);
        assert.equal(receipt.selected_world_context_digest, undefined);
      }
    }
});

it("keeps source hashes, evidence citations, and world identities consistent", () => {
    const expectedSources = {
      "clinical-trials-sec": new Set(["clinicaltrials-gov-api-v2", "sec-edgar-submissions-and-archives"]),
      "open-targets": new Set(["open-targets-graphql-26-06"]),
      "arc-vcc": new Set(["arc-cell-eval2-h1-vcc-real-subset", "arc-vcc-derived-ledger"]),
    };
    for (const receipt of receiptsData.receipts) {
      if (receipt.outcome === "CHECKER_ERROR") {
        assert.deepEqual(receipt.source_hashes, {});
        continue;
      }
      assert.deepEqual(new Set(Object.keys(receipt.source_hashes)), expectedSources[receipt.world_id]);
      for (const citation of receipt.citations) {
        assert.ok(citation.engine_id, receipt.receipt_id);
        assert.ok(citation.reference.startsWith("https://"), receipt.receipt_id);
        const evidence = JSON.stringify(receipt.evidence || {});
        assert.match(evidence, new RegExp(citation.engine_id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
      }
    }
});

it("does not inject positive evidence into unresolved or corrupt outcomes", () => {
    for (const receipt of receiptsData.receipts.filter((item) => ["INCONCLUSIVE", "CHECKER_ERROR"].includes(item.outcome))) {
      assert.deepEqual(receipt.citations, [], receipt.receipt_id);
      assert.equal(receipt.source_reference, null, receipt.receipt_id);
      assert.match(receipt.scope, /^No evidence scope was established/, receipt.receipt_id);
      assert.equal(receipt.evidence, null, receipt.receipt_id);
    }
    for (const receipt of receiptsData.receipts.filter((item) => item.world_id === "arc-vcc")) {
      assert.deepEqual(receipt.citations, [], receipt.receipt_id);
      assert.match(receipt.source_reference.label, /does not issue citation IDs/);
    }
});

it("publishes only reviewed state and reason for non-admitted worlds", () => {
    const allowed = new Set(["id", "presentation_id", "title", "short_title", "modality", "state", "version", "world_digest", "version_label", "description", "capability", "scope", "source_contract", "source_clock", "gate_reason", "receipt_ids", "default_receipt"]);
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
    const outcomes = new Set(receiptsData.receipts.filter((receipt) => receipt.world_id === "clinical-trials-sec").map((receipt) => receipt.outcome));
    assert.deepEqual(outcomes, new Set(["ACCEPTED", "REJECTED", "INCONCLUSIVE", "CHECKER_ERROR"]));
    for (const receipt of receiptsData.receipts.filter((item) => item.world_id === "clinical-trials-sec")) {
      assert.equal(receipt.checker_version, "clinical-trials-sec/0.2.0", receipt.receipt_id);
    }
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

    const defaultWorld = worldsData.worlds.find((world) => world.id === "clinical-trials-sec");
    const defaultReceipt = receiptsData.receipts.find((receipt) => receipt.receipt_id === defaultWorld.default_receipt);
    assert.match(html, new RegExp(`world digest: ${defaultReceipt.world_digest}`));

    const noScript = html.match(/<noscript>([\s\S]*?)<\/noscript>/)?.[1] || "";
    for (const world of worldsData.worlds.filter((item) => item.state !== "ADMITTED")) {
      const publicState = world.state.includes("DEFERRED") ? "DEFERRED" : "WITHHELD";
      const escapedTitle = world.title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      assert.match(html, new RegExp(`<span class="state-badge">${publicState}</span></div><h3>${escapedTitle}</h3>`), world.id);
      assert.match(noScript, new RegExp(`${escapedTitle}[\\s\\S]*${publicState}`, "i"), world.id);
    }
});

it("updates the claim type when switching evidence worlds", () => {
    const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
    assert.match(app, /"open-targets":\s*"TARGET_DISEASE_ASSOCIATION"/);
    assert.match(app, /"arc-vcc":\s*"PERTURBATION_DIRECTION"/);
    assert.match(app, /getElementById\("claim-type"\)\.textContent = claimType/);
});

it("describes the static digest as bundle consistency, not authenticity", () => {
    const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
    const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
    assert.match(app, /bundle consistent/);
    assert.match(app, /bundle mismatch/);
    assert.match(html, /bundle consistent/);
    assert.doesNotMatch(`${app}\n${html}`, /digest verified|authentic/i);
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
