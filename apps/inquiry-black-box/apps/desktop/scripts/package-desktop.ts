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

const scriptDir = dirname(fileURLToPath(import.meta.url));
const desktopRoot = join(scriptDir, "..");
const releaseRoot = join(desktopRoot, "release", "mac");
const appName = "Inquiry Black Box";
const bundleId = "com.inquiry.blackbox";
const sourceElectronApp = join(desktopRoot, "node_modules", "electron", "dist", "Electron.app");
const outputApp = join(releaseRoot, `${appName}.app`);
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
writeFileSync(
  join(releaseRoot, "README.md"),
  [
    "# Inquiry Black Box macOS Package",
    "",
    "This is an unsigned local developer package.",
    "Sign and notarize it before sharing outside a trusted local test machine.",
    "",
    "Smoke checklist:",
    "- Launch the app.",
    "- Pair the unpacked or packaged Chrome extension.",
    "- Record, stop, replay, export, delete, restart, and reload the extension.",
  ].join("\n"),
);

console.log(`Packaged ${outputApp}`);

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

function writeInfoPlist(path: string): void {
  const original = readFileSync(path, "utf8");
  const next = original
    .replace(/<key>CFBundleExecutable<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleExecutable</key>\n\t<string>${appName}</string>`)
    .replace(/<key>CFBundleIdentifier<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleIdentifier</key>\n\t<string>${bundleId}</string>`)
    .replace(/<key>CFBundleName<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleName</key>\n\t<string>${appName}</string>`)
    .replace(/<key>CFBundleDisplayName<\/key>\s*<string>[^<]+<\/string>/, `<key>CFBundleDisplayName</key>\n\t<string>${appName}</string>`);
  writeFileSync(path, next);
}
