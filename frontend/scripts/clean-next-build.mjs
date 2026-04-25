import { rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(scriptDir, "..");
const buildDir = path.join(frontendDir, ".next");
const buildBackupDir = path.join(frontendDir, ".next-novel-backup");
const tsBuildInfo = path.join(frontendDir, "tsconfig.tsbuildinfo");

await rm(buildDir, { force: true, recursive: true });
await rm(buildBackupDir, { force: true, recursive: true });
await rm(tsBuildInfo, { force: true });

console.log("[build] Cleaned frontend production build artifacts.");
