export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };

export type AnyRecord = Record<string, any>;

export async function sha256Hex(buffer: ArrayBuffer): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new Error("Web Crypto subtle digest is required for browser-native SHA-256");
  }

  const digest = await globalThis.crypto.subtle.digest("SHA-256", buffer);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function hasOwn(object: AnyRecord, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(object, key);
}

export function pickExisting(object: AnyRecord, keys: string[]): AnyRecord {
  const picked: AnyRecord = {};
  for (const key of keys) {
    if (hasOwn(object, key)) {
      picked[key] = object[key];
    }
  }
  return picked;
}
