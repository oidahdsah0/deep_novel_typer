import { cp, readdir, readFile, rm, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(scriptDir, "..");
const nextDir = path.join(frontendDir, ".next");
const serverDir = path.join(nextDir, "server");
const appRouteDir = path.join(serverDir, "app");
const appRouteBackupDir = path.join(frontendDir, ".next-novel-backup", "server-app");
const appPathsManifestPath = path.join(serverDir, "app-paths-manifest.json");
const ssrChunkDir = path.join(serverDir, "chunks", "ssr");

const failures = [
  ...(await verifyAppPageEntries()),
  ...(await verifySsrChunks()),
];

if (failures.length > 0) {
  console.error("[build] Next production build is incomplete:");
  for (const failure of failures) {
    console.error(`  - ${failure}`);
  }
  console.error("[build] Remove .next and rebuild before starting production.");
  process.exit(1);
}

await backupAppRouteFiles();

console.log("[build] Verified Next production route manifests.");

async function verifyAppPageEntries() {
  const failures = [];
  const manifest = await readJson(appPathsManifestPath);

  for (const [routeKey, pageFile] of Object.entries(manifest)) {
    if (!routeKey.endsWith("/page")) {
      continue;
    }

    const entryPath = path.join(serverDir, pageFile);
    if (!(await fileExists(entryPath))) {
      failures.push(`${routeKey} is registered but ${relative(entryPath)} is missing`);
    }

    const clientManifestPath = clientReferenceManifestPath(pageFile);
    if (!(await fileExists(clientManifestPath))) {
      failures.push(
        `${routeKey} is missing ${relative(clientManifestPath)}`,
      );
    }
  }

  return failures;
}

async function verifySsrChunks() {
  const failures = [];
  const mapFiles = await listFiles(ssrChunkDir, (filePath) => filePath.endsWith(".js.map"));

  for (const mapFile of mapFiles) {
    const chunkFile = mapFile.slice(0, -".map".length);
    if (!(await fileExists(chunkFile))) {
      failures.push(`${relative(chunkFile)} is missing for ${relative(mapFile)}`);
    }
  }

  return failures;
}

function clientReferenceManifestPath(pageFile) {
  const withoutExtension = pageFile.slice(0, -".js".length);
  return path.join(serverDir, `${withoutExtension}_client-reference-manifest.js`);
}

async function backupAppRouteFiles() {
  await rm(appRouteBackupDir, { force: true, recursive: true });
  await cp(appRouteDir, appRouteBackupDir, { recursive: true });
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

async function fileExists(filePath) {
  try {
    const result = await stat(filePath);
    return result.isFile();
  } catch {
    return false;
  }
}

async function listFiles(dir, predicate) {
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return [];
  }

  const files = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        return listFiles(entryPath, predicate);
      }
      if (entry.isFile() && predicate(entryPath)) {
        return [entryPath];
      }
      return [];
    }),
  );

  return files.flat();
}

function relative(filePath) {
  return path.relative(frontendDir, filePath);
}
