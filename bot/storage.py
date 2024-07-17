import asyncio
import httpx
from bs4 import BeautifulSoup
from login import login
from database import save_task, save_stats
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress httpx logging
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

async def increase_storage_async(username, password, loops, conn):
    cookies = await login(username, password, conn)
    if not cookies:
        return

    async with httpx.AsyncClient(cookies=cookies) as client:
        completed = 0
        start_time = time.time()
        for i in range(loops):
            get_response = await client.get("https://fun.gotravspeed.com/buy2.php?t=2")
            soup = BeautifulSoup(get_response.text, 'html.parser')
            key_element = soup.find('input', {'name': 'key'})

            if key_element is None:
                logger.error("Failed to find key for increasing storage. Clearing cache and cookies, and restarting...")
                client.cookies.clear()
                await asyncio.sleep(1)
                continue

            key = key_element['value']
            data = {
                'selected_res': 4,
                'g-recaptcha-response': 'xxxx',
                'xor': 100,
                'key': key
            }
            await client.post("https://fun.gotravspeed.com/buy2.php?t=2&Shop=done", data=data)
            completed += 1

            end_time = time.time()
            elapsed_time = end_time - start_time
            speed = (i + 1) / elapsed_time if elapsed_time > 0 else 0

            logger.info(f"Storage Increased - {completed} out of {loops} completed - ({speed:.2f} per second)")

        save_task(conn, username, 'storage', loops)
        save_stats(conn, username, 'storage', loops, completed)
        logger.info("Storage increase completed.")
