export interface Bnd4Entry {
  index: number;
  name: string;
  offset: number;
  size: number;
}

export interface ParsedSave {
  format: "BND4";
  entries: Bnd4Entry[];
  getEntry(name: string): Uint8Array;
}

export interface EventFlagLayout {
  recordId: number;
  recordVersion: number;
  recordDataOffset: number;
  pageSize: number;
  pagesPerCategory: number;
  serializedBankCategoryBases: Record<string, number>;
  worldBlockCategories: Array<{
    area: number;
    block: number;
    category: number;
  }>;
}

export interface ItemRecord {
  offset: number;
  offsetHex: string;
  qtyAfterId: number | null;
  hasInventoryMirrorPrefix: boolean;
}

export interface WeaponInventoryRecord {
  offset: number;
  offsetHex: string;
  qtyAfterId: number | null;
}

const INVENTORY_MIRROR_PREFIX_HIGH_BYTE = 0xb0;
const INVENTORY_QUANTITY_MIN = 0;
const INVENTORY_QUANTITY_MAX = 999;
const WEAPON_INVENTORY_RECORD_PREFIX = [0x80, 0x80] as const;
const WEAPON_INVENTORY_QUANTITY = 1;

function bytesFromArrayBuffer(buffer: ArrayBuffer): Uint8Array {
  return new Uint8Array(buffer);
}

function readUint32Le(bytes: Uint8Array, offset: number): number {
  return new DataView(bytes.buffer, bytes.byteOffset + offset, 4).getUint32(0, true);
}

function bytesEqual(bytes: Uint8Array, offset: number, expected: Uint8Array): boolean {
  if (offset < 0 || offset + expected.length > bytes.length) {
    return false;
  }

  for (let index = 0; index < expected.length; index += 1) {
    if (bytes[offset + index] !== expected[index]) {
      return false;
    }
  }
  return true;
}

export function parseBnd4(buffer: ArrayBuffer): Bnd4Entry[] {
  const data = bytesFromArrayBuffer(buffer);
  if (
    data.length < 4 ||
    data[0] !== 0x42 ||
    data[1] !== 0x4e ||
    data[2] !== 0x44 ||
    data[3] !== 0x34
  ) {
    throw new Error("Not a BND4 container");
  }

  const count = readUint32Le(data, 12);
  const decoder = new TextDecoder("utf-16le");
  const entries: Bnd4Entry[] = [];

  for (let index = 0; index < count; index += 1) {
    const recordOffset = 0x40 + index * 0x20;
    if (recordOffset + 0x20 > data.length) {
      throw new Error(`BND4 entry table is truncated at index ${index}`);
    }

    const size = readUint32Le(data, recordOffset + 8);
    const dataOffset = readUint32Le(data, recordOffset + 16);
    const nameOffset = readUint32Le(data, recordOffset + 20);

    if (dataOffset + size > data.length) {
      throw new Error(`BND4 entry ${index} data exceeds file bounds`);
    }
    if (nameOffset >= data.length) {
      throw new Error(`BND4 entry ${index} name offset exceeds file bounds`);
    }

    let cursor = nameOffset;
    while (
      cursor + 1 < data.length &&
      !(data[cursor] === 0 && data[cursor + 1] === 0)
    ) {
      cursor += 2;
    }

    const name = decoder.decode(data.subarray(nameOffset, cursor));
    entries.push({ index, name, offset: dataOffset, size });
  }

  return entries;
}

export function getUserSlot(
  buffer: ArrayBuffer,
  entries: Bnd4Entry[],
  name: string,
): Uint8Array {
  const entry = entries.find((candidate) => candidate.name === name);
  if (!entry) {
    throw new Error(`Missing BND4 entry ${name}`);
  }

  return bytesFromArrayBuffer(buffer).slice(entry.offset, entry.offset + entry.size);
}

export function parseSave(buffer: ArrayBuffer): ParsedSave {
  const entries = parseBnd4(buffer);
  return {
    format: "BND4",
    entries,
    getEntry: (name: string) => getUserSlot(buffer, entries, name),
  };
}

function findEventFlagRecord(slot: Uint8Array, layout: EventFlagLayout): number {
  for (let offset = 0; offset + 16 <= slot.length; offset += 4) {
    if (
      readUint32Le(slot, offset + 4) === layout.recordId &&
      readUint32Le(slot, offset + 8) === layout.recordVersion
    ) {
      return offset;
    }
  }
  return -1;
}

function eventFlagCategory(
  eventFlag: number,
  layout: EventFlagLayout,
): number | null {
  const area = Math.floor(eventFlag / 100_000) % 100;
  const block = Math.floor(eventFlag / 10_000) % 10;

  if (area >= 90 || area + block === 0) {
    return 0;
  }

  return (
    layout.worldBlockCategories.find(
      (candidate) => candidate.area === area && candidate.block === block,
    )?.category ?? null
  );
}

