import httpx
import logging
from session_manager import SessionManager

BASE_URL = "https://fun.gotravspeed.com"

logger = logging.getLogger(__name__)

async def switch_village(session_manager, village_id):
    """
    Switch to a different village by ID.
    """
    cookies = await session_manager.get_cookies()
    async with httpx.AsyncClient(cookies=cookies) as client:
        response = await client.get(f"{BASE_URL}/village2.php?vid={village_id}")
        if response.status_code == 200:
            logger.info(f"Switched to village ID {village_id}")
        else:
            logger.error(f"Failed to switch to village ID {village_id}")
