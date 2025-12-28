# construction.py
import httpx
import logging
from bs4 import BeautifulSoup
from .database import get_buildings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Headers to prevent 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
}


async def get_field_info(client, server_url: str, position_id: int) -> dict:
    """Get info about a resource field or building."""
    response = await client.get(f"{server_url}/build.php?id={position_id}")
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Get name from h1
    h1 = soup.find('h1')
    name = h1.text.strip() if h1 else f"Position {position_id}"
    
    # Extract level from name (e.g., "Woodcutter level 10")
    level = 0
    if 'level' in name.lower():
        try:
            level = int(name.lower().split('level')[1].strip().split()[0])
        except:
            pass
    
    # Find upgrade link
    build_link = soup.find("a", class_="build")
    upgrade_url = None
    if build_link:
        href = build_link.get("href", "")
        if "&k=" in href:
            upgrade_url = href
    
    return {
        'position': position_id,
        'name': name.split(' level')[0].strip() if ' level' in name.lower() else name,
        'level': level,
        'upgrade_url': upgrade_url
    }


async def upgrade_field(client, server_url: str, position_id: int) -> bool:
    """Upgrade a single resource field or building once."""
    response = await client.get(f"{server_url}/build.php?id={position_id}")
    soup = BeautifulSoup(response.text, "html.parser")
    build_link = soup.find("a", class_="build")
    
    if build_link is None:
        return False
    
    href = build_link.get("href", "")
    if "&k=" not in href:
        return False
    
    # The upgrade URL can be village1.php or village2.php
    upgrade_response = await client.get(f"{server_url}/{href}")
    return upgrade_response.status_code == 200


async def construct_building(client, server_url: str, position_id: int, building_id: int) -> bool:
    """
    Construct a NEW building at an empty slot.
    
    Args:
        client: httpx client with cookies
        server_url: Server URL (e.g., https://netus.gotravspeed.com)
        position_id: Building slot position (19-40)
        building_id: Building type ID (e.g., 19 for Barracks, 10 for Warehouse)
    
    Returns:
        True if construction started successfully
    """
    # First, check if the slot is empty (shows construction page)
    response = await client.get(f"{server_url}/build.php?id={position_id}")
    
    if 'construction of a new building' not in response.text.lower():
        logger.warning(f"Position {position_id} is not empty - cannot construct new building")
        return False
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the build link for the specific building ID
    # Format: village2.php?id=X&b=Y&k=CSRF
    build_links = soup.find_all('a', class_='build', href=lambda x: x and f'&b={building_id}&' in str(x) or x.endswith(f'&b={building_id}'))
    
    if not build_links:
        # Try different pattern: href containing b=ID anywhere
        for link in soup.find_all('a', class_='build'):
            href = link.get('href', '')
            if f'&b={building_id}' in href:
                build_links = [link]
                break
    
    if not build_links:
        logger.warning(f"Building ID {building_id} not available at position {position_id}")
        return False
    
    # Click the build link
    href = build_links[0].get('href', '')
    response = await client.get(f"{server_url}/{href}")
    
    if response.status_code == 200:
        logger.info(f"Started construction of building ID {building_id} at position {position_id}")
        return True
    else:
        logger.error(f"Failed to construct building: HTTP {response.status_code}")
        return False


async def find_empty_slot(client, server_url: str) -> int:
    """Find an empty building slot (19-40). Returns position or -1 if none found."""
    for pos in range(19, 41):
        response = await client.get(f"{server_url}/build.php?id={pos}")
        if 'construction of a new building' in response.text.lower():
            return pos
    return -1


