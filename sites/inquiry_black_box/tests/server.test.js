const assert = require("node:assert/strict");
const http = require("node:http");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const { test } = require("bun:test");

const rootUrl = "http://127.0.0.1:4571";

async function startServer() {
  const server = spawn(process.execPath, ["server.js"], {
    cwd: `${__dirname}/..`,
    env: { ...process.env, PORT: "4571" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const [chunk] = await once(server.stdout, "data");
  assert.match(String(chunk), /inquiry black box site listening/);
  return server;
}

async function request(pathname, options = {}) {
  return fetch(`${rootUrl}${pathname}`, { redirect: "manual", ...options });
}

function rawRequest(pathname) {
  return new Promise((resolve, reject) => {
    const request = http.request({ host: "127.0.0.1", port: 4571, path: pathname }, response => {
      response.resume();
      response.on("end", () => resolve(response));
    });
    request.on("error", reject);
    request.end();
  });
}

test("static server serves the Inquiry site and assets", async () => {
  const server = await startServer();
  try {
    const index = await request("/");
    assert.equal(index.status, 200);
    assert.equal(index.headers.get("content-type"), "text/html; charset=utf-8");
    assert.equal(index.headers.get("cache-control"), "no-cache, max-age=0");
    const html = await index.text();
    assert.match(html, /Inquiry Black Box/);
    assert.match(html, /local-first session replay/i);

    const styles = await request("/styles.css");
    assert.equal(styles.status, 200);
    assert.equal(styles.headers.get("content-type"), "text/css; charset=utf-8");
    assert.match(await styles.text(), /--shadow-raised/);

    const icon = await request("/assets/aperture-icon.png", { method: "HEAD" });
    assert.equal(icon.status, 200);
    assert.equal(icon.headers.get("content-type"), "image/png");

    const mark = await request("/assets/aperture-mark.png", { method: "HEAD" });
    assert.equal(mark.status, 200);
    assert.equal(mark.headers.get("content-type"), "image/png");

    const rejected = await request("/", { method: "POST" });
    assert.equal(rejected.status, 405);
    assert.equal(rejected.headers.get("allow"), "GET, HEAD");
  } finally {
    server.kill();
  }
});

test("static server keeps traversal outside the site root", async () => {
  const server = await startServer();
  try {
    const literalTraversal = await rawRequest("/../package.json");
    assert.ok([403, 404].includes(literalTraversal.statusCode), "/../package.json");

    for (const pathname of ["/%2e%2e/package.json", "/..%2fpackage.json"]) {
      const response = await rawRequest(pathname);
      assert.ok([403, 404].includes(response.statusCode), pathname);
    }

    const privateFile = await rawRequest("/package.json");
    assert.equal(privateFile.statusCode, 404);
  } finally {
    server.kill();
  }
});
