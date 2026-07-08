import { execFileSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const extensionRoot = join(scriptDir, "..");
const version = "0.1.0";
const releaseRoot = join(extensionRoot, "release", "extension");
const stageDir = join(releaseRoot, "inquiry-black-box-extension");
const zipPath = join(releaseRoot, `inquiry-black-box-extension-${version}.zip`);

rmSync(releaseRoot, { recursive: true, force: true });
mkdirSync(stageDir, { recursive: true });

copyRequired("manifest.json");
copyRequired("popup.html");
copyRequired("dist/background");
copyRequired("dist/content");
copyRequired("dist/popup");
copyRequired("assets");

execFileSync("zip", ["-qr", zipPath, "."], { cwd: stageDir, stdio: "inherit" });
console.log(`Packaged ${zipPath}`);

function copyRequired(relativePath: string): void {
  const source = join(extensionRoot, relativePath);
  if (!existsSync(source)) {
    throw new Error(`Missing extension package input: ${relativePath}`);
  }

  cpSync(source, join(stageDir, relativePath), { recursive: true });
}