async def apply_preset(cookies, server_url: str, preset: dict, callback=None):
    """
    Apply a building preset to the current village.
    
    This will:
    1. Scan all positions to find existing buildings
    2. For each building in preset, find or construct it
    3. Upgrade all buildings to their target levels
    """
    import asyncio
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS, timeout=30.0) as client:
        # Step 1: Scan all positions to see what's already built
        if callback:
            callback("Scanning existing buildings...")
        
        position_data = {}  # pos -> {'name': str, 'level': int, 'is_empty': bool}
        
        import re
        for pos in range(19, 41):
            # Add delay to avoid rate limiting
            await asyncio.sleep(0.3)
            
            try:
                response = await client.get(f"{server_url}/build.php?id={pos}")
                
                # Handle rate limiting
                if response.status_code == 503:
                    if callback:
                        callback(f"  [{pos}] Rate limited, waiting...")
                    await asyncio.sleep(2)
                    response = await client.get(f"{server_url}/build.php?id={pos}")
                
                soup = BeautifulSoup(response.text, "html.parser")
                h1 = soup.find('h1')
                
                if h1:
                    text = h1.text.strip()
                    text_lower = text.lower()
                    
                    # Skip error pages
                    if '503' in text or 'error' in text_lower or 'unavailable' in text_lower:
                        if callback:
                            callback(f"  [{pos}] Server error, skipping")
                        continue
                    
                    if 'construction' in text_lower or 'new building' in text_lower:
                        position_data[pos] = {'name': None, 'level': 0, 'is_empty': True}
                    else:
                        # Extract name and level using regex (case insensitive)
                        match = re.match(r'^(.+?)\s+level\s*(\d+)', text, re.IGNORECASE)
                        if match:
                            bname = match.group(1).strip()
                            level = int(match.group(2))
                        else:
                            bname = text
                            level = 1
                        position_data[pos] = {'name': bname, 'level': level, 'is_empty': False}
                        if callback:
                            callback(f"  [{pos}] {bname} (Lv {level})")
            except Exception as e:
                if callback:
                    callback(f"  [{pos}] Error: {e}")
                continue
        
        # Show what was found
        empty_count = sum(1 for p in position_data.values() if p['is_empty'])
        if callback:
            callback(f"Summary: {len(position_data) - empty_count} buildings, {empty_count} empty slots")
        
        # Step 2: Process each building in preset
        buildings_to_build = preset.get('buildings', [])
        used_positions = set()
        
        for building in buildings_to_build:
            bid = building['bid']
            name = building['name']
            target_level = building.get('level', 1)
            count = building.get('count', 1)
            
            for i in range(count):
                if callback:
                    if count > 1:
                        callback(f"Processing: {name} ({i+1}/{count})...")
                    else:
                        callback(f"Processing: {name}...")
                
                # Find existing building of this type
                existing_pos = -1
                for pos, data in position_data.items():
                    if pos in used_positions:
                        continue
                    if data['name'] and name.lower() in data['name'].lower():
                        existing_pos = pos
                        used_positions.add(pos)
                        if callback:
                            callback(f"  Found existing {data['name']} at slot {pos} (Lv {data['level']})")
                        break
                
                # If not found, try to build new
                if existing_pos == -1:
                    # Find empty slot
                    empty_pos = -1
                    for pos, data in position_data.items():
                        if pos in used_positions:
                            continue
                        if data['is_empty']:
                            empty_pos = pos
                            break
                    
                    if empty_pos == -1:
                        if callback:
                            callback(f"  ✗ No empty slots for {name}")
                        continue
                    
                    if callback:
                        callback(f"  Building {name} at slot {empty_pos}...")
                    
                    # Delay before construction
                    await asyncio.sleep(0.5)
                    success = await construct_building(client, server_url, empty_pos, bid)
                    if success:
                        existing_pos = empty_pos
                        used_positions.add(empty_pos)
                        position_data[empty_pos] = {'name': name, 'level': 1, 'is_empty': False}
                        if callback:
                            callback(f"  ✓ {name} constructed!")
                    else:
                        if callback:
                            callback(f"  ✗ Failed to construct {name}")
                        continue
                
                # Upgrade to target level
                if existing_pos > 0 and target_level > 1:
                    current = position_data.get(existing_pos, {}).get('level', 1)
                    
                    if current >= target_level:
                        if callback:
                            callback(f"  ✓ Already at level {current}")
                        continue
                    
                    if callback:
                        callback(f"  Upgrading from {current} to {target_level}...")
                    
                    upgrades_done = 0
                    while current < target_level:
                        await asyncio.sleep(0.3)  # Delay between upgrades
                        
                        info = await get_field_info(client, server_url, existing_pos)
                        current = info['level']
                        
                        if current >= target_level:
                            break
                        
                        if info['upgrade_url']:
                            response = await client.get(f"{server_url}/{info['upgrade_url']}")
                            if response.status_code == 200:
                                upgrades_done += 1
                                current += 1
                                if callback:
                                    callback(f"    → Level {current}")
                            else:
                                if callback:
                                    callback(f"  ✗ Upgrade failed (HTTP {response.status_code})")
                                break
                        else:
                            if callback:
                                callback(f"  ⚠ Waiting for resources/queue (at Lv {current})")
                            break
                    
                    # Re-fetch actual level
                    info = await get_field_info(client, server_url, existing_pos)
                    final_level = info['level']
                    position_data[existing_pos]['level'] = final_level
                    
                    if callback:
                        if final_level >= target_level:
                            callback(f"  ✓ {name} at level {final_level}")
                        else:
                            callback(f"  ⚠ {name} at level {final_level}/{target_level}")


