const assert = require("node:assert/strict");
const http = require("node:http");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const { test } = require("node:test");

const rootUrl = "http://127.0.0.1:4567";

async function startServer() {
  const server = spawn(process.execPath, ["server.js"], {
    cwd: __dirname + "/..",
    env: { ...process.env, PORT: "4567" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const [chunk] = await once(server.stdout, "data");
  assert.match(String(chunk), /research mechanism atlas listening/);
  return server;
}

async function request(pathname, options = {}) {
  return fetch(`${rootUrl}${pathname}`, { redirect: "manual", ...options });
}

function rawRequest(pathname) {
  return new Promise((resolve, reject) => {
    const request = http.request({ host: "127.0.0.1", port: 4567, path: pathname }, response => {
      response.resume();
      response.on("end", () => resolve(response));
    });
    request.on("error", reject);
    request.end();
  });
}

test("static server serves expected cache headers and methods", async () => {
  const server = await startServer();
  try {
    const index = await request("/");
    assert.equal(index.status, 200);
    assert.equal(index.headers.get("content-type"), "text/html; charset=utf-8");
    assert.equal(index.headers.get("cache-control"), "no-cache, max-age=0");
    assert.match(await index.text(), /Research Mechanism Atlas/);

    const app = await request("/app.js?v=atlas-8", { method: "HEAD" });
    assert.equal(app.status, 200);
    assert.equal(app.headers.get("content-type"), "text/javascript; charset=utf-8");
    assert.equal(app.headers.get("cache-control"), "public, max-age=300");

    const styles = await request("/styles.css?v=atlas-8");
    assert.equal(styles.status, 200);
    assert.equal(styles.headers.get("content-type"), "text/css; charset=utf-8");
    assert.equal(styles.headers.get("cache-control"), "public, max-age=300");

    const rejected = await request("/", { method: "POST" });
    assert.equal(rejected.status, 405);
    assert.equal(rejected.headers.get("allow"), "GET, HEAD");
  } finally {
    server.kill();
  }
});

test("static server keeps traversal outside the public root", async () => {
  const server = await startServer();
  try {
    for (const pathname of ["/../package.json", "/%2e%2e/package.json", "/..%2fpackage.json"]) {
      const response = await rawRequest(pathname);
      assert.equal(response.statusCode, 403, pathname);
    }
  } finally {
    server.kill();
  }
});
