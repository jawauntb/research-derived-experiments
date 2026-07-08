const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { test } = require("bun:test");

const siteRoot = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(siteRoot, "index.html"), "utf8");
const css = fs.readFileSync(path.join(siteRoot, "styles.css"), "utf8");

test("site explains Inquiry without overstating privacy or cognition", () => {
  assert.match(html, /Chrome extension and desktop app/);
  assert.match(html, /Local SQLite/);
  assert.match(html, /Optional redacted jobs/);
  assert.match(html, /no diagnostic mind-reading claims/i);
  assert.match(html, /no cloud upload unless explicitly enabled/i);
  assert.doesNotMatch(html, /medical diagnosis/i);
  assert.doesNotMatch(html, /always-on background monitoring/i);
});

test("site keeps Neurophenom typography and adds neumorphic tokens", () => {
  assert.match(css, /Iowan Old Style/);
  assert.match(css, /SF Mono/);
  assert.match(css, /--shadow-raised/);
  assert.match(css, /--shadow-inset/);
  assert.match(css, /border-radius: 22px/);
});
