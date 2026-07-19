import {
  findItemRecords,
  findWeaponInventoryRecords,
  hasItem,
  parseBnd4,
  readEventFlag as readEventFlagFromSlot,
  readInventoryQuantity,
  getUserSlot,
  type EventFlagLayout,
} from "@save-analyzer/parser";
import { hasOwn, pickExisting, sha256Hex, type AnyRecord } from "@save-analyzer/shared";

const SOURCE_CONFIDENCE_VERIFIED = "Verified";
const SOURCE_CONFIDENCE_PROBABLE = "Probable";
const SOURCE_CONFIDENCE_UNKNOWN = "Unknown";
const NORMALIZED_CONFIDENCE_VALUES = new Set(["verified", "probable", "unknown"]);

export interface SekiroStaticData {
  eventFlagLayout: AnyRecord;
  itemIds: AnyRecord;
  gourdSeeds: AnyRecord;
  prayerBeads: AnyRecord;
  bosses: AnyRecord;
  prosthetics: AnyRecord;
  prostheticUpgrades: AnyRecord;
  skills: AnyRecord;
  keyItems: AnyRecord;
  endings: AnyRecord;
}

export interface AnalyzeSekiroOptions {
  fileName?: string;
  activeSlot?: string;
}

interface SekiroContext {
  slot: Uint8Array;
  eventLayout: EventFlagLayout & AnyRecord;
}

function pyGet<T = any>(object: AnyRecord | null | undefined, key: string, fallback: T): T {
  if (object && hasOwn(object, key)) {
    return object[key] as T;
  }
  return fallback;
}

function flagSignalStatus(state: boolean | null): string {
  if (state === null) {
    return "unknown";
  }
  return state ? "on" : "off";
}

function readEventFlag(context: SekiroContext, eventFlag: number | null | undefined): boolean | null {
  return readEventFlagFromSlot(context.slot, eventFlag, context.eventLayout);
}

function eventFlagSignal(
  context: SekiroContext,
  eventFlag: number | null | undefined,
  { source, details }: { source: string; details: string },
): AnyRecord {
  const state = readEventFlag(context, eventFlag);
  const confidence =
    eventFlag != null && state !== null
      ? SOURCE_CONFIDENCE_VERIFIED
      : SOURCE_CONFIDENCE_UNKNOWN;

  return {
    eventFlag: eventFlag ?? null,
    state,
    status: flagSignalStatus(state),
    source,
    details,
    confidence,
  };
}

function unmappedSignal(details: string): AnyRecord {
  return {
    eventFlag: null,
    state: null,
    status: "unknown",
    details,
    confidence: SOURCE_CONFIDENCE_UNKNOWN,
  };
}

function analyzeGenericEvidence(context: SekiroContext, evidence: AnyRecord): AnyRecord {
  const evidenceType = evidence.type;

  if (evidenceType === "event_flag") {
    const flag = evidence.flag;
    const state = readEventFlag(context, flag);
    const stateConfidence = flag != null && state !== null ? "verified" : "unknown";
    return {
      ...evidence,
      state,
      status: flagSignalStatus(state),
      stateConfidence,
      confidence: pyGet(evidence, "confidence", stateConfidence),
    };
  }

  if (evidenceType === "inventory_item") {
    const itemIdHex = evidence.itemIdHex;
    const records = itemIdHex ? findItemRecords(context.slot, itemIdHex) : [];
    const state = itemIdHex ? records.length > 0 : null;
    return {
      ...evidence,
      state,
      status: state ? "present" : state === false ? "absent" : "unknown",
      recordCount: records.length,
      records,
      confidence: pyGet(evidence, "confidence", "unknown"),
    };
  }

  if (evidenceType === "inventory_weapon") {
    const itemIdHex = evidence.itemIdHex;
    const records = itemIdHex ? findWeaponInventoryRecords(context.slot, itemIdHex) : [];
    const state = itemIdHex ? records.length > 0 : null;
    const confidence = pyGet(
      evidence,
      "confidence",
      state !== null ? "verified" : "unknown",
    );
    return {
      ...evidence,
      state,
      status: state ? "present" : state === false ? "absent" : "unknown",
      recordCount: records.length,
      records,
      confidence,
    };
  }

  return {
    ...evidence,
    state: null,
    status: "unknown",
    confidence: "unknown",
  };
}

function genericRuleMatches(evidenceById: AnyRecord, rule: AnyRecord): boolean {
  return pyGet<AnyRecord[]>(rule, "when", []).every((condition) => {
    const evidence = evidenceById[condition.evidenceId] ?? {};
    return evidence.state === condition.state;
  });
}

function canonicalConfidence(value: unknown): string {
  if (typeof value === "string") {
    const normalized = value.toLowerCase();
    if (NORMALIZED_CONFIDENCE_VALUES.has(normalized)) {
      return normalized;
    }
  }
  return "unknown";
}

function normalizedNotes(value: unknown): unknown[] {
  if (value == null) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}

function ensureCommonEntityFields(
  entity: AnyRecord,
  {
    category,
    evidence,
    acquisitionMetadata,
    notes,
  }: {
    category?: string;
    evidence?: AnyRecord[];
    acquisitionMetadata?: AnyRecord;
    notes?: unknown[];
  } = {},
): AnyRecord {
  const normalized = { ...entity };

  if (category !== undefined && !hasOwn(normalized, "category")) {
    normalized.category = category;
  }
  if (!hasOwn(normalized, "name")) {
    normalized.name = normalized.id;
  }

  normalized.evidence = evidence !== undefined ? evidence : pyGet(normalized, "evidence", []);

  let entityAcquisitionMetadata = acquisitionMetadata;
  if (entityAcquisitionMetadata === undefined) {
    entityAcquisitionMetadata = pyGet(
      normalized,
      "acquisitionMetadata",
      pyGet(normalized, "sourceLocation", {}),
    );
  }
  normalized.acquisitionMetadata = entityAcquisitionMetadata || {};

  let entityNotes: unknown = notes;
  if (entityNotes === undefined) {
    entityNotes = pyGet(normalized, "notes", null);
    if (
      entityNotes == null &&
      normalized.acquisitionMetadata &&
      typeof normalized.acquisitionMetadata === "object" &&
      !Array.isArray(normalized.acquisitionMetadata)
    ) {
      entityNotes = normalized.acquisitionMetadata.notes;
    }
  }
  normalized.notes = normalizedNotes(entityNotes);

  return normalized;
}

function analyzeGenericEntity(context: SekiroContext, entity: AnyRecord): AnyRecord {
  const evidence = pyGet<AnyRecord[]>(entity, "evidence", []).map((item) =>
    analyzeGenericEvidence(context, item),
  );
  const evidenceById = Object.fromEntries(evidence.map((item) => [item.id, item]));
  const matchedRule =
    pyGet<AnyRecord[]>(entity, "statusRules", []).find((rule) =>
      genericRuleMatches(evidenceById, rule),
    ) ?? null;
  const status = matchedRule ? matchedRule.status : "unknown";
  const confidence = matchedRule ? matchedRule.confidence : "unknown";
  const metadata: AnyRecord = {};

  for (const [key, value] of Object.entries(entity)) {
    if (key !== "evidence" && key !== "statusRules") {
      metadata[key] = value;
    }
  }

  return ensureCommonEntityFields({
    ...metadata,
    status,
    confidence,
    evidence,
  });
}

