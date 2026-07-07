import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
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
});
