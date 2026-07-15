#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const STEAM_ID64_MIN = 76_561_197_960_265_728n;
const STEAM_ID64_MAX = STEAM_ID64_MIN + 0xffff_ffffn;

function steamId64Offsets(buffer) {
  const offsets = [];
  for (let offset = 0; offset <= buffer.length - 8; offset += 1) {
    const value = buffer.readBigUInt64LE(offset);
    if (value >= STEAM_ID64_MIN && value <= STEAM_ID64_MAX) offsets.push(offset);
  }
  return offsets;
}

const [inputArg, outputArg] = process.argv.slice(2);
if (!inputArg || !outputArg) throw new Error("Usage: pnpm sanitize:fixture <input.sl2> <output.sl2>");
const inputPath = path.resolve(inputArg);
const outputPath = path.resolve(outputArg);
if (inputPath === outputPath) throw new Error("Refusing to overwrite the source save; choose a separate output path.");
const fixture = Buffer.from(await readFile(inputPath));
const offsets = steamId64Offsets(fixture);
for (const offset of offsets) fixture.writeBigUInt64LE(0n, offset);
await writeFile(outputPath, fixture);
console.log(`Sanitized ${offsets.length} SteamID64 value(s) into ${outputPath}`);
