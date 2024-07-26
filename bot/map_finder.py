# map_finder.py

import httpx
import logging
from database import save_empty_spot, delete_all_empty_spots
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def generate_spiral_village_ids(center_id, max_villages=1500, max_radius=25):
    radius = 1
    ids = []
    while len(ids) < max_villages and radius <= max_radius:
        for i in range(-radius, radius + 1):
            ids.append(center_id - 401 * radius + i)
        for i in range(-radius + 1, radius):
            ids.append(center_id - 401 * i + radius)
        for i in range(-radius, radius + 1):
            ids.append(center_id + 401 * radius - i)
        for i in range(-radius + 1, radius):
            ids.append(center_id + 401 * i - radius)
        radius += 1
    return ids[:max_villages]

async def is_village_empty(cookies, village_id):
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"https://fun.gotravspeed.com/village3.php?id={village_id}")
        return '»building a new village' in response.text

async def find_empty_village_spots(cookies, potential_village_ids, conn):
    """
    Find and save empty village spots.
    """
    delete_all_empty_spots(conn)
    for village_id in potential_village_ids:
        if await is_village_empty(cookies, village_id):
            save_empty_spot(conn, village_id, 0)  # 0 indicates not settled
            logger.info(f"Found empty spot at village ID {village_id}")
