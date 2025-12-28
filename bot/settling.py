# settling.py
"""
Village settling module for Travian.

Features:
- Find empty spots near current village
- Train settlers
- Send settlers to settle new village
"""

import asyncio
import httpx
import logging
from bs4 import BeautifulSoup
from .troop_training import train_settlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
}


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


async def settle_village(cookies, server_url: str, target_village_id: int, callback=None):
    """
    Send settlers to settle a new village.
    
    Prerequisites:
    - Must have 3 settlers available
    - Target must be an empty spot
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        target_village_id: ID of the empty spot to settle
        callback: Progress callback
    
    Returns:
        True if settling was successful
    """
    async with httpx.AsyncClient(cookies=cookies, headers=HEADERS) as client:
        # Step 1: Go to the empty spot page
        if callback:
            callback(f"Navigating to village ID {target_village_id}...")
        
        response = await client.get(f"{server_url}/village3.php?id={target_village_id}")
        
        if 'building a new village' not in response.text.lower():
            if callback:
                callback("Target is not an empty spot!")
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step 2: Find the settle link/button
        # Look for "Settle here" or similar link
        settle_link = None
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.text.lower()
            if 'settle' in text or 'a2b.php' in href:
                settle_link = href
                break
        
        if not settle_link:
            # Try button
            for btn in soup.find_all('button'):
                if 'settle' in btn.text.lower():
                    # Look for onclick or parent form
                    form = btn.find_parent('form')
                    if form:
                        settle_link = form.get('action', '')
                    break
        
        if not settle_link:
            if callback:
                callback("Could not find settle button. Do you have 3 settlers?")
            return False
        
        # Step 3: Follow the settle link
        if callback:
            callback(f"Settling at {target_village_id}...")
        
        if not settle_link.startswith('http'):
            settle_link = f"{server_url}/{settle_link}"
        
        response = await client.get(settle_link)
        
        if response.status_code == 200:
            if callback:
                coords = await get_coordinates_from_id(target_village_id)
                callback(f"✓ Successfully settled at ({coords[0]}|{coords[1]})!")
            logger.info(f"Settled new village at ID {target_village_id}")
            return True
        else:
            if callback:
                callback(f"Settling failed: HTTP {response.status_code}")
            return False


async def auto_settle(cookies, server_url: str, residence_position: int = 25, callback=None):
    """
    Fully automated settling:
    1. Find nearest empty spot
    2. Check if settlers are trained
    3. Send settlers to settle
    
    Args:
        cookies: Session cookies
        server_url: Server URL
        residence_position: Position of Residence/Palace
        callback: Progress callback
    """
    if callback:
        callback("=== AUTO SETTLE ===")
    
    # Step 1: Find empty spots
    if callback:
        callback("Searching for empty spots...")
    
    spots = await find_empty_spots(cookies, server_url, max_spots=5, max_radius=20, callback=callback)
    
    if not spots:
        if callback:
            callback("No empty spots found nearby!")
        return False
    
    target = spots[0]
    coords = await get_coordinates_from_id(target)
    if callback:
        callback(f"Target: ({coords[0]}|{coords[1]}) - ID {target}")
    
    # Step 2: Check/train settlers
    # TODO: Check if 3 settlers are available, if not train them
    if callback:
        callback("Ensure you have 3 settlers trained in Residence!")
    
    # Step 3: Settle
    success = await settle_village(cookies, server_url, target, callback)
    
    return success
