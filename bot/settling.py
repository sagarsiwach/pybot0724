# settling.py
"""
Village settling module for Travian.

Features:
- CP requirements table
- Celebration logic (Town Hall)
- Build Residence if needed
- Train settlers
- Find empty spots
- Settle new village
"""

import asyncio
import httpx
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
}

# CP Requirements for each village number (3x speed / GotravSpeed)
# Format: village_number -> required_cp
CP_REQUIREMENTS = {
    1: 0,
    2: 500,
    3: 2600,
    4: 6700,
    5: 12900,
    6: 21600,
    7: 32900,
    8: 46900,
    9: 63700,
    10: 83500,
    11: 106400,
    12: 132500,
    13: 161900,
    14: 194500,
    15: 230700,
    16: 270400,
    17: 313700,
    18: 360900,
    19: 411300,
    20: 465700,
    21: 524100,
    22: 586300,
    23: 652500,
    24: 722700,
    25: 797100,
    26: 875500,
    27: 958100,
    28: 1045100,
    29: 1136200,
    30: 1231700,
    31: 1331600,
    32: 1435900,
    33: 1544700,
    34: 1658000,
    35: 1775800,
    36: 1898300,
    37: 2025300,
    38: 2157100,
    39: 2293500,
    40: 2434700,
    # Beyond 40, use formula or extend
}

def get_required_cp(village_count: int) -> int:
    """Get required CP for the next village."""
    next_village = village_count + 1
    if next_village in CP_REQUIREMENTS:
        return CP_REQUIREMENTS[next_village]
    # For villages > 40, approximate
    return int(2434700 * (1.03 ** (next_village - 40)))


async def get_current_cp(client, server_url: str) -> tuple:
    """
    Get current CP and CP production from the game.
    
    Returns: (current_cp, cp_production_per_day, village_count)
    """
    # Check profile or statistics page for CP info
    response = await client.get(f"{server_url}/spieler.php")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    current_cp = 0
    cp_production = 0
    village_count = 0
    
    # Look for CP display
    # Usually shown as "Culture Points: X/Y" or similar
    for td in soup.find_all(['td', 'span', 'div']):
        text = td.text.lower()
        if 'culture' in text or 'cp' in text or 'kulturpunkt' in text:
            # Try to extract numbers
            import re
            numbers = re.findall(r'[\d,]+', text)
            if numbers:
                current_cp = int(numbers[0].replace(',', ''))
                if len(numbers) > 1:
                    cp_production = int(numbers[1].replace(',', ''))
    
    # Count villages
    village_links = soup.find_all('a', href=lambda x: x and 'village' in str(x).lower())
    village_count = len(set([v.get('href') for v in village_links if v.get('href')]))
    
    # If we couldn't find village count, try profile
    if village_count == 0:
        response = await client.get(f"{server_url}/profile.php")
        soup = BeautifulSoup(response.text, 'html.parser')
        village_table = soup.find('table', {'id': 'villages'})
        if village_table:
            rows = village_table.find_all('tr')
            village_count = max(1, len(rows) - 1)  # Subtract header
    
    return current_cp, cp_production, max(1, village_count)


async def run_celebration(client, server_url: str, callback=None) -> bool:
    """
    Start a celebration in Town Hall.
    
    Returns: True if celebration started
    """
    from bot.construction import find_building_position
    
    # Find Town Hall
    town_hall_pos = await find_building_position(client, server_url, "Town Hall")
    
    if town_hall_pos == -1:
        if callback:
            callback("Town Hall not found! Cannot run celebration.")
        return False
    
    # Go to Town Hall
    response = await client.get(f"{server_url}/build.php?id={town_hall_pos}")
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find celebration options
    # Usually "Small celebration" and "Great celebration"
    celebration_link = None
    
    for link in soup.find_all('a'):
        href = link.get('href', '')
        text = link.text.lower()
        # Look for celebration button
        if 'celebration' in text or 'fest' in text or 'party' in text:
            if '&a=' in href or 'action' in href:
                celebration_link = href
                break
    
    # Also check for form buttons
    if not celebration_link:
        for btn in soup.find_all(['button', 'input']):
            name = btn.get('name', '').lower()
            text = (btn.get('value', '') + btn.text if hasattr(btn, 'text') else btn.get('value', '')).lower()
            if 'celebration' in text or 'fest' in text or name.startswith('s'):
                # This might be a form submit
                form = btn.find_parent('form')
                if form:
                    action = form.get('action', f'build.php?id={town_hall_pos}')
                    # Submit the form
                    form_data = {}
                    for inp in form.find_all('input'):
                        n = inp.get('name')
                        v = inp.get('value', '')
                        if n:
                            form_data[n] = v
                    
                    response = await client.post(f"{server_url}/{action}", data=form_data)
                    if response.status_code == 200:
                        if callback:
                            callback("Celebration started!")
                        return True
    
    if celebration_link:
        if not celebration_link.startswith('http'):
            celebration_link = f"{server_url}/{celebration_link}"
        
        response = await client.get(celebration_link)
        if response.status_code == 200:
            if callback:
                callback("Celebration started!")
            return True
    
    if callback:
        callback("Could not start celebration")
    return False