async def find_building_position(client, server_url: str, building_name: str) -> int:
    """Find position of an existing building by name. Returns -1 if not found."""
    for pos in range(19, 41):
        response = await client.get(f"{server_url}/build.php?id={pos}")
        soup = BeautifulSoup(response.text, "html.parser")
        h1 = soup.find('h1')
        if h1:
            text = h1.text.lower()
            if building_name.lower() in text and 'construction' not in text:
                return pos
    return -1


async def demolish_building(cookies, server_url: str, position_id: int, callback=None) -> bool:
    """
    Demolish/destroy a building at a specific position.
    
    This is done through the Main Building's demolish feature.
    The building will be reduced level by level to 0.
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        position_id: Position of building to demolish (19-40)
        callback: Progress callback
    
    Returns:
        True if demolition started
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        # Find Main Building position (usually position 26, but check)
        main_building_pos = await find_building_position(client, server_url, "Main Building")
        
        if main_building_pos == -1:
            if callback:
                callback("Main Building not found!")
            return False
        
        # Go to Main Building page
        response = await client.get(f"{server_url}/build.php?id={main_building_pos}")
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for demolish/destroy link or tab
        # Usually it's a link like build.php?id=26&t=2 or similar
        demolish_link = None
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.text.lower()
            if 'demolish' in text or 'destroy' in text or 'remove' in text or 't=2' in href:
                demolish_link = href
                break
        
        if not demolish_link:
            if callback:
                callback("Demolish feature not found in Main Building")
            return False
        
        # Go to demolish page
        if not demolish_link.startswith('http'):
            demolish_link = f"{server_url}/{demolish_link}"
        
        response = await client.get(demolish_link)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the building in the list and click demolish
        # Usually a form with building position select
        form = soup.find('form')
        if not form:
            if callback:
                callback("Demolish form not found")
            return False
        
        # Submit demolish for the specific position
        # The form usually has a select for building position
        form_data = {
            'demolish': str(position_id),
            's1': 'OK'
        }
        
        response = await client.post(f"{server_url}/build.php?id={main_building_pos}&t=2", data=form_data)
        
        if response.status_code == 200:
            if callback:
                callback(f"Started demolishing building at position {position_id}")
            logger.info(f"Demolishing building at position {position_id}")
            return True
        else:
            if callback:
                callback(f"Demolish failed: HTTP {response.status_code}")
            return False


async def upgrade_field_to_level(cookies, server_url: str, position_id: int, target_level: int) -> tuple:
    """
    Upgrade a field to a target level.
    Returns (success_count, current_level)
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        success = 0
        current = 0
        
        for _ in range(100):  # Safety limit
            info = await get_field_info(client, server_url, position_id)
            current = info['level']
            
            if current >= target_level:
                break
            
            if info['upgrade_url'] is None:
                break
            
            # Upgrade
            response = await client.get(f"{server_url}/{info['upgrade_url']}")
            if response.status_code == 200:
                success += 1
                logger.info(f"{info['name']} upgraded to level {current + 1}")
            else:
                break
        
        return success, current


