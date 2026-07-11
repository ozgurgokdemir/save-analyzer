import type { SekiroStaticData } from "@save-analyzer/analyzer"

import bosses from "../../../../data/sekiro/bosses.json"
import endings from "../../../../data/sekiro/endings.json"
import eventFlagLayout from "../../../../data/sekiro/event-flag-layout.json"
import gourdSeeds from "../../../../data/sekiro/gourd-seeds.json"
import itemIds from "../../../../data/sekiro/item-ids.json"
import keyItems from "../../../../data/sekiro/key-items.json"
import prayerBeads from "../../../../data/sekiro/prayer-beads.json"
import prostheticUpgrades from "../../../../data/sekiro/prosthetic-upgrades.json"
import prosthetics from "../../../../data/sekiro/prosthetics.json"
import skills from "../../../../data/sekiro/skills.json"

export const sekiroStaticData = {
  eventFlagLayout,
  itemIds,
  gourdSeeds,
  prayerBeads,
  bosses,
  prosthetics,
  prostheticUpgrades,
  skills,
  keyItems,
  endings,
} as SekiroStaticData