function analyzeGenericEntities(context: SekiroContext, entities: AnyRecord[]): AnyRecord[] {
  return entities.map((entity) => analyzeGenericEntity(context, entity));
}

function analyzeBossEntities(context: SekiroContext, entities: AnyRecord[]): AnyRecord[] {
  return analyzeGenericEntities(context, entities).map((entity) => {
    const evidence = pyGet<AnyRecord[]>(entity, "evidence", []);
    const memoryAwardFlag = evidence.find((item) => item.id === "memory_award_flag");
    const speedrunSplitFlag = evidence.find(
      (item) => item.id === "speedrunSplitFlagCandidate",
    );
    const state = memoryAwardFlag?.state;
    const status =
      state === true ? "defeated" : state === false ? "not_defeated" : "unknown";
    const confidence =
      typeof state === "boolean"
        ? SOURCE_CONFIDENCE_VERIFIED
        : SOURCE_CONFIDENCE_UNKNOWN;
    const details =
      state === true
        ? "The persistent ItemLotParam Memory award flag is ON in this character save."
        : state === false
          ? "The persistent ItemLotParam Memory award flag is OFF in this character save."
          : "The Memory award flag could not be decoded for this boss.";

    return ensureCommonEntityFields(
      {
        ...entity,
        status,
        confidence,
        progressionEvidence: {
          primary: memoryAwardFlag ?? null,
          corroboratingSplitFlag: speedrunSplitFlag ?? null,
          corroborated:
            typeof state === "boolean" && speedrunSplitFlag?.state === state,
          details,
        },
      },
      { evidence, notes: [details] },
    );
  });
}

function analyzeKeyItemEntities(context: SekiroContext, entities: AnyRecord[]): AnyRecord[] {
  const withAcquisitionFlags = entities.map((entity) => ({
    ...entity,
    evidence: [
      ...pyGet<AnyRecord[]>(entity, "evidence", []),
      ...pyGet<AnyRecord[]>(entity, "acquisitionEventFlags", []).map(
        (mapping, index) => ({
          id: pyGet(mapping, "id", `acquisitionEventFlag${index + 1}`),
          type: "event_flag",
          flag: mapping.flag,
          confidence: pyGet(mapping, "confidence", SOURCE_CONFIDENCE_VERIFIED),
          source: mapping.source,
          details: mapping.details,
          role: "persistent_acquisition",
        }),
      ),
    ],
  }));
  const analyzed = analyzeGenericEntities(context, withAcquisitionFlags);
  for (const entity of analyzed) {
    const ownershipEvidence = pyGet<AnyRecord[]>(entity, "evidence", []);
    const inventoryEvidence = ownershipEvidence.find(
      (evidence) => evidence.id === "inventoryItem",
    );
    const acquisitionEvidence = ownershipEvidence.filter(
      (evidence) => evidence.role === "persistent_acquisition",
    );
    if (acquisitionEvidence.length > 0) {
      const acquired = acquisitionEvidence.some((evidence) => evidence.state === true);
      const allAcquisitionFlagsOff = acquisitionEvidence.every(
        (evidence) => evidence.state === false,
      );
      if (inventoryEvidence?.state === true || acquired) {
        entity.status = "collected";
        entity.confidence = SOURCE_CONFIDENCE_VERIFIED;
      } else if (allAcquisitionFlagsOff) {
        entity.status = "missing";
        entity.confidence = SOURCE_CONFIDENCE_VERIFIED;
      } else {
        entity.status = "unknown";
        entity.confidence = SOURCE_CONFIDENCE_UNKNOWN;
      }
      entity.acquisitionEvidence = acquisitionEvidence;
    }
    entity.ownershipEvidence = ownershipEvidence;
    Object.assign(
      entity,
      ensureCommonEntityFields(entity, {
        evidence: ownershipEvidence,
        acquisitionMetadata: pyGet(entity, "acquisitionMetadata", {}),
      }),
    );
  }
  return analyzed;
}

function compactKeyItemReference(entity: AnyRecord): AnyRecord {
  return pickExisting(entity, [
    "id",
    "category",
    "itemType",
    "name",
    "equipParamGoodsRowId",
    "itemIdHex",
    "status",
    "confidence",
    "ownershipEvidence",
    "acquisitionMetadata",
  ]);
}

function genericStatusSummary(entities: AnyRecord[], statusKeys: string[]): AnyRecord {
  const byStatus = Object.fromEntries(
    statusKeys.map((key) => [
      key,
      entities.filter((entity) => entity.status === key).length,
    ]),
  );
  return {
    total: entities.length,
    ...byStatus,
    byStatus,
  };
}

function aggregateCollectionSummary(total: number, collected: number): AnyRecord {
  const safeCollected = Math.max(0, Math.min(total, collected));
  const byStatus = {
    collected: safeCollected,
    missing: total - safeCollected,
    unknown: 0,
  };
  return {
    total,
    ...byStatus,
    byStatus,
  };
}

function reconcileLocationAttribution(
  locations: AnyRecord[],
  aggregateCollected: number,
): { locations: AnyRecord[]; attribution: AnyRecord | null } {
  const safeCollected = Math.max(0, Math.min(locations.length, aggregateCollected));
  const aggregateMissing = locations.length - safeCollected;
  const knownCollected = locations.filter(
    (location) => location.status === "collected",
  ).length;
  const markedMissing = locations.filter(
    (location) => location.status === "missing",
  ).length;
  const alreadyUnknown = locations.filter(
    (location) => location.status === "unknown",
  ).length;
  const reconciled =
    knownCollected === safeCollected &&
    markedMissing === aggregateMissing &&
    alreadyUnknown === 0;

  if (reconciled) {
    return { locations, attribution: null };
  }

  const unresolvedLocations = markedMissing + alreadyUnknown;
  const details =
    `Inventory progression proves ${safeCollected} of ${locations.length} collected, ` +
    `but location evidence identifies ${knownCollected} collected and leaves ` +
    `${unresolvedLocations} unresolved. The ${aggregateMissing} missing ` +
    `${aggregateMissing === 1 ? "item is" : "items are"} among those unresolved locations.`;
  const reconciledLocations = locations.map((location) => {
    if (location.status !== "missing") {
      return location;
    }
    const confidence = pyGet<AnyRecord | string | null>(location, "confidence", null);
    return {
      ...location,
      status: "unknown",
      statusDetails: details,
      confidence:
        confidence !== null && typeof confidence === "object"
          ? {
              ...confidence,
              collectionStatus: SOURCE_CONFIDENCE_UNKNOWN,
              details,
            }
          : confidence,
    };
  });

  return {
    locations: reconciledLocations,
    attribution: {
      reconciled: false,
      aggregateCollected: safeCollected,
      aggregateMissing,
      knownCollectedLocations: knownCollected,
      unresolvedLocations,
      details,
    },
  };
}

function analyzeEndingRequirement(evidenceById: AnyRecord, requirement: AnyRecord): AnyRecord {
  const evidence = evidenceById[requirement.evidenceId];
  const state = evidence ? evidence.state : null;
  const status = state === true ? "present" : state === false ? "missing" : "unknown";
  return {
    ...requirement,
    state,
    status,
    confidence: evidence ? pyGet(evidence, "confidence", "unknown") : "unknown",
  };
}

function endingMissingRequiredItems(requiredItems: AnyRecord[]): AnyRecord[] {
  return requiredItems.filter(
    (item) => pyGet(item, "required", true) && item.status === "missing",
  );
}

