from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import analyzer as probe


MAPPING_COLLECTIONS = {
    "bosses.json": "bosses",
    "endings.json": "endings",
    "gourd-seeds.json": "locations",
    "key-items.json": "items",
    "prayer-beads.json": "locations",
    "prosthetic-upgrades.json": "upgrades",
    "prosthetics.json": "prosthetics",
    "skills.json": "skills",
}
RULE_COLLECTIONS = {
    "bosses.json": "bosses",
    "key-items.json": "items",
    "prosthetic-upgrades.json": "upgrades",
    "prosthetics.json": "prosthetics",
    "skills.json": "skills",
}
ALLOWED_EVIDENCE_TYPES = {
    "community-docs",
    "community-guide",
    "community-param-data",
    "community-wiki",
    "event_flag",
    "inventory_item",
    "inventory_weapon",
    "key_item",
    "param",
    "save-analysis",
    "unmapped",
    "unverified_inventory_item_candidate",
}
SOURCE_CONFIDENCE_VALUES = {"Verified", "Probable", "Unknown"}
NORMALIZED_CONFIDENCE_VALUES = {"verified", "probable", "unknown"}
ALLOWED_CONFIDENCE_VALUES = SOURCE_CONFIDENCE_VALUES | NORMALIZED_CONFIDENCE_VALUES
EXPECTED_REPORT_STATUSES = {
    "prayerBeads": {"collected", "missing", "unknown"},
    "gourdSeeds": {"collected", "missing", "unknown"},
    "prosthetics": {"collected", "missing", "unknown"},
    "prostheticUpgrades": {"unlocked", "missing", "unknown"},
    "skills": {"unlocked", "missing", "unknown"},
    "keyItems": {"collected", "missing", "unknown"},
    "bosses": {"defeated", "not_defeated", "unknown"},
    "endings": {"completed", "available", "incomplete", "blocked", "unknown"},
}
ALLOWED_MAPPING_STATUSES = {
    "collected",
    "missing",
    "potential_block",
    "unknown",
    "unlocked",
}
ALLOWED_REPORT_EVIDENCE_TYPES = ALLOWED_EVIDENCE_TYPES | {
    "item_lot_flag",
    "shop_flag",
    "offering_box_flag",
    "missing_evidence",
    "inventory_summary",
}
REQUIRED_ENTITY_FIELDS = {
    "id",
    "name",
    "category",
    "status",
    "confidence",
    "evidence",
    "acquisitionMetadata",
    "notes",
}
REQUIRED_EVIDENCE_FIELDS = {"id", "state", "status", "confidence"}
SUPPORT_REPORT_SECTIONS = {"inventory", "eventFlags"}
LEGACY_REPORT_KEYS = {
    "file",
    "sha256",
    "active_slot",
    "sources_used",
    "event_flag_reader",
    "derived_counts",
    "gourd_seed_locations",
    "gourd_seed_summary",
    "prayer_bead_sample_flags",
    "boss_memory_items_found",
    "limitations",
    "parseSekiroSaveShape",
}