export function readEventFlag(
  slot: Uint8Array,
  eventFlag: number | null | undefined,
  layout: EventFlagLayout,
): boolean | null {
  if (eventFlag == null) {
    return null;
  }

  const recordOffset = findEventFlagRecord(slot, layout);
  const bank = Math.floor(eventFlag / 10_000_000) % 10;
  const serializedBankBase = layout.serializedBankCategoryBases[String(bank)];
  const category = eventFlagCategory(eventFlag, layout);
  if (recordOffset < 0 || serializedBankBase === undefined || category === null) {
    return null;
  }

  const thousand = Math.floor(eventFlag / 1_000) % 10;
  const pageBit = eventFlag % 1_000;
  const categorySize = layout.pageSize * layout.pagesPerCategory;
  const pageOffset =
    recordOffset +
    layout.recordDataOffset +
    (serializedBankBase + category) * categorySize +
    thousand * layout.pageSize;
  const wordOffset = pageOffset + Math.floor(pageBit / 32) * 4;
  if (wordOffset + 4 > slot.length) {
    return null;
  }

  const mask = 1 << (31 - (pageBit & 31));
  return Boolean(readUint32Le(slot, wordOffset) & mask);
}

export function bytesFromHex(hex: string): Uint8Array {
  const compact = hex.replace(/\s+/g, "");
  if (compact.length % 2 !== 0) {
    throw new Error(`Invalid hex string length: ${hex}`);
  }

  const bytes = new Uint8Array(compact.length / 2);
  for (let index = 0; index < compact.length; index += 2) {
    bytes[index / 2] = Number.parseInt(compact.slice(index, index + 2), 16);
  }
  return bytes;
}

export function findBytes(haystack: Uint8Array, needle: Uint8Array, start = 0): number {
  if (needle.length === 0) {
    return -1;
  }

  for (let offset = start; offset <= haystack.length - needle.length; offset += 1) {
    if (bytesEqual(haystack, offset, needle)) {
      return offset;
    }
  }
  return -1;
}

export function hasInventoryMirrorPrefix(
  slot: Uint8Array,
  offset: number,
  itemId: Uint8Array,
): boolean {
  if (offset < 4) {
    return false;
  }

  const expected = new Uint8Array([
    itemId[0],
    itemId[1],
    itemId[2],
    INVENTORY_MIRROR_PREFIX_HIGH_BYTE,
  ]);
  return bytesEqual(slot, offset - 4, expected);
}

export function findItemRecords(slot: Uint8Array, itemHex: string): ItemRecord[] {
  const needle = bytesFromHex(itemHex);
  const records: ItemRecord[] = [];
  let start = 0;

  while (true) {
    const offset = findBytes(slot, needle, start);
    if (offset < 0) {
      break;
    }

    const qtyAfterId =
      offset + 8 <= slot.length ? readUint32Le(slot, offset + 4) : null;
    records.push({
      offset,
      offsetHex: `0x${offset.toString(16)}`,
      qtyAfterId,
      hasInventoryMirrorPrefix: hasInventoryMirrorPrefix(slot, offset, needle),
    });
    start = offset + 1;
  }

  return records;
}

function saneQuantity(value: number | null): value is number {
  return (
    value !== null &&
    INVENTORY_QUANTITY_MIN <= value &&
    value <= INVENTORY_QUANTITY_MAX
  );
}

export function readInventoryQuantity(slot: Uint8Array, itemHex: string): number {
  const records = findItemRecords(slot, itemHex);
  const preferred = records.filter(
    (record) => record.hasInventoryMirrorPrefix && saneQuantity(record.qtyAfterId),
  );
  if (preferred.length > 0) {
    return preferred[0].qtyAfterId ?? 0;
  }

  const fallback = records.filter((record) => saneQuantity(record.qtyAfterId));
  return fallback.length > 0 ? fallback[0].qtyAfterId ?? 0 : 0;
}

export function hasItem(slot: Uint8Array, itemHex: string): boolean {
  return findItemRecords(slot, itemHex).length > 0;
}

export function findWeaponInventoryRecords(
  slot: Uint8Array,
  itemHex: string,
): WeaponInventoryRecord[] {
  const records: WeaponInventoryRecord[] = [];
  for (const record of findItemRecords(slot, itemHex)) {
    const offset = record.offset;
    if (
      record.qtyAfterId === WEAPON_INVENTORY_QUANTITY &&
      offset >= 2 &&
      slot[offset - 2] === WEAPON_INVENTORY_RECORD_PREFIX[0] &&
      slot[offset - 1] === WEAPON_INVENTORY_RECORD_PREFIX[1]
    ) {
      records.push({
        offset,
        offsetHex: record.offsetHex,
        qtyAfterId: record.qtyAfterId,
      });
    }
  }

  return records;
}
