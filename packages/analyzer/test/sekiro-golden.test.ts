import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { describe, it } from "node:test";
import { analyzeSekiroSave, type SekiroStaticData } from "../src/sekiro/index.ts";

const root = path.resolve(import.meta.dirname, "../../..");

async function readFixture(
  fixturePath = "research/fixtures/sekiro/001/S0000.sl2",
): Promise<ArrayBuffer> {
  const buffer = await readFile(path.join(root, fixturePath));
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
  it("matches the frozen exact_location_report.json for the reference fixture", async () => {
    const [fixture, data, golden] = await Promise.all([
      readFixture(),
      readSekiroData(),
      readJson("research/reports/exact_location_report.json"),
    ]);

    const report = await analyzeSekiroSave(fixture, data, { fileName: "S0000.sl2" });
    assert.deepEqual(report, golden);
    const acquisitionBackedKeyItems = data.keyItems.items.filter(
      (item: any) => item.acquisitionEventFlags?.length > 0,
    );
    assert.equal(acquisitionBackedKeyItems.length, 15);
    for (const item of acquisitionBackedKeyItems) {
      assert.equal(
        item.absenceSemantics,
        "persistent_acquisition_flag_off_means_missing",
      );
      assert.equal(item.statusRules, undefined);
    }
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
    assert.deepEqual(
      shape.gourdSeeds.entities
        .filter((entity: any) => entity.status === "missing")
        .map((entity: any) => entity.id)
        .sort(),
      ["fountainhead_palace", "mibu_village"],
    );
    assert.deepEqual(
      shape.prayerBeads.entities
        .filter((entity: any) => entity.status === "missing")
        .map((entity: any) => entity.id)
        .sort(),
      [
        "ashina_castle_hidden_chest",
        "ashina_elite_ujinari_mizou",
        "fountainhead_underwater_chest",
        "headless_ape_bead_1",
        "headless_ape_bead_2",
        "hirata_audience_chamber_hidden_chest",
        "juzou_the_drunkard_hirata_revisit",
        "lone_shadow_masanaga_hirata_revisit",
        "lone_shadow_masanaga_serpent_shrine",
        "mibu_underwater_chest",
        "sakura_bull",
        "senpou_temple_underwater",
        "seven_ashina_spears_shume",
        "shigekichi_red_guard",
      ],
    );
    assert.equal(shape.gourdSeeds.locationAttribution, undefined);
    assert.equal(shape.prayerBeads.locationAttribution, undefined);
    assert.deepEqual(shape.bosses.summary, {
      total: 14,
      defeated: 8,
      not_defeated: 6,
      unknown: 0,
      byStatus: { defeated: 8, not_defeated: 6, unknown: 0 },
      notDefeated: 6,
    });
    assert.deepEqual(shape.skills.summary, {
      total: 57,
      unlocked: 31,
      missing: 26,
      unknown: 0,
      byStatus: { unlocked: 31, missing: 26, unknown: 0 },
    });
    assert.deepEqual(shape.keyItems.summary, {
      total: 33,
      collected: 22,
      missing: 11,
      unknown: 0,
      byStatus: { collected: 22, missing: 11, unknown: 0 },
    });
  });

  it("provides acquisition and location guidance for every report entity", async () => {
    const fixture = await readFixture();
    const report = await analyzeSekiroSave(fixture, await readSekiroData(), {
      fileName: "S0000.sl2",
    });
    const shape = report.parseSekiroSaveShape;

    for (const categoryKey of [
      "gourdSeeds",
      "prayerBeads",
      "prosthetics",
      "prostheticUpgrades",
      "skills",
      "keyItems",
      "endings",
      "bosses",
    ]) {
      for (const entity of shape[categoryKey].entities) {
        const metadata = entity.acquisitionMetadata ?? {};
        const acquisition = metadata.acquisition ?? metadata.acquisitionMethod;

        assert.equal(
          typeof acquisition === "string" &&
            acquisition.trim().length > 0 &&
            !/^unknown\b/i.test(acquisition),
          true,
          `${categoryKey}/${entity.id} must provide Acquisition guidance`,
        );
        assert.equal(
          typeof metadata.location === "string" && metadata.location.trim().length > 0,
          true,
          `${categoryKey}/${entity.id} must provide Location guidance`,
        );
      }
    }
  });

  it("reconciles exact progression across late-game fixtures", async () => {
    const data = await readSekiroData();
    const cases = [
      {
        fixture:
          "research/fixtures/sekiro/002/S0000.sl2",
        gourdSeeds: 8,
        prayerBeads: 28,
        skillsUnlocked: 32,
        keyItemsCollected: 23,
        bestowalUnlocked: false,
        defeatedBosses: [
          "corrupted_monk",
          "divine_dragon",
          "genichiro",
          "great_shinobi_owl",
          "guardian_ape",
          "gyoubu_oniwa",
          "lady_butterfly",
          "screen_monkeys",
          "true_monk",
        ],
        missingPrayerBeads: [
          "ashina_castle_hidden_chest",
          "ashina_elite_ujinari_mizou",
          "headless_ape_bead_1",
          "headless_ape_bead_2",
          "hirata_audience_chamber_hidden_chest",
          "juzou_the_drunkard_hirata_revisit",
          "lone_shadow_masanaga_hirata_revisit",
          "mibu_underwater_chest",
          "sakura_bull",
          "senpou_temple_underwater",
          "seven_ashina_spears_shume",
          "shigekichi_red_guard",
        ],
      },
      {
        fixture: "research/fixtures/sekiro/003/S0000.sl2",
        gourdSeeds: 8,
        prayerBeads: 33,
        skillsUnlocked: 33,
        keyItemsCollected: 23,
        bestowalUnlocked: true,
        defeatedBosses: [
          "corrupted_monk",
          "demon_of_hatred",
          "divine_dragon",
          "genichiro",
          "great_shinobi_owl",
          "guardian_ape",
          "gyoubu_oniwa",
          "headless_ape",
          "lady_butterfly",
          "screen_monkeys",
          "true_monk",
        ],
        missingPrayerBeads: [
          "ashina_castle_hidden_chest",
          "hirata_audience_chamber_hidden_chest",
          "juzou_the_drunkard_hirata_revisit",
          "lone_shadow_masanaga_hirata_revisit",
          "sakura_bull",
          "senpou_temple_underwater",
          "shigekichi_red_guard",
        ],
      },
    ];

    for (const testCase of cases) {
      const report = await analyzeSekiroSave(
        await readFixture(testCase.fixture),
        data,
        { fileName: path.basename(testCase.fixture) },
      );
      const shape = report.parseSekiroSaveShape;

      assert.deepEqual(shape.gourdSeeds.summary.byStatus, {
        collected: testCase.gourdSeeds,
        missing: 9 - testCase.gourdSeeds,
        unknown: 0,
      });
      assert.deepEqual(shape.prayerBeads.summary.byStatus, {
        collected: testCase.prayerBeads,
        missing: 40 - testCase.prayerBeads,
        unknown: 0,
      });
      assert.deepEqual(shape.bosses.summary.byStatus, {
        defeated: testCase.defeatedBosses.length,
        not_defeated: 14 - testCase.defeatedBosses.length,
        unknown: 0,
      });
      assert.deepEqual(shape.skills.summary.byStatus, {
        unlocked: testCase.skillsUnlocked,
        missing: 57 - testCase.skillsUnlocked,
        unknown: 0,
      });
      assert.deepEqual(shape.keyItems.summary.byStatus, {
        collected: testCase.keyItemsCollected,
        missing: 33 - testCase.keyItemsCollected,
        unknown: 0,
      });
      assert.deepEqual(
        Object.fromEntries(
          shape.skills.entities
            .filter((entity: any) => entity.skillType === "ninjutsu")
            .map((entity: any) => [entity.id, entity.status]),
        ),
        {
          bloodsmoke_ninjutsu: "unlocked",
          puppeteer_ninjutsu: "unlocked",
          bestowal_ninjutsu: testCase.bestowalUnlocked ? "unlocked" : "missing",
        },
      );
      assert.deepEqual(
        shape.keyItems.entities
          .filter(
            (entity: any) =>
              entity.acquisitionEvidence && entity.status === "missing",
          )
          .map((entity: any) => entity.id)
          .sort(),
        [
          "holy_chapter_dragons_return",
          "holy_chapter_infested",
          "holy_chapter_infested_alt",
          "iron_fortress",
          "malcontents_ring",
        ],
      );
      assert.deepEqual(
        shape.bosses.entities
          .filter((entity: any) => entity.status === "defeated")
          .map((entity: any) => entity.id)
          .sort(),
        testCase.defeatedBosses,
      );
      assert.deepEqual(
        shape.gourdSeeds.entities
          .filter((entity: any) => entity.status === "missing")
          .map((entity: any) => entity.id)
          .sort(),
        ["mibu_village"],
      );
      assert.deepEqual(
        shape.prayerBeads.entities
          .filter((entity: any) => entity.status === "missing")
          .map((entity: any) => entity.id)
          .sort(),
        testCase.missingPrayerBeads,
      );
      for (const categoryKey of ["gourdSeeds", "prayerBeads"]) {
        const category = shape[categoryKey];
        assert.equal(category.locationAttribution, undefined);
        assert.equal(
          category.entities.filter((entity: any) => entity.status === "missing")
            .length,
          category.summary.missing,
        );
        assert.equal(
          category.entities.filter((entity: any) => entity.status === "unknown")
            .length,
          0,
        );
      }
    }
  });
});