async def upgrade_all_resources(cookies, server_url: str, target_level: int = 30, callback=None):
    """
    Upgrade all resource fields (1-18) to target level.
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        results = []
        
        for pos in range(1, 19):
            info = await get_field_info(client, server_url, pos)
            
            if info['level'] >= target_level:
                results.append((pos, info['name'], info['level'], 0, "Already at target"))
                if callback:
                    callback(f"[{pos}] {info['name']} - Level {info['level']} ✓")
                continue
            
            # Upgrade loop
            upgrades = 0
            current = info['level']
            
            while current < target_level:
                # Re-fetch to get new upgrade link
                info = await get_field_info(client, server_url, pos)
                current = info['level']
                
                if current >= target_level:
                    break
                
                if info['upgrade_url'] is None:
                    break
                
                response = await client.get(f"{server_url}/{info['upgrade_url']}")
                if response.status_code == 200:
                    upgrades += 1
                    current += 1
                    if callback:
                        callback(f"[{pos}] {info['name']} → Level {current}")
                else:
                    break
            
            results.append((pos, info['name'], current, upgrades, "Done"))
        
        return results


async def upgrade_all_buildings(cookies, server_url: str, target_level: int = 20, callback=None):
    """
    Upgrade all buildings (19-40) to target level.
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        results = []
        
        for pos in range(19, 41):
            info = await get_field_info(client, server_url, pos)
            
            # Skip empty slots - check for construction page indicators
            name_lower = info['name'].lower()
            if ('empty' in name_lower or 
                'construction' in name_lower or 
                'new building' in name_lower or
                info['name'] == f"Position {pos}" or
                info['level'] == 0):
                if callback:
                    callback(f"[{pos}] Empty slot - skipping")
                results.append((pos, "Empty", 0, 0, "Skipped"))
                continue
            
            if info['level'] >= target_level:
                results.append((pos, info['name'], info['level'], 0, "Already at target"))
                if callback:
                    callback(f"[{pos}] {info['name']} - Level {info['level']} ✓")
                continue
            
            # Upgrade loop
            upgrades = 0
            current = info['level']
            
            while current < target_level:
                info = await get_field_info(client, server_url, pos)
                current = info['level']
                
                if current >= target_level:
                    break
                
                if info['upgrade_url'] is None:
                    break
                
                response = await client.get(f"{server_url}/{info['upgrade_url']}")
                if response.status_code == 200:
                    upgrades += 1
                    current += 1
                    if callback:
                        callback(f"[{pos}] {info['name']} → Level {current}")
                else:
                    break
            
            results.append((pos, info['name'], current, upgrades, "Done"))
        
        return results


# Legacy functions for backwards compatibility
async def build_or_upgrade_resource(cookies, position_id, loop, server_url="https://fun.gotravspeed.com"):
    """Build or upgrade a resource field."""
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        for _ in range(loop):
            if not await upgrade_field(client, server_url, position_id):
                break
            logger.info(f"Upgraded resource at position {position_id}")


async def construct_and_upgrade_building(cookies, position_id, building_id, loops, server_url="https://fun.gotravspeed.com"):
    """Construct or upgrade a building."""
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        for _ in range(loops):
            if not await upgrade_field(client, server_url, position_id):
                break
            logger.info(f"Upgraded building at position {position_id}")


async def research_academy(session_manager, server_url="https://fun.gotravspeed.com"):
    """Research new troops in the Academy."""
    cookies = await session_manager.get_cookies()
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        while True:
            response = await client.get(f"{server_url}/build.php?id=33")
            soup = BeautifulSoup(response.text, 'html.parser')
            research_links = soup.select('table.build_details .act a.build')
            if not research_links:
                logger.info("All troops in the Academy are fully researched.")
                break

            for link in research_links:
                research_url = f"{server_url}/{link['href']}"
                await client.get(research_url)
                logger.info("Researching new troop in the Academy")
                break


async def upgrade_armory(session_manager, server_url="https://fun.gotravspeed.com"):
    """Upgrade troops in the Armory."""
    cookies = await session_manager.get_cookies()
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        while True:
            response = await client.get(f"{server_url}/build.php?id=29")
            soup = BeautifulSoup(response.text, 'html.parser')
            upgrade_links = soup.select('table.build_details .act a.build')
            if not upgrade_links:
                logger.info("All troops in the Armory are fully upgraded.")
                break

            for link in upgrade_links:
                troop_info = link.find_previous('div', class_='tit').text
                troop_level = int(troop_info.split('(')[-1].split(')')[0].split(' ')[-1])
                if troop_level < 20:
                    upgrade_url = f"{server_url}/{link['href']}"
                    await client.get(upgrade_url)
                    logger.info(f"Upgrading {troop_info.split('(')[0].strip()} to level {troop_level + 1} in the Armory")
                    break


async def upgrade_smithy(session_manager, server_url="https://fun.gotravspeed.com"):
    """Upgrade troops in the Smithy."""
    cookies = await session_manager.get_cookies()
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        while True:
            response = await client.get(f"{server_url}/build.php?id=21")
            soup = BeautifulSoup(response.text, 'html.parser')
            upgrade_links = soup.select('table.build_details .act a.build')
            if not upgrade_links:
                logger.info("All troops in the Smithy are fully upgraded.")
                break

            for link in upgrade_links:
                troop_info = link.find_previous('div', class_='tit').text
                troop_level = int(troop_info.split('(')[-1].split(')')[0].split(' ')[-1])
                if troop_level < 20:
                    upgrade_url = f"{server_url}/{link['href']}"
                    await client.get(upgrade_url)
                    logger.info(f"Upgrading {troop_info.split('(')[0].strip()} to level {troop_level + 1} in the Smithy")
                    break
