# presets.py
"""
Village Building Presets for different playstyles.

Building IDs (for reference):
- 1: Woodcutter, 2: Clay Pit, 3: Iron Mine, 4: Cropland (resource fields 1-18)
- 15: Main Building
- 16: Rally Point
- 19: Barracks
- 20: Stable
- 21: Siege Workshop (Workshop)
- 22: Academy
- 11: Granary
- 10: Warehouse
- 12: Smithy
- 13: Armory
- 14: Tournament Square
- 17: Marketplace
- 18: Embassy
- 24: Town Hall
- 25: Residence
- 26: Palace
- 33: City Wall (varies by tribe)
- 37: Hero's Mansion
- 5: Sawmill
- 6: Brickyard
- 7: Iron Foundry
- 8: Grain Mill
- 9: Bakery
"""

# ARMY VILLAGE - Capital with all military + Town Hall for celebrations
PRESET_ARMY = {
    "name": "Army Village (Capital)",
    "description": "Full military + Town Hall for celebrations. For your main attacking village.",
    "resource_target": 20,  # Resource fields to level 20
    "buildings": [
        # Core
        {"bid": 15, "name": "Main Building", "level": 20},
        {"bid": 16, "name": "Rally Point", "level": 20},
        {"bid": 33, "name": "Wall", "level": 20},
        
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
        
        # Bonus
        {"bid": 44, "name": "Christmas Tree", "level": 1},  # 50% production bonus!
    ]
}

# FARM VILLAGE - Resource production + storage, minimal military
PRESET_FARM = {
    "name": "Farm Village (Raiding Endpoint)",
    "description": "Max resource production + storage. Used for collecting resources via raids.",
    "resource_target": 30,  # Resource fields to MAX
    "buildings": [
        # Production Bonus Buildings
        {"bid": 5, "name": "Sawmill", "level": 5},
        {"bid": 6, "name": "Brickyard", "level": 5},
        {"bid": 7, "name": "Iron Foundry", "level": 5},
        {"bid": 8, "name": "Grain Mill", "level": 5},
        {"bid": 9, "name": "Bakery", "level": 5},
        
        # Minimal Military (for raids to arrive)
        {"bid": 16, "name": "Rally Point", "level": 1},
        {"bid": 19, "name": "Barracks", "level": 1},
        
        # Fill rest with storage (15 slots)
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        {"bid": 11, "name": "Granary", "level": 20},
        
        # Bonus
        {"bid": 44, "name": "Christmas Tree", "level": 1},  # 50% production bonus!
    ]
}

# QUICK SETTLE - For fast expansion on Fun server with gold
PRESET_QUICK_SETTLE = {
    "name": "Quick Settle (Gold/Fun Server)",
    "description": "Fast settling mode. Skip resource fields, use gold. Settle ASAP.",
    "resource_target": 0,  # SKIP resource fields
    "buildings": [
        {"bid": 15, "name": "Main Building", "level": 20},
        {"bid": 25, "name": "Residence", "level": 20},
        {"bid": 10, "name": "Warehouse", "level": 10},
        {"bid": 11, "name": "Granary", "level": 10},
        {"bid": 16, "name": "Rally Point", "level": 1},
        
        # Bonus
        {"bid": 44, "name": "Christmas Tree", "level": 1},  # 50% production bonus!
    ]
}

# FULL MODE - Standard balanced build (everything to 20)
PRESET_FULL = {
    "name": "Full Mode (Balanced)",
    "description": "Standard balanced village with everything to level 20.",
    "resource_target": 20,
    "buildings": [
        {"bid": 15, "name": "Main Building", "level": 20},
        {"bid": 16, "name": "Rally Point", "level": 20},
        {"bid": 33, "name": "Wall", "level": 20},
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
        {"bid": 6, "name": "Brickyard", "level": 5},
        {"bid": 7, "name": "Iron Foundry", "level": 5},
        {"bid": 8, "name": "Grain Mill", "level": 5},
        {"bid": 9, "name": "Bakery", "level": 5},
        
        # Bonus
        {"bid": 44, "name": "Christmas Tree", "level": 1},  # 50% production bonus!
    ]
}

# All presets indexed for menu
PRESETS = {
    "1": PRESET_ARMY,
    "2": PRESET_FARM,
    "3": PRESET_QUICK_SETTLE,
    "4": PRESET_FULL,
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
