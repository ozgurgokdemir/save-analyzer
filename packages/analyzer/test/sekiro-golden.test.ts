import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { describe, it } from "node:test";
import { analyzeSekiroSave, type SekiroStaticData } from "../src/sekiro/index.ts";

const root = path.resolve(import.meta.dirname, "../../..");

async function readFixture(): Promise<ArrayBuffer> {
  const buffer = await readFile(path.join(root, "research/fixtures/S0000.sl2"));
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
}

async function readJson(filePath: string): Promise<any> {
  return JSON.parse(await readFile(path.join(root, filePath), "utf8"));
}

async function readSekiroData(): Promise<SekiroStaticData> {
  return {
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
}

describe("Sekiro analyzer golden parity", () => {
  it("matches the frozen exact_location_report.json for S0000.sl2", async () => {
    const [fixture, data, golden] = await Promise.all([
      readFixture(),
      readSekiroData(),
      readJson("research/reports/exact_location_report.json"),
    ]);

    const report = await analyzeSekiroSave(fixture, data, { fileName: "S0000.sl2" });
    assert.deepEqual(report, golden);
  });

  it("preserves the frozen category summaries", async () => {
    const fixture = await readFixture();
    const report = await analyzeSekiroSave(fixture, await readSekiroData(), {
      fileName: "S0000.sl2",
    });
    const shape = report.parseSekiroSaveShape;

    assert.deepEqual(shape.gourdSeeds.summary, {
      total: 9,
      collected: 7,
      missing: 2,
      unknown: 0,
      byStatus: { collected: 7, missing: 2, unknown: 0 },
    });
    assert.deepEqual(shape.prayerBeads.summary, {
      total: 40,
      collected: 26,
      missing: 14,
      unknown: 0,
      byStatus: { collected: 26, missing: 14, unknown: 0 },
    });
    assert.deepEqual(shape.bosses.summary, {
      total: 14,
      defeated: 0,
      not_defeated: 0,
      unknown: 14,
      byStatus: { defeated: 0, not_defeated: 0, unknown: 14 },
      notDefeated: 0,
    });
  });
});
