import { execFileSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, renameSync, rmSync } from "node:fs";
import { homedir } from "node:os";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const desktopRoot = join(scriptDir, "..");
export const appName = "Inquiry Black Box";
export const defaultPackagedApp = join(desktopRoot, "release", "mac", `${appName}.app`);

export type InstallTarget = "user" | "system";

export type InstallDesktopOptions = {
  source?: string;
  target?: InstallTarget;
  destination?: string;
  overwrite?: boolean;
  confirmOverwrite?: (destination: string) => Promise<boolean>;
};

export type InstallDesktopResult = {
  source: string;
  destination: string;
  overwritten: boolean;
};

export function resolveInstallDestination(options: Pick<InstallDesktopOptions, "target" | "destination"> = {}): string {
  if (options.destination) {
    const resolved = isAbsolute(options.destination) ? options.destination : resolve(process.cwd(), options.destination);
    return resolved.endsWith(".app") ? resolved : join(resolved, `${appName}.app`);
  }

  if (options.target === "system") {
    return join("/Applications", `${appName}.app`);
  }

  return join(homedir(), "Applications", `${appName}.app`);
}

export async function installDesktopApp(options: InstallDesktopOptions = {}): Promise<InstallDesktopResult> {
  const source = resolve(options.source ?? defaultPackagedApp);
  const destination = resolveInstallDestination(options);
  validateAppBundle(source, `Packaged app is missing: ${source}. Run bun run package:desktop first.`);
  if (source === resolve(destination)) {
    throw new Error("Refusing to install app over itself");
  }

  const destinationParent = dirname(destination);
  mkdirSync(destinationParent, { recursive: true });
  const tempDestination = join(destinationParent, `.${basename(destination, ".app")}.${process.pid}.${Date.now()}.tmp.app`);
  const backupDestination = join(destinationParent, `.${basename(destination)}.${process.pid}.${Date.now()}.backup`);
  rmSync(tempDestination, { recursive: true, force: true });
  rmSync(backupDestination, { recursive: true, force: true });

  if (!existsSync(source)) {
    throw new Error(`Packaged app is missing: ${source}. Run bun run package:desktop first.`);
  }

  const destinationExists = existsSync(destination);
  if (destinationExists) {
    const confirmed = options.overwrite || (options.confirmOverwrite ? await options.confirmOverwrite(destination) : false);
    if (!confirmed) {
      throw new Error(`Refusing to overwrite existing app without confirmation: ${destination}`);
    }
  }

  try {
    copyAppBundle(source, tempDestination);
    validateAppBundle(tempDestination, `Copied app bundle is invalid: ${tempDestination}`);
    if (destinationExists) {
      renameSync(destination, backupDestination);
    }
    renameSync(tempDestination, destination);
    rmSync(backupDestination, { recursive: true, force: true });
  } catch (error) {
    rmSync(tempDestination, { recursive: true, force: true });
    if (destinationExists && existsSync(backupDestination) && !existsSync(destination)) {
      renameSync(backupDestination, destination);
    }
    throw error;
  } finally {
    rmSync(tempDestination, { recursive: true, force: true });
    rmSync(backupDestination, { recursive: true, force: true });
  }

  return {
    source,
    destination,
    overwritten: destinationExists,
  };
}

export function parseInstallArgs(args: string[]): InstallDesktopOptions {
  const options: InstallDesktopOptions = {};
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--target") {
      const value = args[index + 1];
      if (value !== "user" && value !== "system") {
        throw new Error("--target must be user or system");
      }
      options.target = value;
      index += 1;
      continue;
    }
    if (arg === "--destination") {
      const value = args[index + 1];
      if (!value) {
        throw new Error("--destination requires a path");
      }
      options.destination = value;
      index += 1;
      continue;
    }
    if (arg === "--source") {
      const value = args[index + 1];
      if (!value) {
        throw new Error("--source requires a path");
      }
      options.source = value;
      index += 1;
      continue;
    }
    if (arg === "--overwrite") {
      options.overwrite = true;
      continue;
    }
    throw new Error(`Unknown install option: ${arg}`);
  }

  return options;
}

if (import.meta.main) {
  const options = parseInstallArgs(process.argv.slice(2));
  const result = await installDesktopApp({
    ...options,
    confirmOverwrite: confirmOverwritePrompt,
  });
  console.log(`Installed ${result.destination}`);
  console.log("Open it manually to smoke permissions and pairing.");
}

function copyAppBundle(source: string, destination: string): void {
  if (process.platform === "darwin") {
    execFileSync("ditto", [source, destination], { stdio: "inherit" });
    return;
  }

  cpSync(source, destination, { recursive: true });
}

function validateAppBundle(path: string, missingMessage: string): void {
  if (!existsSync(path)) {
    throw new Error(missingMessage);
  }
  if (!path.endsWith(".app") || !existsSync(join(path, "Contents", "Info.plist"))) {
    throw new Error(`App bundle is invalid: ${path}`);
  }
}

async function confirmOverwritePrompt(destination: string): Promise<boolean> {
  if (!process.stdin.isTTY) {
    return false;
  }

  const readline = createInterface({ input, output });
  try {
    const answer = await readline.question(`Overwrite ${destination}? [y/N] `);
    return answer.trim().toLowerCase() === "y";
  } finally {
    readline.close();
  }
}