function endingUnknownRequiredItems(requiredItems: AnyRecord[]): AnyRecord[] {
  return requiredItems.filter(
    (item) => pyGet(item, "required", true) && item.status === "unknown",
  );
}

function endingHasVerifiedCompletion(completedEvidence: AnyRecord[]): boolean {
  return completedEvidence.some(
    (evidence) =>
      evidence.state === true &&
      evidence.confidence === "verified" &&
      evidence.type === "event_flag",
  );
}

function analyzeEndingBlockEvidence(evidenceById: AnyRecord, blockRule: AnyRecord): AnyRecord {
  const state = genericRuleMatches(evidenceById, blockRule);
  const confidence = pyGet<string>(blockRule, "confidence", "unknown");
  const permanentlyBlocked = blockRule.permanentlyBlocked;
  const isVerifiedBlock =
    state === true && confidence === "verified" && permanentlyBlocked === true;

  return {
    ...blockRule,
    state,
    status: isVerifiedBlock ? "verified_block" : state ? "potential_block" : "not_present",
    statusDriving: isVerifiedBlock,
    conditionEvidence: pyGet<AnyRecord[]>(blockRule, "when", [])
      .map((condition) => evidenceById[condition.evidenceId])
      .filter((evidence) => evidence !== undefined),
  };
}

function endingVerifiedBlock(blockEvidence: AnyRecord[]): AnyRecord | null {
  return blockEvidence.find((evidence) => evidence.statusDriving === true) ?? null;
}

function endingPotentialBlock(blockEvidence: AnyRecord[]): AnyRecord | null {
  return (
    blockEvidence.find(
      (evidence) => evidence.state === true && evidence.statusDriving !== true,
    ) ?? null
  );
}

function analyzeEndingEvidence(
  context: SekiroContext,
  evidence: AnyRecord,
  keyItemById: AnyRecord,
): AnyRecord {
  if (evidence.type !== "key_item") {
    return analyzeGenericEvidence(context, evidence);
  }

  const keyItem = keyItemById[evidence.keyItemId];
  if (!keyItem) {
    return {
      ...evidence,
      state: null,
      status: "unknown",
      confidence: "unknown",
      details: "Referenced key item is not mapped in key-items.json.",
    };
  }

  let state: boolean | null;
  let status: string;
  if (keyItem.status === "collected") {
    state = true;
    status = "present";
  } else if (keyItem.status === "missing") {
    state = false;
    status = "absent";
  } else {
    state = null;
    status = "unknown";
  }

  return {
    ...evidence,
    state,
    status,
    confidence: pyGet(keyItem, "confidence", "unknown"),
    itemIdHex: keyItem.itemIdHex,
    keyItem: compactKeyItemReference(keyItem),
  };
}

function analyzeEndingRoute(
  context: SekiroContext,
  ending: AnyRecord,
  keyItemById: AnyRecord,
): AnyRecord {
  const completionSource = pyGet(
    ending,
    "completionEvidence",
    pyGet(ending, "completedEndingEvidence", []),
  );
  const availabilitySource = pyGet(
    ending,
    "availabilityEvidence",
    pyGet(ending, "routeAvailabilityEvidence", []),
  );
  const blockRules = pyGet(ending, "blockRules", pyGet(ending, "blockingRules", []));
  const completionEvidence = completionSource.map((evidence: AnyRecord) =>
    analyzeEndingEvidence(context, evidence, keyItemById),
  );
  const availabilityEvidence = availabilitySource.map((evidence: AnyRecord) =>
    analyzeEndingEvidence(context, evidence, keyItemById),
  );
  const evidenceById = Object.fromEntries(
    [...completionEvidence, ...availabilityEvidence].map((evidence) => [
      evidence.id,
      evidence,
    ]),
  );
  const requiredItems = pyGet<AnyRecord[]>(ending, "requiredItems", []).map((requirement) =>
    analyzeEndingRequirement(evidenceById, requirement),
  );
  const missingItems = endingMissingRequiredItems(requiredItems);
  const unknownItems = endingUnknownRequiredItems(requiredItems);
  const blockEvidence = blockRules.map((rule: AnyRecord) =>
    analyzeEndingBlockEvidence(evidenceById, rule),
  );
  const verifiedBlock = endingVerifiedBlock(blockEvidence);
  const potentialBlock = endingPotentialBlock(blockEvidence);

  let status: string;
  let confidence: string;
  let availabilityState: string;
  let permanentlyBlocked: boolean | null;
  let statusDetails: string;

  if (endingHasVerifiedCompletion(completionEvidence)) {
    status = "completed";
    confidence = "verified";
    availabilityState = "completed";
    permanentlyBlocked = false;
    statusDetails = "A verified ending completion flag is ON in this save.";
  } else if (verifiedBlock) {
    status = "blocked";
    confidence = "verified";
    availabilityState = pyGet(verifiedBlock, "blockType", "route_choice");
    permanentlyBlocked = true;
    statusDetails = pyGet(
      verifiedBlock,
      "details",
      "Verified permanent block evidence is present in this save.",
    );
  } else if (potentialBlock) {
    status = "unknown";
    confidence = "unknown";
    availabilityState = "potential_block_unverified";
    permanentlyBlocked = null;
    statusDetails =
      "Potential permanent block evidence is present, but its permanence " +
      "is not verified strongly enough to mark this ending blocked.";
  } else if (missingItems.length > 0) {
    status = "incomplete";
    confidence = pyGet(ending, "routeRequirementConfidence", "probable");
    availabilityState = "missing_requirements";
    permanentlyBlocked = false;
    const missingNames = missingItems.map((item) => item.name).join(", ");
    statusDetails =
      "Route is still possible by currently verified evidence, but the " +
      `save is missing required item(s): ${missingNames}.`;
  } else if (unknownItems.length > 0) {
    status = "unknown";
    confidence = "unknown";
    availabilityState = "unknown_requirements";
    permanentlyBlocked = null;
    statusDetails =
      "One or more required route item signals could not be read from this save.";
  } else if (requiredItems.length > 0) {
    status = "available";
    confidence = pyGet(ending, "routeRequirementConfidence", "probable");
    availabilityState = "requirements_satisfied";
    permanentlyBlocked = false;
    statusDetails =
      "All currently mapped required route items are present, and no verified " +
      "permanent block evidence is present.";
  } else {
    status = "unknown";
    confidence = "unknown";
    availabilityState = "unmapped";
    permanentlyBlocked = null;
    statusDetails = "No verified ending status rule is mapped for this route.";
  }

  const blockReason = verifiedBlock
    ? verifiedBlock.blockType
    : potentialBlock
      ? potentialBlock.blockType
      : null;
  const metadata: AnyRecord = {};
  const omitted = new Set([
    "completedEndingEvidence",
    "completionEvidence",
    "routeAvailabilityEvidence",
    "availabilityEvidence",
    "requiredItems",
    "blockingRules",
    "blockRules",
  ]);

  for (const [key, value] of Object.entries(ending)) {
    if (!omitted.has(key)) {
      metadata[key] = value;
    }
  }

  const routeEntity = {
    ...metadata,
    status,
    confidence,
    statusDetails,
    availability: {
      currentCompletionSelectable: status === "available",
      state: availabilityState,
      blockReason,
      permanentlyBlocked,
      details: statusDetails,
    },
    completionEvidence,
    availabilityEvidence,
    requiredItems,
    missingRequirements: missingItems,
    unknownRequirements: unknownItems,
    blockEvidence,
  };

  return ensureCommonEntityFields(routeEntity, {
    evidence: [...completionEvidence, ...availabilityEvidence, ...blockEvidence],
    acquisitionMetadata: pyGet(routeEntity, "guidance", {}),
    notes: [statusDetails],
  });
}

