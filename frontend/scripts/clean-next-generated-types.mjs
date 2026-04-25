import { readdir, rm } from "node:fs/promises";
import path from "node:path";

const duplicateTypeFilePattern = / \d+\.tsx?$/;
const generatedTypeDirs = [
  path.join(".next", "types"),
  path.join(".next", "dev", "types"),
];

for (const dir of generatedTypeDirs) {
  await removeDuplicateTypeFiles(dir);
}

async function removeDuplicateTypeFiles(dir) {
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }

  await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await removeDuplicateTypeFiles(entryPath);
        return;
      }
      if (entry.isFile() && duplicateTypeFilePattern.test(entry.name)) {
        await rm(entryPath, { force: true });
      }
    }),
  );
}
