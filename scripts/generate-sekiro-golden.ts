import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  analyzeSekiroSave,
  type SekiroStaticData,
} from "../packages/analyzer/src/sekiro/index.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

async function readJson(relativePath: string): Promise<any> {
  return JSON.parse(await readFile(path.join(root, relativePath), "utf8"));
}

const data: SekiroStaticData = {
  eventFlagLayout: await readJson("data/sekiro/event-flag-layout.json"),
  itemIds: await readJson("data/sekiro/item-ids.json"),
  gourdSeeds: await readJson("data/sekiro/gourd-seeds.json"),
  prayerBeads: await readJson("data/sekiro/prayer-beads.json"),
  bosses: await readJson("data/sekiro/bosses.json"),
  prosthetics: await readJson("data/sekiro/prosthetics.json"),
  prostheticUpgrades: await readJson("data/sekiro/prosthetic-upgrades.json"),
  skills: await readJson("data/sekiro/skills.json"),
  keyItems: await readJson("data/sekiro/key-items.json"),
  endings: await readJson("data/sekiro/endings.json"),
};

const fixturePath = path.join(
  root,
  "research/fixtures/sekiro/001/S0000.sl2",
);
const fixture = await readFile(fixturePath);
const buffer = fixture.buffer.slice(
  fixture.byteOffset,
  fixture.byteOffset + fixture.byteLength,
);
const report = await analyzeSekiroSave(buffer, data, {
  fileName: "S0000.sl2",
});
const reportPath = path.join(
  root,
  "research/reports/exact_location_report.json",
);

await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(`Wrote ${path.relative(root, reportPath)}`);
