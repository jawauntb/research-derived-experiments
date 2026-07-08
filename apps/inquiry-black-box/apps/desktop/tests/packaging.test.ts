import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, test } from "bun:test";

describe("desktop packaging configuration", () => {
  test("defines a local unsigned macOS package path with identity metadata", () => {
    const desktopRoot = join(import.meta.dir, "..");
    const packageJson = JSON.parse(readFileSync(join(desktopRoot, "package.json"), "utf8")) as {
      scripts?: Record<string, string>;
    };
    const packageScript = readFileSync(join(desktopRoot, "scripts", "package-desktop.ts"), "utf8");
    const entitlements = readFileSync(join(desktopRoot, "packaging", "mac", "entitlements.plist"), "utf8");
    const icon = readFileSync(join(desktopRoot, "assets", "icon.svg"), "utf8");

    expect(packageJson.scripts?.["package:mac"]).toContain("scripts/package-desktop.ts");
    expect(packageScript).toContain("com.inquiry.blackbox");
    expect(packageScript).toContain("`${appName}.app`");
    expect(packageScript).toContain("dist/main/electron.js");
    expect(entitlements).toContain("com.apple.security.device.camera");
    expect(entitlements).toContain("com.apple.security.network.server");
    expect(icon).toContain("<svg");
  });
});
