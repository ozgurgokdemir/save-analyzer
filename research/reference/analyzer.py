#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
from typing import Any

REFERENCE_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = REFERENCE_DIR.parent
ROOT = RESEARCH_DIR.parent
SAVE = RESEARCH_DIR / "fixtures" / "S0000.sl2"
DATA_DIR = ROOT / "data" / "sekiro"
REPORT = RESEARCH_DIR / "reports" / "exact_location_report.json"

# Confidence casing is intentionally split between two layers:
# source/research evidence keeps title case, while normalized entity and rule
# confidence values use lowercase for API-shaped output.
SOURCE_CONFIDENCE_VERIFIED = "Verified"
SOURCE_CONFIDENCE_PROBABLE = "Probable"
SOURCE_CONFIDENCE_UNKNOWN = "Unknown"
NORMALIZED_CONFIDENCE_VALUES = {"verified", "probable", "unknown"}

# Inventory ownership is reverse-engineered from USER_DATA000. Goods records are
# found by raw byte scanning because a complete inventory table boundary is not
# known yet.
INVENTORY_MIRROR_PREFIX_HIGH_BYTE = 0xB0
INVENTORY_QUANTITY_MIN = 0
INVENTORY_QUANTITY_MAX = 999
WEAPON_INVENTORY_RECORD_PREFIX = b"\x80\x80"
WEAPON_INVENTORY_QUANTITY = 1


def load_json(name: str) -> dict[str, Any]:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8-sig"))


EVENT_LAYOUT = load_json("event-flag-layout.json")["layouts"][0]
EVENT_FLAG_BASE = EVENT_LAYOUT["baseOffset"]
EVENT_FLAG_INDEX_MODULO = EVENT_LAYOUT.get("bitIndexModulo")


def parse_bnd4(data: bytes) -> list[dict[str, Any]]:
    if data[:4] != b"BND4":
        raise ValueError("Not a BND4 container")

    count = int.from_bytes(data[12:16], "little")
    entries: list[dict[str, Any]] = []
    for index in range(count):
        record_offset = 0x40 + index * 0x20
        if record_offset + 0x20 > len(data):
            raise ValueError(f"BND4 entry table is truncated at index {index}")

        size = int.from_bytes(data[record_offset + 8 : record_offset + 12], "little")
        data_offset = int.from_bytes(
            data[record_offset + 16 : record_offset + 20], "little"
        )
        name_offset = int.from_bytes(
            data[record_offset + 20 : record_offset + 24], "little"
        )

        if data_offset + size > len(data):
            raise ValueError(f"BND4 entry {index} data exceeds file bounds")
        if name_offset >= len(data):
            raise ValueError(f"BND4 entry {index} name offset exceeds file bounds")

        cursor = name_offset
        parts: list[bytes] = []
        while cursor + 1 < len(data) and data[cursor : cursor + 2] != b"\0\0":
            parts.append(data[cursor : cursor + 2])
            cursor += 2
        name = b"".join(parts).decode("utf-16le", errors="replace")

        entries.append(
            {
                "index": index,
                "name": name,
                "offset": data_offset,
                "size": size,
            }
        )

    return entries


def get_user_slot(data: bytes, entries: list[dict[str, Any]], name: str) -> bytes:
    entry = next((entry for entry in entries if entry["name"] == name), None)
    if entry is None:
        raise ValueError(f"Missing BND4 entry {name}")
    return data[entry["offset"] : entry["offset"] + entry["size"]]


def event_flag_bit_index(event_flag: int) -> int:
    if EVENT_FLAG_INDEX_MODULO:
        return event_flag % EVENT_FLAG_INDEX_MODULO
    return event_flag


def read_event_flag(slot: bytes, event_flag: int | None) -> bool | None:
    if event_flag is None:
        return None
    bit_index = event_flag_bit_index(event_flag)
    byte_offset = EVENT_FLAG_BASE + bit_index // 8
    if byte_offset >= len(slot):
        return None
    return bool((slot[byte_offset] >> (bit_index % 8)) & 1)


def find_item_records(slot: bytes, item_hex: str) -> list[dict[str, Any]]:
    needle = bytes.fromhex(item_hex)
    records: list[dict[str, Any]] = []
    start = 0
    while True:
        offset = slot.find(needle, start)
        if offset < 0:
            break
        qty = (
            int.from_bytes(slot[offset + 4 : offset + 8], "little")
            if offset + 8 <= len(slot)
            else None
        )
        records.append(
            {
                "offset": offset,
                "offsetHex": hex(offset),
                "qtyAfterId": qty,
                "hasInventoryMirrorPrefix": has_inventory_mirror_prefix(
                    slot, offset, needle
                ),
            }
        )
        start = offset + 1
    return records


def has_inventory_mirror_prefix(slot: bytes, offset: int, item_id: bytes) -> bool:
    if offset < 4:
        return False
    # Inventory records observed in USER_DATA000 often store an adjacent mirror ID
    # with the high byte set to 0xB0 immediately before the real 0x40 item ID.
    expected = item_id[:3] + bytes([INVENTORY_MIRROR_PREFIX_HIGH_BYTE])
    return slot[offset - 4 : offset] == expected


def sane_quantity(value: int | None) -> bool:
    return (
        value is not None
        and INVENTORY_QUANTITY_MIN <= value <= INVENTORY_QUANTITY_MAX
    )


def read_inventory_quantity(slot: bytes, item_hex: str) -> int:
    records = find_item_records(slot, item_hex)
    preferred = [
        record
        for record in records
        if record["hasInventoryMirrorPrefix"] and sane_quantity(record["qtyAfterId"])
    ]
    if preferred:
        return preferred[0]["qtyAfterId"]

    fallback = [record for record in records if sane_quantity(record["qtyAfterId"])]
    return fallback[0]["qtyAfterId"] if fallback else 0


def has_item(slot: bytes, item_hex: str) -> bool:
    return bool(find_item_records(slot, item_hex))


