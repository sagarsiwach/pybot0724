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
            
            # Skip empty slots
            if 'empty' in info['name'].lower() or info['name'] == f"Position {pos}":
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
