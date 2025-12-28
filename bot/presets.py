# presets.py
"""
Village Building Presets for different playstyles.

CORRECT Building IDs (from Travian/GotravSpeed):
- 5: Sawmill (+25% wood)
- 6: Brickworks (+25% clay)
- 7: Iron Foundry (+25% iron)
- 8: Flour Mill / Grain Mill (+25% wheat)
- 9: Bakery (+25% wheat, stacks with Flour Mill)
- 10: Warehouse
- 11: Granary
- 12: Smithy (troop upgrades)
- 13: Armory (troop upgrades)
- 14: Tournament Square (+troop speed)
- 15: Main Building
- 16: Rally Point
- 17: Marketplace
- 18: Embassy
- 19: Barracks
- 20: Stable
- 21: Siege Workshop
- 22: Academy
- 23: Cranny
- 24: Town Hall
- 25: Residence
- 26: Palace
- 28: Trade Office
- 31: City Wall (Romans)
- 32: Earth Wall (Teutons)
- 33: Palisade (Gauls)
- 34: Stonemason (capital only)
- 37: Hero's Mansion
- 38: Great Warehouse
- 39: Great Granary
- 44: Christmas Tree (+50% production bonus!)
"""

# ARMY VILLAGE - Capital with all military + Town Hall for celebrations
PRESET_ARMY = {
    "name": "Army Village (Capital)",
    "description": "Full military + Town Hall for celebrations. For your main attacking village.",
    "resource_target": 20,
    "buildings": [
        # PRIORITY ORDER: Main Building → Rally Point → Wall → Christmas Tree
        {"bid": 15, "name": "Main Building", "level": 20},
        {"bid": 16, "name": "Rally Point", "level": 20},
        {"bid": 31, "name": "Wall", "level": 20},  # Use 31 for Romans
        {"bid": 44, "name": "Christmas Tree", "level": 1},  # 50% bonus!
        
        # Military
        {"bid": 19, "name": "Barracks", "level": 20},
        {"bid": 20, "name": "Stable", "level": 20},
        {"bid": 21, "name": "Siege Workshop", "level": 20},
        {"bid": 22, "name": "Academy", "level": 20},
        {"bid": 12, "name": "Smithy", "level": 20},
        {"bid": 14, "name": "Tournament Square", "level": 20},
        {"bid": 37, "name": "Hero's Mansion", "level": 20},
        
        # Expansion & CP
        {"bid": 25, "name": "Residence", "level": 20},
        {"bid": 24, "name": "Town Hall", "level": 20},
        
        # Storage
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
    ]
}

# FARM VILLAGE - Resource production + storage, minimal military
PRESET_FARM = {
    "name": "Farm Village (Raiding Endpoint)",
    "description": "Max resource production + storage. Used for collecting resources via raids.",
    "resource_target": 30,
    "buildings": [
        # PRIORITY: Main Building → Rally Point → Christmas Tree
        {"bid": 15, "name": "Main Building", "level": 20},
        {"bid": 16, "name": "Rally Point", "level": 1},
        {"bid": 44, "name": "Christmas Tree", "level": 1},  # 50% bonus!
        {"bid": 19, "name": "Barracks", "level": 1},
        
        # Production Bonus Buildings (+25% each)
        {"bid": 5, "name": "Sawmill", "level": 5},
        {"bid": 6, "name": "Brickworks", "level": 5},
        {"bid": 7, "name": "Iron Foundry", "level": 5},
        {"bid": 8, "name": "Flour Mill", "level": 5},
        {"bid": 9, "name": "Bakery", "level": 5},
        
        # Storage - fill remaining slots (8 Warehouse + 6 Granary)
        {"bid": 10, "name": "Warehouse", "level": 20, "count": 8},
        {"bid": 11, "name": "Granary", "level": 20, "count": 6},
    ]
}

# QUICK SETTLE - For fast expansion on Fun server with gold
PRESET_QUICK_SETTLE = {
    "name": "Quick Settle (Gold/Fun Server)",
    "description": "Fast settling mode. Skip resource fields, use gold. Settle ASAP.",
    "resource_target": 0,  # SKIP resource fields
    "buildings": [
        # PRIORITY: Main Building → Residence → Christmas Tree
        {"bid": 15, "name": "Main Building", "level": 20},
        {"bid": 16, "name": "Rally Point", "level": 1},
        {"bid": 44, "name": "Christmas Tree", "level": 1},  # 50% bonus!
        {"bid": 25, "name": "Residence", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 10},
        {"bid": 11, "name": "Granary", "level": 10},
    ]
}

# FULL MODE - Standard balanced build
PRESET_FULL = {
    "name": "Full Mode (Balanced)",
    "description": "Standard balanced village with everything to level 20.",
    "resource_target": 20,
    "buildings": [
        {"bid": 15, "name": "Main Building", "level": 20},
        {"bid": 16, "name": "Rally Point", "level": 20},
        {"bid": 31, "name": "Wall", "level": 20},
        {"bid": 19, "name": "Barracks", "level": 20},
        {"bid": 20, "name": "Stable", "level": 20},
        {"bid": 21, "name": "Siege Workshop", "level": 20},
        {"bid": 22, "name": "Academy", "level": 20},
        {"bid": 12, "name": "Smithy", "level": 20},
        {"bid": 25, "name": "Residence", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 17, "name": "Marketplace", "level": 20},
        {"bid": 5, "name": "Sawmill", "level": 5},
        {"bid": 6, "name": "Brickworks", "level": 5},
        {"bid": 7, "name": "Iron Foundry", "level": 5},
        {"bid": 8, "name": "Flour Mill", "level": 5},
        {"bid": 9, "name": "Bakery", "level": 5},
        {"bid": 44, "name": "Christmas Tree", "level": 1},
    ]
}

# All presets indexed for menu
PRESETS = {
    "1": PRESET_ARMY,
    "2": PRESET_FARM,
    "3": PRESET_QUICK_SETTLE,
    "4": PRESET_FULL,
}

# Building ID lookup
BUILDING_IDS = {
    "sawmill": 5,
    "brickworks": 6,
    "iron_foundry": 7,
    "flour_mill": 8,
    "grain_mill": 8,
    "bakery": 9,
    "warehouse": 10,
    "granary": 11,
    "smithy": 12,
    "armory": 13,
    "tournament_square": 14,
    "main_building": 15,
    "rally_point": 16,
    "marketplace": 17,
    "embassy": 18,
    "barracks": 19,
    "stable": 20,
    "siege_workshop": 21,
    "academy": 22,
    "cranny": 23,
    "town_hall": 24,
    "residence": 25,
    "palace": 26,
    "trade_office": 28,
    "city_wall": 31,
    "earth_wall": 32,
    "palisade": 33,
    "stonemason": 34,
    "heros_mansion": 37,
    "great_warehouse": 38,
    "great_granary": 39,
    "christmas_tree": 44,
}


def get_preset_summary():
    """Return formatted summary of all presets."""
    lines = []
    for key, preset in PRESETS.items():
        lines.append(f"[{key}] {preset['name']}")
        lines.append(f"    {preset['description']}")
        lines.append(f"    Resources: {'Level ' + str(preset['resource_target']) if preset['resource_target'] else 'SKIP'}")
        lines.append(f"    Buildings: {len(preset['buildings'])}")
        lines.append("")
    return "\n".join(lines)
