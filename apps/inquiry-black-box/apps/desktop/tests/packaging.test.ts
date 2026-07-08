import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "bun:test";
import {
  appName,
  installDesktopApp,
  parseInstallArgs,
  resolveInstallDestination,
} from "../scripts/install-desktop";
import { writeInfoPlist } from "../scripts/package-desktop";

describe("desktop packaging configuration", () => {
  test("defines a local unsigned macOS package path with identity metadata", () => {
    const desktopRoot = join(import.meta.dir, "..");
    const workspaceRoot = join(desktopRoot, "..", "..");
    const packageJson = JSON.parse(readFileSync(join(desktopRoot, "package.json"), "utf8")) as {
      scripts?: Record<string, string>;
    };
    const workspacePackageJson = JSON.parse(readFileSync(join(workspaceRoot, "package.json"), "utf8")) as {
      scripts?: Record<string, string>;
    };
    const packageScript = readFileSync(join(desktopRoot, "scripts", "package-desktop.ts"), "utf8");
    const installScript = readFileSync(join(desktopRoot, "scripts", "install-desktop.ts"), "utf8");
    const entitlements = readFileSync(join(desktopRoot, "packaging", "mac", "entitlements.plist"), "utf8");
    const icon = readFileSync(join(desktopRoot, "assets", "icon.svg"), "utf8");

    expect(packageJson.scripts?.["package:mac"]).toContain("scripts/package-desktop.ts");
    expect(packageJson.scripts?.["install:mac"]).toContain("scripts/install-desktop.ts");
    expect(workspacePackageJson.scripts?.["install:desktop"]).toContain("apps/desktop install:mac");
    expect(packageScript).toContain("com.inquiry.blackbox");
    expect(packageScript).toContain("`${appName}.app`");
    expect(packageScript).toContain("dist/main/electron.js");
    expect(packageScript).toContain("NSCameraUsageDescription");
    expect(packageScript).toContain("NSAppleEventsUsageDescription");
    expect(entitlements).toContain("com.apple.security.device.camera");
    expect(entitlements).toContain("com.apple.security.network.server");
    expect(entitlements).not.toContain("screen-capture");
    expect(entitlements).not.toContain("com.apple.security.device.audio-input");
    expect(packageScript).not.toContain("ScreenCaptureKit");
    expect(installScript).toContain("Run bun run package:desktop first");
    expect(icon).toContain("<svg");
  });

  test("resolves install targets without defaulting to system Applications", () => {
    expect(resolveInstallDestination()).toBe(join(homedir(), "Applications", `${appName}.app`));
    expect(resolveInstallDestination({ target: "user" })).toBe(join(homedir(), "Applications", `${appName}.app`));
    expect(resolveInstallDestination({ target: "system" })).toBe(join("/Applications", `${appName}.app`));
    expect(resolveInstallDestination({ destination: "/tmp/inquiry-apps" })).toBe(
      join("/tmp/inquiry-apps", `${appName}.app`),
    );
    expect(resolveInstallDestination({ destination: "/tmp/Custom.app" })).toBe("/tmp/Custom.app");
    expect(parseInstallArgs(["--target", "system", "--overwrite"])).toMatchObject({
      target: "system",
      overwrite: true,
    });
  });

  test("refuses missing packages and requires explicit overwrite", async () => {
    const tmpRoot = mkdtempSync(join(tmpdir(), "inquiry-install-"));
    try {
      const source = join(tmpRoot, "Source.app");
      const destinationDir = join(tmpRoot, "Applications");
      const destination = join(destinationDir, `${appName}.app`);
      mkdirSync(join(source, "Contents"), { recursive: true });
      writeFileSync(join(source, "Contents", "marker.txt"), "packaged");
      writeFileSync(join(source, "Contents", "Info.plist"), "<plist><dict></dict></plist>");
      mkdirSync(join(destination, "Contents"), { recursive: true });
      writeFileSync(join(destination, "Contents", "marker.txt"), "old");
      writeFileSync(join(destination, "Contents", "Info.plist"), "<plist><dict></dict></plist>");

      await expect(
        installDesktopApp({ source: join(tmpRoot, "Missing.app"), destination: destinationDir }),
      ).rejects.toThrow(/Run bun run package:desktop first/);
      await expect(installDesktopApp({ source, destination: destinationDir })).rejects.toThrow(/Refusing to overwrite/);

      const result = await installDesktopApp({ source, destination: destinationDir, overwrite: true });

      expect(result).toMatchObject({ source, destination, overwritten: true });
      expect(existsSync(join(destination, "Contents", "marker.txt"))).toBe(true);
      expect(readFileSync(join(destination, "Contents", "marker.txt"), "utf8")).toBe("packaged");
    } finally {
      rmSync(tmpRoot, { recursive: true, force: true });
    }
  });

  test("rewrites Info.plist identity and usage descriptions idempotently", () => {
    const tmpRoot = mkdtempSync(join(tmpdir(), "inquiry-plist-"));
    try {
      const plistPath = join(tmpRoot, "Info.plist");
      writeFileSync(
        plistPath,
        [
          "<plist>",
          "<dict>",
          "<key>CFBundleExecutable</key>",
          "<string>Electron</string>",
          "<key>CFBundleIdentifier</key>",
          "<string>com.github.Electron</string>",
          "<key>CFBundleName</key>",
          "<string>Electron</string>",
          "<key>CFBundleDisplayName</key>",
          "<string>Electron</string>",
          "</dict>",
          "</plist>",
        ].join("\n"),
      );

      writeInfoPlist(plistPath);
      writeInfoPlist(plistPath);
      const plist = readFileSync(plistPath, "utf8");

      expect(plist).toContain("<string>Inquiry Black Box</string>");
      expect(plist).toContain("<string>com.inquiry.blackbox</string>");
      expect(plist.match(/NSCameraUsageDescription/g)).toHaveLength(1);
      expect(plist.match(/NSAppleEventsUsageDescription/g)).toHaveLength(1);
      expect(plist).not.toContain("ScreenCaptureKit");
    } finally {
      rmSync(tmpRoot, { recursive: true, force: true });
    }
  });

  test("rejects invalid app bundles and refuses self-overwrite", async () => {
    const tmpRoot = mkdtempSync(join(tmpdir(), "inquiry-install-invalid-"));
    try {
      const invalidSource = join(tmpRoot, "Invalid.app");
      const source = join(tmpRoot, "Source.app");
      mkdirSync(invalidSource, { recursive: true });
      mkdirSync(join(source, "Contents"), { recursive: true });
      writeFileSync(join(source, "Contents", "Info.plist"), "<plist><dict></dict></plist>");

      await expect(installDesktopApp({ source: invalidSource, destination: join(tmpRoot, "Applications") })).rejects.toThrow(
        /App bundle is invalid/,
      );
      await expect(installDesktopApp({ source, destination: source, overwrite: true })).rejects.toThrow(/over itself/);
    } finally {
      rmSync(tmpRoot, { recursive: true, force: true });
    }
  });
});
