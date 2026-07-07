import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const textExtensions = new Set([".ts", ".tsx", ".json", ".md", ".py", ".toml", ".sql"]);
const privacyGuardExtensions = new Set([".ts", ".tsx", ".py", ".sql"]);
const forbidden = [
  {
    pattern: /raw[_-]?keystroke/i,
    message: "Use aggregate typing metrics, not raw keystroke storage.",
  },
  {
    pattern: /saveFrame|persistFrame|storeFrame/i,
    message: "Raw camera frames must not be persisted in the default flow.",
  },
  {
    pattern: /OPENAI_API_KEY\s*=/,
    message: "Secrets belong in Doppler/provider environments, not source files.",
  },
];

function extension(path: string): string {
  const dot = path.lastIndexOf(".");
  return dot === -1 ? "" : path.slice(dot);
}

function walk(dir: string, files: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === ".git" || entry === "dist" || entry === "build") {
      continue;
    }

    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      walk(full, files);
    } else if (textExtensions.has(extension(full))) {
      files.push(full);
    }
  }

  return files;
}

const failures: string[] = [];

for (const file of walk(root)) {
  const text = readFileSync(file, "utf8");
  const rel = relative(root, file);

  if (/\t/.test(text)) {
    failures.push(`${rel}: contains a tab character`);
  }

  for (const rule of forbidden) {
    if (privacyGuardExtensions.has(extension(file)) && rule.pattern.test(text) && !rel.endsWith("scripts/lint.ts")) {
      failures.push(`${rel}: ${rule.message}`);
    }
  }
}

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log("inquiry-black-box lint passed");