function analyzeEndingRoutes(
  context: SekiroContext,
  endings: AnyRecord[],
  keyItemById: AnyRecord,
): AnyRecord[] {
  return endings.map((ending) => analyzeEndingRoute(context, ending, keyItemById));
}

function analyzeLocations(context: SekiroContext, locations: AnyRecord[]): AnyRecord[] {
  return locations.map((location) => {
    const eventFlag = pyGet<number | null>(location, "eventFlag", null);
    if (eventFlag === null) {
      return {
        ...location,
        status: "unknown",
        eventFlagState: null,
      };
    }

    const flagState = readEventFlag(context, eventFlag);
    return {
      ...location,
      status: flagState ? "collected" : "missing",
      eventFlagState: flagState,
    };
  });
}

function prayerLocationStatus(
  flagState: boolean | null,
  offPrimaryFlagsAreDefiniteMissing: boolean,
  {
    hasVerifiedSecondaryItemLot,
    hasVerifiedMissingEvidence,
  }: {
    hasVerifiedSecondaryItemLot: boolean;
    hasVerifiedMissingEvidence: boolean;
  },
): string {
  if (flagState === true) {
    return "collected";
  }
  if (flagState === false && offPrimaryFlagsAreDefiniteMissing) {
    return "missing";
  }
  if (hasVerifiedSecondaryItemLot) {
    return "collected";
  }
  if (hasVerifiedMissingEvidence) {
    return "missing";
  }
  if (flagState === null) {
    return "unknown";
  }
  if (offPrimaryFlagsAreDefiniteMissing) {
    return "missing";
  }
  return "unknown";
}

function prayerCollectionConfidence(status: string): string {
  if (status === "collected") {
    return SOURCE_CONFIDENCE_VERIFIED;
  }
  if (status === "missing") {
    return SOURCE_CONFIDENCE_VERIFIED;
  }
  return SOURCE_CONFIDENCE_UNKNOWN;
}

function prayerStatusDetails(
  status: string,
  {
    collectedBySecondaryItemLot,
    missingByEvidence,
  }: { collectedBySecondaryItemLot: boolean; missingByEvidence: boolean },
): string {
  if (status === "collected") {
    if (collectedBySecondaryItemLot) {
      return (
        "Primary pickup/shop flag is OFF, but a verified secondary " +
        "ItemLotParam reward/replacement flag is ON in this save."
      );
    }
    return "Primary pickup/shop flag is ON in this save.";
  }
  if (status === "missing") {
    if (missingByEvidence) {
      return (
        "Verified reward/pickup evidence flags for this location are OFF in " +
        "this save, and collected-by-evidence already reconciles to the " +
        "inventory-derived Prayer Bead total."
      );
    }
    return "Primary pickup/shop flag is OFF and Prayer Bead reconciliation is solved.";
  }
  return (
    "Evidence is insufficient to mark this location collected or missing under " +
    "the finalized Prayer Bead status model."
  );
}

function secondaryItemLotSignals(context: SekiroContext, location: AnyRecord): AnyRecord[] {
  return pyGet<AnyRecord[]>(location, "secondaryItemLotFlags", []).map((secondary) => ({
    ...eventFlagSignal(context, secondary.eventFlag, {
      source: "secondary ItemLotParam reward/replacement flag",
      details: pyGet(
        secondary,
        "details",
        "Secondary ItemLotParam row tied to the same source location.",
      ),
    }),
    rowId: secondary.rowId,
    role: secondary.role,
    awardedItemId: secondary.awardedItemId,
    mappingConfidence: pyGet(
      secondary,
      "mappingConfidence",
      SOURCE_CONFIDENCE_UNKNOWN,
    ),
    attributionConfidence: pyGet(
      secondary,
      "attributionConfidence",
      SOURCE_CONFIDENCE_UNKNOWN,
    ),
    evidence: pyGet(secondary, "evidence", []),
  }));
}

function hasVerifiedSecondaryItemLotCollection(secondarySignals: AnyRecord[]): boolean {
  return secondarySignals.some(
    (signal) =>
      signal.state === true && signal.attributionConfidence === SOURCE_CONFIDENCE_VERIFIED,
  );
}

function hasVerifiedSecondaryItemLotMissing(secondarySignals: AnyRecord[]): boolean {
  return (
    secondarySignals.length > 0 &&
    secondarySignals.every(
      (signal) =>
        signal.state === false &&
        signal.confidence === SOURCE_CONFIDENCE_VERIFIED &&
        signal.attributionConfidence === SOURCE_CONFIDENCE_VERIFIED,
    )
  );
}

function missingEvidenceSignal(
  primarySignal: AnyRecord,
  itemLotSignal: AnyRecord,
  shopSignal: AnyRecord,
  secondarySignals: AnyRecord[],
  location: AnyRecord,
): AnyRecord {
  const semantics = pyGet<AnyRecord | null>(location, "primaryFlagSemantics", null);
  if (semantics === null) {
    return {
      rule: null,
      state: null,
      status: "unknown",
      confidence: SOURCE_CONFIDENCE_UNKNOWN,
      details: "No verified missing-evidence rule is mapped for this location.",
    };
  }

  const rule = semantics.missingEvidenceRule;
  let verified = false;
  if (rule === "primary_and_secondary_item_lot_flags_off") {
    verified =
      itemLotSignal.state === false &&
      itemLotSignal.confidence === SOURCE_CONFIDENCE_VERIFIED &&
      hasVerifiedSecondaryItemLotMissing(secondarySignals);
  } else if (rule === "shop_purchase_flag_off") {
    verified =
      shopSignal.state === false && shopSignal.confidence === SOURCE_CONFIDENCE_VERIFIED;
  }

  return {
    rule,
    state: verified,
    status: verified ? "missing" : "not_satisfied",
    confidence: verified ? SOURCE_CONFIDENCE_VERIFIED : SOURCE_CONFIDENCE_UNKNOWN,
    primaryFlag: primarySignal,
    secondaryItemLotFlags: secondarySignals,
    primaryFlagSemantics: semantics,
    details: pyGet(
      semantics,
      "details",
      "Verified evidence rule for determining missing state.",
    ),
  };
}