def find_weapon_inventory_records(
    slot: bytes, item_hex: str
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in find_item_records(slot, item_hex):
        offset = record["offset"]
        if (
            record["qtyAfterId"] == WEAPON_INVENTORY_QUANTITY
            and offset >= 2
            and slot[offset - 2 : offset] == WEAPON_INVENTORY_RECORD_PREFIX
        ):
            records.append(
                {
                    "offset": offset,
                    "offsetHex": record["offsetHex"],
                    "qtyAfterId": record["qtyAfterId"],
                }
            )
    return records


def flag_signal_status(state: bool | None) -> str:
    if state is None:
        return "unknown"
    return "on" if state else "off"


def event_flag_signal(
    slot: bytes,
    event_flag: int | None,
    *,
    source: str,
    details: str,
) -> dict[str, Any]:
    state = read_event_flag(slot, event_flag)
    confidence = (
        SOURCE_CONFIDENCE_VERIFIED
        if event_flag is not None and state is not None
        else SOURCE_CONFIDENCE_UNKNOWN
    )
    return {
        "eventFlag": event_flag,
        "state": state,
        "status": flag_signal_status(state),
        "source": source,
        "details": details,
        "confidence": confidence,
    }


def unmapped_signal(details: str) -> dict[str, Any]:
    return {
        "eventFlag": None,
        "state": None,
        "status": "unknown",
        "details": details,
        "confidence": SOURCE_CONFIDENCE_UNKNOWN,
    }


def analyze_generic_evidence(slot: bytes, evidence: dict[str, Any]) -> dict[str, Any]:
    evidence_type = evidence.get("type")
    if evidence_type == "event_flag":
        flag = evidence.get("flag")
        state = read_event_flag(slot, flag)
        state_confidence = (
            "verified" if flag is not None and state is not None else "unknown"
        )
        return {
            **evidence,
            "state": state,
            "status": flag_signal_status(state),
            "stateConfidence": state_confidence,
            "confidence": evidence.get("confidence", state_confidence),
        }
    if evidence_type == "inventory_item":
        item_id_hex = evidence.get("itemIdHex")
        records = find_item_records(slot, item_id_hex) if item_id_hex else []
        state = bool(records) if item_id_hex else None
        return {
            **evidence,
            "state": state,
            "status": "present" if state else "absent" if state is False else "unknown",
            "recordCount": len(records),
            "records": records,
            "confidence": evidence.get("confidence", "unknown"),
        }
    if evidence_type == "inventory_weapon":
        item_id_hex = evidence.get("itemIdHex")
        records = (
            find_weapon_inventory_records(slot, item_id_hex)
            if item_id_hex
            else []
        )
        state = bool(records) if item_id_hex else None
        confidence = evidence.get(
            "confidence",
            "verified" if state is not None else "unknown",
        )
        return {
            **evidence,
            "state": state,
            "status": "present" if state else "absent" if state is False else "unknown",
            "recordCount": len(records),
            "records": records,
            "confidence": confidence,
        }
    return {
        **evidence,
        "state": None,
        "status": "unknown",
        "confidence": "unknown",
    }


def generic_rule_matches(
    evidence_by_id: dict[str, dict[str, Any]], rule: dict[str, Any]
) -> bool:
    return all(
        evidence_by_id.get(condition.get("evidenceId"), {}).get("state")
        is condition.get("state")
        for condition in rule.get("when", [])
    )


def canonical_confidence(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.lower()
        if normalized in NORMALIZED_CONFIDENCE_VALUES:
            return normalized
    return "unknown"


def normalized_notes(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def ensure_common_entity_fields(
    entity: dict[str, Any],
    *,
    category: str | None = None,
    evidence: list[dict[str, Any]] | None = None,
    acquisition_metadata: dict[str, Any] | None = None,
    notes: list[Any] | None = None,
) -> dict[str, Any]:
    normalized = {**entity}
    if category is not None and "category" not in normalized:
        normalized["category"] = category
    if "name" not in normalized:
        normalized["name"] = normalized.get("id")

    normalized["evidence"] = evidence if evidence is not None else normalized.get(
        "evidence",
        [],
    )

    if acquisition_metadata is None:
        acquisition_metadata = normalized.get(
            "acquisitionMetadata",
            normalized.get("sourceLocation", {}),
        )
    normalized["acquisitionMetadata"] = acquisition_metadata or {}

    if notes is None:
        notes = normalized.get("notes")
        if notes is None and isinstance(normalized["acquisitionMetadata"], dict):
            notes = normalized["acquisitionMetadata"].get("notes")
    normalized["notes"] = normalized_notes(notes)
    return normalized


def analyze_generic_entity(slot: bytes, entity: dict[str, Any]) -> dict[str, Any]:
    evidence = [
        analyze_generic_evidence(slot, evidence)
        for evidence in entity.get("evidence", [])
    ]
    evidence_by_id = {evidence["id"]: evidence for evidence in evidence}
    matched_rule = next(
        (
            rule
            for rule in entity.get("statusRules", [])
            if generic_rule_matches(evidence_by_id, rule)
        ),
        None,
    )
    status = matched_rule["status"] if matched_rule else "unknown"
    confidence = matched_rule["confidence"] if matched_rule else "unknown"
    metadata = {
        key: value
        for key, value in entity.items()
        if key not in {"evidence", "statusRules"}
    }
    return ensure_common_entity_fields(
        {
            **metadata,
            "status": status,
            "confidence": confidence,
            "evidence": evidence,
        }
    )


def analyze_generic_entities(
    slot: bytes, entities: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [analyze_generic_entity(slot, entity) for entity in entities]


def analyze_key_item_entities(
    slot: bytes, entities: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    analyzed = analyze_generic_entities(slot, entities)
    for entity in analyzed:
        ownership_evidence = entity.get("evidence", [])
        entity["ownershipEvidence"] = ownership_evidence
        entity.update(
            ensure_common_entity_fields(
                entity,
                evidence=ownership_evidence,
                acquisition_metadata=entity.get("acquisitionMetadata", {}),
            )
        )
    return analyzed


def compact_key_item_reference(entity: dict[str, Any]) -> dict[str, Any]:
    keys = [
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
    ]
    return {key: entity.get(key) for key in keys if key in entity}


def generic_status_summary(
    entities: list[dict[str, Any]],
    status_keys: list[str],
) -> dict[str, int]:
    by_status = {
        key: sum(1 for entity in entities if entity["status"] == key)
        for key in status_keys
    }
    return {
        "total": len(entities),
        **by_status,
        "byStatus": by_status,
    }


def analyze_ending_requirement(
    evidence_by_id: dict[str, dict[str, Any]],
    requirement: dict[str, Any],
) -> dict[str, Any]:
    evidence = evidence_by_id.get(requirement.get("evidenceId"))
    state = evidence.get("state") if evidence else None
    status = "present" if state is True else "missing" if state is False else "unknown"
    return {
        **requirement,
        "state": state,
        "status": status,
        "confidence": evidence.get("confidence", "unknown") if evidence else "unknown",
    }


def ending_missing_required_items(
    required_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        item
        for item in required_items
        if item.get("required", True) and item["status"] == "missing"
    ]


def ending_unknown_required_items(
    required_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        item
        for item in required_items
        if item.get("required", True) and item["status"] == "unknown"
    ]


def ending_has_verified_completion(completed_evidence: list[dict[str, Any]]) -> bool:
    return any(
        evidence.get("state") is True
        and evidence.get("confidence") == "verified"
        and evidence.get("type") == "event_flag"
        for evidence in completed_evidence
    )


def analyze_ending_block_evidence(
    evidence_by_id: dict[str, dict[str, Any]],
    block_rule: dict[str, Any],
) -> dict[str, Any]:
    state = generic_rule_matches(evidence_by_id, block_rule)
    confidence = block_rule.get("confidence", "unknown")
    permanently_blocked = block_rule.get("permanentlyBlocked")
    is_verified_block = (
        state is True
        and confidence == "verified"
        and permanently_blocked is True
    )
    return {
        **block_rule,
        "state": state,
        "status": (
            "verified_block"
            if is_verified_block
            else "potential_block"
            if state
            else "not_present"
        ),
        "statusDriving": is_verified_block,
        "conditionEvidence": [
            evidence_by_id.get(condition.get("evidenceId"))
            for condition in block_rule.get("when", [])
            if evidence_by_id.get(condition.get("evidenceId")) is not None
        ],
    }


def ending_verified_block(block_evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (
            evidence
            for evidence in block_evidence
            if evidence.get("statusDriving") is True
        ),
        None,
    )


def ending_potential_block(block_evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (
            evidence
            for evidence in block_evidence
            if evidence.get("state") is True
            and evidence.get("statusDriving") is not True
        ),
        None,
    )


def analyze_ending_evidence(
    slot: bytes,
    evidence: dict[str, Any],
    key_item_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if evidence.get("type") != "key_item":
        return analyze_generic_evidence(slot, evidence)

    key_item = key_item_by_id.get(evidence.get("keyItemId"))
    if key_item is None:
        return {
            **evidence,
            "state": None,
            "status": "unknown",
            "confidence": "unknown",
            "details": "Referenced key item is not mapped in key-items.json.",
        }

    if key_item["status"] == "collected":
        state = True
        status = "present"
    elif key_item["status"] == "missing":
        state = False
        status = "absent"
    else:
        state = None
        status = "unknown"

    return {
        **evidence,
        "state": state,
        "status": status,
        "confidence": key_item.get("confidence", "unknown"),
        "itemIdHex": key_item.get("itemIdHex"),
        "keyItem": compact_key_item_reference(key_item),
    }


def analyze_ending_route(
    slot: bytes,
    ending: dict[str, Any],
    key_item_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    completion_source = ending.get(
        "completionEvidence",
        ending.get("completedEndingEvidence", []),
    )
    availability_source = ending.get(
        "availabilityEvidence",
        ending.get("routeAvailabilityEvidence", []),
    )
    block_rules = ending.get("blockRules", ending.get("blockingRules", []))
    completion_evidence = [
        analyze_ending_evidence(slot, evidence, key_item_by_id)
        for evidence in completion_source
    ]
    availability_evidence = [
        analyze_ending_evidence(slot, evidence, key_item_by_id)
        for evidence in availability_source
    ]
    evidence_by_id = {
        evidence["id"]: evidence
        for evidence in [*completion_evidence, *availability_evidence]
    }
    required_items = [
        analyze_ending_requirement(evidence_by_id, requirement)
        for requirement in ending.get("requiredItems", [])
    ]
    missing_items = ending_missing_required_items(required_items)
    unknown_items = ending_unknown_required_items(required_items)
    block_evidence = [
        analyze_ending_block_evidence(evidence_by_id, rule)
        for rule in block_rules
    ]
    verified_block = ending_verified_block(block_evidence)
    potential_block = ending_potential_block(block_evidence)

    if ending_has_verified_completion(completion_evidence):
        status = "completed"
        confidence = "verified"
        availability_state = "completed"
        permanently_blocked = False
        status_details = "A verified ending completion flag is ON in this save."
    elif verified_block:
        status = "blocked"
        confidence = "verified"
        availability_state = verified_block.get("blockType", "route_choice")
        permanently_blocked = True
        status_details = verified_block.get(
            "details",
            "Verified permanent block evidence is present in this save.",
        )
    elif potential_block:
        status = "unknown"
        confidence = "unknown"
        availability_state = "potential_block_unverified"
        permanently_blocked = None
        status_details = (
            "Potential permanent block evidence is present, but its permanence "
            "is not verified strongly enough to mark this ending blocked."
        )
    elif missing_items:
        status = "incomplete"
        confidence = ending.get("routeRequirementConfidence", "probable")
        availability_state = "missing_requirements"
        permanently_blocked = False
        missing_names = ", ".join(item["name"] for item in missing_items)
        status_details = (
            "Route is still possible by currently verified evidence, but the "
            f"save is missing required item(s): {missing_names}."
        )
    elif unknown_items:
        status = "unknown"
        confidence = "unknown"
        availability_state = "unknown_requirements"
        permanently_blocked = None
        status_details = (
            "One or more required route item signals could not be read from this save."
        )
    elif required_items:
        status = "available"
        confidence = ending.get("routeRequirementConfidence", "probable")
        availability_state = "requirements_satisfied"
        permanently_blocked = False
        status_details = (
            "All currently mapped required route items are present, and no verified "
            "permanent block evidence is present."
        )
    else:
        status = "unknown"
        confidence = "unknown"
        availability_state = "unmapped"
        permanently_blocked = None
        status_details = "No verified ending status rule is mapped for this route."

    block_reason = (
        verified_block.get("blockType")
        if verified_block
        else potential_block.get("blockType")
        if potential_block
        else None
    )

    metadata = {
        key: value
        for key, value in ending.items()
        if key
        not in {
            "completedEndingEvidence",
            "completionEvidence",
            "routeAvailabilityEvidence",
            "availabilityEvidence",
            "requiredItems",
            "blockingRules",
            "blockRules",
        }
    }
    route_entity = {
        **metadata,
        "status": status,
        "confidence": confidence,
        "statusDetails": status_details,
        "availability": {
            "currentCompletionSelectable": status == "available",
            "state": availability_state,
            "blockReason": block_reason,
            "permanentlyBlocked": permanently_blocked,
            "details": status_details,
        },
        "completionEvidence": completion_evidence,
        "availabilityEvidence": availability_evidence,
        "requiredItems": required_items,
        "missingRequirements": missing_items,
        "unknownRequirements": unknown_items,
        "blockEvidence": block_evidence,
    }
    return ensure_common_entity_fields(
        route_entity,
        evidence=[
            *completion_evidence,
            *availability_evidence,
            *block_evidence,
        ],
        acquisition_metadata=route_entity.get("guidance", {}),
        notes=[status_details],
    )


def analyze_ending_routes(
    slot: bytes,
    endings: list[dict[str, Any]],
    key_item_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        analyze_ending_route(slot, ending, key_item_by_id)
        for ending in endings
    ]


def analyze_locations(slot: bytes, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    analyzed: list[dict[str, Any]] = []
    for location in locations:
        event_flag = location.get("eventFlag")
        if event_flag is None:
            status = "unknown"
            flag_state = None
        else:
            flag_state = read_event_flag(slot, event_flag)
            status = "collected" if flag_state else "missing"

        analyzed.append(
            {
                **location,
                "status": status,
                "eventFlagState": flag_state,
            }
        )
    return analyzed


def prayer_location_status(
    flag_state: bool | None,
    off_primary_flags_are_definite_missing: bool,
    *,
    has_verified_secondary_item_lot: bool,
    has_verified_missing_evidence: bool,
) -> str:
    if flag_state is True:
        return "collected"
    if has_verified_secondary_item_lot:
        return "collected"
    if has_verified_missing_evidence:
        return "missing"
    if flag_state is None:
        return "unknown"
    if off_primary_flags_are_definite_missing:
        return "missing"
    return "unknown"


def prayer_collection_confidence(status: str) -> str:
    if status == "collected":
        return SOURCE_CONFIDENCE_VERIFIED
    if status == "missing":
        return SOURCE_CONFIDENCE_VERIFIED
    return SOURCE_CONFIDENCE_UNKNOWN


def prayer_status_details(
    status: str,
    *,
    collected_by_secondary_item_lot: bool,
    missing_by_evidence: bool,
) -> str:
    if status == "collected":
        if collected_by_secondary_item_lot:
            return (
                "Primary pickup/shop flag is OFF, but a verified secondary "
                "ItemLotParam reward/replacement flag is ON in this save."
            )
        return "Primary pickup/shop flag is ON in this save."
    if status == "missing":
        if missing_by_evidence:
            return (
                "Verified reward/pickup evidence flags for this location are OFF in "
                "this save, and collected-by-evidence already reconciles to the "
                "inventory-derived Prayer Bead total."
            )
        return "Primary pickup/shop flag is OFF and Prayer Bead reconciliation is solved."
    return (
        "Evidence is insufficient to mark this location collected or missing under "
        "the finalized Prayer Bead status model."
    )


def secondary_item_lot_signals(
    slot: bytes, location: dict[str, Any]
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for secondary in location.get("secondaryItemLotFlags", []):
        signals.append(
            {
                **event_flag_signal(
                    slot,
                    secondary.get("eventFlag"),
                    source="secondary ItemLotParam reward/replacement flag",
                    details=secondary.get(
                        "details",
                        "Secondary ItemLotParam row tied to the same source location.",
                    ),
                ),
                "rowId": secondary.get("rowId"),
                "role": secondary.get("role"),
                "awardedItemId": secondary.get("awardedItemId"),
                "mappingConfidence": secondary.get(
                    "mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN
                ),
                "attributionConfidence": secondary.get(
                    "attributionConfidence", SOURCE_CONFIDENCE_UNKNOWN
                ),
                "evidence": secondary.get("evidence", []),
            }
        )
    return signals


def has_verified_secondary_item_lot_collection(
    secondary_signals: list[dict[str, Any]]
) -> bool:
    return any(
        signal.get("state") is True
        and signal.get("attributionConfidence") == "Verified"
        for signal in secondary_signals
    )


def has_verified_secondary_item_lot_missing(
    secondary_signals: list[dict[str, Any]]
) -> bool:
    return bool(secondary_signals) and all(
        signal.get("state") is False
        and signal.get("confidence") == "Verified"
        and signal.get("attributionConfidence") == "Verified"
        for signal in secondary_signals
    )


def missing_evidence_signal(
    primary_signal: dict[str, Any],
    item_lot_signal: dict[str, Any],
    shop_signal: dict[str, Any],
    secondary_signals: list[dict[str, Any]],
    location: dict[str, Any],
) -> dict[str, Any]:
    semantics = location.get("primaryFlagSemantics")
    if semantics is None:
        return {
            "rule": None,
            "state": None,
            "status": "unknown",
            "confidence": SOURCE_CONFIDENCE_UNKNOWN,
            "details": (
                "No verified missing-evidence rule is mapped for this location."
            ),
        }

    rule = semantics.get("missingEvidenceRule")
    if rule == "primary_and_secondary_item_lot_flags_off":
        verified = (
            item_lot_signal.get("state") is False
            and item_lot_signal.get("confidence") == "Verified"
            and has_verified_secondary_item_lot_missing(secondary_signals)
        )
    elif rule == "shop_purchase_flag_off":
        verified = (
            shop_signal.get("state") is False
            and shop_signal.get("confidence") == "Verified"
        )
    else:
        verified = False

    return {
        "rule": rule,
        "state": verified,
        "status": "missing" if verified else "not_satisfied",
        "confidence": (
            SOURCE_CONFIDENCE_VERIFIED
            if verified
            else SOURCE_CONFIDENCE_UNKNOWN
        ),
        "primaryFlag": primary_signal,
        "secondaryItemLotFlags": secondary_signals,
        "primaryFlagSemantics": semantics,
        "details": semantics.get(
            "details",
            "Verified evidence rule for determining missing state.",
        ),
    }


def analyze_prayer_locations(
    slot: bytes,
    locations: list[dict[str, Any]],
    inventory_evidence: dict[str, Any],
    *,
    off_primary_flags_are_definite_missing: bool,
) -> list[dict[str, Any]]:
    analyzed: list[dict[str, Any]] = []
    for location in locations:
        event_flag = location.get("eventFlag")
        flag_state = read_event_flag(slot, event_flag)
        secondary_item_lot = secondary_item_lot_signals(slot, location)
        collected_by_secondary_item_lot = has_verified_secondary_item_lot_collection(
            secondary_item_lot
        )
        primary_signal = event_flag_signal(
            slot,
            event_flag,
            source="primary Prayer Bead mapping",
            details=(
                "Current primary collection flag from the mapping data. For shop rows, "
                "this is the ShopLineupParam purchase flag."
            ),
        )

        item_lot_row_id = location.get("itemLotParamRowId")
        if item_lot_row_id is None:
            item_lot_signal = unmapped_signal(
                "No ItemLotParam row is mapped for this Prayer Bead."
            )
        else:
            item_lot_signal = {
                **event_flag_signal(
                    slot,
                    event_flag,
                    source="SoulSplitter ItemLotParam pickup flag",
                    details=(
                        "ItemLotParam row maps to this pickup/award flag. This is not "
                        "an independent aggregate inventory signal."
                    ),
                ),
                "rowId": item_lot_row_id,
                "secondary": secondary_item_lot,
            }
            if not secondary_item_lot:
                item_lot_signal["secondary"] = []

        shop_row_id = location.get("shopLineupParamRowId")
        if shop_row_id is None:
            shop_signal = unmapped_signal(
                "No ShopLineupParam row is mapped for this Prayer Bead."
            )
        else:
            shop_signal = {
                **event_flag_signal(
                    slot,
                    event_flag,
                    source="ShopLineupParam purchase flag",
                    details="ShopLineupParam row event flag for this merchant purchase.",
                ),
                "rowId": shop_row_id,
            }

        missing_evidence = missing_evidence_signal(
            primary_signal,
            item_lot_signal,
            shop_signal,
            secondary_item_lot,
            location,
        )
        missing_by_evidence = missing_evidence["confidence"] == "Verified"
        status = prayer_location_status(
            flag_state,
            off_primary_flags_are_definite_missing,
            has_verified_secondary_item_lot=collected_by_secondary_item_lot,
            has_verified_missing_evidence=missing_by_evidence,
        )

        analyzed.append(
            {
                **location,
                "status": status,
                "statusDetails": prayer_status_details(
                    status,
                    collected_by_secondary_item_lot=collected_by_secondary_item_lot,
                    missing_by_evidence=missing_by_evidence,
                ),
                "eventFlagState": flag_state,
                "primaryPickupFlag": primary_signal,
                "bossDefeatFlag": unmapped_signal(
                    "Separate boss/miniboss defeat flag has not been mapped for this Prayer Bead."
                ),
                "itemLotFlag": item_lot_signal,
                "shopFlag": shop_signal,
                "offeringBoxFlag": unmapped_signal(
                    "Offering Box replacement flag/state has not been mapped for this Prayer Bead."
                ),
                "missingEvidence": missing_evidence,
                "inventoryEvidence": inventory_evidence,
                "confidence": {
                    "locationMapping": location.get(
                        "mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN
                    ),
                    "primaryFlagState": primary_signal["confidence"],
                    "collectionStatus": prayer_collection_confidence(status),
                    "secondaryItemLotAttribution": (
                        SOURCE_CONFIDENCE_VERIFIED
                        if collected_by_secondary_item_lot
                        else SOURCE_CONFIDENCE_UNKNOWN
                    ),
                    "details": prayer_status_details(
                        status,
                        collected_by_secondary_item_lot=collected_by_secondary_item_lot,
                        missing_by_evidence=missing_by_evidence,
                    ),
                },
            }
        )
    return analyzed


def compact_location(location: dict[str, Any]) -> dict[str, Any]:
    keys = [
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
    ]
    return {key: location.get(key) for key in keys if key in location}


def gourd_location_entity(location: dict[str, Any]) -> dict[str, Any]:
    event_flag = location.get("eventFlag")
    evidence_type = (
        "shop_flag"
        if location.get("sourceType") == "shop"
        else "item_lot_flag"
        if location.get("itemLotParamRowId") is not None
        else "event_flag"
    )
    evidence = [
        {
            "id": "eventFlag",
            "type": evidence_type,
            "flag": event_flag,
            "eventFlag": event_flag,
            "state": location.get("eventFlagState"),
            "status": flag_signal_status(location.get("eventFlagState")),
            "confidence": canonical_confidence(
                location.get("mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN)
            ),
            "source": "data/sekiro/gourd-seeds.json",
            "details": (
                "Verified Gourd Seed pickup or shop-purchase event flag for "
                "this current save state."
            ),
        }
    ]
    return ensure_common_entity_fields(
        {
            **compact_location(location),
            "category": "gourd_seed",
            "confidence": canonical_confidence(
                location.get("mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN)
            ),
        },
        evidence=evidence,
        acquisition_metadata={
            "area": location.get("area"),
            "location": location.get("location"),
            "sourceType": location.get("sourceType"),
            "itemLotParamRowId": location.get("itemLotParamRowId"),
            "shopLineupParamRowId": location.get("shopLineupParamRowId"),
            "confidence": canonical_confidence(
                location.get("mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN)
            ),
        },
        notes=[],
    )


def evidence_entry(
    source: dict[str, Any],
    *,
    evidence_id: str,
    evidence_type: str,
) -> dict[str, Any]:
    entry = {**source, "id": evidence_id, "type": evidence_type}
    if "eventFlag" in entry and "flag" not in entry:
        entry["flag"] = entry["eventFlag"]
    entry.setdefault("state", None)
    entry.setdefault("status", "unknown")
    entry.setdefault("confidence", "Unknown")
    return entry


def prayer_location_entity(location: dict[str, Any]) -> dict[str, Any]:
    confidence_details = location.get("confidence", {})
    evidence = [
        evidence_entry(
            location.get("primaryPickupFlag", {}),
            evidence_id="primaryPickupFlag",
            evidence_type="event_flag",
        ),
        evidence_entry(
            location.get("bossDefeatFlag", {}),
            evidence_id="bossDefeatFlag",
            evidence_type="event_flag",
        ),
        evidence_entry(
            location.get("itemLotFlag", {}),
            evidence_id="itemLotFlag",
            evidence_type="item_lot_flag",
        ),
        evidence_entry(
            location.get("shopFlag", {}),
            evidence_id="shopFlag",
            evidence_type="shop_flag",
        ),
        evidence_entry(
            location.get("offeringBoxFlag", {}),
            evidence_id="offeringBoxFlag",
            evidence_type="offering_box_flag",
        ),
        evidence_entry(
            location.get("missingEvidence", {}),
            evidence_id="missingEvidence",
            evidence_type="missing_evidence",
        ),
        evidence_entry(
            location.get("inventoryEvidence", {}),
            evidence_id="inventoryEvidence",
            evidence_type="inventory_summary",
        ),
    ]
    return ensure_common_entity_fields(
        {
            **compact_location(location),
            "category": "prayer_bead",
            "confidence": canonical_confidence(
                confidence_details.get(
                    "collectionStatus", SOURCE_CONFIDENCE_UNKNOWN
                )
            ),
            "confidenceDetails": confidence_details,
        },
        evidence=evidence,
        acquisition_metadata={
            "area": location.get("area"),
            "location": location.get("location"),
            "sourceType": location.get("sourceType"),
            "itemLotParamRowId": location.get("itemLotParamRowId"),
            "shopLineupParamRowId": location.get("shopLineupParamRowId"),
            "confidence": canonical_confidence(
                location.get("mappingConfidence", SOURCE_CONFIDENCE_UNKNOWN)
            ),
        },
        notes=[location.get("statusDetails")] if location.get("statusDetails") else [],
    )


def mapped_event_flags(
    gourd_locations: list[dict[str, Any]], prayer_locations: list[dict[str, Any]]
) -> list[int]:
    flags = {
        location["eventFlag"]
        for location in [*gourd_locations, *prayer_locations]
        if location.get("eventFlag") is not None
    }
    for location in prayer_locations:
        for secondary in location.get("secondaryItemLotFlags", []):
            if secondary.get("eventFlag") is not None:
                flags.add(secondary["eventFlag"])
    return sorted(flags)


def generic_entity_event_flags(entities: list[dict[str, Any]]) -> list[int]:
    flags: set[int] = set()
    for entity in entities:
        for evidence in entity.get("evidence", []):
            if evidence.get("type") == "event_flag" and evidence.get("flag") is not None:
                flags.add(evidence["flag"])
    return sorted(flags)


def parse_sekiro_save(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    entries = parse_bnd4(data)
    slot_name = "USER_DATA000"
    slot = get_user_slot(data, entries, slot_name)

    item_ids = load_json("item-ids.json")
    gourd_data = load_json("gourd-seeds.json")
    prayer_data = load_json("prayer-beads.json")
    boss_data = load_json("bosses.json")
    prosthetic_data = load_json("prosthetics.json")
    prosthetic_upgrade_data = load_json("prosthetic-upgrades.json")
    skill_data = load_json("skills.json")
    key_item_data = load_json("key-items.json")
    ending_data = load_json("endings.json")

    item_by_id = {item["id"]: item for item in item_ids["items"]}
    healing_gourd_uses = read_inventory_quantity(
        slot, item_by_id["healing_gourd"]["itemIdHex"]
    )
    unused_gourd_seeds = read_inventory_quantity(
        slot, item_by_id["gourd_seed"]["itemIdHex"]
    )
    unused_prayer_beads = read_inventory_quantity(
        slot, item_by_id["prayer_bead"]["itemIdHex"]
    )
    prayer_necklaces = sum(
        1 for item_hex in item_ids["prayerNecklaceItemIdsHex"] if has_item(slot, item_hex)
    )

    gourd_seeds_found = healing_gourd_uses - 1 + unused_gourd_seeds
    gourd_seeds_missing = gourd_data["total"] - gourd_seeds_found
    prayer_beads_found = prayer_necklaces * 4 + unused_prayer_beads
    prayer_beads_missing = prayer_data["total"] - prayer_beads_found
    derived_counts = {
        "healingGourdUses": healing_gourd_uses,
        "unusedGourdSeeds": unused_gourd_seeds,
        "gourdSeedsFound": gourd_seeds_found,
        "gourdSeedsMissing": gourd_seeds_missing,
        "prayerNecklaces": prayer_necklaces,
        "unusedPrayerBeads": unused_prayer_beads,
        "prayerBeadsFound": prayer_beads_found,
        "prayerBeadsMissing": prayer_beads_missing,
    }
    prayer_inventory_evidence = {
        "aggregatePrayerBeadsFound": prayer_beads_found,
        "aggregatePrayerBeadsMissing": prayer_beads_missing,
        "prayerNecklaces": prayer_necklaces,
        "unusedPrayerBeads": unused_prayer_beads,
        "exactLocationAttribution": None,
        "confidence": SOURCE_CONFIDENCE_VERIFIED,
        "details": (
            "Aggregate inventory evidence is derived from Prayer Necklace count times four "
            "plus unused Prayer Bead quantity. It proves total collected count for this save "
            "but does not identify any exact location."
        ),
    }
    off_primary_flags_are_definite_missing = False
    gourd_locations = analyze_locations(slot, gourd_data["locations"])
    prayer_locations = analyze_prayer_locations(
        slot,
        prayer_data["locations"],
        prayer_inventory_evidence,
        off_primary_flags_are_definite_missing=off_primary_flags_are_definite_missing,
    )
    prayer_flags_on = sum(
        1 for location in prayer_locations if location["eventFlagState"] is True
    )
    prayer_flags_off = sum(
        1 for location in prayer_locations if location["eventFlagState"] is False
    )
    prayer_flags_unknown = sum(
        1 for location in prayer_locations if location["eventFlagState"] is None
    )
    prayer_status_missing = sum(
        1 for location in prayer_locations if location["status"] == "missing"
    )
    prayer_status_collected = sum(
        1 for location in prayer_locations if location["status"] == "collected"
    )
    prayer_status_unknown = sum(
        1 for location in prayer_locations if location["status"] == "unknown"
    )
    prayer_secondary_item_lot_attributed = sum(
        1
        for location in prayer_locations
        if location["eventFlagState"] is not True
        and has_verified_secondary_item_lot_collection(
            location["itemLotFlag"].get("secondary", [])
        )
    )
    prayer_summary = generic_status_summary(
        prayer_locations,
        ["collected", "missing", "unknown"],
    )

    known_gourd_missing = [
        location for location in gourd_locations if location["status"] == "missing"
    ]
    shop_gourd = [
        location for location in gourd_locations if location.get("sourceType") == "shop"
    ]
    shop_gourd_collected = [
        location for location in shop_gourd if location["status"] == "collected"
    ]
    shop_gourd_missing = [
        location for location in shop_gourd if location["status"] == "missing"
    ]
    shop_gourd_unknown = [
        location for location in shop_gourd if location["status"] == "unknown"
    ]
    gourd_summary = generic_status_summary(
        gourd_locations,
        ["collected", "missing", "unknown"],
    )

    shop_seed_inference = {
        "shopSeedsTotal": len(shop_gourd),
        "shopSeedsFoundByEventFlags": len(shop_gourd_collected),
        "shopSeedsMissingByEventFlags": len(shop_gourd_missing),
        "shopSeedsUnknown": len(shop_gourd_unknown),
        "confidence": (
            SOURCE_CONFIDENCE_VERIFIED
            if not shop_gourd_unknown
            else SOURCE_CONFIDENCE_PROBABLE
        ),
        "details": (
            "ShopLineupParam event flags resolve both merchant Gourd Seeds in this save."
            if not shop_gourd_unknown
            else "Derived from total Gourd Seed count minus verified non-shop item-lot flags. This does not identify which shop seed is missing."
        ),
    }

    mapped_flags = [
        *mapped_event_flags(gourd_locations, prayer_locations),
        *generic_entity_event_flags(boss_data.get("bosses", [])),
    ]
    flag_states = {
        str(flag): read_event_flag(slot, flag)
        for flag in sorted(set(mapped_flags))
    }

    boss_entities = analyze_generic_entities(slot, boss_data.get("bosses", []))
    boss_summary = generic_status_summary(
        boss_entities,
        ["defeated", "not_defeated", "unknown"],
    )
    boss_summary["notDefeated"] = boss_summary["not_defeated"]
    prosthetic_entities = analyze_generic_entities(
        slot, prosthetic_data.get("prosthetics", [])
    )
    prosthetic_summary = generic_status_summary(
        prosthetic_entities,
        ["collected", "missing", "unknown"],
    )
    prosthetic_upgrade_entities = analyze_generic_entities(
        slot, prosthetic_upgrade_data.get("upgrades", [])
    )
    prosthetic_upgrade_summary = generic_status_summary(
        prosthetic_upgrade_entities,
        ["unlocked", "missing", "unknown"],
    )
    skill_entities = analyze_generic_entities(slot, skill_data.get("skills", []))
    skill_summary = generic_status_summary(
        skill_entities,
        ["unlocked", "missing", "unknown"],
    )
    key_item_entities = analyze_key_item_entities(
        slot, key_item_data.get("items", [])
    )
    key_item_summary = generic_status_summary(
        key_item_entities,
        ["collected", "missing", "unknown"],
    )
    key_item_by_id = {entity["id"]: entity for entity in key_item_entities}
    ending_entities = analyze_ending_routes(
        slot, ending_data.get("endings", []), key_item_by_id
    )
    ending_summary = generic_status_summary(
        ending_entities,
        ["completed", "available", "incomplete", "blocked", "unknown"],
    )
    memory_items_found = [
        {
            "id": item["id"],
            "name": item["name"],
            "itemIdHex": item["itemIdHex"],
            "status": "found" if has_item(slot, item["itemIdHex"]) else "not_found",
            "confidence": SOURCE_CONFIDENCE_PROBABLE,
        }
        for item in boss_data["memoryItemIds"]
    ]

    warnings: list[str] = []
    if shop_gourd_unknown:
        warnings.append(
            "One or more Gourd Seed shop rows still have unknown purchase state because their ShopLineupParam event flags are not verified."
        )
    if "complete" not in prayer_data["coverage"]:
        warnings.append(
            f"Prayer Bead coverage is {prayer_data['coverage']}; unresolved replacement or row-ordering behavior remains documented in the mapping data."
        )

    primary_flag_count_matches_inventory = prayer_flags_on == prayer_beads_found
    evidence_count_matches_inventory = prayer_status_collected == prayer_beads_found
    unrepresented_collected_count = max(0, prayer_beads_found - prayer_flags_on)
    remaining_unattributed_count = max(0, prayer_beads_found - prayer_status_collected)
    prayer_reconciliation = {
        "reconciled": evidence_count_matches_inventory,
        "offPrimaryFlagsAreDefiniteMissing": off_primary_flags_are_definite_missing,
        "inventoryDerivedFound": prayer_beads_found,
        "inventoryDerivedMissing": prayer_beads_missing,
        "primaryFlagsOn": prayer_flags_on,
        "primaryFlagsOff": prayer_flags_off,
        "primaryFlagsUnknown": prayer_flags_unknown,
        "unrepresentedCollectedCount": unrepresented_collected_count,
        "knownCollectedByEvidence": prayer_status_collected,
        "knownMissingByEvidence": prayer_status_missing,
        "unknownByEvidence": prayer_status_unknown,
        "attributedByPrimaryFlags": prayer_flags_on,
        "attributedBySecondaryItemLotFlags": prayer_secondary_item_lot_attributed,
        "remainingUnattributedCount": remaining_unattributed_count,
        "matchesInventoryDerivedCountAfterSecondaryEvidence": (
            evidence_count_matches_inventory
        ),
        "prayerNecklacesIncludedInDerivedTotal": True,
        "openEvidenceSignals": [
            "bossDefeatFlag",
            "itemLotFlag",
            "shopFlag",
            "offeringBoxFlag",
            "inventoryEvidence",
        ],
        "details": (
            "The save carries more Prayer Beads by inventory/progression evidence than "
            "the mapped primary pickup/shop flags show as ON. Verified secondary "
            "ItemLotParam reward/replacement flags currently attribute the 11-bead "
            "primary-flag gap for this save. The remaining 14 locations have verified "
            "reward/pickup or shop-purchase evidence flags OFF, so they are missing "
            "by evidence in this save."
        ),
    }
    prayer_flag_summary = {
        "mappedLocations": len(prayer_locations),
        "onByPrimaryFlags": prayer_flags_on,
        "offByPrimaryFlags": prayer_flags_off,
        "unknownByPrimaryFlags": prayer_flags_unknown,
        "collectedByEventFlags": prayer_flags_on,
        "collectedByLocationStatus": prayer_status_collected,
        "collectedByEvidence": prayer_status_collected,
        "missingByEvidence": prayer_status_missing,
        "unknownByEvidence": prayer_status_unknown,
        "definitelyMissingByLocationStatus": prayer_status_missing,
        "matchesInventoryDerivedCount": primary_flag_count_matches_inventory,
        "matchesInventoryDerivedCountAfterSecondaryEvidence": (
            evidence_count_matches_inventory
        ),
        "offPrimaryFlagsAreDefiniteMissing": off_primary_flags_are_definite_missing,
        "details": (
            "Primary pickup/shop flags are readable current save event states. OFF primary "
            "flags are not promoted to definitive missing locations. Verified secondary "
            "ItemLotParam flags can independently attribute collection for locations where "
            "the primary flag is OFF; verified missing-evidence rules mark the remaining "
            "OFF reward/pickup or shop-purchase states as missing."
        ),
    }
    if not prayer_flag_summary["matchesInventoryDerivedCountAfterSecondaryEvidence"]:
        warnings.append(
            "Prayer Bead evidence signals do not reconcile with the inventory-derived Prayer Bead count in this save; OFF primary flags are reported as unknown, not as definite missing locations."
        )

    return {
        "file": path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "container": {
            "format": "BND4",
            "entries": entries,
            "activeSlot": slot_name,
        },
        "inventory": {
            "healingGourdUses": healing_gourd_uses,
            "unusedGourdSeeds": unused_gourd_seeds,
            "unusedPrayerBeads": unused_prayer_beads,
            "prayerNecklaces": prayer_necklaces,
        },
        "eventFlags": {
            "layout": EVENT_LAYOUT,
            "mappedStates": flag_states,
        },
        "bosses": {
            "coverage": boss_data["coverage"],
            "statusPolicy": boss_data.get("statusPolicy"),
            "entities": boss_entities,
            "summary": boss_summary,
            "memoryItems": memory_items_found,
            "unresolved": boss_data["unresolved"],
        },
        "prayerBeads": {
            "total": prayer_data["total"],
            "coverage": prayer_data["coverage"],
            "locations": [compact_location(location) for location in prayer_locations],
            "entities": [
                prayer_location_entity(location) for location in prayer_locations
            ],
            "summary": prayer_summary,
            "flagStateSummary": prayer_flag_summary,
            "reconciliation": prayer_reconciliation,
            "unresolved": prayer_data["unresolved"],
        },
        "gourdSeeds": {
            "total": gourd_data["total"],
            "locations": [compact_location(location) for location in gourd_locations],
            "entities": [
                gourd_location_entity(location) for location in gourd_locations
            ],
            "summary": gourd_summary,
            "confirmedMissingLocations": [
                compact_location(location) for location in known_gourd_missing
            ],
            "unresolvedShopCandidates": [
                compact_location(location) for location in shop_gourd_unknown
            ],
            "shopSeedInference": shop_seed_inference,
        },
        "prosthetics": {
            "coverage": prosthetic_data["coverage"],
            "statusPolicy": prosthetic_data.get("statusPolicy"),
            "entities": prosthetic_entities,
            "summary": prosthetic_summary,
            "unresolved": prosthetic_data["unresolved"],
        },
        "prostheticUpgrades": {
            "coverage": prosthetic_upgrade_data["coverage"],
            "statusPolicy": prosthetic_upgrade_data.get("statusPolicy"),
            "upgradeSourcePolicy": prosthetic_upgrade_data.get(
                "upgradeSourcePolicy"
            ),
            "entities": prosthetic_upgrade_entities,
            "summary": prosthetic_upgrade_summary,
            "unresolved": prosthetic_upgrade_data["unresolved"],
        },
        "skills": {
            "coverage": skill_data["coverage"],
            "statusPolicy": skill_data.get("statusPolicy"),
            "entities": skill_entities,
            "summary": skill_summary,
            "unresolved": skill_data["unresolved"],
        },
        "keyItems": {
            "coverage": key_item_data["coverage"],
            "statusPolicy": key_item_data.get("statusPolicy"),
            "entities": key_item_entities,
            "summary": key_item_summary,
            "unresolved": key_item_data["unresolved"],
        },
        "endings": {
            "coverage": ending_data["coverage"],
            "statusPolicy": ending_data.get("statusPolicy"),
            "entities": ending_entities,
            "summary": ending_summary,
            "unresolved": ending_data["unresolved"],
        },
        "derivedCounts": derived_counts,
        "warnings": warnings,
        "sourcesUsed": [
            "SoulSplitter wiki: Sekiro item pickup flags extracted via Yapped; right-most column is event flag.",
            "PowerPyx Prayer Bead guide: exact human-readable Prayer Bead location/source enemy names.",
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
            "sekiro-online/params: EquipParamGoods row data for Ninjutsu candidate goods IDs.",
            "Fextralife Skills and Skill Trees page: community skill tree/name/cost/prerequisite context.",
            "Fextralife skill and Esoteric Text pages: community acquisition metadata for mapped Combat Arts.",
            "Fextralife Endings page: community ending-route requirements and final choice items.",
            "sekiro-online/params: EquipParamGoods row data for key item, Esoteric Text, and Prosthetic Tool source item names and IDs.",
            "sekiro-online/params: ItemLotParam row data for secondary Prayer Bead reward/replacement entries.",
            "sekiro-online/params: ShopLineupParam row data for merchant entries.",
            "S0000.sl2, read-only local inspection.",
        ],
    }


def legacy_report(result: dict[str, Any]) -> dict[str, Any]:
    gourd = result["gourdSeeds"]
    bosses = result["bosses"]["memoryItems"]
    return {
        "file": result["file"],
        "sha256": result["sha256"],
        "active_slot": result["container"]["activeSlot"],
        "sources_used": result["sourcesUsed"],
        "event_flag_reader": {
            "event_flag_base_hex": EVENT_LAYOUT["baseOffsetHex"],
            "bit_index_modulo": EVENT_LAYOUT.get("bitIndexModulo"),
            "bit_order": EVENT_LAYOUT["bitOrder"],
            "status": EVENT_LAYOUT["scope"],
        },
        "derived_counts": result["derivedCounts"],
        "gourd_seed_locations": gourd["locations"],
        "gourd_seed_summary": {
            "confirmed_missing_locations": gourd["confirmedMissingLocations"],
            "shop_seed_inference": gourd["shopSeedInference"],
            "unresolved_shop_candidates": gourd["unresolvedShopCandidates"],
            "plain_english": "Confirmed missing: Sunken Valley treasure and Fujioka the Info Broker purchase. Battlefield Memorial Mob purchase is collected.",
        },
        "prayer_bead_sample_flags": result["prayerBeads"]["locations"],
        "boss_memory_items_found": [
            boss["name"] for boss in bosses if boss["status"] == "found"
        ],
        "limitations": result["warnings"],
        "parseSekiroSaveShape": {
            key: result[key]
            for key in [
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
            ]
        },
    }


def main() -> None:
    result = parse_sekiro_save(SAVE)
    report = legacy_report(result)
    rendered = json.dumps(report, indent=2)
    REPORT.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
