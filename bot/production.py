import asyncio
import httpx
from bs4 import BeautifulSoup
from .database import save_task, save_stats
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)


async def increase_production_async(username, password, loops, conn, cookies=None, debug=False):
    """
    Increase production resources.
    
    Args:
        username: Username for saving stats
        password: Password (kept for backwards compatibility, not used if cookies provided)
        loops: Number of times to increase production
        conn: Database connection
        cookies: Optional pre-authenticated cookies. If not provided, will login.
        debug: If True, print detailed response info
    """
    if cookies is None:
        from .session_manager import SessionManager
        session_manager = SessionManager(username, password, '', conn)
        cookies = await session_manager.get_cookies()
        if not cookies:
            return

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://fun.gotravspeed.com',
        'Referer': 'https://fun.gotravspeed.com/buy2.php?t=0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    }

    # Use follow_redirects=False so we can detect success via 302
    async with httpx.AsyncClient(cookies=cookies, headers=headers, follow_redirects=False) as client:
        completed = 0
        start_time = time.time()
        
        for i in range(loops):
            # Get fresh key
            get_response = await client.get("https://fun.gotravspeed.com/buy2.php?t=0")
            soup = BeautifulSoup(get_response.text, 'html.parser')
            key_element = soup.find('input', {'name': 'key'})

            if key_element is None:
                logger.error("Failed to find key for production. Retrying...")
                await asyncio.sleep(0.5)
                continue

            key = key_element['value']
            
            # Working coordinates - verified from testing!
            data = {
                'selected_res': '4',
                'xor': '100',
                'key_x': '719',
                'key_y': '588',
                'key': key
            }
            
            response = await client.post(
                "https://fun.gotravspeed.com/buy2.php?t=0&Shop=done", 
                data=data
            )
            
            # 302 redirect means SUCCESS!
            if response.status_code == 302:
                completed += 1
                end_time = time.time()
                elapsed_time = end_time - start_time
                speed = completed / elapsed_time if elapsed_time > 0 else 0
                logger.info(f"✅ Production Increased - {completed}/{loops} - ({speed:.2f}/sec)")
            else:
                # Check for success message in response
                soup = BeautifulSoup(response.text, 'html.parser')
                success = soup.find('span', class_='succes')
                if success and 'You got' in success.text:
                    completed += 1
                    logger.info(f"✅ Production Increased - {completed}/{loops}")
                else:
                    logger.warning(f"⚠️ Request may have failed - status {response.status_code}")

        save_task(conn, username, 'production', loops)
        save_stats(conn, username, 'production', loops, completed)
        logger.info(f"Production increase completed. Success: {completed}/{loops}")
