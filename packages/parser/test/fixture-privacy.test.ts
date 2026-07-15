import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { describe, it } from "node:test";

const STEAM_ID64_MIN = 76_561_197_960_265_728n;
const STEAM_ID64_MAX = STEAM_ID64_MIN + 0xffff_ffffn;
const STEAM_ID64_HIGH_WORD = Number(STEAM_ID64_MIN >> 32n);
const root = path.resolve(import.meta.dirname, "../../..");

describe("public fixture privacy", () => {
  it("contains no embedded SteamID64 account identifiers", async () => {
    const fixture = await readFile(path.join(root, "research/fixtures/S0000.sl2"));
    const matches: number[] = [];
    for (let offset = 0; offset <= fixture.length - 8; offset += 1) {
      if (fixture.readUInt32LE(offset + 4) !== STEAM_ID64_HIGH_WORD) continue;
      const value = fixture.readBigUInt64LE(offset);
      if (value >= STEAM_ID64_MIN && value <= STEAM_ID64_MAX) matches.push(offset);
    }
    assert.deepEqual(matches, []);
  });
});
