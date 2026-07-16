import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { describe, it } from "node:test";
import {
  getUserSlot,
  parseBnd4,
  readEventFlag,
  readInventoryQuantity,
} from "../src/index.ts";

const root = path.resolve(import.meta.dirname, "../../..");

async function readFixture(): Promise<ArrayBuffer> {
  const buffer = await readFile(path.join(root, "research/fixtures/sekiro/001/S0000.sl2"));
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
}

async function readJson(filePath: string): Promise<any> {
  return JSON.parse(await readFile(path.join(root, filePath), "utf8"));
}

describe("BND4 parser", () => {
  it("extracts USER_DATA000 from the frozen fixture", async () => {
    const fixture = await readFixture();
    const entries = parseBnd4(fixture);
    const slot = getUserSlot(fixture, entries, "USER_DATA000");

    assert.equal(entries.length, 12);
    assert.equal(entries[0].name, "USER_DATA000");
    assert.equal(entries.at(-1)?.name, "USER_DATA011");
    assert.deepEqual(
      entries.map((entry) => entry.name),
      Array.from({ length: 12 }, (_, index) => `USER_DATA${index.toString().padStart(3, "0")}`),
    );
    assert.equal(entries[0].offset, 768);
    assert.equal(entries[0].size, 1048592);
    assert.equal(slot.length, entries[0].size);
  });
});

describe("event flag and inventory readers", () => {
  it("matches the documented Sekiro event flag layout", async () => {
    const fixture = await readFixture();
    const entries = parseBnd4(fixture);
    const slot = getUserSlot(fixture, entries, "USER_DATA000");
    const layoutData = await readJson("data/sekiro/event-flag-layout.json");
    const layout = layoutData.layouts[0];

    assert.equal(layout.recordId, 1000);
    assert.equal(layout.recordVersion, 101);
    assert.equal(layout.recordDataOffset, 0x34);
    assert.equal(layout.pageSize, 0x80);
    assert.equal(readEventFlag(slot, 6723, layout), true);
    assert.equal(readEventFlag(slot, 6724, layout), true);
    assert.equal(readEventFlag(slot, 6728, layout), false);
    assert.equal(readEventFlag(slot, 71101210, layout), true);
    assert.equal(readEventFlag(slot, 71102000, layout), true);
  });

  it("reads inventory quantities used by derived counts", async () => {
    const fixture = await readFixture();
    const entries = parseBnd4(fixture);
    const slot = getUserSlot(fixture, entries, "USER_DATA000");
    const itemIds = await readJson("data/sekiro/item-ids.json");
    const itemsById = Object.fromEntries(itemIds.items.map((item: any) => [item.id, item]));

    assert.equal(readInventoryQuantity(slot, itemsById.healing_gourd.itemIdHex), 8);
    assert.equal(readInventoryQuantity(slot, itemsById.gourd_seed.itemIdHex), 0);
    assert.equal(readInventoryQuantity(slot, itemsById.prayer_bead.itemIdHex), 2);
  });
});
