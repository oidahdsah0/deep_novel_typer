import { rm } from "node:fs/promises";
import { resolve } from "node:path";

await rm(resolve(".test-build"), { force: true, recursive: true });