async def check_and_celebrate(cookies, server_url: str, callback=None) -> bool:
    """
    Check if CP is enough for next village. If not, run celebrations.
    
    Returns: True if we have enough CP (or started celebration)
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        current_cp, cp_prod, village_count = await get_current_cp(client, server_url)
        required_cp = get_required_cp(village_count)
        
        if callback:
            callback(f"Current CP: {current_cp:,}")
            callback(f"Villages: {village_count}")
            callback(f"Required for village {village_count + 1}: {required_cp:,}")
        
        if current_cp >= required_cp:
            if callback:
                callback("✓ Enough CP to settle!")
            return True
        else:
            cp_needed = required_cp - current_cp
            if callback:
                callback(f"Need {cp_needed:,} more CP. Starting celebration...")
            
            success = await run_celebration(client, server_url, callback)
            return success


def generate_spiral_ids(center_id: int, max_villages: int = 100, max_radius: int = 10):
    """
    Generate village IDs in a spiral pattern from center.
    
    The map is 401x401 (-200 to +200), so moving by 1 in Y = +/- 401 in ID.
    Moving by 1 in X = +/- 1 in ID.
    """
    ids = [center_id]
    radius = 1
    
    while len(ids) < max_villages and radius <= max_radius:
        # Top row
        for x in range(-radius, radius + 1):
            ids.append(center_id + x + (radius * 401))
        # Right column
        for y in range(radius - 1, -radius - 1, -1):
            ids.append(center_id + radius + (y * 401))
        # Bottom row
        for x in range(radius - 1, -radius - 1, -1):
            ids.append(center_id + x - (radius * 401))
        # Left column
        for y in range(-radius + 1, radius):
            ids.append(center_id - radius + (y * 401))
        
        radius += 1
    
    return ids[:max_villages]


async def check_if_empty(client, server_url: str, village_id: int) -> bool:
    """Check if a map position is an empty spot (available for settling)."""
    try:
        response = await client.get(f"{server_url}/village3.php?id={village_id}", timeout=10.0)
        text = response.text.lower()
        
        # Empty spots have "building a new village" text
        if 'building a new village' in text or '»building a new village' in text:
            return True
        
        # Also check for settle button
        if 'settle' in text and 'settler' in text:
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Error checking village ID {village_id}: {e}")
        return False


async def find_empty_spots(cookies, server_url: str, center_village_id: int = 160801, 
                           max_spots: int = 10, max_radius: int = 15, callback=None):
    """
    Find empty spots near a center position.
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        center_village_id: Village ID to search around (default is 0|0 = 160801)
        max_spots: Maximum number of spots to find
        max_radius: How far to search
        callback: Progress callback
    
    Returns:
        List of empty spot village IDs
    """
    spots = []
    ids_to_check = generate_spiral_ids(center_village_id, max_villages=500, max_radius=max_radius)
    
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        for i, vid in enumerate(ids_to_check):
            if len(spots) >= max_spots:
                break
            
            if callback and i % 20 == 0:
                callback(f"Scanned {i}/{len(ids_to_check)} positions, found {len(spots)} spots...")
            
            if await check_if_empty(client, server_url, vid):
                spots.append(vid)
                if callback:
                    callback(f"Found empty spot: ID {vid}")
                logger.info(f"Found empty spot at village ID {vid}")
    
    return spots


async def get_coordinates_from_id(village_id: int) -> tuple:
    """
    Convert village ID to (x, y) coordinates.
    
    Map is 401x401, center (0,0) is at ID 160801.
    Formula: id = (200 + y) * 401 + (200 + x) + 1
    """
    # Reverse: x = (id - 1) % 401 - 200, y = (id - 1) // 401 - 200
    id_adj = village_id - 1
    x = (id_adj % 401) - 200
    y = (id_adj // 401) - 200
    return (x, y)


async def check_settlers_available(client, server_url: str, residence_pos: int) -> int:
    """Check how many settlers are available in Residence/Palace."""
    response = await client.get(f"{server_url}/build.php?id={residence_pos}")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for settler count in the troops available
    settlers = 0
    for elem in soup.find_all(['td', 'span', 'div']):
        text = elem.text.lower()
        if 'settler' in text:
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                settlers = int(numbers[0])
                break
    
    return settlers


async def smart_settle(cookies, server_url: str, callback=None):
    """
    Smart settling with all checks:
    1. Check CP - run celebration if needed
    2. Check Residence - build if needed
    3. Check settlers - train if needed
    4. Find empty spot
    5. Settle
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        callback: Progress callback
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        if callback:
            callback("=== SMART SETTLE ===")
        
        # Step 1: Check CP
        if callback:
            callback("Step 1: Checking Culture Points...")
        
        current_cp, cp_prod, village_count = await get_current_cp(client, server_url)
        required_cp = get_required_cp(village_count)
        
        if callback:
            callback(f"  Current CP: {current_cp:,}")
            callback(f"  Villages: {village_count}")
            callback(f"  Required for #{village_count + 1}: {required_cp:,}")
        
        if current_cp < required_cp:
            cp_needed = required_cp - current_cp
            if callback:
                callback(f"  Need {cp_needed:,} more CP!")
                callback("  Running celebration...")
            
            await run_celebration(client, server_url, callback)
            
            if callback:
                callback("  ⚠ Wait for celebration to complete before settling")
            return False
        
        if callback:
            callback("  ✓ Enough CP!")
        
        # Step 2: Check Residence
        if callback:
            callback("\nStep 2: Checking Residence...")
        
        from bot.construction import find_building_position, construct_building, find_empty_slot
        
        residence_pos = await find_building_position(client, server_url, "Residence")
        
        if residence_pos == -1:
            # Check for Palace instead
            residence_pos = await find_building_position(client, server_url, "Palace")
        
        if residence_pos == -1:
            if callback:
                callback("  No Residence/Palace found! Building...")
            
            empty_slot = await find_empty_slot(client, server_url)
            if empty_slot == -1:
                if callback:
                    callback("  ✗ No empty building slots!")
                return False
            
            from bot.presets import BUILDING_IDS
            success = await construct_building(client, server_url, empty_slot, BUILDING_IDS['residence'])
            
            if success:
                residence_pos = empty_slot
                if callback:
                    callback(f"  ✓ Residence built at position {empty_slot}")
            else:
                if callback:
                    callback("  ✗ Failed to build Residence")
                return False
        else:
            if callback:
                callback(f"  ✓ Residence found at position {residence_pos}")
        
        # Step 3: Check settlers
        if callback:
            callback("\nStep 3: Checking settlers...")
        
        settlers = await check_settlers_available(client, server_url, residence_pos)
        
        if callback:
            callback(f"  Available settlers: {settlers}")
        
        if settlers < 3:
            if callback:
                callback(f"  Need {3 - settlers} more settlers!")
                callback("  Training settlers...")
            
            from bot.troop_training import train_settlers
            await train_settlers(cookies, server_url, residence_pos, 3 - settlers, callback)
            
            if callback:
                callback("  ⚠ Wait for settlers to train before settling")
            return False
        
        if callback:
            callback("  ✓ Have 3 settlers!")
        
        # Step 4: Find empty spot
        if callback:
            callback("\nStep 4: Finding empty spot...")
        
        spots = await find_empty_spots(cookies, server_url, max_spots=1, max_radius=25, callback=callback)
        
        if not spots:
            if callback:
                callback("  ✗ No empty spots found!")
            return False
        
        target = spots[0]
        coords = await get_coordinates_from_id(target)
        
        if callback:
            callback(f"  ✓ Target: ({coords[0]}|{coords[1]})")
        
        # Step 5: Settle
        if callback:
            callback("\nStep 5: Settling...")
        
        response = await client.get(f"{server_url}/village3.php?id={target}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find settle link
        settle_link = None
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.text.lower()
            if 'settle' in text or 'a2b.php' in href:
                settle_link = href
                break
        
        if not settle_link:
            if callback:
                callback("  ✗ Could not find settle button")
            return False
        
        if not settle_link.startswith('http'):
            settle_link = f"{server_url}/{settle_link}"
        
        response = await client.get(settle_link)
        
        if response.status_code == 200:
            if callback:
                callback(f"  ✓ SETTLED at ({coords[0]}|{coords[1]})!")
            return True
        else:
            if callback:
                callback(f"  ✗ Settling failed: HTTP {response.status_code}")
            return False


async def auto_settle(cookies, server_url: str, callback=None):
    """Wrapper for smart_settle - for backwards compatibility."""
    return await smart_settle(cookies, server_url, callback)
