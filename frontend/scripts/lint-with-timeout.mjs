import { spawn } from "node:child_process";
import path from "node:path";

const DEFAULT_TIMEOUT_MS = 45_000;
const configuredTimeoutMs = Number.parseInt(
  process.env.ESLINT_CHUNK_TIMEOUT_MS ?? String(DEFAULT_TIMEOUT_MS),
  10,
);
const timeoutMs =
  Number.isFinite(configuredTimeoutMs) && configuredTimeoutMs > 0
    ? configuredTimeoutMs
    : DEFAULT_TIMEOUT_MS;
const eslintBin = path.join(
  "node_modules",
  ".bin",
  process.platform === "win32" ? "eslint.cmd" : "eslint",
);

const defaultChunks = [
  { label: "app", args: ["app"] },
  { label: "features/library", args: ["features/library"] },
  { label: "features/workspace", args: ["features/workspace"] },
  {
    label: "features/debug + model queue",
    args: ["features/debug", "features/model-queue"],
  },
  { label: "lib", args: ["lib"] },
  { label: "scripts + eslint config", args: ["scripts", "eslint.config.mjs"] },
];

const extraArgs = process.argv.slice(2);
const hasExplicitTargets = includesExplicitTargets(extraArgs);
const chunks = hasExplicitTargets
  ? [{ label: "custom", args: extraArgs }]
  : defaultChunks.map((chunk) => ({ ...chunk, args: [...chunk.args, ...extraArgs] }));

for (const chunk of chunks) {
  await runLintChunk(chunk);
}

async function runLintChunk(chunk) {
  console.log(`\n[lint] ${chunk.label}`);

  const child = spawn(eslintBin, chunk.args, {
    stdio: "inherit",
    detached: process.platform !== "win32",
  });

  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    console.error(
      `\n[lint] Timed out after ${timeoutMs}ms while running: eslint ${chunk.args.join(" ")}`,
    );
    console.error(
      "[lint] Increase ESLINT_CHUNK_TIMEOUT_MS only after checking why this chunk hangs.",
    );
    stopChild(child, "SIGTERM");
    setTimeout(() => stopChild(child, "SIGKILL"), 2_000).unref();
  }, timeoutMs);

  const { code, signal } = await waitForExit(child);
  clearTimeout(timeout);

  if (timedOut) {
    process.exitCode = 124;
    process.exit(124);
  }

  if (code !== 0) {
    process.exitCode = code ?? 1;
    process.exit(process.exitCode);
  }

  if (signal) {
    process.exitCode = 1;
    process.exit(1);
  }
}

function waitForExit(child) {
  return new Promise((resolve, reject) => {
    child.on("error", reject);
    child.on("exit", (code, signal) => resolve({ code, signal }));
  });
}

function stopChild(child, signal) {
  if (child.exitCode !== null || child.killed) {
    return;
  }
  try {
    if (process.platform !== "win32") {
      process.kill(-child.pid, signal);
      return;
    }
    child.kill(signal);
  } catch {
    child.kill(signal);
  }
}

function includesExplicitTargets(args) {
  const optionsWithValues = new Set([
    "--cache-location",
    "--config",
    "--env",
    "--ext",
    "--format",
    "--global",
    "--ignore-pattern",
    "--max-warnings",
    "--output-file",
    "--parser",
    "--plugin",
    "--resolve-plugins-relative-to",
    "--rule",
    "-c",
    "-f",
    "-o",
  ]);

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--") {
      return index < args.length - 1;
    }
    if (optionsWithValues.has(arg)) {
      index += 1;
      continue;
    }
    if (arg.startsWith("-")) {
      continue;
    }
    return true;
  }
  return false;
}
