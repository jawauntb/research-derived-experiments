import { execFileSync } from "node:child_process";
import {
  chmodSync,
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { INQUIRY_DEEP_LINK_PROTOCOL } from "../src/main/deepLink";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const desktopRoot = join(scriptDir, "..");
const releaseRoot = join(desktopRoot, "release", "mac");
const appName = "Inquiry Black Box";
const bundleId = "com.inquiry.blackbox";
const sourceElectronApp = join(desktopRoot, "node_modules", "electron", "dist", "Electron.app");
const outputApp = join(releaseRoot, `${appName}.app`);
const bundleIcon = join(desktopRoot, "assets", "icon.icns");
const entitlementsPath = join(desktopRoot, "packaging", "mac", "entitlements.plist");

export type PackageDesktopResult = {
  appPath: string;
  bundleId: string;
  signing: SigningResult;
};

export type SigningResult =
  | {
      status: "signed";
      identity: string;
    }
  | {
      status: "skipped";
      reason: string;
    };

type ExecFileSyncLike = (
  file: string,
  args: string[],
  options: {
    cwd: string;
    stdio: "inherit";
  },
) => unknown;

export type SigningDependencies = {
  env?: NodeJS.ProcessEnv;
  platform?: NodeJS.Platform;
  execFileSync?: ExecFileSyncLike;
};

export function packageDesktopApp(): PackageDesktopResult {
  const resourcesDir = join(outputApp, "Contents", "Resources");
  const appResourcesDir = join(resourcesDir, "app");

  ensureElectronRuntime();
  rmSync(outputApp, { recursive: true, force: true });
  mkdirSync(releaseRoot, { recursive: true });
  cpSync(sourceElectronApp, outputApp, { recursive: true });

  const defaultExecutable = join(outputApp, "Contents", "MacOS", "Electron");
  const renamedExecutable = join(outputApp, "Contents", "MacOS", appName);
  if (existsSync(defaultExecutable)) {
    rmSync(renamedExecutable, { force: true });
    cpSync(defaultExecutable, renamedExecutable);
    chmodSync(renamedExecutable, 0o755);
  }

  writeInfoPlist(join(outputApp, "Contents", "Info.plist"));
  cpSync(bundleIcon, join(resourcesDir, "icon.icns"));
  rmSync(appResourcesDir, { recursive: true, force: true });
  mkdirSync(appResourcesDir, { recursive: true });
  cpSync(join(desktopRoot, "dist"), join(appResourcesDir, "dist"), { recursive: true });
  cpSync(join(desktopRoot, "assets"), join(appResourcesDir, "assets"), { recursive: true });
  writeFileSync(
    join(appResourcesDir, "package.json"),
    JSON.stringify(
      {
        name: "@inquiry/desktop-packaged",
        version: "0.1.0",
        type: "module",
        main: "dist/main/electron.js",
      },
      null,
      2,
    ),
  );
  const signing = signMacApp(outputApp);
  writeFileSync(
    join(releaseRoot, "README.md"),
    [
      "# Inquiry Black Box macOS Package",
      "",
      signing.status === "signed"
        ? `This package was signed with ${signing.identity}.`
        : `This is an unsigned local developer package: ${signing.reason}`,
      "Notarize signed release archives before sharing outside a trusted local test machine.",
      "",
      "Smoke checklist:",
      "- Launch the app.",
      `- Confirm ${INQUIRY_DEEP_LINK_PROTOCOL}://pair opens or focuses the desktop app.`,
      "- Pair the unpacked or packaged Chrome extension.",
      "- Record, stop, replay, export, delete, restart, and reload the extension.",
    ].join("\n"),
  );

  return { appPath: outputApp, bundleId, signing };
}

function ensureElectronRuntime(): void {
  if (existsSync(sourceElectronApp)) {
    return;
  }

  const installScript = join(desktopRoot, "node_modules", "electron", "install.js");
  if (!existsSync(installScript)) {
    throw new Error("Electron dependency is missing. Run bun install from apps/inquiry-black-box.");
  }

  execFileSync("bun", [installScript], { cwd: desktopRoot, stdio: "inherit" });
  if (!existsSync(sourceElectronApp)) {
    throw new Error("Electron runtime download did not produce dist/Electron.app.");
  }
}

export function writeInfoPlist(path: string): void {
  const original = readFileSync(path, "utf8");
  const next = original
    .replace(/<key>CFBundleExecutable<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleExecutable</key>\n\t<string>${appName}</string>`)
    .replace(/<key>CFBundleIdentifier<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleIdentifier</key>\n\t<string>${bundleId}</string>`)
    .replace(/<key>CFBundleName<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleName</key>\n\t<string>${appName}</string>`)
    .replace(/<key>CFBundleDisplayName<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleDisplayName</key>\n\t<string>${appName}</string>`)
    .replace(/<key>CFBundleIconFile<\/key>\s*<string>[^<]+<\/string>/, "<key>CFBundleIconFile</key>\n\t<string>icon.icns</string>");
  const withUsageDescriptions = ensurePlistString(
    ensurePlistString(
      ensurePlistString(next, "CFBundleIconFile", "icon.icns"),
      "NSCameraUsageDescription",
      "Inquiry Black Box can derive local camera feature windows when you explicitly enable camera features.",
    ),
    "NSAppleEventsUsageDescription",
    "Inquiry Black Box can read the foreground app name and optional focused-window title when desktop activity is enabled.",
  );
  writeFileSync(path, ensureProtocolScheme(withUsageDescriptions));
}

export function ensurePlistString(plist: string, key: string, value: string): string {
  if (plist.includes(`<key>${key}</key>`)) {
    return plist;
  }

  return insertTopLevelPlistEntry(plist, `\t<key>${key}</key>\n\t<string>${value}</string>`);
}

export function ensureProtocolScheme(plist: string): string {
  if (plist.includes("<key>CFBundleURLTypes</key>")) {
    return plist;
  }

  return insertTopLevelPlistEntry(
    plist,
    [
      "\t<key>CFBundleURLTypes</key>",
      "\t<array>",
      "\t\t<dict>",
      "\t\t\t<key>CFBundleURLName</key>",
      `\t\t\t<string>${bundleId}</string>`,
      "\t\t\t<key>CFBundleURLSchemes</key>",
      "\t\t\t<array>",
      `\t\t\t\t<string>${INQUIRY_DEEP_LINK_PROTOCOL}</string>`,
      "\t\t\t</array>",
      "\t\t</dict>",
      "\t</array>",
    ].join("\n"),
  );
}

function insertTopLevelPlistEntry(plist: string, entry: string): string {
  return plist.replace(/<\/dict>\s*<\/plist>\s*$/u, `${entry}\n</dict>\n</plist>`);
}

export function signMacApp(appPath: string, dependencies: SigningDependencies = {}): SigningResult {
  const env = dependencies.env ?? process.env;
  const platform = dependencies.platform ?? process.platform;
  const run = dependencies.execFileSync ?? execFileSync;
  const identity = env.INQUIRY_MAC_CODESIGN_IDENTITY ?? env.INQUIRY_MAC_DEVELOPER_ID;
  if (!identity) {
    return { status: "skipped", reason: "INQUIRY_MAC_CODESIGN_IDENTITY is not set" };
  }
  if (platform !== "darwin") {
    return { status: "skipped", reason: "codesign is available only on macOS" };
  }

  try {
    run(
      "codesign",
      [
        "--force",
        "--deep",
        "--options",
        "runtime",
        "--entitlements",
        entitlementsPath,
        "--sign",
        identity,
        appPath,
      ],
      { cwd: desktopRoot, stdio: "inherit" },
    );
  } catch (error) {
    if (env.INQUIRY_MAC_CODESIGN_STRICT === "1") {
      throw error;
    }

    return { status: "skipped", reason: `codesign failed: ${errorMessage(error)}` };
  }

  return { status: "signed", identity };
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

if (import.meta.main) {
  const result = packageDesktopApp();
  console.log(`Packaged ${result.appPath} (${result.signing.status})`);
}