function analyzePrayerLocations(
  context: SekiroContext,
  locations: AnyRecord[],
  inventoryEvidence: AnyRecord,
  { offPrimaryFlagsAreDefiniteMissing }: { offPrimaryFlagsAreDefiniteMissing: boolean },
): AnyRecord[] {
  return locations.map((location) => {
    const eventFlag = pyGet<number | null>(location, "eventFlag", null);
    const flagState = readEventFlag(context, eventFlag);
    const secondaryItemLot = secondaryItemLotSignals(context, location);
    const collectedBySecondaryItemLot =
      hasVerifiedSecondaryItemLotCollection(secondaryItemLot);
    const primarySignal = eventFlagSignal(context, eventFlag, {
      source: "primary Prayer Bead mapping",
      details:
        "Current primary collection flag from the mapping data. For shop rows, " +
        "this is the ShopLineupParam purchase flag.",
    });

    const itemLotRowId = pyGet<number | null>(location, "itemLotParamRowId", null);
    const itemLotSignal =
      itemLotRowId === null
        ? unmappedSignal("No ItemLotParam row is mapped for this Prayer Bead.")
        : {
            ...eventFlagSignal(context, eventFlag, {
              source: "SoulSplitter ItemLotParam pickup flag",
              details:
                "ItemLotParam row maps to this pickup/award flag. This is not " +
                "an independent aggregate inventory signal.",
            }),
            rowId: itemLotRowId,
            secondary: secondaryItemLot.length > 0 ? secondaryItemLot : [],
          };

    const shopRowId = pyGet<number | null>(location, "shopLineupParamRowId", null);
    const shopSignal =
      shopRowId === null
        ? unmappedSignal("No ShopLineupParam row is mapped for this Prayer Bead.")
        : {
            ...eventFlagSignal(context, eventFlag, {
              source: "ShopLineupParam purchase flag",
              details: "ShopLineupParam row event flag for this merchant purchase.",
            }),
            rowId: shopRowId,
          };

    const missingEvidence = missingEvidenceSignal(
      primarySignal,
      itemLotSignal,
      shopSignal,
      secondaryItemLot,
      location,
    );
    const missingByEvidence = missingEvidence.confidence === SOURCE_CONFIDENCE_VERIFIED;
    const status = prayerLocationStatus(flagState, offPrimaryFlagsAreDefiniteMissing, {
      hasVerifiedSecondaryItemLot: collectedBySecondaryItemLot,
      hasVerifiedMissingEvidence: missingByEvidence,
    });
    const statusDetails = prayerStatusDetails(status, {
      collectedBySecondaryItemLot,
      missingByEvidence,
    });

    return {
      ...location,
      status,
      statusDetails,
      eventFlagState: flagState,
      primaryPickupFlag: primarySignal,
      bossDefeatFlag: unmappedSignal(
        "Separate boss/miniboss defeat flag has not been mapped for this Prayer Bead.",
      ),
      itemLotFlag: itemLotSignal,
      shopFlag: shopSignal,
      offeringBoxFlag: unmappedSignal(
        "Offering Box replacement flag/state has not been mapped for this Prayer Bead.",
      ),
      missingEvidence,
      inventoryEvidence,
      confidence: {
        locationMapping: pyGet(
          location,
          "mappingConfidence",
          SOURCE_CONFIDENCE_UNKNOWN,
        ),
        primaryFlagState: primarySignal.confidence,
        collectionStatus: prayerCollectionConfidence(status),
        secondaryItemLotAttribution: collectedBySecondaryItemLot
          ? SOURCE_CONFIDENCE_VERIFIED
          : SOURCE_CONFIDENCE_UNKNOWN,
        details: statusDetails,
      },
    };
  });
}

function compactLocation(location: AnyRecord): AnyRecord {
  return pickExisting(location, [
    "id",
    "name",
    "area",
    "location",
    "sourceType",
    "itemLotParamRowId",
    "shopLineupParamRowId",
    "eventFlag",
    "mappingConfidence",
    "status",
    "statusDetails",
    "eventFlagState",
    "primaryPickupFlag",
    "bossDefeatFlag",
    "itemLotFlag",
    "shopFlag",
    "offeringBoxFlag",
    "missingEvidence",
    "inventoryEvidence",
    "confidence",
  ]);
}

