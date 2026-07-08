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
    const entries = listing
      .split("\n")
      .map((line) => line.trim().match(/^\d+\s+\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}\s+(.+)$/)?.[1])
      .filter((entry): entry is string => Boolean(entry));

    expect(existsSync(zipPath)).toBe(true);
    expect(entries).toContain("manifest.json");
    expect(entries).toContain("popup.html");
    expect(entries).toContain("dist/background/service-worker.js");
    expect(entries).toContain("dist/content/index.js");
    expect(entries).toContain("dist/popup/App.js");
    expect(entries).toContain("assets/icon16.png");
    expect(entries).toContain("assets/icon32.png");
    expect(entries).toContain("assets/icon48.png");
    expect(entries).toContain("assets/icon128.png");
    expect(entries).not.toContain("assets/icon.svg");
    expect(entries.some((entry) => entry.startsWith("tests/"))).toBe(false);
  });
});
