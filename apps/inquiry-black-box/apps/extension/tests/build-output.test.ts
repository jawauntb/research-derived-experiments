import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, test } from "bun:test";

describe("extension build output", () => {
  test("builds the content script as a classic content script", () => {
    const extensionRoot = join(import.meta.dir, "..");

    execFileSync("bun", ["run", "build"], {
      cwd: extensionRoot,
      stdio: "pipe",
    });

    const contentScript = readFileSync(join(extensionRoot, "dist/content/index.js"), "utf8");

    expect(contentScript).toContain("installContentScript();");
    expect(contentScript).not.toMatch(/^\\s*(import|export)\\s/m);
  });

  test("packages a reviewable MV3 zip with runtime assets only", () => {
    const extensionRoot = join(import.meta.dir, "..");

    execFileSync("bun", ["run", "package"], {
      cwd: extensionRoot,
      stdio: "pipe",
    });

    const zipPath = join(extensionRoot, "release", "extension", "inquiry-black-box-extension-0.1.0.zip");
    const listing = execFileSync("unzip", ["-l", zipPath], { encoding: "utf8" });

    expect(existsSync(zipPath)).toBe(true);
    expect(listing).toContain("manifest.json");
    expect(listing).toContain("popup.html");
    expect(listing).toContain("dist/background/service-worker.js");
    expect(listing).toContain("dist/content/index.js");
    expect(listing).toContain("dist/popup/App.js");
    expect(listing).toContain("assets/icon16.png");
    expect(listing).toContain("assets/icon32.png");
    expect(listing).toContain("assets/icon48.png");
    expect(listing).toContain("assets/icon128.png");
    expect(listing).not.toContain("assets/icon.svg");
    expect(listing).not.toContain("tests/");
  });
});