function gourdLocationEntity(location: AnyRecord): AnyRecord {
  const eventFlag = pyGet<number | null>(location, "eventFlag", null);
  const evidenceType =
    location.sourceType === "shop"
      ? "shop_flag"
      : pyGet(location, "itemLotParamRowId", null) !== null
        ? "item_lot_flag"
        : "event_flag";
  const evidence = [
    {
      id: "eventFlag",
      type: evidenceType,
      flag: eventFlag,
      eventFlag,
      state: location.eventFlagState,
      status: flagSignalStatus(location.eventFlagState),
      confidence: canonicalConfidence(
        pyGet(location, "mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN),
      ),
      source: "data/sekiro/gourd-seeds.json",
      details:
        "Verified Gourd Seed pickup or shop-purchase event flag for " +
        "this current save state.",
    },
  ];

  return ensureCommonEntityFields(
    {
      ...compactLocation(location),
      category: "gourd_seed",
      confidence: canonicalConfidence(
        pyGet(location, "mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN),
      ),
    },
    {
      evidence,
      acquisitionMetadata: {
        area: pyGet(location, "area", null),
        location: pyGet(location, "location", null),
        acquisition: pyGet(location, "acquisition", null),
        sourceType: pyGet(location, "sourceType", null),
        itemLotParamRowId: pyGet(location, "itemLotParamRowId", null),
        shopLineupParamRowId: pyGet(location, "shopLineupParamRowId", null),
        confidence: canonicalConfidence(
          pyGet(location, "mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN),
        ),
      },
      notes: [],
    },
  );
}

function evidenceEntry(
  source: AnyRecord,
  { evidenceId, evidenceType }: { evidenceId: string; evidenceType: string },
): AnyRecord {
  const entry: AnyRecord = { ...source, id: evidenceId, type: evidenceType };
  if (hasOwn(entry, "eventFlag") && !hasOwn(entry, "flag")) {
    entry.flag = entry.eventFlag;
  }
  if (!hasOwn(entry, "state")) {
    entry.state = null;
  }
  if (!hasOwn(entry, "status")) {
    entry.status = "unknown";
  }
  if (!hasOwn(entry, "confidence")) {
    entry.confidence = SOURCE_CONFIDENCE_UNKNOWN;
  }
  return entry;
}

function prayerLocationEntity(location: AnyRecord): AnyRecord {
  const confidenceDetails = pyGet<AnyRecord>(location, "confidence", {});
  const evidence = [
    evidenceEntry(pyGet(location, "primaryPickupFlag", {}), {
      evidenceId: "primaryPickupFlag",
      evidenceType: "event_flag",
    }),
    evidenceEntry(pyGet(location, "bossDefeatFlag", {}), {
      evidenceId: "bossDefeatFlag",
      evidenceType: "event_flag",
    }),
    evidenceEntry(pyGet(location, "itemLotFlag", {}), {
      evidenceId: "itemLotFlag",
      evidenceType: "item_lot_flag",
    }),
    evidenceEntry(pyGet(location, "shopFlag", {}), {
      evidenceId: "shopFlag",
      evidenceType: "shop_flag",
    }),
    evidenceEntry(pyGet(location, "offeringBoxFlag", {}), {
      evidenceId: "offeringBoxFlag",
      evidenceType: "offering_box_flag",
    }),
    evidenceEntry(pyGet(location, "missingEvidence", {}), {
      evidenceId: "missingEvidence",
      evidenceType: "missing_evidence",
    }),
    evidenceEntry(pyGet(location, "inventoryEvidence", {}), {
      evidenceId: "inventoryEvidence",
      evidenceType: "inventory_summary",
    }),
  ];

  return ensureCommonEntityFields(
    {
      ...compactLocation(location),
      category: "prayer_bead",
      confidence: canonicalConfidence(
        pyGet(
          confidenceDetails,
          "collectionStatus",
          SOURCE_CONFIDENCE_UNKNOWN,
        ),
      ),
      confidenceDetails,
    },
    {
      evidence,
      acquisitionMetadata: {
        area: pyGet(location, "area", null),
        location: pyGet(location, "location", null),
        acquisition: pyGet(location, "acquisition", null),
        sourceType: pyGet(location, "sourceType", null),
        itemLotParamRowId: pyGet(location, "itemLotParamRowId", null),
        shopLineupParamRowId: pyGet(location, "shopLineupParamRowId", null),
        confidence: canonicalConfidence(
          pyGet(location, "mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN),
        ),
      },
      notes: location.statusDetails ? [location.statusDetails] : [],
    },
  );
}

function mappedEventFlags(gourdLocations: AnyRecord[], prayerLocations: AnyRecord[]): number[] {
  const flags = new Set<number>();
  for (const location of [...gourdLocations, ...prayerLocations]) {
    if (pyGet(location, "eventFlag", null) !== null) {
      flags.add(location.eventFlag);
    }
  }
  for (const location of prayerLocations) {
    for (const secondary of pyGet<AnyRecord[]>(location, "secondaryItemLotFlags", [])) {
      if (pyGet(secondary, "eventFlag", null) !== null) {
        flags.add(secondary.eventFlag);
      }
    }
  }
  return [...flags].sort((left, right) => left - right);
}

function genericEntityEventFlags(entities: AnyRecord[]): number[] {
  const flags = new Set<number>();
  for (const entity of entities) {
    for (const evidence of pyGet<AnyRecord[]>(entity, "evidence", [])) {
      if (evidence.type === "event_flag" && pyGet(evidence, "flag", null) !== null) {
        flags.add(evidence.flag);
      }
    }
  }
  return [...flags].sort((left, right) => left - right);
}

const SOURCES_USED = [
  "SoulSplitter wiki: Sekiro item pickup flags extracted via Yapped; right-most column is event flag.",
  "PowerPyx Prayer Bead guide: exact human-readable Prayer Bead location/source enemy names.",
  "PowerPyx boss guide: human-readable major boss locations and route requirements.",
  "PowerPyx skills and combat styles guide: individual skill reward and merchant locations.",
  "GameWith skill guide: skill-tree acquisition and Sculptor's Idol guidance.",
  "SoulsMods Paramdex: ItemLotParam and ShopLineupParam field definitions.",
  "sekiro-online/params: EquipParamGoods row data for boss Memory goods names.",
  "sekiro-online/params: ItemLotParam row data for boss Memory award entries.",
  "SoulSplitter source: Sekiro Boss enum and splitter logic for candidate speedrun boss split flags.",
  "sekiro-online/params: EquipParamWeapon row data for base Prosthetic Tool weapon IDs.",
  "sekiro-online/params: EquipParamWeapon row data for Prosthetic Tool upgrade weapon IDs.",
  "sekiro-online/params: EquipParamGoods row data for Prosthetic Tool source item names.",
  "sekiro-online/params: SkillParam row data for combat-art skill links.",
  "sekiro-online/params: EquipParamWeapon row data for combat-art skill weapon IDs and names.",
  "sekiro-online/params: SkillParam and EquipParamWeapon row data for verified passive, latent, martial-art, and special skill ownership rows.",
  "sekiro-online/params: EquipParamGoods and ItemLotParam rows for Ninjutsu identities and acquisition flags.",
  "Fextralife Skills and Skill Trees page: community skill tree/name/cost/prerequisite context.",
  "Fextralife skill and Esoteric Text pages: community acquisition metadata for mapped Combat Arts.",
  "Fextralife Endings page: community ending-route requirements and final choice items.",
  "sekiro-online/params: EquipParamGoods row data for key item, Esoteric Text, and Prosthetic Tool source item names and IDs.",
  "sekiro-online/params: ItemLotParam row data for Prayer Bead rewards, boss Memories, Ninjutsu, and Key Item acquisition.",
  "sekiro-online/params: ShopLineupParam row data for merchant and Key Item acquisition.",
  "Uploaded .sl2 save, read-only local inspection.",
];

export async function parseSekiroSaveShape(
  buffer: ArrayBuffer,
  data: SekiroStaticData,
  options: AnalyzeSekiroOptions = {},
): Promise<AnyRecord> {
  const fileName = options.fileName ?? "S0000.sl2";
  const slotName = options.activeSlot ?? "USER_DATA000";
  const entries = parseBnd4(buffer);
  const slot = getUserSlot(buffer, entries, slotName);
  const eventLayout = data.eventFlagLayout.layouts[0] as EventFlagLayout & AnyRecord;
  const context: SekiroContext = { slot, eventLayout };

  const itemById = Object.fromEntries(
    pyGet<AnyRecord[]>(data.itemIds, "items", []).map((item) => [item.id, item]),
  );
  const healingGourdUses = readInventoryQuantity(
    slot,
    itemById.healing_gourd.itemIdHex,
  );
  const unusedGourdSeeds = readInventoryQuantity(slot, itemById.gourd_seed.itemIdHex);
  const unusedPrayerBeads = readInventoryQuantity(slot, itemById.prayer_bead.itemIdHex);
  const prayerNecklaces = pyGet<string[]>(
    data.itemIds,
    "prayerNecklaceItemIdsHex",
    [],
  ).filter((itemHex) => hasItem(slot, itemHex)).length;

  const gourdSeedsFound = healingGourdUses - 1 + unusedGourdSeeds;
  const gourdSeedsMissing = data.gourdSeeds.total - gourdSeedsFound;
  const prayerBeadsFound = prayerNecklaces * 4 + unusedPrayerBeads;
  const prayerBeadsMissing = data.prayerBeads.total - prayerBeadsFound;
  const derivedCounts = {
    healingGourdUses,
    unusedGourdSeeds,
    gourdSeedsFound,
    gourdSeedsMissing,
    prayerNecklaces,
    unusedPrayerBeads,
    prayerBeadsFound,
    prayerBeadsMissing,
  };
  const prayerInventoryEvidence = {
    aggregatePrayerBeadsFound: prayerBeadsFound,
    aggregatePrayerBeadsMissing: prayerBeadsMissing,
    prayerNecklaces,
    unusedPrayerBeads,
    exactLocationAttribution: null,
    confidence: SOURCE_CONFIDENCE_VERIFIED,
    details:
      "Aggregate inventory evidence is derived from Prayer Necklace count times four " +
      "plus unused Prayer Bead quantity. It proves total collected count for this save " +
      "but does not identify any exact location.",
  };

  const offPrimaryFlagsAreDefiniteMissing = true;
  const analyzedGourdLocations = analyzeLocations(
    context,
    pyGet<AnyRecord[]>(data.gourdSeeds, "locations", []),
  );
  const analyzedPrayerLocations = analyzePrayerLocations(
    context,
    pyGet<AnyRecord[]>(data.prayerBeads, "locations", []),
    prayerInventoryEvidence,
    { offPrimaryFlagsAreDefiniteMissing },
  );
  const gourdAttribution = reconcileLocationAttribution(
    analyzedGourdLocations,
    gourdSeedsFound,
  );
  const prayerAttribution = reconcileLocationAttribution(
    analyzedPrayerLocations,
    prayerBeadsFound,
  );
  const gourdLocations = gourdAttribution.locations;
  const prayerLocations = prayerAttribution.locations;
  const prayerFlagsOn = prayerLocations.filter(
    (location) => location.eventFlagState === true,
  ).length;
  const prayerFlagsOff = prayerLocations.filter(
    (location) => location.eventFlagState === false,
  ).length;
  const prayerFlagsUnknown = prayerLocations.filter(
    (location) => location.eventFlagState === null,
  ).length;
  const prayerStatusMissing = prayerLocations.filter(
    (location) => location.status === "missing",
  ).length;
  const prayerStatusCollected = prayerLocations.filter(
    (location) => location.status === "collected",
  ).length;
  const prayerStatusUnknown = prayerLocations.filter(
    (location) => location.status === "unknown",
  ).length;
  const prayerSecondaryItemLotAttributed = prayerLocations.filter(
    (location) =>
      location.eventFlagState !== true &&
      hasVerifiedSecondaryItemLotCollection(pyGet(location.itemLotFlag, "secondary", [])),
  ).length;
  // Location flags answer "which ones?", while inventory/progression answers
  // "how many?". The latter remains valid when a save's serialized event-flag
  // layout cannot attribute every collected location.
  const prayerSummary = aggregateCollectionSummary(
    data.prayerBeads.total,
    prayerBeadsFound,
  );

  const knownGourdMissing = gourdLocations.filter(
    (location) => location.status === "missing",
  );
  const shopGourd = gourdLocations.filter((location) => location.sourceType === "shop");
  const shopGourdCollected = shopGourd.filter(
    (location) => location.status === "collected",
  );
  const shopGourdMissing = shopGourd.filter((location) => location.status === "missing");
  const shopGourdUnknown = shopGourd.filter((location) => location.status === "unknown");
  const gourdSummary = aggregateCollectionSummary(
    data.gourdSeeds.total,
    gourdSeedsFound,
  );
  const shopSeedInference = {
    shopSeedsTotal: shopGourd.length,
    shopSeedsFoundByEventFlags: shopGourdCollected.length,
    shopSeedsMissingByEventFlags: shopGourdMissing.length,
    shopSeedsUnknown: shopGourdUnknown.length,
    confidence:
      shopGourdUnknown.length === 0
        ? SOURCE_CONFIDENCE_VERIFIED
        : SOURCE_CONFIDENCE_PROBABLE,
    details:
      shopGourdUnknown.length === 0
        ? "ShopLineupParam event flags resolve both merchant Gourd Seeds in this save."
        : "Derived from total Gourd Seed count minus verified non-shop item-lot flags. This does not identify which shop seed is missing.",
  };

  const mappedFlags = [
    ...mappedEventFlags(gourdLocations, prayerLocations),
    ...genericEntityEventFlags(pyGet<AnyRecord[]>(data.bosses, "bosses", [])),
  ];
  const flagStates: AnyRecord = {};
  for (const flag of [...new Set(mappedFlags)].sort((left, right) => left - right)) {
    flagStates[String(flag)] = readEventFlag(context, flag);
  }

  const bossEntities = analyzeBossEntities(
    context,
    pyGet<AnyRecord[]>(data.bosses, "bosses", []),
  );
  const bossSummary = genericStatusSummary(bossEntities, [
    "defeated",
    "not_defeated",
    "unknown",
  ]);
  bossSummary.notDefeated = bossSummary.not_defeated;

  const prostheticEntities = analyzeGenericEntities(
    context,
    pyGet<AnyRecord[]>(data.prosthetics, "prosthetics", []),
  );
  const prostheticSummary = genericStatusSummary(prostheticEntities, [
    "collected",
    "missing",
    "unknown",
  ]);
  const prostheticUpgradeEntities = analyzeGenericEntities(
    context,
    pyGet<AnyRecord[]>(data.prostheticUpgrades, "upgrades", []),
  );
  const prostheticUpgradeSummary = genericStatusSummary(prostheticUpgradeEntities, [
    "unlocked",
    "missing",
    "unknown",
  ]);
  const skillEntities = analyzeGenericEntities(
    context,
    pyGet<AnyRecord[]>(data.skills, "skills", []),
  );
  const skillSummary = genericStatusSummary(skillEntities, [
    "unlocked",
    "missing",
    "unknown",
  ]);
  const keyItemEntities = analyzeKeyItemEntities(
    context,
    pyGet<AnyRecord[]>(data.keyItems, "items", []),
  );
  const keyItemSummary = genericStatusSummary(keyItemEntities, [
    "collected",
    "missing",
    "unknown",
  ]);
  const keyItemById = Object.fromEntries(
    keyItemEntities.map((entity) => [entity.id, entity]),
  );
  const endingEntities = analyzeEndingRoutes(
    context,
    pyGet<AnyRecord[]>(data.endings, "endings", []),
    keyItemById,
  );
  const endingSummary = genericStatusSummary(endingEntities, [
    "completed",
    "available",
    "incomplete",
    "blocked",
    "unknown",
  ]);
  const memoryItemsFound = pyGet<AnyRecord[]>(data.bosses, "memoryItemIds", []).map(
    (item) => ({
      id: item.id,
      name: item.name,
      itemIdHex: item.itemIdHex,
      status: hasItem(slot, item.itemIdHex) ? "found" : "not_found",
      confidence: SOURCE_CONFIDENCE_PROBABLE,
    }),
  );

  const warnings: string[] = [];
  if (shopGourdUnknown.length > 0) {
    warnings.push(
      "One or more Gourd Seed shop rows still have unknown purchase state because their ShopLineupParam event flags are not verified.",
    );
  }
  if (!String(data.prayerBeads.coverage).includes("complete")) {
    warnings.push(
      `Prayer Bead coverage is ${data.prayerBeads.coverage}; unresolved replacement or row-ordering behavior remains documented in the mapping data.`,
    );
  }

  const primaryFlagCountMatchesInventory = prayerFlagsOn === prayerBeadsFound;
  const evidenceCountMatchesInventory = prayerStatusCollected === prayerBeadsFound;
  const unrepresentedCollectedCount = Math.max(0, prayerBeadsFound - prayerFlagsOn);
  const remainingUnattributedCount = Math.max(
    0,
    prayerBeadsFound - prayerStatusCollected,
  );
  const prayerEvidenceDetails =
    prayerFlagsUnknown === 0 && primaryFlagCountMatchesInventory
      ? `All ${prayerLocations.length} primary Prayer Bead pickup/shop flags decode, and their ${prayerFlagsOn} ON / ${prayerFlagsOff} OFF split matches the inventory-derived total. ON means collected and OFF means missing for these verified persistent flags.`
      : evidenceCountMatchesInventory
        ? `Primary flags identify ${prayerFlagsOn} collected locations, and verified secondary evidence accounts for the remaining ${prayerSecondaryItemLotAttributed} collected locations needed to match the inventory-derived total.`
        : "Primary and secondary location evidence does not reconcile with the inventory-derived Prayer Bead total for this save.";
  const prayerReconciliation = {
    reconciled: evidenceCountMatchesInventory,
    offPrimaryFlagsAreDefiniteMissing,
    inventoryDerivedFound: prayerBeadsFound,
    inventoryDerivedMissing: prayerBeadsMissing,
    primaryFlagsOn: prayerFlagsOn,
    primaryFlagsOff: prayerFlagsOff,
    primaryFlagsUnknown: prayerFlagsUnknown,
    unrepresentedCollectedCount,
    knownCollectedByEvidence: prayerStatusCollected,
    knownMissingByEvidence: prayerStatusMissing,
    unknownByEvidence: prayerStatusUnknown,
    attributedByPrimaryFlags: prayerFlagsOn,
    attributedBySecondaryItemLotFlags: prayerSecondaryItemLotAttributed,
    remainingUnattributedCount,
    matchesInventoryDerivedCountAfterSecondaryEvidence: evidenceCountMatchesInventory,
    prayerNecklacesIncludedInDerivedTotal: true,
    openEvidenceSignals: [
      "primaryPickupOrShopFlag",
      "secondaryItemLotFlag",
      "offeringBoxFlag",
      "inventoryEvidence",
    ],
    details: prayerEvidenceDetails,
  };
  const prayerFlagSummary = {
    mappedLocations: prayerLocations.length,
    onByPrimaryFlags: prayerFlagsOn,
    offByPrimaryFlags: prayerFlagsOff,
    unknownByPrimaryFlags: prayerFlagsUnknown,
    collectedByEventFlags: prayerFlagsOn,
    collectedByLocationStatus: prayerStatusCollected,
    collectedByEvidence: prayerStatusCollected,
    missingByEvidence: prayerStatusMissing,
    unknownByEvidence: prayerStatusUnknown,
    definitelyMissingByLocationStatus: prayerStatusMissing,
    matchesInventoryDerivedCount: primaryFlagCountMatchesInventory,
    matchesInventoryDerivedCountAfterSecondaryEvidence: evidenceCountMatchesInventory,
    offPrimaryFlagsAreDefiniteMissing,
    details: prayerEvidenceDetails,
  };

  if (!prayerFlagSummary.matchesInventoryDerivedCountAfterSecondaryEvidence) {
    warnings.push(
      "Prayer Bead evidence signals do not reconcile with the inventory-derived Prayer Bead count in this save; exact location statuses remain unknown where attribution is unresolved.",
    );
  }
  if (
    gourdLocations.filter((location) => location.status === "collected").length !==
    gourdSeedsFound
  ) {
    warnings.push(
      "Gourd Seed location evidence does not reconcile with the inventory-derived Gourd Seed count in this save; the category total uses inventory progression while exact location attribution remains incomplete.",
    );
  }

  return {
    file: fileName,
    sha256: await sha256Hex(buffer),
    container: {
      format: "BND4",
      entries,
      activeSlot: slotName,
    },
    inventory: {
      healingGourdUses,
      unusedGourdSeeds,
      unusedPrayerBeads,
      prayerNecklaces,
    },
    eventFlags: {
      layout: eventLayout,
      mappedStates: flagStates,
    },
    bosses: {
      coverage: data.bosses.coverage,
      statusPolicy: data.bosses.statusPolicy,
      entities: bossEntities,
      summary: bossSummary,
      memoryItems: memoryItemsFound,
      unresolved: data.bosses.unresolved,
    },
    prayerBeads: {
      total: data.prayerBeads.total,
      coverage: data.prayerBeads.coverage,
      locations: prayerLocations.map((location) => compactLocation(location)),
      entities: prayerLocations.map((location) => prayerLocationEntity(location)),
      summary: prayerSummary,
      flagStateSummary: prayerFlagSummary,
      reconciliation: prayerReconciliation,
      ...(prayerAttribution.attribution === null
        ? {}
        : { locationAttribution: prayerAttribution.attribution }),
      unresolved: data.prayerBeads.unresolved,
    },
    gourdSeeds: {
      total: data.gourdSeeds.total,
      locations: gourdLocations.map((location) => compactLocation(location)),
      entities: gourdLocations.map((location) => gourdLocationEntity(location)),
      summary: gourdSummary,
      confirmedMissingLocations: knownGourdMissing.map((location) =>
        compactLocation(location),
      ),
      unresolvedShopCandidates: shopGourdUnknown.map((location) =>
        compactLocation(location),
      ),
      shopSeedInference,
      ...(gourdAttribution.attribution === null
        ? {}
        : { locationAttribution: gourdAttribution.attribution }),
    },
    prosthetics: {
      coverage: data.prosthetics.coverage,
      statusPolicy: data.prosthetics.statusPolicy,
      entities: prostheticEntities,
      summary: prostheticSummary,
      unresolved: data.prosthetics.unresolved,
    },
    prostheticUpgrades: {
      coverage: data.prostheticUpgrades.coverage,
      statusPolicy: data.prostheticUpgrades.statusPolicy,
      upgradeSourcePolicy: data.prostheticUpgrades.upgradeSourcePolicy,
      entities: prostheticUpgradeEntities,
      summary: prostheticUpgradeSummary,
      unresolved: data.prostheticUpgrades.unresolved,
    },
    skills: {
      coverage: data.skills.coverage,
      statusPolicy: data.skills.statusPolicy,
      entities: skillEntities,
      summary: skillSummary,
      unresolved: data.skills.unresolved,
    },
    keyItems: {
      coverage: data.keyItems.coverage,
      statusPolicy: data.keyItems.statusPolicy,
      entities: keyItemEntities,
      summary: keyItemSummary,
      unresolved: data.keyItems.unresolved,
    },
    endings: {
      coverage: data.endings.coverage,
      statusPolicy: data.endings.statusPolicy,
      entities: endingEntities,
      summary: endingSummary,
      unresolved: data.endings.unresolved,
    },
    derivedCounts,
    warnings,
    sourcesUsed: SOURCES_USED,
  };
}

export function legacyReport(result: AnyRecord): AnyRecord {
  const gourd = result.gourdSeeds;
  const bosses = result.bosses.memoryItems;
  return {
    file: result.file,
    sha256: result.sha256,
    active_slot: result.container.activeSlot,
    sources_used: result.sourcesUsed,
    event_flag_reader: {
      record_id: result.eventFlags.layout.recordId,
      record_version: result.eventFlags.layout.recordVersion,
      record_data_offset_hex: result.eventFlags.layout.recordDataOffsetHex,
      page_size_hex: result.eventFlags.layout.pageSizeHex,
      bit_order: result.eventFlags.layout.bitOrder,
      status: result.eventFlags.layout.scope,
    },
    derived_counts: result.derivedCounts,
    gourd_seed_locations: gourd.locations,
    gourd_seed_summary: {
      confirmed_missing_locations: gourd.confirmedMissingLocations,
      shop_seed_inference: gourd.shopSeedInference,
      unresolved_shop_candidates: gourd.unresolvedShopCandidates,
      plain_english:
        gourd.confirmedMissingLocations.length === 0
          ? "All Gourd Seeds are collected."
          : `Confirmed missing: ${gourd.confirmedMissingLocations
              .map((location: AnyRecord) => location.name)
              .join(" and ")}.`,
    },
    prayer_bead_sample_flags: result.prayerBeads.locations,
    boss_memory_items_found: bosses
      .filter((boss: AnyRecord) => boss.status === "found")
      .map((boss: AnyRecord) => boss.name),
    limitations: result.warnings,
    parseSekiroSaveShape: pickExisting(result, [
      "inventory",
      "eventFlags",
      "bosses",
      "prayerBeads",
      "gourdSeeds",
      "prosthetics",
      "prostheticUpgrades",
      "skills",
      "keyItems",
      "endings",
    ]),
  };
}

export async function analyzeSekiroSave(
  buffer: ArrayBuffer,
  data: SekiroStaticData,
  options: AnalyzeSekiroOptions = {},
): Promise<AnyRecord> {
  return legacyReport(await parseSekiroSaveShape(buffer, data, options));
}