def iter_mapping_nodes(value, path):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from iter_mapping_nodes(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_mapping_nodes(child, f"{path}[{index}]")


class SekiroSaveParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.save_data = probe.SAVE.read_bytes()
        cls.entries = probe.parse_bnd4(cls.save_data)
        cls.slot = probe.get_user_slot(cls.save_data, cls.entries, "USER_DATA000")
        cls.result = probe.parse_sekiro_save(probe.SAVE)

    def assert_mapping_contract(self, mapping_file, data) -> None:
        for node_path, node in iter_mapping_nodes(data, mapping_file):
            evidence_type = node.get("type")
            if evidence_type is not None:
                with self.subTest(mapping_node=node_path, field="type"):
                    self.assertIn(evidence_type, ALLOWED_EVIDENCE_TYPES)

            for key, value in node.items():
                if key == "confidence" or key.endswith("Confidence"):
                    with self.subTest(mapping_node=node_path, field=key):
                        self.assertIsInstance(value, str)
                        self.assertIn(value, ALLOWED_CONFIDENCE_VALUES)

            status = node.get("status")
            if status is not None:
                with self.subTest(mapping_node=node_path, field="status"):
                    self.assertIsInstance(status, str)
                    self.assertIn(status, ALLOWED_MAPPING_STATUSES)

            for flag_key in ["eventFlag", "flag"]:
                if flag_key in node:
                    event_flag = node[flag_key]
                    with self.subTest(mapping_node=node_path, field=flag_key):
                        self.assertIs(type(event_flag), int)
                        self.assertGreaterEqual(event_flag, 0)

    def assert_rule_contract(self, owner_path, evidence_ids, rules) -> None:
        self.assertIsInstance(rules, list)
        for rule_index, rule in enumerate(rules):
            rule_path = f"{owner_path}.rules[{rule_index}]"
            with self.subTest(mapping_node=rule_path, field="status"):
                self.assertIn(rule.get("status"), ALLOWED_MAPPING_STATUSES)
            with self.subTest(mapping_node=rule_path, field="confidence"):
                self.assertIn(rule.get("confidence"), NORMALIZED_CONFIDENCE_VALUES)

            when = rule.get("when")
            with self.subTest(mapping_node=rule_path, field="when"):
                self.assertIsInstance(when, list)
                self.assertTrue(when)
            if not isinstance(when, list):
                continue

            for condition_index, condition in enumerate(when):
                condition_path = f"{rule_path}.when[{condition_index}]"
                with self.subTest(mapping_node=condition_path, field="evidenceId"):
                    self.assertIn("evidenceId", condition)
                    self.assertIn(condition["evidenceId"], evidence_ids)
                with self.subTest(mapping_node=condition_path, field="state"):
                    self.assertIn("state", condition)
                    self.assertIs(type(condition["state"]), bool)

    def test_bnd4_sl2_parsing(self) -> None:
        self.assertEqual(self.save_data[:4], b"BND4")
        self.assertEqual(len(self.entries), 12)
        self.assertEqual(self.result["container"]["format"], "BND4")

        entry_names = [entry["name"] for entry in self.entries]
        self.assertEqual(entry_names[0], "USER_DATA000")
        self.assertEqual(entry_names[-1], "USER_DATA011")
        self.assertEqual(
            entry_names,
            [f"USER_DATA{index:03d}" for index in range(12)],
        )

    def test_user_data_000_extraction(self) -> None:
        user_data_000 = self.entries[0]

        self.assertEqual(user_data_000["name"], "USER_DATA000")
        self.assertEqual(user_data_000["offset"], 768)
        self.assertEqual(user_data_000["size"], 1048592)
        self.assertEqual(len(self.slot), user_data_000["size"])
        self.assertEqual(self.result["container"]["activeSlot"], "USER_DATA000")

    def test_json_mapping_loading(self) -> None:
        event_layout = probe.load_json("event-flag-layout.json")["layouts"][0]
        gourd_data = probe.load_json("gourd-seeds.json")
        locations_by_id = {
            location["id"]: location for location in gourd_data["locations"]
        }

        self.assertEqual(gourd_data["total"], 9)
        self.assertEqual(event_layout["baseOffset"], 0xE8000)
        self.assertEqual(event_layout["bitIndexModulo"], 1_000_000)
        self.assertEqual(event_layout["bitOrder"], "LSB-first")
        self.assertEqual(
            locations_by_id["battlefield_memorial_mob"]["eventFlag"],
            71101210,
        )
        self.assertEqual(
            locations_by_id["fujioka_info_broker"]["eventFlag"],
            71102000,
        )
        self.assertEqual(locations_by_id["sunken_valley"]["eventFlag"], 6724)
        self.assertEqual(
            locations_by_id["battlefield_memorial_mob"]["mappingConfidence"],
            "Verified",
        )
        self.assertEqual(
            locations_by_id["fujioka_info_broker"]["mappingConfidence"],
            "Verified",
        )

    def test_event_flag_reader_uses_documented_layout(self) -> None:
        self.assertEqual(probe.EVENT_FLAG_BASE, 0xE8000)
        self.assertEqual(probe.EVENT_FLAG_INDEX_MODULO, 1_000_000)

        self.assertEqual(probe.event_flag_bit_index(6724), 6724)
        self.assertEqual(probe.event_flag_bit_index(71101210), 101210)
        self.assertEqual(probe.event_flag_bit_index(71102000), 102000)

        battlefield_bit_index = probe.event_flag_bit_index(71101210)
        battlefield_byte_offset = probe.EVENT_FLAG_BASE + battlefield_bit_index // 8
        battlefield_bit = battlefield_bit_index % 8
        self.assertEqual(battlefield_byte_offset, 0xEB16B)
        self.assertEqual(battlefield_bit, 2)

        fujioka_bit_index = probe.event_flag_bit_index(71102000)
        fujioka_byte_offset = probe.EVENT_FLAG_BASE + fujioka_bit_index // 8
        fujioka_bit = fujioka_bit_index % 8
        self.assertEqual(fujioka_byte_offset, 0xEB1CE)
        self.assertEqual(fujioka_bit, 0)

        self.assertTrue(probe.read_event_flag(self.slot, 6723))
        self.assertFalse(probe.read_event_flag(self.slot, 6724))
        self.assertTrue(probe.read_event_flag(self.slot, 71101210))
        self.assertFalse(probe.read_event_flag(self.slot, 71102000))

    def test_final_gourd_seed_report(self) -> None:
        gourd = self.result["gourdSeeds"]
        derived_counts = self.result["derivedCounts"]
        locations_by_id = {
            location["id"]: location for location in gourd["locations"]
        }

        self.assertEqual(gourd["total"], 9)
        self.assertEqual(derived_counts["gourdSeedsFound"], 7)
        self.assertEqual(derived_counts["gourdSeedsMissing"], 2)

        missing_ids = {
            location["id"] for location in gourd["confirmedMissingLocations"]
        }
        self.assertEqual(missing_ids, {"sunken_valley", "fujioka_info_broker"})

        self.assertEqual(locations_by_id["sunken_valley"]["status"], "missing")
        self.assertFalse(locations_by_id["sunken_valley"]["eventFlagState"])
        self.assertEqual(locations_by_id["fujioka_info_broker"]["status"], "missing")
        self.assertFalse(locations_by_id["fujioka_info_broker"]["eventFlagState"])
        self.assertEqual(
            locations_by_id["battlefield_memorial_mob"]["status"],
            "collected",
        )
        self.assertTrue(
            locations_by_id["battlefield_memorial_mob"]["eventFlagState"]
        )

        self.assertEqual(gourd["unresolvedShopCandidates"], [])
        self.assertEqual(gourd["shopSeedInference"]["shopSeedsTotal"], 2)
        self.assertEqual(gourd["shopSeedInference"]["shopSeedsFoundByEventFlags"], 1)
        self.assertEqual(gourd["shopSeedInference"]["shopSeedsMissingByEventFlags"], 1)
        self.assertEqual(gourd["shopSeedInference"]["shopSeedsUnknown"], 0)
        self.assertEqual(gourd["shopSeedInference"]["confidence"], "Verified")

    def test_prayer_bead_batch_event_flags_and_states(self) -> None:
        prayer = self.result["prayerBeads"]
        locations_by_id = {
            location["id"]: location for location in prayer["locations"]
        }

        self.assertEqual(prayer["total"], 40)
        self.assertGreaterEqual(len(prayer["locations"]), 40)
        self.assertEqual(self.result["derivedCounts"]["prayerBeadsFound"], 26)
        self.assertEqual(self.result["derivedCounts"]["prayerBeadsMissing"], 14)
        self.assertEqual(prayer["flagStateSummary"]["mappedLocations"], 40)
        self.assertEqual(prayer["flagStateSummary"]["onByPrimaryFlags"], 15)
        self.assertEqual(prayer["flagStateSummary"]["offByPrimaryFlags"], 25)
        self.assertEqual(prayer["flagStateSummary"]["unknownByPrimaryFlags"], 0)
        self.assertEqual(prayer["flagStateSummary"]["collectedByEventFlags"], 15)
        self.assertEqual(prayer["flagStateSummary"]["collectedByLocationStatus"], 26)
        self.assertEqual(prayer["flagStateSummary"]["collectedByEvidence"], 26)
        self.assertEqual(prayer["flagStateSummary"]["missingByEvidence"], 14)
        self.assertEqual(prayer["flagStateSummary"]["unknownByEvidence"], 0)
        self.assertNotIn("missingByEventFlags", prayer["flagStateSummary"])
        self.assertEqual(
            prayer["flagStateSummary"]["definitelyMissingByLocationStatus"],
            14,
        )
        self.assertNotIn("unresolvedByLocationStatus", prayer["flagStateSummary"])
        self.assertFalse(prayer["flagStateSummary"]["matchesInventoryDerivedCount"])
        self.assertTrue(
            prayer["flagStateSummary"][
                "matchesInventoryDerivedCountAfterSecondaryEvidence"
            ]
        )
        self.assertFalse(
            prayer["flagStateSummary"]["offPrimaryFlagsAreDefiniteMissing"]
        )

        reconciliation = prayer["reconciliation"]
        self.assertTrue(reconciliation["reconciled"])
        self.assertFalse(reconciliation["offPrimaryFlagsAreDefiniteMissing"])
        self.assertEqual(reconciliation["inventoryDerivedFound"], 26)
        self.assertEqual(reconciliation["inventoryDerivedMissing"], 14)
        self.assertEqual(reconciliation["primaryFlagsOn"], 15)
        self.assertEqual(reconciliation["primaryFlagsOff"], 25)
        self.assertEqual(reconciliation["unrepresentedCollectedCount"], 11)
        self.assertEqual(reconciliation["knownCollectedByEvidence"], 26)
        self.assertEqual(reconciliation["knownMissingByEvidence"], 14)
        self.assertEqual(reconciliation["unknownByEvidence"], 0)
        self.assertEqual(reconciliation["attributedByPrimaryFlags"], 15)
        self.assertEqual(reconciliation["attributedBySecondaryItemLotFlags"], 11)
        self.assertEqual(reconciliation["remainingUnattributedCount"], 0)
        self.assertTrue(
            reconciliation["matchesInventoryDerivedCountAfterSecondaryEvidence"]
        )
        self.assertTrue(reconciliation["prayerNecklacesIncludedInDerivedTotal"])

        secondary_attributed_ids = {
            "ashina_elite_ujinari_mizou",
            "blazing_bull",
            "general_kuranosuke_matsumoto",
            "general_naomori_kawarada_bead",
            "headless_ape_bead_1",
            "mibu_watermill_attic",
            "okami_leader_shizu",
            "orin_of_the_water",
            "snake_eyes_shirafuji",
            "sunken_valley_treasure_1",
            "tokujiro_the_glutton",
        }
        missing_by_evidence_ids = {
            "abandoned_dungeon_memorial_mob",
            "fountainhead_underwater_chest",
            "headless_ape_bead_2",
            "hirata_audience_chamber_hidden_chest",
            "juzou_the_drunkard_hirata_revisit",
            "long_arm_centipede_senun",
            "mibu_underwater_chest",
            "senpou_temple_underwater",
            "seven_ashina_spears_shikibu",
            "seven_ashina_spears_shume",
            "shigekichi_red_guard",
            "shinobi_hunter_enshin",
            "sunken_valley_treasure_2",
            "sunken_valley_treasure_3",
        }

        expected_batch = {
            "abandoned_dungeon_memorial_mob": (71111000, False),
            "ashina_castle_gate_attic_chest": (6788, True),
            "ashina_elite_ujinari_mizou": (6785, False),
            "blazing_bull": (6765, False),
            "chained_ogre_outskirts": (6761, True),
            "headless_ape_bead_1": (6798, False),
            "headless_ape_bead_2": (6799, False),
            "hirata_audience_chamber_hidden_chest": (6789, False),
            "shinobi_hunter_enshin": (6763, False),
            "juzou_the_drunkard_hirata": (6764, True),
            "juzou_the_drunkard_hirata_revisit": (6782, False),
            "general_kuranosuke_matsumoto": (6766, False),
            "ashina_elite_jinsuke_saze": (6767, True),
            "seven_ashina_spears_shikibu": (6769, False),
            "seven_ashina_spears_shume": (6786, False),
            "lone_shadow_longswordsman": (6770, True),
            "armored_warrior": (6771, True),
            "long_arm_centipede_senun": (6772, False),
            "long_arm_centipede_giraffe": (6774, True),
            "mibu_watermill_attic": (6795, False),
            "okami_leader_shizu": (6784, False),
            "orin_of_the_water": (6777, False),
            "senpou_temple_underwater": (6791, False),
            "shigekichi_red_guard": (6787, False),
            "snake_eyes_shirahagi": (6775, True),
            "snake_eyes_shirafuji": (6773, False),
            "tokujiro_the_glutton": (6776, False),
            "chained_ogre_ashina_castle": (6778, True),
            "lone_shadow_vilehand": (6779, True),
            "lone_shadow_masanaga_serpent_shrine": (6780, True),
            "lone_shadow_masanaga_hirata_revisit": (6781, True),
            "sakura_bull": (6783, True),
        }

        for location_id, (event_flag, flag_state) in expected_batch.items():
            with self.subTest(location_id=location_id):
                location = locations_by_id[location_id]
                expected_status = (
                    "collected"
                    if flag_state or location_id in secondary_attributed_ids
                    else "missing"
                    if location_id in missing_by_evidence_ids
                    else "unknown"
                )
                self.assertEqual(location["eventFlag"], event_flag)
                self.assertEqual(location["status"], expected_status)
                self.assertEqual(location["eventFlagState"], flag_state)
                self.assertEqual(location["mappingConfidence"], "Verified")
                self.assertEqual(
                    location["primaryPickupFlag"]["eventFlag"],
                    event_flag,
                )
                self.assertEqual(location["primaryPickupFlag"]["state"], flag_state)
                self.assertEqual(
                    location["primaryPickupFlag"]["status"],
                    "on" if flag_state else "off",
                )
                self.assertEqual(
                    location["confidence"]["collectionStatus"],
                    "Verified"
                    if expected_status in {"collected", "missing"}
                    else "Unresolved",
                )

        off_primary_locations = [
            location
            for location in prayer["locations"]
            if location["eventFlagState"] is False
        ]
        self.assertEqual(len(off_primary_locations), 25)
        self.assertTrue(
            all(
                location["status"] in {"collected", "missing"}
                for location in off_primary_locations
            )
        )
        self.assertFalse(any(location["status"] == "unresolved" for location in off_primary_locations))
        self.assertEqual(
            {
                location["id"]
                for location in off_primary_locations
                if location["status"] == "collected"
            },
            secondary_attributed_ids,
        )
        self.assertEqual(
            {
                location["id"]
                for location in off_primary_locations
                if location["status"] == "missing"
            },
            missing_by_evidence_ids,
        )

    def test_prayer_bead_evidence_signals(self) -> None:
        prayer = self.result["prayerBeads"]
        locations_by_id = {
            location["id"]: location for location in prayer["locations"]
        }

        chained_ogre = locations_by_id["chained_ogre_outskirts"]
        self.assertEqual(chained_ogre["status"], "collected")
        self.assertEqual(chained_ogre["primaryPickupFlag"]["eventFlag"], 6761)
        self.assertTrue(chained_ogre["primaryPickupFlag"]["state"])
        self.assertEqual(chained_ogre["itemLotFlag"]["rowId"], 50201000)
        self.assertEqual(chained_ogre["itemLotFlag"]["eventFlag"], 6761)
        self.assertTrue(chained_ogre["itemLotFlag"]["state"])
        self.assertIsNone(chained_ogre["shopFlag"]["eventFlag"])
        self.assertEqual(chained_ogre["shopFlag"]["confidence"], "Unknown")
        self.assertEqual(chained_ogre["bossDefeatFlag"]["confidence"], "Unknown")
        self.assertEqual(chained_ogre["offeringBoxFlag"]["confidence"], "Unknown")
        self.assertEqual(
            chained_ogre["inventoryEvidence"]["aggregatePrayerBeadsFound"],
            26,
        )
        self.assertEqual(
            chained_ogre["inventoryEvidence"]["aggregatePrayerBeadsMissing"],
            14,
        )
        self.assertIsNone(chained_ogre["inventoryEvidence"]["exactLocationAttribution"])

        shop_bead = locations_by_id["abandoned_dungeon_memorial_mob"]
        self.assertEqual(shop_bead["status"], "missing")
        self.assertFalse(shop_bead["eventFlagState"])
        self.assertEqual(shop_bead["primaryPickupFlag"]["eventFlag"], 71111000)
        self.assertFalse(shop_bead["primaryPickupFlag"]["state"])
        self.assertEqual(shop_bead["shopFlag"]["rowId"], 1110000)
        self.assertEqual(shop_bead["shopFlag"]["eventFlag"], 71111000)
        self.assertFalse(shop_bead["shopFlag"]["state"])
        self.assertIsNone(shop_bead["itemLotFlag"]["eventFlag"])
        self.assertEqual(shop_bead["missingEvidence"]["rule"], "shop_purchase_flag_off")
        self.assertTrue(shop_bead["missingEvidence"]["state"])
        self.assertEqual(shop_bead["confidence"]["collectionStatus"], "Verified")

    def test_prayer_bead_secondary_item_lot_attribution(self) -> None:
        prayer = self.result["prayerBeads"]
        locations_by_id = {
            location["id"]: location for location in prayer["locations"]
        }

        expected_secondary = {
            "ashina_elite_ujinari_mizou": (14001005, 51110978, 3704),
            "blazing_bull": (13700005, 51110976, 3704),
            "general_kuranosuke_matsumoto": (10202005, 51110970, 3704),
            "general_naomori_kawarada_bead": (10200005, 51100905, 3704),
            "headless_ape_bead_1": (2017, 50002017, 5213),
            "mibu_watermill_attic": (1500045, 51500045, 3720),
            "okami_leader_shizu": (13100005, 52500905, 3704),
            "orin_of_the_water": (70000005, 51500925, 3704),
            "snake_eyes_shirafuji": (11900005, 51701015, 3704),
            "sunken_valley_treasure_1": (1700025, 51700025, 3720),
            "tokujiro_the_glutton": (10702005, 51500935, 3704),
        }

        attributed_ids = {
            location["id"]
            for location in prayer["locations"]
            if any(
                secondary["state"] is True
                and secondary["attributionConfidence"] == "Verified"
                for secondary in location["itemLotFlag"].get("secondary", [])
            )
        }
        self.assertEqual(attributed_ids, set(expected_secondary))

        for location_id, (row_id, event_flag, awarded_item_id) in expected_secondary.items():
            with self.subTest(location_id=location_id):
                location = locations_by_id[location_id]
                self.assertEqual(location["status"], "collected")
                self.assertFalse(location["primaryPickupFlag"]["state"])
                secondary = location["itemLotFlag"]["secondary"]
                self.assertEqual(len(secondary), 1)
                self.assertEqual(secondary[0]["rowId"], row_id)
                self.assertEqual(secondary[0]["eventFlag"], event_flag)
                self.assertEqual(secondary[0]["awardedItemId"], awarded_item_id)
                self.assertTrue(secondary[0]["state"])
                self.assertEqual(secondary[0]["status"], "on")
                self.assertEqual(secondary[0]["mappingConfidence"], "Verified")
                self.assertEqual(secondary[0]["attributionConfidence"], "Verified")
                self.assertTrue(
                    self.result["eventFlags"]["mappedStates"][str(event_flag)]
                )

        headless_ape_2 = locations_by_id["headless_ape_bead_2"]
        self.assertEqual(headless_ape_2["status"], "missing")
        self.assertEqual(headless_ape_2["itemLotFlag"]["secondary"][0]["rowId"], 2018)
        self.assertEqual(
            headless_ape_2["itemLotFlag"]["secondary"][0]["eventFlag"],
            50002018,
        )
        self.assertFalse(headless_ape_2["itemLotFlag"]["secondary"][0]["state"])

    def test_prayer_bead_missing_evidence(self) -> None:
        prayer = self.result["prayerBeads"]
        locations_by_id = {
            location["id"]: location for location in prayer["locations"]
        }

        expected_missing = {
            "shinobi_hunter_enshin": (10500005, 51000925, 3704),
            "seven_ashina_spears_shikibu": (10212005, 51112900, 3704),
            "long_arm_centipede_senun": (10400005, 52000945, 3704),
            "mibu_underwater_chest": (1500325, 51500325, 3720),
            "fountainhead_underwater_chest": (2500025, 52500025, 3720),
            "sunken_valley_treasure_2": (1700035, 51700035, 3720),
            "sunken_valley_treasure_3": (1700045, 51700045, 3720),
            "hirata_audience_chamber_hidden_chest": (1000505, 51000505, 3720),
            "senpou_temple_underwater": (2000045, 52000045, 3720),
            "headless_ape_bead_2": (2018, 50002018, 5400),
            "juzou_the_drunkard_hirata_revisit": (10700105, 51000955, 3704),
            "seven_ashina_spears_shume": (10212105, 51112910, 3704),
            "shigekichi_red_guard": (10701005, 51100965, 3704),
        }

        missing_ids = {
            location["id"]
            for location in prayer["locations"]
            if location["status"] == "missing"
        }
        self.assertEqual(
            missing_ids,
            {*expected_missing, "abandoned_dungeon_memorial_mob"},
        )

        for location_id, (row_id, event_flag, awarded_item_id) in expected_missing.items():
            with self.subTest(location_id=location_id):
                location = locations_by_id[location_id]
                self.assertEqual(location["status"], "missing")
                self.assertFalse(location["primaryPickupFlag"]["state"])
                self.assertEqual(
                    location["missingEvidence"]["rule"],
                    "primary_and_secondary_item_lot_flags_off",
                )
                self.assertTrue(location["missingEvidence"]["state"])
                self.assertEqual(location["missingEvidence"]["confidence"], "Verified")
                secondary = location["itemLotFlag"]["secondary"]
                self.assertEqual(len(secondary), 1)
                self.assertEqual(secondary[0]["rowId"], row_id)
                self.assertEqual(secondary[0]["eventFlag"], event_flag)
                self.assertEqual(secondary[0]["awardedItemId"], awarded_item_id)
                self.assertFalse(secondary[0]["state"])
                self.assertEqual(secondary[0]["status"], "off")
                self.assertFalse(
                    self.result["eventFlags"]["mappedStates"][str(event_flag)]
                )

        shop_bead = locations_by_id["abandoned_dungeon_memorial_mob"]
        self.assertEqual(shop_bead["missingEvidence"]["rule"], "shop_purchase_flag_off")
        self.assertTrue(shop_bead["missingEvidence"]["state"])
        self.assertFalse(shop_bead["shopFlag"]["state"])

    def test_boss_memory_award_evidence(self) -> None:
        bosses = self.result["bosses"]
        entities_by_id = {entity["id"]: entity for entity in bosses["entities"]}

        expected_flags = {
            "gyoubu_oniwa": (50002001, True, True),
            "lady_butterfly": (50002031, True, True),
            "genichiro": (50002081, True, True),
            "screen_monkeys": (50002021, True, True),
            "guardian_ape": (50002011, True, True),
            "corrupted_monk": (50002051, True, True),
            "great_shinobi_owl": (50002091, True, True),
            "foster_father": (50002101, True, False),
            "true_monk": (50002061, False, True),
            "divine_dragon": (50002071, False, False),
            "demon_of_hatred": (50002041, True, False),
            "sword_saint_isshin": (50002131, True, False),
            "isshin_ashina": (50002121, True, False),
            "headless_ape": (50002017, True, False),
        }
        expected_split_flags = {
            "gyoubu_oniwa": (9301, True),
            "lady_butterfly": (9302, True),
            "genichiro": (9303, False),
            "guardian_ape": (9304, True),
            "screen_monkeys": (9305, True),
            "corrupted_monk": (9306, True),
            "headless_ape": (9307, True),
            "great_shinobi_owl": (9308, True),
            "true_monk": (9309, True),
            "divine_dragon": (9310, True),
            "sword_saint_isshin": (9312, False),
            "demon_of_hatred": (9313, True),
            "isshin_ashina": (9316, False),
            "foster_father": (9317, True),
        }
        self.assertEqual(
            bosses["coverage"],
            "deferred-memory-comparison-plus-speedrun-split-candidates",
        )
        self.assertFalse(
            bosses["statusPolicy"]["memoryEvidenceSufficientForDefeated"]
        )
        self.assertFalse(
            bosses["statusPolicy"]["speedrunSplitFlagsSufficientForDefeated"]
        )
        self.assertEqual(bosses["summary"]["total"], 14)
        self.assertEqual(bosses["summary"]["defeated"], 0)
        self.assertEqual(bosses["summary"]["notDefeated"], 0)
        self.assertEqual(bosses["summary"]["unknown"], 14)
        self.assertEqual(set(entities_by_id), set(expected_flags))

        for boss_id, (flag, flag_state, inventory_state) in expected_flags.items():
            with self.subTest(boss_id=boss_id):
                boss = entities_by_id[boss_id]
                split_flag, split_flag_state = expected_split_flags[boss_id]
                evidence_by_id = {
                    evidence["id"]: evidence for evidence in boss["evidence"]
                }
                self.assertEqual(boss["category"], "boss")
                self.assertEqual(boss["status"], "unknown")
                self.assertEqual(boss["confidence"], "unknown")
                self.assertEqual(evidence_by_id["memory_award_flag"]["flag"], flag)
                self.assertEqual(
                    evidence_by_id["memory_award_flag"]["state"],
                    flag_state,
                )
                self.assertEqual(
                    evidence_by_id["memory_award_flag"]["stateConfidence"],
                    "verified",
                )
                self.assertEqual(
                    evidence_by_id["memory_inventory_item"]["state"],
                    inventory_state,
                )
                self.assertEqual(
                    self.result["eventFlags"]["mappedStates"][str(flag)],
                    flag_state,
                )
                self.assertEqual(
                    evidence_by_id["speedrunSplitFlagCandidate"]["flag"],
                    split_flag,
                )
                self.assertEqual(
                    evidence_by_id["speedrunSplitFlagCandidate"]["state"],
                    split_flag_state,
                )
                self.assertEqual(
                    evidence_by_id["speedrunSplitFlagCandidate"]["confidence"],
                    "unknown",
                )
                self.assertEqual(
                    evidence_by_id["speedrunSplitFlagCandidate"][
                        "statusContribution"
                    ],
                    "candidate_only",
                )
                self.assertEqual(
                    self.result["eventFlags"]["mappedStates"][str(split_flag)],
                    split_flag_state,
                )

        self.assertNotEqual(entities_by_id["isshin_ashina"]["status"], "defeated")
        self.assertNotEqual(
            entities_by_id["isshin_ashina"]["status"],
            "not_defeated",
        )
        self.assertEqual(entities_by_id["isshin_ashina"]["status"], "unknown")
        self.assertEqual(entities_by_id["genichiro"]["status"], "unknown")
        self.assertNotEqual(
            entities_by_id["genichiro"]["status"],
            "not_defeated",
        )
        self.assertNotEqual(entities_by_id["headless_ape"]["status"], "defeated")
        self.assertNotEqual(
            entities_by_id["headless_ape"]["status"],
            "not_defeated",
        )
        self.assertEqual(entities_by_id["headless_ape"]["status"], "unknown")
        self.assertTrue(
            entities_by_id["isshin_ashina"]["evidence"][0]["state"],
        )
        self.assertTrue(
            entities_by_id["headless_ape"]["evidence"][0]["state"],
        )
        self.assertFalse(
            {
                boss["id"]
                for boss in bosses["entities"]
                if boss["status"] in {"defeated", "not_defeated"}
            }
        )

    def test_prosthetic_tool_inventory_evidence(self) -> None:
        prosthetics = self.result["prosthetics"]
        entities_by_id = {
            entity["id"]: entity for entity in prosthetics["entities"]
        }
        mapping_data = probe.load_json("prosthetics.json")
        mappings_by_id = {
            entity["id"]: entity for entity in mapping_data["prosthetics"]
        }

        expected_tools = {
            "loaded_shuriken": (
                70000,
                9700,
                "70110100",
                True,
                "collected",
                "0x8f930",
            ),
            "shinobi_firecracker": (
                71000,
                9710,
                "58150100",
                True,
                "collected",
                "0x8fb70",
            ),
            "flame_vent": (
                72000,
                9720,
                "40190100",
                True,
                "collected",
                "0x8fa10",
            ),
            "loaded_axe": (
                73000,
                9730,
                "281D0100",
                True,
                "collected",
                "0x8fa20",
            ),
            "mist_raven": (
                74000,
                9740,
                "10210100",
                True,
                "collected",
                "0x8fa50",
            ),
            "sabimaru": (
                75000,
                9750,
                "F8240100",
                True,
                "collected",
                "0x90000",
            ),
            "loaded_umbrella": (
                76000,
                9760,
                "E0280100",
                False,
                "missing",
                None,
            ),
            "divine_abduction": (
                77000,
                9770,
                "C82C0100",
                True,
                "collected",
                "0x8fa90",
            ),
            "loaded_spear": (
                78000,
                9780,
                "B0300100",
                True,
                "collected",
                "0x8fbf0",
            ),
            "finger_whistle": (
                79000,
                9790,
                "98340100",
                True,
                "collected",
                "0x8fee0",
            ),
        }

        self.assertEqual(
            prosthetics["coverage"],
            "base-prosthetic-tools-inventory-evidence",
        )
        self.assertEqual(prosthetics["summary"]["total"], 10)
        self.assertEqual(prosthetics["summary"]["collected"], 9)
        self.assertEqual(prosthetics["summary"]["missing"], 1)
        self.assertEqual(prosthetics["summary"]["unknown"], 0)
        self.assertEqual(set(entities_by_id), set(expected_tools))

        for tool_id, (
            weapon_row_id,
            source_goods_row_id,
            item_id_hex,
            state,
            status,
            offset_hex,
        ) in expected_tools.items():
            with self.subTest(tool_id=tool_id):
                mapping = mappings_by_id[tool_id]
                entity = entities_by_id[tool_id]
                evidence_by_id = {
                    evidence["id"]: evidence for evidence in entity["evidence"]
                }
                weapon_evidence = evidence_by_id["weaponInventoryItem"]

                self.assertEqual(mapping["equipParamWeaponRowId"], weapon_row_id)
                self.assertEqual(
                    mapping["sourceGoodsParamRowId"],
                    source_goods_row_id,
                )
                self.assertEqual(mapping["evidence"][0]["itemIdHex"], item_id_hex)
                self.assertEqual(entity["equipParamWeaponRowId"], weapon_row_id)
                self.assertEqual(
                    entity["sourceGoodsParamRowId"],
                    source_goods_row_id,
                )
                self.assertEqual(
                    entity["sourceItemName"],
                    mapping["sourceItemName"],
                )
                self.assertEqual(entity["category"], "prosthetic")
                self.assertEqual(entity["status"], status)
                self.assertEqual(entity["confidence"], "verified")
                self.assertEqual(weapon_evidence["type"], "inventory_weapon")
                self.assertEqual(weapon_evidence["itemIdHex"], item_id_hex)
                self.assertEqual(weapon_evidence["state"], state)
                self.assertEqual(
                    weapon_evidence["status"],
                    "present" if state else "absent",
                )
                self.assertEqual(weapon_evidence["confidence"], "verified")
                self.assertEqual(weapon_evidence["recordCount"], 1 if state else 0)
                self.assertEqual(bool(weapon_evidence["records"]), state)
                if offset_hex is not None:
                    self.assertEqual(
                        weapon_evidence["records"][0]["offsetHex"],
                        offset_hex,
                    )
                    self.assertEqual(
                        weapon_evidence["records"][0]["qtyAfterId"],
                        1,
                    )

    def test_prosthetic_tool_location_metadata(self) -> None:
        prosthetics = self.result["prosthetics"]
        entities_by_id = {
            entity["id"]: entity for entity in prosthetics["entities"]
        }

        expected_metadata = {
            "loaded_shuriken": {
                "area": "Ashina Outskirts",
                "locationContains": "Outskirts Wall - Gate Path",
                "acquisitionContains": "Shuriken Wheel",
                "vendor": None,
                "chest": None,
                "enemy": None,
            },
            "shinobi_firecracker": {
                "area": "Ashina Outskirts",
                "locationContains": "Crow's Bed Memorial Mob",
                "acquisitionContains": "Robert's Firecrackers",
                "vendor": "Crow's Bed Memorial Mob",
                "chest": None,
                "enemy": None,
            },
            "flame_vent": {
                "area": "Hirata Estate",
                "locationContains": "Estate Path",
                "acquisitionContains": "Flame Barrel",
                "vendor": None,
                "chest": None,
                "enemy": None,
            },
            "loaded_axe": {
                "area": "Hirata Estate",
                "locationContains": "small garden house",
                "acquisitionContains": "Shinobi Axe of the Monkey",
                "vendor": None,
                "chest": "Small garden house / shrine",
                "enemy": None,
            },
            "mist_raven": {
                "area": "Hirata Estate",
                "locationContains": "Bamboo Thicket Slope",
                "acquisitionContains": "Mist Raven's Feathers",
                "vendor": None,
                "chest": "Hidden temple",
                "enemy": "Guarding Lone Shadow / purple ninja",
            },
            "sabimaru": {
                "area": "Ashina Castle",
                "locationContains": "Upper Tower - Antechamber",
                "acquisitionContains": "Sabimaru",
                "vendor": None,
                "chest": "Chest in the lower Antechamber room",
                "enemy": None,
            },
            "loaded_umbrella": {
                "area": "Ashina Castle",
                "locationContains": "Old Grave",
                "acquisitionContains": "Purchase Iron Fortress from Blackhat Badger",
                "vendor": "Blackhat Badger",
                "chest": None,
                "enemy": None,
            },
            "divine_abduction": {
                "area": "Sunken Valley",
                "locationContains": "Long-arm Centipede Giraffe room",
                "acquisitionContains": "Large Fan",
                "vendor": None,
                "chest": None,
                "enemy": "Long-arm Centipede Giraffe",
            },
            "loaded_spear": {
                "area": "Ashina Reservoir",
                "locationContains": "Gatehouse",
                "acquisitionContains": "Gyoubu's Broken Horn",
                "vendor": None,
                "chest": "Gatehouse chest",
                "enemy": None,
            },
            "finger_whistle": {
                "area": "Sunken Valley",
                "locationContains": "Guardian Ape",
                "acquisitionContains": "Slender Finger",
                "vendor": None,
                "chest": None,
                "enemy": "Guardian Ape",
            },
        }

        self.assertEqual(set(entities_by_id), set(expected_metadata))
        for tool_id, expected in expected_metadata.items():
            with self.subTest(tool_id=tool_id):
                entity = entities_by_id[tool_id]
                source_location = entity["sourceLocation"]

                self.assertEqual(source_location["area"], expected["area"])
                self.assertIn(
                    expected["locationContains"],
                    source_location["location"],
                )
                self.assertIn(
                    expected["acquisitionContains"],
                    source_location["acquisition"],
                )
                self.assertEqual(source_location["vendor"], expected["vendor"])
                self.assertEqual(source_location["chest"], expected["chest"])
                self.assertEqual(source_location["enemy"], expected["enemy"])
                self.assertEqual(source_location["confidence"], "Probable")
                self.assertTrue(source_location["requiredProgression"])
                self.assertEqual(len(source_location["sourceReferences"]), 1)
                self.assertEqual(
                    source_location["sourceReferences"][0]["type"],
                    "community-wiki",
                )
                self.assertTrue(
                    source_location["sourceReferences"][0]["url"].startswith(
                        "https://sekiroshadowsdietwice.wiki.fextralife.com/"
                    )
                )
                self.assertTrue(source_location["sourceReferences"][0]["evidence"])

        loaded_umbrella = entities_by_id["loaded_umbrella"]
        self.assertEqual(loaded_umbrella["status"], "missing")
        self.assertEqual(loaded_umbrella["sourceItemName"], "Iron Fortress")
        self.assertEqual(loaded_umbrella["equipParamWeaponRowId"], 76000)
        self.assertEqual(loaded_umbrella["sourceGoodsParamRowId"], 9760)
        self.assertEqual(
            loaded_umbrella["sourceLocation"]["acquisition"],
            "Purchase Iron Fortress from Blackhat Badger, then fit it with the Sculptor as Loaded Umbrella.",
        )

    def test_prosthetic_upgrade_inventory_evidence(self) -> None:
        upgrades = self.result["prostheticUpgrades"]
        entities_by_id = {
            entity["id"]: entity for entity in upgrades["entities"]
        }
        mapping_data = probe.load_json("prosthetic-upgrades.json")
        mappings_by_id = {
            entity["id"]: entity for entity in mapping_data["upgrades"]
        }

        expected_upgrades = {
            "spinning_shuriken": (
                "loaded_shuriken",
                70100,
                "D4110100",
                "unlocked",
                "0x8fbc0",
            ),
            "gouging_top": (
                "loaded_shuriken",
                70200,
                "38120100",
                "unlocked",
                "0x8ff90",
            ),
            "phantom_kunai": (
                "loaded_shuriken",
                70300,
                "9C120100",
                "missing",
                None,
            ),
            "sen_throw": (
                "loaded_shuriken",
                70400,
                "00130100",
                "missing",
                None,
            ),
            "lazulite_shuriken": (
                "loaded_shuriken",
                70500,
                "64130100",
                "missing",
                None,
            ),
            "spring_load_firecracker": (
                "shinobi_firecracker",
                71100,
                "BC150100",
                "unlocked",
                "0x8f870",
            ),
            "long_spark": (
                "shinobi_firecracker",
                71200,
                "20160100",
                "unlocked",
                "0x8ff20",
            ),
            "purple_fume_spark": (
                "shinobi_firecracker",
                71300,
                "84160100",
                "missing",
                None,
            ),
            "spring_load_flame_vent": (
                "flame_vent",
                72100,
                "A4190100",
                "unlocked",
                "0x8fcb0",
            ),
            "okinagas_flame_vent": (
                "flame_vent",
                72200,
                "081A0100",
                "missing",
                None,
            ),
            "lazulite_sacred_flame": (
                "flame_vent",
                72300,
                "6C1A0100",
                "missing",
                None,
            ),
            "spring_load_axe": (
                "loaded_axe",
                73100,
                "8C1D0100",
                "unlocked",
                "0x8ffd0",
            ),
            "sparking_axe": (
                "loaded_axe",
                73200,
                "F01D0100",
                "missing",
                None,
            ),
            "lazulite_axe": (
                "loaded_axe",
                73300,
                "541E0100",
                "missing",
                None,
            ),
            "aged_feather_mist_raven": (
                "mist_raven",
                74100,
                "74210100",
                "unlocked",
                "0x90040",
            ),
            "great_feather_mist_raven": (
                "mist_raven",
                74200,
                "D8210100",
                "missing",
                None,
            ),
            "improved_sabimaru": (
                "sabimaru",
                75100,
                "5C250100",
                "unlocked",
                "0x90020",
            ),
            "piercing_sabimaru": (
                "sabimaru",
                75200,
                "C0250100",
                "missing",
                None,
            ),
            "lazulite_sabimaru": (
                "sabimaru",
                75300,
                "24260100",
                "missing",
                None,
            ),
            "loaded_umbrella_magnet": (
                "loaded_umbrella",
                76100,
                "44290100",
                "missing",
                None,
            ),
            "suzakus_lotus_umbrella": (
                "loaded_umbrella",
                76200,
                "A8290100",
                "missing",
                None,
            ),
            "phoenixs_lilac_umbrella": (
                "loaded_umbrella",
                76300,
                "0C2A0100",
                "missing",
                None,
            ),
            "double_divine_abduction": (
                "divine_abduction",
                77100,
                "2C2D0100",
                "unlocked",
                "0x8ff00",
            ),
            "golden_vortex": (
                "divine_abduction",
                77200,
                "902D0100",
                "missing",
                None,
            ),
            "loaded_spear_thrust_type": (
                "loaded_spear",
                78100,
                "14310100",
                "unlocked",
                "0x8fc10",
            ),
            "loaded_spear_cleave_type": (
                "loaded_spear",
                78200,
                "78310100",
                "unlocked",
                "0x8fc30",
            ),
            "spiral_spear": (
                "loaded_spear",
                78300,
                "DC310100",
                "missing",
                None,
            ),
            "leaping_flame": (
                "loaded_spear",
                78400,
                "40320100",
                "missing",
                None,
            ),
            "mountain_echo": (
                "finger_whistle",
                79100,
                "FC340100",
                "unlocked",
                "0x8ff40",
            ),
            "malcontent": (
                "finger_whistle",
                79200,
                "60350100",
                "missing",
                None,
            ),
        }

        self.assertEqual(
            upgrades["coverage"],
            "prosthetic-upgrade-weapon-inventory-evidence",
        )
        self.assertEqual(upgrades["summary"]["total"], 30)
        self.assertEqual(upgrades["summary"]["unlocked"], 12)
        self.assertEqual(upgrades["summary"]["missing"], 18)
        self.assertEqual(upgrades["summary"]["unknown"], 0)
        self.assertEqual(set(entities_by_id), set(expected_upgrades))

        for upgrade_id, (
            base_tool_id,
            row_id,
            item_id_hex,
            status,
            offset_hex,
        ) in expected_upgrades.items():
            with self.subTest(upgrade_id=upgrade_id):
                mapping = mappings_by_id[upgrade_id]
                entity = entities_by_id[upgrade_id]
                evidence_by_id = {
                    evidence["id"]: evidence for evidence in entity["evidence"]
                }
                weapon_evidence = evidence_by_id["weaponInventoryItem"]

                self.assertEqual(mapping["baseToolId"], base_tool_id)
                self.assertEqual(mapping["equipParamWeaponRowId"], row_id)
                self.assertEqual(mapping["itemIdHex"], item_id_hex)
                self.assertEqual(entity["category"], "prosthetic_upgrade")
                self.assertEqual(entity["baseToolId"], base_tool_id)
                self.assertEqual(entity["equipParamWeaponRowId"], row_id)
                self.assertEqual(entity["status"], status)
                self.assertEqual(entity["confidence"], "verified")
                self.assertEqual(entity["prerequisites"]["confidence"], "Unknown")
                self.assertEqual(entity["prerequisites"]["materials"], [])
                self.assertEqual(entity["sourceLocation"]["area"], "Dilapidated Temple")
                self.assertEqual(entity["sourceLocation"]["source"], "Sculptor")
                self.assertEqual(
                    entity["sourceLocation"]["location"],
                    "Sculptor Prosthetic Tool upgrade menu",
                )
                self.assertEqual(
                    entity["sourceLocation"]["confidence"],
                    "Probable",
                )
                self.assertEqual(weapon_evidence["type"], "inventory_weapon")
                self.assertEqual(weapon_evidence["itemIdHex"], item_id_hex)
                self.assertEqual(weapon_evidence["state"], status == "unlocked")
                self.assertEqual(
                    weapon_evidence["status"],
                    "present" if status == "unlocked" else "absent",
                )
                self.assertEqual(weapon_evidence["confidence"], "verified")
                self.assertEqual(
                    weapon_evidence["recordCount"],
                    1 if status == "unlocked" else 0,
                )
                self.assertEqual(
                    bool(weapon_evidence["records"]),
                    status == "unlocked",
                )
                if offset_hex is not None:
                    self.assertEqual(
                        weapon_evidence["records"][0]["offsetHex"],
                        offset_hex,
                    )
                    self.assertEqual(
                        weapon_evidence["records"][0]["qtyAfterId"],
                        1,
                    )

        loaded_umbrella_upgrades = {
            entity["id"]: entity
            for entity in upgrades["entities"]
            if entity["baseToolId"] == "loaded_umbrella"
        }
        self.assertEqual(
            set(loaded_umbrella_upgrades),
            {
                "loaded_umbrella_magnet",
                "suzakus_lotus_umbrella",
                "phoenixs_lilac_umbrella",
            },
        )
        self.assertTrue(
            all(
                entity["status"] == "missing"
                and entity["evidence"][0]["state"] is False
                for entity in loaded_umbrella_upgrades.values()
            )
        )

    def test_combat_art_skill_inventory_evidence(self) -> None:
        skills = self.result["skills"]
        entities_by_id = {
            entity["id"]: entity for entity in skills["entities"]
        }
        mapping_data = probe.load_json("skills.json")
        mappings_by_id = {
            entity["id"]: entity for entity in mapping_data["skills"]
        }

        expected_skills = {
            "whirlwind_slash": (
                "Shinobi Arts",
                "Whirlwind Slash",
                10,
                210000,
                5100,
                "EC130000",
                "unlocked",
                "0x8f990",
            ),
            "shadowrush": (
                "Shinobi Arts",
                "Shadowrush",
                20,
                211000,
                6000,
                "70170000",
                "missing",
                None,
            ),
            "nightjar_slash": (
                "Prosthetic Arts",
                "Nightjar Slash",
                110,
                310000,
                5200,
                "50140000",
                "unlocked",
                "0x8fac0",
            ),
            "nightjar_slash_reversal": (
                "Prosthetic Arts",
                "Nightjar Slash Reversal",
                111,
                310100,
                7000,
                "581B0000",
                "missing",
                None,
            ),
            "ichimonji": (
                "Ashina Arts",
                "Ichimonji",
                210,
                410000,
                5300,
                "B4140000",
                "unlocked",
                "0x8fb80",
            ),
            "ichimonji_double": (
                "Ashina Arts",
                "Ichimonji: Double",
                211,
                410100,
                7100,
                "BC1B0000",
                "unlocked",
                "0x8fe60",
            ),
            "ashina_cross": (
                "Ashina Arts",
                "Ashina Cross",
                220,
                411000,
                5500,
                "7C150000",
                "missing",
                None,
            ),
            "praying_strikes": (
                "Temple Arts",
                "Praying Strikes",
                310,
                510000,
                5900,
                "0C170000",
                "unlocked",
                "0x8ffe0",
            ),
            "praying_strikes_exorcism": (
                "Temple Arts",
                "Praying Strikes - Exorcism",
                311,
                510100,
                7500,
                "4C1D0000",
                "missing",
                None,
            ),
            "senpou_leaping_kicks": (
                "Temple Arts",
                "Senpou Leaping Kicks",
                320,
                511000,
                5800,
                "A8160000",
                "missing",
                None,
            ),
            "high_monk": (
                "Temple Arts",
                "High Monk",
                321,
                511100,
                7400,
                "E81C0000",
                "missing",
                None,
            ),
            "shadowfall": (
                "Mushin Arts",
                "Shadowfall",
                411,
                610100,
                7600,
                "B01D0000",
                "missing",
                None,
            ),
            "spiral_cloud_passage": (
                "Mushin Arts",
                "Spiral Cloud Passage",
                421,
                611100,
                7200,
                "201C0000",
                "missing",
                None,
            ),
            "empowered_mortal_draw": (
                "Mushin Arts",
                "Empowered Mortal Draw",
                431,
                612100,
                7300,
                "841C0000",
                "missing",
                None,
            ),
            "mortal_draw": (
                "Special Combat Arts",
                "Mortal Draw",
                630,
                670000,
                5700,
                "44160000",
                "unlocked",
                "0x8fd90",
            ),
            "dragon_flash": (
                "Special Combat Arts",
                "Dragon Flash",
                640,
                671000,
                5400,
                "18150000",
                "missing",
                None,
            ),
            "floating_passage": (
                "Special Combat Arts",
                "Floating Passage",
                650,
                672000,
                5600,
                "E0150000",
                "missing",
                None,
            ),
            "one_mind": (
                "Special Combat Arts",
                "One Mind",
                660,
                673000,
                6100,
                "D4170000",
                "missing",
                None,
            ),
        }
        expected_acquisition = {
            "whirlwind_slash": (
                1,
                "skill_points",
                [],
                "Shinobi Esoteric Text",
                None,
                None,
                None,
            ),
            "shadowrush": (
                6,
                "skill_points",
                ["Shinobi Eyes", "Mid-air Combat Arts"],
                "Shinobi Esoteric Text",
                None,
                None,
                None,
            ),
            "nightjar_slash": (
                2,
                "skill_points",
                ["Grappling Hook Attack"],
                "Prosthetic Esoteric Text",
                None,
                None,
                None,
            ),
            "nightjar_slash_reversal": (
                3,
                "skill_points",
                ["Nightjar Slash", "Emma's Medicine: Potency"],
                "Prosthetic Esoteric Text",
                None,
                None,
                None,
            ),
            "ichimonji": (
                2,
                "skill_points",
                [],
                "Ashina Esoteric Text",
                None,
                None,
                None,
            ),
            "ichimonji_double": (
                3,
                "skill_points",
                ["Ascending Carp", "Descending Carp"],
                "Ashina Esoteric Text",
                None,
                None,
                None,
            ),
            "ashina_cross": (
                5,
                "skill_points",
                ["Flowing Water", "Ichimonji: Double"],
                "Ashina Esoteric Text",
                None,
                None,
                None,
            ),
            "praying_strikes": (
                2,
                "skill_points",
                [],
                "Senpou Esoteric Text",
                None,
                None,
                None,
            ),
            "praying_strikes_exorcism": (
                3,
                "skill_points",
                ["Praying Strikes"],
                "Senpou Esoteric Text",
                None,
                None,
                None,
            ),
            "senpou_leaping_kicks": (
                3,
                "skill_points",
                ["Virtuous Deed"],
                "Senpou Esoteric Text",
                None,
                None,
                None,
            ),
            "high_monk": (
                4,
                "skill_points",
                ["Senpou Leaping Kicks"],
                "Senpou Esoteric Text",
                None,
                None,
                None,
            ),
            "shadowfall": (
                6,
                "skill_points",
                ["High Monk", "Shadowrush"],
                "Mushin Esoteric Text",
                None,
                None,
                None,
            ),
            "spiral_cloud_passage": (
                9,
                "skill_points",
                ["Shadowrush", "Ashina Cross"],
                "Mushin Esoteric Text",
                None,
                None,
                None,
            ),
            "empowered_mortal_draw": (
                5,
                "skill_points",
                ["Living Force", "Ashina Cross"],
                "Mushin Esoteric Text",
                None,
                None,
                None,
            ),
            "mortal_draw": (
                None,
                "not_applicable_direct_acquisition",
                [],
                None,
                None,
                "Folding Screen Monkeys",
                "Mortal Blade",
            ),
            "dragon_flash": (
                None,
                "not_applicable_direct_acquisition",
                [],
                None,
                None,
                "Isshin, The Sword Saint",
                None,
            ),
            "floating_passage": (
                None,
                "not_applicable_direct_acquisition",
                [],
                None,
                "Pot Noble Harunaga",
                None,
                "Floating Passage Text",
            ),
            "one_mind": (
                None,
                "not_applicable_direct_acquisition",
                [],
                None,
                None,
                "Isshin Ashina",
                None,
            ),
        }

        self.assertEqual(
            skills["coverage"],
            "combat-art-passive-latent-and-ninjutsu-skills-with-verified-or-unknown-save-evidence",
        )
        self.assertEqual(skills["summary"]["total"], 57)
        self.assertEqual(skills["summary"]["unlocked"], 29)
        self.assertEqual(skills["summary"]["missing"], 25)
        self.assertEqual(skills["summary"]["unknown"], 3)
        self.assertLessEqual(set(expected_skills), set(entities_by_id))

        for skill_id, (
            skill_tree,
            name,
            skill_param_row_id,
            skill_description_id,
            weapon_row_id,
            item_id_hex,
            status,
            offset_hex,
        ) in expected_skills.items():
            with self.subTest(skill_id=skill_id):
                mapping = mappings_by_id[skill_id]
                entity = entities_by_id[skill_id]
                evidence_by_id = {
                    evidence["id"]: evidence for evidence in entity["evidence"]
                }
                weapon_evidence = evidence_by_id["combatArtWeaponInventoryItem"]

                self.assertEqual(mapping["skillTree"], skill_tree)
                self.assertEqual(mapping["name"], name)
                self.assertEqual(mapping["skillParamRowId"], skill_param_row_id)
                self.assertEqual(mapping["skillDescriptionId"], skill_description_id)
                self.assertEqual(mapping["combatArtWeaponRowId"], weapon_row_id)
                self.assertEqual(mapping["itemIdHex"], item_id_hex)
                self.assertEqual(entity["category"], "skill")
                self.assertEqual(entity["skillType"], "combat_art")
                self.assertEqual(entity["skillTree"], skill_tree)
                self.assertEqual(entity["name"], name)
                self.assertEqual(entity["skillParamRowId"], skill_param_row_id)
                self.assertEqual(entity["skillDescriptionId"], skill_description_id)
                self.assertEqual(entity["combatArtWeaponRowId"], weapon_row_id)
                self.assertEqual(entity["status"], status)
                self.assertEqual(entity["confidence"], "verified")

                (
                    skill_point_cost,
                    skill_point_cost_type,
                    prerequisite_names,
                    esoteric_text,
                    vendor,
                    boss,
                    required_item_or_text,
                ) = expected_acquisition[skill_id]
                acquisition = entity["acquisitionMetadata"]
                self.assertEqual(entity["requiredSkillPoints"], skill_point_cost)
                self.assertEqual(entity["requiredSkillPointsConfidence"], "Probable")
                self.assertEqual(entity["prerequisites"]["confidence"], "Probable")
                self.assertEqual(
                    [skill["name"] for skill in entity["prerequisites"]["skills"]],
                    prerequisite_names,
                )
                self.assertEqual(acquisition["skillTree"], skill_tree)
                self.assertTrue(acquisition["acquisitionMethod"])
                self.assertEqual(acquisition["skillPointCost"], skill_point_cost)
                self.assertEqual(
                    acquisition["skillPointCostType"],
                    skill_point_cost_type,
                )
                self.assertEqual(
                    acquisition["skillPointCostConfidence"],
                    "Probable",
                )
                self.assertEqual(
                    [
                        skill["name"]
                        for skill in acquisition["requiredPrerequisiteSkills"]
                    ],
                    prerequisite_names,
                )
                if esoteric_text is None:
                    self.assertIsNone(acquisition["requiredEsotericText"])
                else:
                    self.assertEqual(
                        acquisition["requiredEsotericText"]["name"],
                        esoteric_text,
                    )
                    self.assertEqual(
                        acquisition["requiredEsotericText"]["confidence"],
                        "Probable",
                    )
                    self.assertTrue(
                        acquisition["requiredEsotericText"]["sourceReferences"]
                    )
                self.assertEqual(acquisition["vendor"], vendor)
                self.assertEqual(acquisition["boss"], boss)
                self.assertEqual(
                    acquisition["requiredItemOrText"],
                    required_item_or_text,
                )
                self.assertEqual(
                    acquisition["acquisitionMetadataConfidence"],
                    "Probable",
                )
                self.assertTrue(acquisition["sourceReferences"])
                self.assertIn(
                    "Status remains driven only by verified inventory_weapon evidence",
                    acquisition["ownershipInferencePolicy"],
                )
                self.assertEqual(weapon_evidence["type"], "inventory_weapon")
                self.assertEqual(weapon_evidence["itemIdHex"], item_id_hex)
                self.assertEqual(weapon_evidence["state"], status == "unlocked")
                self.assertEqual(
                    weapon_evidence["status"],
                    "present" if status == "unlocked" else "absent",
                )
                self.assertEqual(weapon_evidence["confidence"], "verified")
                self.assertEqual(
                    weapon_evidence["recordCount"],
                    1 if status == "unlocked" else 0,
                )
                self.assertEqual(
                    bool(weapon_evidence["records"]),
                    status == "unlocked",
                )
                if offset_hex is not None:
                    self.assertEqual(
                        weapon_evidence["records"][0]["offsetHex"],
                        offset_hex,
                    )
                    self.assertEqual(
                        weapon_evidence["records"][0]["qtyAfterId"],
                        1,
                    )

        missing_skills = {
            skill_id
            for skill_id, entity in entities_by_id.items()
            if entity["skillType"] == "combat_art" and entity["status"] == "missing"
        }
        self.assertEqual(
            missing_skills,
            {
                "shadowrush",
                "nightjar_slash_reversal",
                "ashina_cross",
                "praying_strikes_exorcism",
                "senpou_leaping_kicks",
                "high_monk",
                "shadowfall",
                "spiral_cloud_passage",
                "empowered_mortal_draw",
                "dragon_flash",
                "floating_passage",
                "one_mind",
            },
        )
        self.assertEqual(
            entities_by_id["shadowrush"]["acquisitionMetadata"]["skillPointCost"],
            6,
        )
        self.assertEqual(
            entities_by_id["shadowrush"]["acquisitionMetadata"][
                "requiredEsotericText"
            ]["name"],
            "Shinobi Esoteric Text",
        )
        self.assertEqual(
            entities_by_id["floating_passage"]["acquisitionMetadata"]["vendor"],
            "Pot Noble Harunaga",
        )
        self.assertEqual(
            entities_by_id["floating_passage"]["acquisitionMetadata"]["currency"],
            "5 Treasure Carp Scales",
        )
        self.assertEqual(
            entities_by_id["dragon_flash"]["acquisitionMetadata"]["boss"],
            "Isshin, The Sword Saint",
        )
        self.assertEqual(
            entities_by_id["one_mind"]["acquisitionMetadata"]["boss"],
            "Isshin Ashina",
        )

        unresolved_ids = {entry["id"] for entry in skills["unresolved"]}
        self.assertIn("ninjutsu_goods_ownership_record_shape", unresolved_ids)
        self.assertIn(
            "skill_costs_prerequisites_param_semantics",
            unresolved_ids,
        )
        self.assertIn("sakura_dance_skillparam_670_weapon_7700", unresolved_ids)
        self.assertIn("skills", self.result)
        self.assertIn("skills", probe.legacy_report(self.result)["parseSekiroSaveShape"])

    def test_non_combat_skill_inventory_evidence_and_ninjutsu_unknown(self) -> None:
        skills = self.result["skills"]
        entities_by_id = {
            entity["id"]: entity for entity in skills["entities"]
        }
        mapping_data = probe.load_json("skills.json")
        mappings_by_id = {
            entity["id"]: entity for entity in mapping_data["skills"]
        }

        expected_verified_skills = {
            "mid_air_deflection": (
                "Shinobi Arts",
                "Mid-air Deflection",
                "martial_art",
                2,
                200100,
                "A40D0300",
                "unlocked",
                "0x8fb20",
            ),
            "mikiri_counter": (
                "Shinobi Arts",
                "Mikiri Counter",
                "martial_art",
                4,
                200300,
                "6C0E0300",
                "unlocked",
                "0x8f9f0",
            ),
            "run_and_slide": (
                "Shinobi Arts",
                "Run and Slide",
                "martial_art",
                5,
                200400,
                "D00E0300",
                "unlocked",
                "0x8fa40",
            ),
            "mid_air_combat_arts": (
                "Shinobi Arts",
                "Mid-air Combat Arts",
                "martial_art",
                6,
                200500,
                "340F0300",
                "unlocked",
                "0x8fb10",
            ),
            "vault_over": (
                "Shinobi Arts",
                "Vault Over",
                "martial_art",
                7,
                200600,
                "980F0300",
                "missing",
                None,
            ),
            "suppress_presence": (
                "Shinobi Arts",
                "Suppress Presence",
                "latent_skill",
                60,
                620000,
                "E0750900",
                "unlocked",
                "0x8f880",
            ),
            "suppress_sound": (
                "Shinobi Arts",
                "Suppress Sound",
                "latent_skill",
                61,
                620100,
                "44760900",
                "missing",
                None,
            ),
            "shinobi_eyes": (
                "Shinobi Arts",
                "Shinobi Eyes",
                "latent_skill",
                70,
                660400,
                "B0130A00",
                "unlocked",
                "0x8fa30",
            ),
            "a_shinobis_karma_body": (
                "Shinobi Arts",
                "A Shinobi's Karma: Body",
                "latent_skill",
                75,
                650000,
                "10EB0900",
                "unlocked",
                "0x8fb30",
            ),
            "a_shinobis_karma_mind": (
                "Shinobi Arts",
                "A Shinobi's Karma: Mind",
                "latent_skill",
                76,
                650100,
                "74EB0900",
                "missing",
                None,
            ),
            "breath_of_life_light": (
                "Shinobi Arts",
                "Breath of Life: Light",
                "latent_skill",
                80,
                660000,
                "20120A00",
                "unlocked",
                "0x8ff60",
            ),
            "chasing_slice": (
                "Prosthetic Arts",
                "Chasing Slice",
                "martial_art",
                100,
                301000,
                "C8970400",
                "unlocked",
                "0x8f9d0",
            ),
            "fang_and_blade": (
                "Prosthetic Arts",
                "Fang and Blade",
                "martial_art",
                101,
                301100,
                "2C980400",
                "missing",
                None,
            ),
            "projected_force": (
                "Prosthetic Arts",
                "Projected Force",
                "martial_art",
                102,
                301200,
                "90980400",
                "missing",
                None,
            ),
            "living_force": (
                "Prosthetic Arts",
                "Living Force",
                "martial_art",
                103,
                301300,
                "F4980400",
                "missing",
                None,
            ),
            "grappling_hook_attack": (
                "Prosthetic Arts",
                "Grappling Hook Attack",
                "martial_art",
                104,
                200000,
                "400D0300",
                "unlocked",
                "0x8faa0",
            ),
            "mid_air_prosthetic_tool": (
                "Prosthetic Arts",
                "Mid-air Prosthetic Tool",
                "martial_art",
                105,
                200200,
                "080E0300",
                "unlocked",
                "0x8fa60",
            ),
            "emmas_medicine_potency": (
                "Prosthetic Arts",
                "Emma's Medicine: Potency",
                "latent_skill",
                170,
                640000,
                "00C40900",
                "unlocked",
                "0x8fd40",
            ),
            "emmas_medicine_aroma": (
                "Prosthetic Arts",
                "Emma's Medicine: Aroma",
                "latent_skill",
                171,
                640100,
                "64C40900",
                "unlocked",
                "0x8fdb0",
            ),
            "sculptors_karma_blood": (
                "Prosthetic Arts",
                "Sculptor's Karma: Blood",
                "latent_skill",
                175,
                650200,
                "D8EB0900",
                "missing",
                None,
            ),
            "sculptors_karma_scars": (
                "Prosthetic Arts",
                "Sculptor's Karma: Scars",
                "latent_skill",
                176,
                650300,
                "3CEC0900",
                "missing",
                None,
            ),
            "breath_of_nature_light": (
                "Ashina Arts",
                "Breath of Nature: Light",
                "latent_skill",
                265,
                660200,
                "E8120A00",
                "unlocked",
                "0x8fcf0",
            ),
            "ascending_carp": (
                "Ashina Arts",
                "Ascending Carp",
                "latent_skill",
                270,
                660600,
                "78140A00",
                "unlocked",
                "0x8fca0",
            ),
            "descending_carp": (
                "Ashina Arts",
                "Descending Carp",
                "latent_skill",
                275,
                660700,
                "DC140A00",
                "unlocked",
                "0x8fbe0",
            ),
            "flowing_water": (
                "Ashina Arts",
                "Flowing Water",
                "latent_skill",
                280,
                660800,
                "40150A00",
                "unlocked",
                "0x8fef0",
            ),
            "virtuous_deed": (
                "Temple Arts",
                "Virtuous Deed",
                "latent_skill",
                365,
                630000,
                "F09C0900",
                "missing",
                None,
            ),
            "most_virtuous_deed": (
                "Temple Arts",
                "Most Virtuous Deed",
                "latent_skill",
                366,
                630100,
                "549D0900",
                "missing",
                None,
            ),
            "devotion": (
                "Temple Arts",
                "Devotion",
                "latent_skill",
                370,
                660500,
                "14140A00",
                "missing",
                None,
            ),
            "shinobi_medicine_rank_1": (
                "Special Skills",
                "Shinobi Medicine Rank 1",
                "latent_skill",
                600,
                640200,
                "C8C40900",
                "unlocked",
                "0x8f940",
            ),
            "shinobi_medicine_rank_2": (
                "Special Skills",
                "Shinobi Medicine Rank 2",
                "latent_skill",
                601,
                640300,
                "2CC50900",
                "unlocked",
                "0x8faf0",
            ),
            "shinobi_medicine_rank_3": (
                "Special Skills",
                "Shinobi Medicine Rank 3",
                "latent_skill",
                602,
                640400,
                "90C50900",
                "unlocked",
                "0x8ffc0",
            ),
            "a_beasts_karma": (
                "Special Skills",
                "A Beast's Karma",
                "latent_skill",
                603,
                650400,
                "A0EC0900",
                "missing",
                None,
            ),
            "breath_of_life_shadow": (
                "Special Skills",
                "Breath of Life: Shadow",
                "latent_skill",
                604,
                660100,
                "84120A00",
                "unlocked",
                "0x8feb0",
            ),
            "breath_of_nature_shadow": (
                "Special Skills",
                "Breath of Nature: Shadow",
                "latent_skill",
                605,
                660300,
                "4C130A00",
                "unlocked",
                "0x8fd20",
            ),
            "mibu_breathing_technique": (
                "Special Skills",
                "Mibu Breathing Technique",
                "special_skill",
                610,
                680000,
                "40600A00",
                "unlocked",
                "0x8fdc0",
            ),
            "anti_air_deathblow": (
                "Special Skills",
                "Anti-air Deathblow",
                "special_skill",
                620,
                681000,
                "28640A00",
                "missing",
                None,
            ),
        }
        expected_type_counts = {
            "combat_art": 18,
            "martial_art": 11,
            "latent_skill": 23,
            "special_skill": 2,
            "ninjutsu": 3,
        }
        observed_type_counts = {
            skill_type: sum(
                1
                for entity in skills["entities"]
                if entity["skillType"] == skill_type
            )
            for skill_type in expected_type_counts
        }
        self.assertEqual(observed_type_counts, expected_type_counts)

        for skill_id, (
            skill_tree,
            name,
            skill_type,
            skill_param_row_id,
            skill_description_weapon_row_id,
            item_id_hex,
            status,
            offset_hex,
        ) in expected_verified_skills.items():
            with self.subTest(skill_id=skill_id):
                mapping = mappings_by_id[skill_id]
                entity = entities_by_id[skill_id]
                evidence_by_id = {
                    evidence["id"]: evidence for evidence in entity["evidence"]
                }
                weapon_evidence = evidence_by_id[
                    "skillDescriptionWeaponInventoryItem"
                ]

                self.assertEqual(mapping["skillTree"], skill_tree)
                self.assertEqual(mapping["name"], name)
                self.assertEqual(mapping["skillType"], skill_type)
                self.assertEqual(mapping["skillParamRowId"], skill_param_row_id)
                self.assertEqual(
                    mapping["skillDescriptionWeaponRowId"],
                    skill_description_weapon_row_id,
                )
                self.assertEqual(mapping["itemIdHex"], item_id_hex)
                self.assertEqual(entity["category"], "skill")
                self.assertEqual(entity["skillType"], skill_type)
                self.assertEqual(entity["skillTree"], skill_tree)
                self.assertEqual(entity["name"], name)
                self.assertEqual(entity["skillParamRowId"], skill_param_row_id)
                self.assertEqual(
                    entity["skillDescriptionWeaponRowId"],
                    skill_description_weapon_row_id,
                )
                self.assertEqual(entity["status"], status)
                self.assertEqual(entity["confidence"], "verified")
                self.assertEqual(weapon_evidence["type"], "inventory_weapon")
                self.assertEqual(weapon_evidence["itemIdHex"], item_id_hex)
                self.assertEqual(weapon_evidence["state"], status == "unlocked")
                self.assertEqual(
                    weapon_evidence["status"],
                    "present" if status == "unlocked" else "absent",
                )
                self.assertEqual(weapon_evidence["confidence"], "verified")
                self.assertEqual(
                    weapon_evidence["recordCount"],
                    1 if status == "unlocked" else 0,
                )
                self.assertEqual(
                    bool(weapon_evidence["records"]),
                    status == "unlocked",
                )
                self.assertIn(
                    "Status remains driven only by verified inventory_weapon evidence",
                    entity["acquisitionMetadata"]["ownershipInferencePolicy"],
                )
                if offset_hex is not None:
                    self.assertEqual(
                        weapon_evidence["records"][0]["offsetHex"],
                        offset_hex,
                    )
                    self.assertEqual(
                        weapon_evidence["records"][0]["qtyAfterId"],
                        1,
                    )

        expected_ninjutsu = {
            "bloodsmoke_ninjutsu": ("Bloodsmoke Ninjutsu", 2100, "34080000"),
            "puppeteer_ninjutsu": ("Puppeteer Ninjutsu", 2110, "3E080000"),
            "bestowal_ninjutsu": ("Bestowal Ninjutsu", 2120, "48080000"),
        }
        for skill_id, (name, goods_row_id, item_id_hex) in expected_ninjutsu.items():
            with self.subTest(skill_id=skill_id):
                mapping = mappings_by_id[skill_id]
                entity = entities_by_id[skill_id]
                evidence = entity["evidence"][0]

                self.assertEqual(mapping["skillType"], "ninjutsu")
                self.assertEqual(mapping["equipParamGoodsRowId"], goods_row_id)
                self.assertEqual(mapping["itemIdHex"], item_id_hex)
                self.assertEqual(entity["name"], name)
                self.assertEqual(entity["skillTree"], "Ninjutsu")
                self.assertEqual(entity["status"], "unknown")
                self.assertEqual(entity["confidence"], "unknown")
                self.assertEqual(
                    evidence["type"],
                    "unverified_inventory_item_candidate",
                )
                self.assertIsNone(evidence["state"])
                self.assertEqual(evidence["status"], "unknown")
                self.assertNotIn("records", evidence)
                self.assertEqual(mapping["statusRules"], [])

    def test_key_item_inventory_evidence_and_guidance(self) -> None:
        key_items = self.result["keyItems"]
        entities_by_id = {
            entity["id"]: entity for entity in key_items["entities"]
        }
        mapping_data = probe.load_json("key-items.json")

        self.assertEqual(
            key_items["coverage"],
            "progression-key-items-with-verified-inventory-evidence",
        )
        self.assertEqual(key_items["summary"]["total"], 33)
        self.assertEqual(key_items["summary"]["collected"], 12)
        self.assertEqual(key_items["summary"]["missing"], 6)
        self.assertEqual(key_items["summary"]["unknown"], 15)
        self.assertEqual(len(mapping_data["items"]), 33)

        expected_items = {
            "divine_dragons_tears": ("28230040", "missing", "verified", None),
            "frozen_tears": ("83230040", "missing", "verified", None),
            "fresh_serpent_viscera": ("E8230040", "missing", "verified", None),
            "dried_serpent_viscera": ("E9230040", "collected", "verified", "0x96980"),
            "fathers_bell_charm": ("33230040", "missing", "verified", None),
            "aromatic_flower": ("C7090040", "missing", "verified", None),
            "aromatic_branch": ("C6090040", "collected", "verified", "0x96960"),
            "mortal_blade": ("60090040", "collected", "verified", "0x96920"),
            "shelter_stone": ("C5090040", "collected", "verified", "0x96930"),
            "lotus_of_the_palace": ("C4090040", "collected", "verified", "0x969a0"),
            "shinobi_esoteric_text": ("680B0040", "collected", "verified", "0x967a0"),
            "prosthetic_esoteric_text": ("690B0040", "collected", "verified", "0x967c0"),
            "ashina_esoteric_text": ("6A0B0040", "collected", "verified", "0x96880"),
            "senpou_esoteric_text": ("6B0B0040", "collected", "verified", "0x96900"),
            "mushin_esoteric_text": ("6C0B0040", "missing", "verified", None),
            "holy_chapter_dragons_return": ("F9230040", "unknown", "unknown", None),
            "immortal_severance_text": ("FA230040", "collected", "verified", "0x96870"),
            "immortal_severance_scrap": ("FB230040", "collected", "verified", "0x969b0"),
            "fragrant_flower_note": ("FC230040", "collected", "verified", "0x96830"),
            "holy_chapter_infested": ("FF230040", "unknown", "unknown", None),
            "holy_chapter_infested_alt": ("0C240040", "unknown", "unknown", None),
            "mechanical_barrel": ("5E0B0040", "unknown", "unknown", None),
            "shuriken_wheel": ("E4250040", "unknown", "unknown", None),
            "roberts_firecrackers": ("EE250040", "unknown", "unknown", None),
            "flame_barrel": ("F8250040", "unknown", "unknown", None),
            "shinobi_axe_of_the_monkey": ("02260040", "unknown", "unknown", None),
            "mist_ravens_feathers": ("0C260040", "unknown", "unknown", None),
            "sabimaru": ("16260040", "unknown", "unknown", None),
            "iron_fortress": ("20260040", "unknown", "unknown", None),
            "large_fan": ("2A260040", "unknown", "unknown", None),
            "gyoubus_broken_horn": ("34260040", "unknown", "unknown", None),
            "slender_finger": ("3E260040", "unknown", "unknown", None),
            "malcontents_ring": ("3F260040", "unknown", "unknown", None),
        }

        self.assertEqual(set(entities_by_id), set(expected_items))
        for item_id, (item_id_hex, status, confidence, offset_hex) in expected_items.items():
            with self.subTest(item_id=item_id):
                entity = entities_by_id[item_id]
                ownership = entity["ownershipEvidence"][0]
                self.assertEqual(entity["category"], "key_item")
                self.assertEqual(entity["itemIdHex"], item_id_hex)
                self.assertEqual(entity["status"], status)
                self.assertEqual(entity["confidence"], confidence)
                self.assertTrue(entity["sourceReferences"])
                self.assertTrue(entity["acquisitionMetadata"])
                self.assertIn("confidence", entity["acquisitionMetadata"])
                self.assertEqual(ownership["type"], "inventory_item")
                self.assertEqual(ownership["itemIdHex"], item_id_hex)
                self.assertEqual(ownership["state"], status == "collected")
                self.assertEqual(
                    ownership["status"],
                    "present" if status == "collected" else "absent",
                )
                self.assertEqual(
                    ownership["recordCount"],
                    1 if status == "collected" else 0,
                )
                self.assertEqual(bool(ownership["records"]), status == "collected")
                if offset_hex is not None:
                    self.assertEqual(ownership["records"][0]["offsetHex"], offset_hex)
                    self.assertEqual(ownership["records"][0]["qtyAfterId"], 1)

        self.assertEqual(
            entities_by_id["iron_fortress"]["absenceSemantics"],
            "prosthetic_source_absence_not_missing",
        )
        self.assertEqual(entities_by_id["iron_fortress"]["status"], "unknown")
        self.assertEqual(
            entities_by_id["holy_chapter_dragons_return"]["absenceSemantics"],
            "absence_not_promoted_to_missing_until_retention_is_verified",
        )
        self.assertEqual(
            entities_by_id["mushin_esoteric_text"]["status"],
            "missing",
        )

        unresolved_ids = {entry["id"] for entry in key_items["unresolved"]}
        self.assertIn("prosthetic_source_item_consumption", unresolved_ids)
        self.assertIn("quest_context_item_retention", unresolved_ids)
        self.assertIn("key_item_acquisition_flags", unresolved_ids)
        self.assertIn("keyItems", self.result)
        self.assertIn("keyItems", probe.legacy_report(self.result)["parseSekiroSaveShape"])

    def test_golden_report_matches_generated_output(self) -> None:
        generated = json.dumps(probe.legacy_report(self.result), indent=2) + "\n"
        golden = probe.REPORT.read_text(encoding="utf-8")

        self.assertEqual(json.loads(golden), json.loads(generated))
        self.assertEqual(golden, generated)

    def test_json_mappings_validate_and_references_resolve(self) -> None:
        for path in sorted(probe.DATA_DIR.glob("*.json")):
            with self.subTest(mapping_file=path.name):
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                self.assertIsInstance(data, dict)
                self.assert_mapping_contract(path.name, data)

                collection_key = MAPPING_COLLECTIONS.get(path.name)
                if collection_key is not None:
                    ids = [entry["id"] for entry in data[collection_key]]
                    self.assertEqual(len(ids), len(set(ids)))

                rule_collection_key = RULE_COLLECTIONS.get(path.name)
                if rule_collection_key is not None:
                    for entity in data[rule_collection_key]:
                        evidence_ids = {
                            evidence["id"]
                            for evidence in entity.get("evidence", [])
                        }
                        self.assert_rule_contract(
                            f"{path.name}.{rule_collection_key}.{entity['id']}",
                            evidence_ids,
                            entity.get("statusRules", []),
                        )

        key_item_ids = {
            item["id"] for item in probe.load_json("key-items.json")["items"]
        }
        ending_data = probe.load_json("endings.json")
        self.assertNotIn("keyItems", ending_data)

        for ending in ending_data["endings"]:
            ending_evidence_ids = {
                evidence["id"]
                for evidence in [
                    *ending.get("completionEvidence", []),
                    *ending.get("availabilityEvidence", []),
                ]
            }
            for evidence in ending.get("availabilityEvidence", []):
                with self.subTest(ending=ending["id"], evidence=evidence["id"]):
                    self.assertNotEqual(evidence["type"], "inventory_item")
                    if evidence["type"] == "key_item":
                        self.assertIn(evidence["keyItemId"], key_item_ids)
            for requirement in ending.get("requiredItems", []):
                with self.subTest(
                    ending=ending["id"],
                    requirement=requirement["id"],
                    field="evidenceId",
                ):
                    self.assertIn("evidenceId", requirement)
                    self.assertIn(requirement["evidenceId"], ending_evidence_ids)
            self.assert_rule_contract(
                f"endings.json.endings.{ending['id']}.blockRules",
                ending_evidence_ids,
                ending.get("blockRules", []),
            )

    def test_report_schema_consistency(self) -> None:
        legacy_shape = probe.legacy_report(self.result)["parseSekiroSaveShape"]

        self.assertEqual(set(legacy_shape), set(EXPECTED_REPORT_STATUSES) | SUPPORT_REPORT_SECTIONS)
        for section in SUPPORT_REPORT_SECTIONS:
            with self.subTest(support_section=section):
                self.assertIn(section, legacy_shape)
                self.assertNotIn("summary", legacy_shape[section])
                self.assertNotIn("entities", legacy_shape[section])

        for category, allowed_statuses in EXPECTED_REPORT_STATUSES.items():
            with self.subTest(category=category):
                report = self.result[category]
                self.assertIn(category, legacy_shape)
                self.assertIn("entities", legacy_shape[category])
                self.assertIn("summary", legacy_shape[category])
                self.assertIn("entities", report)
                self.assertIn("summary", report)
                entities = report["entities"]
                summary = report["summary"]

                self.assertEqual(summary["total"], len(entities))
                self.assertIn("byStatus", summary)
                self.assertEqual(set(summary["byStatus"]), allowed_statuses)

                observed_statuses = {entity["status"] for entity in entities}
                self.assertLessEqual(observed_statuses, allowed_statuses)

                for status in allowed_statuses:
                    expected_count = sum(
                        1 for entity in entities if entity["status"] == status
                    )
                    self.assertEqual(summary["byStatus"][status], expected_count)
                    self.assertEqual(summary[status], expected_count)

                for entity in entities:
                    self.assertLessEqual(REQUIRED_ENTITY_FIELDS, set(entity))
                    self.assertIn(entity["status"], allowed_statuses)
                    self.assertIsInstance(entity["evidence"], list)
                    self.assertIsInstance(entity["acquisitionMetadata"], dict)
                    self.assertIsInstance(entity["notes"], list)
                    if entity["confidence"] == "verified":
                        self.assertTrue(entity["evidence"])

        self.assertEqual(
            self.result["bosses"]["summary"]["notDefeated"],
            self.result["bosses"]["summary"]["not_defeated"],
        )

    def test_report_evidence_contract(self) -> None:
        for category in EXPECTED_REPORT_STATUSES:
            for entity in self.result[category]["entities"]:
                block_evidence_ids = {
                    evidence["id"]
                    for evidence in entity.get("blockEvidence", [])
                    if isinstance(evidence, dict)
                }
                for evidence in entity["evidence"]:
                    with self.subTest(category=category, entity=entity["id"], evidence=evidence.get("id")):
                        self.assertLessEqual(REQUIRED_EVIDENCE_FIELDS, set(evidence))
                        self.assertIsInstance(evidence["id"], str)
                        self.assertIsInstance(evidence["confidence"], str)
                        self.assertIsInstance(evidence["status"], str)
                        self.assertIn(type(evidence["state"]), {bool, type(None)})
                        if "type" in evidence:
                            self.assertIn(evidence["type"], ALLOWED_REPORT_EVIDENCE_TYPES)
                        else:
                            self.assertEqual(category, "endings")
                            self.assertIn(evidence["id"], block_evidence_ids)
                            self.assertIn("when", evidence)
                            self.assertIn("conditionEvidence", evidence)

    def test_ending_specific_fields_are_generic_model_compatible(self) -> None:
        for ending in self.result["endings"]["entities"]:
            with self.subTest(ending=ending["id"]):
                self.assertLessEqual(
                    {
                        "availability",
                        "completionEvidence",
                        "availabilityEvidence",
                        "requiredItems",
                        "missingRequirements",
                        "unknownRequirements",
                        "blockEvidence",
                    },
                    set(ending),
                )
                expected_evidence = [
                    *ending["completionEvidence"],
                    *ending["availabilityEvidence"],
                    *ending["blockEvidence"],
                ]
                self.assertEqual(ending["evidence"], expected_evidence)
                self.assertIs(ending["acquisitionMetadata"], ending["guidance"])

    def test_legacy_report_fields_are_intentionally_preserved(self) -> None:
        report = probe.legacy_report(self.result)
        self.assertEqual(set(report), LEGACY_REPORT_KEYS)
        self.assertIs(report["gourd_seed_locations"], report["parseSekiroSaveShape"]["gourdSeeds"]["locations"])
        self.assertIs(report["prayer_bead_sample_flags"], report["parseSekiroSaveShape"]["prayerBeads"]["locations"])
        self.assertEqual(
            report["boss_memory_items_found"],
            [
                boss["name"]
                for boss in report["parseSekiroSaveShape"]["bosses"]["memoryItems"]
                if boss["status"] == "found"
            ],
        )

    def test_verified_statuses_are_evidence_backed(self) -> None:
        for category in [
            "prayerBeads",
            "gourdSeeds",
            "prosthetics",
            "prostheticUpgrades",
            "skills",
            "keyItems",
            "bosses",
            "endings",
        ]:
            for entity in self.result[category]["entities"]:
                with self.subTest(category=category, entity=entity["id"]):
                    if entity["confidence"] != "verified":
                        continue

                    evidence = entity["evidence"]
                    self.assertTrue(evidence)
                    self.assertTrue(
                        any(
                            item.get("state") is not None
                            or item.get("records")
                            or item.get("status") not in {None, "unknown"}
                            for item in evidence
                        )
                    )

    def test_community_guidance_is_not_promoted_to_verified_metadata(self) -> None:
        for category in [
            "prosthetics",
            "prostheticUpgrades",
            "skills",
            "keyItems",
            "endings",
        ]:
            for entity in self.result[category]["entities"]:
                metadata = entity["acquisitionMetadata"]
                references = metadata.get("sourceReferences", [])
                has_community_source = any(
                    "fextralife" in reference.get("url", "").lower()
                    for reference in references
                    if isinstance(reference, dict)
                )
                if has_community_source:
                    with self.subTest(category=category, entity=entity["id"]):
                        self.assertNotEqual(
                            str(metadata.get("confidence", "")).lower(),
                            "verified",
                        )

    def test_category_status_models(self) -> None:
        expected_statuses = {
            "prayerBeads": {"collected", "missing", "unknown"},
            "gourdSeeds": {"collected", "missing", "unknown"},
            "prosthetics": {"collected", "missing", "unknown"},
            "prostheticUpgrades": {"unlocked", "missing", "unknown"},
            "skills": {"unlocked", "missing", "unknown"},
            "keyItems": {"collected", "missing", "unknown"},
            "bosses": {"defeated", "not_defeated", "unknown"},
            "endings": {"completed", "available", "incomplete", "blocked", "unknown"},
        }

        observed_statuses = {
            "prayerBeads": {
                entity["status"]
                for entity in self.result["prayerBeads"]["entities"]
            },
            "gourdSeeds": {
                entity["status"] for entity in self.result["gourdSeeds"]["entities"]
            },
            "prosthetics": {
                entity["status"] for entity in self.result["prosthetics"]["entities"]
            },
            "prostheticUpgrades": {
                entity["status"]
                for entity in self.result["prostheticUpgrades"]["entities"]
            },
            "skills": {
                entity["status"] for entity in self.result["skills"]["entities"]
            },
            "keyItems": {
                entity["status"] for entity in self.result["keyItems"]["entities"]
            },
            "bosses": {
                entity["status"] for entity in self.result["bosses"]["entities"]
            },
            "endings": {
                entity["status"] for entity in self.result["endings"]["entities"]
            },
        }

        for category, statuses in observed_statuses.items():
            with self.subTest(category=category):
                self.assertLessEqual(statuses, expected_statuses[category])

    def test_ending_route_key_item_evidence(self) -> None:
        endings = self.result["endings"]
        entities_by_id = {
            entity["id"]: entity for entity in endings["entities"]
        }
        mapping_data = probe.load_json("endings.json")

        self.assertEqual(
            endings["coverage"],
            "ending-routes-with-verified-key-item-inventory-evidence",
        )
        self.assertEqual(endings["summary"]["total"], 4)
        self.assertEqual(endings["summary"]["completed"], 0)
        self.assertEqual(endings["summary"]["available"], 0)
        self.assertEqual(endings["summary"]["incomplete"], 3)
        self.assertEqual(endings["summary"]["blocked"], 0)
        self.assertEqual(endings["summary"]["unknown"], 1)
        self.assertEqual(
            {ending["id"] for ending in mapping_data["endings"]},
            {"shura", "immortal_severance", "purification", "return"},
        )
        self.assertNotIn("keyItems", mapping_data)

        expected_statuses = {
            "shura": ("unknown", "unknown"),
            "immortal_severance": ("incomplete", "probable"),
            "purification": ("incomplete", "probable"),
            "return": ("incomplete", "probable"),
        }
        for entity in entities_by_id.values():
            with self.subTest(ending_id=entity["id"]):
                self.assertEqual(entity["category"], "ending")
                self.assertEqual(
                    (entity["status"], entity["confidence"]),
                    expected_statuses[entity["id"]],
                )
                self.assertFalse(
                    entity["availability"]["currentCompletionSelectable"]
                )
                self.assertNotIn("completedEndingEvidence", entity)
                self.assertNotIn("routeAvailabilityEvidence", entity)
                self.assertNotIn("matchedBlockingRule", entity)
                self.assertTrue(entity["completionEvidence"])
                completion = entity["completionEvidence"][0]
                self.assertEqual(completion["type"], "unmapped")
                self.assertEqual(completion["status"], "unknown")
                self.assertIsNone(completion["state"])
                self.assertEqual(completion["confidence"], "unknown")
                self.assertTrue(entity["guidance"]["whatStillNeeded"])
                self.assertTrue(entity["guidance"]["sourceReferences"])
                self.assertNotIn(
                    "boss memory",
                    repr(entity["completionEvidence"]).lower(),
                )
                self.assertNotIn(
                    "boss memory",
                    repr(entity["availabilityEvidence"]).lower(),
                )
                self.assertNotIn(
                    "memory_inventory_item",
                    repr(entity["availabilityEvidence"]).lower(),
                )

        expected_item_states = {
            ("shura", "lotusOfThePalace"): (
                "lotus_of_the_palace",
                "C4090040",
                True,
                "present",
                "verified",
                "0x969a0",
            ),
            ("shura", "shelterStone"): (
                "shelter_stone",
                "C5090040",
                True,
                "present",
                "verified",
                "0x96930",
            ),
            ("shura", "nonShuraBranchIndicator"): (
                "aromatic_branch",
                "C6090040",
                True,
                "present",
                "verified",
                "0x96960",
            ),
            ("immortal_severance", "mortalBlade"): (
                "mortal_blade",
                "60090040",
                True,
                "present",
                "verified",
                "0x96920",
            ),
            ("immortal_severance", "divineDragonsTears"): (
                "divine_dragons_tears",
                "28230040",
                False,
                "absent",
                "verified",
                None,
            ),
            ("immortal_severance", "nonShuraBranchIndicator"): (
                "aromatic_branch",
                "C6090040",
                True,
                "present",
                "verified",
                "0x96960",
            ),
            ("purification", "divineDragonsTears"): (
                "divine_dragons_tears",
                "28230040",
                False,
                "absent",
                "verified",
                None,
            ),
            ("purification", "fathersBellCharm"): (
                "fathers_bell_charm",
                "33230040",
                False,
                "absent",
                "verified",
                None,
            ),
            ("purification", "aromaticFlower"): (
                "aromatic_flower",
                "C7090040",
                False,
                "absent",
                "verified",
                None,
            ),
            ("purification", "fragrantFlowerNote"): (
                "fragrant_flower_note",
                "FC230040",
                True,
                "present",
                "verified",
                "0x96830",
            ),
            ("return", "divineDragonsTears"): (
                "divine_dragons_tears",
                "28230040",
                False,
                "absent",
                "verified",
                None,
            ),
            ("return", "frozenTears"): (
                "frozen_tears",
                "83230040",
                False,
                "absent",
                "verified",
                None,
            ),
            ("return", "freshSerpentViscera"): (
                "fresh_serpent_viscera",
                "E8230040",
                False,
                "absent",
                "verified",
                None,
            ),
            ("return", "driedSerpentViscera"): (
                "dried_serpent_viscera",
                "E9230040",
                True,
                "present",
                "verified",
                "0x96980",
            ),
            ("return", "holyChapterDragonsReturn"): (
                "holy_chapter_dragons_return",
                "F9230040",
                None,
                "unknown",
                "unknown",
                None,
            ),
            ("return", "holyChapterInfested"): (
                "holy_chapter_infested",
                "FF230040",
                None,
                "unknown",
                "unknown",
                None,
            ),
            ("return", "holyChapterInfestedAlt"): (
                "holy_chapter_infested_alt",
                "0C240040",
                None,
                "unknown",
                "unknown",
                None,
            ),
        }

        for (ending_id, evidence_id), (
            key_item_id,
            item_id_hex,
            state,
            status,
            confidence,
            offset_hex,
        ) in expected_item_states.items():
            with self.subTest(ending_id=ending_id, evidence_id=evidence_id):
                evidence_by_id = {
                    evidence["id"]: evidence
                    for evidence in entities_by_id[ending_id]["availabilityEvidence"]
                }
                evidence = evidence_by_id[evidence_id]
                self.assertEqual(evidence["type"], "key_item")
                self.assertEqual(evidence["keyItemId"], key_item_id)
                self.assertEqual(evidence["itemIdHex"], item_id_hex)
                self.assertEqual(evidence["state"], state)
                self.assertEqual(evidence["status"], status)
                self.assertEqual(evidence["confidence"], confidence)
                self.assertEqual(evidence["keyItem"]["id"], key_item_id)
                self.assertEqual(evidence["keyItem"]["itemIdHex"], item_id_hex)
                self.assertEqual(evidence["keyItem"]["status"], "collected" if state is True else "missing" if state is False else "unknown")
                self.assertEqual(evidence["keyItem"]["confidence"], confidence)
                ownership = evidence["keyItem"]["ownershipEvidence"][0]
                self.assertEqual(ownership["type"], "inventory_item")
                self.assertEqual(ownership["itemIdHex"], item_id_hex)
                self.assertEqual(ownership["state"], state is True)
                self.assertEqual(ownership["status"], "present" if state is True else "absent")
                self.assertEqual(ownership["recordCount"], 1 if state is True else 0)
                self.assertEqual(bool(ownership["records"]), state is True)
                if offset_hex is not None:
                    self.assertEqual(
                        ownership["records"][0]["offsetHex"],
                        offset_hex,
                    )
                    self.assertEqual(
                        ownership["records"][0]["qtyAfterId"],
                        1,
                    )

        shura = entities_by_id["shura"]
        self.assertEqual(shura["status"], "unknown")
        self.assertEqual(
            shura["availability"]["state"],
            "potential_block_unverified",
        )
        self.assertEqual(shura["availability"]["blockReason"], "route_choice")
        self.assertIsNone(shura["availability"]["permanentlyBlocked"])
        self.assertEqual(shura["missingRequirements"], [])
        self.assertEqual(len(shura["blockEvidence"]), 1)
        self.assertEqual(shura["blockEvidence"][0]["id"], "non_shura_branch_committed")
        self.assertTrue(shura["blockEvidence"][0]["state"])
        self.assertEqual(shura["blockEvidence"][0]["confidence"], "probable")
        self.assertEqual(shura["blockEvidence"][0]["status"], "potential_block")
        self.assertFalse(shura["blockEvidence"][0]["statusDriving"])
        self.assertEqual(
            shura["blockEvidence"][0]["conditionEvidence"][0]["id"],
            "nonShuraBranchIndicator",
        )

        immortal = entities_by_id["immortal_severance"]
        self.assertEqual(immortal["status"], "incomplete")
        self.assertEqual(
            immortal["availability"]["state"],
            "missing_requirements",
        )
        self.assertFalse(immortal["availability"]["permanentlyBlocked"])
        self.assertEqual(immortal["blockEvidence"], [])
        self.assertEqual(
            {item["id"] for item in immortal["missingRequirements"]},
            {"divine_dragons_tears"},
        )
        self.assertIn(
            "Give Divine Dragon's Tears only",
            immortal["guidance"]["criticalChoice"],
        )

        purification = entities_by_id["purification"]
        self.assertEqual(purification["status"], "incomplete")
        self.assertEqual(
            {item["id"] for item in purification["missingRequirements"]},
            {
                "divine_dragons_tears",
                "fathers_bell_charm",
                "aromatic_flower",
            },
        )
        purification_evidence = {
            evidence["id"]: evidence
            for evidence in purification["availabilityEvidence"]
        }
        self.assertTrue(purification_evidence["fragrantFlowerNote"]["state"])
        self.assertEqual(
            purification_evidence["fragrantFlowerNote"]["role"],
            "quest_context_item",
        )
        self.assertIn(
            "Father's Bell Charm",
            purification["guidance"]["whatStillNeeded"][0],
        )

        return_route = entities_by_id["return"]
        self.assertEqual(return_route["status"], "incomplete")
        self.assertEqual(
            {item["id"] for item in return_route["missingRequirements"]},
            {
                "divine_dragons_tears",
                "frozen_tears",
                "fresh_serpent_viscera",
            },
        )
        return_evidence = {
            evidence["id"]: evidence
            for evidence in return_route["availabilityEvidence"]
        }
        self.assertTrue(return_evidence["driedSerpentViscera"]["state"])
        self.assertIsNone(return_evidence["holyChapterDragonsReturn"]["state"])
        self.assertIsNone(return_evidence["holyChapterInfested"]["state"])
        self.assertIsNone(return_evidence["holyChapterInfestedAlt"]["state"])
        self.assertNotIn(
            "holy_chapter_dragons_return",
            {item["id"] for item in return_route["missingRequirements"]},
        )
        self.assertIn(
            "Fresh Serpent Viscera",
            return_route["guidance"]["whatStillNeeded"][0],
        )

        unresolved_ids = {entry["id"] for entry in endings["unresolved"]}
        self.assertIn("ending_completion_flags", unresolved_ids)
        self.assertIn("ending_route_npc_quest_flags", unresolved_ids)
        self.assertIn("holy_chapter_retention_semantics", unresolved_ids)
        self.assertIn("endings", self.result)
        self.assertIn("endings", probe.legacy_report(self.result)["parseSekiroSaveShape"])


if __name__ == "__main__":
    unittest.main()
