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
import { ensureProtocolScheme, signMacApp, writeInfoPlist } from "../scripts/package-desktop";

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
    const iconPng = readFileSync(join(desktopRoot, "assets", "icon.png"));
    const iconIcns = readFileSync(join(desktopRoot, "assets", "icon.icns"));
    const storeSmallTile = readFileSync(join(workspaceRoot, "assets", "store", "chrome-store-small-tile.png"));
    const storeMarquee = readFileSync(join(workspaceRoot, "assets", "store", "chrome-store-marquee.png"));
    const storeScreenshot = readFileSync(join(workspaceRoot, "assets", "store", "chrome-store-screenshot.png"));

    expect(packageJson.scripts?.["package:mac"]).toContain("scripts/package-desktop.ts");
    expect(packageJson.scripts?.["install:mac"]).toContain("scripts/install-desktop.ts");
    expect(workspacePackageJson.scripts?.["install:desktop"]).toContain("apps/desktop install:mac");
    expect(packageScript).toContain("com.inquiry.blackbox");
    expect(packageScript).toContain("`${appName}.app`");
    expect(packageScript).toContain("dist/main/electron.js");
    expect(packageScript).toContain("CFBundleIconFile");
    expect(packageScript).toContain("icon.icns");
    expect(packageScript).toContain("NSCameraUsageDescription");
    expect(packageScript).toContain("NSAppleEventsUsageDescription");
    expect(packageScript).toContain("CFBundleURLTypes");
    expect(packageScript).toContain("inquiry-black-box");
    expect(packageScript).toContain("INQUIRY_MAC_CODESIGN_IDENTITY");
    expect(packageScript).toContain("codesign");
    expect(entitlements).toContain("com.apple.security.device.camera");
    expect(entitlements).toContain("com.apple.security.network.server");
    expect(entitlements).not.toContain("screen-capture");
    expect(entitlements).not.toContain("com.apple.security.device.audio-input");
    expect(packageScript).not.toContain("ScreenCaptureKit");
    expect(installScript).toContain("Run bun run package:desktop first");
    expect([...iconPng.subarray(0, 8)]).toEqual([137, 80, 78, 71, 13, 10, 26, 10]);
    expect(iconIcns.subarray(0, 4).toString("ascii")).toBe("icns");
    expect(pngDimensions(storeSmallTile)).toEqual({ width: 440, height: 280 });
    expect(pngDimensions(storeMarquee)).toEqual({ width: 1280, height: 800 });
    expect(pngDimensions(storeScreenshot)).toEqual({ width: 1280, height: 800 });
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
          "<key>CFBundleIconFile</key>",
          "<string>electron.icns</string>",
          "</dict>",
          "</plist>",
        ].join("\n"),
      );

      writeInfoPlist(plistPath);
      writeInfoPlist(plistPath);
      const plist = readFileSync(plistPath, "utf8");

      expect(plist).toContain("<string>Inquiry Black Box</string>");
      expect(plist).toContain("<string>com.inquiry.blackbox</string>");
      expect(plist).toContain("<string>icon.icns</string>");
      expect(plist).not.toContain("electron.icns");
      expect(plist.match(/CFBundleIconFile/g)).toHaveLength(1);
      expect(plist.match(/CFBundleURLTypes/g)).toHaveLength(1);
      expect(plist).toContain("<string>inquiry-black-box</string>");
      expect(plist.match(/NSCameraUsageDescription/g)).toHaveLength(1);
      expect(plist.match(/NSAppleEventsUsageDescription/g)).toHaveLength(1);
      expect(plist).not.toContain("ScreenCaptureKit");
    } finally {
      rmSync(tmpRoot, { recursive: true, force: true });
    }
  });

  test("keeps protocol scheme insertion and signing fallback deterministic", () => {
    const plist = ensureProtocolScheme("<plist><dict></dict></plist>");
    expect(plist).toContain("<key>CFBundleURLTypes</key>");
    expect(ensureProtocolScheme(plist).match(/CFBundleURLTypes/g)).toHaveLength(1);
    const nestedPlist = ensureProtocolScheme(
      [
        "<plist>",
        "<dict>",
        "<key>ElectronAsarIntegrity</key>",
        "<dict>",
        "<key>Resources/default_app.asar</key>",
        "<dict>",
        "<key>hash</key>",
        "<string>fixture</string>",
        "</dict>",
        "</dict>",
        "</dict>",
        "</plist>",
      ].join("\n"),
    );
    expect(nestedPlist.indexOf("<key>CFBundleURLTypes</key>")).toBeGreaterThan(nestedPlist.indexOf("</dict>\n</dict>"));
    expect(nestedPlist).toContain("<key>ElectronAsarIntegrity</key>");
    expect(signMacApp("/tmp/Inquiry Black Box.app", { env: {}, platform: "darwin" })).toEqual({
      status: "skipped",
      reason: "INQUIRY_MAC_CODESIGN_IDENTITY is not set",
    });
    expect(
      signMacApp("/tmp/Inquiry Black Box.app", {
        env: { INQUIRY_MAC_CODESIGN_IDENTITY: "Developer ID Application: Inquiry" },
        platform: "linux",
      }),
    ).toEqual({
      status: "skipped",
      reason: "codesign is available only on macOS",
    });
  });

  test("runs codesign with the expected arguments and degrades unless strict signing is requested", () => {
    const calls: Array<{ file: string; args: string[]; cwd: string }> = [];
    const signed = signMacApp("/tmp/Inquiry Black Box.app", {
      env: { INQUIRY_MAC_CODESIGN_IDENTITY: "Developer ID Application: Inquiry" },
      platform: "darwin",
      execFileSync: (file, args, options) => {
        calls.push({ file, args, cwd: options.cwd });
      },
    });

    expect(signed).toEqual({ status: "signed", identity: "Developer ID Application: Inquiry" });
    expect(calls[0]).toMatchObject({
      file: "codesign",
      args: [
        "--force",
        "--deep",
        "--options",
        "runtime",
        "--entitlements",
        expect.stringContaining("entitlements.plist"),
        "--sign",
        "Developer ID Application: Inquiry",
        "/tmp/Inquiry Black Box.app",
      ],
    });

    const skipped = signMacApp("/tmp/Inquiry Black Box.app", {
      env: { INQUIRY_MAC_CODESIGN_IDENTITY: "Developer ID Application: Inquiry" },
      platform: "darwin",
      execFileSync: () => {
        throw new Error("keychain locked");
      },
    });
    expect(skipped).toEqual({ status: "skipped", reason: "codesign failed: keychain locked" });

    expect(() =>
      signMacApp("/tmp/Inquiry Black Box.app", {
        env: {
          INQUIRY_MAC_CODESIGN_IDENTITY: "Developer ID Application: Inquiry",
          INQUIRY_MAC_CODESIGN_STRICT: "1",
        },
        platform: "darwin",
        execFileSync: () => {
          throw new Error("keychain locked");
        },
      }),
    ).toThrow("keychain locked");
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

function pngDimensions(buffer: Buffer): { width: number; height: number } {
  expect([...buffer.subarray(0, 8)]).toEqual([137, 80, 78, 71, 13, 10, 26, 10]);
  return {
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20),
  };
}
